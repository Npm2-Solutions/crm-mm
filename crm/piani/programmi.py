# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Programmes of stages on the person's page (design.md, "I piani": "Programmi a
tappe: contenuti che si aprono col tempo o finita la tappa prima, per i percorsi
di nutrizione e di allenamento").

- **Written like a plan**: a draft of its author (`piani.scrivi`), stages in order,
  each with what the person reads and, if its author writes one, the plan to
  follow while it is open - of the kinds the author's qualification writes.
- **Published**, the programme opens its first stage on its first day. By time,
  each next stage opens on its day (the daily job); at one's own pace, when the
  person says the stage is finished, in their area, or its author does.
- **A stage that opens** publishes its plan - closing the person's other plan of
  the same kind, as any plan does - and the person hears there is news in their
  area. A stage finished closes its plan: it stays with the person.
- **Closed** by its author, the programme closes the plan of its open stage; the
  last stage finished completes it.
- **Who reads it**: like a plan (`api.puo_leggere`) - its author always, the others
  once published; with a stage's plan of health data, the programme carries the
  mark too and is read like the clinical record, every opening in the access log.
"""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, getdate, now_datetime

from crm.permissions import livelli, sanitari
from crm.piani import api as piani
from crm.piani import programmi_regole as P

PROGRAMMA = "CRM Programme"
TAPPA = "CRM Programme Stage"
BOZZA, PUBBLICATO, COMPLETATO, CHIUSO = "Draft", "Published", "Completed", "Closed"


# ------------------------------------------------------------------ who reads, who writes


def puo_leggere(doc, user: str | None = None) -> bool:
	"""As a plan: its author, always; the others once published, a programme with
	health data by the clinic's rule."""
	return piani.puo_leggere(doc, user)


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return livelli.puo("piani.scrivi", user)
	if ptype in ("write", "delete"):
		return doc.get("practitioner") == user and doc.get("status") == BOZZA
	if ptype in ("submit", "cancel", "amend"):
		return False
	return puo_leggere(doc, user)


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	return piani.condizione(frappe.qb.DocType(PROGRAMMA), user).get_sql(
		with_namespace=True, quote_char="`", secondary_quote_char="'"
	)


def marca(doc) -> None:
	"""A programme carries the mark "health data" when a stage's plan does, or by
	who wrote it (`crm.permissions.sanitari`)."""
	piani_delle_tappe = [t.plan for t in doc.stages if t.plan]
	doc.clinical = (
		1
		if sanitari.per_chi_scrive(doc)
		or (
			piani_delle_tappe
			and frappe.db.exists(piani.PIANO, {"name": ("in", piani_delle_tappe), "clinical": 1})
		)
		else 0
	)


