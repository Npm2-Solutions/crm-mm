# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's economics, on a real site: what was collected and what waits, the
suppliers' costs, the margin and the VAT of the period.

Collected is a fact of its own (`incassi`): an invoice to a person issued at the
desk was paid there, one to a company waits to be marked, a credit note is never
collected. The numbers come from the same widgets the «Centre economics» template
draws, each asked over this test's own month.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate, nowdate

from crm.dashboard import registry
from crm.dashboard.context import Context
from crm.dashboard.widgets import invoicing as W
from crm.invoicing import incassi
from crm.tests.test_invoicing import PIVA, InvoicingBase


class EconomiaTest(InvoicingBase):
	def numero(self, widget_id: str, **config) -> float:
		widget = registry.get(widget_id)
		ctx = Context.build(
			add_days(nowdate(), -5), add_days(nowdate(), 5), scope="site", config=widget.clean_config(config)
		)
		return widget.fn(ctx)

	def a_un_azienda(self):
		documento = self.fattura(
			self.trattamento.name,
			self.osteopata.name,
			recipient_type="soggetto_iva",
			billing_name="Acme Srl",
			company_name="Acme Srl",
			tax_id=PIVA,
			recipient_code="0000000",
		)
		documento.submit()
		return documento

	def test_alla_cassa_una_persona_ha_pagato_un_azienda_aspetta(self):
		persona = self.fattura(self.seduta.name, self.psicologo.name)
		persona.submit()
		incassi.alla_cassa(persona)
		persona.reload()
		self.assertEqual(getdate(persona.collected_on), getdate(persona.payment_date))

		azienda = self.a_un_azienda()
		incassi.alla_cassa(azienda)
		azienda.reload()
		self.assertIsNone(azienda.collected_on)

	def test_si_segna_e_si_toglie(self):
		azienda = self.a_un_azienda()
		self.assertEqual(incassi.set_collected(azienda.name, nowdate())["collected_on"], nowdate())
		self.assertIsNone(incassi.set_collected(azienda.name)["collected_on"])
		self.assertTrue(frappe.db.exists("CRM Invoice Log", {"invoice": azienda.name, "event": "collected"}))
		with self.assertRaises(frappe.ValidationError):
			# before the invoice existed, without being a prepayment
			incassi.set_collected(azienda.name, add_days(azienda.posting_date, -10))

	def test_da_incassare_e_incassato(self):
		prima = self.numero("to_collect")["value"]
		azienda = self.a_un_azienda()
		self.assertAlmostEqual(self.numero("to_collect")["value"], prima + float(azienda.net_payable))
		incassati = self.numero("collected")["value"]
		incassi.set_collected(azienda.name, nowdate())
		self.assertAlmostEqual(self.numero("to_collect")["value"], prima)
		self.assertAlmostEqual(self.numero("collected")["value"], incassati + float(azienda.net_payable))

	def test_le_fasce_di_attesa(self):
		self.assertEqual(
			[W.age_bucket(g) for g in (0, 30, 31, 60, 61, 90, 91, 400)], [0, 0, 1, 1, 2, 2, 3, 3]
		)
		self.a_un_azienda()
		torta = self.numero("to_collect_by_age")
		self.assertEqual(torta["kind"], "donut")
		# as many rows as it gives: the site may hold older ones waiting
		elenco = self.numero("to_collect_list", limit=20)
		self.assertIn("Acme Srl", [voce["title"] for voce in elenco["items"]])
		# what the page receives: the bands' words travel as JSON (a lazy one
		# failed the whole dashboard's request)
		frappe.as_json(torta)
		frappe.as_json(elenco)
		self.assertTrue(all(isinstance(voce["badge"]["label"], str) for voce in elenco["items"]))

	def test_costi_margine_e_iva(self):
		fattura = frappe.get_doc(
			{
				"doctype": "CRM Supplier Invoice",
				"company": self.azienda.name,
				"supplier_name": "Forniture Mediche Srl",
				"document_date": nowdate(),
				"total_amount": 122,
				"taxable_amount": 100,
				"vat_amount": 22,
				"status": "ricevuta",
			}
		).insert(ignore_permissions=True)
		con_iva = self.numero("supplier_invoices_received")["value"]
		senza = self.numero("supplier_invoices_received", costs="net")["value"]
		# with its VAT the invoice costs 22 more than without
		self.assertGreaterEqual(con_iva - senza, 22)
		self.assertGreaterEqual(con_iva, 122)
		barre = self.numero("costs_by_supplier")
		self.assertIn("Forniture Mediche Srl", barre["x"]["values"])

		margine = self.numero("margin")["value"]
		fattura.db_set("status", "rifiutata")
		# a disputed invoice is not a cost
		self.assertAlmostEqual(self.numero("margin")["value"], margine + 122)
		self.assertEqual(self.numero("margin_trend")["kind"], "axis")
		self.assertEqual(self.numero("vat_balance")["kind"], "number")

	def test_il_modello_economia_del_centro(self):
		from crm.dashboard import templates

		modello = next(t for t in templates.TEMPLATES if t.id == "economy")
		for nome in modello.widget_ids():
			self.assertIsNotNone(registry.get(nome), nome)
