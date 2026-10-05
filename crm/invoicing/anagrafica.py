# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""One fiscal profile per person, read by the invoice and completed by it.

The rules are in `crm.invoicing.engine.anagrafica`; this is where they meet the
records: whose profile an invoice uses, the two directions (a new invoice takes, a
confirmed one gives back), and the two calls behind the "Billing details" panel on
the person's page.

**Whose profile.** The invoice's record says it: a person or an organization is
itself; a contact is the person it belongs to; a deal is its organization when the
invoice goes to a company or an office, and its person when it goes to a person.

**Made out to whoever pays.** A child's visit goes to the parent who pays for them,
when the desk has said one does (`crm.persone`): their profile, their name, and the
child's name in the causale. The details come back to whichever of the two the
confirmed invoice names.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.invoicing.doctype.crm_billing_profile.crm_billing_profile import TITOLARI
from crm.invoicing.engine import anagrafica as motore
from crm.invoicing.engine.codici import TipoDestinatario
from crm.permissions import livelli

DOCTYPE = "CRM Billing Profile"

#: The names the invoice writes on a person, compared with theirs before giving back.
_NOMI = ("first_name", "last_name")


def titolare_di(party_type: str | None, party: str | None, recipient_type: str | None = None):
	"""``(doctype, name)`` of the profile an invoice to this record uses, or ``None``."""
	if not (party_type and party):
		return None
	if party_type in TITOLARI:
		return party_type, party
	if party_type == "Contact":
		persona = frappe.db.get_value("CRM Lead", {"contact": party}, "name")
		return ("CRM Lead", persona) if persona else None
	if party_type == "CRM Deal":
		trattativa = frappe.db.get_value("CRM Deal", party, ["lead", "organization"], as_dict=True)
		if not trattativa:
			return None
		a_una_persona = (recipient_type or TipoDestinatario.PERSONA_FISICA) == TipoDestinatario.PERSONA_FISICA
		if trattativa.organization and not a_una_persona:
			return "CRM Organization", trattativa.organization
		return ("CRM Lead", trattativa.lead) if trattativa.lead else None
	return None


def intestatario_di(fattura):
	"""``(doctype, name)`` of whom the invoice is made out to: the client, or the one
	person who pays for them.

	Whoever pays, unless the invoice already names the client - their name or their
	codice fiscale, written at the desk: then it is theirs, and nothing of the
	parent's is mixed into it.
	"""
	titolare = titolare_di(fattura.get("party_type"), fattura.get("party"), fattura.get("recipient_type"))
	tipo = fattura.get("recipient_type") or TipoDestinatario.PERSONA_FISICA
	if not titolare or titolare[0] != "CRM Lead" or tipo != TipoDestinatario.PERSONA_FISICA:
		return titolare
	from crm.persone.collegate import pagante_di

	pagante = pagante_di(titolare[1])
	if not pagante or _nomina(fattura, titolare[1]):
		return titolare
	return "CRM Lead", pagante


def _nomina(fattura, persona: str) -> bool:
	"""The invoice already names this person: their codice fiscale, or their name."""
	codice = (fattura.get("fiscal_code") or "").strip().upper()
	if codice:
		return codice == (
			frappe.db.get_value(DOCTYPE, {"party_type": "CRM Lead", "party": persona}, "fiscal_code") or ""
		)
	scritto = " ".join(p for p in (fattura.get("first_name"), fattura.get("last_name")) if p) or fattura.get(
		"billing_name"
	)
	if not scritto:
		return False
	nomi = frappe.db.get_value("CRM Lead", persona, list(_NOMI), as_dict=True) or {}
	return motore.stessa_persona({"first_name": scritto}, nomi)


def pagante_della_fattura(fattura) -> str | None:
	"""The person who pays for the invoice's client, when it is made out to them."""
	titolare = titolare_di(fattura.get("party_type"), fattura.get("party"), fattura.get("recipient_type"))
	intestatario = intestatario_di(fattura)
	return intestatario[1] if intestatario and intestatario != titolare else None