def _programma(name: str):
	doc = frappe.get_doc(PROGRAMMA, name)
	frappe.has_permission("CRM Lead", "read", doc=doc.lead, throw=True)
	if not puo_leggere(doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc


def _mio(name: str):
	doc = _programma(name)
	if doc.practitioner != frappe.session.user:
		frappe.throw(_("A programme is changed by who wrote it"), frappe.PermissionError)
	return doc


def _mio_in_bozza(name: str):
	doc = _mio(name)
	if doc.status != BOZZA:
		frappe.throw(_("A published programme is not rewritten: close it and write another"))
	return doc


# ------------------------------------------------------------------ reading


def _come_tappe(doc) -> list[dict]:
	return [
		{
			"key": t.stage_key,
			"title": t.title,
			"description": t.description,
			"days": t.days or None,
			"plan": t.plan,
			"opened_on": getdate(t.opened_on) if t.opened_on else None,
			"completed_on": getdate(t.completed_on) if t.completed_on else None,
		}
		for t in doc.stages
	]


def _riga(doc) -> dict:
	tappe = _come_tappe(doc)
	aperta = P.aperta(tappe)
	return {
		"name": doc.name,
		"title": doc.title,
		"mode": doc.mode,
		"status": doc.status,
		"starts_on": doc.starts_on,
		"practitioner": doc.practitioner,
		"practitioner_name": get_fullname(doc.practitioner),
		"mine": doc.practitioner == frappe.session.user,
		"stages": len(tappe),
		"open_stage": aperta,
		"open_title": tappe[aperta]["title"] if aperta is not None else None,
		"clinical": cint(doc.get("clinical")),
	}


@frappe.whitelist()
def get_programmes(lead: str) -> dict:
	"""The person's programmes the session reads, newest first."""
	piani._della_persona(lead)
	documenti = [
		doc
		for doc in (
			frappe.get_doc(PROGRAMMA, nome)
			for nome in frappe.get_all(
				PROGRAMMA, filters={"lead": lead}, pluck="name", order_by="creation desc"
			)
		)
		if puo_leggere(doc)
	]
	return {
		"programmes": [_riga(doc) for doc in documenti],
		# the published ones with health data the session may know of but does not read
		"hidden": sanitari.nascosti(
			PROGRAMMA, lead, {doc.name for doc in documenti}, filtri={"status": ("!=", BOZZA)}
		),
		"can_write": livelli.puo("piani.scrivi"),
	}


def _piani_delle_tappe(doc) -> dict[str, dict]:
	nomi = [t.plan for t in doc.stages if t.plan]
	if not nomi:
		return {}
	return {
		riga.name: riga
		for riga in frappe.get_all(
			piani.PIANO,
			filters={"name": ("in", nomi)},
			fields=["name", "title", "plan_type", "status", "starts_on", "ends_on"],
		)
	}


@frappe.whitelist()
def get_programme(name: str) -> dict:
	"""A programme to read or to go on writing: its stages with their state and
	their plans. With health data, the opening goes in the access log."""
	doc = _programma(name)
	piani._aperto(doc)
	oggi = getdate()
	tappe = _come_tappe(doc)
	stati = P.stati(doc.mode, getdate(doc.starts_on) if doc.starts_on else None, tappe, oggi)
	del_piano = _piani_delle_tappe(doc)
	mio = doc.practitioner == frappe.session.user
	righe = []
	for tappa, stato in zip(tappe, stati, strict=True):
		piano = del_piano.get(tappa["plan"]) if tappa["plan"] else None
		righe.append(
			{
				**tappa,
				**stato,
				"plan_title": piano.title if piano else None,
				"plan_type": piano.plan_type if piano else None,
				"plan_status": piano.status if piano else None,
			}
		)
	aperta = P.aperta(tappe)
	return {
		**_riga(doc),
		"lead": doc.lead,
		"instructions": doc.instructions,
		"published_on": doc.published_on,
		"completed_on": doc.completed_on,
		"closed_on": doc.closed_on,
		"stages": righe,
		"kinds": [piani.descrivi_tipo(tipo) for tipo in piani.tipi_consentiti()] if mio else [],
		"can_edit": mio and doc.status == BOZZA,
		"can_open_next": mio and doc.status == PUBBLICATO and P.prossima(tappe) is not None,
		"can_finish": mio and doc.status == PUBBLICATO and aperta is not None,
		"can_close": mio and doc.status == PUBBLICATO,
	}


# ------------------------------------------------------------------ writing


def _chiave() -> str:
	return secrets.token_hex(4)


def _tappe(dati: dict) -> list[dict]:
	tappe = []
	for tappa in dati.get("stages") or []:
		tappe.append(
			{
				"key": tappa.get("key") or _chiave(),
				"title": (tappa.get("title") or "").strip(),
				"description": (tappa.get("description") or "").strip() or None,
				"days": cint(tappa.get("days")) or None,
				"plan": tappa.get("plan") or None,
			}
		)
	return tappe


def _controlla(modo: str, tappe: list[dict], doc=None) -> None:
	problemi = P.valida(modo, tappe)
	if problemi:
		frappe.throw(
			"<br>".join(dict.fromkeys(p.testo(_) for p in problemi)), title=_("The programme is not ready")
		)
	# a stage's plan is one of this programme's
	for tappa in tappe:
		if tappa["plan"] and (
			not doc or frappe.db.get_value(piani.PIANO, tappa["plan"], "programme") != doc.name
		):
			frappe.throw(_("A stage's plan is written from its stage"))


@frappe.whitelist(methods=["POST"])
def save_programme(lead: str, data: dict | str, name: str | None = None) -> dict:
	"""A draft of the session's own, new or carried on."""
	livelli.verifica("piani.scrivi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	if name:
		doc = _mio_in_bozza(name)
		if doc.lead != lead:
			frappe.throw(_("This programme belongs to somebody else"))
	else:
		doc = frappe.new_doc(PROGRAMMA)
		doc.lead = lead
		doc.practitioner = frappe.session.user
		doc.status = BOZZA
	modo = dati.get("mode") or doc.mode or P.RITMO
	tappe = _tappe(dati)
	_controlla(modo, tappe, None if doc.is_new() else doc)
	doc.mode = modo
	doc.title = (dati.get("title") or "").strip()[:140] or _("Programme")
	doc.starts_on = dati.get("starts_on") or None
	doc.instructions = (dati.get("instructions") or "").strip() or None
	doc.discipline = piani.qualifica_di(frappe.session.user)
	# the plans of the stages taken away go with them
	restano = {t["plan"] for t in tappe if t["plan"]}
	lasciati = [t.plan for t in doc.stages if t.plan and t.plan not in restano]
	doc.set(
		"stages",
		[
			{
				"stage_key": t["key"],
				"title": t["title"],
				"description": t["description"],
				"days": t["days"],
				"plan": t["plan"],
			}
			for t in tappe
		],
	)
	marca(doc)
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	for piano in lasciati:
		if frappe.db.get_value(piani.PIANO, piano, "status") == piani.BOZZA:
			frappe.delete_doc(piani.PIANO, piano, ignore_permissions=True)
	return get_programme(doc.name)


@frappe.whitelist(methods=["POST"])
def stage_plan(name: str, stage: str, plan_type: str) -> dict:
	"""The plan of a stage, as a draft to write in the plan's editor: one per stage,
	of a kind the author writes. A stage already open has its plan already."""
	doc = _mio(name)
	if doc.status not in (BOZZA, PUBBLICATO):
		frappe.throw(_("This programme is over"))
	tappa = next((t for t in doc.stages if t.stage_key == stage), None)
	if not tappa:
		frappe.throw(_("This stage is not in the programme"))
	if tappa.plan:
		return {"plan": tappa.plan}
	if tappa.opened_on:
		frappe.throw(_("This stage is open already: its plan is written before it opens"))
	if plan_type not in piani.tipi_consentiti():
		frappe.throw(_("Your qualification does not write a plan of this kind"), frappe.PermissionError)
	piano = frappe.new_doc(piani.PIANO)
	piano.update(
		{
			"lead": doc.lead,
			"plan_type": plan_type,
			"title": tappa.title,
			"status": piani.BOZZA,
			"practitioner": frappe.session.user,
			"discipline": piani.qualifica_di(frappe.session.user),
			"programme": doc.name,
			"stage_key": stage,
		}
	)
	piani.marca(piano)
	piano.insert(ignore_permissions=True)
	frappe.db.set_value(TAPPA, tappa.name, "plan", piano.name, update_modified=False)
	# a stage's plan of health data marks its programme
	if piano.clinical and not doc.clinical:
		frappe.db.set_value(PROGRAMMA, doc.name, "clinical", 1, update_modified=False)
	return {"plan": piano.name}


@frappe.whitelist(methods=["POST"])
def delete_programme_draft(name: str) -> None:
	"""A draft is thrown away by who wrote it, with the drafts of its stages' plans."""
	doc = _mio_in_bozza(name)
	# each points to the other: the stage lets its plan go, the plan goes, then the programme
	for tappa in doc.stages:
		if not tappa.plan:
			continue
		piano = tappa.plan
		frappe.db.set_value(TAPPA, tappa.name, "plan", None, update_modified=False)
		if frappe.db.get_value(piani.PIANO, piano, "status") == piani.BOZZA:
			frappe.delete_doc(piani.PIANO, piano, ignore_permissions=True)
	frappe.delete_doc(PROGRAMMA, doc.name, ignore_permissions=True)


# ------------------------------------------------------------------ the stages open


def _avvisa(lead: str) -> None:
	piani.avvisa(lead)


def _tappa(doc, posizione: int):
	return doc.stages[posizione]


def _apri(doc, posizione: int, oggi) -> None:
	"""A stage opens today: its plan is published for its days, and it is news."""
	tappa = _tappa(doc, posizione)
	tappa.opened_on = oggi
	if tappa.plan:
		fine = None
		if doc.mode == P.TEMPO and doc.starts_on:
			fine = P.finestre(getdate(doc.starts_on), _come_tappe(doc))[posizione][1]
		piano = frappe.get_doc(piani.PIANO, tappa.plan)
		if piano.status == piani.BOZZA:
			piani.pubblica(piano, dal=oggi, al=fine)


def _completa(doc, posizione: int, oggi, chi: str | None) -> None:
	"""A stage finished: its plan is closed, and stays with the person."""
	tappa = _tappa(doc, posizione)
	tappa.completed_on = oggi
	tappa.completed_by = chi
	if tappa.plan and frappe.db.get_value(piani.PIANO, tappa.plan, "status") == piani.PUBBLICATO:
		piani._chiudi(frappe.get_doc(piani.PIANO, tappa.plan), now_datetime())


def _salva(doc) -> None:
	doc.flags.dal_programma = True
	doc.save(ignore_permissions=True)


def avanza(doc, oggi, chi: str | None) -> bool:
	"""The open stage finished and the next opened; the last finished completes the
	programme. Whether anything opened."""
	tappe = _come_tappe(doc)
	aperta = P.aperta(tappe)
	if aperta is not None:
		_completa(doc, aperta, oggi, chi)
	prossima = P.prossima(_come_tappe(doc))
	if prossima is None:
		doc.status = COMPLETATO
		doc.completed_on = now_datetime()
		_salva(doc)
		return False
	_apri(doc, prossima, oggi)
	_salva(doc)
	return True


def controlli_prima_di_pubblicare(doc) -> None:
	tappe = _come_tappe(doc)
	_controlla(doc.mode, tappe, doc)
	if doc.mode == P.TEMPO and not doc.starts_on:
		frappe.throw(_("A programme by time starts on a day: say which"))
	for tappa in doc.stages:
		if not tappa.plan:
			continue
		piano = frappe.get_doc(piani.PIANO, tappa.plan)
		momenti, voci = piani.righe_del_piano(piano)
		if not voci:
			frappe.throw(_("The plan of stage {0} is empty").format(frappe.bold(tappa.title)))
		piani._controlla(piano.plan_type, momenti, voci)


@frappe.whitelist(methods=["POST"])
def publish_programme(name: str) -> dict:
	"""The programme goes to the person's area; its first stage opens on its first
	day - today, if it is not later."""
	doc = _mio_in_bozza(name)
	controlli_prima_di_pubblicare(doc)
	oggi = getdate()
	doc.starts_on = doc.starts_on or oggi
	doc.status = PUBBLICATO
	doc.published_on = now_datetime()
	if getdate(doc.starts_on) <= oggi:
		_apri(doc, 0, oggi)
	_salva(doc)
	_avvisa(doc.lead)
	return get_programme(doc.name)


@frappe.whitelist(methods=["POST"])
def open_next_stage(name: str) -> dict:
	"""Its author finishes the open stage and opens the next one now,
	whatever the days said. The days after it stay where they were."""
	doc = _mio(name)
	if doc.status != PUBBLICATO:
		frappe.throw(_("Only a published programme goes on"))
	if avanza(doc, getdate(), frappe.session.user):
		_avvisa(doc.lead)
	return get_programme(doc.name)


@frappe.whitelist(methods=["POST"])
def close_programme(name: str) -> dict:
	"""No longer followed: the open stage's plan is closed, and all stays with the person."""
	doc = _mio(name)
	if doc.status != PUBBLICATO:
		frappe.throw(_("Only a published programme is closed"))
	aperta = P.aperta(_come_tappe(doc))
	if aperta is not None:
		_completa(doc, aperta, getdate(), frappe.session.user)
	doc.status = CHIUSO
	doc.closed_on = now_datetime()
	_salva(doc)
	return get_programme(doc.name)


# ------------------------------------------------------------------ the days going by


def apri_del_giorno() -> None:
	"""Every morning: the programmes whose first day has come open their first
	stage; by time, a stage whose days are over gives way to the next."""
	oggi = getdate()
	for nome in frappe.get_all(PROGRAMMA, filters={"status": PUBBLICATO}, pluck="name"):
		frappe.db.savepoint("crm_programma")
		try:
			_giorno(frappe.get_doc(PROGRAMMA, nome), oggi)
		except Exception:
			frappe.db.rollback(save_point="crm_programma")
			frappe.log_error(title=f"Programme {nome}: stages not opened")


def _giorno(doc, oggi) -> None:
	inizio = getdate(doc.starts_on) if doc.starts_on else None
	if not inizio or oggi < inizio:
		return
	tappe = _come_tappe(doc)
	if P.prossima(tappe) == 0:
		# the first day came
		_apri(doc, 0, oggi)
		_salva(doc)
		_avvisa(doc.lead)
		tappe = _come_tappe(doc)
	if doc.mode != P.TEMPO:
		return
	dovuta = P.tappa_del_giorno(inizio, tappe, oggi)
	aperte = False
	while doc.status == PUBBLICATO:
		aperta = P.aperta(_come_tappe(doc))
		if aperta is None or dovuta is None or aperta >= dovuta:
			break
		aperte = avanza(doc, oggi, None) or aperte
	if aperte:
		_avvisa(doc.lead)


def area_dei_programmi(person: str, oggi=None) -> list[dict]:
	"""The programmes a person follows now, as their area shows them: every stage
	with its state, what the open one says, and its plan."""
	oggi = oggi or getdate()
	righe = []
	for doc in (
		frappe.get_doc(PROGRAMMA, nome)
		for nome in frappe.get_all(
			PROGRAMMA,
			filters={"lead": person, "status": PUBBLICATO},
			pluck="name",
			order_by="published_on desc",
		)
	):
		tappe = _come_tappe(doc)
		stati = P.stati(doc.mode, getdate(doc.starts_on) if doc.starts_on else None, tappe, oggi)
		aperta = P.aperta(tappe)
		righe.append(
			{
				"name": doc.name,
				"title": doc.title,
				"mode": doc.mode,
				"instructions": doc.instructions,
				"starts_on": doc.starts_on,
				"practitioner_name": get_fullname(doc.practitioner),
				"open_stage": aperta,
				# at one's own pace the person says a stage is finished
				"can_finish": doc.mode == P.RITMO and aperta is not None,
				"stages": [
					{
						"key": tappa["key"],
						"title": tappa["title"],
						# what a stage says is read once it is open
						"description": tappa["description"] if stato["state"] != P.CHIUSA else None,
						"plan": tappa["plan"] if stato["state"] == P.APERTA else None,
						"state": stato["state"],
						"opens_on": stato["opens_on"],
						"completed_on": stato["completed_on"],
					}
					for tappa, stato in zip(tappe, stati, strict=True)
				],
			}
		)
	return righe


def finisce_la_tappa(person: str, programme: str, stage: str) -> None:
	"""The person says the open stage is finished: at one's own pace the next opens."""
	doc = frappe.get_doc(PROGRAMMA, programme)
	if doc.lead != person or doc.status != PUBBLICATO:
		frappe.throw(_("This programme is not followed now"), frappe.PermissionError)
	if doc.mode != P.RITMO:
		frappe.throw(_("In this programme the stages open by themselves, on their day"))
	tappe = _come_tappe(doc)
	aperta = P.aperta(tappe)
	if aperta is None or tappe[aperta]["key"] != stage:
		frappe.throw(_("This stage is not the one open"))
	# the person opened the next stage: no email to tell them what they did
	avanza(doc, getdate(), frappe.session.user)
