# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Dental care plans on the person's page (docs/gestionale-medico, phase 3: "piani di
cura (odontoiatria)"); the rules without a site are `cure_regole`.

- **The chart** (`Clinic Dental Chart`, one per person): what each tooth is now, one
  row per condition. Written by the dentists (`cure.scrivi` and a dentist's
  qualification), read like the record: who started it, and the others with the
  dossier. Its changes stay in its history; every opening goes in the access log.
- **The plan** (`Clinic Care Plan`) is a quote first. Its dentist writes the
  treatments - a service, maybe on a tooth and its surfaces, in phases - priced
  from the price list, with a discount. A draft is theirs alone.
- **Proposed**, it is frozen: its quote is made as a PDF to hand over, and the
  person's deal in the quotes pipeline goes to "quote delivered". The desk
  (`cure.preventivi`) reads it from then on and records it accepted - how, in a few
  words - or declined, and why: the deal is won or lost.
- **Accepted**, it is done treatment by treatment: an appointment of a treatment's
  service for the person takes the first one still to do, at the price agreed -
  the ones already booked too - and when the person came, it is done. A
  cancellation or a no-show gives it back. Every treatment done or cancelled, the
  plan is completed.
- **A new version** starts from a plan as a draft with its treatments: after a
  quote declined, or to change one.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, formatdate, get_fullname, getdate, now_datetime, nowdate

from crm.clinica import cure_regole as R
from crm.clinica import dossier, paziente
from crm.permissions import livelli, org_hierarchy

CARTELLA = "Clinic Dental Chart"
PIANO = "Clinic Care Plan"
VOCE = "Clinic Care Plan Item"
APPUNTAMENTO = "CRM Appointment"
PARTECIPANTE = "CRM Appointment Participant"
#: How long a quote holds, unless the dentist says otherwise.
GIORNI_VALIDITA = 60
#: What a treatment keeps from the editor; the rest is the plan's to decide.
CAMPI_VOCE = ("service", "description", "tooth", "surfaces", "phase", "qty", "rate", "discount")
MODELLO_PREVENTIVO = "crm/clinica/templates/preventivo.html"


# ------------------------------------------------------------------ who


def dentista(user: str | None = None) -> bool:
	"""Whether ``user`` writes charts and plans: the capability, and a dentist's
	qualification on their provider record."""
	user = user or frappe.session.user
	return livelli.puo("cure.scrivi", user) and R.scrive(dossier.disciplina_di(user))


def _preventivi(user: str | None = None) -> bool:
	return livelli.puo("cure.preventivi", user or frappe.session.user)


def _sql(condizione) -> str:
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def puo_leggere_cartella(doc, user: str | None = None) -> bool:
	"""Who started it; the others like the record, with the dossier."""
	user = user or frappe.session.user
	return doc.get("practitioner") == user or dossier.legge_le_altre(doc, user)


def has_chart_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return dentista(user)
	if ptype == "write":
		return dentista(user) and puo_leggere_cartella(doc, user)
	if ptype in ("delete", "submit", "cancel", "amend"):
		return False
	return puo_leggere_cartella(doc, user)


def get_chart_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	cartella = frappe.qb.DocType(CARTELLA)
	condizione = cartella.practitioner == user
	condivisa = dossier.condizione_condivisa(cartella, user)
	if condivisa is not None:
		condizione = condizione | condivisa
	return _sql(condizione)


def puo_leggere_piano(doc, user: str | None = None) -> bool:
	"""Its dentist, always. Proposed, the desk that handles quotes for the people it
	sees, and the other practitioners like the record."""
	user = user or frappe.session.user
	if doc.get("practitioner") == user:
		return True
	if doc.get("status") == R.BOZZA:
		return False
	if _preventivi(user) and frappe.has_permission("CRM Lead", "read", doc=doc.get("lead"), user=user):
		return True
	return dossier.legge_le_altre(doc, user)


def has_plan_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return dentista(user)
	if ptype in ("write", "delete"):
		# a draft is its dentist's; what is proposed goes on through its own calls
		return doc.get("practitioner") == user and doc.get("status") == R.BOZZA
	if ptype in ("submit", "cancel", "amend"):
		return False
	return puo_leggere_piano(doc, user)


