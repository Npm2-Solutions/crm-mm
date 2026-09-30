# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The menu for the nutritionist (design.md, "L'assistente", point 5): "obiettivi
suoi, nutrienti calcolati dalle tabelle, l'IA propone solo le ricette".

- **The targets are the nutritionist's**: kcal, proteins, carbohydrates, fats and
  fibre for a day, written on the plan.
- **The nutrients come from the tables**: the engine (`piani_regole.nutrienti`)
  counts them from the library's values for 100 g, meal by meal and day by day;
  the browser counts the same way while the plan is written.
- **The assistant proposes only recipes**: which foods of the centre's library go
  together in one meal, and how to prepare them. Of its answer the engine keeps
  the foods of the library by their id and their proportions
  (`piani_regole.ricetta`); the grams are scaled by the engine to the meal's
  energy, and every number shown comes from the tables.
- **Never about the patient**: the model reads the meal, the energy, what the
  nutritionist asks ("vegetarian", "quick to cook") and the library; not who the
  plan is for. With the patient's consent to the assistant, as every other use in
  the clinic.
- **Chosen, it becomes the nutritionist's**: its foods go into the meal, its
  method into the meal's note with the mark "AI draft, checked by … on …"; the
  plan stays a draft, to read and publish as any other. The register keeps what
  was proposed and what was kept.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import flt

from crm.assistente import modello, regole
from crm.clinica import ASSISTENTE, RICETTE
from crm.clinica import piani_regole as R
from crm.clinica.piani import CIBO
from crm.moduli import consensi
from crm.permissions import livelli
from crm.piani import api as piani

#: How many recipes a proposal holds, and how many foods of the library it reads.
MAX_RICETTE = 3
MAX_CIBI = 600

ISTRUZIONI = """{scopo}
You propose recipes for one meal of a meal plan that a nutritionist is writing.
The nutritionist sets the targets and checks every recipe; the calories and the
nutrients are computed from the centre's food tables, never by you.

Use only foods from the list, by their id, each with its grams for one person.
Propose up to three different recipes that fit the meal and what the
nutritionist asks. Each has a short title and, in a few plain sentences, how to
prepare it. No health claims, no advice, no calories or nutrients.

Answer with JSON only:
{{"recipes": [{{"title": "...", "method": "...", "foods": [{{"id": "...", "grams": 80}}]}}]}}

Write the titles and the methods in the language of the nutritionist's request
or, when it asks nothing, in the language of the food names."""


def _libreria() -> dict[str, dict]:
	"""The centre's foods, with what the tables say of them for 100 g."""
	return {
		riga.name: riga
		for riga in frappe.get_all(
			CIBO,
			filters={"enabled": 1},
			fields=["name", "food_name", "food_group", "portion_g", *R.NUTRIENTI],
			order_by="food_name asc",
			limit=MAX_CIBI,
		)
	}


def disponibile(lead: str) -> dict:
	"""Whether the session may ask for recipes for this person's menu, and if the
	person's consent is missing."""
	if not livelli.puo(RICETTE.usa) or not modello.acceso(RICETTE.chiave):
		return {}
	return {"on": True, "consent": consensi.ha_il_consenso(lead, ASSISTENTE.chiave)}


@frappe.whitelist()
def recipes_available(lead: str) -> dict:
	"""For a menu still to save: whether "Propose recipes" is offered."""
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	return disponibile(lead)


def _il_mio_menu(name: str):
	livelli.verifica(RICETTE.usa)
	doc = piani._mio_in_bozza(name)
	if doc.plan_type != R.MENU:
		frappe.throw(_("Recipes are proposed for a meal plan"))
	if not consensi.ha_il_consenso(doc.lead, ASSISTENTE.chiave):
		frappe.throw(_("The patient has not agreed to the assistant: record their consent first"))
	return doc


def _momento(doc, chiave: str):
	momento = next((m for m in doc.moments if m.moment_key == chiave), None)
	if not momento:
		frappe.throw(_("This meal is not in the plan: save the plan first"))
	return momento


def _richiesta(momento, kcal: float | None, note: str, cibi: dict[str, dict]) -> str:
	righe = [f"Meal: {momento.label or _('Meal')}"]
	if kcal:
		righe.append(f"Energy for this meal: about {round(kcal)} kcal")
	if note:
		righe.append(f"The nutritionist asks: {note}")
	righe.append("Foods (id | name | group | usual portion):")
	for nome, cibo in cibi.items():
		porzione = f"{flt(cibo.portion_g):g} g" if cibo.portion_g else "-"
		righe.append(f"{nome} | {cibo.food_name} | {cibo.food_group or '-'} | {porzione}")
	return "\n".join(righe)


