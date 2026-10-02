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
- **Loaded again**, the library brings its numbers; the words the centre changed -
  a name, a group, a portion - stay the centre's, and a name the centre never
  touched follows the library's (`library_name` keeps the one it gave). The centre
  adds its own foods. A food is switched off, not deleted: a plan may point to it.
- **A number the table does not give** counts as nothing: the site keeps a number.
  A food without its energy is not in the library.
"""

from __future__ import annotations

import hashlib
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
#: The fingerprint of the library a site last loaded (a default of the site).
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


# ------------------------------------------------------------------ correcting, adding


@frappe.whitelist(methods=["POST"])
def save_food(name: str | None = None, data: dict | str | None = None) -> dict:
	"""A food of the library put right, or a new one of the centre's: its name in
	the centre's words, its group, its portion, on or off. The library's numbers
	stay the library's; the centre's own food has its numbers written here."""
	livelli.verifica("piani.librerie")
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	doc = frappe.get_doc(CIBO, name) if name else frappe.new_doc(CIBO)
	nome = (dati.get("food_name") or "").strip()
	if not nome:
		frappe.throw(_("A food has a name"))
	if dati.get("food_group") not in T.GRUPPI:
		frappe.throw(_("Choose the group"))
	doc.food_name = nome[:140]
	doc.food_group = dati["food_group"]
	doc.portion_g = flt(dati.get("portion_g")) or None
	doc.enabled = 1 if cint(dati.get("enabled", 1)) else 0
	if not name:
		doc.source = CENTRO
	if (doc.source or CENTRO) == CENTRO:
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
	migrate whose file is not the one the site loaded last."""
	contenuto = LIBRERIA.read_bytes()
	impronta = hashlib.sha256(contenuto).hexdigest()
	if not forza and frappe.db.get_default(VERSIONE_CARICATA) == impronta:
		return None
	fatto = carica(json.loads(contenuto))
	frappe.db.set_default(VERSIONE_CARICATA, impronta)
	return fatto