def get_plan_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	piano = frappe.qb.DocType(PIANO)
	condizione = piano.practitioner == user
	condivisa = dossier.condizione_condivisa(piano, user)
	if condivisa is not None:
		condizione = condizione | ((piano.status != R.BOZZA) & condivisa)
	if _preventivi(user):
		visibili = org_hierarchy.visible_leads(user)
		persone = piano.lead.isin(visibili) if visibili is not None else piano.lead.isnotnull()
		condizione = condizione | ((piano.status != R.BOZZA) & persone)
	return _sql(condizione)


def _legge() -> bool:
	return livelli.puo("clinica.vedi") or livelli.puo("cure.scrivi") or _preventivi()


def _della_persona(lead: str) -> None:
	if not _legge():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _piano(name: str):
	doc = frappe.get_doc(PIANO, name)
	frappe.has_permission("CRM Lead", "read", doc=doc.lead, throw=True)
	if not puo_leggere_piano(doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc


def _mio(name: str, stato: str | None = None):
	doc = _piano(name)
	if doc.practitioner != frappe.session.user:
		frappe.throw(_("A care plan is changed by the dentist who wrote it"), frappe.PermissionError)
	if stato and doc.status != stato:
		frappe.throw(_("This care plan is {0}: it does not go that way").format(_(doc.status)))
	return doc


def _problemi(problemi: list) -> None:
	if problemi:
		frappe.throw("<br>".join(p.testo(_) for p in problemi))


# ------------------------------------------------------------------ the sums


def _nome_del_servizio(servizio: str | None) -> str | None:
	if not servizio:
		return None
	return frappe.db.get_value("CRM Service", servizio, "service_name") or servizio


def calcola(doc) -> None:
	"""`validate` of a plan: each treatment's amount, and the plan's sums."""
	if not doc.currency:
		doc.currency = (
			frappe.db.get_value("CRM Price List", doc.price_list, "currency") if doc.price_list else None
		) or "EUR"
	for voce in doc.items:
		voce.phase = max(cint(voce.phase), 1)
		voce.qty = flt(voce.qty) or 1
		voce.discount = min(max(flt(voce.discount), 0), 100)
		voce.amount = R.importo(voce.qty, voce.rate, voce.discount)
		voce.currency = doc.currency
		voce.status = voce.status or R.DA_FARE
		if voce.tooth and R.e_dente(voce.tooth):
			voce.tooth = str(int(voce.tooth))
		voce.surfaces = (R.superfici(voce.surfaces) or None) if voce.tooth else None
		voce.description = (voce.description or "").strip() or _nome_del_servizio(voce.service)
	somme = R.totali([voce.as_dict() for voce in doc.items])
	doc.total_gross = somme["gross"]
	doc.total_discount = somme["discount"]
	doc.total_net = somme["net"]
	doc.total_done = somme["done"]


# ------------------------------------------------------------------ reading


def _cartella(doc) -> dict:
	return {
		"name": doc.name,
		"dentition": doc.dentition or R.PERMANENTE,
		"teeth": [
			{
				"tooth": riga.tooth,
				"condition": riga.condition,
				"surfaces": riga.surfaces or "",
				"note": riga.note or "",
				"noted_on": str(riga.noted_on) if riga.noted_on else None,
				"noted_by_name": get_fullname(riga.noted_by) if riga.noted_by else None,
			}
			for riga in doc.teeth
		],
		"notes": doc.notes,
		"updated_on": str(doc.updated_on) if doc.updated_on else None,
		"updated_by_name": get_fullname(doc.updated_by) if doc.updated_by else None,
		"can_write": dentista() and puo_leggere_cartella(doc),
	}


def _voce(voce) -> dict:
	return {
		"name": voce.name,
		"service": voce.service,
		"description": voce.description,
		"tooth": voce.tooth,
		"surfaces": voce.surfaces,
		"phase": cint(voce.phase) or 1,
		"qty": flt(voce.qty),
		"rate": flt(voce.rate),
		"discount": flt(voce.discount),
		"amount": flt(voce.amount),
		"status": voce.status or R.DA_FARE,
		"appointment": voce.appointment,
		"done_on": str(voce.done_on) if voce.done_on else None,
		"done_by_name": get_fullname(voce.done_by) if voce.done_by else None,
	}


def _riga(doc) -> dict:
	fatte = sum(1 for voce in doc.items if voce.status == R.FATTA)
	contano = sum(1 for voce in doc.items if voce.status != R.ANNULLATA)
	return {
		"name": doc.name,
		"title": doc.title,
		"status": doc.status,
		"practitioner": doc.practitioner,
		"practitioner_name": get_fullname(doc.practitioner),
		"proposed_on": str(doc.proposed_on) if doc.proposed_on else None,
		"accepted_on": str(doc.accepted_on) if doc.accepted_on else None,
		"total_net": flt(doc.total_net),
		"total_done": flt(doc.total_done),
		"currency": doc.currency,
		"treatments": contano,
		"done": fatte,
		"mine": doc.practitioner == frappe.session.user,
	}


def _dettaglio(doc) -> dict:
	mio = doc.practitioner == frappe.session.user
	decide = doc.status == R.PROPOSTO and (mio or _preventivi())
	return {
		**_riga(doc),
		"lead": doc.lead,
		"lead_name": doc.lead_name,
		"price_list": doc.price_list,
		"valid_until": str(doc.valid_until) if doc.valid_until else None,
		"patient_notes": doc.patient_notes,
		"items": [_voce(voce) for voce in doc.items],
		"totals": R.totali([voce.as_dict() for voce in doc.items]),
		"quote_pdf": doc.quote_pdf,
		"deal": doc.deal,
		"accepted_by_name": get_fullname(doc.accepted_by) if doc.accepted_by else None,
		"acceptance_note": doc.acceptance_note,
		"declined_on": str(doc.declined_on) if doc.declined_on else None,
		"decline_reason": doc.decline_reason,
		"closed_on": str(doc.closed_on) if doc.closed_on else None,
		"replaces": doc.replaces,
		"can_edit": mio and doc.status == R.BOZZA,
		"can_withdraw": mio and doc.status == R.PROPOSTO,
		"can_decide": decide,
		# the deal's lost reasons, for a quote declined
		"lost_reasons": frappe.get_all("CRM Lost Reason", pluck="name", order_by="name") if decide else [],
		"can_mark": doc.status in (R.ACCETTATO, R.COMPLETATO) and dentista(),
		"can_close": doc.status == R.ACCETTATO and (mio or dossier.vede_gli_oscurati()),
		"can_copy": dentista() and doc.status != R.BOZZA,
	}


@frappe.whitelist()
def get_dental(lead: str) -> dict:
	"""The person's chart and care plans the session reads, for the Clinic tab."""
	_della_persona(lead)
	cartella = None
	nome = frappe.db.get_value(CARTELLA, {"lead": lead}, "name")
	if nome:
		doc = frappe.get_doc(CARTELLA, nome)
		if puo_leggere_cartella(doc):
			doc.add_viewed()
			cartella = _cartella(doc)
		elif livelli.puo("clinica.vedi"):
			# a colleague's, without the dossier: said, not shown; the desk is not told
			cartella = {"hidden": True, "practitioner_name": get_fullname(doc.practitioner)}
	piani = [
		doc
		for doc in (
			frappe.get_doc(PIANO, nome)
			for nome in frappe.get_all(PIANO, filters={"lead": lead}, pluck="name", order_by="creation desc")
		)
		if puo_leggere_piano(doc)
	]
	return {
		"chart": cartella,
		"plans": [_riga(doc) for doc in piani],
		"is_dentist": dentista(),
		"can_quote": _preventivi(),
		"price_lists": frappe.get_all(
			"CRM Price List",
			filters={"enabled": 1},
			fields=["name", "price_list_name"],
			order_by="price_list_name",
		)
		if dentista()
		else [],
	}


@frappe.whitelist()
def get_care_plan(name: str) -> dict:
	doc = _piano(name)
	doc.add_viewed()
	return _dettaglio(doc)


@frappe.whitelist()
def price_of(service: str, price_list: str | None = None) -> dict:
	"""A treatment's price from the price list, for the dentist to start from."""
	if not dentista():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	from crm.scheduling import pricing

	prezzo = pricing.resolve_price(service, now_datetime(), price_list=price_list or None)
	return {"rate": flt(prezzo.rate), "currency": prezzo.currency, "description": _nome_del_servizio(service)}


# ------------------------------------------------------------------ the chart


@frappe.whitelist(methods=["POST"])
def save_chart(lead: str, teeth, dentition: str | None = None, notes: str | None = None) -> dict:
	"""The chart as the dentist left it: a row that did not change keeps who noted it
	and when."""
	_della_persona(lead)
	if not dentista():
		frappe.throw(_("The chart is written by a dentist"), frappe.PermissionError)
	righe = frappe.parse_json(teeth) if isinstance(teeth, str) else (teeth or [])
	_problemi(R.valida_stato(righe))
	nome = frappe.db.get_value(CARTELLA, {"lead": lead}, "name")
	utente = frappe.session.user
	if nome:
		doc = frappe.get_doc(CARTELLA, nome)
		if not puo_leggere_cartella(doc):
			frappe.throw(
				_("The chart was started by a colleague: with the dossier consent you read it and write it"),
				frappe.PermissionError,
			)
	else:
		doc = frappe.new_doc(CARTELLA)
		doc.lead = lead
		doc.practitioner = utente
		doc.discipline = dossier.disciplina_di(utente)
	prima = {(riga.tooth, riga.condition): riga for riga in doc.teeth}
	doc.set("teeth", [])
	for riga in R.pulisci_stato(righe):
		vecchia = prima.get((riga["tooth"], riga["condition"]))
		uguale = (
			vecchia is not None
			and (vecchia.surfaces or "") == riga["surfaces"]
			and (vecchia.note or "") == riga["note"]
		)
		doc.append(
			"teeth",
			{
				**riga,
				"noted_on": vecchia.noted_on if uguale else nowdate(),
				"noted_by": vecchia.noted_by if uguale else utente,
			},
		)
	if dentition in R.DENTIZIONI:
		doc.dentition = dentition
	if notes is not None:
		doc.notes = notes.strip() or None
	doc.updated_on = now_datetime()
	doc.updated_by = utente
	if doc.is_new():
		doc.insert()
	else:
		doc.save()
	return _cartella(doc)


# ------------------------------------------------------------------ writing a plan


def _voci_dal_modulo(dati: dict) -> list[dict]:
	"""The treatments as the editor sends them: one of each, unless it says how many."""
	voci = []
	for voce in dati.get("items") or []:
		riga = {campo: voce.get(campo) for campo in CAMPI_VOCE}
		if riga["qty"] in (None, ""):
			riga["qty"] = 1
		voci.append(riga)
	return voci


@frappe.whitelist(methods=["POST"])
def save_care_plan(lead: str, data, name: str | None = None) -> dict:
	"""A draft, new or put right, by its dentist."""
	_della_persona(lead)
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	if name:
		doc = _mio(name, R.BOZZA)
		if doc.lead != lead:
			frappe.throw(_("This care plan belongs to somebody else"))
	else:
		if not dentista():
			frappe.throw(_("A care plan is written by a dentist"), frappe.PermissionError)
		doc = frappe.new_doc(PIANO)
		doc.lead = lead
		doc.practitioner = frappe.session.user
		doc.discipline = dossier.disciplina_di(frappe.session.user)
		doc.status = R.BOZZA
	voci = _voci_dal_modulo(dati)
	# a draft may be unfinished, never wrong
	if voci:
		_problemi(R.valida_piano(voci))
	doc.title = (dati.get("title") or "").strip() or _("Care plan")
	doc.price_list = dati.get("price_list") or None
	doc.valid_until = dati.get("valid_until") or None
	doc.patient_notes = (dati.get("patient_notes") or "").strip() or None
	doc.set("items", [])
	for voce in voci:
		doc.append("items", {**voce, "status": R.DA_FARE})
	if doc.is_new():
		doc.insert()
	else:
		doc.save()
	return _dettaglio(doc)


@frappe.whitelist(methods=["POST"])
def delete_care_plan_draft(name: str) -> None:
	doc = _mio(name, R.BOZZA)
	frappe.delete_doc(PIANO, doc.name)


def _salva(doc) -> None:
	"""A plan moved on by its own calls: past the draft, the calls decide."""
	doc.flags.dal_piano = True
	doc.save(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def propose_care_plan(name: str) -> dict:
	"""Handed to the person: frozen, its quote made, the quotes deal moved."""
	doc = _mio(name, R.BOZZA)
	_problemi(R.valida_piano([voce.as_dict() for voce in doc.items]))
	doc.status = R.PROPOSTO
	doc.proposed_on = now_datetime()
	doc.valid_until = doc.valid_until or add_days(getdate(), GIORNI_VALIDITA)
	_salva(doc)
	_preventivo_pdf(doc)
	_nel_deal(doc, consegnato=True)
	return _dettaglio(frappe.get_doc(PIANO, doc.name))


@frappe.whitelist(methods=["POST"])
def withdraw_care_plan(name: str) -> dict:
	"""Back to a draft, to change it before the person says yes: the quote handed
	over is no longer the plan's."""
	doc = _mio(name, R.PROPOSTO)
	vecchio = doc.quote_pdf
	doc.status = R.BOZZA
	doc.proposed_on = None
	doc.quote_pdf = None
	_salva(doc)
	if vecchio:
		for file in frappe.get_all(
			"File", filters={"file_url": vecchio, "attached_to_name": doc.name}, pluck="name"
		):
			frappe.delete_doc("File", file, ignore_permissions=True)
	return _dettaglio(doc)


def _decide(name: str):
	doc = _piano(name)
	if doc.status != R.PROPOSTO:
		frappe.throw(_("Only a proposed care plan is accepted or declined"))
	if doc.practitioner != frappe.session.user and not _preventivi():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc


@frappe.whitelist(methods=["POST"])
def accept_care_plan(name: str, note: str | None = None) -> dict:
	"""The person said yes: how, in a few words. The appointments already booked for
	its treatments take them."""
	doc = _decide(name)
	doc.status = R.ACCETTATO
	doc.accepted_on = now_datetime()
	doc.accepted_by = frappe.session.user
	doc.acceptance_note = (note or "").strip() or None
	_salva(doc)
	_nel_deal(doc, accettato=True)
	_raccogli(doc.name)
	return _dettaglio(frappe.get_doc(PIANO, doc.name))


@frappe.whitelist(methods=["POST"])
def decline_care_plan(name: str, reason: str | None = None, note: str | None = None) -> dict:
	"""The person said no, and maybe why: the reason is the deal's lost reason."""
	doc = _decide(name)
	doc.status = R.RIFIUTATO
	doc.declined_on = now_datetime()
	doc.decline_reason = ", ".join(v for v in ((reason or "").strip(), (note or "").strip()) if v) or None
	_salva(doc)
	_nel_deal(doc, accettato=False, motivo=reason, note=note)
	return _dettaglio(doc)


@frappe.whitelist(methods=["POST"])
def mark_treatment(name: str, item: str, status: str) -> dict:
	"""A treatment done, back to do, or cancelled, by a dentist: the appointments do
	it by themselves, this is for what happened otherwise."""
	doc = _piano(name)
	if doc.status not in (R.ACCETTATO, R.COMPLETATO):
		frappe.throw(_("Treatments are marked on an accepted care plan"))
	if not dentista():
		frappe.throw(_("Treatments are marked by a dentist"), frappe.PermissionError)
	if status not in (R.DA_FARE, R.FATTA, R.ANNULLATA):
		frappe.throw(_("Unknown status {0}").format(status))
	voce = next((riga for riga in doc.items if riga.name == item), None)
	if not voce:
		frappe.throw(_("This treatment is not in the plan"))
	if status == R.FATTA:
		voce.status, voce.done_on, voce.done_by = R.FATTA, getdate(), frappe.session.user
	elif status == R.DA_FARE:
		voce.status = R.PRENOTATA if voce.appointment else R.DA_FARE
		voce.done_on = voce.done_by = None
	else:
		voce.status, voce.appointment = R.ANNULLATA, None
		voce.done_on = voce.done_by = None
	_salva(doc)
	_completa(doc.name)
	return _dettaglio(frappe.get_doc(PIANO, doc.name))


@frappe.whitelist(methods=["POST"])
def close_care_plan(name: str) -> dict:
	"""Stopped half-way: by its dentist or the medical director. What was done stays."""
	doc = _piano(name)
	if doc.status != R.ACCETTATO:
		frappe.throw(_("Only an accepted care plan is closed"))
	if doc.practitioner != frappe.session.user and not dossier.vede_gli_oscurati():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc.status = R.CHIUSO
	doc.closed_on = now_datetime()
	_salva(doc)
	return _dettaglio(doc)


@frappe.whitelist(methods=["POST"])
def copy_care_plan(name: str) -> dict:
	"""A new version: a draft of the session's dentist with the same treatments."""
	fonte = _piano(name)
	if not dentista():
		frappe.throw(_("A care plan is written by a dentist"), frappe.PermissionError)
	doc = frappe.new_doc(PIANO)
	doc.lead = fonte.lead
	doc.practitioner = frappe.session.user
	doc.discipline = dossier.disciplina_di(frappe.session.user)
	doc.status = R.BOZZA
	doc.title = fonte.title
	doc.price_list = fonte.price_list
	doc.patient_notes = fonte.patient_notes
	doc.replaces = fonte.name
	for voce in fonte.items:
		if voce.status == R.ANNULLATA:
			continue
		doc.append("items", {campo: voce.get(campo) for campo in CAMPI_VOCE} | {"status": R.DA_FARE})
	doc.insert()
	return _dettaglio(doc)


# ------------------------------------------------------------------ the quote and the deal


def _contesto(doc) -> dict:
	from crm.moduli.richieste import nome_del_centro

	voci = [_voce(voce) for voce in doc.items if voce.status != R.ANNULLATA]
	gruppi = []
	for fase, posizioni in R.fasi(voci):
		gruppi.append({"phase": fase, "items": [voci[n] for n in posizioni]})
	return {
		"doc": doc,
		"centro": nome_del_centro(),
		"titolo": doc.title,
		"lingua": (frappe.local.lang or "it")[:2],
		"persona": doc.lead_name,
		"dentista": get_fullname(doc.practitioner),
		"data": formatdate(getdate(doc.proposed_on or now_datetime())),
		"valido_fino": formatdate(doc.valid_until) if doc.valid_until else None,
		"fasi": gruppi,
		"piu_fasi": len(gruppi) > 1,
		"totali": R.totali(voci),
		"valuta": doc.currency or "EUR",
		"soldi": lambda valore: frappe.utils.fmt_money(valore, currency=doc.currency or "EUR"),
		"_": _,
	}


def html_del_preventivo(doc) -> str:
	return frappe.render_template(MODELLO_PREVENTIVO, _contesto(doc))


def _preventivo_pdf(doc) -> None:
	"""The quote as it is handed over, kept private with the plan. One that cannot be
	made does not stop the proposal: the log says so."""
	from crm.moduli import pdf

	try:
		dati = pdf.pdf_da_html(html_del_preventivo(doc))
	except Exception:
		frappe.log_error(title=f"Care plan quote {doc.name}", message=frappe.get_traceback())
		return
	allegato = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{doc.name}.pdf",
			"attached_to_doctype": PIANO,
			"attached_to_name": doc.name,
			"attached_to_field": "quote_pdf",
			"is_private": 1,
			"content": dati,
		}
	).insert(ignore_permissions=True)
	doc.db_set("quote_pdf", allegato.file_url, update_modified=False)


