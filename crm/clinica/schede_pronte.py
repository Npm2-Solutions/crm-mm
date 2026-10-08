# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinical sheets DottorCloud ships (`dati/schede_pronte.json`): a
physiotherapy assessment and follow-up, a first nutrition visit and its
follow-up, a first dental visit, a general medical history. Their own questions,
written by NPM2: no validated scale, nobody's questionnaire.

- **Drafts of the centre's.** Where the clinic is on, each sheet is a draft
  template (Settings > Clients > Forms), in the centre's language
  (`crm.lingue.del_centro`), never published by itself: the medical director
  reads it, changes what the centre does otherwise and publishes it.
- **Loaded** at install, at every migrate that brings a new file or finds the
  centre in another language, when the clinic is switched on and when the
  centre changes language. A sheet the centre touched - changed, published,
  deleted - is never written again: only a draft still as it was loaded follows
  the file and the language (`schede_pronte_regole.impronta`). A template of the
  centre's own with the same title is left alone, and the sheet not made.
- **To start from**, in the builder's «Start from» beside the CRM's own
  (`modelli.registra_partenze`): a copy, however the draft was changed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import frappe

from crm.clinica import schede_pronte_regole as R

FILE = Path(__file__).parent / "dati" / "schede_pronte.json"
#: The file and the language a site last loaded (a default of the site).
CARICATE = "crm_clinical_sheets"
#: Each sheet's template and the fingerprint of what was loaded into it.
TENUTE = "crm_clinical_sheets_kept"


def _dati() -> dict:
	return json.loads(FILE.read_text(encoding="utf-8"))


def _accesa() -> bool:
	from crm.clinica.paziente import clinica_accesa

	return clinica_accesa()


def _lingua() -> str:
	from crm import lingue

	return lingue.del_centro()


def nella_lingua_del_centro() -> list[dict]:
	"""The sheets as the centre reads them: key, title, description, specialty, schema."""
	dati = _dati()
	lingua = _lingua()
	return [R.nella_lingua(scheda, dati.get("words"), lingua) for scheda in dati.get("sheets") or []]


def partenze() -> list[dict]:
	"""The sheets to start a template from, where the clinic is on."""
	from crm.moduli import modelli

	if not _accesa():
		return []
	return [
		{
			"key": f"clinic.{scheda['key']}",
			"use": modelli.SCHEDA,
			"clinical": 1,
			"title": scheda["title"],
			"description": scheda.get("description") or "",
			"specialty": scheda.get("specialty") or "",
			"schema": scheda["schema"],
		}
		for scheda in nella_lingua_del_centro()
	]


def _impronta_del_modello(doc) -> str:
	from crm.moduli import modelli

	return R.impronta(doc.title, doc.description, doc.specialty, modelli.carica_schema(doc.schema))


def _titoli_del_centro() -> set[str]:
	"""The titles of the centre's own templates: not the demo's, which go."""
	from crm.demo import registro
	from crm.moduli import modelli

	della_demo = registro.nomi_di_prova(modelli.MODELLO)
	return {
		riga.title.strip().lower()
		for riga in frappe.get_all(modelli.MODELLO, fields=["name", "title"])
		if riga.name not in della_demo and riga.title
	}


def carica_schede(forza: bool = False) -> dict | None:
	"""The sheets into the site's drafts, where the clinic is on: once per file and
	language, a sheet nobody touched brought up to date, the others left as the
	centre has them."""
	if not _accesa():
		return None
	from crm.moduli import modelli

	contenuto = FILE.read_bytes()
	lingua = _lingua()
	segno = hashlib.sha256(contenuto + lingua.encode()).hexdigest()
	if not forza and frappe.db.get_default(CARICATE) == segno:
		return None
	tenute = json.loads(frappe.db.get_default(TENUTE) or "{}")
	titoli = _titoli_del_centro()
	fatto = {"created": 0, "updated": 0, "kept": 0}
	for scheda in nella_lingua_del_centro():
		impronta = R.impronta(
			scheda["title"], scheda.get("description"), scheda.get("specialty"), scheda["schema"]
		)
		prima = tenute.get(scheda["key"])
		if prima is None:
			if scheda["title"].strip().lower() in titoli:
				# the centre has its own of that name: not a second one beside it
				tenute[scheda["key"]] = {"name": None, "hash": None}
				fatto["kept"] += 1
				continue
			doc = frappe.get_doc(
				{
					"doctype": modelli.MODELLO,
					"title": scheda["title"],
					"use": modelli.SCHEDA,
					"clinical": 1,
					"specialty": scheda.get("specialty"),
					"description": scheda.get("description"),
					"enabled": 1,
					"schema": json.dumps(scheda["schema"], ensure_ascii=False),
				}
			).insert(ignore_permissions=True)
			tenute[scheda["key"]] = {"name": doc.name, "hash": impronta}
			fatto["created"] += 1
			continue
		if not prima.get("name") or not frappe.db.exists(modelli.MODELLO, prima["name"]):
			# its own of that name, or deleted: the centre's choice
			continue
		doc = frappe.get_doc(modelli.MODELLO, prima["name"])
		if doc.current_version or _impronta_del_modello(doc) != prima.get("hash"):
			# published, or changed: the centre's now
			fatto["kept"] += 1
			continue
		if impronta == prima.get("hash"):
			continue
		doc.update(
			{
				"title": scheda["title"],
				"specialty": scheda.get("specialty"),
				"description": scheda.get("description"),
				"schema": json.dumps(scheda["schema"], ensure_ascii=False),
			}
		)
		doc.save(ignore_permissions=True)
		tenute[scheda["key"]] = {"name": doc.name, "hash": impronta}
		fatto["updated"] += 1
	frappe.db.set_default(TENUTE, json.dumps(tenute))
	frappe.db.set_default(CARICATE, segno)
	return fatto


def in_seguito(_args=None) -> None:
	"""The clinic switched on, or the centre's language changed: the sheets follow,
	in the background."""
	frappe.enqueue(
		"crm.clinica.schede_pronte.carica_schede",
		queue="long",
		job_id="crm-schede-cliniche",
		deduplicate=True,
		enqueue_after_commit=True,
	)
