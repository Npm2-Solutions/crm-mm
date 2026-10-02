# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Each person's own mailbox, on a real site (doc 51, second part).

Giulia of the front desk connects her mailbox from her own page: it is hers, it makes
nobody a person, and she writes from it first. She also chooses which of the
centre's mailboxes she writes from - a list the framework keeps for the
administrator - but never somebody else's own. The centre's page does not show it.
Disconnected, its password goes and what it brought stays; connected again with
another address, it is the same mailbox. With Google she signs in on Google's page,
and the mailbox waits until the access comes back.

From her mailbox only the centre's emails are taken: the answers to what was written
from DottorCloud and what the people the centre knows write. She is told of them,
whoever follows the person or not.
"""

from unittest.mock import patch

import frappe
from frappe.email.doctype.email_account.email_account import EmailAccount

from crm.posta import personale
from crm.tests.test_documenti_del_core import FRONT_DESK, MANAGER, CoreTestCase


class PersonaleCase(CoreTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.centro = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Segreteria Aurora",
				"email_id": "segreteria@aurora.test",
				"enable_incoming": 1,
				"enable_outgoing": 1,
				"email_server": "imaps.aruba.it",
				"smtp_server": "smtps.aruba.it",
				"imap_folder": [{"folder_name": "INBOX"}],
			}
		)
		self.centro.flags.ignore_validate = True
		self.centro.insert(ignore_permissions=True)

	def collega(self, utente=FRONT_DESK, indirizzo="giulia@aurora.test"):
		frappe.set_user(utente)
		stato = personale.connect_my_mailbox(
			{"provider": "aruba", "email_id": indirizzo, "password": "segreta"}
		)
		frappe.set_user("Administrator")
		return stato


class LaCasellaDiOgnuno(PersonaleCase):
	def test_e_sua_e_scrive_da_li(self):
		stato = self.collega()
		self.assertEqual(
			(stato["mailbox"]["email_id"], stato["mailbox"]["provider"], stato["mailbox"]["connected"]),
			("giulia@aurora.test", "aruba", True),
		)
		doc = frappe.get_doc("Email Account", "giulia@aurora.test")
		self.assertEqual(
			(doc.crm_owner, doc.create_lead_from_incoming_email, doc.create_contact, doc.default_outgoing),
			(FRONT_DESK, 0, 0, 0),
		)
		self.assertEqual((doc.email_server, doc.smtp_server), ("imaps.aruba.it", "smtps.aruba.it"))
		# written where the framework would ask for the administrator
		self.assertEqual(
			frappe.get_all("User Email", {"parent": FRONT_DESK}, pluck="email_account"),
			["giulia@aurora.test"],
		)
		frappe.set_user(FRONT_DESK)
		self.assertEqual([s["email_id"] for s in personale.get_my_senders()], ["giulia@aurora.test"])

	def test_da_quali_caselle_del_centro_scrive(self):
		self.collega()
		self.collega(utente=MANAGER, indirizzo="direzione@aurora.test")
		frappe.set_user(FRONT_DESK)
		stato = personale.set_my_senders(["Segreteria Aurora", "direzione@aurora.test"])
		# the centre's, never somebody else's own
		self.assertEqual(stato["senders"], ["Segreteria Aurora"])
		self.assertNotIn("direzione@aurora.test", [c["name"] for c in stato["centre"]])
		# her own first
		self.assertEqual(
			[s["email_account"] for s in personale.get_my_senders()],
			["giulia@aurora.test", "Segreteria Aurora"],
		)

	def test_la_pagina_del_centro_non_la_mostra(self):
		from crm.api import settings

		self.collega()
		frappe.set_user(MANAGER)
		self.assertNotIn("giulia@aurora.test", [a.name for a in settings.get_email_accounts()])
		self.assertNotIn("giulia@aurora.test", [a.name for a in settings.list_email_accounts(outgoing=1)])
		# nor changes it
		with self.assertRaises(frappe.PermissionError):
			settings.update_email_account("giulia@aurora.test", {"enable_outgoing": 0})

	def test_una_casella_del_centro_non_diventa_di_nessuno(self):
		frappe.set_user(FRONT_DESK)
		with self.assertRaises(frappe.ValidationError):
			personale.connect_my_mailbox(
				{"provider": "aruba", "email_id": "segreteria@aurora.test", "password": "x"}
			)
		with self.assertRaises(frappe.ValidationError):
			personale.connect_my_mailbox({"provider": "aruba", "email_id": "giulia@aurora.test"})

	def test_scollegata_e_ricollegata(self):
		self.collega()
		frappe.set_user(FRONT_DESK)
		stato = personale.disconnect_my_mailbox()
		self.assertFalse(stato["mailbox"]["connected"])
		self.assertEqual(personale.get_my_senders(), [])
		frappe.set_user("Administrator")
		doc = frappe.get_doc("Email Account", "giulia@aurora.test")
		self.assertFalse(doc.get_password("password", raise_exception=False))
		# connected again with another address: the same mailbox, renamed
		self.collega(indirizzo="giulia.rossi@aurora.test")
		self.assertFalse(frappe.db.exists("Email Account", "giulia@aurora.test"))
		self.assertEqual(
			frappe.db.get_value("Email Account", "giulia.rossi@aurora.test", "crm_owner"), FRONT_DESK
		)


class AccediConGoogle(PersonaleCase):
	def setUp(self):
		super().setUp()
		# whatever the site had, the test's own app is the only one
		for app in frappe.get_all("Connected App", fields=["name", "authorization_uri"]):
			if any(segno in (app.authorization_uri or "") for segno in ("google.com", "microsoftonline.com")):
				frappe.delete_doc("Connected App", app.name, force=True, ignore_permissions=True)
		self.app = frappe.get_doc(
			{
				"doctype": "Connected App",
				"provider_name": "Google",
				"client_id": "id-di-prova",
				"client_secret": "segreto",
				"authorization_uri": "https://accounts.google.com/o/oauth2/v2/auth",
				"token_uri": "https://oauth2.googleapis.com/token",
				"scopes": [{"scope": "https://mail.google.com/"}],
			}
		).insert(ignore_permissions=True)

	def test_dalla_pagina_di_google_e_ritorno(self):
		# with a password first, then signing in: the password goes
		self.collega(indirizzo="giulia@gmail.test")
		frappe.set_user(FRONT_DESK)
		self.assertEqual(personale.get_my_email()["sign_in"], {"google": True, "microsoft": False})
		# the framework commits the state it sends Google: not in a test
		with patch.object(frappe.db, "commit"):
			url = personale.start_sign_in("google", "giulia@gmail.test")
		self.assertTrue(url.startswith("https://accounts.google.com/"))
		self.assertIn("id-di-prova", url)
		stato = personale.get_my_email()
		self.assertEqual((stato["mailbox"]["signed_in_with"], stato["mailbox"]["waiting"]), ("google", True))
		self.assertFalse(stato["mailbox"]["connected"])
		# back without the access: still waiting
		self.assertTrue(personale.finish_sign_in()["mailbox"]["waiting"])
		with patch("frappe.integrations.doctype.connected_app.connected_app.has_token", return_value=True):
			stato = personale.finish_sign_in()
		self.assertTrue(stato["mailbox"]["connected"])
		frappe.set_user("Administrator")
		doc = frappe.get_doc("Email Account", "giulia@gmail.test")
		self.assertEqual(
			(doc.auth_method, doc.connected_app, doc.connected_user, doc.email_server),
			("OAuth", self.app.name, FRONT_DESK, "imap.gmail.com"),
		)
		self.assertFalse(doc.get_password("password", raise_exception=False))

	def test_senza_l_app_dell_agenzia_no(self):
		frappe.set_user(FRONT_DESK)
		with self.assertRaises(frappe.ValidationError):
			personale.start_sign_in("microsoft", "giulia@outlook.test")


class _Email:
	"""An email as the framework hands it over, before it is stored."""

	def __init__(self, mittente, risposta=None):
		self.from_email = mittente
		self._risposta = risposta

	def parent_communication(self):
		return self._risposta


class SoloQuelloDelCentro(PersonaleCase):
	def setUp(self):
		super().setUp()
		self.anna = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Anna",
				"last_name": "Rossi",
				"email": "anna@personale.test",
			}
		).insert(ignore_permissions=True)

	def test_dalla_casella_di_giulia_solo_risposte_e_persone_note(self):
		self.collega()
		arrivate = [
			_Email("anna@personale.test"),
			_Email("amico@vacanze.test"),
			_Email("x@y.test", risposta="C1"),
		]
		casella = frappe.get_doc("Email Account", "giulia@aurora.test")
		with patch.object(EmailAccount, "get_inbound_mails", return_value=arrivate):
			tenute = casella.get_inbound_mails()
		self.assertEqual([e.from_email for e in tenute], ["anna@personale.test", "x@y.test"])
		# the centre's mailbox is read whole
		with patch.object(EmailAccount, "get_inbound_mails", return_value=arrivate):
			self.assertEqual(len(frappe.get_doc("Email Account", self.centro.name).get_inbound_mails()), 3)

	def test_giulia_lo_sa_anche_se_anna_non_e_sua(self):
		self.collega()
		frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "Domani",
				"sender": "anna@personale.test",
				"email_account": "giulia@aurora.test",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(
			frappe.db.exists(
				"CRM Notification",
				{"to_user": FRONT_DESK, "type": "Email", "reference_name": self.anna.name},
			)
		)
		# nobody becomes a person from her mailbox
		frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Received",
				"subject": "Ciao",
				"sender": "nuovo@ingresso.test",
				"email_account": "giulia@aurora.test",
			}
		).insert(ignore_permissions=True)
		self.assertFalse(frappe.db.exists("CRM Lead", {"email": "nuovo@ingresso.test"}))
