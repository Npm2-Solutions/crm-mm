# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Plans on the person's page: written by a practitioner, followed in the area.

- **Who writes which** (`piani.scrivi`): the kinds of their qualification
  (`piani_regole.tipi_per`): a diet by a doctor, a biologist nutritionist or a
  dietitian; exercises at home by a physiotherapist or a doctor; a training and
  habits by whoever writes plans.
- **Who reads it**: its author, always; the others like a visit
  (`crm.clinica.dossier`), once it is published: a draft is its author's. Every
  opening is written in the access log, with the record's.
- **Published, a plan is not rewritten.** A new version starts as a draft that
  replaces it once published, or the plan is closed. Publishing closes the
  person's other plan of the same kind - one diet at a time - and who enters the
  area gets an email that says only that there is news.
- **The libraries**: the centre's foods and exercises, searched and added to by
  whoever writes plans. Nutrients come from the tables, never from a guess.
"""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_fullname, getdate, now_datetime

from crm.clinica import dossier
from crm.clinica import piani_regole as R
from crm.permissions import livelli

PIANO = "Clinic Plan"
CIBO = "Clinic Food"
ESERCIZIO = "Clinic Exercise"
REGISTRO = "Clinic Plan Log"
BOZZA, PUBBLICATO, CHIUSO = "Draft", "Published", "Closed"
#: How far back a plan shows how the days went.
GIORNI_ANDAMENTO = 14
#: What a plan's rows keep, by kind of item; the rest is dropped.
CAMPI_VOCE = (
	"kind",
	"food",
	"quantity_g",
	"food_group",
	"portions",
	"alternatives",
	"exercise",
	"sets",
	"reps",
	"duration",
	"rest",
	"load",
	"text",
	"times_per_week",
	"note",
)


# ------------------------------------------------------------------ who reads, who writes


def puo_leggere(doc, user: str | None = None) -> bool:
	"""Its author, always; the others by the dossier's rules, once published."""
	user = user or frappe.session.user
	if doc.get("practitioner") == user:
		return True
	if doc.get("status") == BOZZA:
		return False
	return dossier.legge_le_altre(doc, user)


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return livelli.puo("piani.scrivi", user)
	if ptype in ("write", "delete"):
		# a draft is its author's; what is published is replaced or closed
		return doc.get("practitioner") == user and doc.get("status") == BOZZA
	if ptype in ("submit", "cancel", "amend"):
		return False
	return puo_leggere(doc, user)


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	piano = frappe.qb.DocType(PIANO)
	condizione = piano.practitioner == user
	condivisa = dossier.condizione_condivisa(piano, user)
	if condivisa is not None:
		condizione = condizione | ((piano.status != BOZZA) & condivisa)
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def tipi_consentiti(user: str | None = None) -> list[str]:
	"""The kinds of plan the session writes: none without `piani.scrivi`."""
	user = user or frappe.session.user
	if not livelli.puo("piani.scrivi", user):
		return []
	return R.tipi_per(dossier.disciplina_di(user))


def _legge() -> bool:
	return livelli.puo("clinica.vedi") or livelli.puo("clinica.scrivi") or livelli.puo("piani.scrivi")