def _con_i_conti(ricetta: dict, cibi: dict[str, dict]) -> dict:
	"""A recipe with the names of its foods and the nutrients the tables give."""
	voci = [
		{**voce, "food_name": cibi[voce["food"]].food_name, "food_detail": cibi[voce["food"]]}
		for voce in ricetta["items"]
	]
	return {**ricetta, "items": voci, "nutrients": R.nutrienti(voci, cibi)}


def _proposte(dati, cibi: dict[str, dict], kcal: float | None) -> list[dict]:
	"""What the engine keeps of the model's answer: recipes of the library's foods,
	scaled to the meal's energy by the tables."""
	ricette = []
	for proposta in ((dati or {}).get("recipes") or [])[:MAX_RICETTE]:
		ricetta = R.ricetta(proposta, cibi)
		if not ricetta:
			continue
		if kcal:
			ricetta["items"] = R.scala(ricetta["items"], cibi, kcal)
		ricette.append(_con_i_conti(ricetta, cibi))
	return ricette


@frappe.whitelist(methods=["POST"])
def propose_recipes(plan: str, moment: str, kcal=None, notes: str | None = None) -> dict:
	"""Up to three recipes for one meal of one's own draft menu: nothing is written
	in the plan, only the register's event."""
	doc = _il_mio_menu(plan)
	momento = _momento(doc, moment)
	energia = flt(kcal) or None
	if energia is not None and not 0 < energia <= 5000:
		frappe.throw(_("The energy of a meal is between 1 and 5000 kcal"))
	cibi = _libreria()
	if not cibi:
		frappe.throw(_("The food library is empty: add the centre's foods first"))
	risposta = modello.chiedi(
		RICETTE.chiave,
		ISTRUZIONI.format(scopo=regole.SCOPO),
		_richiesta(momento, energia, (notes or "").strip()[:500], cibi),
		json_atteso=True,
		riferimento=(piani.PIANO, doc.name),
	)
	if risposta.errore:
		return {"event": risposta.evento, "recipes": [], "error": _(risposta.errore)}
	ricette = _proposte(risposta.dati, cibi, energia)
	if not ricette:
		modello.scarta(risposta.evento)
		return {
			"event": None,
			"recipes": [],
			"error": _("The assistant proposed nothing made of the library's foods"),
		}
	return {"event": risposta.evento, "recipes": ricette}


def _in_parole(ricetta: dict, cibi: dict[str, dict]) -> str:
	"""A recipe as the register keeps it: its title, its method, its foods."""
	righe = [ricetta.get("title") or "", ricetta.get("method") or ""]
	for voce in ricetta.get("items") or []:
		cibo = cibi.get(voce.get("food"))
		righe.append(f"- {cibo.food_name if cibo else voce.get('food')}: {voce.get('quantity_g')} g")
	return "\n".join(riga for riga in righe if riga)


@frappe.whitelist(methods=["POST"])
def use_recipe(event: str, moment: str, recipe) -> dict:
	"""The nutritionist chose a recipe, as the dialog shows it: its foods go into the
	meal, its method into the meal's note with the mark. The engine reads it again:
	nothing outside the library comes in."""
	evento = frappe.get_doc(modello.EVENTO, event)
	if evento.function != RICETTE.chiave or evento.reference_doctype != piani.PIANO:
		frappe.throw(_("This is not a recipe for a plan"))
	doc = _il_mio_menu(evento.reference_name)
	momento = _momento(doc, moment)
	cibi = _libreria()
	scelta = frappe.parse_json(recipe) if isinstance(recipe, str) else (recipe or {})
	ricetta = R.ricetta(
		{
			"title": scelta.get("title"),
			"method": scelta.get("method"),
			"foods": [
				{"id": voce.get("food"), "grams": voce.get("quantity_g")}
				for voce in scelta.get("items") or []
			],
		},
		cibi,
	)
	if not ricetta:
		frappe.throw(_("A recipe needs its title and a food of the library"))
	# what the model proposed, written the way the kept recipe is, for the register
	proposte = [
		R.ricetta(p, cibi) for p in ((regole.estrai_json(evento.draft or "") or {}).get("recipes") or [])
	]
	confronto = next((p for p in proposte if p and p["title"] == ricetta["title"]), None)
	evento = modello.accetta(
		event,
		_in_parole(ricetta, cibi),
		confronto=_in_parole(confronto, cibi) if confronto else "",
	)
	segno = modello.segno(evento)
	for voce in ricetta["items"]:
		doc.append(
			"items",
			{
				"item_key": piani._chiave(),
				"moment_key": momento.moment_key,
				"kind": R.CIBO,
				"food": voce["food"],
				"quantity_g": voce["quantity_g"],
			},
		)
	testo = "\n".join(filter(None, [ricetta["title"], ricetta["method"], segno]))
	momento.note = "\n\n".join(filter(None, [momento.note, testo]))
	doc.save(ignore_permissions=True)
	return piani.get_plan(doc.name)


@frappe.whitelist(methods=["POST"])
def discard_recipes(event: str) -> None:
	modello.scarta(event)
