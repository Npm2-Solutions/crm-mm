# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How an email looks: what the layout needs of the brand and of the centre, and
the pieces a module puts in its message.

The centre's mark leads, as on its public pages: its logo where a mail client can
show it - a PNG or a JPEG at a public address, never an SVG - else its name; the
product's logo only for a centre with neither, and then it does not sign twice.
The product signs at the foot ("Powered by DottorCloud"), in the brand of the
vertical that is on.

Styles go on the elements themselves: a mail client keeps little else. The
framework inlines the layout's `<style>` too, for the clients that read it.
"""

from __future__ import annotations

from html import escape

import frappe
from frappe import _
from frappe.utils import get_url

from crm import marchio

#: The brand's surfaces and inks in the light theme: no mail client is asked to
#: draw the dark one (Espresso's tokens, brand/dottorcloud/design-system/espresso/tokens.css).
CANVAS = "#f6f9f8"
CARTA = "#ffffff"
FILO = "#ebeeed"
TITOLO = "#0e100f"
TESTO = "#151817"
META = "#4e5352"
TENUE = "#6a716f"
#: Images a mail client shows: not an SVG.
IMMAGINI = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def _immagine_pubblica(url: str | None) -> str | None:
	"""The address a mail client can load a logo from, or None: a public file of
	the site, as an image every client shows."""
	url = (url or "").split("?", 1)[0]
	if not url.startswith(("/files/", "/assets/")) or not url.lower().endswith(IMMAGINI):
		return None
	return get_url(url)


def contesto_email() -> dict:
	"""What every email wears (a Jinja method of the layout). Never raises: an
	email without it still goes, in the base's brand."""
	try:
		dati = marchio.per_le_pagine()
		attivo = marchio.attivo()
	except Exception:
		dati, attivo = marchio._dati(marchio.BASE), marchio.BASE
	logo_centro = _immagine_pubblica(dati.get("centre_logo"))
	nome_centro = dati.get("centre_name") or ""
	colori = dati.get("colors") or {}
	return {
		"logo": logo_centro,
		# a wide logo carries the centre's name; a square one goes beside it
		"logo_wide": bool(logo_centro) and dati.get("centre_logo_shape") == "wide",
		"centre": nome_centro,
		# the product leads only for a centre with neither a logo nor a name
		"product_leads": not (logo_centro or nome_centro),
		"product": attivo.nome,
		"product_logo": get_url(attivo.logo_email) if attivo.logo_email else "",
		"product_icon": get_url(attivo.icona_email) if attivo.icona_email else "",
		"signature": _("Powered by {0}").format(attivo.nome),
		"action": colori.get("--brand-strong") or attivo.colore_scuro,
		"brand": colori.get("--brand") or attivo.colore,
		"canvas": CANVAS,
		"card": CARTA,
		"line": FILO,
		"title": TITOLO,
		"text": TESTO,
		"meta": META,
		"muted": TENUE,
		"site": get_url(),
	}


def pulsante(url: str, testo: str) -> str:
	"""A button for the one thing an email asks: the brand's action colour, the
	cloud's tail, a table so that every client draws it (Outlook included)."""
	colore = contesto_email()["action"]
	return (
		'<table role="presentation" border="0" cellpadding="0" cellspacing="0" class="dc-pulsante" '
		'style="margin:8px 0 20px">'
		f'<tr><td bgcolor="{colore}" style="border-radius:8px 8px 8px 2px;background:{colore}">'
		f'<a href="{escape(url, quote=True)}" target="_blank" class="btn btn-primary" '
		f'style="display:inline-block;padding:12px 20px;font-size:15px;font-weight:600;'
		f"line-height:20px;color:#ffffff;background:{colore};text-decoration:none;"
		f'border-radius:8px 8px 8px 2px;margin:0">'
		f"{escape(testo)}</a></td></tr></table>"
	)


def codice(valore: str) -> str:
	"""A code to type, in its own box: big, spaced, easy to read and to copy."""
	return (
		f'<p class="dc-codice" style="margin:8px 0 20px;padding:14px 20px;display:inline-block;'
		f"background:{CANVAS};border:1px solid {FILO};border-radius:12px 12px 12px 2px;"
		f"font-size:28px;font-weight:700;letter-spacing:0.18em;color:{TITOLO};"
		f'font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">{escape(str(valore))}</p>'
	)
