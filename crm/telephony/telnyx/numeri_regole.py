# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Italian numbers from the centre's Telnyx account, without a site (doc 65).

- **The kinds Telnyx sells in Italy**: geographic numbers (02, 06…) and toll-free
  ones (800). Telnyx sells no Italian mobile: SMS to Italy leave with the centre's
  name, or from a number of another country that sends them.
- **Whose number it is**: a company (Telnyx's "legal entity") or a professional
  with a VAT number in their own name (its "sole proprietorship").
- **The documents**: Telnyx's requirements for Italy - text, an address in Italy,
  documents as PDF - gathered in a requirement group, reusable for the next number
  of the same kind. A requirement DottorCloud recognises by its name gets its words
  and the centre's value (invoicing's company); the others keep Telnyx's.
- **Where a request is**: Italy has no approval before the order, so the number is
  chosen first and ordered with the documents; Telnyx checks both, by hand, in a
  few days, and the order says how it went.
- **A month's price**, from what Telnyx's search says of each number.

The words are English, translated where they are shown.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from crm.telephony import numeri_regole as T


@dataclass(frozen=True)
class Tipo:
	"""A kind of number, as the page offers it."""

	chiave: str
	#: the name in Telnyx's search and requirements
	telnyx: str
	nome: str
	spiegazione: str
	chiama: bool
	sms: bool
	zona: bool = False


TIPI: dict[str, Tipo] = {
	"local": Tipo(
		"local",
		"local",
		"Geographic number",
		"02, 06, 011…: calls in and out. Telnyx asks for an address in Italy and checks the documents by hand.",
		chiama=True,
		sms=False,
		zona=True,
	),
	"toll_free": Tipo(
		"toll_free",
		"toll_free",
		"Toll-free number",
		"800: only takes calls, from Italy, free for whoever calls; the centre pays each minute.",
		chiama=False,
		sms=False,
	),
}

#: Whose the number is, in the page's words and in Telnyx's.
AZIENDA, PERSONA = T.AZIENDA, T.PERSONA
DI_CHI = T.DI_CHI
CLIENTE = {AZIENDA: "legal_entity", PERSONA: "sole_proprietorship"}

#: What Telnyx takes as a document's file for Italy: PDF only, up to 20 MB.
ESTENSIONI = ("pdf",)
MASSIMO = 20 * 1024 * 1024

#: Where a request is: as Twilio's.
BOZZA, IN_VERIFICA, APPROVATA, RIFIUTATA = T.BOZZA, T.IN_VERIFICA, T.APPROVATA, T.RIFIUTATA

#: The words in a requirement's name that say which of the centre's values it asks,
#: the first that matches; the words DottorCloud gives it.
NOTI: tuple[tuple[tuple[str, ...], str, str | None], ...] = (
	(("customer type", "end user type", "type of customer", "entity type"), "Kind of owner", None),
	(
		("company name", "business name", "legal name", "organization name", "ragione sociale"),
		"Business name",
		"business_name",
	),
	(("vat",), "VAT number", "vat_number"),
	(("tax code", "fiscal code", "tax id", "codice fiscale"), "Codice fiscale", "fiscal_code"),
	(("first name", "given name"), "First name", "first_name"),
	(("last name", "surname", "family name"), "Surname", "last_name"),
	(("e-mail", "email"), "Email", "email"),
	(("phone", "contact number"), "Phone", "phone"),
	(("nationality",), "Nationality", "nationality"),
	(("date of birth", "birth date"), "Date of birth", None),
	(("place of birth", "birth place"), "Place of birth", None),
	(("gender",), "Gender", None),
	(("document type", "identity document type", "id type"), "Kind of identity document", None),
	(("issuer", "issuing"), "Issued by", None),
	(("document number", "id number", "passport number"), "Document number", None),
	(("issuance date", "issue date", "date of issue"), "Issue date", None),
	(("expiration date", "expiry date"), "Expiry date", None),
)

#: The documents a centre has to hand, by the words in Telnyx's name for them.
DOCUMENTI: tuple[tuple[tuple[str, ...], str], ...] = (
	(
		("proof of address", "utility", "address proof"),
		"A utility bill at the office's address, of the last three months",
	),
	(
		("registration", "certificate of incorporation", "business register", "chamber of commerce"),
		"Business register extract (visura camerale)",
	),
	(
		("passport", "identity", "id card", "id document", "copy of id"),
		"Identity document of the legal representative, both sides",
	),
	(("tax", "fiscal"), "The codice fiscale card of the legal representative"),
)


def _normale(testo: str | None) -> str:
	return re.sub(r"\s+", " ", (testo or "").lower().replace("_", " ")).strip()


