# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""One fiscal profile per person, on a real site.

The codice fiscale and the address were retyped on every invoice: the invoice took
only the name from the person. Now the invoice reads the profile, a confirmed
invoice fills it where it is empty, and whoever sees the person - and may see
billing details at all - reads and corrects it from the person's page.
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_linked_docs_of_document
from crm.invoicing import anagrafica
from crm.patches.v1_0 import billing_details_from_past_invoices
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.tests.test_invoicing import CF_PAZIENTE, InvoicingBase

CF_GIULIA = "RSSGLI12M41H501W"
DESK = "profile.desk@example.com"
DOCTOR = "profile.doctor@example.com"
SALES = "profile.sales@example.com"

SENZA_CLIENTE = {
	"fiscal_code": None,
	"address_line": None,
	"postal_code": None,
	"city": None,
	"province": None,
}

INDIRIZZO = {
	"address_line": "Via Verdi",
	"civic_number": "3",
	"postal_code": "00100",
	"city": "Roma",
	"province": "RM",
}


class ProfileBase(InvoicingBase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.mario = self.persona("Mario", "Rossi")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	@staticmethod
	def persona(nome, cognome=None, **valori):
		return frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": nome, "last_name": cognome, **valori}
		).insert(ignore_permissions=True)

	@staticmethod
	def profilo(party, party_type="CRM Lead", **valori):
		return frappe.get_doc(
			{"doctype": "CRM Billing Profile", "party_type": party_type, "party": party, **valori}
		).insert()

	@staticmethod
	def del_titolare(party, party_type="CRM Lead"):
		nome = anagrafica.nome_del_profilo(party_type, party)
		return frappe.get_doc("CRM Billing Profile", nome) if nome else None

	def fattura_a(self, persona, **valori):
		return self.fattura(
			self.seduta.name,
			self.psicologo.name,
			party_type="CRM Lead",
			party=persona.name,
			**{**SENZA_CLIENTE, **valori},
		)


class LaFatturaLeggeIlProfilo(ProfileBase):
	def test_codice_fiscale_e_indirizzo_non_si_riscrivono(self):
		self.profilo(self.mario.name, fiscal_code=CF_PAZIENTE, **INDIRIZZO)
		documento = self.fattura_a(self.mario)
		self.assertEqual(documento.fiscal_code, CF_PAZIENTE)
		self.assertEqual(documento.city, "Roma")
		self.assertEqual(documento.civic_number, "3")
		self.assertEqual(documento.billing_name, "Mario Rossi")

	def test_quello_scritto_sulla_fattura_resta(self):
		self.profilo(self.mario.name, fiscal_code=CF_PAZIENTE, **INDIRIZZO)
		documento = self.fattura_a(self.mario, fiscal_code=CF_GIULIA, city="Milano")
		self.assertEqual(documento.fiscal_code, CF_GIULIA)
		# a city typed at the desk keeps the profile's street off the invoice
		self.assertEqual(documento.city, "Milano")
		self.assertFalse(documento.address_line)

	def test_la_trattativa_porta_alla_persona_o_all_organizzazione(self):
		organizzazione = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": f"Acme {frappe.generate_hash(length=6)} Srl"}
		).insert(ignore_permissions=True)
		trattativa = frappe.get_doc(
			{"doctype": "CRM Deal", "lead": self.mario.name, "organization": organizzazione.name}
		).insert(ignore_permissions=True)
		self.assertEqual(
			anagrafica.titolare_di("CRM Deal", trattativa.name, "persona_fisica"),
			("CRM Lead", self.mario.name),
		)
		self.assertEqual(
			anagrafica.titolare_di("CRM Deal", trattativa.name, "soggetto_iva"),
			("CRM Organization", organizzazione.name),
		)

	def test_il_contatto_e_la_sua_persona(self):
		contatto = frappe.db.get_value("CRM Lead", self.mario.name, "contact")
		if not contatto:
			self.skipTest("this site does not give every person a contact")
		self.assertEqual(anagrafica.titolare_di("Contact", contatto), ("CRM Lead", self.mario.name))


