# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# See license.txt

from frappe.tests import UnitTestCase

from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import in_frase


class TestCRMFieldsLayout(UnitTestCase):
	def test_il_nome_di_un_campo_dentro_una_frase(self):
		self.assertEqual(in_frase("Sito web"), "sito web")
		self.assertEqual(in_frase("Azienda"), "azienda")
		self.assertEqual(in_frase("Partita IVA"), "partita IVA")
		# as written: an acronym, an abbreviation, a capital inside, one letter
		for come_scritto in ("IVA", "PEC", "N. di dipendenti", "WhatsApp", "X", ""):
			self.assertEqual(in_frase(come_scritto), come_scritto)