def causale_per_conto(fattura) -> str | None:
	"""Whom the service was for, on an invoice made out to whoever pays for them.

	The document goes to the parent; the deduction and the patient's own records
	need to know it was the child's visit.
	"""
	titolare = titolare_di(fattura.party_type, fattura.party, fattura.recipient_type)
	if not titolare or titolare[0] != "CRM Lead":
		return None
	nome = frappe.db.get_value("CRM Lead", titolare[1], "lead_name")
	if not nome:
		return None
	codice = frappe.db.get_value(DOCTYPE, {"party_type": "CRM Lead", "party": titolare[1]}, "fiscal_code")
	return f"Prestazione resa a {nome}, codice fiscale {codice}" if codice else f"Prestazione resa a {nome}"


def nome_del_profilo(party_type: str, party: str) -> str | None:
	return frappe.db.get_value(DOCTYPE, {"party_type": party_type, "party": party})


def cancella_con_il_titolare(doc, method=None) -> None:
	"""A person or an organization was deleted: their billing details go with them.

	They are part of the record, not a document linked to it. Left behind they
	would stop the deletion - Frappe refuses to delete what something still points
	at - and a right to be forgotten that stops at the codice fiscale is not one.
	"""
	for nome in frappe.get_all(DOCTYPE, filters={"party_type": doc.doctype, "party": doc.name}, pluck="name"):
		frappe.delete_doc(DOCTYPE, nome, ignore_permissions=True, force=True)


def compila_fattura(fattura) -> None:
	"""Fill what the invoice has left empty from its client's profile - or from the
	profile of whoever pays for them."""
	intestatario = intestatario_di(fattura)
	if not intestatario:
		return
	profilo = frappe.db.get_value(
		DOCTYPE, {"party_type": intestatario[0], "party": intestatario[1]}, list(motore.CAMPI), as_dict=True
	)
	if not profilo:
		return
	valori_fattura = {campo: fattura.get(campo) for campo in (*motore.CAMPI, "recipient_type")}
	for campo, valore in motore.da_compilare(valori_fattura, profilo).items():
		fattura.set(campo, valore)


def completa_da_fattura(fattura) -> str | None:
	"""Give a confirmed invoice's data back to its client's profile, where it is empty.

	Never raises: an invoice that cannot be issued because a profile could not be
	updated would be a strange thing to explain at the desk. A failure is logged and
	the invoice goes on.
	"""
	try:
		frappe.db.savepoint("anagrafica_fiscale")
		return _completa(fattura)
	except Exception:
		frappe.db.rollback(save_point="anagrafica_fiscale")
		frappe.log_error(
			title=_("Billing details not completed from invoice {0}").format(fattura.name),
			reference_doctype=fattura.doctype,
			reference_name=fattura.name,
		)
		return None


def _completa(fattura) -> str | None:
	titolare = titolare_di(fattura.party_type, fattura.party, fattura.recipient_type)
	if not titolare or not frappe.db.exists(*titolare):
		return None
	party_type, party = titolare
	valori_fattura = {campo: fattura.get(campo) for campo in (*motore.CAMPI, "recipient_type", *_NOMI)}
	if party_type == "CRM Lead" and fattura.recipient_type == TipoDestinatario.PERSONA_FISICA:
		# made out to the person, or to the parent who pays for them: the details
		# go back to whichever of the two the invoice names, and to nobody when it
		# names somebody else - their codice fiscale is not this person's
		intestatario = intestatario_di(fattura)
		candidati = dict.fromkeys(p for p in (intestatario and intestatario[1], party) if p)
		for candidato in candidati:
			persona = frappe.db.get_value("CRM Lead", candidato, list(_NOMI), as_dict=True) or {}
			if motore.stessa_persona(valori_fattura, persona):
				party = candidato
				break
		else:
			return None

	nome = nome_del_profilo(party_type, party)
	profilo = frappe.get_doc(DOCTYPE, nome) if nome else frappe.new_doc(DOCTYPE)
	if not nome:
		profilo.party_type, profilo.party = party_type, party

	nuovi = motore.da_completare(profilo.as_dict(), valori_fattura)
	# what the profile would refuse stays on the invoice alone: a malformed value
	# from an old document is not a reason to lose the good ones beside it
	sbagliati = set(motore.errori(motore.normalizza({**profilo.as_dict(), **nuovi})))
	nuovi = {campo: valore for campo, valore in nuovi.items() if campo not in sbagliati}
	if sbagliati & set(motore.INDIRIZZO):
		nuovi = {campo: valore for campo, valore in nuovi.items() if campo not in motore.INDIRIZZO}
	if not nuovi:
		return None

	profilo.update(nuovi)
	profilo.filled_from_invoice = fattura.name
	profilo.flags.ignore_permissions = True
	profilo.save()
	return profilo.name


