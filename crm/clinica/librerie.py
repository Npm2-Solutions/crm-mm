# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The centre's libraries: the foods and the exercises its plans are written with
(design.md, "I piani"; ricerca-design.md §2.3), in Settings > Libraries.

- **Who** (`piani.librerie`): the manager and the medical director; a
  practitioner when the manager turns it on - the nutritionist who keeps the
  foods. Whoever writes plans still adds a food or an exercise from the editor.
- **A food table** (`tabelle`): CIQUAL, free (Licence Ouverte); BDA-IEO with the
  licence for commercial software; CREA with its written permission; USDA, public
  domain. The sheet is read on the server, its columns and its categories shown
  to check, the foods chosen - all, or the ones the Italian tables lack - and the
  import says who declared which licence (`Clinic Library Import`).
- **exercises-dataset**: 1,324 exercises, the data MIT; the pictures © Gym visual,
  with its authorisation to NPM2 Solutions, served from where the agency hosts
  them (one copy per server or a CDN, not one per site), never used by the
  assistant.
- **Imported again**, a table updates its numbers and the dataset its pictures and
  muscles; the words the centre changed - a name in Italian, a group, how an
  exercise is done - stay the centre's. A food or an exercise is switched off, not
  deleted: a plan may point to it.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from crm.clinica import tabelle as T
from crm.permissions import livelli
from crm.utils import count_field

CIBO = "Clinic Food"
ESERCIZIO = "Clinic Exercise"
IMPORTAZIONE = "Clinic Library Import"
IMPOSTAZIONI = "Clinic Settings"
CIBI, ESERCIZI = "Foods", "Exercises"
CENTRO = "Centre"
FONTI = ("CIQUAL", "CREA", "BDA-IEO", "USDA")
#: What each source asks to be shown with its numbers, as the import proposes it.
ATTRIBUZIONI = {
	"CIQUAL": "ANSES-CIQUAL 2020, Licence Ouverte",
	"CREA": "CREA, Tabelle di composizione degli alimenti",
	"BDA-IEO": "BDA-IEO, Banca Dati di Composizione degli Alimenti",
	"USDA": "USDA FoodData Central, public domain",
}
#: The sources whose numbers a centre uses only with a licence or a written
#: permission: the import asks who declares it.
CON_LICENZA = {
	"CREA": "The centre has the written permission of CREA to use its tables",
	"BDA-IEO": "The centre has the licence of BDA-IEO for commercial software",
}
PER_PAGINA = 50
MAX_ANTEPRIMA = 5000
#: The dataset is 17 MB; a bigger file is not it.
MAX_DATASET = 40 * 1024 * 1024


# ------------------------------------------------------------------ reading the libraries


def _base_media() -> str | None:
	# a single's value is kept by Frappe for the request
	return frappe.db.get_single_value(IMPOSTAZIONI, "exercise_media_url")


