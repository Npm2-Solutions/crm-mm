# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Italian numbers in the centre's Twilio space, without a site (doc 52, second part).

- **The kinds Twilio sells in Italy**, and what each one is for:
  - a mobile (+39 3…) takes calls and SMS, but since 19/11/2025 the AGCOM has calls
    from abroad showing an Italian mobile blocked: not for calling out;
  - a geographic number (02, 06…) calls in and out;
  - a toll-free number (800) only takes calls, and the centre pays each minute.
- **Whose number it is**: a company (srl, sas, a registered firm) or a professional
  in their own name, as invoicing's company says: Twilio asks different documents.
- **The documents** every Italian number wants: Twilio's regulation lists the fields
  of whoever the number is for and the documents that prove them. A field DottorCloud
  knows gets its words and the centre's value (from invoicing's company); the others
  keep Twilio's words. A file is a PDF, JPEG or PNG of 5 MB at most, as Twilio takes.
- **Where the request is**, from Twilio's state of its bundle, and what can be done
  then: send it, wait, buy the number, put the documents right. Approved documents
  are good for more numbers of the same kind - of the same area, for a geographic
  one - so a second number is bought at once.
- **A month's price**, from Twilio's pricing, with its currency.

The words are English, translated where they are shown.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Tipo:
	"""A kind of number, as the page offers it."""

	chiave: str
	#: the name in Twilio's regulations and prices
	twilio: str
	nome: str
	spiegazione: str
	#: may call out showing it
	chiama: bool
	sms: bool
	#: asks the area's prefix
	zona: bool = False


TIPI: dict[str, Tipo] = {
	"mobile": Tipo(
		"mobile",
		"mobile",
		"Mobile number",
		"+39 3…: takes calls and SMS, and the answers to them. Not for calling out: since 19 November 2025 "
		"the AGCOM has calls from abroad showing an Italian mobile blocked.",
		chiama=False,
		sms=True,
	),
	"local": Tipo(
		"local",
		"local",
		"Geographic number",
		"02, 06, 011…: calls in and out. The address on the documents must be in the area of the prefix.",
		chiama=True,
		sms=False,
		zona=True,
	),
	"toll_free": Tipo(
		"toll_free",
		"toll free",
		"Toll-free number",
		"800: only takes calls, free for whoever calls; the centre pays each minute.",
		chiama=False,
		sms=False,
	),
}

#: Whose the number is, in Twilio's words and in the page's.
AZIENDA, PERSONA = "business", "individual"
DI_CHI = {
	AZIENDA: ("A company", "A company or a firm in the business register: srl, sas, snc…"),
	PERSONA: ("A professional", "A professional in their own name, with a VAT number and no company."),
}

#: The fields DottorCloud knows by Twilio's machine name: their words, and where
#: the centre's value comes from (a key of `numeri.dati_del_centro`).
CAMPI_NOTI: dict[str, tuple[str, str | None]] = {
	"business_name": ("Business name", "business_name"),
	"business_registration_number": ("VAT number", "vat_number"),
	"business_registration_identifier": ("Kind of registration number", None),
	"business_identity": ("Kind of business", None),
	"business_type": ("Kind of business", None),
	"business_website": ("Website", "website"),
	"email": ("Email", "email"),
	"phone_number": ("Phone", "phone"),
	"first_name": ("First name", "first_name"),
	"last_name": ("Surname", "last_name"),
	"birth_date": ("Date of birth", None),
	"birth_place": ("Place of birth", None),
	"nationality": ("Nationality", "nationality"),
	"fiscal_code": ("Codice fiscale", "fiscal_code"),
	"tax_code": ("Codice fiscale", "fiscal_code"),
	"vat_number": ("VAT number", "vat_number"),
	"document_number": ("Document number", None),
	"issue_date": ("Issue date", None),
	"expiration_date": ("Expiry date", None),
	"address_sids": ("Address", None),
}

#: The documents a centre has to hand, by Twilio's type, in words.
DOCUMENTI_NOTI: dict[str, str] = {
	"government_issued_document": "Identity document of the legal representative",
	"passport": "Passport of the legal representative",
	"business_registration": "Business register extract (visura camerale)",
	"commercial_registrar_excerpt": "Business register extract (visura camerale)",
	"utility_bill": "A utility bill at the office's address",
	"tax_notice": "A tax notice at the office's address",
	"rent_receipt": "A rent receipt at the office's address",
	"title_deed": "The title deed of the office",
	"address": "The office's address",
}

