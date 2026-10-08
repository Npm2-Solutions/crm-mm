# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's plans, on the CRM's engine (`crm.piani`): the diets and the
exercises at home, the foods, and who reads what carries health data.

- **Its kinds** (`piani_regole`): a menu and an exchange diet a doctor, a
  biologist nutritionist or a dietitian writes; exercises at home a
  physiotherapist or a doctor. Health data: switched on with the clinic.
- **What a health professional writes is health data**, whatever its kind: a
  nutritionist's habits too, a doctor's programme (`dossier.e_sanitario`, by the
  author's qualification).
- **Who reads them**: their author, always; the others like a visit
  (`crm.clinica.dossier`, registered with `crm.permissions.sanitari`), once
  published - every opening in the access log.
- **Its items**: a food and how much, with what instead, the calories from the
  tables only if the practitioner shows them; a food group and its portions, the
  patient choosing the food. Their fields are the clinic's own on the CRM's plan
  (`crm/clinica/custom`).
- **A menu's targets** for a day, the nutritionist's; the totals come from the
  tables, never from a guess, and the assistant proposes only recipes (`menu`).
- **The shopping list** of a diet, for the patient.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, get_fullname

from crm.clinica import piani_regole as R
from crm.permissions import livelli
from crm.piani import api as piani

CIBO = "Clinic Food"
#: A plan's fields that are the clinic's: the calories shown, a menu's targets.
CAMPI_PIANO = ("show_calories", *(f"target_{nome}" for nome in R.NUTRIENTI))


# ------------------------------------------------------------------ the foods


def cibi(nomi: set[str]) -> dict[str, dict]:
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


def _cibo_per_l_autore(voce: dict, cibo: dict | None) -> dict:
	if not cibo:
		return {}
	return {
		"food_name": cibo.food_name,
		"food_detail": cibo,
		"kcal": R.calorie(cibo.kcal, voce.get("quantity_g")),
	}


def _cibo_per_il_paziente(voce: dict, piano, contesto: dict) -> dict:
	riga = {
		"food_name": voce.get("food_name"),
		# its group: the food's mark, and the kitchen's measure of its grams
		"food_group": (voce.get("food_detail") or {}).get("food_group"),
		"quantity_g": voce.get("quantity_g"),
		"alternatives": voce.get("alternatives"),
	}
	# calories only if the practitioner chose to show them
	if cint(piano.get("show_calories")):
		riga["kcal"] = voce.get("kcal")
	return riga


def scelte(gruppi: set[str]) -> dict[str, list]:
	"""The foods of these groups the patient chooses from, a portion each."""
	if not gruppi:
		return {}
	fatto: dict[str, list] = {}
	for cibo in frappe.get_all(
		CIBO,
		filters={"food_group": ("in", list(gruppi)), "enabled": 1},
		fields=["food_name", "food_group", "portion_g"],
		order_by="food_name asc",
		limit=200,
	):
		fatto.setdefault(cibo.food_group, []).append(
			{"food_name": cibo.food_name, "portion_g": cibo.portion_g}
		)
	return fatto


def _gruppi_del_giorno(voci: list[dict]) -> dict:
	return {"choices": scelte({v.get("food_group") for v in voci if v.get("food_group")})}


def _gruppo_per_il_paziente(voce: dict, piano, contesto: dict) -> dict:
	return {
		"food_group": voce.get("food_group"),
		"portions": voce.get("portions"),
		# the patient chooses within the limits: the group's foods, a portion each
		"choices": (contesto.get("choices") or {}).get(voce.get("food_group"), []),
	}


# ------------------------------------------------------------------ what a diet keeps


def _legge_il_piano(doc) -> dict:
	if doc.plan_type not in R.DIETE_TIPI:
		return {}
	risposta = {
		"show_calories": cint(doc.get("show_calories")),
		# the nutritionist's targets for a day; the totals come from the tables
		"targets": {nome: doc.get(f"target_{nome}") or None for nome in R.NUTRIENTI},
	}
	if doc.practitioner == frappe.session.user and doc.status == piani.BOZZA and doc.plan_type == R.MENU:
		from crm.clinica import menu

		# whether the author may ask the assistant for recipes on this draft
		risposta["recipes"] = menu.disponibile(doc.lead)
	return risposta


def _scrive_il_piano(doc, dati: dict) -> None:
	dieta = doc.plan_type in R.DIETE_TIPI
	doc.set("show_calories", 1 if dieta and cint(dati.get("show_calories")) else 0)
	obiettivi = dati.get("targets") or {}
	for nome in R.NUTRIENTI:
		# a menu's targets only: the other kinds have none
		valore = flt(obiettivi.get(nome)) if doc.plan_type == R.MENU else 0
		doc.set(f"target_{nome}", valore if valore > 0 else None)


# ------------------------------------------------------------------ the shopping list


def lista_della_spesa(doc, dal=None, giorni: int = 7) -> dict:
	"""What to buy for a diet's days from ``dal`` (today, or the plan's first day
	if later): the foods with their grams, an exchange diet's portions by group,
	only within the plan's period."""
	from frappe.utils import add_days, getdate

	inizio = getdate(doc.starts_on) if doc.starts_on else None
	fine = getdate(doc.ends_on) if doc.ends_on else None
	oggi = getdate()
	dal = getdate(dal) if dal else max(oggi, inizio or oggi)
	quanti = max(1, min(cint(giorni) or 7, R.MAX_GIORNI_SPESA))
	momenti, voci = piani.righe_del_piano(doc)
	del_piano = {v["food"]: v["food_detail"] for v in voci if v.get("food") and v.get("food_detail")}
	lista = R.spesa(momenti, voci, del_piano, R.giorni_del_periodo(dal, quanti, inizio, fine))
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
	doc = piani._piano(name)
	if doc.plan_type not in R.DIETE_TIPI:
		frappe.throw(_("Only a diet has a shopping list"))
	piani._aperto(doc)
	return lista_della_spesa(doc, start, days)


def lista_per_il_paziente(doc, dal, giorni) -> dict:
	"""The shopping list as the patient reads it: the groups with their choices, the
	plan's own words, no calories."""
	lista = lista_della_spesa(doc, dal, giorni)
	del_gruppo = scelte({g["food_group"] for g in lista["groups"]})
	for gruppo in lista["groups"]:
		gruppo["choices"] = del_gruppo.get(gruppo["food_group"], [])
	lista["plan"]["practitioner_name"] = get_fullname(doc.practitioner)
	return lista


# ------------------------------------------------------------------ the library


@frappe.whitelist()
def search_foods(text: str | None = None, group: str | None = None) -> list[dict]:
	return piani.cerca(
		CIBO,
		"food_name",
		text,
		{"food_group": group},
		["name", "food_name", "food_group", "portion_g", *R.NUTRIENTI, "source"],
	)


@frappe.whitelist()
def browse_foods(text: str | None = None, group: str | None = None, start: int | str = 0) -> dict:
	"""The foods' library a page at a time, filtered by group, with their values for
	100 g: what a diet's editor browses."""
	return piani.sfoglia(
		CIBO,
		"food_name",
		text,
		{"food_group": group},
		["name", "food_name", "food_group", "portion_g", *R.NUTRIENTI, "source"],
		("food_group",),
		start,
		uso="food",
		# the drinks are hundreds of mineral waters: after the foods
		in_fondo={"food_group": ["Drinks"]},
	)


@frappe.whitelist(methods=["POST"])
def add_food(
	food_name: str,
	food_group: str,
	portion_g: float | str | None = None,
	kcal: float | str | None = None,
	source_note: str | None = None,
	protein_g: float | str | None = None,
	carbs_g: float | str | None = None,
	fat_g: float | str | None = None,
	fibre_g: float | str | None = None,
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


# ------------------------------------------------------------------ into the CRM's engine


ESTENSIONE = piani.Estensione(legge=_legge_il_piano, scrive=_scrive_il_piano, copia=CAMPI_PIANO)


def registra() -> None:
	"""The clinic's kinds of item, and what a diet keeps."""
	piani.registra_genere(
		piani.Genere(
			R.CIBO,
			campo="food",
			libreria=CIBO,
			dettagli=cibi,
			per_l_autore=_cibo_per_l_autore,
			per_la_persona=_cibo_per_il_paziente,
			numeri={"quantity_g": flt},
		)
	)
	piani.registra_genere(
		piani.Genere(
			R.GRUPPO,
			per_la_persona=_gruppo_per_il_paziente,
			contesto=_gruppi_del_giorno,
			numeri={"portions": flt},
		)
	)
	piani.registra_estensione(ESTENSIONE)
