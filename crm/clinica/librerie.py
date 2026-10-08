# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's foods, the library its diets are written with (design.md, "I piani";
ricerca-design.md §2.3), in Settings > Clients > Libraries. The exercises are the
CRM's (`crm.piani.librerie`), and so is what every library shares.

- **Who** (`piani.librerie`): the manager and the medical director; a
  practitioner when the manager turns it on - the nutritionist who keeps the
  foods. Whoever writes a diet still adds a food from the editor.
- **The library** DottorCloud ships (`dati/alimenti.json`, made by
  `tabelle.libreria_ciqual`): the 3,403 foods of CIQUAL 2025 that have their
  energy, free under the Licence Ouverte, with their names in Italian, ready on
  every site. `carica_libreria` puts it in at install and at every migrate that
  brings a new version of the file. The centre never imports a table: an Italian
  one (BDA-IEO with the licence for software, CREA with the written permission)
  NPM2 adds to the library in the code.
- **The centre** changes nothing of the library's, nor of a table it imported
  before: it switches off the foods it does not use (`switch_food`) and adds its
  own, with their numbers (`save_food`), which it puts right as it likes. A food
  is switched off, not deleted: a plan may point to it.
- **Loaded again**, the library brings its numbers; what a centre wrote on one of
  its foods before - a name, a group, a portion - stays, and a name nobody
  touched follows the library's (`library_name` keeps the one it gave), in the
  centre's language (`crm.lingue`): a site loaded in English before it said it is
  in Italy loads it again, and its foods' names take Italian.
- **A number the table does not give** counts as nothing: the site keeps a number.
  A food without its energy is not in the library.
"""

from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import cint, flt

from crm.clinica import tabelle as T
from crm.permissions import livelli
from crm.piani import librerie as L

CIBO = "Clinic Food"
CENTRO = L.CENTRO
#: The library DottorCloud ships, and the table it comes from.
LIBRERIA = Path(__file__).parent / "dati" / "alimenti.json"
FONTE = "CIQUAL"
#: What the licence asks to be shown with the numbers: the source and its version.
ATTRIBUZIONE = "Anses. 2025. Ciqual French food composition table"
#: The library a site last loaded, its fingerprint and the language of its names
#: (a default of the site).
VERSIONE_CARICATA = "crm_food_library"


# ------------------------------------------------------------------ reading the library


CAMPI_CIBO = [
	"name",
	"food_name",
	"food_group",
	"portion_g",
	"enabled",
	*T.VALORI,
	"kcal_computed",
	"source",
	"source_code",
	"name_in_source",
	"source_note",
]


@frappe.whitelist()
def get_foods(
	text: str | None = None,
	group: str | None = None,
	source: str | None = None,
	enabled: str | None = None,
	start: int = 0,
) -> dict:
	"""A page of the foods, searched and filtered, with how many come from where."""
	livelli.verifica("piani.librerie")
	return L.pagina(
		CIBO,
		"food_name",
		CAMPI_CIBO,
		L.filtri_della_pagina("food_group", group, source, enabled),
		text,
		start,
	)


# ------------------------------------------------------------------ adding, switching off


@frappe.whitelist(methods=["POST"])
def save_food(name: str | None = None, data: dict | str | None = None) -> dict:
	"""A new food of the centre's, or one of its own put right: its name, its
	group, its portion, its numbers for 100 g, on or off. The library's are
	DottorCloud's: switched off or on (`switch_food`), never changed."""
	livelli.verifica("piani.librerie")
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	doc = frappe.get_doc(CIBO, name) if name else frappe.new_doc(CIBO)
	if name and (doc.source or CENTRO) != CENTRO:
		frappe.throw(_("The library's foods are switched off, not changed: add the centre's own"))
	nome = (dati.get("food_name") or "").strip()
	if not nome:
		frappe.throw(_("A food has a name"))
	if dati.get("food_group") not in T.GRUPPI:
		frappe.throw(_("Choose the group"))
	# a food without its energy counts nothing in a diet: the library leaves one out too
	if not flt(dati.get("kcal")) > 0:
		frappe.throw(_("A food needs its kcal for 100 g"))
	doc.food_name = nome[:140]
	doc.food_group = dati["food_group"]
	doc.portion_g = flt(dati.get("portion_g")) or None
	doc.enabled = 1 if cint(dati.get("enabled", 1)) else 0
	doc.source = CENTRO
	for campo in T.VALORI:
		valore = dati.get(campo)
		doc.set(campo, flt(valore) if valore not in (None, "") else None)
	doc.kcal_computed = 0
	doc.source_note = (dati.get("source_note") or "").strip()[:140] or None
	if name:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)
	return frappe.get_all(CIBO, filters={"name": doc.name}, fields=CAMPI_CIBO)[0]