def _della_persona(lead: str) -> None:
	if not _legge():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _piano(name: str):
	doc = frappe.get_doc(PIANO, name)
	frappe.has_permission("CRM Lead", "read", doc=doc.lead, throw=True)
	if not puo_leggere(doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc


def _mio_in_bozza(name: str):
	doc = _piano(name)
	if doc.practitioner != frappe.session.user:
		frappe.throw(_("A plan is changed by who wrote it"), frappe.PermissionError)
	if doc.status != BOZZA:
		frappe.throw(_("A published plan is not rewritten: make a new version"))
	return doc


# ------------------------------------------------------------------ reading


def _andamento(piani: list[str], dal) -> dict[str, list]:
	"""The check-ins of these plans from ``dal``, by plan."""
	per_piano: dict[str, list] = {}
	if not piani:
		return per_piano
	for riga in frappe.get_all(
		REGISTRO,
		filters={"plan": ("in", piani), "log_date": (">=", dal)},
		fields=["plan", "item_key", "log_date", "outcome", "effort", "note"],
		order_by="log_date asc",
	):
		per_piano.setdefault(riga.plan, []).append(riga)
	return per_piano


def _riga(doc, andamento: list | None = None) -> dict:
	return {
		"name": doc.name,
		"title": doc.title,
		"plan_type": doc.plan_type,
		"status": doc.status,
		"starts_on": doc.starts_on,
		"ends_on": doc.ends_on,
		"practitioner": doc.practitioner,
		"practitioner_name": get_fullname(doc.practitioner),
		"published_on": doc.published_on,
		"closed_on": doc.closed_on,
		"replaces": doc.replaces,
		"replaced_by": doc.replaced_by,
		"mine": doc.practitioner == frappe.session.user,
		"items": len(doc.items),
		# how the last days went, counted: not a score
		"summary": R.riepilogo([r.outcome for r in andamento or []]),
	}


@frappe.whitelist()
def get_plans(lead: str) -> dict:
	"""The person's plans the session reads, newest first, with the kinds it writes."""
	_della_persona(lead)
	documenti = [
		doc
		for doc in (
			frappe.get_doc(PIANO, nome)
			for nome in frappe.get_all(PIANO, filters={"lead": lead}, pluck="name", order_by="creation desc")
		)
		if puo_leggere(doc)
	]
	# "done this week": from Monday, as the patient's week goes
	lunedi, _domenica = R.settimana(getdate())
	andamento = _andamento([d.name for d in documenti if d.status != BOZZA], lunedi)
	return {
		"plans": [_riga(doc, andamento.get(doc.name)) for doc in documenti],
		"kinds": tipi_consentiti(),
	}


def _cibi(nomi: set[str]) -> dict[str, dict]:
	if not nomi:
		return {}
	return {
		riga.name: riga
		for riga in frappe.get_all(
			CIBO,
			filters={"name": ("in", list(nomi))},
			fields=["name", "food_name", "food_group", "portion_g", *R.NUTRIENTI],
		)
	}


def _esercizi(nomi: set[str]) -> dict[str, dict]:
	"""The exercises of a plan, with their pictures: the centre's own, or the
	library's from where the agency hosts them (`librerie.media`)."""
	from crm.clinica.librerie import media

	if not nomi:
		return {}
	return {
		riga.name: frappe._dict({**riga, **media(riga)})
		for riga in frappe.get_all(
			ESERCIZIO,
			filters={"name": ("in", list(nomi))},
			fields=[
				"name",
				"exercise_name",
				"body_part",
				"equipment",
				"image",
				"video_url",
				"instructions",
				"attribution",
				"source",
				"media_path",
				"animation_path",
			],
		)
	}


def righe_del_piano(doc) -> tuple[list[dict], list[dict]]:
	"""The moments and the items of a plan, the items with what the libraries say
	of their food or exercise."""
	cibi = _cibi({v.food for v in doc.items if v.food})
	esercizi = _esercizi({v.exercise for v in doc.items if v.exercise})
	momenti = [
		{
			"key": m.moment_key,
			"label": m.label,
			"day": m.day,
			"time": str(m.time) if m.time else None,
			"note": m.note,
		}
		for m in doc.moments
	]
	voci = []
	for voce in doc.items:
		riga = {"key": voce.item_key, "moment": voce.moment_key, **{c: voce.get(c) for c in CAMPI_VOCE}}
		if voce.food and voce.food in cibi:
			cibo = cibi[voce.food]
			riga["food_name"] = cibo.food_name
			riga["food_detail"] = cibo
			riga["kcal"] = R.calorie(cibo.kcal, voce.quantity_g)
		if voce.exercise and voce.exercise in esercizi:
			riga["exercise_name"] = esercizi[voce.exercise].exercise_name
			riga["exercise_detail"] = esercizi[voce.exercise]
		voci.append(riga)
	return momenti, voci


def _ricette(doc) -> dict:
	"""Whether the author may ask the assistant for recipes on this draft."""
	if doc.practitioner != frappe.session.user or doc.status != BOZZA or doc.plan_type != R.MENU:
		return {}
	from crm.clinica import menu

	return menu.disponibile(doc.lead)


@frappe.whitelist()
def get_plan(name: str) -> dict:
	"""A plan to read or to go on writing, with how the last two weeks went. The
	opening goes in the access log."""
	doc = _piano(name)
	doc.add_viewed()
	momenti, voci = righe_del_piano(doc)
	dal = add_days(getdate(), -(GIORNI_ANDAMENTO - 1))
	return {
		**_riga(doc),
		"lead": doc.lead,
		"instructions": doc.instructions,
		"show_calories": cint(doc.show_calories),
		# the nutritionist's targets for a day; the totals come from the tables
		"targets": {nome: doc.get(f"target_{nome}") or None for nome in R.NUTRIENTI},
		"moments": momenti,
		"items": voci,
		"logs": _andamento([doc.name], dal).get(doc.name, []),
		"days": [str(add_days(dal, giorno)) for giorno in range(GIORNI_ANDAMENTO)],
		"can_edit": doc.practitioner == frappe.session.user and doc.status == BOZZA,
		"recipes": _ricette(doc),
		"can_close": doc.practitioner == frappe.session.user and doc.status == PUBBLICATO,
		"can_version": doc.status != BOZZA
		and doc.plan_type in tipi_consentiti()
		and not doc.replaced_by
		and not frappe.db.exists(PIANO, {"replaces": doc.name, "status": BOZZA}),
	}


# ------------------------------------------------------------------ the shopping list


def lista_della_spesa(doc, dal=None, giorni: int = 7) -> dict:
	"""What to buy for a diet's days from ``dal`` (today, or the plan's first day
	if later): the foods with their grams, an exchange diet's portions by group,
	only within the plan's period."""
	inizio = getdate(doc.starts_on) if doc.starts_on else None
	fine = getdate(doc.ends_on) if doc.ends_on else None
	oggi = getdate()
	dal = getdate(dal) if dal else max(oggi, inizio or oggi)
	quanti = max(1, min(cint(giorni) or 7, R.MAX_GIORNI_SPESA))
	momenti, voci = righe_del_piano(doc)
	cibi = {v["food"]: v["food_detail"] for v in voci if v.get("food") and v.get("food_detail")}
	lista = R.spesa(momenti, voci, cibi, R.giorni_del_periodo(dal, quanti, inizio, fine))
	return {
		**lista,
		"from": str(dal),
		"until": str(add_days(dal, quanti - 1)),
		"asked": quanti,
		"plan": {"name": doc.name, "title": doc.title, "plan_type": doc.plan_type},
	}


@frappe.whitelist()
def shopping_list(name: str, start: str | None = None, days: int = 7) -> dict:
	"""A diet's shopping list, to give the patient: opening it is reading the plan."""
	doc = _piano(name)
	if doc.plan_type not in (R.MENU, R.SCAMBI):
		frappe.throw(_("Only a diet has a shopping list"))
	doc.add_viewed()
	return lista_della_spesa(doc, start, days)


# ------------------------------------------------------------------ writing


def _chiave() -> str:
	return secrets.token_hex(4)


def _righe(dati: dict) -> tuple[list[dict], list[dict]]:
	"""The moments and items as sent, each with its key: kept if it had one, so the
	check-ins of an item stay with it."""
	momenti = []
	for momento in dati.get("moments") or []:
		momenti.append(
			{
				"key": (momento.get("key") or _chiave()),
				"label": (momento.get("label") or "").strip(),
				"day": momento.get("day") or R.OGNI_GIORNO,
				"time": momento.get("time") or None,
				"note": (momento.get("note") or "").strip() or None,
			}
		)
	voci = []
	for voce in dati.get("items") or []:
		riga = {c: voce.get(c) for c in CAMPI_VOCE}
		riga["key"] = voce.get("key") or _chiave()
		riga["moment"] = voce.get("moment")
		# "every time" is no weekly count
		riga["times_per_week"] = cint(voce.get("times_per_week")) or None
		voci.append(riga)
	return momenti, voci


def _controlla(tipo: str, momenti: list[dict], voci: list[dict]) -> None:
	problemi = R.valida(tipo, momenti, voci)
	if problemi:
		frappe.throw(
			"<br>".join(dict.fromkeys(p.testo(_) for p in problemi)), title=_("The plan is not ready")
		)
	cibi = {v["food"] for v in voci if v.get("kind") == R.CIBO and v.get("food")}
	esercizi = {v["exercise"] for v in voci if v.get("kind") == R.ESERCIZIO and v.get("exercise")}
	for doctype, nomi in ((CIBO, cibi), (ESERCIZIO, esercizi)):
		trovati = set(
			frappe.get_all(doctype, filters={"name": ("in", list(nomi)), "enabled": 1}, pluck="name")
		)
		if nomi - trovati:
			frappe.throw(_("Something in the plan is no longer in the library"))


def _scrivi(doc, dati: dict, momenti: list[dict], voci: list[dict]) -> None:
	doc.title = (dati.get("title") or "").strip() or _(doc.plan_type)
	doc.starts_on = dati.get("starts_on") or None
	doc.ends_on = dati.get("ends_on") or None
	if doc.starts_on and doc.ends_on and getdate(doc.ends_on) < getdate(doc.starts_on):
		frappe.throw(_("A plan ends after it starts"))
	doc.instructions = (dati.get("instructions") or "").strip() or None
	doc.show_calories = 1 if cint(dati.get("show_calories")) else 0
	obiettivi = dati.get("targets") or {}
	for nome in R.NUTRIENTI:
		# a menu's targets only: the other kinds have none
		valore = flt(obiettivi.get(nome)) if doc.plan_type == R.MENU else 0
		doc.set(f"target_{nome}", valore if valore > 0 else None)
	doc.set(
		"moments",
		[
			{
				"moment_key": m["key"],
				"label": m["label"],
				"day": m["day"],
				"time": m["time"],
				"note": m["note"],
			}
			for m in momenti
		],
	)
	doc.set(
		"items",
		[
			{
				"item_key": v["key"],
				"moment_key": v["moment"],
				**{c: v.get(c) for c in CAMPI_VOCE},
				# the numbers are numbers; what the patient reads is text
				"quantity_g": flt(v.get("quantity_g")) or None,
				"portions": flt(v.get("portions")) or None,
				"sets": cint(v.get("sets")) or None,
				"times_per_week": cint(v.get("times_per_week")) or None,
			}
			for v in voci
		],
	)


@frappe.whitelist(methods=["POST"])
def save_plan(lead: str, data, name: str | None = None) -> dict:
	"""A draft of the session's own, new or carried on. The first plan makes a patient."""
	livelli.verifica("piani.scrivi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	if name:
		doc = _mio_in_bozza(name)
		if doc.lead != lead:
			frappe.throw(_("This plan belongs to somebody else"))
	else:
		doc = frappe.new_doc(PIANO)
		doc.lead = lead
		doc.practitioner = frappe.session.user
		doc.status = BOZZA
	tipo = dati.get("plan_type") or doc.plan_type
	if tipo not in tipi_consentiti():
		frappe.throw(_("Your qualification does not write a plan of this kind"), frappe.PermissionError)
	doc.plan_type = tipo
	doc.discipline = dossier.disciplina_di(frappe.session.user)
	momenti, voci = _righe(dati)
	_controlla(tipo, momenti, voci)
	_scrivi(doc, dati, momenti, voci)
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	return get_plan(doc.name)


@frappe.whitelist(methods=["POST"])
def publish_plan(name: str) -> dict:
	"""The draft goes to the person's area. It closes the plan it replaces, and the
	person's other plan of the same kind: one at a time."""
	doc = _mio_in_bozza(name)
	if doc.plan_type not in tipi_consentiti():
		frappe.throw(_("Your qualification does not write a plan of this kind"), frappe.PermissionError)
	momenti, voci = righe_del_piano(doc)
	if not voci:
		frappe.throw(_("A plan to follow has something in it"))
	_controlla(doc.plan_type, momenti, voci)
	adesso = now_datetime()
	for vecchio in frappe.get_all(
		PIANO,
		filters={
			"lead": doc.lead,
			"plan_type": doc.plan_type,
			"status": PUBBLICATO,
			"name": ("!=", doc.name),
		},
		pluck="name",
	):
		_chiudi(frappe.get_doc(PIANO, vecchio), adesso, sostituito_da=doc.name)
	doc.flags.dal_piano = True
	doc.status = PUBBLICATO
	doc.published_on = adesso
	doc.save(ignore_permissions=True)
	_avvisa(doc.lead)
	return get_plan(doc.name)


def _chiudi(doc, adesso, sostituito_da: str | None = None) -> None:
	doc.flags.dal_piano = True
	doc.status = CHIUSO
	doc.closed_on = adesso
	if sostituito_da:
		doc.replaced_by = sostituito_da
	doc.save(ignore_permissions=True)


def _avvisa(lead: str) -> None:
	# the same news as a message: the area says what it is
	from crm.clinica.area import messaggi

	messaggi._avvisa(lead)


@frappe.whitelist(methods=["POST"])
def close_plan(name: str) -> dict:
	"""No longer to follow: it leaves the area and stays in the record."""
	doc = _piano(name)
	if doc.practitioner != frappe.session.user:
		frappe.throw(_("A plan is closed by who wrote it"), frappe.PermissionError)
	if doc.status != PUBBLICATO:
		frappe.throw(_("Only a published plan is closed"))
	_chiudi(doc, now_datetime())
	return get_plan(doc.name)


@frappe.whitelist(methods=["POST"])
def new_version(name: str) -> dict:
	"""A draft copy of a published or closed plan, to change and publish in its place."""
	vecchio = _piano(name)
	if vecchio.status == BOZZA:
		frappe.throw(_("A draft is changed as it is"))
	if vecchio.plan_type not in tipi_consentiti():
		frappe.throw(_("Your qualification does not write a plan of this kind"), frappe.PermissionError)
	gia = frappe.db.get_value(PIANO, {"replaces": vecchio.name, "status": BOZZA}, "name")
	if gia:
		frappe.throw(_("A new version of this plan is already being written"))
	nuovo = frappe.new_doc(PIANO)
	nuovo.update(
		{
			"lead": vecchio.lead,
			"plan_type": vecchio.plan_type,
			"title": vecchio.title,
			"status": BOZZA,
			"practitioner": frappe.session.user,
			"discipline": dossier.disciplina_di(frappe.session.user),
			"starts_on": None,
			"ends_on": vecchio.ends_on,
			"instructions": vecchio.instructions,
			"show_calories": vecchio.show_calories,
			"replaces": vecchio.name,
		}
	)
	for momento in vecchio.moments:
		nuovo.append("moments", {c: momento.get(c) for c in ("moment_key", "label", "day", "time")})
	for voce in vecchio.items:
		nuovo.append(
			"items",
			{
				"item_key": voce.item_key,
				"moment_key": voce.moment_key,
				**{c: voce.get(c) for c in CAMPI_VOCE},
			},
		)
	nuovo.insert(ignore_permissions=True)
	return get_plan(nuovo.name)


@frappe.whitelist(methods=["POST"])
def delete_draft(name: str) -> None:
	"""A draft is thrown away by who wrote it; a published plan never."""
	doc = _mio_in_bozza(name)
	frappe.delete_doc(PIANO, doc.name, ignore_permissions=True)


# ------------------------------------------------------------------ the libraries


def _cerca(doctype: str, campo: str, testo: str | None, filtri: dict, campi: list[str]) -> list[dict]:
	filtri = {"enabled": 1, **{k: v for k, v in filtri.items() if v}}
	parole = (testo or "").strip()
	if parole:
		filtri[campo] = ("like", f"%{parole}%")
	return frappe.get_all(doctype, filters=filtri, fields=campi, order_by=f"{campo} asc", limit=30)


@frappe.whitelist()
def search_foods(text: str | None = None, group: str | None = None) -> list[dict]:
	livelli.verifica("piani.scrivi")
	return _cerca(
		CIBO,
		"food_name",
		text,
		{"food_group": group},
		["name", "food_name", "food_group", "portion_g", *R.NUTRIENTI, "source"],
	)


@frappe.whitelist()
def search_exercises(text: str | None = None, body_part: str | None = None) -> list[dict]:
	livelli.verifica("piani.scrivi")
	return _cerca(
		ESERCIZIO,
		"exercise_name",
		text,
		{"body_part": body_part},
		["name", "exercise_name", "body_part", "equipment", "image", "video_url"],
	)


@frappe.whitelist(methods=["POST"])
def add_food(
	food_name: str,
	food_group: str,
	portion_g=None,
	kcal=None,
	source_note: str | None = None,
	protein_g=None,
	carbs_g=None,
	fat_g=None,
	fibre_g=None,
) -> dict:
	"""A food of the centre, when the library has not got it: its values for 100 g
	from a table, whose name goes with it."""
	livelli.verifica("piani.scrivi")
	valori = {"kcal": kcal, "protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g, "fibre_g": fibre_g}
	doc = frappe.get_doc(
		{
			"doctype": CIBO,
			"food_name": (food_name or "").strip(),
			"food_group": food_group,
			"portion_g": flt(portion_g) or None,
			**{nome: flt(valore) if valore not in (None, "") else None for nome, valore in valori.items()},
			"source": "Centre",
			"source_note": source_note,
		}
	).insert(ignore_permissions=True)
	return {
		"name": doc.name,
		"food_name": doc.food_name,
		"food_group": doc.food_group,
		"portion_g": doc.portion_g,
		**{nome: doc.get(nome) for nome in R.NUTRIENTI},
	}


@frappe.whitelist(methods=["POST"])
def add_exercise(
	exercise_name: str,
	body_part: str | None = None,
	instructions: str | None = None,
	video_url: str | None = None,
) -> dict:
	"""An exercise of the centre: how it is done, and a video of the centre's if any."""
	livelli.verifica("piani.scrivi")
	doc = frappe.get_doc(
		{
			"doctype": ESERCIZIO,
			"exercise_name": (exercise_name or "").strip(),
			"body_part": body_part or None,
			"instructions": instructions,
			"video_url": (video_url or "").strip() or None,
		}
	).insert(ignore_permissions=True)
	return {
		"name": doc.name,
		"exercise_name": doc.exercise_name,
		"body_part": doc.body_part,
		"video_url": doc.video_url,
	}