def campo_noto(nome: str | None) -> tuple[str, str | None] | None:
	"""DottorCloud's words for a textual requirement, and the centre's value it
	takes (a key of `numeri.dati_del_centro`); None for one it does not recognise."""
	testo = _normale(nome)
	for parole, etichetta, fonte in NOTI:
		if any(parola in testo for parola in parole):
			return etichetta, fonte
	return None


def documento_noto(nome: str | None) -> str | None:
	"""DottorCloud's words for a document Telnyx asks; None for one it does not
	recognise."""
	testo = _normale(nome)
	for parole, etichetta in DOCUMENTI:
		if any(parola in testo for parola in parole):
			return etichetta
	return None


def _valori_ammessi(tipo: dict) -> list[str]:
	criteri = tipo.get("acceptance_criteria") or {}
	return [str(v) for v in criteri.get("acceptable_values") or [] if str(v).strip()]


def campi(requisiti: list[dict], dati: dict, utente: str) -> list[dict]:
	"""The textual requirements as the page's fields: their name, words, the
	values Telnyx accepts, and the centre's value where DottorCloud knows it."""
	righe = []
	for tipo in requisiti:
		if (tipo.get("type") or "").lower() not in ("textual", "datetime", "text"):
			continue
		noto = campo_noto(tipo.get("name"))
		ammessi = _valori_ammessi(tipo)
		valore = ""
		if noto and noto[1]:
			valore = dati.get(noto[1]) or ""
		if ammessi and CLIENTE.get(utente) in ammessi:
			valore = CLIENTE[utente]
		righe.append(
			{
				"name": str(tipo.get("id")),
				"label": noto[0] if noto else (tipo.get("name") or str(tipo.get("id"))),
				"known": bool(noto),
				"description": (tipo.get("description") or tipo.get("example") or "")[:300],
				"value": valore,
				"options": ammessi or None,
			}
		)
	return righe


def documenti(requisiti: list[dict]) -> list[dict]:
	"""The document and address requirements as the page's documents: each one a
	file to upload, the address one the office's address."""
	righe = []
	for tipo in requisiti:
		genere = (tipo.get("type") or "").lower()
		if genere not in ("document", "address"):
			continue
		indirizzo = genere == "address"
		noto = None if indirizzo else documento_noto(tipo.get("name"))
		righe.append(
			{
				"requirement": str(tipo.get("id")),
				"description": (tipo.get("description") or "")[:300],
				"accepted": [
					{
						"type": str(tipo.get("id")),
						"label": "The office's address" if indirizzo else (noto or tipo.get("name") or ""),
						"known": indirizzo or bool(noto),
						"address": indirizzo,
						"fields": ["address_sids"] if indirizzo else [],
						"inputs": [],
					}
				],
			}
		)
	return righe


def mancanti(requisiti: list[dict], valori: dict[str, str]) -> list[str]:
	"""The requirements still without a value, by their names: Telnyx takes a group
	for an order only when every one has its value."""
	return [
		tipo.get("name") or str(tipo.get("id"))
		for tipo in requisiti
		if not str(valori.get(str(tipo.get("id"))) or "").strip()
	]


def file_accettato(nome: str | None, dimensione: int | None) -> str:
	"""What is wrong with a document's file for Telnyx in Italy; '' when nothing."""
	estensione = (nome or "").rsplit(".", 1)[-1].lower() if "." in (nome or "") else ""
	if estensione not in ESTENSIONI:
		return "Telnyx takes the documents for Italy as PDF only."
	if (dimensione or 0) > MASSIMO:
		return "The document is larger than 20 MB: Telnyx does not take it."
	return ""


#: An order's state, and a requirement group's, as a request's.
DA_ORDINE = {"pending": IN_VERIFICA, "success": APPROVATA, "failure": RIFIUTATA}
DA_GRUPPO = {
	"unapproved": BOZZA,
	"pending-approval": IN_VERIFICA,
	"approved": APPROVATA,
	"declined": RIFIUTATA,
	"expired": RIFIUTATA,
	"no-longer-eligible": RIFIUTATA,
}


def stato_dell_ordine(stato: str | None) -> str:
	return DA_ORDINE.get((stato or "").strip().lower(), IN_VERIFICA)


def stato_del_gruppo(stato: str | None) -> str:
	return DA_GRUPPO.get((stato or "").strip().lower(), BOZZA)


def prezzo_al_mese(costo: dict | None) -> Decimal | None:
	"""A number's monthly price from Telnyx's search; None when it gave none."""
	try:
		valore = Decimal(str((costo or {}).get("monthly_cost")))
	except (InvalidOperation, TypeError, ValueError):
		return None
	return valore if valore.is_finite() else None


def prefissi(zona: str) -> list[str]:
	"""How Telnyx may write an Italian area's code in its search: with the 0 and
	without it, the first tried first."""
	zona = T.prefisso(zona)
	return [zona, zona.lstrip("0")] if zona else []