class LaFatturaConfermataCompleta(ProfileBase):
	def test_il_secondo_documento_non_chiede_niente(self):
		self.fattura_a(self.mario, fiscal_code=CF_PAZIENTE, **INDIRIZZO).submit()
		profilo = self.del_titolare(self.mario.name)
		self.assertEqual(profilo.fiscal_code, CF_PAZIENTE)
		self.assertEqual(profilo.city, "Roma")
		self.assertEqual(str(profilo.birth_date), "1980-01-01")
		self.assertEqual(profilo.sex, "M")
		self.assertTrue(profilo.filled_from_invoice)
		seconda = self.fattura_a(self.mario)
		self.assertEqual(seconda.fiscal_code, CF_PAZIENTE)
		self.assertEqual(seconda.postal_code, "00100")

	def test_non_sovrascrive_quello_che_c_e(self):
		self.profilo(
			self.mario.name,
			fiscal_code=CF_PAZIENTE,
			address_line="Via Po",
			city="Torino",
			postal_code="10100",
		)
		self.fattura_a(self.mario, fiscal_code=CF_PAZIENTE, **INDIRIZZO, pec="mario@pec.it").submit()
		profilo = self.del_titolare(self.mario.name)
		self.assertEqual(profilo.city, "Torino")
		self.assertEqual(profilo.pec, "mario@pec.it")

	def test_a_nome_del_genitore_non_si_completa(self):
		giulia = self.persona("Giulia", "Rossi")
		self.fattura_a(
			giulia,
			billing_name="Luca Rossi",
			first_name="Luca",
			last_name="Rossi",
			fiscal_code=CF_PAZIENTE,
			**INDIRIZZO,
		).submit()
		self.assertIsNone(self.del_titolare(giulia.name))

	def test_il_nome_intero_scritto_nel_nome(self):
		intero = self.persona("Mario Rossi")
		self.fattura_a(intero, billing_name="Mario Rossi", fiscal_code=CF_PAZIENTE, **INDIRIZZO).submit()
		self.assertEqual(self.del_titolare(intero.name).fiscal_code, CF_PAZIENTE)

	def test_un_errore_non_ferma_la_fattura(self):
		with patch.object(anagrafica, "_completa", side_effect=RuntimeError("boom")):
			documento = self.fattura_a(self.mario, fiscal_code=CF_PAZIENTE, **INDIRIZZO)
			documento.submit()
		self.assertEqual(documento.docstatus, 1)
		self.assertIsNone(self.del_titolare(self.mario.name))

	def test_il_recupero_dalle_fatture_gia_emesse(self):
		prima = self.fattura_a(self.mario, fiscal_code=CF_PAZIENTE, **INDIRIZZO, posting_date="2026-01-10")
		prima.submit()
		dopo = self.fattura_a(
			self.mario, fiscal_code=CF_PAZIENTE, **{**INDIRIZZO, "city": "Frascati", "postal_code": "00044"}
		)
		dopo.submit()
		# as if they had been issued before the profile existed
		frappe.delete_doc("CRM Billing Profile", anagrafica.nome_del_profilo("CRM Lead", self.mario.name))
		billing_details_from_past_invoices.execute()
		profilo = self.del_titolare(self.mario.name)
		self.assertEqual(profilo.city, "Frascati")
		self.assertEqual(profilo.filled_from_invoice, dopo.name)


