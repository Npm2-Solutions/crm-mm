# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The exercises the plans are written with (design.md, "I piani";
ricerca-design.md §2.3), and what every library shares: a page of it, its entries
put in all at once, the site's language. A module keeps its own libraries the same
way: the clinic its foods (`crm.clinica.librerie`). Nobody imports a library any
more: what `CRM Library Import` holds is the record of the imports before.

- **Who** (`piani.librerie`): the manager; a practitioner when the manager turns it
  on. Whoever writes plans still adds an exercise from the editor.
- **The library** DottorCloud ships (`dati/esercizi.json`, `dataset`): 1,324
  exercises, their names in Italian, all there on every site. `carica_libreria`
  puts it in at install and at every migrate that brings a new version of the
  file; NPM2 adds an exercise to the library in that file. The pictures
  © Gym visual, with its authorisation to NPM2 Solutions, are the server's own
  copy, brought there by itself (`immagini`), or a CDN the agency names; never
  used by the assistant.
- **The centre** changes nothing of the library's: it switches off the exercises
  it does not use (`switch_exercise`) and adds its own (`save_exercise`), which it
  puts right as it likes. An exercise is switched off, not deleted: a plan may
  point to it.
- **Loaded again**, the library updates its pictures and muscles, and its words
  kept in another language take the centre's; what a centre wrote on one of them
  before - a name, how it is done - stays.
- **In the centre's language** (`crm.lingue`): a site loaded in English before
  it said it is in Italy loads the library again, and the library's own words
  take Italian; the centre's stay.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from crm import lingue
from crm.permissions import livelli
from crm.piani import dataset as D
from crm.piani import immagini
from crm.utils import count_field

ESERCIZIO = "CRM Exercise"
#: Where the agency may name a CDN of its own for the library's pictures, in the
#: Desk: the area's settings.
IMPOSTAZIONI = "CRM Area Settings"
CENTRO = "Centre"
PER_PAGINA = 50
#: The exercise library DottorCloud ships.
LIBRERIA = Path(__file__).parent / "dati" / "esercizi.json"
#: The library a site last loaded, its fingerprint and the language of its words
#: (a default of the site).
VERSIONE_CARICATA = "crm_exercise_library"


# ------------------------------------------------------------------ what every library shares


def pagina(
	doctype: str,
	campo_nome: str,
	campi: list[str],
	filtri: dict,
	text: str | None = None,
	start: int = 0,
) -> dict:
	"""A page of a library, searched by name (the centre's or the source's) and
	filtered, with how many there are and how many come from where."""
	parole = (text or "").strip()
	o_filtri = []
	if parole:
		o_filtri = [[campo_nome, "like", f"%{parole}%"], ["name_in_source", "like", f"%{parole}%"]]
	righe = frappe.get_all(
		doctype,
		filters=filtri,
		or_filters=o_filtri or None,
		fields=campi,
		order_by=f"{campo_nome} asc",
		start=cint(start),
		limit=PER_PAGINA,
	)
	totale = frappe.get_all(
		doctype, filters=filtri, or_filters=o_filtri or None, fields=[count_field("quanti")]
	)[0].quanti
	fonti = {
		riga.source or CENTRO: riga.quanti
		for riga in frappe.get_all(doctype, fields=["source", count_field("quanti")], group_by="source")
	}
	return {"rows": righe, "total": totale, "sources": fonti}


def filtri_della_pagina(campo_gruppo: str, group=None, source=None, enabled=None) -> dict:
	filtri: dict = {}
	if group:
		filtri[campo_gruppo] = group
	if source:
		filtri["source"] = source
	if enabled not in (None, ""):
		filtri["enabled"] = cint(enabled)
	return filtri


def _nuovo(adesso, valori: dict) -> tuple:
	return (
		frappe.generate_hash(length=10),
		adesso,
		adesso,
		frappe.session.user,
		frappe.session.user,
		0,
		*valori.values(),
	)


