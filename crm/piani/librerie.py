# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's exercises, the library its plans are written with (design.md, "I
piani"; ricerca-design.md §2.3), and what every library shares: a page of it, the
file uploaded, the imports and who declared which licence (`CRM Library Import`).
A module keeps its own libraries the same way: the clinic its foods
(`crm.clinica.librerie`).

- **Who** (`piani.librerie`): the manager; a practitioner when the manager turns it
  on. Whoever writes plans still adds an exercise from the editor.
- **exercises-dataset** (`dataset`): 1,324 exercises, the data MIT; the pictures
  © Gym visual, with its authorisation to NPM2 Solutions, served from where the
  agency hosts them (one copy per server or a CDN, not one per site), never used by
  the assistant.
- **Imported again**, the dataset updates its pictures and muscles; the words the
  centre changed - a name in Italian, the body part, how it is done - stay the
  centre's. An exercise is switched off, not deleted: a plan may point to it.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from crm.permissions import livelli
from crm.piani import dataset as D
from crm.utils import count_field

ESERCIZIO = "CRM Exercise"
IMPORTAZIONE = "CRM Library Import"
#: Where the agency says it hosts the dataset's pictures: the area's settings.
IMPOSTAZIONI = "CRM Area Settings"
ESERCIZI = "Exercises"
CENTRO = "Centre"
PER_PAGINA = 50
#: The dataset is 17 MB; a bigger file is not it.
MAX_DATASET = 40 * 1024 * 1024


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


def importazioni(libreria: str) -> list[dict]:
	"""The last imports into a library: which source, who, what they declared."""
	return frappe.get_all(
		IMPORTAZIONE,
		filters={"library": libreria},
		fields=[
			"name",
			"source",
			"attribution",
			"file_name",
			"imported_by",
			"imported_on",
			"licence",
			"rows_read",
			"created_count",
			"updated_count",
			"skipped_count",
		],
		order_by="imported_on desc",
		limit=10,
	)


def file_caricato(file_url: str):
	"""The file the session uploaded: read by who may read it."""
	nome = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not nome:
		frappe.throw(_("There is no such file"))
	file = frappe.get_doc("File", nome)
	file.check_permission("read")
	contenuto = file.get_content(encodings=[])
	if isinstance(contenuto, str):
		contenuto = contenuto.encode("utf-8")
	return file, contenuto


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


def registra_importazione(
	libreria: str, fonte: str, attribuzione: str | None, file_name: str | None, **conti
) -> str:
	"""An import, written once: which library, which source, who, what they declared."""
	doc = frappe.get_doc(
		{
			"doctype": IMPORTAZIONE,
			"library": libreria,
			"source": fonte,
			"attribution": attribuzione,
			"file_name": file_name,
			"imported_by": frappe.session.user,
			"imported_on": now_datetime(),
			**conti,
		}
	).insert(ignore_permissions=True)
	return doc.name


# ------------------------------------------------------------------ the exercises


def _base_media() -> str | None:
	# a single's value is kept by Frappe for the request
	return frappe.db.get_single_value(IMPOSTAZIONI, "exercise_media_url")


def media(riga) -> dict:
	"""An exercise's pictures as a page shows them: the centre's own picture, else
	the library's from where the agency hosts it; the animation; and whose they are."""
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
	"""A page of the exercises, searched and filtered, with how many come from where,
	the imports, and where the agency hosts the dataset's pictures."""
	livelli.verifica("piani.librerie")
	risposta = pagina(
		ESERCIZIO,
		"exercise_name",
		CAMPI_ESERCIZIO,
		filtri_della_pagina("body_part", group, source, enabled),
		text,
		start,
	)
	tecnico = livelli.puo("tecnico.integrazioni")
	return {
		**risposta,
		"rows": [_riga_esercizio(r) for r in risposta["rows"]],
		"imports": importazioni(ESERCIZI),
		"media_url": _base_media() if tecnico else None,
		"can_set_media": tecnico,
		"has_media": bool(_base_media()),
	}


