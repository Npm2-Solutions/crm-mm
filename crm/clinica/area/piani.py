# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The plans in the patient area: what to do on a day, one tap an item.

- **The plans followed now** (`area_plans`): the published ones whose period
  holds today, each with how today is going.
- **A day** (`area_plan`): the plan's moments of that day - every day's and that
  weekday's - each with its items as the patient reads them: the food and how
  much, and what instead; the portions of a group, with the foods of that group
  to choose from; the exercise with its sets, a picture, a video and how it is
  done; the habit. Calories only if the practitioner chose to show them.
- **One tap** (`log_item`): done, partly, skipped; one answer an item a day,
  changed with another tap. A missed day is made up within two days, never a day
  ahead (`piani_regole.si_segna`).
- **The week**: an item asked so many times a week says how many are left; what
  is shown is what is left to do, never what went wrong.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_fullname, getdate, now_datetime

from crm.clinica import piani
from crm.clinica import piani_regole as R
from crm.clinica import tabelle as T
from crm.clinica.area.api import _mia

#: How far ahead the patient looks at a plan: next week's menu, to shop for it.
GIORNI_AVANTI = 6


def _in_corso(person: str, oggi) -> list:
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
	"""How many plans the person follows today: the area shows "Plans" when any."""
	return len(_in_corso(person, getdate()))


def _della_persona(person: str, plan: str):
	"""A plan of this person that is followed now; any other is a refusal."""
	oggi = getdate()
	for doc in _in_corso(person, oggi):
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
	for doc in _in_corso(person, oggi):
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
			}
		)
	return {"plans": voci}


def _immagine(url: str | None) -> str | None:
	"""A picture the area can show: a public file of the site, or an address."""
	if url and (url.startswith("/files/") or url.startswith("https://")):
		return url
	return None


def _figura(esercizio: dict) -> tuple[str | None, str | None]:
	"""What the patient sees of an exercise, and whose it is: the centre's own
	picture; else the library's animation or picture, with the name of their
	owner; the author of a centre's exercise always."""
	propria = _immagine(esercizio.get("image"))
	della_libreria = esercizio.get("animation") or (
		None if esercizio.get("image") else esercizio.get("picture")
	)
	dal_dataset = esercizio.get("source") == T.DATASET
	if propria or not della_libreria:
		return propria, None if dal_dataset else esercizio.get("attribution")
	return della_libreria, esercizio.get("attribution")


def _per_il_paziente(voce: dict, mostra_calorie: bool, scelte: dict[str, list]) -> dict:
	"""An item as the patient reads it: what to do, and nothing of the tables."""
	riga = {
		"key": voce["key"],
		"kind": voce["kind"],
		"note": voce.get("note"),
		"times_per_week": voce.get("times_per_week"),
	}
	if voce["kind"] == R.CIBO:
		riga.update(
			{
				"food_name": voce.get("food_name"),
				"quantity_g": voce.get("quantity_g"),
				"alternatives": voce.get("alternatives"),
			}
		)
		if mostra_calorie:
			riga["kcal"] = voce.get("kcal")
	elif voce["kind"] == R.GRUPPO:
		riga.update(
			{
				"food_group": voce.get("food_group"),
				"portions": voce.get("portions"),
				# the patient chooses within the limits: the group's foods, a portion each
				"choices": scelte.get(voce.get("food_group"), []),
			}
		)
	elif voce["kind"] == R.ESERCIZIO:
		esercizio = voce.get("exercise_detail") or {}
		immagine, autore = _figura(esercizio)
		riga.update(
			{
				"exercise_name": voce.get("exercise_name"),
				"sets": voce.get("sets"),
				"reps": voce.get("reps"),
				"duration": voce.get("duration"),
				"rest": voce.get("rest"),
				"load": voce.get("load"),
				"instructions": esercizio.get("instructions"),
				"image": immagine,
				"video_url": esercizio.get("video_url"),
				"attribution": autore,
			}
		)
	else:
		riga["text"] = voce.get("text")
	return riga


def _scelte(gruppi: set[str]) -> dict[str, list]:
	if not gruppi:
		return {}
	scelte: dict[str, list] = {}
	for cibo in frappe.get_all(
		piani.CIBO,
		filters={"food_group": ("in", list(gruppi)), "enabled": 1},
		fields=["food_name", "food_group", "portion_g"],
		order_by="food_name asc",
		limit=200,
	):
		scelte.setdefault(cibo.food_group, []).append(
			{"food_name": cibo.food_name, "portion_g": cibo.portion_g}
		)
	return scelte


@frappe.whitelist()
def area_plan(person: str, plan: str, day: str | None = None) -> dict:
	"""A plan on a day: its moments, its items, what was answered, what is left
	this week. From two days back to a week ahead."""
	_mia(person)
	doc = _della_persona(person, plan)
	oggi = getdate()
	giorno = getdate(day) if day else oggi
	if not (add_days(oggi, -R.GIORNI_RECUPERO) <= giorno <= add_days(oggi, GIORNI_AVANTI)):
		frappe.throw(_("This day is not shown"))
	momenti, voci = _voci_del_giorno(doc, giorno)
	lunedi, domenica = R.settimana(giorno)
	settimana = _esiti(doc.name, lunedi, domenica)
	del_giorno = {r.item_key: r.outcome for r in settimana if getdate(r.log_date) == giorno}
	scelte = _scelte({v.get("food_group") for v in voci if v["kind"] == R.GRUPPO})
	mostra = bool(cint(doc.show_calories))
	righe = []
	for momento in momenti:
		elementi = []
		for voce in voci:
			if voce["moment"] != momento["key"]:
				continue
			riga = _per_il_paziente(voce, mostra, scelte)
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
		},
		"day": str(giorno),
		"today": str(oggi),
		"can_log": R.si_segna(giorno, oggi),
		"days": [str(add_days(oggi, n)) for n in range(-R.GIORNI_RECUPERO, GIORNI_AVANTI + 1)],
		"moments": righe,
	}


@frappe.whitelist()
def area_shopping_list(person: str, plan: str, start: str | None = None, days: int = 7) -> dict:
	"""What to buy for the days ahead: the diet's foods and how much, the groups
	to choose from with their portions. From two days back to five weeks ahead."""
	_mia(person)
	doc = _della_persona(person, plan)
	if doc.plan_type not in (R.MENU, R.SCAMBI):
		frappe.throw(_("Only a diet has a shopping list"))
	oggi = getdate()
	dal = getdate(start) if start else oggi
	if not (add_days(oggi, -R.GIORNI_RECUPERO) <= dal <= add_days(oggi, R.MAX_GIORNI_SPESA)):
		frappe.throw(_("This day is not shown"))
	lista = piani.lista_della_spesa(doc, dal, days)
	scelte = _scelte({g["food_group"] for g in lista["groups"]})
	for gruppo in lista["groups"]:
		gruppo["choices"] = scelte.get(gruppo["food_group"], [])
	# the plan's own words, not the tables': no calories on a shopping list
	lista["plan"]["practitioner_name"] = get_fullname(doc.practitioner)
	return lista


@frappe.whitelist(methods=["POST"])
def log_item(
	person: str,
	plan: str,
	item: str,
	outcome: str | None = None,
	day: str | None = None,
	effort=None,
	note: str | None = None,
) -> dict:
	"""One tap: how an item went on a day. Tapped again, it changes; with no
	outcome, the answer is taken back."""
	_mia(person)
	doc = _della_persona(person, plan)
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
