# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A deal takes its value from its quotes: the products grid leaves its page.

The deal had a grid of products from a catalogue of its own, while a quote takes
the centre's services and price lists: two catalogues and two values for one sale,
and the products' total could overwrite what the quote said. The grid and its two
totals leave the deal's fields where no deal holds a product. Where one does they
stay: nothing a centre wrote is hidden from it. The fields stay in the DocType, so
whoever wants the grid back puts it back from the layout.
"""

import json

import frappe

LAYOUT = "CRM Deal-Data Fields"
#: the grid and its two totals
VIA = frozenset({"products", "total", "net_total"})


def execute():
	if not frappe.db.exists("CRM Fields Layout", LAYOUT):
		return
	if frappe.db.exists("CRM Products", {"parenttype": "CRM Deal"}):
		return
	prima = frappe.db.get_value("CRM Fields Layout", LAYOUT, "layout")
	dopo = senza_prodotti(prima)
	if dopo != prima:
		frappe.db.set_value("CRM Fields Layout", LAYOUT, "layout", dopo, update_modified=False)


def senza_prodotti(layout: str | None) -> str | None:
	"""The layout without the grid and its totals; a column or a section left empty
	goes with them. A layout that does not read as JSON is left as it is."""
	try:
		schede = json.loads(layout or "[]")
	except ValueError:
		return layout
	if not isinstance(schede, list):
		return layout
	con_schede = any(isinstance(scheda, dict) and "sections" in scheda for scheda in schede)
	tutte = schede if con_schede else [{"sections": schede}]
	cambiato = False
	for scheda in tutte:
		sezioni = []
		for sezione in scheda.get("sections") or []:
			if not isinstance(sezione, dict) or "columns" not in sezione:
				sezioni.append(sezione)
				continue
			colonne = []
			for colonna in sezione.get("columns") or []:
				campi = [campo for campo in (colonna.get("fields") or []) if campo not in VIA]
				if len(campi) != len(colonna.get("fields") or []):
					cambiato = True
					if not campi:
						continue
				colonne.append({**colonna, "fields": campi})
			if not colonne and sezione.get("columns"):
				cambiato = True
				continue
			sezioni.append({**sezione, "columns": colonne})
		scheda["sections"] = sezioni
	if not cambiato:
		return layout
	return json.dumps(tutte if con_schede else tutte[0]["sections"])
