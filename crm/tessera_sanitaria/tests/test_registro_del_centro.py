# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The practice's own register wins over the one DottorCloud ships, on a real site.

The massoterapista is shipped as a health profession, with a point still open for
the accountant. A practice whose accountant decides otherwise makes it ordinary in
its register, and its invoices follow its register; one that switches the osteopath
off gets a refusal, never the osteopath as it shipped.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from crm.invoicing import estensioni


class IlRegistroDelCentroVince(IntegrationTestCase):
	def test_una_qualifica_sanitaria_resa_ordinaria_resta_ordinaria(self):
		frappe.db.set_value(
			"CRM Professional Qualification",
			"massoterapista",
			{"sender_category": "non_sanitario", "ts_required": 0, "is_healthcare": 0},
		)
		prof = estensioni.risolutore()("massoterapista")
		self.assertFalse(prof.comunicazione_esterna)
		self.assertIsNone(prof.soggetto_comunicazione)

	def test_quella_scritta_dal_centro_porta_le_sue_correzioni(self):
		frappe.db.set_value("CRM Professional Qualification", "fisioterapista", "fund_rate", 2)
		prof = estensioni.risolutore()("fisioterapista")
		self.assertEqual(str(prof.cassa_percentuale), "2.0")
		self.assertTrue(prof.comunicazione_esterna)

	def test_una_qualifica_spenta_non_torna_come_spedita(self):
		frappe.db.set_value("CRM Professional Qualification", "osteopata", "enabled", 0)
		with self.assertRaises(estensioni.QualificaRifiutata) as errore:
			estensioni.risolutore()("osteopata")
		self.assertIn("Osteopata", str(errore.exception))
