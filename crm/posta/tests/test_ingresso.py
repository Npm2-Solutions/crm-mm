# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An email received reaches the person it is from, on a real site.

Anna Rossi is known: whatever mailbox she writes to, her email is on her page, never
a second Anna. Her answer to an appointment's reminder moves from the appointment
to her page, and the appointment keeps a link to it; a ticket of another app keeps
its thread. Somebody new becomes a person only where the mailbox says so, and never
"noreply", somebody of the centre or the mailbox a booking platform writes to.
Whoever follows Anna is told, and the second email adds to the first.
"""

import frappe
from frappe.tests import IntegrationTestCase

from crm.notifiche import regole as R
from crm.posta import ingresso
from crm.tests.test_documenti_del_core import FRONT_DESK, make_user


class IngressoCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		for campo in (
			"auto_reopen_on_new_communication",
			"auto_mark_replied_on_response",
			"update_timestamp_on_new_communication",
		):
			frappe.db.set_single_value("FCRM Settings", campo, 0)
		self.anna = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Anna",
				"last_name": "Rossi",
				"email": "anna.rossi@ingresso.test",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def casella(self, nuove_persone: int = 1, nome: str = "Ingresso Aurora"):
		if frappe.db.exists("Email Account", nome):
			return frappe.get_doc("Email Account", nome)
		doc = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": nome,
				"email_id": f"{frappe.scrub(nome)}@aurora.test",
				"enable_incoming": 1,
				"create_lead_from_incoming_email": nuove_persone,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.flags.ignore_validate = True
		return doc.insert(ignore_permissions=True)

	def arriva(self, mittente: str, casella=None, nome: str | None = None, **altro):
		doc = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": altro.pop("subject", "Una domanda"),
				"content": "Buongiorno",
				"sender": mittente,
				"sender_full_name": nome,
				"email_account": (casella or self.casella()).name,
				**altro,
			}
		)
		return doc.insert(ignore_permissions=True)


class ChiScriveEConosciuto(IngressoCase):
	def test_va_sulla_sua_pagina_e_non_nasce_un_altra_anna(self):
		# a mailbox that makes no new people still brings Anna her email
		email = self.arriva("anna.rossi@ingresso.test", casella=self.casella(nuove_persone=0))
		self.assertEqual((email.reference_doctype, email.reference_name), ("CRM Lead", self.anna.name))
		self.assertEqual(frappe.db.count("CRM Lead", {"email": "anna.rossi@ingresso.test"}), 1)

	def test_la_risposta_a_un_documento_suo_va_da_lei(self):
		cosa = frappe.get_doc(
			{"doctype": "CRM Task", "title": "Ricordare la visita", "reference_doctype": "CRM Lead"}
		).insert(ignore_permissions=True)
		email = self.arriva(
			"anna.rossi@ingresso.test",
			subject="Re: Il tuo appuntamento",
			reference_doctype="CRM Task",
			reference_name=cosa.name,
		)
		email.reload()
		self.assertEqual((email.reference_doctype, email.reference_name), ("CRM Lead", self.anna.name))
		# the document keeps it in its history
		self.assertIn(
			("CRM Task", str(cosa.name)), [(l.link_doctype, l.link_name) for l in email.timeline_links]
		)

	def test_il_filo_di_un_altra_app_resta_dov_e(self):
		compito = frappe.get_doc({"doctype": "ToDo", "description": "Un ticket"}).insert(
			ignore_permissions=True
		)
		email = self.arriva("anna.rossi@ingresso.test", reference_doctype="ToDo", reference_name=compito.name)
		self.assertEqual((email.reference_doctype, email.reference_name), ("ToDo", compito.name))


class ChiScriveENuovo(IngressoCase):
	def test_diventa_una_persona_dove_la_casella_lo_dice(self):
		email = self.arriva("maria.bianchi@ingresso.test", nome="Anna Maria Bianchi")
		persona = frappe.get_doc("CRM Lead", email.reference_name)
		self.assertEqual(
			(persona.email, persona.first_name, persona.last_name),
			("maria.bianchi@ingresso.test", "Anna Maria", "Bianchi"),
		)
		self.arriva("paolo.verdi@ingresso.test", casella=self.casella(nuove_persone=0, nome="Solo lettura"))
		self.assertFalse(frappe.db.exists("CRM Lead", {"email": "paolo.verdi@ingresso.test"}))

	def test_non_le_macchine_ne_il_centro_ne_le_piattaforme(self):
		for mittente in ("noreply@banca.test", "MAILER-DAEMON@aurora.test", "notifiche+123@social.test"):
			self.assertTrue(ingresso.mittente_automatico(mittente), mittente)
			self.arriva(mittente)
			self.assertFalse(frappe.db.exists("CRM Lead", {"email": mittente}), mittente)
		self.assertFalse(ingresso.mittente_automatico("info@aurora.test"))

		# somebody of the centre, and one of its own mailboxes
		make_user("collega@aurora.test", "Sales User")
		altra = self.casella(nome="Amministrazione")
		for mittente in ("collega@aurora.test", altra.email_id):
			self.arriva(mittente)
			self.assertFalse(frappe.db.exists("CRM Lead", {"email": mittente}), mittente)

		# the mailbox a booking platform writes to: its sync finds the person
		piattaforma = self.casella(nome="Prenotazioni")
		connessione = frappe.get_doc(
			{
				"doctype": "CRM Booking Connection",
				"connection_name": "Piattaforma di prova",
				"platform": "MioDottore (email)",
				"inbound_email_account": piattaforma.name,
			}
		)
		connessione.flags.ignore_validate = True
		connessione.insert(ignore_permissions=True)
		self.arriva("prenotazioni@piattaforma.test", casella=piattaforma)
		self.assertFalse(frappe.db.exists("CRM Lead", {"email": "prenotazioni@piattaforma.test"}))

	def test_un_email_mandata_non_fa_una_persona(self):
		email = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Sent",
				"subject": "Preventivo",
				"sender": "segreteria@aurora.test",
				"recipients": "nuovo@ingresso.test",
				"email_account": self.casella().name,
			}
		).insert(ignore_permissions=True)
		self.assertIsNone(email.reference_doctype)

	def test_nome_e_cognome(self):
		self.assertEqual(ingresso.nome_e_cognome('"Anna Maria Rossi"', "x@y.test"), ("Anna Maria", "Rossi"))
		self.assertEqual(ingresso.nome_e_cognome("Anna", "x@y.test"), ("Anna", ""))
		self.assertEqual(ingresso.nome_e_cognome(None, "anna.rossi@y.test"), ("anna.rossi", ""))


class ChiLaSegueLoSa(IngressoCase):
	def test_l_avviso_e_il_secondo_si_aggiunge(self):
		make_user(FRONT_DESK, "Sales User")
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": FRONT_DESK,
				"reference_type": "CRM Lead",
				"reference_name": self.anna.name,
				"description": "Anna",
			}
		).insert(ignore_permissions=True)
		casella = self.casella()
		prima = self.arriva("anna.rossi@ingresso.test", casella=casella, subject="Posso spostare?")
		avvisi = frappe.get_all(
			"CRM Notification",
			filters={"to_user": FRONT_DESK, "type": "Email"},
			fields=["sentence", "count", "message", "notification_type_doc", "reference_name"],
		)
		self.assertEqual(len(avvisi), 1)
		self.assertEqual(
			(
				avvisi[0].sentence,
				avvisi[0].message,
				avvisi[0].notification_type_doc,
				avvisi[0].reference_name,
			),
			(R.EMAIL, "Posso spostare?", prima.name, self.anna.name),
		)
		self.arriva("anna.rossi@ingresso.test", casella=casella, subject="Anche giovedì")
		avvisi = frappe.get_all(
			"CRM Notification",
			filters={"to_user": FRONT_DESK, "type": "Email"},
			fields=["sentence", "count"],
		)
		self.assertEqual([(a.sentence, a.count) for a in avvisi], [(R.EMAIL_MOLTI, 2)])


class LaPatch(IngressoCase):
	def test_le_caselle_smettono_di_fare_persone_a_ogni_email(self):
		from crm.patches.v1_0 import emails_reach_their_person as patch
		from crm.permissions import utenti

		vecchia = self.casella(nuove_persone=0, nome="Vecchia segreteria")
		vecchia.append("imap_folder", {"folder_name": "INBOX", "append_to": "CRM Lead"})
		vecchia.flags.ignore_validate = True
		vecchia.save(ignore_permissions=True)
		make_user(FRONT_DESK, "Sales User")
		utenti.assegna_livelli(FRONT_DESK, ["segreteria"])
		frappe.db.set_value("User", FRONT_DESK, "thread_notify", 1)

		patch.execute()

		vecchia.reload()
		self.assertEqual([(f.folder_name, f.append_to) for f in vecchia.imap_folder], [("INBOX", None)])
		# who wrote the first time became a person: it still does, through DottorCloud
		self.assertEqual(vecchia.create_lead_from_incoming_email, 1)
		# the panel tells them, not the framework's copy in their own mailbox
		self.assertEqual(frappe.db.get_value("User", FRONT_DESK, "thread_notify"), 0)