def inserisci(doctype: str, righe: list[dict]) -> None:
	"""A library's new entries, all at once: a table is thousands of rows."""
	if not righe:
		return
	adesso = now_datetime()
	campi = ["name", "creation", "modified", "owner", "modified_by", "docstatus", *righe[0].keys()]
	frappe.db.bulk_insert(doctype, campi, [_nuovo(adesso, riga) for riga in righe], chunk_size=500)


# ------------------------------------------------------------------ the exercises


def _base_media() -> str | None:
	"""Where the library's pictures come from: a CDN the agency named, else the
	server's own copy once it has one."""
	# a single's value is kept by Frappe for the request
	return frappe.db.get_single_value(IMPOSTAZIONI, "exercise_media_url") or immagini.indirizzo()


def media(riga) -> dict:
	"""An exercise's pictures as a page shows them: the centre's own picture, else
	the library's; the animation; and whose they are."""
	base = _base_media()
	immagine = riga.get("image") or D.indirizzo_media(base, riga.get("media_path"))
	animazione = D.indirizzo_media(base, riga.get("animation_path"))
	dal_dataset = bool(animazione or (not riga.get("image") and immagine))
	return {
		"picture": immagine,
		"animation": animazione,
		# the attribution goes with the library's pictures, not with the centre's
		"media_attribution": riga.get("attribution") if dal_dataset else None,
	}


CAMPI_ESERCIZIO = [
	"name",
	"exercise_name",
	"body_part",
	"equipment",
	"enabled",
	"primary_muscles",
	"secondary_muscles",
	"instructions",
	"image",
	"video_url",
	"attribution",
	"source",
	"source_code",
	"name_in_source",
	"media_path",
	"animation_path",
]


def _riga_esercizio(riga) -> dict:
	return {**riga, **media(riga)}


@frappe.whitelist()
def get_exercises(
	text: str | None = None,
	group: str | None = None,
	source: str | None = None,
	enabled: str | None = None,
	start: int = 0,
) -> dict:
	"""A page of the exercises, searched and filtered, with how many come from where."""
	livelli.verifica("piani.librerie")
	risposta = pagina(
		ESERCIZIO,
		"exercise_name",
		CAMPI_ESERCIZIO,
		filtri_della_pagina("body_part", group, source, enabled),
		text,
		start,
	)
	return {
		**risposta,
		"rows": [_riga_esercizio(r) for r in risposta["rows"]],
		# whose the pictures are, said under the list where there are pictures
		"has_media": bool(_base_media()),
	}


@frappe.whitelist(methods=["POST"])
def save_exercise(name: str | None = None, data: dict | str | None = None) -> dict:
	"""A new exercise of the centre's, or one of its own put right: its name, the
	body part, the equipment, how it is done, its video, on or off. The library's
	are DottorCloud's: switched off or on (`switch_exercise`), never changed."""
	livelli.verifica("piani.librerie")
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	doc = frappe.get_doc(ESERCIZIO, name) if name else frappe.new_doc(ESERCIZIO)
	if (doc.source or CENTRO) != CENTRO:
		frappe.throw(_("The library's exercises are switched off, not changed: add the centre's own"))
	nome = (dati.get("exercise_name") or "").strip()
	if not nome:
		frappe.throw(_("An exercise has a name"))
	parti = frappe.get_meta(ESERCIZIO).get_field("body_part").options.split("\n")
	doc.exercise_name = nome[:140]
	doc.body_part = dati.get("body_part") if dati.get("body_part") in parti else None
	doc.equipment = (dati.get("equipment") or "").strip()[:140] or None
	doc.instructions = (dati.get("instructions") or "").strip() or None
	doc.video_url = (dati.get("video_url") or "").strip() or None
	doc.primary_muscles = (dati.get("primary_muscles") or "").strip() or None
	doc.secondary_muscles = (dati.get("secondary_muscles") or "").strip() or None
	doc.enabled = 1 if cint(dati.get("enabled", 1)) else 0
	if name:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)
	return _riga_esercizio(frappe.get_all(ESERCIZIO, filters={"name": doc.name}, fields=CAMPI_ESERCIZIO)[0])


