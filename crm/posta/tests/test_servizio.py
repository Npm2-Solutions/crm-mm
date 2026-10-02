# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""DottorCloud's own emails, through the agency's sending service, on a real site.

The agency writes the service in the configuration: the site makes its account,
the one emails leave from, and takes the place of the centre's mailbox for that. A
reminder comes from Centro Aurora on the service's address - the envelope too - and
its answers go to the address the centre chose, else its mailbox; somebody of the
centre writing without a mailbox of their own shows "Anna Bianchi · Centro Aurora".
A service on port 465 speaks TLS from the start, one without a password needs no
login. Without the configuration the account stops, and the centre's mailbox sends
again. The settings page is the manager's; syncing it now, the agency's.
"""

import email
from email.header import decode_header, make_header
from unittest.mock import patch

import frappe

from crm.posta import servizio
from crm.tests.test_documenti_del_core import AGENCY, FRONT_DESK, MANAGER, CoreTestCase

CONF = {
	"server": "smtp.servizio.test",
	"porta": 587,
	"utente": "AKIAUTENTE",
	"password": "segreta",
	"mittente": "notifiche@posta.dottorcloud.test",
}


def _intestazione(messaggio: str, nome: str) -> str:
	valore = email.message_from_string(messaggio).get(nome) or ""
	return str(make_header(decode_header(valore)))


class ServizioCase(CoreTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		# whatever the site had, each test starts without the service
		if frappe.db.exists("Email Account", servizio.ACCOUNT):
			frappe.delete_doc("Email Account", servizio.ACCOUNT, force=True, ignore_permissions=True)
		self.configura(CONF)
		frappe.db.set_single_value("FCRM Settings", "brand_name", "Centro Aurora")
		frappe.db.set_single_value("FCRM Settings", "reply_to_email", None)
		# the centre's own mailbox, which sent everything until now
		self.casella = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Segreteria Aurora",
				"email_id": "segreteria@aurora.test",
				"enable_incoming": 1,
				"default_incoming": 1,
				"enable_outgoing": 1,
				"default_outgoing": 1,
				"email_server": "imaps.aruba.it",
				"smtp_server": "smtps.aruba.it",
				"password": "x",
				"imap_folder": [{"folder_name": "INBOX"}],
			}
		)
		self.casella.flags.ignore_validate = True
		self.casella.insert(ignore_permissions=True)

	def configura(self, conf):
		patcher = patch.dict(frappe.conf, {servizio.CONF: conf})
		patcher.start()
		self.addCleanup(patcher.stop)

	def senza_configurazione(self):
		patcher = patch.dict(frappe.conf, {})
		patcher.start()
		frappe.conf.pop(servizio.CONF, None)
		self.addCleanup(patcher.stop)

	def manda(self, **altro):
		# the outgoing account is remembered for the request: a test is a new one
		frappe.local.outgoing_email_account = {}
		frappe.sendmail(
			recipients=["anna.rossi@example.com"],
			subject="Il tuo appuntamento",
			message="<p>Domani alle 10.</p>",
			now=False,
			**altro,
		)
		return frappe.get_last_doc("Email Queue")


class IlServizioDiInvio(ServizioCase):
	def test_l_account_segue_la_configurazione(self):
		self.assertEqual(servizio.assicura(), servizio.ACCOUNT)
		doc = frappe.get_doc("Email Account", servizio.ACCOUNT)
		self.assertEqual(
			(doc.email_id, doc.smtp_server, doc.smtp_port, doc.use_tls, doc.use_ssl_for_outgoing),
			(CONF["mittente"], CONF["server"], "587", 1, 0),
		)
		self.assertEqual((doc.login_id_is_different, doc.login_id), (1, CONF["utente"]))
		self.assertEqual(doc.get_password("password"), "segreta")
		self.assertTrue(doc.default_outgoing and doc.enable_outgoing and not doc.enable_incoming)
		self.assertTrue(servizio.attivo())
		# the centre's mailbox is no longer the one DottorCloud's emails leave from
		self.assertFalse(frappe.db.get_value("Email Account", self.casella.name, "default_outgoing"))
		# a second time, nothing to change and nothing saved
		prima = frappe.db.get_value("Email Account", servizio.ACCOUNT, "modified")
		servizio.assicura()
		self.assertEqual(frappe.db.get_value("Email Account", servizio.ACCOUNT, "modified"), prima)

	def test_porta_465_e_senza_password(self):
		self.configura({"server": "relay.test", "porta": 465, "mittente": "invio@relay.test"})
		servizio.assicura()
		doc = frappe.get_doc("Email Account", servizio.ACCOUNT)
		self.assertEqual((doc.use_ssl_for_outgoing, doc.use_tls), (1, 0))
		self.assertEqual((doc.no_smtp_authentication, doc.login_id_is_different), (1, 0))

	def test_una_configurazione_a_meta_non_e_un_servizio(self):
		self.configura({"server": "relay.test"})
		self.assertIsNone(servizio.configurazione())
		self.configura({"server": "relay.test", "mittente": "non-un-indirizzo"})
		self.assertIsNone(servizio.configurazione())

	def test_un_promemoria_viene_dal_centro_e_le_risposte_vanno_al_centro(self):
		servizio.assicura()
		coda = self.manda()
		self.assertEqual(coda.email_account, servizio.ACCOUNT)
		# the envelope is the service's: it accepts nothing else
		self.assertEqual(coda.sender, f"Centro Aurora <{CONF['mittente']}>")
		self.assertEqual(_intestazione(coda.message, "From"), f"Centro Aurora <{CONF['mittente']}>")
		# no address chosen: the mailbox where the centre reads its answers
		self.assertEqual(_intestazione(coda.message, "Reply-To"), "Centro Aurora <segreteria@aurora.test>")
		frappe.db.set_single_value("FCRM Settings", "reply_to_email", "info@aurora.test")
		coda = self.manda()
		self.assertEqual(_intestazione(coda.message, "Reply-To"), "Centro Aurora <info@aurora.test>")

	def test_chi_scrive_senza_casella_sua_scrive_a_nome_del_centro(self):
		servizio.assicura()
		coda = self.manda(sender="Anna Bianchi <anna.bianchi@personale.test>")
		self.assertEqual(
			_intestazione(coda.message, "From"), f"Anna Bianchi · Centro Aurora <{CONF['mittente']}>"
		)
		# the answer goes back to who wrote
		self.assertIn("anna.bianchi@personale.test", _intestazione(coda.message, "Reply-To"))

	def test_senza_configurazione_si_ferma_e_torna_la_casella_del_centro(self):
		servizio.assicura()
		self.senza_configurazione()
		servizio.assicura()
		self.assertFalse(servizio.attivo())
		self.assertEqual(frappe.db.get_value("Email Account", self.casella.name, "default_outgoing"), 1)
		coda = self.manda()
		self.assertEqual(coda.email_account, self.casella.name)

	def test_un_servizio_che_non_risponde_non_disfa_il_resto(self):
		# what the migrate wrote before it, in the same transaction
		frappe.db.set_single_value("FCRM Settings", "reply_to_email", "info@aurora.test")
		with patch(
			"frappe.email.doctype.email_account.email_account.EmailAccount.validate",
			side_effect=Exception("timed out"),
		):
			self.assertIsNone(servizio.assicura())
		self.assertFalse(frappe.db.exists("Email Account", servizio.ACCOUNT))
		self.assertEqual(frappe.db.get_single_value("FCRM Settings", "reply_to_email"), "info@aurora.test")
		# and the centre's mailbox still sends
		self.assertEqual(frappe.db.get_value("Email Account", self.casella.name, "default_outgoing"), 1)

	def test_il_nome_mostrato(self):
		self.assertEqual(servizio.mostrato(None, "Centro Aurora"), "Centro Aurora")
		self.assertEqual(servizio.mostrato(servizio.ACCOUNT, "Centro Aurora"), "Centro Aurora")
		self.assertEqual(servizio.mostrato("Anna Bianchi", "Centro Aurora"), "Anna Bianchi · Centro Aurora")
		# who already says the centre is not said twice
		self.assertEqual(
			servizio.mostrato("Segreteria Centro Aurora", "Centro Aurora"), "Segreteria Centro Aurora"
		)


class LaPagina(ServizioCase):
	def test_il_manager_la_legge_e_sceglie_dove_arrivano_le_risposte(self):
		servizio.assicura()
		frappe.set_user(MANAGER)
		stato = servizio.get_sending_service()
		self.assertTrue(stato["active"])
		self.assertEqual(stato["sender"], f"Centro Aurora <{CONF['mittente']}>")
		self.assertEqual(stato["reply_to"], "segreteria@aurora.test")
		self.assertNotIn("server", stato)
		with self.assertRaises(frappe.ValidationError):
			servizio.set_reply_address("non-un-indirizzo")
		self.assertEqual(servizio.set_reply_address("info@aurora.test")["reply_to"], "info@aurora.test")
		# the agency's own
		with self.assertRaises(frappe.PermissionError):
			servizio.sync_sending_service()

	def test_la_segreteria_no_l_agenzia_si(self):
		frappe.set_user(FRONT_DESK)
		with self.assertRaises(frappe.PermissionError):
			servizio.get_sending_service()
		frappe.set_user(AGENCY)
		self.assertEqual(servizio.sync_sending_service()["server"], "smtp.servizio.test:587")

	def test_le_caselle_del_centro_non_lo_mostrano(self):
		from crm.api import settings

		servizio.assicura()
		frappe.set_user(MANAGER)
		self.assertNotIn(servizio.ACCOUNT, [a.name for a in settings.get_email_accounts()])
		self.assertNotIn(servizio.ACCOUNT, [a.name for a in settings.list_email_accounts(outgoing=1)])
		with self.assertRaises(frappe.PermissionError):
			settings.update_email_account(servizio.ACCOUNT, {"enable_outgoing": 0})
		# while the service sends, no mailbox of the centre is the default for it
		settings.update_email_account(self.casella.name, {"default_outgoing": 1})
		self.assertEqual(frappe.db.get_value("Email Account", self.casella.name, "default_outgoing"), 0)

	def test_il_manager_aggiunge_una_casella_che_riceve(self):
		from crm.api import settings

		servizio.assicura()
		frappe.set_user(MANAGER)
		nome = settings.create_email_account(
			{
				"provider": "aruba",
				"email_id": "accoglienza@aurora.test",
				"email_account_name": "Accoglienza Aurora",
				"password": "segreta",
				"enable_incoming": 1,
				"default_outgoing": 1,
				"create_lead_from_incoming_email": 1,
			}
		)
		frappe.set_user("Administrator")
		doc = frappe.get_doc("Email Account", nome)
		self.assertEqual((doc.email_server, doc.smtp_server), ("imaps.aruba.it", "smtps.aruba.it"))
		# the inbox is read, and DottorCloud finds who wrote: no document to file into
		self.assertEqual([(f.folder_name, f.append_to) for f in doc.imap_folder], [("INBOX", None)])
		self.assertEqual((doc.create_lead_from_incoming_email, doc.default_outgoing), (1, 0))