@frappe.whitelist(methods=["POST"])
def save_exercise(name: str, data: dict | str) -> dict:
	"""An exercise corrected: its name, the body part, the equipment, how it is
	done, the centre's video, on or off. The library's pictures stay the library's."""
	livelli.verifica("piani.librerie")
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	doc = frappe.get_doc(ESERCIZIO, name)
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
	doc.save(ignore_permissions=True)
	return _riga_esercizio(frappe.get_all(ESERCIZIO, filters={"name": doc.name}, fields=CAMPI_ESERCIZIO)[0])


@frappe.whitelist(methods=["POST"])
def save_media_url(url: str | None = None) -> dict:
	"""Where the agency hosts the dataset's pictures: an https address or a path
	of this server. Every exercise of the dataset follows it."""
	livelli.verifica("tecnico.integrazioni")
	indirizzo = (url or "").strip() or None
	if indirizzo and not D.indirizzo_media(indirizzo, "images/prova.jpg"):
		frappe.throw(_("Write an https address, or a path of this server that starts with /"))
	frappe.db.set_single_value(IMPOSTAZIONI, "exercise_media_url", indirizzo)
	return {"media_url": indirizzo}


def _lingua_del_sito() -> str:
	lingua = (frappe.db.get_single_value("System Settings", "language") or "it")[:2]
	return "it" if lingua == "it" else "en"


def _dataset(file_url: str | None) -> tuple[list, str | None]:
	"""The dataset's records: from the file uploaded, or downloaded at the version
	the import was written on."""
	if file_url:
		file, contenuto = file_caricato(file_url)
		nome = file.file_name
	else:
		import requests

		try:
			risposta = requests.get(D.DATASET_URL, timeout=90)
			risposta.raise_for_status()
		except Exception:
			frappe.throw(_("exercises-dataset could not be downloaded: upload its exercises.json instead"))
		contenuto, nome = risposta.content, "exercises.json"
	if len(contenuto) > MAX_DATASET:
		frappe.throw(_("This is not exercises-dataset's exercises.json"))
	try:
		record = json.loads(contenuto)
	except ValueError:
		frappe.throw(_("This is not exercises-dataset's exercises.json"))
	if not isinstance(record, list):
		frappe.throw(_("This is not exercises-dataset's exercises.json"))
	return record, nome


@frappe.whitelist(methods=["POST"])
def import_exercises(file_url: str | None = None) -> dict:
	"""exercises-dataset into the library: the name in English, how it is done in
	the site's language, the pictures from where the agency hosts them. An
	exercise already there gets the dataset's pictures and muscles again; its
	name, body part and instructions stay as the centre left them."""
	livelli.verifica("piani.librerie")
	record, nome_file = _dataset(file_url)
	lingua = _lingua_del_sito()
	presenti = {
		riga.source_code: riga.name
		for riga in frappe.get_all(
			ESERCIZIO, filters={"source": D.DATASET}, fields=["name", "source_code"], limit=100000
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
		immagini = {
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
			aggiornati[esistente] = immagini
			continue
		nuovi.append(
			{
				"exercise_name": esercizio["name"],
				"body_part": esercizio["body_part"],
				"equipment": esercizio["equipment"],
				"enabled": 1,
				"instructions": esercizio["instructions"],
				**immagini,
				"source": D.DATASET,
				"source_code": esercizio["code"],
				"name_in_source": esercizio["name_in_source"],
			}
		)
	if not nuovi and not aggiornati:
		frappe.throw(_("This is not exercises-dataset's exercises.json"))
	inserisci(ESERCIZIO, nuovi)
	frappe.db.bulk_update(ESERCIZIO, aggiornati, chunk_size=200)
	registro = registra_importazione(
		ESERCIZI,
		D.DATASET,
		"exercises-dataset (MIT); pictures © Gym visual",
		nome_file,
		licence=_("Data under the MIT licence; pictures © Gym visual, authorised to NPM2 Solutions"),
		rows_read=len(record),
		created_count=len(nuovi),
		updated_count=len(aggiornati),
		skipped_count=scartati,
	)
	return {"created": len(nuovi), "updated": len(aggiornati), "skipped": scartati, "import": registro}