def _nel_deal(doc, consegnato=False, accettato=None, motivo=None, note=None) -> None:
	"""The quotes pipeline follows the plan; a deal that cannot move never stops it."""
	from crm.clinica import pipeline

	frappe.db.savepoint("cure_deal")
	try:
		if consegnato:
			deal = pipeline.preventivo_consegnato(doc.lead, flt(doc.total_net), doc.deal)
			if deal and deal != doc.deal:
				doc.db_set("deal", deal, update_modified=False)
		else:
			pipeline.preventivo_chiuso(doc.deal, bool(accettato), motivo, note)
	except Exception:
		frappe.db.rollback(save_point="cure_deal")
		frappe.log_error(
			title=_("Quotes deal not moved for care plan {0}").format(doc.name),
			reference_doctype=PIANO,
			reference_name=doc.name,
		)


# ------------------------------------------------------------------ the appointments


def _persone(appuntamento, anche_annullati: bool = False) -> list[str]:
	persone = []
	for riga in appuntamento.get("participants") or []:
		if riga.status == "Cancelled" and not anche_annullati:
			continue
		persona = paziente.persona_di(riga.party_type, riga.party)
		if persona:
			persone.append(persona)
	return persone


def _voci_del_piano(piano: str) -> list[frappe._dict]:
	return frappe.get_all(
		VOCE,
		filters={"parent": piano, "parenttype": PIANO},
		fields=["name", "service", "phase", "status", "amount", "appointment"],
		order_by="idx asc",
	)


