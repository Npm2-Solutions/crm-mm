# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Invoices only to whoever should read them, and the site only where Builder is.

A line of an invoice says what was done - "seduta di psicoterapia" - and that is
health data: the Sales User no longer reads invoices, the practitioner reads those
of their own services, the front desk issues them and transmits them only where the
manager allowed it (doc 30).
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.activities import invoices_on
from crm.invoicing import permessi
from crm.invoicing.api import _verifica_invio
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

DESK = "invoices.desk@example.com"
DOCTOR = "invoices.doctor@example.com"
OTHER_DOCTOR = "invoices.other@example.com"
SALES = "invoices.sales@example.com"
MANAGER = "invoices.manager@example.com"
ACCOUNTANT = "invoices.accountant@example.com"


class InvoiceAccessCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		utenti.sincronizza()
		for user in (DESK, DOCTOR, OTHER_DOCTOR, SALES, MANAGER):
			make_user(user)
		utenti.assegna_livelli(DESK, ["segreteria"])
		utenti.assegna_livelli(DOCTOR, ["operatore"])
		utenti.assegna_livelli(OTHER_DOCTOR, ["operatore"])
		utenti.assegna_livelli(SALES, ["commerciale"])
		utenti.assegna_livelli(MANAGER, ["manager"])
		# an accountant who works on the Desk with the invoicing role only
		make_user(ACCOUNTANT, roles=["Invoicing Manager"])
		self.provider = self.make_provider(DOCTOR)
		self.other_provider = self.make_provider(OTHER_DOCTOR)
		livelli.dimentica_cache()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def make_provider(self, user):
		name = frappe.db.get_value("CRM Service Provider", {"user": user})
		if name:
			return name
		qualification = frappe.get_all("CRM Professional Qualification", pluck="name", limit=1)[0]
		return (
			frappe.get_doc(
				{
					"doctype": "CRM Service Provider",
					"provider_name": f"Provider {user}",
					"qualification": qualification,
					"user": user,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def as_user(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()


class TestChiLegge(InvoiceAccessCase):
	def test_il_commerciale_non_legge_le_fatture(self):
		self.assertFalse(frappe.has_permission("CRM Invoice", "read", user=SALES))

	def test_la_segreteria_le_legge_le_emette_e_non_le_annulla(self):
		self.assertTrue(frappe.has_permission("CRM Invoice", "read", user=DESK))
		self.assertTrue(frappe.has_permission("CRM Invoice", "create", user=DESK))
		self.assertTrue(frappe.has_permission("CRM Invoice", "submit", user=DESK))
		self.assertFalse(frappe.has_permission("CRM Invoice", "cancel", user=DESK))

	def test_l_operatore_legge_e_non_scrive(self):
		self.assertTrue(frappe.has_permission("CRM Invoice", "read", user=DOCTOR))
		self.assertFalse(frappe.has_permission("CRM Invoice", "create", user=DOCTOR))

	def test_il_manager_fa_tutto(self):
		for ptype in ("read", "create", "submit", "cancel"):
			self.assertTrue(frappe.has_permission("CRM Invoice", ptype, user=MANAGER), ptype)


class TestLeSue(InvoiceAccessCase):
	def invoice_by(self, provider):
		return frappe.get_doc({"doctype": "CRM Invoice", "items": [{"service_provider": provider}]})

	def test_l_operatore_vede_solo_le_fatture_delle_sue_prestazioni(self):
		self.assertTrue(permessi.has_permission(self.invoice_by(self.provider), "read", DOCTOR))
		self.assertFalse(permessi.has_permission(self.invoice_by(self.other_provider), "read", DOCTOR))

	def test_la_condizione_della_lista_e_la_stessa(self):
		condizione = permessi.get_permission_query_conditions(DOCTOR)
		self.assertIn(frappe.db.escape(self.provider), condizione)
		self.assertNotIn(frappe.db.escape(self.other_provider), condizione)

	def test_un_operatore_senza_erogatore_non_vede_niente(self):
		make_user("invoices.new.doctor@example.com")
		utenti.assegna_livelli("invoices.new.doctor@example.com", ["operatore"])
		self.assertEqual(permessi.get_permission_query_conditions("invoices.new.doctor@example.com"), "1=0")

	def test_chi_vede_il_centro_non_viene_ristretto(self):
		self.assertEqual(permessi.get_permission_query_conditions(DESK), "")
		self.assertEqual(permessi.get_permission_query_conditions(MANAGER), "")
		self.assertTrue(permessi.has_permission(self.invoice_by(self.other_provider), "read", DESK))

	def test_chi_lavora_dal_desk_tiene_quello_che_aveva(self):
		"""The scope narrows, never widens, and never touches who is outside levels."""
		self.assertEqual(permessi.get_permission_query_conditions(ACCOUNTANT), "")

	def test_la_cronologia_non_mostra_fatture_a_chi_non_le_legge(self):
		self.as_user(SALES)
		get_list = frappe.get_list

		def guarded(doctype, *args, **kwargs):
			if doctype == "CRM Invoice":
				raise AssertionError("the invoices must not even be asked for")
			return get_list(doctype, *args, **kwargs)

		with patch.object(frappe, "get_list", side_effect=guarded):
			self.assertEqual(invoices_on("CRM Lead", "CRM-LEAD-NONE"), [])


class TestInvio(InvoiceAccessCase):
	def test_la_segreteria_trasmette_solo_se_il_manager_lo_ha_permesso(self):
		self.as_user(DESK)
		self.assertRaises(frappe.PermissionError, _verifica_invio)
		frappe.set_user("Administrator")
		utenti.imposta_capacita(DESK, "fatture.invia", True)
		self.as_user(DESK)
		_verifica_invio()

	def test_il_manager_trasmette(self):
		self.as_user(MANAGER)
		_verifica_invio()

	def test_chi_lavora_dal_desk_trasmette_come_prima(self):
		self.as_user(ACCOUNTANT)
		_verifica_invio()


class TestSito(InvoiceAccessCase):
	def test_senza_builder_il_sito_non_e_di_nessuno(self):
		builder = "builder" in frappe.get_installed_apps()
		self.assertEqual(livelli.puo("sito.gestisci", MANAGER), builder)
		self.assertEqual(livelli.puo("sito.gestisci", "Administrator"), builder)

	def test_con_builder_torna(self):
		with patch.object(frappe, "get_installed_apps", return_value=["frappe", "crm", "builder"]):
			livelli.dimentica_cache()
			self.assertTrue(livelli.puo("sito.gestisci", MANAGER))
