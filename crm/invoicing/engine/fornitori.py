# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A supplier's invoice, read out of its own XML.

The FatturaPA a supplier sent is the record: what the centre owes, by when, and
how much of it is VAT it can take back. Itala hands a summary too, but its shape is
theirs (`busta.fattura_ricevuta`); the file is the SdI's, the same for every
intermediary, so the amounts come from here.

Namespace-agnostic, local names only, as the notices are read (`ricevute`): a
supplier's software writes `p:`, `ns2:` or nothing. A file with a DOCTYPE is not
read at all: a FatturaPA has none, and one that brings entities brings trouble.
Without a site, tested with plain `unittest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET


@dataclass
class Riga:
	descrizione: str
	quantita: Decimal | None
	prezzo_totale: Decimal
	aliquota_iva: Decimal
	natura: str | None = None


@dataclass
class FatturaFornitore:
	fornitore: str = ""
	partita_iva: str = ""
	codice_fiscale: str = ""
	tipo_documento: str = ""
	numero: str = ""
	data: date | None = None
	divisa: str = "EUR"
	totale: Decimal = Decimal("0")
	imponibile: Decimal = Decimal("0")
	iva: Decimal = Decimal("0")
	scadenza: date | None = None
	righe: list[Riga] = field(default_factory=list)

	def campi(self) -> dict:
		"""What `CRM Supplier Invoice` keeps of it."""
		return {
			"supplier_name": self.fornitore or None,
			"supplier_tax_id": self.partita_iva or None,
			"supplier_fiscal_code": self.codice_fiscale or None,
			"document_type": self.tipo_documento or None,
			"document_number": self.numero or None,
			"document_date": self.data.isoformat() if self.data else None,
			"currency": self.divisa or "EUR",
			"total_amount": float(self.totale),
			"taxable_amount": float(self.imponibile),
			"vat_amount": float(self.iva),
			"due_date": self.scadenza.isoformat() if self.scadenza else None,
		}


def _locale(elemento) -> str:
	return elemento.tag.rsplit("}", 1)[-1]


def _figlio(padre, *percorso):
	"""The first descendant along the local names given, or None."""
	corrente = padre
	for nome in percorso:
		if corrente is None:
			return None
		corrente = next((f for f in corrente if _locale(f) == nome), None)
	return corrente


def _testo(padre, *percorso) -> str:
	elemento = _figlio(padre, *percorso)
	return (elemento.text or "").strip() if elemento is not None else ""


def _numero(testo: str) -> Decimal | None:
	try:
		return Decimal(testo) if testo else None
	except InvalidOperation:
		return None


def _data(testo: str) -> date | None:
	try:
		return date.fromisoformat(testo[:10]) if testo else None
	except ValueError:
		return None


def leggi(contenuto: bytes | str) -> FatturaFornitore | None:
	"""The invoice's facts, or None for what is not a readable FatturaPA. Of a file
	with several bodies, the first: the one its name and the SdI's id stand for."""
	if isinstance(contenuto, str):
		contenuto = contenuto.encode()
	if not contenuto or b"<!DOCTYPE" in contenuto[:4096].upper() or b"<!ENTITY" in contenuto.upper():
		return None
	try:
		radice = ET.fromstring(contenuto)
	except ET.ParseError:
		return None
	if _locale(radice) != "FatturaElettronica":
		return None

	testata = _figlio(radice, "FatturaElettronicaHeader")
	corpo = _figlio(radice, "FatturaElettronicaBody")
	if testata is None or corpo is None:
		return None

	cedente = _figlio(testata, "CedentePrestatore", "DatiAnagrafici")
	nome = _testo(cedente, "Anagrafica", "Denominazione") or " ".join(
		p for p in (_testo(cedente, "Anagrafica", "Nome"), _testo(cedente, "Anagrafica", "Cognome")) if p
	)
	paese = _testo(cedente, "IdFiscaleIVA", "IdPaese")
	codice = _testo(cedente, "IdFiscaleIVA", "IdCodice")
	documento = _figlio(corpo, "DatiGenerali", "DatiGeneraliDocumento")

	fattura = FatturaFornitore(
		fornitore=nome,
		# an Italian VAT number as the centre writes its own: without the prefix
		partita_iva=codice if paese in ("", "IT") else f"{paese}{codice}",
		codice_fiscale=_testo(cedente, "CodiceFiscale"),
		tipo_documento=_testo(documento, "TipoDocumento"),
		numero=_testo(documento, "Numero"),
		data=_data(_testo(documento, "Data")),
		divisa=_testo(documento, "Divisa") or "EUR",
	)

	beni = _figlio(corpo, "DatiBeniServizi")
	for blocco in list(beni) if beni is not None else []:
		if _locale(blocco) == "DettaglioLinee":
			fattura.righe.append(
				Riga(
					descrizione=_testo(blocco, "Descrizione"),
					quantita=_numero(_testo(blocco, "Quantita")),
					prezzo_totale=_numero(_testo(blocco, "PrezzoTotale")) or Decimal("0"),
					aliquota_iva=_numero(_testo(blocco, "AliquotaIVA")) or Decimal("0"),
					natura=_testo(blocco, "Natura") or None,
				)
			)
		elif _locale(blocco) == "DatiRiepilogo":
			fattura.imponibile += _numero(_testo(blocco, "ImponibileImporto")) or Decimal("0")
			fattura.iva += _numero(_testo(blocco, "Imposta")) or Decimal("0")

	dichiarato = _numero(_testo(documento, "ImportoTotaleDocumento"))
	# the total the supplier wrote, else what the summaries add up to
	fattura.totale = dichiarato if dichiarato is not None else fattura.imponibile + fattura.iva

	scadenze = [
		_data(_testo(dettaglio, "DataScadenzaPagamento"))
		for pagamento in corpo
		if _locale(pagamento) == "DatiPagamento"
		for dettaglio in pagamento
		if _locale(dettaglio) == "DettaglioPagamento"
	]
	scadenze = [s for s in scadenze if s]
	fattura.scadenza = min(scadenze) if scadenze else None
	return fattura