def _da_prendere(persone: list[str], servizio: str) -> tuple | None:
	"""The treatment an appointment of ``servizio`` takes: of its people in order, in
	their accepted plans from the oldest, the first still to do."""
	for persona in persone:
		for piano in frappe.get_all(
			PIANO, filters={"lead": persona, "status": R.ACCETTATO}, pluck="name", order_by="accepted_on asc"
		):
			voci = _voci_del_piano(piano)
			n = R.voce_per(voci, servizio)
			if n is not None:
				return piano, voci[n].name, flt(voci[n].amount), persona
	return None


def _della_voce(appuntamento: str) -> frappe._dict | None:
	righe = frappe.get_all(
		VOCE,
		filters={"parenttype": PIANO, "appointment": appuntamento},
		fields=["name", "parent", "service", "amount"],
		limit=1,
	)
	return righe[0] if righe else None


def _prezzo(appuntamento, importo: float, persona: str) -> None:
	"""The price agreed in the plan, for the plan's person."""
	attivi = [riga for riga in appuntamento.participants if riga.status != "Cancelled"]
	for riga in attivi:
		if paziente.persona_di(riga.party_type, riga.party) == persona:
			riga.amount = importo
	if cint(appuntamento.per_participant):
		appuntamento.total_amount = sum(flt(riga.amount) for riga in attivi)
	elif len(attivi) <= 1:
		appuntamento.unit_price = appuntamento.total_amount = importo
	else:
		return
	appuntamento.price_source = _("As agreed in the care plan")