#: What Twilio takes as a document's file.
ESTENSIONI = ("pdf", "jpg", "jpeg", "png")
MASSIMO = 5 * 1024 * 1024

#: Twilio's states of a bundle, and where the request is.
BOZZA, IN_VERIFICA, APPROVATA, RIFIUTATA = "Draft", "In review", "Approved", "Rejected"
DA_TWILIO = {
	"draft": BOZZA,
	"pending-review": IN_VERIFICA,
	"in-review": IN_VERIFICA,
	"twilio-approved": APPROVATA,
	"provisionally-approved": APPROVATA,
	"twilio-rejected": RIFIUTATA,
}


def stato_della_richiesta(stato_twilio: str | None) -> str:
	"""Where a request is, from its bundle's state; a draft when Twilio has none."""
	return DA_TWILIO.get((stato_twilio or "").strip().lower(), BOZZA)


def si_compra(stato: str) -> bool:
	"""Whether numbers may be bought on a request in this state."""
	return stato == APPROVATA


def si_rimanda(stato: str) -> bool:
	"""Whether the documents of a request may be written and sent again."""
	return stato in (BOZZA, RIFIUTATA)


def di_chi(dati: dict) -> str:
	"""Whose the number is, from what invoicing knows: a professional in their own
	name has a first name and a surname and no company's name."""
	if (dati.get("business_name") or "").strip():
		return AZIENDA
	if (dati.get("first_name") or "").strip() and (dati.get("last_name") or "").strip():
		return PERSONA
	return AZIENDA


def prefisso(valore: str | None) -> str:
	"""An area's prefix as written - "02", "+39 06", "0039 011" - as its digits with
	the 0 in front; "" when it is no Italian area's prefix."""
	cifre = re.sub(r"\D", "", valore or "")
	if cifre.startswith("0039"):
		cifre = cifre[4:]
	elif cifre.startswith("39") and len(cifre) > 2:
		cifre = cifre[2:]
	if not re.fullmatch(r"0\d{1,3}", cifre):
		return ""
	return cifre


def nella_zona(numero: str | None, zona: str | None) -> bool:
	"""Whether a number (E.164) is of an area: its prefix right after +39."""
	zona = prefisso(zona)
	return bool(zona) and (numero or "").startswith("+39" + zona)


def del_tipo(numero: str | None, tipo: str) -> bool:
	"""Whether a number (E.164) looks like a kind's: a mobile starts with 3, a
	geographic number with 0, a toll-free one with 80."""
	resto = (numero or "")[3:] if (numero or "").startswith("+39") else ""
	if tipo == "mobile":
		return resto.startswith("3")
	if tipo == "local":
		return resto.startswith("0")
	if tipo == "toll_free":
		return resto.startswith("80")
	return False


def riusabile(richieste: list[dict], tipo: str, utente: str, zona: str | None = None) -> dict | None:
	"""An approved request whose documents are good for a new number: of the same
	kind and the same owner, of the same area for a geographic one. The newest."""
	for richiesta in richieste or []:
		if richiesta.get("status") != APPROVATA or richiesta.get("number_type") != tipo:
			continue
		if (richiesta.get("end_user_type") or AZIENDA) != utente:
			continue
		if TIPI[tipo].zona and prefisso(richiesta.get("area_code")) != prefisso(zona):
			continue
		return richiesta
	return None


def file_accettato(nome: str | None, dimensione: int | None) -> str:
	"""What is wrong with a document's file, as Twilio takes them; "" when nothing."""
	estensione = (nome or "").rsplit(".", 1)[-1].lower() if "." in (nome or "") else ""
	if estensione not in ESTENSIONI:
		return "The document has to be a PDF, a JPEG or a PNG."
	if (dimensione or 0) > MASSIMO:
		return "The document is larger than 5 MB: Twilio does not take it."
	return ""