def accendi(doctype: str, name: str, enabled) -> dict:
	"""A library's entry offered when plans are written, or no longer: one of the
	library the centre does not use, or one of its own. The plans that have it
	keep it."""
	doc = frappe.get_doc(doctype, name)
	doc.enabled = 1 if cint(enabled) else 0
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "enabled": doc.enabled}


@frappe.whitelist(methods=["POST"])
def switch_exercise(name: str, enabled: int | str = 1) -> dict:
	"""An exercise switched off, or on again."""
	livelli.verifica("piani.librerie")
	return accendi(ESERCIZIO, name, enabled)


def lingua_del_sito() -> str:
	"""The libraries' words in the centre's language (`crm.lingue`): Italian, else
	English."""
	return "it" if lingue.del_centro() == "it" else "en"


def caricata(contenuto: bytes, lingua: str) -> str:
	"""What a site keeps of the library it loaded: a new file, or words wanted in
	another language, load it again."""
	return f"{hashlib.sha256(contenuto).hexdigest()} {lingua}"


def carica(record: list, lingua: str | None = None) -> dict:
	"""The library's records into the site: a new exercise comes in; one already
	there gets the library's pictures and muscles again, and what a centre wrote
	on it before - its name, body part, how it is done - stays. The library's own
	words the site keeps in another language, or as they were before NPM2 put
	them right, take the library's words in ``lingua`` (`dataset.nella_lingua`)."""
	lingua = lingua or lingua_del_sito()
	presenti = {
		riga.source_code: riga
		for riga in frappe.get_all(
			ESERCIZIO,
			filters={"source": D.DATASET},
			fields=["name", "source_code", "exercise_name", "equipment", "instructions"],
			limit=100000,
		)
		if riga.source_code
	}
	nuovi, aggiornati, visti = [], {}, set()
	scartati = 0
	for voce in record:
		esercizio = D.esercizio(voce, lingua)
		if not esercizio or esercizio["code"] in visti:
			scartati += 1
			continue
		visti.add(esercizio["code"])
		della_libreria = {
			campo: esercizio[campo]
			for campo in (
				"media_path",
				"animation_path",
				"attribution",
				"primary_muscles",
				"secondary_muscles",
			)
		}
		esistente = presenti.get(esercizio["code"])
		if esistente:
			aggiornati[esistente.name] = {**della_libreria, **D.nella_lingua(voce, lingua, esistente)}
			continue
		nuovi.append(
			{
				"exercise_name": esercizio["name"],
				"body_part": esercizio["body_part"],
				"equipment": esercizio["equipment"],
				"enabled": 1,
				"instructions": esercizio["instructions"],
				**della_libreria,
				"source": D.DATASET,
				"source_code": esercizio["code"],
				"name_in_source": esercizio["name_in_source"],
			}
		)
	inserisci(ESERCIZIO, nuovi)
	frappe.db.bulk_update(ESERCIZIO, aggiornati, chunk_size=200)
	return {"created": len(nuovi), "updated": len(aggiornati), "skipped": scartati}


def carica_libreria(forza: bool = False) -> dict | None:
	"""The library DottorCloud ships, into this site: at install, and at every
	migrate whose file is not the one the site loaded last, or whose words the
	centre wants in another language."""
	contenuto = LIBRERIA.read_bytes()
	lingua = lingua_del_sito()
	segno = caricata(contenuto, lingua)
	if not forza and frappe.db.get_default(VERSIONE_CARICATA) == segno:
		return None
	fatto = carica(json.loads(contenuto), lingua)
	frappe.db.set_default(VERSIONE_CARICATA, segno)
	return fatto


def dopo_la_configurazione(_args=None) -> None:
	"""The setup wizard chose the site's language and country: the library's words
	follow them, in the background."""
	frappe.enqueue(
		"crm.piani.librerie.carica_libreria",
		queue="long",
		job_id="crm-libreria-esercizi",
		deduplicate=True,
		enqueue_after_commit=True,
	)
