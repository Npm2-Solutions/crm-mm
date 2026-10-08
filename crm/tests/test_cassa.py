# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The desk's cash closing on a real site (`crm.api.oggi`, `crm.invoicing.cassa`):
the day's money by way of paying and by who issued it, the credit notes out, the
drawer's cash against what was counted. A test invoice is never money."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, nowdate

from crm.api import oggi
from crm.tests.test_invoicing import InvoicingBase


class CassaTest(InvoicingBase):
	def incassata(self, metodo="MP01", **kwargs):
		documento = self.fattura(self.consulenza.name, self.consulente.name, payment_method=metodo, **kwargs)
		documento.submit()
		frappe.db.set_value("CRM Invoice", documento.name, {"collected_on": nowdate(), "test_document": 0})
		documento.reload()
		return documento

	def metodo(self, conti, codice) -> dict:
		return next(
			(voce for voce in conti["methods"] if voce["method"] == codice),
			{"collected": 0, "refunded": 0, "net": 0, "count": 0},
		)

	def test_per_metodo_con_i_nomi_e_le_note_di_credito(self):
		prima = oggi.get_cash_summary(nowdate())
		contanti = self.incassata("MP01")
		carta = self.incassata("MP08")
		nota = self.incassata("MP01")
		frappe.db.set_value(
			"CRM Invoice",
			nota.name,
			{"document_type": "TD04", "collected_on": None, "posting_date": nowdate()},
		)
		prova = self.incassata("MP01")
		frappe.db.set_value("CRM Invoice", prova.name, "test_document", 1)

		dopo = oggi.get_cash_summary(nowdate())
		importo = float(contanti.net_payable or contanti.grand_total)
		cash = self.metodo(dopo, "MP01")
		self.assertAlmostEqual(cash["collected"] - self.metodo(prima, "MP01")["collected"], importo)
		self.assertAlmostEqual(cash["refunded"] - self.metodo(prima, "MP01")["refunded"], importo)
		self.assertAlmostEqual(
			self.metodo(dopo, "MP08")["collected"] - self.metodo(prima, "MP08")["collected"],
			float(carta.net_payable or carta.grand_total),
		)
		# names, never codes
		self.assertEqual(cash["name"], "Cash")
		self.assertTrue(cash["cash"])
		self.assertAlmostEqual(dopo["expected_cash"], prima["expected_cash"])
		self.assertIn("Administrator", [chi["user"] for chi in dopo["by_user"]])

	def test_si_chiude_e_si_conta_di_nuovo(self):
		self.incassata("MP01")
		conti = oggi.get_cash_summary(nowdate())
		chiusa = oggi.close_cash_day(nowdate(), conti["expected_cash"] - 5, "Five euros short")
		self.assertEqual(chiusa["closing"]["difference"], -5)
		self.assertEqual(chiusa["closing"]["note"], "Five euros short")
		self.assertEqual(frappe.db.count("CRM Cash Closing", {"date": nowdate()}), 1)
		di_nuovo = oggi.close_cash_day(nowdate(), conti["expected_cash"])
		self.assertEqual(di_nuovo["closing"]["difference"], 0)
		self.assertEqual(frappe.db.count("CRM Cash Closing", {"date": nowdate()}), 1)
		self.assertTrue(
			frappe.get_all("CRM Cash Closing Method", filters={"parent": di_nuovo["closing"]["name"]})
		)

	def test_non_un_giorno_che_non_e_venuto(self):
		with self.assertRaises(frappe.ValidationError):
			oggi.close_cash_day(add_days(nowdate(), 1), 10)
		with self.assertRaises(frappe.ValidationError):
			oggi.close_cash_day(nowdate(), -1)