def _senza_fermare(titolo: str, doc, funzione) -> None:
	from crm.clinica.eventi import _senza_fermare as senza_fermare

	senza_fermare(titolo, doc, funzione)


def appuntamento_in_validazione(doc, method=None) -> None:
	"""`validate` of an appointment: a new one of a treatment still to do, for the
	person of an accepted plan, will take it at the price agreed; one that has it
	keeps the price."""
	if not doc.service or doc.status == "Cancelled" or not paziente.clinica_accesa():
		return
	try:
		if doc.is_new():
			scelta = _da_prendere(_persone(doc), doc.service)
			if scelta:
				doc.flags.voce_di_cura = scelta
				_prezzo(doc, scelta[2], scelta[3])
			return
		voce = _della_voce(doc.name)
		if voce and voce.service == doc.service:
			persona = frappe.db.get_value(PIANO, voce.parent, "lead")
			if persona in _persone(doc, anche_annullati=True):
				_prezzo(doc, flt(voce.amount), persona)
	except Exception:
		frappe.log_error(title=_("Care plan price not applied"), reference_doctype=doc.doctype)


def appuntamento_creato(doc, method=None) -> None:
	"""`after_insert`: the treatment is booked with it."""
	scelta = doc.flags.get("voce_di_cura")
	if not scelta:
		return

	def prenota():
		frappe.db.set_value(VOCE, scelta[1], {"appointment": doc.name, "status": R.PRENOTATA})

	_senza_fermare(_("Care plan treatment not booked for {0}").format(doc.name), doc, prenota)