def media(riga) -> dict:
	"""An exercise's pictures as a page shows them: the centre's own picture, else
	the library's from where the agency hosts it; the animation; and whose they are."""
	base = _base_media()
	immagine = riga.get("image") or T.indirizzo_media(base, riga.get("media_path"))
	animazione = T.indirizzo_media(base, riga.get("animation_path"))
	dal_dataset = bool(animazione or (not riga.get("image") and immagine))
	return {
		"picture": immagine,
		"animation": animazione,
		# the attribution goes with the library's pictures, not with the centre's
		"media_attribution": riga.get("attribution") if dal_dataset else None,
	}


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
def get_library(
	kind: str = CIBI,
	text: str | None = None,
	group: str | None = None,
	source: str | None = None,
	enabled: str | None = None,
	start: int = 0,
) -> dict:
	"""A page of a library, searched and filtered, with how many come from where."""
	livelli.verifica("piani.librerie")
	cibi = kind != ESERCIZI
	doctype, campo_nome, campo_gruppo = (
		(CIBO, "food_name", "food_group") if cibi else (ESERCIZIO, "exercise_name", "body_part")
	)
	filtri: dict = {}
	if group:
		filtri[campo_gruppo] = group
	if source:
		filtri["source"] = source
	if enabled not in (None, ""):
		filtri["enabled"] = cint(enabled)
	parole = (text or "").strip()
	o_filtri = []
	if parole:
		o_filtri = [[campo_nome, "like", f"%{parole}%"], ["name_in_source", "like", f"%{parole}%"]]
	righe = frappe.get_all(
		doctype,
		filters=filtri,
		or_filters=o_filtri or None,
		fields=CAMPI_CIBO if cibi else CAMPI_ESERCIZIO,
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
	risposta = {
		"rows": righe if cibi else [_riga_esercizio(r) for r in righe],
		"total": totale,
		"sources": fonti,
		"imports": _importazioni(CIBI if cibi else ESERCIZI),
	}
	if not cibi:
		risposta["media_url"] = _base_media() if livelli.puo("tecnico.integrazioni") else None
		risposta["can_set_media"] = livelli.puo("tecnico.integrazioni")
		risposta["has_media"] = bool(_base_media())
	return risposta


def _importazioni(libreria: str) -> list[dict]:
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


# ------------------------------------------------------------------ correcting


@frappe.whitelist(methods=["POST"])
def save_food(name: str, data) -> dict:
	"""A food of the library corrected: its name in the centre's words, its group,
	its portion, on or off. A table's numbers stay the table's; the centre's own
	food has its numbers written here."""
	livelli.verifica("piani.librerie")
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	doc = frappe.get_doc(CIBO, name)
	nome = (dati.get("food_name") or "").strip()
	if not nome:
		frappe.throw(_("A food has a name"))
	if dati.get("food_group") not in T.GRUPPI:
		frappe.throw(_("Choose the group"))
	doc.food_name = nome[:140]
	doc.food_group = dati["food_group"]
	doc.portion_g = flt(dati.get("portion_g")) or None
	doc.enabled = 1 if cint(dati.get("enabled", 1)) else 0
	if (doc.source or CENTRO) == CENTRO:
		for campo in T.VALORI:
			valore = dati.get(campo)
			doc.set(campo, flt(valore) if valore not in (None, "") else None)
		doc.kcal_computed = 0
		doc.source_note = (dati.get("source_note") or "").strip()[:140] or None
	doc.save(ignore_permissions=True)
	return frappe.get_all(CIBO, filters={"name": doc.name}, fields=CAMPI_CIBO)[0]


@frappe.whitelist(methods=["POST"])
def save_exercise(name: str, data) -> dict:
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
	if indirizzo and not T.indirizzo_media(indirizzo, "images/prova.jpg"):
		frappe.throw(_("Write an https address, or a path of this server that starts with /"))
	frappe.db.set_single_value(IMPOSTAZIONI, "exercise_media_url", indirizzo)
	return {"media_url": indirizzo}


# ------------------------------------------------------------------ a food table


def _file(file_url: str):
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


def _mappa(mapping, intestazioni: list) -> dict:
	"""The columns the person chose, over the recognised ones: an index per field,
	the group one or more."""
	riconosciuta = T.riconosci(intestazioni)
	if not mapping:
		return riconosciuta
	scelta = frappe.parse_json(mapping) if isinstance(mapping, str) else mapping
	mappa: dict = {}
	for campo in T.CIBO_CAMPI:
		valore = scelta.get(campo)
		indici = valore if isinstance(valore, list) else [valore]
		indici = [cint(i) for i in indici if i not in (None, "") and 0 <= cint(i) < len(intestazioni)]
		if not indici:
			continue
		mappa[campo] = indici if campo == "group" else indici[0]
	if riconosciuta.get("carbs_with_fibre") and mappa.get("carbs_g") == riconosciuta.get("carbs_g"):
		mappa["carbs_with_fibre"] = True
	return mappa


def _leggi_tabella(file_url: str, mapping=None) -> dict:
	file, contenuto = _file(file_url)
	try:
		righe = T.leggi_foglio(file.file_name or file_url, contenuto)
	except Exception:
		frappe.throw(_("This file is not a table that can be read: an Excel sheet or a CSV"))
	if len(righe) > T.MAX_RIGHE:
		frappe.throw(_("A table of at most {0} rows").format(T.MAX_RIGHE))
	indice = T.trova_intestazione(righe)
	if indice is None:
		frappe.throw(
			_(
				"The columns were not recognised: the table needs a row with the name of the food and its values"
			)
		)
	intestazioni = ["" if c is None else str(c) for c in righe[indice]]
	mappa = _mappa(mapping, intestazioni)
	if "name" not in mappa:
		frappe.throw(_("Say which column holds the name of the food"))
	lingua = T.lingua_delle_colonne(intestazioni)
	letti = T.alimenti(righe[indice + 1 :], mappa, lingua)
	return {
		"file": file,
		"columns": intestazioni,
		"mapping": mappa,
		"language": lingua,
		"guess": T.fonte_probabile(intestazioni),
		"rows_read": max(len(righe) - indice - 1, 0),
		**letti,
	}


def _chiave(cibo: dict) -> str:
	return cibo["code"] or "name:" + T.normalizza(cibo["name"])


def _presenti(fonte: str) -> dict[str, str]:
	"""The foods already in the library from ``fonte``, by their key in the table."""
	presenti = {}
	for riga in frappe.get_all(
		CIBO, filters={"source": fonte}, fields=["name", "source_code", "name_in_source"], limit=100000
	):
		if riga.source_code:
			presenti[riga.source_code] = riga.name
		if riga.name_in_source:
			presenti.setdefault("name:" + T.normalizza(riga.name_in_source), riga.name)
	return presenti


@frappe.whitelist(methods=["POST"])
def preview_foods(file_url: str, source: str | None = None, mapping=None) -> dict:
	"""A food table as it would be imported: the columns recognised, each category
	with its group, the foods, which are already in the library."""
	livelli.verifica("piani.librerie")
	letta = _leggi_tabella(file_url, mapping)
	fonte = source if source in FONTI else letta["guess"]
	presenti = _presenti(fonte) if fonte else {}
	cibi = letta["foods"]
	return {
		"columns": letta["columns"],
		"mapping": letta["mapping"],
		"language": letta["language"],
		"source": fonte,
		"attribution": ATTRIBUZIONI.get(fonte or ""),
		"licence": CON_LICENZA.get(fonte or ""),
		"categories": T.categorie(cibi),
		"foods": [
			{**cibo, "key": _chiave(cibo), "known": _chiave(cibo) in presenti}
			for cibo in cibi[:MAX_ANTEPRIMA]
		],
		"total": len(cibi),
		"rows_read": letta["rows_read"],
		"without_name": letta["without_name"],
		"without_values": letta["without_values"],
		"twice": letta["twice"],
		"dropped_values": letta["dropped_values"],
		"computed": sum(1 for cibo in cibi if cibo["kcal_computed"]),
	}


def _nuovo(doctype: str, adesso, valori: dict) -> tuple:
	return (
		frappe.generate_hash(length=10),
		adesso,
		adesso,
		frappe.session.user,
		frappe.session.user,
		0,
		*valori.values(),
	)


def _inserisci(doctype: str, righe: list[dict]) -> None:
	if not righe:
		return
	adesso = now_datetime()
	campi = ["name", "creation", "modified", "owner", "modified_by", "docstatus", *righe[0].keys()]
	frappe.db.bulk_insert(doctype, campi, [_nuovo(doctype, adesso, riga) for riga in righe], chunk_size=500)


def _registra(libreria: str, fonte: str, attribuzione: str | None, file_name: str | None, **conti) -> str:
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


@frappe.whitelist(methods=["POST"])
def import_foods(
	file_url: str,
	source: str,
	attribution: str | None = None,
	mapping=None,
	groups=None,
	keys=None,
	licence: int = 0,
) -> dict:
	"""The foods of a table into the library: the ones chosen, or all. A food
	already there from the same table gets the table's numbers again; its name,
	group and portion stay as the centre left them."""
	livelli.verifica("piani.librerie")
	if source not in FONTI:
		frappe.throw(_("Choose the table the file comes from"))
	dichiarazione = CON_LICENZA.get(source)
	if dichiarazione and not cint(licence):
		frappe.throw(_("Tick that the centre may use this table: {0}").format(_(dichiarazione)))
	letta = _leggi_tabella(file_url, mapping)
	scelte = frappe.parse_json(groups) if isinstance(groups, str) else groups
	cibi = T.applica_gruppi(letta["foods"], scelte)
	if keys is not None:
		volute = set(frappe.parse_json(keys) if isinstance(keys, str) else keys)
		cibi = [cibo for cibo in cibi if _chiave(cibo) in volute]
	if not cibi:
		frappe.throw(_("Choose at least one food"))
	attribuzione = (attribution or "").strip()[:140] or ATTRIBUZIONI[source]
	presenti = _presenti(source)
	nuovi, aggiornati = [], {}
	for cibo in cibi:
		numeri = {campo: cibo[campo] for campo in T.VALORI}
		numeri["kcal_computed"] = 1 if cibo["kcal_computed"] else 0
		esistente = presenti.get(_chiave(cibo))
		if esistente:
			aggiornati[esistente] = {**numeri, "source_note": attribuzione}
			continue
		nuovi.append(
			{
				"food_name": cibo["name"],
				"food_group": cibo["group"],
				"enabled": 1,
				**numeri,
				"source": source,
				"source_code": cibo["code"],
				"name_in_source": cibo["name"],
				"source_note": attribuzione,
			}
		)
	_inserisci(CIBO, nuovi)
	frappe.db.bulk_update(CIBO, aggiornati, chunk_size=200)
	lasciati = letta["without_name"] + letta["without_values"] + letta["twice"]
	registro = _registra(
		CIBI,
		source,
		attribuzione,
		letta["file"].file_name,
		licence=_(dichiarazione) if dichiarazione else None,
		rows_read=letta["rows_read"],
		created_count=len(nuovi),
		updated_count=len(aggiornati),
		skipped_count=lasciati,
	)
	return {"created": len(nuovi), "updated": len(aggiornati), "skipped": lasciati, "import": registro}


# ------------------------------------------------------------------ exercises-dataset


def _lingua_del_sito() -> str:
	lingua = (frappe.db.get_single_value("System Settings", "language") or "it")[:2]
	return "it" if lingua == "it" else "en"


def _dataset(file_url: str | None) -> tuple[list, str | None]:
	"""The dataset's records: from the file uploaded, or downloaded at the version
	the import was written on."""
	if file_url:
		file, contenuto = _file(file_url)
		nome = file.file_name
	else:
		import requests

		try:
			risposta = requests.get(T.DATASET_URL, timeout=90)
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
			ESERCIZIO, filters={"source": T.DATASET}, fields=["name", "source_code"], limit=100000
		)
		if riga.source_code
	}
	nuovi, aggiornati, visti = [], {}, set()
	scartati = 0
	for voce in record:
		esercizio = T.esercizio(voce, lingua)
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
				"source": T.DATASET,
				"source_code": esercizio["code"],
				"name_in_source": esercizio["name_in_source"],
			}
		)
	if not nuovi and not aggiornati:
		frappe.throw(_("This is not exercises-dataset's exercises.json"))
	_inserisci(ESERCIZIO, nuovi)
	frappe.db.bulk_update(ESERCIZIO, aggiornati, chunk_size=200)
	registro = _registra(
		ESERCIZI,
		T.DATASET,
		"exercises-dataset (MIT); pictures © Gym visual",
		nome_file,
		licence=_("Data under the MIT licence; pictures © Gym visual, authorised to NPM2 Solutions"),
		rows_read=len(record),
		created_count=len(nuovi),
		updated_count=len(aggiornati),
		skipped_count=scartati,
	)
	return {"created": len(nuovi), "updated": len(aggiornati), "skipped": scartati, "import": registro}
