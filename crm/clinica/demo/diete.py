# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's diets and exercises at home, through the clinic's kinds of plan.

The dietitian gave a menu of the week to a few of the people she sees - the foods of
the library with their grams, the targets of the day, the calories counted - and an
exchange diet to others; the physiotherapist the exercises to do at home between the
sessions, chosen by why the person came. Each at the person's last session, with that
date. Who has the area ticks them there, as the plans of the CRM are ticked.
"""

from __future__ import annotations

import json

import frappe
from frappe import _

from crm.clinica.demo import dati as D
from crm.demo.contesto import Contesto
from crm.demo.simulazione import visti_da
from crm.piani.demo import divisi, piano_alla_seduta, spuntano

MENU, SCAMBI, ESERCIZI = "Meal plan", "Exchange diet", "Home exercises"


def crea(ctx: Contesto) -> None:
	ctx.avanza(_("Diets and exercises at home"))
	nell_area = set(
		frappe.get_all(
			"CRM Area Access",
			filters={"enabled": 1, "relation": "Self", "last_seen_on": ["is", "set"]},
			pluck="lead",
		)
	)
	elena = ctx.squadra("elena")
	if elena:
		cibi = _cibi()
		con_il_menu, a_scambi = divisi(ctx, visti_da(ctx, elena, 45), nell_area, ctx.quanti(4), ctx.quanti(2))
		for persona, fine in con_il_menu:
			momenti, voci = _menu(cibi)
			piano_alla_seduta(
				ctx,
				elena,
				persona,
				fine,
				MENU,
				"Il menù della settimana",
				"I grammi sono dell'alimento come è scritto: la pasta e il riso già cotti. Se salta "
				"un pasto non lo recuperi al successivo; la lista della spesa è nell'area.",
				momenti,
				voci,
				show_calories=1,
				targets=_obiettivi(ctx),
			)
		for persona, fine in a_scambi:
			momenti, voci = _scambi()
			piano_alla_seduta(
				ctx,
				elena,
				persona,
				fine,
				SCAMBI,
				"Dieta a scambi",
				"In ogni pasto scelga liberamente dentro ogni gruppo: una porzione è quella della "
				"tabella che le ho dato.",
				momenti,
				voci,
				show_calories=1,
			)
	giulia = ctx.squadra("giulia")
	if giulia:
		esercizi = _esercizi()
		motivi = _motivi(ctx)
		a_casa, _niente = divisi(ctx, visti_da(ctx, giulia, 30), nell_area, ctx.quanti(6), 0)
		for persona, fine in a_casa:
			motivo = motivi.get(persona) or ctx.rng.choice(list(D.ESERCIZI_A_CASA))
			momenti, voci = _a_casa(esercizi, D.ESERCIZI_A_CASA.get(motivo, ()))
			piano_alla_seduta(
				ctx,
				giulia,
				persona,
				fine,
				ESERCIZI,
				f"Esercizi a casa: {motivo.lower()}",
				"Tutte le sere, prima di cena: venti minuti. Se un esercizio fa male si fermi, e me lo "
				"dica alla prossima seduta.",
				momenti,
				voci,
			)
	ctx.salva()
	spuntano(ctx)


def _cibi() -> dict[str, str]:
	"""The library's foods the menus use, by their CIQUAL code: one the centre
	switched off is left out of the menu."""
	codici = {codice for _c, _e, _o, cibi in D.MENU for codice, _g, _a in cibi}
	return {
		riga.source_code: riga.name
		for riga in frappe.get_all(
			"Clinic Food",
			filters={"source": "CIQUAL", "source_code": ["in", sorted(codici)], "enabled": 1},
			fields=["name", "source_code"],
		)
	}


def _obiettivi(ctx: Contesto) -> dict:
	"""The day's targets, by the person's needs."""
	kcal = ctx.rng.choice((1500, 1600, 1700, 1800, 1900, 2000))
	return {
		"kcal": kcal,
		"protein_g": round(kcal * 0.2 / 4),
		"carbs_g": round(kcal * 0.5 / 4),
		"fat_g": round(kcal * 0.3 / 9),
		"fibre_g": 25 if kcal < 1800 else 30,
	}


def _menu(cibi: dict[str, str]) -> tuple[list[dict], list[dict]]:
	momenti = [{"key": "giorno", "label": "Durante la giornata", "day": "Every day"}]
	voci = [
		{"kind": "Habit", "moment": "giorno", "text": testo, "times_per_week": volte}
		for testo, volte in D.ABITUDINI_DEL_MENU
	]
	for chiave, etichetta, ora, alimenti in D.MENU:
		momenti.append({"key": chiave, "label": etichetta, "day": "Every day", "time": ora})
		voci += [
			{
				"kind": "Food",
				"moment": chiave,
				"food": cibi[codice],
				"quantity_g": grammi,
				"alternatives": altro,
			}
			for codice, grammi, altro in alimenti
			if codice in cibi
		]
	return momenti, voci


def _scambi() -> tuple[list[dict], list[dict]]:
	momenti, voci = [], []
	for chiave, etichetta, ora, gruppi in D.SCAMBI:
		momenti.append({"key": chiave, "label": etichetta, "day": "Every day", "time": ora})
		voci += [
			{
				"kind": "Food group",
				"moment": chiave,
				"food_group": gruppo,
				"portions": porzioni,
				"alternatives": altro,
			}
			for gruppo, porzioni, altro in gruppi
		]
	return momenti, voci


def _esercizi() -> dict[str, str]:
	nomi = {esercizio[0] for esercizi in D.ESERCIZI_A_CASA.values() for esercizio in esercizi}
	trovati: dict[str, str] = {}
	for riga in frappe.get_all(
		"CRM Exercise",
		# by the dataset's English name: the library's own name follows the centre's language
		filters={"name_in_source": ["in", sorted(nomi)], "enabled": 1},
		fields=["name", "name_in_source"],
		order_by="name_in_source, name",
	):
		trovati.setdefault(riga.name_in_source.lower(), riga.name)
	return trovati


def _motivi(ctx: Contesto) -> dict[str, str]:
	"""Why each came to the physiotherapist, as the first visit's sheet says."""
	scheda = ctx.trova("clinic_sheet.fisio")
	if not scheda:
		return {}
	motivi = {}
	for riga in frappe.get_all(
		"Clinic Record",
		filters={"template": scheda, "docstatus": 1},
		fields=["lead", "answers"],
	):
		motivo = (json.loads(riga.answers or "{}") or {}).get("motivo")
		if motivo:
			motivi[riga.lead] = motivo
	return motivi


def _a_casa(esercizi: dict[str, str], scelti) -> tuple[list[dict], list[dict]]:
	momenti = [{"key": "sera", "label": "La sera", "day": "Every day", "time": "19:00"}]
	voci = [
		{
			"kind": "Exercise",
			"moment": "sera",
			"exercise": esercizi[nome.lower()],
			"sets": serie,
			"reps": ripetizioni,
			"duration": durata,
			"rest": recupero,
			"times_per_week": 5,
		}
		for nome, serie, ripetizioni, durata, recupero in scelti
		if nome.lower() in esercizi
	]
	return momenti, voci