def _libera(voce) -> None:
	frappe.db.set_value(
		VOCE, voce.name, {"appointment": None, "status": R.DA_FARE, "done_on": None, "done_by": None}
	)


def appuntamento_aggiornato(doc, method=None) -> None:
	"""`on_update`: the person came, the treatment is done; cancelled, missed, or
	of another service now, it is to do again."""
	voce = _della_voce(doc.name)
	if not voce:
		return

	def segui():
		persona = frappe.db.get_value(PIANO, voce.parent, "lead")
		riga = next(
			(r for r in doc.participants if paziente.persona_di(r.party_type, r.party) == persona), None
		)
		if (
			doc.status in ("Cancelled", "No Show")
			or riga is None
			or riga.status in ("Cancelled", "No Show")
			or voce.service != doc.service
		):
			_libera(voce)
		elif doc.status == "Completed" or riga.status == "Attended":
			chi = next((r.user for r in doc.staff or [] if r.user), None)
			frappe.db.set_value(
				VOCE, voce.name, {"status": R.FATTA, "done_on": getdate(doc.starts_on), "done_by": chi}
			)
		_completa(voce.parent)

	_senza_fermare(_("Care plan not followed for appointment {0}").format(doc.name), doc, segui)


def appuntamento_eliminato(doc, method=None) -> None:
	"""`on_trash`: the treatment is to do again, before the link would stop the delete."""
	voce = _della_voce(doc.name)
	if voce:
		_libera(voce)
		_completa(voce.parent)


