# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Giving a report to the patient: the CRM's delivery (`crm.documenti.consegna`)
with the clinic's rule, online for 45 days.

By hand is always possible, and says to whom. Online needs the consent to online
reports and a document that may go online; the email carries a link and no
content, the code that opens it is given another way, five wrong codes lock it,
a withdrawn or expired delivery opens nothing, and every download is logged.
"""

from unittest import mock

import frappe
from frappe.utils import add_days, now_datetime

from crm.clinica import documenti
from crm.clinica.tests.test_archivio import ArchivioCase
from crm.clinica.tests.test_cartella import DESK, DOC1
from crm.documenti import consegna
from crm.moduli import consensi, traccia

LINK = "link-del-referto"


class ConsegnaCase(ArchivioCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		frappe.local.outgoing_email_account = {}
		posta = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Centro Referti",
				"email_id": "centro.referti@example.com",
				"enable_outgoing": 1,
				"default_outgoing": 1,
			}
		)
		posta.flags.ignore_mandatory = True
		posta.flags.ignore_validate = True
		posta.insert(ignore_permissions=True)
		stili = mock.patch("frappe.utils.get_assets_json", return_value={})
		stili.start()
		self.addCleanup(stili.stop)
		frappe.db.set_value("CRM Lead", self.anna.name, "email", "anna.referto@example.com")
		self.documento = self.archivia(DOC1, title="Esami", document_type="Test result")

	def tearDown(self):
		super().tearDown()
		frappe.local.outgoing_email_account = {}

	def consenso(self):
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, documenti.REFERTI_ONLINE)

	def online(self, **altro):
		self.come(DOC1)
		with mock.patch.object(consegna, "_segreto", return_value=LINK):
			return consegna.deliver_online(self.documento["name"], **altro)

	def apri(self, codice):
		frappe.set_user("Guest")
		return consegna.open_document(LINK, codice)


class AMano(ConsegnaCase):
	def test_si_consegna_sempre_a_mano(self):
		self.come(DOC1)
		fatto = consegna.deliver_by_hand(self.documento["name"], "Mario Cartella, il marito")
		[riga] = fatto["deliveries"]
		self.assertEqual(
			(riga["channel"], riga["status"], riga["delivered_to"]),
			("By hand", "Delivered", "Mario Cartella, il marito"),
		)
		# nobody named: the patient
		fatto = consegna.deliver_by_hand(self.documento["name"])
		self.assertEqual(fatto["deliveries"][0]["delivered_to"], "Anna Cartella")

	def test_chi_non_legge_il_documento_non_lo_consegna(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			consegna.deliver_by_hand(self.documento["name"])


class Online(ConsegnaCase):
	def test_senza_consenso_o_mai_online_no(self):
		self.come(DOC1)
		with self.assertRaises(frappe.ValidationError):
			consegna.deliver_online(self.documento["name"])
		self.consenso()
		frappe.db.set_value("CRM Document", self.documento["name"], "not_online", 1)
		self.come(DOC1)
		with self.assertRaises(frappe.ValidationError):
			consegna.deliver_online(self.documento["name"])

	def test_il_link_per_email_il_codice_a_voce(self):
		self.consenso()
		fatto = self.online()
		self.assertTrue(fatto["link"].endswith(f"/documento/{LINK}"))
		self.assertEqual(len(fatto["code"]), 6)
		self.assertEqual(fatto["email"], "anna.referto@example.com")
		frappe.set_user("Administrator")
		[posta] = frappe.get_all("Email Queue", fields=["message"], order_by="creation desc", limit=1)
		self.assertIn(f"/documento/{LINK}", posta.message)
		self.assertNotIn(fatto["code"], posta.message)
		self.assertNotIn("Esami", posta.message)
		# 45 days, at most
		self.assertEqual(
			frappe.utils.getdate(fatto["expires_on"]), frappe.utils.getdate(add_days(now_datetime(), 45))
		)

	def test_col_codice_si_scarica_e_resta_scritto(self):
		self.consenso()
		fatto = self.online(send_email=0)
		with self.assertRaises(frappe.ValidationError):
			self.apri("000000" if fatto["code"] != "000000" else "111111")
		aperto = self.apri(fatto["code"])
		self.assertEqual(aperto["title"], "Esami")
		consegna.download_document(LINK, aperto["session"])
		self.assertEqual(frappe.local.response.filecontent, b"Esame di record.doctor1@example.com")
		frappe.set_user("Administrator")
		[riga] = frappe.get_all(
			consegna.CONSEGNA,
			filters={"document": self.documento["name"]},
			fields=["name", "status", "downloads"],
		)
		self.assertEqual((riga.status, riga.downloads), ("Downloaded", 1))
		eventi = [e.event for e in traccia.eventi(consegna.CONSEGNA, riga.name)]
		self.assertEqual(eventi, ["online", "code_wrong", "opened", "downloaded"])
		# a session is not a code: an invented one opens nothing
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			consegna.download_document(LINK, "inventata")

	def test_cinque_codici_sbagliati_chiudono(self):
		self.consenso()
		fatto = self.online(send_email=0)
		sbagliato = "000000" if fatto["code"] != "000000" else "111111"
		for _volta in range(consegna.TENTATIVI):
			with self.assertRaises(frappe.ValidationError):
				self.apri(sbagliato)
		with self.assertRaises(frappe.PermissionError):
			self.apri(fatto["code"])

	def test_ritirato_o_scaduto_non_apre(self):
		self.consenso()
		fatto = self.online(send_email=0)
		frappe.set_user("Administrator")
		nome = frappe.db.get_value(consegna.CONSEGNA, {"document": self.documento["name"]}, "name")
		self.come(DOC1)
		consegna.withdraw(nome)
		with self.assertRaises(frappe.PermissionError):
			self.apri(fatto["code"])
		# a new code takes the place of the old one; and 45 days later it is gone
		fatto = self.online(send_email=0)
		frappe.set_user("Administrator")
		frappe.db.set_value(
			consegna.CONSEGNA,
			{"document": self.documento["name"], "status": "Available"},
			"expires_on",
			add_days(now_datetime(), -1),
		)
		with self.assertRaises(frappe.PermissionError):
			self.apri(fatto["code"])
