# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who reads what the others wrote: the dossier, obscuring, the opening with a reason.

The Garante's guidelines on the health dossier (4/6/2015), as doc 30 puts them:

- **The dossier** exists only with the patient's consent. With it, the
  practitioners who have the patient in care read the whole record, not only
  their own visits; without it, each one reads their own. The medical director
  reads everything.
- **Obscuring**: the patient can ask that an episode (a visit, with its addenda
  and its reports; or one of the person's documents) is not in the dossier. The
  medical director does it, and can undo it. An obscured episode stays readable
  by who wrote or added it, and by the medical director; the others do not see
  it at all - not a padlock, not a count, not the source of a line of the summary
  - because they must not be able to tell that something was obscured.
- **A discipline**: an entry can be for the colleagues of one's own discipline
  (the qualification of their provider record), not the whole care team.
- **Out of the care team**: a practitioner who needs the record of somebody not
  in their care opens it writing why. For a day the person is theirs (the
  dossier's rules still apply); the opening and its reason are in the access log,
  for the manager and the medical director to see.
"""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, get_fullname, now_datetime

from crm.permissions import livelli

DOSSIER = "health_dossier"
TUTTI, DISCIPLINA, SOLO_IO = "Care team", "My discipline", "Only me"
VISIBILITA = (TUTTI, DISCIPLINA, SOLO_IO)
VOCE, DOCUMENTO = "Clinic Record", "CRM Document"
CONCESSIONE = "Clinic Access Grant"
#: How long an opening out of the care team lasts.
ORE_FUORI_EQUIPE = 24


# ------------------------------------------------------------------ the rules


def col_dossier(lead: str) -> bool:
	# the register keeps one "Given" row per consent at most, and it is the current one
	return bool(frappe.db.exists("CRM Consent", {"lead": lead, "consent_type": DOSSIER, "status": "Given"}))


def disciplina_di(user: str) -> str | None:
	"""A practitioner's discipline: the qualification of their provider record."""
	return frappe.db.get_value("CRM Service Provider", {"user": user, "enabled": 1}, "qualification")


def vede_gli_oscurati(user: str | None = None) -> bool:
	"""The medical director, who obscures and reveals."""
	return livelli.ambito("clinica.vedi", user or frappe.session.user) == livelli.CENTRO


def legge_le_altre(doc, user: str | None = None) -> bool:
	"""Whether ``user`` reads an entry or a document somebody else wrote or added."""
	user = user or frappe.session.user
	ambito = livelli.ambito("clinica.vedi", user)
	if not ambito:
		return False
	if ambito == livelli.CENTRO:
		return doc.get("visibility") != SOLO_IO
	if cint(doc.get("obscured")) or doc.get("visibility") == SOLO_IO:
		return False
	if doc.get("visibility") == DISCIPLINA and (
		not doc.get("discipline") or doc.get("discipline") != disciplina_di(user)
	):
		return False
	# the dossier: with the consent, and for the people in their care
	return col_dossier(doc.get("lead")) and bool(
		frappe.has_permission("CRM Lead", "read", doc=doc.get("lead"), user=user)
	)


def condizione_condivisa(tabella, user: str):
	"""The same rule for a list: the rows of ``tabella`` ``user`` reads though they
	are somebody else's, or None when there are none."""
	ambito = livelli.ambito("clinica.vedi", user)
	if not ambito:
		return None
	condizione = tabella.visibility != SOLO_IO
	if ambito == livelli.CENTRO:
		return condizione
	from crm.permissions import org_hierarchy

	condizione = condizione & (tabella.obscured == 0)
	disciplina = disciplina_di(user)
	condizione = condizione & (
		(tabella.visibility == TUTTI)
		| ((tabella.visibility == DISCIPLINA) & (tabella.discipline == disciplina))
		if disciplina
		else tabella.visibility == TUTTI
	)
	consenso = frappe.qb.DocType("CRM Consent")
	condizione = condizione & tabella.lead.isin(
		frappe.qb.from_(consenso)
		.select(consenso.lead)
		.where((consenso.consent_type == DOSSIER) & (consenso.status == "Given"))
	)
	visibili = org_hierarchy.visible_leads(user)
	if visibili is not None:
		condizione = condizione & tabella.lead.isin(visibili)
	return condizione


def e_sanitario(doc) -> bool:
	"""What a health professional writes, or what is for one, is health data whatever
	its kind - a nutritionist's habits too. With the clinic on."""
	from crm.clinica.paziente import clinica_accesa

	qualifica = doc.get("discipline")
	return bool(
		qualifica
		and clinica_accesa()
		and frappe.db.get_value("CRM Professional Qualification", qualifica, "is_healthcare")
	)


def lettore():
	"""The clinic's reader of what carries the mark of health data in the CRM (a plan,
	a programme, a document): the dossier's rules, and the mark by who wrote it."""
	from crm.permissions import sanitari

	return sanitari.Lettore(legge=legge_le_altre, condizione=condizione_condivisa, marca=e_sanitario)


def fonti_nascoste(fonti: list[tuple[str, str]], user: str | None = None) -> set[tuple[str, str]]:
	"""Of these entries and documents, the obscured ones ``user`` must not know of."""
	user = user or frappe.session.user
	if vede_gli_oscurati(user):
		return set()
	nascoste = set()
	for doctype, autore in ((VOCE, "practitioner"), (DOCUMENTO, "added_by")):
		nomi = [nome for tipo, nome in fonti if tipo == doctype]
		if not nomi:
			continue
		for riga in frappe.get_all(
			doctype,
			filters={"name": ("in", nomi), "obscured": 1},
			fields=["name", "practitioner", autore],
		):
			if user not in (riga.practitioner, riga.get(autore)):
				nascoste.add((doctype, riga.name))
	return nascoste


# ------------------------------------------------------------------ obscuring


def _episodio(doctype: str, nome: str) -> list[tuple[str, str]]:
	"""What obscuring an entry covers: a visit with its addenda and their reports
	among the person's documents; a document alone."""
	if doctype == DOCUMENTO:
		return [(DOCUMENTO, nome)]
	radice = frappe.db.get_value(VOCE, nome, "addendum_to") or nome
	voci = [radice, *frappe.get_all(VOCE, filters={"addendum_to": radice}, pluck="name")]
	documenti = frappe.get_all(DOCUMENTO, filters={"record": ("in", voci)}, pluck="name")
	return [(VOCE, voce) for voce in voci] + [(DOCUMENTO, documento) for documento in documenti]


def _imposta(doctype: str, name: str, oscura: bool, note: str | None) -> dict:
	from crm.moduli import traccia

	if doctype not in (VOCE, DOCUMENTO):
		frappe.throw(_("Only a visit or a person's document is obscured"))
	livelli.verifica("clinica.oscura")
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	if doctype == VOCE and doc.docstatus != 1:
		frappe.throw(_("A draft is its author's alone: there is nothing to obscure yet"))
	if doctype == DOCUMENTO and doc.get("record"):
		frappe.throw(_("A report is obscured with its visit"))
	adesso = now_datetime()
	parti = _episodio(doctype, name)
	for tipo, nome in parti:
		frappe.db.set_value(
			tipo,
			nome,
			{
				"obscured": 1 if oscura else 0,
				"obscured_by": frappe.session.user if oscura else None,
				"obscured_on": adesso if oscura else None,
			},
			update_modified=False,
		)
		# the patient's request, its reason if one was written, who did it and when
		traccia.traccia(tipo, nome, "obscured" if oscura else "revealed", (note or "").strip() or None)
	return {"obscured": oscura, "entries": len(parti)}


@frappe.whitelist(methods=["POST"])
def obscure(doctype: str, name: str, note: str | None = None) -> dict:
	"""At the patient's request: the episode leaves the dossier."""
	return _imposta(doctype, name, True, note)


@frappe.whitelist(methods=["POST"])
def reveal(doctype: str, name: str, note: str | None = None) -> dict:
	"""The patient changed their mind: the episode is back in the dossier."""
	return _imposta(doctype, name, False, note)


# ------------------------------------------------------------------ out of the care team


def _codice_fiscale(testo: str) -> bool:
	return bool(re.fullmatch(r"[A-Za-z0-9]{16}", testo))


@frappe.whitelist()
def find_out_of_care(query: str) -> list[dict]:
	"""Somebody not in the session's care, by tax code or by name and surname as
	they are written: a handful of exact matches, never a browse of the centre."""
	livelli.verifica("clinica.fuori_equipe")
	testo = " ".join((query or "").split())
	if len(testo) < 5:
		return []
	persone: list[str] = []
	if _codice_fiscale(testo):
		persone += frappe.get_all(
			"CRM Billing Profile",
			filters={"party_type": "CRM Lead", "fiscal_code": testo.upper()},
			pluck="party",
			limit=5,
		)
	persone += frappe.get_all("CRM Lead", filters={"lead_name": testo}, pluck="name", limit=5)
	righe = []
	for nome in dict.fromkeys(persone):
		in_cura = frappe.has_permission("CRM Lead", "read", doc=nome)
		righe.append(
			{
				"name": nome,
				"lead_name": frappe.db.get_value("CRM Lead", nome, "lead_name"),
				"in_care": bool(in_cura),
			}
		)
	return righe[:5]


@frappe.whitelist(methods=["POST"])
def open_out_of_care(lead: str, reason: str) -> dict:
	"""The person is the session's for a day, and the access log says why."""
	livelli.verifica("clinica.fuori_equipe")
	motivo = " ".join((reason or "").split())
	if len(motivo) < 10:
		frappe.throw(_("Write why you open this record: a sentence, which the access log keeps"))
	if not frappe.db.exists("CRM Lead", lead):
		frappe.throw(_("There is no such person"))
	adesso = now_datetime()
	concessione = frappe.get_doc(
		{
			"doctype": CONCESSIONE,
			"user": frappe.session.user,
			"lead": lead,
			"reason": motivo,
			"granted_on": adesso,
			"expires_on": add_to_date(adesso, hours=ORE_FUORI_EQUIPE),
		}
	).insert(ignore_permissions=True)
	return {"name": concessione.name, "lead": lead, "expires_on": concessione.expires_on}


def aperti_con_motivo(user: str):
	"""`crm_people_in_care`: the people ``user`` opened out of their care, while it
	lasts."""
	from crm.clinica import paziente

	if not paziente.clinica_accesa():
		return None
	concessione = frappe.qb.DocType(CONCESSIONE).as_("_fuori_equipe")
	return (
		frappe.qb.from_(concessione)
		.select(concessione.lead)
		.where((concessione.user == user) & (concessione.expires_on > now_datetime()))
	)


def apertura_in_corso(lead: str, user: str | None = None) -> dict | None:
	"""The session's opening of this person, while it lasts: shown on the Clinic tab."""
	riga = frappe.get_all(
		CONCESSIONE,
		filters={
			"user": user or frappe.session.user,
			"lead": lead,
			"expires_on": (">", now_datetime()),
		},
		fields=["reason", "granted_on", "expires_on"],
		order_by="expires_on desc",
		limit=1,
	)
	return riga[0] if riga else None


def aperture(lead: str) -> list[dict]:
	"""The openings out of the care team, for the access log: who, when, why."""
	return [
		frappe._dict(
			viewed_by=riga.user,
			viewed_by_name=get_fullname(riga.user),
			creation=riga.granted_on,
			kind="out_of_care",
			reason=riga.reason,
			count=1,
		)
		for riga in frappe.get_all(
			CONCESSIONE,
			filters={"lead": lead},
			fields=["user", "reason", "granted_on"],
			order_by="granted_on desc",
			limit=100,
		)
	]