def _completa(piano: str) -> None:
	"""The sums again; every treatment done or cancelled, the plan is completed, and
	one to do again opens it."""
	doc = frappe.get_doc(PIANO, piano)
	voci = [voce.as_dict() for voce in doc.items]
	somme = R.totali(voci)
	stato = doc.status
	if stato == R.ACCETTATO and R.completato(voci):
		stato = R.COMPLETATO
	elif stato == R.COMPLETATO and not R.completato(voci):
		stato = R.ACCETTATO
	frappe.db.set_value(
		PIANO,
		piano,
		{"status": stato, "total_net": somme["net"], "total_done": somme["done"]},
		update_modified=False,
	)


def _scrivi_prezzo(appuntamento: str, importo: float, persona: str) -> None:
	doc = frappe.get_doc(APPUNTAMENTO, appuntamento)
	_prezzo(doc, importo, persona)
	frappe.db.set_value(
		APPUNTAMENTO,
		appuntamento,
		{"unit_price": doc.unit_price, "total_amount": doc.total_amount, "price_source": doc.price_source},
		update_modified=False,
	)
	for riga in doc.participants:
		frappe.db.set_value(PARTECIPANTE, riga.name, "amount", riga.amount, update_modified=False)


def _raccogli(piano: str) -> None:
	"""Accepted: the person's appointments already booked from today, of a
	treatment's service and of no treatment yet, take theirs in order."""
	doc = frappe.get_doc(PIANO, piano)
	servizi = {voce.service for voce in doc.items if voce.status == R.DA_FARE}
	if not servizi:
		return
	prenotati = frappe.get_all(
		PARTECIPANTE,
		filters={
			"parenttype": APPUNTAMENTO,
			"party_type": "CRM Lead",
			"party": doc.lead,
			"status": ("!=", "Cancelled"),
		},
		pluck="parent",
	)
	if not prenotati:
		return
	oggi = datetime.datetime.combine(getdate(), datetime.time.min)
	for appuntamento in frappe.get_all(
		APPUNTAMENTO,
		filters=[
			["name", "in", list(set(prenotati))],
			["service", "in", list(servizi)],
			["status", "not in", ("Cancelled", "No Show")],
			["starts_on", ">=", oggi],
		],
		fields=["name", "service"],
		order_by="starts_on asc",
	):
		if _della_voce(appuntamento.name):
			continue
		voci = _voci_del_piano(piano)
		n = R.voce_per(voci, appuntamento.service)
		if n is None:
			continue
		frappe.db.set_value(VOCE, voci[n].name, {"appointment": appuntamento.name, "status": R.PRENOTATA})
		_scrivi_prezzo(appuntamento.name, flt(voci[n].amount), doc.lead)