@frappe.whitelist(methods=["POST"])
def switch_food(name: str, enabled: int | str = 1) -> dict:
	"""A food switched off, or on again."""
	livelli.verifica("piani.librerie")
	return L.accendi(CIBO, name, enabled)


# ------------------------------------------------------------------ the library DottorCloud ships


def carica(record: list, lingua: str | None = None) -> dict:
	"""The library's foods into the site: a new food comes in; one already there
	from CIQUAL - the library loaded before, or a table a centre imported - gets
	the library's numbers again. Its name follows the library's while the centre
	never changed it; a name, a group and a portion the centre wrote stay."""
	lingua = lingua or L.lingua_del_sito()
	presenti = {
		riga.source_code: riga
		for riga in frappe.get_all(
			CIBO,
			filters={"source": FONTE},
			fields=["name", "source_code", "food_name", "name_in_source", "library_name"],
			limit=100000,
		)
		if riga.source_code
	}
	nuovi, aggiornati, visti = [], {}, set()
	scartati = 0
	for voce in record:
		cibo = T.dalla_libreria(voce, lingua)
		if not cibo or cibo["code"] in visti:
			scartati += 1
			continue
		visti.add(cibo["code"])
		# what the table does not give counts as nothing: the site keeps a number
		numeri = {campo: cibo[campo] or 0 for campo in (*T.VALORI, "kcal_computed")}
		esistente = presenti.get(cibo["code"])
		if esistente:
			cambi = {
				**numeri,
				"name_in_source": cibo["name_in_source"],
				"library_name": cibo["name"],
				"source_note": ATTRIBUZIONE,
			}
			# a name the centre never changed - the library's, or the one of a table
			# it imported before - becomes the library's
			if (esistente.food_name or "") in (esistente.library_name, esistente.name_in_source):
				cambi["food_name"] = cibo["name"]
			aggiornati[esistente.name] = cambi
			continue
		nuovi.append(
			{
				"food_name": cibo["name"],
				"food_group": cibo["group"],
				"enabled": 1,
				**numeri,
				"source": FONTE,
				"source_code": cibo["code"],
				"name_in_source": cibo["name_in_source"],
				"library_name": cibo["name"],
				"source_note": ATTRIBUZIONE,
			}
		)
	L.inserisci(CIBO, nuovi)
	frappe.db.bulk_update(CIBO, aggiornati, chunk_size=200)
	return {"created": len(nuovi), "updated": len(aggiornati), "skipped": scartati}


def carica_libreria(forza: bool = False) -> dict | None:
	"""The library DottorCloud ships, into this site: at install, and at every
	migrate whose file is not the one the site loaded last, or whose names the
	centre wants in another language."""
	contenuto = LIBRERIA.read_bytes()
	lingua = L.lingua_del_sito()
	segno = L.caricata(contenuto, lingua)
	if not forza and frappe.db.get_default(VERSIONE_CARICATA) == segno:
		return None
	fatto = carica(json.loads(contenuto), lingua)
	frappe.db.set_default(VERSIONE_CARICATA, segno)
	return fatto


def dopo_la_configurazione(_args=None) -> None:
	"""The setup wizard chose the site's language and country: the foods' names
	follow them, in the background."""
	frappe.enqueue(
		"crm.clinica.librerie.carica_libreria",
		queue="long",
		job_id="crm-libreria-alimenti",
		deduplicate=True,
		enqueue_after_commit=True,
	)
