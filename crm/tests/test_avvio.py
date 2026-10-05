# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the page says at the start, so that the first page waits on no call in a
row: whether the session opens DottorCloud, whether it is welcomed first
(crm.www.crm, crm.benvenuto)."""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm import benvenuto
from crm.www.crm import get_boot, session_opens_the_crm


class TestAvvio(FrappeTestCase):
	def setUp(self):
		from crm.registrazione import carica

		carica()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_the_page_says_the_session_opens_dottorcloud(self):
		boot = get_boot()
		self.assertIs(boot.crm_user, True)
		self.assertIn("benvenuto", boot)

	def test_a_guest_does_not(self):
		frappe.set_user("Guest")
		self.assertFalse(session_opens_the_crm())
		self.assertFalse(benvenuto.per_il_boot())

	def test_welcomed_while_the_centre_has_no_name(self):
		frappe.defaults.clear_default(benvenuto.FATTO)
		with patch("crm.moduli.richieste.nome_del_centro", return_value=""):
			self.assertTrue(benvenuto.per_il_boot())
		# a centre that already works has its name
		with patch("crm.moduli.richieste.nome_del_centro", return_value="Studio Rossi"):
			self.assertFalse(benvenuto.per_il_boot())