# ------------------------------------------------------------------ in the area


def della_persona(persona: str) -> list[dict]:
	"""For the person's own area: the plans proposed to them and going on, in the
	words they read - treatments, teeth, what is done - with the sums."""
	fatto = []
	for nome in frappe.get_all(
		PIANO,
		filters={"lead": persona, "status": ("in", (R.PROPOSTO, R.ACCETTATO, R.COMPLETATO))},
		pluck="name",
		order_by="creation desc",
	):
		doc = frappe.get_doc(PIANO, nome)
		voci = [voce for voce in doc.items if voce.status != R.ANNULLATA]
		fatto.append(
			{
				"name": doc.name,
				"title": doc.title,
				"status": doc.status,
				"practitioner_name": get_fullname(doc.practitioner),
				"valid_until": str(doc.valid_until) if doc.valid_until else None,
				"patient_notes": doc.patient_notes,
				"currency": doc.currency,
				"totals": R.totali([voce.as_dict() for voce in voci]),
				"items": [
					{
						"description": voce.description,
						"tooth": voce.tooth,
						"phase": cint(voce.phase) or 1,
						"amount": flt(voce.amount),
						"status": voce.status,
						"when": str(frappe.db.get_value(APPUNTAMENTO, voce.appointment, "starts_on"))
						if voce.appointment and voce.status == R.PRENOTATA
						else None,
					}
					for voce in voci
				],
			}
		)
	return fatto


def piani_nell_area(persona: str) -> int:
	return frappe.db.count(PIANO, {"lead": persona, "status": ("in", (R.PROPOSTO, R.ACCETTATO))})
