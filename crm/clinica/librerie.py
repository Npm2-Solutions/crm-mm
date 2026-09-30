# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's foods, the library its diets are written with (design.md, "I piani";
ricerca-design.md §2.3), in Settings > Clinic > Foods. The exercises are the CRM's
(`crm.piani.librerie`), and so is what every library shares.

- **Who** (`piani.librerie`): the manager and the medical director; a
  practitioner when the manager turns it on - the nutritionist who keeps the
  foods. Whoever writes a diet still adds a food from the editor.
- **A food table** (`tabelle`): CIQUAL, free (Licence Ouverte); BDA-IEO with the
  licence for commercial software; CREA with its written permission; USDA, public
  domain. The sheet is read on the server, its columns and its categories shown
  to check, the foods chosen - all, or the ones the Italian tables lack - and the
  import says who declared which licence (`CRM Library Import`).
- **Imported again**, a table updates its numbers; the words the centre changed -
  a name in Italian, a group - stay the centre's. A food is switched off, not
  deleted: a plan may point to it.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt

from crm.clinica import tabelle as T
from crm.permissions import livelli
from crm.piani import librerie as L

CIBO = "Clinic Food"
CIBI = "Foods"
CENTRO = L.CENTRO
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
MAX_ANTEPRIMA = 5000


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
	return {
		**L.pagina(
			CIBO,
			"food_name",
			CAMPI_CIBO,
			L.filtri_della_pagina("food_group", group, source, enabled),
			text,
			start,
		),
		"imports": L.importazioni(CIBI),
	}


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


# ------------------------------------------------------------------ a food table


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
	file, contenuto = L.file_caricato(file_url)
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
	L.inserisci(CIBO, nuovi)
	frappe.db.bulk_update(CIBO, aggiornati, chunk_size=200)
	lasciati = letta["without_name"] + letta["without_values"] + letta["twice"]
	registro = L.registra_importazione(
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