# ------------------------------------------------------------------- the panel


def _verifica(party_type: str, party: str) -> None:
	if party_type not in TITOLARI:
		frappe.throw(_("Billing details belong to a person or an organization"))
	livelli.verifica_nel_crm("persone.dati_fiscali")
	frappe.has_permission(party_type, "read", doc=party, throw=True)


def _sesso(genere: str | None) -> str | None:
	"""The CRM's Gender, in the codice fiscale's terms: M, F or unknown."""
	return {"male": "M", "female": "F"}.get((genere or "").strip().lower())


def avvisi(profilo) -> list[str]:
	"""What looks wrong without being wrong: said, never blocked.

	The codice fiscale that contradicts the person it is filed under - the swapped
	patient, the most expensive mistake there is - and the same codice fiscale on
	another record, which is usually the same person twice.
	"""
	messaggi: list[str] = []
	if not profilo.fiscal_code:
		return messaggi
	if profilo.party_type == "CRM Lead":
		persona = frappe.db.get_value(
			"CRM Lead", profilo.party, ["first_name", "last_name", "gender"], as_dict=True
		)
		if persona:
			frasi = {
				"cognome": _("The codice fiscale does not match the surname {0}").format(persona.last_name),
				"nome": _("The codice fiscale does not match the first name {0}").format(persona.first_name),
				"sesso": _("The codice fiscale does not match the sex recorded for this person"),
			}
			for chiave in motore.incoerenze(
				profilo.fiscal_code,
				cognome=persona.last_name,
				nome=persona.first_name,
				sesso=_sesso(persona.gender),
			):
				messaggi.append(frasi[chiave])

	for altro in frappe.get_all(
		DOCTYPE,
		filters={"fiscal_code": profilo.fiscal_code, "name": ("!=", profilo.name or "")},
		fields=["party_type", "party", "party_name"],
		limit=3,
	):
		if frappe.has_permission(altro.party_type, "read", doc=altro.party):
			messaggi.append(_("The same codice fiscale is on {0}").format(altro.party_name or altro.party))
		else:
			messaggi.append(_("The same codice fiscale is on another record"))
	return messaggi


def _risposta(party_type: str, party: str) -> dict:
	nome = nome_del_profilo(party_type, party)
	if nome:
		profilo = frappe.get_doc(DOCTYPE, nome)
		profilo.check_permission("read")
		puo_scrivere = bool(profilo.has_permission("write"))
	else:
		profilo = frappe.new_doc(DOCTYPE)
		profilo.party_type, profilo.party = party_type, party
		frappe.has_permission(DOCTYPE, "read", throw=True)
		puo_creare = frappe.has_permission(DOCTYPE, "create")
		puo_scrivere = bool(puo_creare)
	return {
		"name": nome,
		"values": {campo: profilo.get(campo) for campo in motore.CAMPI},
		"birth_date": profilo.birth_date,
		"sex": profilo.sex,
		"warnings": avvisi(profilo),
		"can_write": puo_scrivere,
	}


@frappe.whitelist()
def get_billing_profile(party_type: str, party: str) -> dict:
	"""The billing details of a person or an organization, for their page."""
	_verifica(party_type, party)
	return _risposta(party_type, party)


@frappe.whitelist(methods=["POST"])
def save_billing_profile(party_type: str, party: str, values: dict | str) -> dict:
	"""Write some billing details; the profile is created with the first of them."""
	_verifica(party_type, party)
	valori = frappe.parse_json(values) if isinstance(values, str) else (values or {})
	nome = nome_del_profilo(party_type, party)
	profilo = frappe.get_doc(DOCTYPE, nome) if nome else frappe.new_doc(DOCTYPE)
	if not nome:
		profilo.party_type, profilo.party = party_type, party
	profilo.update({campo: valore for campo, valore in valori.items() if campo in motore.CAMPI})
	profilo.save()
	return _risposta(party_type, party)
