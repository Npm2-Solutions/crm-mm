# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How an email looks, on a real site.

Centro Aurora has a name and no logo: its name leads at the top of the card, the
product signs under it. With a logo of its own, a PNG, the logo leads; an SVG,
which no mail client shows everywhere, is left for the name. A centre with
neither: the product's logo leads, and does not sign twice. An email somebody
wrote stays a plain email. The framework's dot, its "Sent via", its Desk links are
gone; the unsubscribe link and the read receipt keep their place.
"""

from unittest.mock import patch

import frappe
from frappe.email.email_body import get_formatted_html
from frappe.tests import IntegrationTestCase

from crm.posta import aspetto


def _contesto(logo="", nome=""):
	dati = {
		"centre_logo": logo,
		"centre_logo_shape": "wide" if logo else "",
		"centre_name": nome,
		"colors": {"--brand": "#12a594", "--brand-strong": "#0b6f64"},
	}
	return patch("crm.marchio.per_le_pagine", return_value=dati)


class IlMarchioInAlto(IntegrationTestCase):
	def test_il_nome_del_centro(self):
		with _contesto(nome="Centro Aurora"):
			dc = aspetto.contesto_email()
		self.assertIsNone(dc["logo"])
		self.assertEqual(dc["centre"], "Centro Aurora")
		self.assertFalse(dc["product_leads"])
		self.assertTrue(dc["product_icon"].endswith(".png"))
		self.assertEqual(dc["action"], "#0b6f64")

	def test_un_logo_png_si_un_svg_no(self):
		with _contesto(logo="/files/aurora.png", nome="Centro Aurora"):
			self.assertTrue(aspetto.contesto_email()["logo"].endswith("/files/aurora.png"))
		with _contesto(logo="/files/aurora.svg", nome="Centro Aurora"):
			self.assertIsNone(aspetto.contesto_email()["logo"])
		# a private file is not for a mail client
		with _contesto(logo="/private/files/aurora.png", nome="Centro Aurora"):
			self.assertIsNone(aspetto.contesto_email()["logo"])

	def test_senza_niente_il_prodotto(self):
		with _contesto():
			dc = aspetto.contesto_email()
		self.assertTrue(dc["product_leads"])
		self.assertTrue(dc["product_logo"].endswith(".png"))


class LaCarta(IntegrationTestCase):
	def test_un_email_del_sistema(self):
		with _contesto(nome="Centro Aurora"):
			html = get_formatted_html(
				"Your code", "<p>Here is the code</p>", header="Your code", with_container=True
			)
		self.assertIn("Centro Aurora", html)
		self.assertIn("16px 16px 16px 2px", html)
		self.assertIn("Powered by", html)
		self.assertNotIn("indicator", html)
		self.assertNotIn("Frappe", html)
		self.assertIn("<!--email_open_check-->", html)
		self.assertIn("unsubscribe link here", html)

	def test_senza_nome_ne_logo_non_firma_due_volte(self):
		with _contesto():
			html = get_formatted_html("Your code", "<p>Here</p>", with_container=True)
		self.assertNotIn("Powered by", html)
		self.assertIn("dottorcloud-orizzontale.png", html)

	def test_un_email_scritta_da_qualcuno_resta_semplice(self):
		with _contesto(nome="Centro Aurora"):
			html = get_formatted_html("Re: domanda", "<p>Le confermo le 11.</p>")
		self.assertNotIn("Powered by", html)
		self.assertNotIn("dc-marchio-nome", html)
		self.assertIn("Le confermo le 11.", html)


class IPezzi(IntegrationTestCase):
	def test_il_pulsante(self):
		with _contesto(nome="Centro Aurora"):
			html = aspetto.pulsante('https://example.com/a?b=1&c="2"', "Apri <subito>")
		self.assertIn('href="https://example.com/a?b=1&amp;c=&quot;2&quot;"', html)
		self.assertIn("Apri &lt;subito&gt;", html)
		self.assertIn("#0b6f64", html)
		self.assertIn('class="btn btn-primary"', html)

	def test_il_codice(self):
		self.assertIn(">48&lt;29<", aspetto.codice("48<29"))

	def test_le_email_del_framework_per_assegnazioni_e_menzioni_non_partono(self):
		saltate = frappe.get_hooks("notification_skip_email_types")
		for tipo in ("Assignment", "Mention", "Share"):
			self.assertIn(tipo, saltate)
