#!/usr/bin/env python3
"""Generate the Builder components the CRM ships.

Block trees are JSON-in-JSON and unforgiving — a wrong key or a repeater with two
children fails silently at render time, on a customer's live page. So they are generated
from this file rather than hand-edited, and `crm/tests/test_builder_files.py` checks the
output against the contract documented in `crm/builder_files/README.md`.

    python3 scripts/builder/build_components.py

Run it after changing anything here, and commit the JSON it writes.
"""

import json
import os

TS = "2026-09-06 16:00:00.000000"
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "crm", "builder_files", "components")

INK = "#171717"
MUTED = "#737373"
LINE = "#e5e5e5"
# A card with no cover still needs a valid src: an empty one makes the browser
# re-request the page itself. Declared inside each data script, which runs sandboxed.


def block(block_id, element, **kw):
	b = {
		"blockId": block_id,
		"element": element,
		"children": kw.pop("children", []),
		"baseStyles": kw.pop("baseStyles", {}),
		"mobileStyles": kw.pop("mobileStyles", {}),
		"tabletStyles": kw.pop("tabletStyles", {}),
		"rawStyles": {},
		"attributes": kw.pop("attributes", {}),
		"customAttributes": {},
		"classes": [],
		"dataKey": kw.pop("dataKey", None),
	}
	b.update(kw)
	return b


def prop(default):
	"""A component prop as Builder stores it: the author's value, or our default."""
	return {
		"isStandard": True,
		"value": None,
		"propOptions": {"type": "string", "options": {"defaultValue": default}},
	}


def bind(key, prop_name, source):
	"""`source` is 'props' for a component prop, 'componentData' for the data script."""
	return {"key": key, "type": "key", "property": prop_name, "comesFrom": source}


def repeater(block_id, data_key, child):
	"""A loop over `component.<data_key>`. Builder renders children[0] and only that."""
	return block(
		block_id,
		"div",
		isRepeaterBlock=True,
		dataKey={"key": data_key, "property": "dataKey", "type": "key", "comesFrom": "componentData"},
		children=[child],
	)


def section(block_id, children, gap="24px"):
	return block(
		block_id,
		"div",
		baseStyles={
			"display": "flex",
			"flexDirection": "column",
			"gap": gap,
			"width": "100%",
			"padding": "48px 24px",
		},
		children=children,
	)


def heading(block_id, text, key="titolo"):
	return block(
		block_id,
		"h2",
		innerHTML=text,
		baseStyles={"fontSize": "1.75rem", "fontWeight": "600", "lineHeight": "1.2", "color": INK},
		dynamicValues=[bind(key, "innerHTML", "props")],
	)


def grid(block_id, children, minimum="260px"):
	return block(
		block_id,
		"div",
		baseStyles={
			"display": "grid",
			"gridTemplateColumns": f"repeat(auto-fill, minmax({minimum}, 1fr))",
			"gap": "16px",
			"width": "100%",
		},
		mobileStyles={"gridTemplateColumns": "1fr"},
		children=children,
	)


def card(block_id, children):
	return block(
		block_id,
		"div",
		baseStyles={
			"display": "flex",
			"flexDirection": "column",
			"gap": "8px",
			"padding": "20px",
			"border": f"1px solid {LINE}",
			"borderRadius": "10px",
			"background": "#ffffff",
			"height": "100%",
		},
		children=children,
	)


