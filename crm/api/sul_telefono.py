# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the phone's own screens read (docs/progetto-ghl/29, the phone).

On a phone a list is not the desk's table squeezed into cards: it is one line
per thing, found by typing, with what one does next. These calls give exactly
that, each in one round trip, through the same permissions as everything else:
`frappe.get_list` applies who reads which person, deal and task, and a person's
email and phone come masked to whoever may not read them.

- **People**: by name, number (written any way: the digits are compared) or
  email, the newest first; with the next appointment for whoever reads the
  agenda. Whoever reads them masked finds them by name only.
- **Tasks**: the open ones, one's own or everybody's, by when they are due, with
  the name of the person or deal they are about.
- **Deals**: the stages of a pipeline with how many open deals each holds, and
  the deals of one stage.
- **Contacts**: a company's people, by name, company, email or a number written
  any way.
- **Companies**: by name, website or industry, with how many deals the session
  reads of each.
- **Calls**: the register, the latest first, with whom each was (the person, else
  the number), which way, whether nobody took it; found by a name or a number
  written any way.
"""

from __future__ import annotations

import frappe
from frappe.utils import cint, now_datetime

from crm.permissions import livelli
from crm.telephony.pannello import persa
from crm.utils import count_field

#: How many rows a page of the phone's lists holds.
PER_PAGINA = 30
#: How many digits of a number are compared, from its end: written with or
#: without its prefix, the same number.
CIFRE = 9
#: Task states that are over.
CHIUSE = ("Done", "Canceled")
#: How many open tasks the phone's list holds at most.
APERTE = 200


def _cifre(testo: str) -> str:
	return "".join(c for c in testo if c.isdigit())


def _pagina(righe: list, start: int) -> dict:
	return {"rows": righe[:PER_PAGINA], "more": len(righe) > PER_PAGINA, "start": start}


# ------------------------------------------------------------------ people


@frappe.whitelist()
def get_people(text: str | None = None, start: int = 0) -> dict:
	"""The people the session reads, newest first; found by name, number or email."""
	livelli.verifica_nel_crm("persone.vedi")
	start = max(cint(start), 0)
	testo = (text or "").strip()
	filtri, o_filtri = {}, None
	# whoever reads people masked (Marketing) finds them by name only: a number
	# or an email typed would tell whose it is
	mascherato = livelli.ambito("persone.vedi") == livelli.MASCHERATO

	cifre = _cifre(testo)
	if testo and cifre and not any(c.isalpha() for c in testo):
		if len(cifre) < 3 or mascherato:
			return _pagina([], start)
		coda = cifre[-CIFRE:]
		# the numbers as written - "+39 340 111 2233" - read as digits only
		candidati = frappe.db.sql(
			"""select name from `tabCRM Lead`
			where replace(replace(replace(replace(coalesce(mobile_no, ''), ' ', ''), '-', ''), '.', ''), '/', '') like %(coda)s
			or replace(replace(replace(replace(coalesce(phone, ''), ' ', ''), '-', ''), '.', ''), '/', '') like %(coda)s
			order by modified desc limit 200""",
			{"coda": f"%{coda}%"},
			pluck=True,
		)
		if not candidati:
			return _pagina([], start)
		filtri = {"name": ["in", candidati]}
	elif testo:
		simile = f"%{testo}%"
		o_filtri = [
			["lead_name", "like", simile],
			["organization", "like", simile],
			["name", "like", simile],
		]
		if not mascherato:
			o_filtri.append(["email", "like", simile])

	righe = frappe.get_list(
		"CRM Lead",
		filters=filtri,
		or_filters=o_filtri,
		fields=[
			"name",
			"lead_name",
			"first_name",
			"image",
			"mobile_no",
			"phone",
			"email",
			"organization",
			"modified",
		],
		order_by="modified desc",
		offset=start,
		limit=PER_PAGINA + 1,
	)
	pagina = _pagina(righe, start)
	if livelli.puo("agenda.vedi"):
		prossimi = _prossimi_appuntamenti([r.name for r in pagina["rows"]])
		for riga in pagina["rows"]:
			riga["next_appointment"] = prossimi.get(riga.name)
	return pagina


def _prossimi_appuntamenti(persone: list[str]) -> dict:
	"""When each of these people comes next: one query for the page."""
	if not persone:
		return {}
	righe = frappe.db.sql(
		"""select p.party, min(a.starts_on)
		from `tabCRM Appointment Participant` p
		join `tabCRM Appointment` a on a.name = p.parent
		where p.parenttype = 'CRM Appointment' and p.party_type = 'CRM Lead'
			and p.party in %(persone)s and a.starts_on >= %(adesso)s
			and a.status not in ('Cancelled', 'No Show')
			and coalesce(p.status, '') != 'Cancelled'
		group by p.party""",
		{"persone": persone, "adesso": now_datetime()},
	)
	return dict(righe)


# ------------------------------------------------------------------ tasks


@frappe.whitelist()
def get_tasks(mine: bool | int | str = True) -> dict:
	"""The open tasks the session reads - one's own, or everybody's - by when
	they are due, the ones without a day last; with whom they are about. Open
	tasks are few: the list comes whole, up to `APERTE`."""
	livelli.verifica_nel_crm("persone.vedi")
	filtri = {"status": ["not in", CHIUSE]}
	if frappe.utils.sbool(mine):
		filtri["assigned_to"] = frappe.session.user
	righe = frappe.get_list(
		"CRM Task",
		filters=filtri,
		fields=[
			"name",
			"title",
			"status",
			"priority",
			"due_date",
			"assigned_to",
			"reference_doctype",
			"reference_docname",
			"modified",
		],
		order_by="modified desc",
		limit=APERTE + 1,
	)
	# the ones due first, the soonest on top; without a day, the latest touched
	righe.sort(key=lambda r: (r.due_date is None, r.due_date or now_datetime()))
	nomi = _nomi_dei_riferimenti(righe[:APERTE])
	for riga in righe[:APERTE]:
		riga["reference_title"] = nomi.get((riga.reference_doctype, riga.reference_docname), "")
	return {"rows": righe[:APERTE], "more": len(righe) > APERTE}


def _nomi_dei_riferimenti(righe) -> dict:
	"""The people and deals the tasks are about, by name: one query each."""
	nomi = {}
	for doctype, campo in (("CRM Lead", "lead_name"), ("CRM Deal", "lead_name")):
		chiavi = [
			r.reference_docname for r in righe if r.reference_doctype == doctype and r.reference_docname
		]
		if not chiavi:
			continue
		campi = ["name", campo] + (["organization"] if doctype == "CRM Deal" else [])
		for r in frappe.get_all(doctype, filters={"name": ["in", chiavi]}, fields=campi):
			nomi[(doctype, r.name)] = r.get(campo) or r.get("organization") or r.name
	return nomi


# ------------------------------------------------------------------ deals


@frappe.whitelist()
def get_deal_stages(pipeline: str | None = None) -> list[dict]:
	"""How many deals the session reads in each stage of a pipeline."""
	livelli.verifica_nel_crm("trattative.vedi")
	filtri = {"pipeline": pipeline} if pipeline else {}
	righe = frappe.get_list(
		"CRM Deal", filters=filtri, fields=["status", count_field()], group_by="status", as_list=True
	)
	return [{"status": stato, "deals": cint(quante)} for stato, quante in righe if stato]


@frappe.whitelist()
def get_deals(status: str, pipeline: str | None = None, start: int = 0) -> dict:
	"""The deals of one stage the session reads, the latest moved first."""
	livelli.verifica_nel_crm("trattative.vedi")
	start = max(cint(start), 0)
	filtri = {"status": status}
	if pipeline:
		filtri["pipeline"] = pipeline
	righe = frappe.get_list(
		"CRM Deal",
		filters=filtri,
		fields=[
			"name",
			"lead_name",
			"organization",
			"deal_value",
			"currency",
			"deal_owner",
			"expected_closure_date",
			"modified",
		],
		order_by="modified desc",
		offset=start,
		limit=PER_PAGINA + 1,
	)
	return _pagina(righe, start)


# ------------------------------------------------------------------ contacts


@frappe.whitelist()
def get_contacts(text: str | None = None, start: int = 0) -> dict:
	"""The contacts the session reads, the latest touched first; found by name,
	company, email or a number written any way."""
	livelli.verifica_nel_crm("persone.vedi")
	start = max(cint(start), 0)
	testo = (text or "").strip()
	filtri, o_filtri = {}, None
	cifre = _cifre(testo)
	if testo and cifre and not any(c.isalpha() for c in testo):
		if len(cifre) < 3:
			return _pagina([], start)
		candidati = frappe.db.sql(
			"""select name from `tabContact`
			where replace(replace(replace(replace(coalesce(mobile_no, ''), ' ', ''), '-', ''), '.', ''), '/', '') like %(coda)s
			or replace(replace(replace(replace(coalesce(phone, ''), ' ', ''), '-', ''), '.', ''), '/', '') like %(coda)s
			order by modified desc limit 200""",
			{"coda": f"%{cifre[-CIFRE:]}%"},
			pluck=True,
		)
		if not candidati:
			return _pagina([], start)
		filtri = {"name": ["in", candidati]}
	elif testo:
		simile = f"%{testo}%"
		o_filtri = [
			["full_name", "like", simile],
			["company_name", "like", simile],
			["email_id", "like", simile],
		]
	righe = frappe.get_list(
		"Contact",
		filters=filtri,
		or_filters=o_filtri,
		fields=[
			"name",
			"full_name",
			"first_name",
			"image",
			"email_id",
			"mobile_no",
			"phone",
			"company_name",
			"modified",
		],
		order_by="modified desc",
		offset=start,
		limit=PER_PAGINA + 1,
	)
	return _pagina(righe, start)


# ------------------------------------------------------------------ companies


@frappe.whitelist()
def get_organizations(text: str | None = None, start: int = 0) -> dict:
	"""The companies the session reads, the latest touched first; found by name,
	website or industry; each with how many of its deals the session reads."""
	livelli.verifica_nel_crm("persone.vedi")
	start = max(cint(start), 0)
	testo = (text or "").strip()
	o_filtri = None
	if testo:
		simile = f"%{testo}%"
		o_filtri = [
			["organization_name", "like", simile],
			["website", "like", simile],
			["industry", "like", simile],
		]
	righe = frappe.get_list(
		"CRM Organization",
		or_filters=o_filtri,
		fields=["name", "organization_name", "organization_logo", "website", "industry", "modified"],
		order_by="modified desc",
		offset=start,
		limit=PER_PAGINA + 1,
	)
	pagina = _pagina(righe, start)
	if pagina["rows"] and livelli.puo("trattative.vedi"):
		quante = frappe.get_list(
			"CRM Deal",
			filters={"organization": ["in", [r.name for r in pagina["rows"]]]},
			fields=["organization", count_field()],
			group_by="organization",
			as_list=True,
		)
		quante = {azienda: cint(numero) for azienda, numero in quante}
		for riga in pagina["rows"]:
			riga["deals"] = quante.get(riga.name, 0)
	return pagina


# ------------------------------------------------------------------ calls


@frappe.whitelist()
def get_calls(text: str | None = None, start: int = 0) -> dict:
	"""The register of calls the session reads, the latest first; found by the
	name of whom they were with or by a number written any way."""
	livelli.verifica_nel_crm("telefono.registro")
	start = max(cint(start), 0)
	testo = (text or "").strip()
	filtri = {}
	cifre = _cifre(testo)
	if testo and cifre and not any(c.isalpha() for c in testo):
		if len(cifre) < 3:
			return _pagina([], start)
		# the numbers as the carrier or a hand wrote them, read as digits only
		candidate = frappe.db.sql(
			"""select name from `tabCRM Call Log`
			where replace(replace(replace(replace(coalesce(`from`, ''), ' ', ''), '-', ''), '.', ''), '/', '') like %(coda)s
			or replace(replace(replace(replace(coalesce(`to`, ''), ' ', ''), '-', ''), '.', ''), '/', '') like %(coda)s
			order by creation desc limit 500""",
			{"coda": f"%{cifre[-CIFRE:]}%"},
			pluck=True,
		)
		if not candidate:
			return _pagina([], start)
		filtri = {"name": ["in", candidate]}
	elif testo:
		simile = f"%{testo}%"
		con_chi = frappe.get_list(
			"CRM Lead", filters={"lead_name": ["like", simile]}, pluck="name", limit=200
		) + frappe.get_list("CRM Deal", filters={"lead_name": ["like", simile]}, pluck="name", limit=200)
		if not con_chi:
			return _pagina([], start)
		filtri = {"reference_docname": ["in", con_chi]}

	righe = frappe.get_list(
		"CRM Call Log",
		filters=filtri,
		fields=[
			"name",
			"type",
			"status",
			"from",
			"to",
			"start_time",
			"creation",
			"duration",
			"reference_doctype",
			"reference_docname",
			"left_message",
			"callback_status",
		],
		order_by="creation desc",
		offset=start,
		limit=PER_PAGINA + 1,
	)
	pagina = _pagina(righe, start)
	nomi = _nomi_dei_riferimenti(pagina["rows"])
	pagina["rows"] = [
		frappe._dict(
			name=r.name,
			type=r.type,
			status=r.status,
			missed=persa(r),
			left_message=bool(r.left_message),
			number=r.get("from") if r.type == "Incoming" else r.get("to"),
			when=str(r.start_time or r.creation),
			duration=r.duration,
			person=nomi.get((r.reference_doctype, r.reference_docname)),
			reference_doctype=r.reference_doctype,
			reference_docname=r.reference_docname,
			callback_status=r.callback_status,
		)
		for r in pagina["rows"]
	]
	return pagina
