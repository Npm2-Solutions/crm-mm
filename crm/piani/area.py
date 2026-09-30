# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The plans in the client area: what to do on a day, one tap an item.

- **The plans followed now** (`area_plans`): the published ones whose period
  holds today, each with how today is going.
- **A day** (`area_plan`): the plan's moments of that day - every day's and that
  weekday's - each with its items as the person reads them, each kind its own way
  (`api.Genere.per_la_persona`): the exercise with its sets, a picture, a video
  and how it is done; the habit; the clinic's food and how much, the portions of a
  group with the foods to choose from.
- **One tap** (`log_item`): done, partly, skipped; one answer an item a day,
  changed with another tap. A missed day is made up within two days, never a day
  ahead (`regole.si_segna`).
- **The week**: an item asked so many times a week says how many are left; what
  is shown is what is left to do, never what went wrong.
- **The programmes** (`area_programmes`, `finish_stage`): stage by stage, the next
  opened by the person at their own pace.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_fullname, getdate, now_datetime

from crm.area.api import _mia
from crm.piani import api as piani
from crm.piani import regole as R

#: How far ahead the person looks at a plan: next week's menu, to shop for it.
GIORNI_AVANTI = 6


def in_corso(person: str, oggi) -> list:
	"""The person's published plans whose period holds ``oggi``."""
	return [
		doc
		for doc in (
			frappe.get_doc(piani.PIANO, nome)
			for nome in frappe.get_all(
				piani.PIANO,
				filters={"lead": person, "status": piani.PUBBLICATO},
				pluck="name",
				order_by="published_on desc",
			)
		)
		if R.in_corso(
			getdate(doc.starts_on) if doc.starts_on else None,
			getdate(doc.ends_on) if doc.ends_on else None,
			oggi,
		)
	]


def piani_in_corso(person: str) -> int:
	"""How many plans and programmes the person follows today: the area shows
	"Plans" when any."""
	from crm.piani import programmi

	return len(in_corso(person, getdate())) + frappe.db.count(
		programmi.PROGRAMMA, {"lead": person, "status": programmi.PUBBLICATO}
	)


def della_persona(person: str, plan: str):
	"""A plan of this person that is followed now; any other is a refusal."""
	oggi = getdate()
	for doc in in_corso(person, oggi):
		if doc.name == plan:
			return doc
	frappe.throw(_("This plan is not followed now"), frappe.PermissionError)


def _esiti(plan: str, dal, al) -> list:
	return frappe.get_all(
		piani.REGISTRO,
		filters={"plan": plan, "log_date": ("between", (dal, al))},
		fields=["name", "item_key", "log_date", "outcome"],
	)


def _voci_del_giorno(doc, giorno) -> tuple[list[dict], list[dict]]:
	momenti, voci = piani.righe_del_piano(doc)
	del_giorno = R.momenti_del_giorno(momenti, giorno)
	chiavi = {m["key"] for m in del_giorno}
	return del_giorno, [v for v in voci if v["moment"] in chiavi]


@frappe.whitelist()
def area_plans(person: str) -> dict:
	"""The plans the person follows now, and how today is going on each."""
	_mia(person)
	oggi = getdate()
	voci = []
	for doc in in_corso(person, oggi):
		_momenti, di_oggi = _voci_del_giorno(doc, oggi)
		fatti = {r.item_key for r in _esiti(doc.name, oggi, oggi) if r.outcome in (R.FATTO, R.IN_PARTE)}
		voci.append(
			{
				"name": doc.name,
				"title": doc.title,
				"plan_type": doc.plan_type,
				"practitioner_name": get_fullname(doc.practitioner),
				"today": len(di_oggi),
				"done_today": len([v for v in di_oggi if v["key"] in fatti]),
				# a stage's plan says which programme it is part of
				"programme": doc.get("programme"),
				"features": piani.descrivi_tipo(doc.plan_type)["features"],
			}
		)
	return {"plans": voci}


@frappe.whitelist()
def area_programmes(person: str) -> dict:
	"""The programmes the person follows now, stage by stage."""
	from crm.piani import programmi

	_mia(person)
	return {"programmes": programmi.area_dei_programmi(person)}


@frappe.whitelist(methods=["POST"])
def finish_stage(person: str, programme: str, stage: str) -> dict:
	"""At one's own pace, the person says the open stage is finished: the next opens."""
	from crm.piani import programmi

	_mia(person)
	programmi.finisce_la_tappa(person, programme, stage)
	return {"programmes": programmi.area_dei_programmi(person)}