def write(component_id, name, root, data_script=""):
	folder = component_id.replace("-", "_")
	path = os.path.join(OUT, folder)
	os.makedirs(path, exist_ok=True)
	doc = {
		"doctype": "Builder Component",
		"name": component_id,
		"component_id": component_id,
		"component_name": name,
		"component_data_script": data_script,
		"block": json.dumps(root, ensure_ascii=False, separators=(",", ":")),
		"docstatus": 0,
		"idx": 0,
		"modified": TS,
		"modified_by": "Administrator",
		"owner": "Administrator",
	}
	target = os.path.join(path, f"{folder}.json")
	with open(target, "w", encoding="utf-8") as f:
		f.write(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
	return target


# --------------------------------------------------------------- servizi

SERVIZI_SCRIPT = """# Services published on the website, from CRM Service.
# Props: titolo, categoria (empty = all), limite
#
# Frappe's Jinja environment does not autoescape and Builder emits no "|safe", so every
# value below reaches the page as HTML: text has to be escaped here or a "<" in a service
# name lands on the page as markup.
BLANK_PIXEL = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

filters = {"enabled": 1, "publish_on_website": 1}
if props.categoria:
	filters["category"] = props.categoria

limite = frappe.utils.cint(props.limite)
if limite < 1 or limite > 48:
	limite = 6

rows = frappe.get_all(
	"CRM Service",
	filters=filters,
	fields=["name", "service_name", "short_description", "website_slug", "website_image",
	        "duration", "default_price", "currency", "cta_label"],
	order_by="website_order asc, service_name asc",
	limit_page_length=limite,
)

servizi = []
for row in rows:
	prezzo = ""
	if row.default_price:
		prezzo = frappe.utils.fmt_money(row.default_price, currency=row.currency or "EUR")
	durata = ""
	if row.duration:
		durata = frappe.utils.cstr(row.duration) + " min"
	servizi.append({
		"nome": frappe.utils.escape_html(row.service_name or row.name),
		"descrizione": frappe.utils.escape_html(row.short_description or ""),
		"immagine": row.website_image or BLANK_PIXEL,
		"link": "/servizi/" + (row.website_slug or ""),
		"cta": frappe.utils.escape_html(row.cta_label or "Scopri di piu'"),
		"durata": durata,
		"prezzo": prezzo,
	})

component["servizi"] = servizi
component["vuoto"] = 0 if servizi else 1
"""


def servizi():
	item = card(
		"crm-servizi-card",
		[
			block(
				"crm-servizi-img",
				"img",
				attributes={"src": "", "alt": "", "loading": "lazy"},
				baseStyles={
					"width": "100%",
					"height": "160px",
					"objectFit": "cover",
					"borderRadius": "8px",
				},
				dynamicValues=[bind("immagine", "src", "componentData")],
			),
			block(
				"crm-servizi-nome",
				"h3",
				innerHTML="Nome servizio",
				baseStyles={"fontSize": "1.05rem", "fontWeight": "600", "color": INK},
				dynamicValues=[bind("nome", "innerHTML", "componentData")],
			),
			block(
				"crm-servizi-desc",
				"p",
				innerHTML="Descrizione breve",
				baseStyles={"fontSize": "0.9rem", "lineHeight": "1.55", "color": MUTED, "margin": "0"},
				dynamicValues=[bind("descrizione", "innerHTML", "componentData")],
			),
			block(
				"crm-servizi-meta",
				"div",
				baseStyles={
					"display": "flex",
					"gap": "12px",
					"marginTop": "auto",
					"paddingTop": "8px",
					"fontSize": "0.85rem",
					"color": "#525252",
				},
				children=[
					block(
						"crm-servizi-durata",
						"span",
						innerHTML="",
						dynamicValues=[bind("durata", "innerHTML", "componentData")],
					),
					block(
						"crm-servizi-prezzo",
						"span",
						innerHTML="",
						baseStyles={"fontWeight": "600", "color": INK},
						dynamicValues=[bind("prezzo", "innerHTML", "componentData")],
					),
				],
			),
			block(
				"crm-servizi-cta",
				"a",
				innerHTML="Scopri di piu'",
				attributes={"href": "#"},
				baseStyles={
					"marginTop": "4px",
					"fontSize": "0.9rem",
					"fontWeight": "600",
					"color": INK,
					"textDecoration": "none",
				},
				dynamicValues=[
					bind("cta", "innerHTML", "componentData"),
					{"key": "link", "type": "attribute", "property": "href", "comesFrom": "componentData"},
				],
			),
		],
	)
	root = section(
		"crm-servizi-root",
		[
			heading("crm-servizi-titolo", "I nostri servizi"),
			grid("crm-servizi-grid", [repeater("crm-servizi-repeater", "servizi", item)]),
		],
	)
	root["props"] = {
		"titolo": prop("I nostri servizi"),
		"categoria": prop(""),
		"limite": prop("6"),
	}
	return write("crm-servizi", "Servizi CRM", root, SERVIZI_SCRIPT)


# --------------------------------------------------------------- prodotti

PRODOTTI_SCRIPT = """# Products published on the website, from CRM Product.
# Props: titolo, limite. Text is escaped here — the renderer does not autoescape.
limite = frappe.utils.cint(props.limite)
if limite < 1 or limite > 48:
	limite = 6

rows = frappe.get_all(
	"CRM Product",
	filters={"disabled": 0, "publish_on_website": 1},
	fields=["name", "product_name", "short_description", "website_slug", "image",
	        "standard_rate", "cta_label"],
	order_by="website_order asc, product_name asc",
	limit_page_length=limite,
)

prodotti = []
for row in rows:
	prezzo = ""
	if row.standard_rate:
		prezzo = frappe.utils.fmt_money(row.standard_rate)
	prodotti.append({
		"nome": frappe.utils.escape_html(row.product_name or row.name),
		"descrizione": frappe.utils.escape_html(row.short_description or ""),
		"immagine": row.image or BLANK_PIXEL,
		"link": "/prodotti/" + (row.website_slug or ""),
		"cta": frappe.utils.escape_html(row.cta_label or "Dettagli"),
		"prezzo": prezzo,
	})

component["prodotti"] = prodotti
component["vuoto"] = 0 if prodotti else 1
"""


def prodotti():
	item = card(
		"crm-prodotti-card",
		[
			block(
				"crm-prodotti-img",
				"img",
				attributes={"src": "", "alt": "", "loading": "lazy"},
				baseStyles={
					"width": "100%",
					"height": "180px",
					"objectFit": "cover",
					"borderRadius": "8px",
				},
				dynamicValues=[bind("immagine", "src", "componentData")],
			),
			block(
				"crm-prodotti-nome",
				"h3",
				innerHTML="Nome prodotto",
				baseStyles={"fontSize": "1.05rem", "fontWeight": "600", "color": INK},
				dynamicValues=[bind("nome", "innerHTML", "componentData")],
			),
			block(
				"crm-prodotti-desc",
				"p",
				innerHTML="Descrizione breve",
				baseStyles={"fontSize": "0.9rem", "lineHeight": "1.55", "color": MUTED, "margin": "0"},
				dynamicValues=[bind("descrizione", "innerHTML", "componentData")],
			),
			block(
				"crm-prodotti-prezzo",
				"div",
				innerHTML="",
				baseStyles={"marginTop": "auto", "fontWeight": "600", "color": INK},
				dynamicValues=[bind("prezzo", "innerHTML", "componentData")],
			),
		],
	)
	root = section(
		"crm-prodotti-root",
		[
			heading("crm-prodotti-titolo", "I nostri prodotti"),
			grid("crm-prodotti-grid", [repeater("crm-prodotti-repeater", "prodotti", item)], "240px"),
		],
	)
	root["props"] = {"titolo": prop("I nostri prodotti"), "limite": prop("8")}
	return write("crm-prodotti", "Prodotti CRM", root, PRODOTTI_SCRIPT)


# --------------------------------------------------------------- form / prenota / contatti
#
# These three need no data script: their markup calls a Jinja method the CRM registers
# (see hooks.jinja), and Builder resolves it when it renders the page.


def jinja_block(component_id, name, call, props_map, title_default, wrapper_width="640px"):
	body = block(
		f"{component_id}-body",
		"div",
		innerHTML=call,
		baseStyles={"width": "100%", "maxWidth": wrapper_width, "margin": "0 auto"},
	)
	root = section(
		f"{component_id}-root",
		[heading(f"{component_id}-titolo", title_default), body],
		gap="20px",
	)
	root["props"] = props_map
	return write(component_id, name, root)


def build_all():
	written = [
		servizi(),
		prodotti(),
		jinja_block(
			"crm-form",
			"Form CRM",
			"{{ crm_form_html(props.modulo, props.titolo_form, props.pulsante) }}",
			{
				"titolo": prop("Scrivici"),
				"modulo": prop(""),
				"titolo_form": prop(""),
				"pulsante": prop(""),
			},
			"Scrivici",
		),
		jinja_block(
			"crm-prenota",
			"Prenota",
			"{{ crm_booking_html(props.calendario, props.pulsante) }}",
			{"titolo": prop("Prenota un appuntamento"), "calendario": prop(""), "pulsante": prop("")},
			"Prenota un appuntamento",
			"520px",
		),
		jinja_block(
			"crm-contatti",
			"Contatti",
			"{{ crm_contact_html(page_name) }}",
			{"titolo": prop("Dove siamo")},
			"Dove siamo",
			"900px",
		),
	]
	for path in written:
		print("scritto", os.path.relpath(path))


if __name__ == "__main__":
	build_all()