def campi_della_regola(campi: list[dict], dati: dict) -> list[dict]:
	"""The fields a regulation asks, as the page draws them: Twilio's machine name,
	the words (DottorCloud's where it knows the field, Twilio's otherwise) and the
	centre's value where there is one. ``campi``: Twilio's `detailed_fields`."""
	disegnati = []
	for campo in campi or []:
		nome = campo.get("machine_name") or ""
		if not nome or nome == "address_sids":
			# an address is asked as an address, not as SIDs
			continue
		parole, fonte = CAMPI_NOTI.get(nome, (None, None))
		disegnati.append(
			{
				"name": nome,
				"label": parole or campo.get("friendly_name") or nome,
				"description": "" if parole else (campo.get("description") or ""),
				"known": bool(parole),
				"value": (dati.get(fonte) or "") if fonte else "",
			}
		)
	return disegnati


def documenti_della_regola(requisiti: list, dati: dict | None = None) -> list[dict]:
	"""The documents a regulation asks, one per requirement: each with the kinds
	that satisfy it (an address, a file), the ones a centre is likely to have first,
	and what each one asks to be written (`inputs`, as `campi_della_regola`).
	``requisiti``: Twilio's `supporting_document`, a list of requirements or of
	lists of them."""
	piatti = []
	for voce in requisiti or []:
		piatti.extend(voce if isinstance(voce, list) else [voce])
	richiesti = []
	for requisito in piatti:
		accettati = []
		for documento in requisito.get("accepted_documents") or []:
			tipo = documento.get("type") or ""
			dettagli = documento.get("detailed_fields") or []
			campi = [c.get("machine_name") for c in dettagli if c.get("machine_name")]
			accettati.append(
				{
					"type": tipo,
					"label": DOCUMENTI_NOTI.get(tipo) or documento.get("name") or tipo,
					"known": tipo in DOCUMENTI_NOTI,
					# only the address: no file to upload
					"address": tipo == "address",
					"fields": campi or list(documento.get("fields") or []),
					"inputs": campi_della_regola(dettagli, dati or {}),
				}
			)
		accettati.sort(key=lambda d: (not d["known"], d["address"]))
		# two of Twilio's kinds DottorCloud calls the same - a visura either way - are one
		visti = set()
		accettati = [d for d in accettati if not (d["label"] in visti or visti.add(d["label"]))]
		richiesti.append(
			{
				"requirement": requisito.get("requirement_name") or requisito.get("name") or "",
				"label": requisito.get("name") or "",
				"description": requisito.get("description") or "",
				"accepted": accettati,
			}
		)
	return richiesti


def chiede_l_indirizzo(documenti: list[dict]) -> bool:
	"""Whether the documents chosen need the office's address."""
	return any("address_sids" in (d.get("fields") or []) for d in documenti or [])


def prezzo_al_mese(prezzi: list[dict], tipo: str) -> Decimal | None:
	"""A month of a kind of number, from Twilio's prices: the current price, else the
	base one; None when Twilio has none for it. ``tipo``: DottorCloud's key."""
	twilio = TIPI[tipo].twilio if tipo in TIPI else tipo
	for prezzo in prezzi or []:
		if (prezzo.get("number_type") or "").lower() == twilio:
			for chiave in ("current_price", "base_price"):
				try:
					return Decimal(str(prezzo[chiave]))
				except (KeyError, InvalidOperation, TypeError):
					continue
	return None


def errori_della_valutazione(risultati: list[dict], parole: dict | None = None) -> list[str]:
	"""What Twilio's evaluation of a bundle found missing or wrong, one line each.
	A field DottorCloud knows is named by ``parole`` (its machine name to its words);
	the rest, and the reasons, are Twilio's own words: they are the only ones that
	name its fields. ``risultati``: the evaluation's `results`, each with `passed`,
	`requirement_friendly_name`, `failure_reason` and the `invalid` fields."""
	parole = parole or {}
	righe = []
	for risultato in risultati or []:
		if risultato.get("passed", True):
			continue
		requisito = risultato.get("requirement_friendly_name") or risultato.get("friendly_name") or ""
		invalidi = risultato.get("invalid") or []
		for campo in invalidi:
			nome = (
				parole.get(campo.get("object_field") or "")
				or campo.get("friendly_name")
				or campo.get("object_field")
				or ""
			)
			motivo = campo.get("failure_reason") or ""
			righe.append(" · ".join(p for p in (requisito, nome, motivo) if p))
		if not invalidi:
			righe.append(" · ".join(p for p in (requisito, risultato.get("failure_reason") or "") if p))
	return [riga for riga in dict.fromkeys(righe) if riga]