def per_la_persona(voce: dict, doc, contesti: dict[str, dict]) -> dict:
	"""An item as the person reads it: what to do, and nothing of the tables."""
	riga = {
		"key": voce["key"],
		"kind": voce["kind"],
		"note": voce.get("note"),
		"times_per_week": voce.get("times_per_week"),
	}
	del_genere = piani.genere(voce["kind"])
	if del_genere and del_genere.per_la_persona:
		riga.update(del_genere.per_la_persona(voce, doc, contesti.get(voce["kind"], {})))
	return riga


def contesti(voci: list[dict]) -> dict[str, dict]:
	"""What each kind of the day's items needs, once: an exchange diet's choices."""
	fatto = {}
	for chiave in {v["kind"] for v in voci}:
		del_genere = piani.genere(chiave)
		if del_genere and del_genere.contesto:
			fatto[chiave] = del_genere.contesto([v for v in voci if v["kind"] == chiave])
	return fatto


@frappe.whitelist()
def area_plan(person: str, plan: str, day: str | None = None) -> dict:
	"""A plan on a day: its moments, its items, what was answered, what is left
	this week. From two days back to a week ahead."""
	_mia(person)
	doc = della_persona(person, plan)
	oggi = getdate()
	giorno = getdate(day) if day else oggi
	if not (add_days(oggi, -R.GIORNI_RECUPERO) <= giorno <= add_days(oggi, GIORNI_AVANTI)):
		frappe.throw(_("This day is not shown"))
	momenti, voci = _voci_del_giorno(doc, giorno)
	lunedi, domenica = R.settimana(giorno)
	settimana = _esiti(doc.name, lunedi, domenica)
	del_giorno = {r.item_key: r.outcome for r in settimana if getdate(r.log_date) == giorno}
	del_contesto = contesti(voci)
	righe = []
	for momento in momenti:
		elementi = []
		for voce in voci:
			if voce["moment"] != momento["key"]:
				continue
			riga = per_la_persona(voce, doc, del_contesto)
			riga["outcome"] = del_giorno.get(voce["key"])
			riga["left_this_week"] = R.restano(
				voce.get("times_per_week"), [r.outcome for r in settimana if r.item_key == voce["key"]]
			)
			elementi.append(riga)
		if elementi:
			righe.append({**momento, "items": elementi})
	return {
		"plan": {
			"name": doc.name,
			"title": doc.title,
			"plan_type": doc.plan_type,
			"practitioner_name": get_fullname(doc.practitioner),
			"instructions": doc.instructions,
			"starts_on": doc.starts_on,
			"ends_on": doc.ends_on,
			"features": piani.descrivi_tipo(doc.plan_type)["features"],
		},
		"day": str(giorno),
		"today": str(oggi),
		"can_log": R.si_segna(giorno, oggi),
		"days": [str(add_days(oggi, n)) for n in range(-R.GIORNI_RECUPERO, GIORNI_AVANTI + 1)],
		"moments": righe,
	}


@frappe.whitelist(methods=["POST"])
def log_item(
	person: str,
	plan: str,
	item: str,
	outcome: str | None = None,
	day: str | None = None,
	effort: int | str | None = None,
	note: str | None = None,
) -> dict:
	"""One tap: how an item went on a day. Tapped again, it changes; with no
	outcome, the answer is taken back."""
	_mia(person)
	doc = della_persona(person, plan)
	oggi = getdate()
	giorno = getdate(day) if day else oggi
	if not R.si_segna(giorno, oggi):
		frappe.throw(_("A day is marked when it comes, or within two days"))
	if outcome and outcome not in R.ESITI:
		frappe.throw(_("{0} is not how it went").format(outcome))
	voce = next((v for v in doc.items if v.item_key == item), None)
	if not voce:
		frappe.throw(_("This is not in the plan"))
	fatica = cint(effort) if effort not in (None, "") else None
	if fatica is not None and not 0 <= fatica <= 10:
		frappe.throw(_("Effort or pain goes from 0 to 10"))
	esistente = frappe.db.get_value(
		piani.REGISTRO, {"plan": doc.name, "item_key": item, "log_date": giorno}, "name"
	)
	if not outcome:
		if esistente:
			frappe.delete_doc(piani.REGISTRO, esistente, ignore_permissions=True)
		return {"outcome": None}
	valori = {
		"outcome": outcome,
		# 0 when not said: the area does not ask it yet
		"effort": fatica or 0,
		"note": (note or "").strip()[:500] or None,
		"logged_by": frappe.session.user,
		"logged_on": now_datetime(),
	}
	if esistente:
		frappe.db.set_value(piani.REGISTRO, esistente, valori)
	else:
		frappe.get_doc(
			{
				"doctype": piani.REGISTRO,
				"plan": doc.name,
				"lead": doc.lead,
				"item_key": item,
				"moment_key": voce.moment_key,
				"log_date": giorno,
				"practitioner": doc.practitioner,
				**valori,
			}
		).insert(ignore_permissions=True)
	return {"outcome": outcome}
