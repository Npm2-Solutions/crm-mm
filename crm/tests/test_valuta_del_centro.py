# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a site that never said where the centre is reads as Italian: the currency
it counts in, the prefix of a number typed without one."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm import lingue
from crm.dashboard.context import Context
from crm.utils import _region_of, to_e164


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

	def test_un_cellulare_senza_prefisso_e_italiano(self):
		# India, the library's fallback, left it as typed: no WhatsApp, SMS or call
		self.scegli()
		_region_of.cache_clear()
		self.assertEqual(to_e164("333 123 4567"), "+393331234567")

	def test_il_paese_detto_vale_per_i_suoi_numeri(self):
		self.scegli(paese="United Kingdom")
		_region_of.cache_clear()
		self.assertEqual(to_e164("020 7946 0018"), "+442079460018")
