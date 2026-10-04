# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The currency the centre counts in, where nobody chose one in Settings."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm import lingue
from crm.dashboard.context import Context


class LaValutaDelCentro(IntegrationTestCase):
	def setUp(self):
		self.prima = (
			frappe.db.get_single_value("FCRM Settings", "currency"),
			frappe.db.get_single_value("System Settings", "country"),
		)

	def tearDown(self):
		frappe.db.rollback()
		# written again, not committed: the cached values follow the rollback
		valuta, paese = self.prima
		frappe.db.set_single_value("FCRM Settings", "currency", valuta)
		frappe.db.set_single_value("System Settings", "country", paese)

	def scegli(self, valuta=None, paese=None):
		frappe.db.set_single_value("FCRM Settings", "currency", valuta)
		frappe.db.set_single_value("System Settings", "country", paese)

	def test_il_euro_dove_nessuno_ha_detto_niente(self):
		self.scegli()
		self.assertEqual(lingue.valuta(), "EUR")

	def test_la_valuta_del_paese_del_centro(self):
		self.scegli(paese="Switzerland")
		self.assertEqual(lingue.valuta(), "CHF")

	def test_quella_scelta_nelle_impostazioni_vince(self):
		self.scegli(valuta="GBP", paese="Italy")
		self.assertEqual(lingue.valuta(), "GBP")

	def test_la_dashboard_conta_in_euro(self):
		self.scegli()
		oggi = frappe.utils.getdate()
		self.assertEqual(Context(start=oggi, end=oggi, viewer="Administrator").currency, "EUR")

	def test_una_trattativa_in_euro_non_chiede_un_cambio(self):
		# with the dollar as the fallback, a deal in euros asked a provider for the
		# day's rate and was summed in dollars
		self.scegli()
		with patch("crm.fcrm.doctype.crm_deal.crm_deal.get_exchange_rate") as cambio:
			deal = frappe.get_doc(
				{"doctype": "CRM Deal", "currency": "EUR", "first_name": "Valuta", "deal_value": 100}
			).insert(ignore_permissions=True)
		cambio.assert_not_called()
		self.assertEqual(deal.exchange_rate, 1)