class IlProfilo(ProfileBase):
	def test_se_ne_va_con_la_persona(self):
		"""Part of the person: it neither stops the deletion nor outlives it."""
		self.profilo(self.mario.name, fiscal_code=CF_PAZIENTE)
		self.assertNotIn(
			"CRM Billing Profile",
			[d["doc"] for d in get_linked_docs_of_document("CRM Lead", self.mario.name)],
		)
		# an automation of the site may have enrolled the new person: not ours to test
		frappe.db.delete(
			"CRM Automation Enrollment", {"reference_doctype": "CRM Lead", "reference_name": self.mario.name}
		)
		frappe.delete_doc("CRM Lead", self.mario.name)
		self.assertIsNone(self.del_titolare(self.mario.name))

	def test_un_codice_sbagliato_non_si_salva(self):
		with self.assertRaises(frappe.ValidationError):
			self.profilo(self.mario.name, fiscal_code="RSSMRA80A01H501A")

	def test_un_profilo_per_persona(self):
		self.profilo(self.mario.name, city="Roma")
		with self.assertRaises(frappe.DuplicateEntryError):
			self.profilo(self.mario.name, city="Milano")

	def test_si_scrive_sempre_allo_stesso_modo(self):
		profilo = self.profilo(self.mario.name, fiscal_code=" rssmra80a01h501u", province="rm")
		self.assertEqual(profilo.fiscal_code, CF_PAZIENTE)
		self.assertEqual(profilo.province, "RM")
		self.assertEqual(profilo.party_name, "Mario Rossi")

	def test_gli_avvisi_dicono_senza_bloccare(self):
		if not frappe.db.exists("Gender", "Female"):
			frappe.get_doc({"doctype": "Gender", "gender": "Female"}).insert(ignore_permissions=True)
		giulia = self.persona("Giulia", "Bianchi", gender="Female")
		profilo = self.profilo(giulia.name, fiscal_code=CF_PAZIENTE)
		avvisi = " | ".join(anagrafica.avvisi(profilo))
		self.assertIn("surname Bianchi", avvisi)
		self.assertIn("first name Giulia", avvisi)
		self.assertIn("sex", avvisi)
		self.profilo(self.mario.name, fiscal_code=CF_PAZIENTE)
		self.assertIn("is on Mario Rossi", " | ".join(anagrafica.avvisi(profilo)))


class ChiLoVede(ProfileBase):
	def setUp(self):
		super().setUp()
		utenti.sincronizza()
		for user in (DESK, DOCTOR, SALES):
			make_user(user)
		utenti.assegna_livelli(DESK, ["segreteria"])
		utenti.assegna_livelli(DOCTOR, ["operatore"])
		utenti.assegna_livelli(SALES, ["commerciale"])
		self.del_desk = self.persona("Anna", "Verdi", lead_owner=DESK)
		self.profilo(self.del_desk.name, fiscal_code=CF_PAZIENTE)
		self.profilo(self.mario.name, city="Roma")
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def test_il_commerciale_non_vede_i_dati_fiscali(self):
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			anagrafica.get_billing_profile("CRM Lead", self.del_desk.name)

	def test_la_segreteria_li_legge_e_li_corregge(self):
		self.come(DESK)
		risposta = anagrafica.get_billing_profile("CRM Lead", self.del_desk.name)
		self.assertEqual(risposta["values"]["fiscal_code"], CF_PAZIENTE)
		self.assertTrue(risposta["can_write"])
		risposta = anagrafica.save_billing_profile("CRM Lead", self.del_desk.name, {"city": "Napoli"})
		self.assertEqual(risposta["values"]["city"], "Napoli")

	def test_seguono_la_persona(self):
		"""Billing details of a person the practitioner does not look after stay out of
		reach; the front desk sees the whole centre (doc 30), theirs included."""
		sua = self.persona("Carla", "Gialli", lead_owner=DOCTOR)
		self.profilo(sua.name, city="Torino")
		self.come(DOCTOR)
		with self.assertRaises(frappe.PermissionError):
			anagrafica.get_billing_profile("CRM Lead", self.mario.name)
		visibili = frappe.get_list("CRM Billing Profile", pluck="party")
		self.assertIn(sua.name, visibili)
		self.assertNotIn(self.mario.name, visibili)
		self.come(DESK)
		visibili = frappe.get_list("CRM Billing Profile", pluck="party")
		self.assertIn(self.mario.name, visibili)
		self.assertIn(self.del_desk.name, visibili)

	def test_il_primo_dato_crea_il_profilo(self):
		nuova = self.persona("Paola", "Neri", lead_owner=DESK)
		self.come(DESK)
		self.assertIsNone(anagrafica.get_billing_profile("CRM Lead", nuova.name)["name"])
		risposta = anagrafica.save_billing_profile("CRM Lead", nuova.name, '{"pec": "paola@pec.it"}')
		self.assertTrue(risposta["name"])

	def test_il_medico_scrive_il_codice_fiscale_una_volta(self):
		sua = self.persona("Carla", "Gialli", lead_owner=DOCTOR)
		self.come(DOCTOR)
		risposta = anagrafica.save_billing_profile("CRM Lead", sua.name, {"fiscal_code": CF_GIULIA})
		self.assertEqual(risposta["sex"], "F")
