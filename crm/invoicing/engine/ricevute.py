r"""What the Sistema di Interscambio says back.

Six kinds of notice, and only one of them is good news. They matter because a
rejection means the invoice **counts as not issued**: the five days to correct and
resend run from the notice, not from when somebody opens the mailbox.

	RC  Ricevuta di consegna                  delivered to the client
	NS  Notifica di scarto                    rejected - the invoice does not exist
	MC  Mancata consegna                      the SdI has it, the client has not
	AT  Attestazione di trasmissione          delivery impossible, filed instead
	NE  Notifica esito committente            the PA accepted or refused it
	DT  Decorrenza termini                    the PA said nothing for fifteen days

`MC` is the one that gets misread. It is not a failure: the invoice is fiscally
issued and sits in the client's reserved area. What is owed is telling the client,
because the SdI will not.

The parsing is namespace-agnostic on purpose - local names only. The notice
namespaces are versioned and differ between the test and production environments;
a parser that insists on them breaks at the first change, and breaks silently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from xml.etree import ElementTree as ET

from .codici import StatoSdI, StrEnum


class TipoRicevuta(StrEnum):
	CONSEGNA = "RC"
	SCARTO = "NS"
	MANCATA_CONSEGNA = "MC"
	ATTESTAZIONE = "AT"
	ESITO_COMMITTENTE = "NE"
	DECORRENZA_TERMINI = "DT"
	SCARTO_ESITO = "EC"


DESCRIZIONE_RICEVUTA: dict[str, str] = {
	"RC": "Ricevuta di consegna: la fattura e' stata recapitata al destinatario",
	"NS": "Notifica di scarto: la fattura si considera non emessa",
	"MC": "Mancata consegna: la fattura e' emessa e depositata nell'area riservata del destinatario",
	"AT": "Attestazione di avvenuta trasmissione con impossibilita' di recapito",
	"NE": "Notifica di esito committente: la PA ha accettato o rifiutato il documento",
	"DT": "Decorrenza termini: la PA non si e' espressa entro quindici giorni",
	"EC": "Scarto dell'esito committente",
}

#: `ITxxxxxxxxxxx_00001_RC_001.xml` - the notice carries the name of the file it
#: answers, which is the only reliable way back to the document.
NOME_RICEVUTA = re.compile(
	r"^(?P<trasmittente>[A-Z]{2}[A-Za-z0-9]{2,28})_(?P<progressivo>[A-Za-z0-9]{1,10})"
	r"_(?P<tipo>RC|NS|MC|AT|NE|DT|EC)_(?P<contatore>\w{1,3})\.xml$",
	re.IGNORECASE,
)

#: The outcome a public administration returns.
ESITO_ACCETTAZIONE = "EC01"
ESITO_RIFIUTO = "EC02"

#: Which invoice state each notice leaves behind.
STATO_PER_TIPO: dict[str, str] = {
	TipoRicevuta.CONSEGNA: StatoSdI.CONSEGNATA,
	TipoRicevuta.SCARTO: StatoSdI.SCARTATA,
	TipoRicevuta.MANCATA_CONSEGNA: StatoSdI.MANCATA_CONSEGNA,
	TipoRicevuta.ATTESTAZIONE: StatoSdI.MANCATA_CONSEGNA,
	TipoRicevuta.ESITO_COMMITTENTE: StatoSdI.ESITO_PA,
	TipoRicevuta.DECORRENZA_TERMINI: StatoSdI.DECORRENZA_TERMINI,
	TipoRicevuta.SCARTO_ESITO: StatoSdI.ERRORE,
}

#: Notices after which the document is fiscally settled and needs nothing more.
TIPI_TERMINALI: frozenset[str] = frozenset(
	{
		TipoRicevuta.CONSEGNA,
		TipoRicevuta.MANCATA_CONSEGNA,
		TipoRicevuta.ATTESTAZIONE,
		TipoRicevuta.DECORRENZA_TERMINI,
	}
)

#: The rejection codes worth naming, because they are the ones that recur.
DESCRIZIONE_SCARTO: dict[str, str] = {
	"00001": "Nome file non valido",
	"00002": "Nome file duplicato",
	"00003": "Le dimensioni del file superano quelle ammesse",
	"00102": "File non integro (firma non valida)",
	"00200": "File non conforme al formato",
	"00201": "Piu' di 50 errori di formato",
	"00300": "IdFiscaleIVA del CedentePrestatore non valido",
	"00301": "IdFiscaleIVA del CessionarioCommittente non valido",
	"00305": "Codice destinatario non valido",
	"00306": "Codice destinatario non valido",
	"00311": "Codice destinatario non valido",
	"00312": "Codice destinatario non attivo",
	"00313": "PEC destinatario non valida",
	"00318": "Errore di elaborazione del file",
	"00320": "Fattura duplicata",
	"00321": "Fattura gia' trasmessa e accolta",
	"00327": "CessionarioCommittente in Gruppo IVA: il codice fiscale deve essere quello della societa' partecipante, non del Gruppo",
	"00330": "IdFiscaleIVA del CedentePrestatore cessato",
	"00400": "Aliquota IVA a zero senza Natura",
	"00401": "Natura presente con aliquota diversa da zero",
	"00411": "DatiCassaPrevidenziale non congruente",
	"00415": "DatiRitenuta senza righe soggette a ritenuta",
	"00417": "CessionarioCommittente senza identificativo fiscale",
	"00419": "Riepilogo mancante per un'aliquota presente sulle linee",
	"00421": "Imposta non congruente con l'imponibile",
	"00422": "ImportoTotaleDocumento non congruente",
	"00423": "Imponibile del riepilogo non congruente con le linee",
	"00425": "Numero documento privo di cifre",
	"00427": "Codice destinatario di lunghezza errata per il formato",
	"00443": "Imposta non coerente con imponibile e aliquota",
	"00444": "Aliquota non ammessa per il tipo documento",
	"00445": "Natura ritirata con il tracciato 1.2.2",
}


@dataclass(frozen=True)
class ErroreSdI:
	codice: str
	descrizione: str
	suggerimento: str = ""

	def testo(self) -> str:
		nota = DESCRIZIONE_SCARTO.get(self.codice)
		parti = [f"{self.codice}: {self.descrizione or nota or ''}".strip(": ")]
		if nota and nota.lower() not in (self.descrizione or "").lower():
			parti.append(f"({nota})")
		return " ".join(parti)


@dataclass
class Ricevuta:
	"""One notice, read."""

	tipo: str
	identificativo_sdi: str | None = None
	nome_file: str | None = None
	message_id: str | None = None
	data: datetime | None = None
	esito: str | None = None
	descrizione: str | None = None
	errori: list[ErroreSdI] = field(default_factory=list)
	riferimento_fattura: str | None = None

	@property
	def stato(self) -> str:
		return STATO_PER_TIPO.get(self.tipo, StatoSdI.INVIATO)

	@property
	def scartata(self) -> bool:
		return self.tipo == TipoRicevuta.SCARTO or self.esito == ESITO_RIFIUTO

	@property
	def terminale(self) -> bool:
		"""Is there nothing further to wait for?"""
		if self.tipo in TIPI_TERMINALI:
			return True
		return self.tipo == TipoRicevuta.ESITO_COMMITTENTE and self.esito == ESITO_ACCETTAZIONE

	def riassunto(self) -> str:
		"""A sentence for whoever has to act on it."""
		base = DESCRIZIONE_RICEVUTA.get(self.tipo, f"Ricevuta {self.tipo}")
		if self.tipo == TipoRicevuta.SCARTO and self.errori:
			return base + ". " + " · ".join(e.testo() for e in self.errori)
		if self.tipo == TipoRicevuta.ESITO_COMMITTENTE:
			esito = "accettata" if self.esito == ESITO_ACCETTAZIONE else "rifiutata"
			coda = f" - {self.descrizione}" if self.descrizione else ""
			return f"{base}: {esito}{coda}"
		if self.descrizione:
			return f"{base}. {self.descrizione}"
		return base


def tipo_da_nome(nome: str | None) -> str | None:
	"""The notice type, read out of the file name.

	The name is not decoration: it carries the transmitter, the progressive of the
	file being answered and the notice type, and it is the only reliable way back to
	the document when the body does not name it.
	"""
	corrispondenza = NOME_RICEVUTA.match((nome or "").strip())
	if not corrispondenza:
		return None
	return corrispondenza.group("tipo").upper()


def riferimento_da_nome(nome: str | None) -> str | None:
	"""The name of the invoice file this notice answers."""
	corrispondenza = NOME_RICEVUTA.match((nome or "").strip())
	if not corrispondenza:
		return None
	return f"{corrispondenza.group('trasmittente')}_{corrispondenza.group('progressivo')}.xml"


def e_ricevuta(nome: str | None) -> bool:
	return tipo_da_nome(nome) is not None


def _tutti(radice, nome: str) -> list:
	return radice.findall(f".//{{*}}{nome}")


def _testo(radice, *nomi: str) -> str | None:
	for nome in nomi:
		for nodo in _tutti(radice, nome):
			valore = (nodo.text or "").strip()
			if valore:
				return valore
	return None


def _data(valore: str | None) -> datetime | None:
	if not valore:
		return None
	for formato in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
		try:
			return datetime.strptime(valore.split("+")[0].rstrip("Z"), formato)
		except ValueError:
			continue
	return None


_RADICI: dict[str, str] = {
	"RicevutaConsegna": TipoRicevuta.CONSEGNA,
	"RicevutaScarto": TipoRicevuta.SCARTO,
	"RicevutaImpossibilitaRecapito": TipoRicevuta.MANCATA_CONSEGNA,
	"RicevutaImpossibultaRecapito": TipoRicevuta.MANCATA_CONSEGNA,
	"AttestazioneTrasmissioneFattura": TipoRicevuta.ATTESTAZIONE,
	"NotificaEsito": TipoRicevuta.ESITO_COMMITTENTE,
	"NotificaDecorrenzaTermini": TipoRicevuta.DECORRENZA_TERMINI,
	"NotificaScartoEsito": TipoRicevuta.SCARTO_ESITO,
}


def analizza(contenuto: bytes, nome_file: str | None = None) -> Ricevuta | None:
	"""Read a notice. Returns `None` when the file is not one.

	The type comes from the root element when it is recognisable and from the file
	name otherwise - the SdI has shipped both spellings of the undelivered notice
	over the years, and a parser that knows only one of them loses the notice.
	"""
	try:
		radice = ET.fromstring(contenuto)
	except ET.ParseError:
		return None

	locale = radice.tag.split("}")[-1]
	tipo = _RADICI.get(locale) or tipo_da_nome(nome_file)
	if not tipo:
		return None

	ricevuta = Ricevuta(
		tipo=tipo,
		identificativo_sdi=_testo(radice, "IdentificativoSdI"),
		nome_file=_testo(radice, "NomeFile") or nome_file,
		message_id=_testo(radice, "MessageId", "MessageIdCommittente"),
		data=_data(
			_testo(radice, "DataOraConsegna", "DataOraRicezione", "DataOraMessaAdisposizione", "Data")
		),
		esito=_testo(radice, "Esito"),
		descrizione=_testo(radice, "Descrizione", "MessaggioIstruzione"),
		riferimento_fattura=riferimento_da_nome(nome_file),
	)

	for nodo in _tutti(radice, "Errore"):
		codice = _testo(nodo, "Codice") or ""
		descrizione = _testo(nodo, "Descrizione") or ""
		suggerimento = _testo(nodo, "Suggerimento") or ""
		if codice or descrizione:
			ricevuta.errori.append(ErroreSdI(codice, descrizione, suggerimento))

	if ricevuta.tipo == TipoRicevuta.SCARTO and not ricevuta.errori and ricevuta.descrizione:
		ricevuta.errori.append(ErroreSdI("", ricevuta.descrizione))
	return ricevuta
