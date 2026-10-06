# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Notifications by email too, on a real site.

Bruno is mentioned: still unread after five minutes, it reaches his email, once,
with a button that opens Laura in DottorCloud. Read in the panel before, it never
goes; a minute old, it waits. Two at once are one email that lists them. A
WhatsApp message stays in the panel, as Bruno did not ask for messages by email;
once he does, a conversation goes once while it is unread, not at every message.
Each person chooses for themselves.
"""

import json

import frappe
from frappe.utils import add_to_date, now_datetime

from crm.notifiche import api, posta
from crm.notifiche import regole as R
from crm.notifiche.avvisi import avvisa
from crm.notifiche.tests.test_api import ANNA, BRUNO, NOTIFICA, NotificheCase


class PostaCase(NotificheCase):
	def setUp(self):
		super().setUp()
		# the emails in Bruno's language, whatever the site's
		frappe.db.set_value("User", BRUNO, "language", "en")
		frappe.clear_document_cache("User", BRUNO)
		frappe.defaults.clear_user_default(posta.CHIAVE, BRUNO)
		frappe.db.delete("Email Queue", {"message": ("like", f"%{BRUNO}%")})

	def menziona(self):
		return avvisa(
			BRUNO,
			"Mention",
			R.MENZIONE,
			["Anna", self.laura.lead_name],
			da=ANNA,
			riguarda=("CRM Lead", self.laura.name),
			oggetto=("Comment", frappe.generate_hash(length=10)),
			messaggio="<p>Puoi richiamarla?</p>",
		)

	def invecchia(self, nome, minuti=10):
		frappe.db.set_value(
			NOTIFICA, nome, "creation", add_to_date(now_datetime(), minutes=-minuti), update_modified=False
		)

	def email_a_bruno(self):
		return frappe.get_all(
			"Email Queue Recipient", filters={"recipient": BRUNO}, pluck="parent", order_by="creation asc"
		)


class LeScelte(PostaCase):
	def test_quelle_di_solito(self):
		self.come(BRUNO)
		gruppi = {g["key"]: g["on"] for g in posta.get_email_preferences()["groups"]}
		self.assertTrue(gruppi["mentions"])
		self.assertTrue(gruppi["assignments"])
		self.assertFalse(gruppi["messages"])
		self.assertFalse(gruppi["agenda"])

	def test_solo_quelle_che_riceve(self):
		# the desk: the day's question, not invoicing's alerts
		self.come(BRUNO)
		gruppi = [g["key"] for g in posta.get_email_preferences()["groups"]]
		self.assertIn("agenda", gruppi)
		self.assertIn("messages", gruppi)
		self.assertNotIn("invoicing", gruppi)
		# a practitioner: neither
		self.come(ANNA)
		gruppi = [g["key"] for g in posta.get_email_preferences()["groups"]]
		self.assertNotIn("agenda", gruppi)
		self.assertNotIn("invoicing", gruppi)
		self.assertIn("mentions", gruppi)

	def test_ognuno_le_sue(self):
		self.come(BRUNO)
		posta.save_email_preferences({"messages": True, "mentions": False, "something": True})
		self.assertEqual(posta.preferenze(BRUNO), {"messages": True, "mentions": False})
		self.come(ANNA)
		self.assertEqual(posta.preferenze(ANNA), {})

	def test_la_notifica_sa_se_andra(self):
		self.assertEqual(frappe.db.get_value(NOTIFICA, self.menziona(), "email_due"), 1)
		whatsapp = self.whatsapp("Buongiorno")
		self.assertEqual(frappe.db.get_value(NOTIFICA, whatsapp, "email_due"), 0)


class Quando(PostaCase):
	def test_non_letta_dopo_cinque_minuti(self):
		nome = self.menziona()
		self.invecchia(nome)
		posta.manda_le_email()
		code = self.email_a_bruno()
		self.assertEqual(len(code), 1)
		messaggio = frappe.db.get_value("Email Queue", code[0], "message")
		self.assertIn("mentioned you in a comment on", messaggio)
		self.assertIn(f"/crm/persone/{self.laura.name}", messaggio)
		self.assertNotIn("/app/", messaggio)
		self.assertEqual(frappe.db.get_value(NOTIFICA, nome, "email_due"), 0)
		self.assertTrue(frappe.db.get_value(NOTIFICA, nome, "emailed_on"))
		# and only once
		posta.manda_le_email()
		self.assertEqual(len(self.email_a_bruno()), 1)

	def test_letta_prima_non_va(self):
		nome = self.menziona()
		self.invecchia(nome)
		self.come(BRUNO)
		api.mark_as_read([nome])
		frappe.set_user("Administrator")
		posta.manda_le_email()
		self.assertEqual(self.email_a_bruno(), [])

	def test_appena_arrivata_aspetta(self):
		self.menziona()
		posta.manda_le_email()
		self.assertEqual(self.email_a_bruno(), [])

	def test_due_insieme_una_email(self):
		for nome in (self.menziona(), self.menziona()):
			self.invecchia(nome)
		posta.manda_le_email()
		code = self.email_a_bruno()
		self.assertEqual(len(code), 1)
		self.assertIn("You have 2 notifications in", frappe.db.get_value("Email Queue", code[0], "message"))


class UnaConversazione(PostaCase):
	def test_una_volta_finche_non_e_letta(self):
		frappe.defaults.set_user_default(posta.CHIAVE, json.dumps({"messages": True}), user=BRUNO)
		primo = self.whatsapp("Buongiorno")
		self.invecchia(primo)
		posta.manda_le_email()
		self.assertEqual(len(self.email_a_bruno()), 1)
		# the next message adds to the unread one, and does not go again
		secondo = self.whatsapp("Ci sono?")
		self.assertEqual(frappe.db.get_value(NOTIFICA, secondo, "email_due"), 0)
		self.invecchia(secondo)
		posta.manda_le_email()
		self.assertEqual(len(self.email_a_bruno()), 1)


class DoveApre(PostaCase):
	def test_gli_indirizzi(self):
		self.assertTrue(
			posta.indirizzo({"name": "Lead", "params": {"leadId": "L-1"}, "hash": "#c1"}).endswith(
				"/crm/persone/L-1#c1"
			)
		)
		self.assertTrue(
			posta.indirizzo({"name": "Deal", "params": {"dealId": "D-1"}}).endswith("/crm/deals/D-1")
		)
		self.assertTrue(posta.indirizzo({"name": "Today"}).endswith("/crm/accoglienza"))
		self.assertTrue(posta.indirizzo({"name": "Invoices"}).endswith("/crm/fatture"))
		self.assertTrue(posta.indirizzo(None).endswith("/crm/notifications"))
