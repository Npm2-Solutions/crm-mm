"""FatturaPA 1.2.2: the XML, generated here.

The original design bought this conversion from a provider, and for good reason:
XML generation is where 90% of the bugs live, and outsourcing it was cheaper than
owning it. That trade stops making sense once the system runs on its own
infrastructure in Europe. Owning the format means the invoice can be produced,
inspected and kept without a round trip to anybody's API, and the transmission
channel becomes a swappable last mile rather than the thing that holds the data.

So this module builds the document, and `valida` re-reads it with the SdI's own
rejection codes before anybody sends it. Being rejected is not free: the invoice
is considered not issued, and the five days to resubmit run from the notice.

Element order is not cosmetic. The schema is a sequence, so a block in the wrong
position is rejected with code 00001 and no explanation worth the name. The order
in this file is the order of the XSD, and that is why the builders are verbose
instead of clever.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET

from .codici import (
	CODICE_DESTINATARIO_ASSENTE,
	CODICE_DESTINATARIO_ESTERO,
	FORMATO_PA,
	FORMATO_PRIVATI,
	LUNGHEZZA_CODICE_PA,
	LUNGHEZZA_CODICE_PRIVATI,
	NATURE_RITIRATE,
	TIPI_DOCUMENTO_CON_RIFERIMENTO,
	CondizioniPagamento,
	EsigibilitaIVA,
	TipoDocumento,
)

NAMESPACE = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"
SCHEMA_LOCATION = (
	"http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2 "
	"http://www.fatturapa.gov.it/export/fatturazione/sdi/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd"
)
XSI = "http://www.w3.org/2001/XMLSchema-instance"
DS = "http://www.w3.org/2000/09/xmldsig#"

ZERO = Decimal("0.00")
#: The SdI tolerates a one-cent rounding gap on the summary blocks and one euro
#: on the document total (specifiche tecniche, controlli 00421 and 00422).
TOLLERANZA_CENTESIMO = Decimal("0.01")
TOLLERANZA_TOTALE = Decimal("1.00")

_ALFANUM = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class ErroreFatturaPA(ValueError):
	"""The document cannot be serialised: a mandatory element is missing."""


def _d(valore: Decimal | None, decimali: int = 2) -> str:
	return f"{Decimal(valore or 0):.{decimali}f}"


def _sub(parent: ET.Element, tag: str, testo: str | None = None) -> ET.Element:
	elemento = ET.SubElement(parent, tag)
	if testo is not None:
		elemento.text = testo
	return elemento


def _sub_se(parent: ET.Element, tag: str, testo: str | None) -> None:
	"""Add the element only when there is something to put in it.

	An empty element is not the same as an absent one: the schema rejects
	`<Provincia></Provincia>` where it happily accepts no Provincia at all.
	"""
	if testo is None:
		return
	pulito = str(testo).strip()
	if pulito:
		_sub(parent, tag, pulito)


@dataclass
class Sede:
	indirizzo: str
	cap: str
	comune: str
	provincia: str | None = None
	numero_civico: str | None = None
	nazione: str = "IT"

	def xml(self, parent: ET.Element, tag: str = "Sede") -> ET.Element:
		blocco = _sub(parent, tag)
		_sub(blocco, "Indirizzo", (self.indirizzo or "").strip()[:60])
		_sub_se(blocco, "NumeroCivico", self.numero_civico)
		_sub(blocco, "CAP", re.sub(r"\s", "", self.cap or ""))
		_sub(blocco, "Comune", (self.comune or "").strip()[:60])
		_sub_se(blocco, "Provincia", (self.provincia or "").strip().upper()[:2] or None)
		_sub(blocco, "Nazione", (self.nazione or "IT").strip().upper())
		return blocco


@dataclass
class Anagrafica:
	"""Who a party is. Either a `denominazione` or a `nome`/`cognome` pair."""

	denominazione: str | None = None
	nome: str | None = None
	cognome: str | None = None
	titolo: str | None = None
	cod_eori: str | None = None
	id_paese: str | None = None
	id_codice: str | None = None
	codice_fiscale: str | None = None

	def xml_anagrafica(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "Anagrafica")
		if self.denominazione:
			_sub(blocco, "Denominazione", self.denominazione.strip()[:80])
		else:
			_sub(blocco, "Nome", (self.nome or "").strip()[:60])
			_sub(blocco, "Cognome", (self.cognome or "").strip()[:60])
		_sub_se(blocco, "Titolo", self.titolo)
		_sub_se(blocco, "CodEORI", self.cod_eori)

	def xml_identificativi(self, parent: ET.Element, iva_obbligatoria: bool) -> None:
		if self.id_codice:
			id_fiscale = _sub(parent, "IdFiscaleIVA")
			_sub(id_fiscale, "IdPaese", (self.id_paese or "IT").strip().upper())
			_sub(id_fiscale, "IdCodice", self.id_codice.strip())
		elif iva_obbligatoria:
			raise ErroreFatturaPA(
				"the issuer has no VAT number: FatturaPA requires IdFiscaleIVA on the CedentePrestatore"
			)
		_sub_se(parent, "CodiceFiscale", (self.codice_fiscale or "").strip().upper() or None)


@dataclass
class Contatti:
	telefono: str | None = None
	fax: str | None = None
	email: str | None = None

	@property
	def vuoto(self) -> bool:
		return not (self.telefono or self.fax or self.email)

	def xml(self, parent: ET.Element, tag: str = "Contatti") -> None:
		if self.vuoto:
			return
		blocco = _sub(parent, tag)
		_sub_se(blocco, "Telefono", self.telefono)
		_sub_se(blocco, "Fax", self.fax)
		_sub_se(blocco, "Email", self.email)


@dataclass
class IscrizioneREA:
	ufficio: str
	numero_rea: str
	stato_liquidazione: str = "LN"
	capitale_sociale: Decimal | None = None
	socio_unico: str | None = None

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "IscrizioneREA")
		_sub(blocco, "Ufficio", self.ufficio.strip().upper()[:2])
		_sub(blocco, "NumeroREA", self.numero_rea.strip())
		if self.capitale_sociale is not None:
			_sub(blocco, "CapitaleSociale", _d(self.capitale_sociale))
		_sub_se(blocco, "SocioUnico", self.socio_unico)
		_sub(blocco, "StatoLiquidazione", self.stato_liquidazione)


@dataclass
class Cedente:
	"""The supplier. Everything the recipient reads to know who invoiced them."""

	anagrafica: Anagrafica
	sede: Sede
	regime_fiscale: str = "RF01"
	albo_professionale: str | None = None
	provincia_albo: str | None = None
	numero_iscrizione_albo: str | None = None
	data_iscrizione_albo: date | None = None
	contatti: Contatti = field(default_factory=Contatti)
	iscrizione_rea: IscrizioneREA | None = None
	riferimento_amministrazione: str | None = None

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "CedentePrestatore")
		dati = _sub(blocco, "DatiAnagrafici")
		self.anagrafica.xml_identificativi(dati, iva_obbligatoria=True)
		self.anagrafica.xml_anagrafica(dati)
		# For a professional this block is what makes the document readable to
		# whoever receives it. Optional in the schema, worth filling in.
		_sub_se(dati, "AlboProfessionale", self.albo_professionale)
		_sub_se(dati, "ProvinciaAlbo", (self.provincia_albo or "").upper()[:2] or None)
		_sub_se(dati, "NumeroIscrizioneAlbo", self.numero_iscrizione_albo)
		if self.data_iscrizione_albo:
			_sub(dati, "DataIscrizioneAlbo", self.data_iscrizione_albo.isoformat())
		_sub(dati, "RegimeFiscale", self.regime_fiscale)
		self.sede.xml(blocco)
		if self.iscrizione_rea:
			self.iscrizione_rea.xml(blocco)
		self.contatti.xml(blocco)
		_sub_se(blocco, "RiferimentoAmministrazione", self.riferimento_amministrazione)


@dataclass
class Cessionario:
	"""The client. A natural person here has neither a VAT number nor a code."""

	anagrafica: Anagrafica
	sede: Sede

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "CessionarioCommittente")
		dati = _sub(blocco, "DatiAnagrafici")
		self.anagrafica.xml_identificativi(dati, iva_obbligatoria=False)
		self.anagrafica.xml_anagrafica(dati)
		self.sede.xml(blocco)


@dataclass
class ScontoMaggiorazione:
	tipo: str = "SC"
	percentuale: Decimal | None = None
	importo: Decimal | None = None

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "ScontoMaggiorazione")
		_sub(blocco, "Tipo", self.tipo)
		if self.percentuale is not None:
			_sub(blocco, "Percentuale", _d(self.percentuale))
		if self.importo is not None:
			_sub(blocco, "Importo", _d(self.importo))


@dataclass
class Linea:
	numero: int
	descrizione: str
	prezzo_unitario: Decimal
	prezzo_totale: Decimal
	aliquota_iva: Decimal = ZERO
	quantita: Decimal | None = None
	unita_misura: str | None = None
	natura: str | None = None
	sconti: list[ScontoMaggiorazione] = field(default_factory=list)
	ritenuta: bool = False
	data_inizio_periodo: date | None = None
	data_fine_periodo: date | None = None
	codice_articolo: tuple[str, str] | None = None
	altri_dati: list[tuple[str, str | None, Decimal | None, date | None]] = field(default_factory=list)

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "DettaglioLinee")
		_sub(blocco, "NumeroLinea", str(self.numero))
		if self.codice_articolo:
			codice = _sub(blocco, "CodiceArticolo")
			_sub(codice, "CodiceTipo", self.codice_articolo[0])
			_sub(codice, "CodiceValore", self.codice_articolo[1])
		# The description is the only free field the recipient actually reads. It is
		# also the one that leaks: on a healthcare document it says the specialty.
		_sub(blocco, "Descrizione", (self.descrizione or "").strip()[:1000])
		if self.quantita is not None:
			_sub(blocco, "Quantita", _d(self.quantita, 8).rstrip("0").rstrip(".") or "0")
		_sub_se(blocco, "UnitaMisura", self.unita_misura)
		if self.data_inizio_periodo:
			_sub(blocco, "DataInizioPeriodo", self.data_inizio_periodo.isoformat())
		if self.data_fine_periodo:
			_sub(blocco, "DataFinePeriodo", self.data_fine_periodo.isoformat())
		_sub(blocco, "PrezzoUnitario", _d(self.prezzo_unitario))
		for sconto in self.sconti:
			sconto.xml(blocco)
		_sub(blocco, "PrezzoTotale", _d(self.prezzo_totale))
		_sub(blocco, "AliquotaIVA", _d(self.aliquota_iva))
		if self.ritenuta:
			_sub(blocco, "Ritenuta", "SI")
		_sub_se(blocco, "Natura", self.natura)
		for tipo_dato, testo, numero, data_dato in self.altri_dati:
			altri = _sub(blocco, "AltriDatiGestionali")
			_sub(altri, "TipoDato", tipo_dato)
			_sub_se(altri, "RiferimentoTesto", testo)
			if numero is not None:
				_sub(altri, "RiferimentoNumero", _d(numero))
			if data_dato is not None:
				_sub(altri, "RiferimentoData", data_dato.isoformat())


@dataclass
class Riepilogo:
	aliquota_iva: Decimal
	imponibile_importo: Decimal
	imposta: Decimal
	natura: str | None = None
	spese_accessorie: Decimal | None = None
	arrotondamento: Decimal | None = None
	esigibilita_iva: str | None = EsigibilitaIVA.IMMEDIATA
	riferimento_normativo: str | None = None

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "DatiRiepilogo")
		_sub(blocco, "AliquotaIVA", _d(self.aliquota_iva))
		_sub_se(blocco, "Natura", self.natura)
		if self.spese_accessorie is not None:
			_sub(blocco, "SpeseAccessorie", _d(self.spese_accessorie))
		if self.arrotondamento is not None:
			_sub(blocco, "Arrotondamento", _d(self.arrotondamento))
		_sub(blocco, "ImponibileImporto", _d(self.imponibile_importo))
		_sub(blocco, "Imposta", _d(self.imposta))
		_sub_se(blocco, "EsigibilitaIVA", self.esigibilita_iva)
		_sub_se(blocco, "RiferimentoNormativo", (self.riferimento_normativo or "")[:100] or None)


@dataclass
class DatiRitenuta:
	tipo_ritenuta: str
	importo_ritenuta: Decimal
	aliquota_ritenuta: Decimal
	causale_pagamento: str

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "DatiRitenuta")
		_sub(blocco, "TipoRitenuta", self.tipo_ritenuta)
		_sub(blocco, "ImportoRitenuta", _d(self.importo_ritenuta))
		_sub(blocco, "AliquotaRitenuta", _d(self.aliquota_ritenuta))
		_sub(blocco, "CausalePagamento", self.causale_pagamento)


@dataclass
class DatiCassa:
	tipo_cassa: str
	al_cassa: Decimal
	importo_contributo: Decimal
	aliquota_iva: Decimal
	imponibile_cassa: Decimal | None = None
	ritenuta: bool = False
	natura: str | None = None

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "DatiCassaPrevidenziale")
		_sub(blocco, "TipoCassa", self.tipo_cassa)
		_sub(blocco, "AlCassa", _d(self.al_cassa))
		_sub(blocco, "ImportoContributoCassa", _d(self.importo_contributo))
		if self.imponibile_cassa is not None:
			_sub(blocco, "ImponibileCassa", _d(self.imponibile_cassa))
		_sub(blocco, "AliquotaIVA", _d(self.aliquota_iva))
		if self.ritenuta:
			_sub(blocco, "Ritenuta", "SI")
		_sub_se(blocco, "Natura", self.natura)


@dataclass
class DocumentoCollegato:
	id_documento: str
	data: date | None = None
	num_item: str | None = None
	codice_commessa: str | None = None
	codice_cup: str | None = None
	codice_cig: str | None = None
	riferimento_linee: list[int] = field(default_factory=list)

	def xml(self, parent: ET.Element, tag: str) -> None:
		blocco = _sub(parent, tag)
		for linea in self.riferimento_linee:
			_sub(blocco, "RiferimentoNumeroLinea", str(linea))
		_sub(blocco, "IdDocumento", self.id_documento.strip()[:20])
		if self.data:
			_sub(blocco, "Data", self.data.isoformat())
		_sub_se(blocco, "NumItem", self.num_item)
		_sub_se(blocco, "CodiceCommessaConvenzione", self.codice_commessa)
		_sub_se(blocco, "CodiceCUP", self.codice_cup)
		_sub_se(blocco, "CodiceCIG", self.codice_cig)


@dataclass
class DettaglioPagamento:
	modalita_pagamento: str
	importo_pagamento: Decimal
	data_scadenza: date | None = None
	giorni_termini: int | None = None
	beneficiario: str | None = None
	istituto_finanziario: str | None = None
	iban: str | None = None
	bic: str | None = None

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "DettaglioPagamento")
		_sub_se(blocco, "Beneficiario", self.beneficiario)
		_sub(blocco, "ModalitaPagamento", self.modalita_pagamento)
		if self.giorni_termini is not None:
			_sub(blocco, "GiorniTerminiPagamento", str(self.giorni_termini))
		if self.data_scadenza:
			_sub(blocco, "DataScadenzaPagamento", self.data_scadenza.isoformat())
		_sub(blocco, "ImportoPagamento", _d(self.importo_pagamento))
		_sub_se(blocco, "IstitutoFinanziario", self.istituto_finanziario)
		_sub_se(blocco, "IBAN", re.sub(r"\s", "", self.iban or "") or None)
		_sub_se(blocco, "BIC", self.bic)


@dataclass
class Allegato:
	nome: str
	contenuto_base64: str
	formato: str | None = None
	descrizione: str | None = None

	def xml(self, parent: ET.Element) -> None:
		blocco = _sub(parent, "Allegati")
		_sub(blocco, "NomeAttachment", self.nome[:60])
		_sub_se(blocco, "FormatoAttachment", self.formato)
		_sub_se(blocco, "DescrizioneAttachment", self.descrizione)
		_sub(blocco, "Attachment", self.contenuto_base64)


@dataclass
class FatturaElettronica:
	"""One document, ready to be serialised and validated."""

	cedente: Cedente
	cessionario: Cessionario
	numero: str
	data: date
	linee: list[Linea]
	riepiloghi: list[Riepilogo]
	importo_totale: Decimal
	tipo_documento: str = TipoDocumento.FATTURA
	divisa: str = "EUR"
	codice_destinatario: str = CODICE_DESTINATARIO_ASSENTE
	pec_destinatario: str | None = None
	progressivo_invio: str = "00001"
	formato_trasmissione: str | None = None
	contatti_trasmittente: Contatti = field(default_factory=Contatti)
	dati_ritenuta: list[DatiRitenuta] = field(default_factory=list)
	bollo_virtuale: bool = False
	importo_bollo: Decimal | None = None
	dati_cassa: list[DatiCassa] = field(default_factory=list)
	sconti_documento: list[ScontoMaggiorazione] = field(default_factory=list)
	arrotondamento: Decimal | None = None
	causale: list[str] = field(default_factory=list)
	art73: bool = False
	documenti_collegati: list[DocumentoCollegato] = field(default_factory=list)
	ordini_acquisto: list[DocumentoCollegato] = field(default_factory=list)
	contratti: list[DocumentoCollegato] = field(default_factory=list)
	convenzioni: list[DocumentoCollegato] = field(default_factory=list)
	condizioni_pagamento: str | None = CondizioniPagamento.COMPLETO
	pagamenti: list[DettaglioPagamento] = field(default_factory=list)
	allegati: list[Allegato] = field(default_factory=list)

	@property
	def formato(self) -> str:
		if self.formato_trasmissione:
			return self.formato_trasmissione
		return FORMATO_PA if len(self.codice_destinatario or "") == LUNGHEZZA_CODICE_PA else FORMATO_PRIVATI

	# ------------------------------------------------------------ serialisation

	def elemento(self) -> ET.Element:
		ET.register_namespace("p", NAMESPACE)
		ET.register_namespace("ds", DS)
		ET.register_namespace("xsi", XSI)
		radice = ET.Element(
			f"{{{NAMESPACE}}}FatturaElettronica",
			{"versione": self.formato, f"{{{XSI}}}schemaLocation": SCHEMA_LOCATION},
		)
		self._header(radice)
		self._body(radice)
		return radice

	def _header(self, radice: ET.Element) -> None:
		header = _sub(radice, "FatturaElettronicaHeader")
		trasmissione = _sub(header, "DatiTrasmissione")
		id_trasmittente = _sub(trasmissione, "IdTrasmittente")
		_sub(id_trasmittente, "IdPaese", (self.cedente.anagrafica.id_paese or "IT").upper())
		_sub(
			id_trasmittente,
			"IdCodice",
			(self.cedente.anagrafica.id_codice or self.cedente.anagrafica.codice_fiscale or "").strip(),
		)
		_sub(trasmissione, "ProgressivoInvio", self.progressivo_invio)
		_sub(trasmissione, "FormatoTrasmissione", self.formato)
		_sub(trasmissione, "CodiceDestinatario", self.codice_destinatario)
		self.contatti_trasmittente.xml(trasmissione, "ContattiTrasmittente")
		# `0000000` plus a PEC address: without the PEC the invoice reaches the SdI
		# and stops there, and the client is never told.
		if self.pec_destinatario and self.codice_destinatario == CODICE_DESTINATARIO_ASSENTE:
			_sub(trasmissione, "PECDestinatario", self.pec_destinatario)
		self.cedente.xml(header)
		self.cessionario.xml(header)

	def _body(self, radice: ET.Element) -> None:
		body = _sub(radice, "FatturaElettronicaBody")
		generali = _sub(body, "DatiGenerali")
		documento = _sub(generali, "DatiGeneraliDocumento")
		_sub(documento, "TipoDocumento", self.tipo_documento)
		_sub(documento, "Divisa", self.divisa)
		_sub(documento, "Data", self.data.isoformat())
		_sub(documento, "Numero", self.numero)
		for ritenuta in self.dati_ritenuta:
			ritenuta.xml(documento)
		if self.bollo_virtuale:
			bollo = _sub(documento, "DatiBollo")
			_sub(bollo, "BolloVirtuale", "SI")
			if self.importo_bollo is not None:
				_sub(bollo, "ImportoBollo", _d(self.importo_bollo))
		for cassa in self.dati_cassa:
			cassa.xml(documento)
		for sconto in self.sconti_documento:
			sconto.xml(documento)
		_sub(documento, "ImportoTotaleDocumento", _d(self.importo_totale))
		if self.arrotondamento is not None:
			_sub(documento, "Arrotondamento", _d(self.arrotondamento))
		for riga in self.causale:
			# The `Causale` is capped at 200 characters per repetition, so a long
			# annotation is split rather than truncated: a legal wording cut in half
			# is worse than one spread over two lines.
			for pezzo in _spezza(riga, 200):
				_sub(documento, "Causale", pezzo)
		if self.art73:
			_sub(documento, "Art73", "SI")

		for ordine in self.ordini_acquisto:
			ordine.xml(generali, "DatiOrdineAcquisto")
		for contratto in self.contratti:
			contratto.xml(generali, "DatiContratto")
		for convenzione in self.convenzioni:
			convenzione.xml(generali, "DatiConvenzione")
		for collegato in self.documenti_collegati:
			collegato.xml(generali, "DatiFattureCollegate")

		beni = _sub(body, "DatiBeniServizi")
		for linea in self.linee:
			linea.xml(beni)
		for riepilogo in self.riepiloghi:
			riepilogo.xml(beni)

		if self.pagamenti:
			pagamento = _sub(body, "DatiPagamento")
			_sub(pagamento, "CondizioniPagamento", self.condizioni_pagamento or CondizioniPagamento.COMPLETO)
			for dettaglio in self.pagamenti:
				dettaglio.xml(pagamento)

		for allegato in self.allegati:
			allegato.xml(body)

	def xml(self, indenta: bool = True) -> str:
		radice = self.elemento()
		if indenta:
			ET.indent(radice, space="  ")
		corpo = ET.tostring(radice, encoding="unicode", xml_declaration=False)
		return f'<?xml version="1.0" encoding="UTF-8"?>\n{corpo}\n'

	def nome_file(self, progressivo: str | None = None) -> str:
		"""`ITxxxxxxxxxxx_NNNNN.xml` - the name the SdI expects.

		The progressive is free per sender but has to be unique: the SdI rejects a
		name it has already seen with code 00002, and it does not forget.
		"""
		paese = (self.cedente.anagrafica.id_paese or "IT").upper()
		codice = (self.cedente.anagrafica.id_codice or self.cedente.anagrafica.codice_fiscale or "").strip()
		return f"{paese}{codice}_{(progressivo or self.progressivo_invio).strip()}.xml"


def _spezza(testo: str, lunghezza: int) -> list[str]:
	testo = (testo or "").strip()
	if not testo:
		return []
	return [testo[i : i + lunghezza] for i in range(0, len(testo), lunghezza)]


def progressivo_alfanumerico(contatore: int) -> str:
	"""Base-36 progressive, five characters, as the SdI convention wants it."""
	if contatore < 0:
		raise ValueError("the progressive cannot be negative")
	cifre = ""
	valore = contatore
	while valore:
		valore, resto = divmod(valore, 36)
		cifre = _ALFANUM[resto] + cifre
	return (cifre or "0").rjust(5, "0")[-5:]


def codice_destinatario(
	codice: str | None, pec: str | None, estero: bool = False, pubblica_amministrazione: bool = False
) -> tuple[str, str | None]:
	"""Pick the interchange code, and say whether a PEC has to travel with it."""
	pulito = (codice or "").strip().upper()
	if pubblica_amministrazione:
		if len(pulito) != LUNGHEZZA_CODICE_PA:
			raise ErroreFatturaPA(
				"an invoice to the public administration needs the six-character IPA office code: "
				f"{pulito!r} is not one"
			)
		return pulito, None
	if estero:
		return CODICE_DESTINATARIO_ESTERO, None
	if len(pulito) == LUNGHEZZA_CODICE_PRIVATI:
		return pulito, None
	return CODICE_DESTINATARIO_ASSENTE, pec


# ------------------------------------------------------------------ validation


def valida(fattura: FatturaElettronica) -> list[str]:
	"""Re-read the document with the SdI's own checks, before sending it.

	Rejection is not free: the invoice counts as not issued, and the five days to
	resubmit run from the notice, not from when somebody notices. Every message
	here carries the SdI code so it can be looked up in the specification.
	"""
	problemi: list[str] = []
	problemi.extend(_valida_trasmissione(fattura))
	problemi.extend(_valida_anagrafiche(fattura))
	problemi.extend(_valida_documento(fattura))
	problemi.extend(_valida_importi(fattura))
	return problemi


#: A finding that carries an SdI code is one the SdI itself would reject on. The
#: rest are things a human on the other side will notice - a credit note that does
#: not say what it corrects, an invoice with nowhere to be delivered - and they are
#: worth saying without stopping the document.
_CODICE = re.compile(r"^\d{5}:")


def bloccanti(problemi: list[str]) -> list[str]:
	"""The subset of findings that would come back as a rejection."""
	return [p for p in problemi if _CODICE.match(p)]


def _valida_trasmissione(fattura: FatturaElettronica) -> list[str]:
	problemi: list[str] = []
	codice = fattura.codice_destinatario or ""
	if fattura.formato == FORMATO_PA:
		if len(codice) != LUNGHEZZA_CODICE_PA:
			problemi.append(
				f"00427: with FormatoTrasmissione FPA12 the CodiceDestinatario is six characters, "
				f"{codice!r} has {len(codice)}"
			)
	elif len(codice) != LUNGHEZZA_CODICE_PRIVATI:
		problemi.append(
			f"00427: with FormatoTrasmissione FPR12 the CodiceDestinatario is seven characters, "
			f"{codice!r} has {len(codice)}"
		)
	if codice == CODICE_DESTINATARIO_ASSENTE and not fattura.pec_destinatario:
		problemi.append(
			"the recipient has neither an interchange code nor a PEC address: the invoice reaches "
			"the SdI and stops there. It is valid, but the client never receives it"
		)
	if not re.fullmatch(r"[A-Za-z0-9]{1,10}", fattura.progressivo_invio or ""):
		problemi.append("00001: ProgressivoInvio must be alphanumeric, at most ten characters")
	return problemi


def _valida_anagrafiche(fattura: FatturaElettronica) -> list[str]:
	problemi: list[str] = []
	cedente = fattura.cedente.anagrafica
	if not cedente.id_codice:
		problemi.append("00400: the CedentePrestatore has no IdFiscaleIVA")
	if not (cedente.denominazione or (cedente.nome and cedente.cognome)):
		problemi.append("00000: the CedentePrestatore has neither a Denominazione nor Nome/Cognome")

	cessionario = fattura.cessionario.anagrafica
	if not (cessionario.id_codice or cessionario.codice_fiscale):
		problemi.append(
			"00417: the CessionarioCommittente has neither IdFiscaleIVA nor CodiceFiscale - at "
			"least one of the two is mandatory"
		)
	if not (cessionario.denominazione or (cessionario.nome and cessionario.cognome)):
		problemi.append("00000: the CessionarioCommittente has neither a Denominazione nor Nome/Cognome")

	for etichetta, sede in (
		("CedentePrestatore", fattura.cedente.sede),
		("CessionarioCommittente", fattura.cessionario.sede),
	):
		if not sede.indirizzo or not sede.comune:
			problemi.append(
				f"00000: the {etichetta} address is incomplete (Indirizzo and Comune are mandatory)"
			)
		nazione = (sede.nazione or "").upper()
		if not re.fullmatch(r"[A-Z]{2}", nazione):
			problemi.append(f"00000: {etichetta} Nazione must be a two-letter ISO code, not {sede.nazione!r}")
		cap = re.sub(r"\s", "", sede.cap or "")
		if nazione == "IT" and not re.fullmatch(r"\d{5}", cap):
			problemi.append(
				f"00000: {etichetta} CAP must be five digits for an Italian address, not {sede.cap!r}"
			)
		if sede.provincia and not re.fullmatch(r"[A-Za-z]{2}", sede.provincia.strip()):
			problemi.append(f"00000: {etichetta} Provincia must be two letters, not {sede.provincia!r}")
	return problemi


def _valida_documento(fattura: FatturaElettronica) -> list[str]:
	problemi: list[str] = []
	if not fattura.numero:
		problemi.append("00425: the document number is missing")
	elif not any(c.isdigit() for c in fattura.numero):
		problemi.append(
			f"00425: the document number {fattura.numero!r} contains no digit - the SdI requires at least one"
		)
	if fattura.tipo_documento in TIPI_DOCUMENTO_CON_RIFERIMENTO and not fattura.documenti_collegati:
		problemi.append(
			f"{fattura.tipo_documento} without DatiFattureCollegate: a credit or debit note has to "
			"say which document it corrects. The SdI accepts it, the recipient's accounting does not"
		)
	if not fattura.linee:
		problemi.append("00423: the document has no DettaglioLinee")
	if not fattura.riepiloghi:
		problemi.append("00419: the document has no DatiRiepilogo")
	for linea in fattura.linee:
		if linea.aliquota_iva == ZERO and not linea.natura:
			problemi.append(
				f"00400: line {linea.numero} has AliquotaIVA zero without a Natura - the reason the "
				"tax is not charged is mandatory"
			)
		if linea.aliquota_iva != ZERO and linea.natura:
			problemi.append(
				f"00401: line {linea.numero} carries a Natura together with a non-zero AliquotaIVA"
			)
		if linea.natura in NATURE_RITIRATE:
			problemi.append(
				f"00445: line {linea.numero} uses Natura {linea.natura!r}, retired with tracciato "
				"1.2.2 - use the sub-code"
			)
	for riepilogo in fattura.riepiloghi:
		if riepilogo.aliquota_iva == ZERO and not riepilogo.natura:
			problemi.append("00429: a DatiRiepilogo block has AliquotaIVA zero without a Natura")
		if riepilogo.aliquota_iva != ZERO and riepilogo.natura:
			problemi.append("00430: a DatiRiepilogo block carries a Natura with a non-zero AliquotaIVA")
		if riepilogo.natura in NATURE_RITIRATE:
			problemi.append(f"00445: DatiRiepilogo uses the retired Natura {riepilogo.natura!r}")
	return problemi


def _valida_importi(fattura: FatturaElettronica) -> list[str]:
	problemi: list[str] = []

	# 00423 - each summary block's taxable amount against the lines that feed it.
	per_chiave: dict[tuple[str, str], Decimal] = {}
	for linea in fattura.linee:
		chiave = (_d(linea.aliquota_iva), linea.natura or "")
		per_chiave[chiave] = per_chiave.get(chiave, ZERO) + Decimal(linea.prezzo_totale)
	for riepilogo in fattura.riepiloghi:
		chiave = (_d(riepilogo.aliquota_iva), riepilogo.natura or "")
		atteso = per_chiave.pop(chiave, None)
		if atteso is None:
			continue
		# The levy and the re-charged stamp duty live in the summary and not on a
		# line, so the summary is legitimately the larger of the two.
		if Decimal(riepilogo.imponibile_importo) < atteso - TOLLERANZA_CENTESIMO:
			problemi.append(
				f"00423: the DatiRiepilogo block at {riepilogo.aliquota_iva}% carries "
				f"{riepilogo.imponibile_importo} against {atteso} on the lines"
			)
		# 00421 - the tax against its own taxable amount.
		atteso_imposta = (
			Decimal(riepilogo.imponibile_importo) * Decimal(riepilogo.aliquota_iva) / Decimal("100")
		).quantize(Decimal("0.01"))
		if abs(Decimal(riepilogo.imposta) - atteso_imposta) > TOLLERANZA_CENTESIMO:
			problemi.append(
				f"00421: the DatiRiepilogo block at {riepilogo.aliquota_iva}% carries Imposta "
				f"{riepilogo.imposta}, computed {atteso_imposta}"
			)
	for (aliquota, natura), importo in per_chiave.items():
		problemi.append(
			f"00419: there are lines at {aliquota}%"
			+ (f" with Natura {natura}" if natura else "")
			+ f" totalling {importo} and no matching DatiRiepilogo block"
		)

	# 00422 - the document total against the summary blocks.
	atteso_totale = sum(
		(Decimal(r.imponibile_importo) + Decimal(r.imposta) for r in fattura.riepiloghi), ZERO
	)
	if fattura.bollo_virtuale and fattura.importo_bollo:
		# A virtual stamp duty that is not re-charged does not enter the total; when
		# it is re-charged it is already inside a summary block. Either way the gap
		# stays within the one-euro tolerance, so we only warn on a real divergence.
		atteso_totale_con_bollo = atteso_totale + Decimal(fattura.importo_bollo)
		if (
			abs(Decimal(fattura.importo_totale) - atteso_totale) > TOLLERANZA_TOTALE
			and abs(Decimal(fattura.importo_totale) - atteso_totale_con_bollo) > TOLLERANZA_TOTALE
		):
			problemi.append(
				f"00422: ImportoTotaleDocumento {fattura.importo_totale} against {atteso_totale} "
				f"from the summary blocks ({atteso_totale_con_bollo} counting the stamp duty)"
			)
	elif abs(Decimal(fattura.importo_totale) - atteso_totale) > TOLLERANZA_TOTALE:
		problemi.append(
			f"00422: ImportoTotaleDocumento {fattura.importo_totale} against {atteso_totale} from "
			"the summary blocks"
		)

	for cassa in fattura.dati_cassa:
		if cassa.aliquota_iva == ZERO and not cassa.natura:
			problemi.append("00413: DatiCassaPrevidenziale has AliquotaIVA zero without a Natura")
		if cassa.aliquota_iva != ZERO and cassa.natura:
			problemi.append("00414: DatiCassaPrevidenziale carries a Natura with a non-zero AliquotaIVA")
	for ritenuta in fattura.dati_ritenuta:
		if Decimal(ritenuta.importo_ritenuta) <= ZERO:
			problemi.append("00434: DatiRitenuta with a zero or negative ImportoRitenuta")
		if not any(linea.ritenuta for linea in fattura.linee) and not any(
			c.ritenuta for c in fattura.dati_cassa
		):
			problemi.append(
				"00415: DatiRitenuta is present but no line and no levy is flagged Ritenuta=SI - the "
				"SdI wants to know what the withholding was computed on"
			)
			break
	return problemi


# -------------------------------------------------- from the computed document

#: Where the levy and the re-charged stamp duty go, and why the totals reconcile
#: only when both are placed exactly here.
#:
#: * the **fund levy** does not sit on a line. It travels in
#:   `DatiCassaPrevidenziale`, and check 00423 counts it towards the summary block,
#:   so lines plus levy blocks equal the summary;
#: * the **re-charged stamp duty** does get a line, because it is part of the
#:   compensation (Risposta AdE 428/2022) and follows the VAT regime of the service.
#:   Leaving it out of the lines is how the summary ends up two euros over.
#:
#: These live here rather than in the Frappe layer so the reconciliation can be
#: tested without a database - it is the seam where a wrong total actually happens.


def linee_da_calcolo(calcolo, dettagli: list[dict]) -> list[Linea]:
	"""Lines from a computed document.

	`dettagli` runs parallel to `calcolo.righe` and carries what the arithmetic does
	not know: the description, the quantity, the unit and the period.
	"""
	linee: list[Linea] = []
	numero = 0
	riaddebiti: dict[tuple[str, str], Decimal] = {}

	for riga, dettaglio in zip(calcolo.righe, dettagli, strict=True):
		numero += 1
		quantita = Decimal(str(dettaglio.get("quantita") or 1))
		prezzo = dettaglio.get("prezzo_unitario")
		if prezzo is None:
			prezzo = riga.imponibile / quantita if quantita else riga.imponibile
		linee.append(
			Linea(
				numero=numero,
				descrizione=dettaglio.get("descrizione") or "",
				quantita=quantita,
				unita_misura=dettaglio.get("unita_misura"),
				prezzo_unitario=Decimal(str(prezzo)),
				prezzo_totale=riga.imponibile,
				aliquota_iva=riga.aliquota,
				natura=riga.natura,
				ritenuta=bool(dettaglio.get("ritenuta")) and not riga.fuori_base_iva,
				data_inizio_periodo=dettaglio.get("data_inizio_periodo"),
				data_fine_periodo=dettaglio.get("data_fine_periodo"),
			)
		)
		if riga.bollo_riaddebitato > ZERO:
			chiave = (_d(riga.aliquota), riga.natura or "")
			riaddebiti[chiave] = riaddebiti.get(chiave, ZERO) + riga.bollo_riaddebitato

	for (aliquota, natura), importo in sorted(riaddebiti.items()):
		numero += 1
		linee.append(
			Linea(
				numero=numero,
				descrizione="Recupero imposta di bollo",
				quantita=Decimal("1"),
				prezzo_unitario=importo,
				prezzo_totale=importo,
				aliquota_iva=Decimal(aliquota),
				natura=natura or None,
			)
		)
	return linee


def riepiloghi_da_calcolo(calcolo) -> list[Riepilogo]:
	return [
		Riepilogo(
			aliquota_iva=r.aliquota,
			natura=r.natura,
			imponibile_importo=r.imponibile,
			imposta=r.imposta,
			esigibilita_iva=r.esigibilita,
			riferimento_normativo=r.riferimento_normativo,
		)
		for r in calcolo.riepiloghi
	]


def casse_da_calcolo(calcolo, ritenuta: bool = False) -> list[DatiCassa]:
	"""One levy block per (rate, nature) pair, so the summary reconciles."""
	if calcolo.cassa <= ZERO or not calcolo.tipo_cassa:
		return []
	per_chiave: dict[tuple[str, str], list[Decimal]] = {}
	for riga in calcolo.righe:
		if riga.cassa <= ZERO:
			continue
		chiave = (_d(riga.aliquota), riga.natura or "")
		quote = per_chiave.setdefault(chiave, [ZERO, ZERO])
		quote[0] += riga.cassa
		quote[1] += riga.imponibile
	return [
		DatiCassa(
			tipo_cassa=calcolo.tipo_cassa,
			al_cassa=calcolo.percentuale_cassa or ZERO,
			importo_contributo=contributo,
			imponibile_cassa=imponibile,
			aliquota_iva=Decimal(aliquota),
			natura=natura or None,
			ritenuta=ritenuta,
		)
		for (aliquota, natura), (contributo, imponibile) in sorted(per_chiave.items())
	]


def ritenute_da_calcolo(calcolo) -> list[DatiRitenuta]:
	if calcolo.ritenuta <= ZERO:
		return []
	return [
		DatiRitenuta(
			tipo_ritenuta=calcolo.tipo_ritenuta or "RT01",
			importo_ritenuta=calcolo.ritenuta,
			aliquota_ritenuta=calcolo.aliquota_ritenuta,
			causale_pagamento=calcolo.causale_pagamento or "A",
		)
	]
