# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's summary (crm/persone/riepilogo.py, docs/crm/54).

Mario has a cycle of physiotherapy going on, two things left to do - one done is not
among them - and an invoice issued and not collected yet: a collected one, a test
one, a credit note are no money owed. The desk reads it all in one call, the tasks
with a day first. Marketing reads people, not the agenda nor the invoices: those
lines are not there for them, and nothing says they were refused. A line that
refuses or breaks leaves the summary standing.
"""

from unittest.mock import patch

import frappe
from frappe.utils import add_days, getdate, today

from crm.invoicing import api as fatture
from crm.invoicing.install import semina_qualifiche
from crm.persone import riepilogo
from crm.scheduling import cicli

# modules, not classes: a TestCase imported here would run here too
from crm.tests import test_cicli as casi_dei_cicli
from crm.tests import test_invoicing as fatturazione

DESK = casi_dei_cicli.DESK
MARKETING = casi_dei_cicli.MARKETING


class RiepilogoCase(casi_dei_cicli.CicliCase):
	def riepilogo(self, user=DESK):
		self.come(user)
		try:
			return riepilogo.get_summary(self.mario.name)
		finally:
			frappe.set_user("Administrator")

	def compito(self, titolo, **campi):
		return frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": titolo,
				"reference_doctype": "CRM Lead",
				"reference_docname": self.mario.name,
				"status": "Todo",
				**campi,
			}
		).insert(ignore_permissions=True)


class IlRiepilogo(RiepilogoCase):
	def test_una_persona_nuova_non_ha_niente_da_dire(self):
		self.assertEqual(self.riepilogo(), {})

	def test_le_cose_da_fare_prima_quelle_con_un_giorno(self):
		self.compito("Senza giorno")
		self.compito("Richiamare", due_date=f"{add_days(getdate(), 1)} 10:00:00")
		self.compito("Fatto", status="Done")
		fatto = self.riepilogo()["tasks"]
		self.assertEqual(fatto["count"], 2)
		self.assertEqual([riga["title"] for riga in fatto["tasks"]], ["Richiamare", "Senza giorno"])
		self.assertIsNone(fatto["tasks"][1]["due_date"])

	def test_il_ciclo_in_corso_per_chi_legge_l_agenda(self):
		ciclo = self.ciclo(3)
		[riga] = self.riepilogo()["in_progress"]["cycles"]
		self.assertEqual((riga["name"], riga["service"]), (ciclo["name"], "Fisioterapia a cicli"))
		self.assertEqual((riga["counts"]["total"], riga["counts"]["done"]), (3, 0))
		# marketing reads the person, not the agenda: no line, and no refusal
		frappe.local.message_log = []
		self.assertNotIn("in_progress", self.riepilogo(MARKETING))
		self.assertEqual(frappe.local.message_log, [])

	def test_un_ciclo_chiuso_non_e_in_corso(self):
		ciclo = self.ciclo(3)
		frappe.db.set_value(cicli.CICLO, ciclo["name"], "status", "Closed")
		self.assertNotIn("in_progress", self.riepilogo())

	def test_una_riga_che_rifiuta_o_si_rompe_non_ferma_il_resto(self):
		def rifiuta(lead):
			frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

		def si_rompe(lead):
			raise ValueError("broken")

		voci = {
			"rifiuta": riepilogo.Voce("rifiuta", rifiuta),
			"si_rompe": riepilogo.Voce("si_rompe", si_rompe),
			"dice": riepilogo.Voce("dice", lambda lead: {"lead": lead}),
		}
		errori = frappe.db.count("Error Log")
		frappe.local.message_log = []
		with patch.dict(riepilogo._voci, voci):
			fatto = self.riepilogo()
		self.assertEqual(fatto["dice"], {"lead": self.mario.name})
		self.assertNotIn("rifiuta", fatto)
		self.assertNotIn("si_rompe", fatto)
		# what the refusal said goes with it; the one that broke is written down
		self.assertEqual(frappe.local.message_log, [])
		self.assertEqual(frappe.db.count("Error Log"), errori + 1)

	def test_chi_non_legge_la_persona_non_legge_il_riepilogo(self):
		# a physiotherapist reads the people in their care: Mario is not, yet
		with self.assertRaises(frappe.PermissionError):
			self.riepilogo(casi_dei_cicli.ALTRO)


class IlDaPagare(RiepilogoCase):
	def setUp(self):
		super().setUp()
		semina_qualifiche()
		fatturazione.InvoicingBase.crea_azienda()
		erogatore = fatturazione.InvoicingBase.crea_erogatore("Dott.ssa Bianchi", "psicologo")
		frappe.get_doc(
			{
				"doctype": "CRM Billable Service",
				"service_name": "Fisioterapia a cicli (riepilogo)",
				"fiscal_description": "Seduta di fisioterapia",
				"crm_service": self.fisio.name,
				"is_healthcare": 0,
				"vat_rate": 22,
				"default_rate": 50,
				"default_provider": erogatore.name,
				"enabled": 1,
			}
		).insert()

	def fattura(self, emessa=True):
		"""An invoice to Mario: the cycle's draft, issued - a real one, not a test -
		and still to collect."""
		fatto = self.ciclo(2, price=90, billing=cicli.INTERO, starts_on=str(add_days(getdate(), -7)))
		nome = fatture.issue_from_cycle(fatto["name"])
		if emessa:
			frappe.db.set_value(
				"CRM Invoice", nome, {"docstatus": 1, "collected_on": None, "test_document": 0}
			)
		return nome

	def test_una_fattura_da_incassare(self):
		nome = self.fattura()
		pagabile = frappe.db.get_value("CRM Invoice", nome, "net_payable") or frappe.db.get_value(
			"CRM Invoice", nome, "grand_total"
		)
		fatto = self.riepilogo()["to_collect"]
		self.assertEqual((fatto["count"], fatto["drafts"]), (1, 0))
		self.assertEqual(fatto["total"], pagabile)
		self.assertEqual(fatto["invoices"][0]["name"], nome)
		# marketing does not read invoices
		self.assertNotIn("to_collect", self.riepilogo(MARKETING))

	def test_incassata_di_prova_o_nota_di_credito_non_si_deve(self):
		nome = self.fattura()
		frappe.db.set_value("CRM Invoice", nome, "collected_on", today())
		self.assertNotIn("to_collect", self.riepilogo())
		frappe.db.set_value("CRM Invoice", nome, {"collected_on": None, "test_document": 1})
		self.assertNotIn("to_collect", self.riepilogo())
		frappe.db.set_value("CRM Invoice", nome, {"test_document": 0, "document_type": "TD04"})
		self.assertNotIn("to_collect", self.riepilogo())

	def test_una_bozza_si_dice_da_emettere(self):
		self.fattura(emessa=False)
		fatto = self.riepilogo()["to_collect"]
		self.assertEqual((fatto["count"], fatto["drafts"], fatto["invoices"]), (0, 1, []))
