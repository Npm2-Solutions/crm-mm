# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The notifications on a real site.

Anna mentions Bruno in a comment on Laura: Bruno reads it in his panel, in his
language, with the first words of the comment, and it opens Laura's page on that
comment; the comment saved again mentions nobody again. Laura writes three times
on WhatsApp: Bruno, who follows her, reads one notification for three messages,
opening on the last one; once he has read it, the next message is a new one.
Anna gives Bruno a task: it opens Laura's tasks while it is his. The day's
appointments without an outcome open the desk's day, an invoicing alert the
invoices. Laura deleted: what was about her opens nothing.

Bruno reads one, all, none with an empty list, one again; Carlo, who only reads,
reads his own too. Six months on, they are gone.
"""

from unittest.mock import patch

import frappe
from frappe.desk.form import assign_to
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.api import comment as commenti
from crm.fcrm.doctype.crm_notification.crm_notification import CRMNotification
from crm.notifiche import api
from crm.notifiche import regole as R
from crm.notifiche.avvisi import avvisa
from crm.permissions import documenti, livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

ANNA = "notifiche.anna@example.com"
BRUNO = "notifiche.bruno@example.com"
CARLO = "notifiche.carlo@example.com"
NOTIFICA = "CRM Notification"


class NotificheCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		utenti.sincronizza()
		for utente, livelli_ in (
			(ANNA, ["operatore"]),
			(BRUNO, ["segreteria"]),
			(CARLO, ["segreteria", "sola_lettura"]),
		):
			make_user(utente)
			utenti.assegna_livelli(utente, livelli_)
		frappe.db.set_value(
			"User", ANNA, {"first_name": "Anna", "last_name": "Notifiche", "full_name": "Anna Notifiche"}
		)
		frappe.clear_document_cache("User", ANNA)
		livelli.dimentica_cache()
		frappe.db.delete(NOTIFICA, {"to_user": ("in", [ANNA, BRUNO, CARLO])})
		self.laura = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Laura", "last_name": "Notifica"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.local.lang = "en"
		frappe.db.rollback()
		livelli.dimentica_cache()

	def come(self, utente, lingua="en"):
		frappe.set_user(utente)
		frappe.local.lang = lingua
		livelli.dimentica_cache()

	def pannello(self, **parametri):
		return api.get_notifications(**parametri)

	def whatsapp(self, testo):
		return avvisa(
			BRUNO,
			"WhatsApp",
			R.WHATSAPP,
			[self.laura.lead_name],
			frase_molti=R.WHATSAPP_MOLTI,
			riguarda=("CRM Lead", self.laura.name),
			oggetto=("WhatsApp Message", frappe.generate_hash(length=10)),
			messaggio=testo,
		)


class UnaMenzione(NotificheCase):
	def menziona(self, testo="puoi richiamarla?"):
		self.come(ANNA)
		commento = frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "CRM Lead",
				"reference_name": self.laura.name,
				"content": (
					f'<p><span class="mention" data-type="mention" data-id="{BRUNO}" '
					f'data-label="Bruno">@Bruno</span>, {testo}</p>'
				),
			}
		).insert(ignore_permissions=True)
		frappe.set_user("Administrator")
		return commento

	def test_bruno_la_legge_nella_sua_lingua(self):
		commento = self.menziona()
		self.come(BRUNO, "it")
		pannello = self.pannello()
		self.assertEqual(pannello["unread"], 1)
		riga = pannello["rows"][0]
		self.assertEqual(riga["kind"], "mention")
		self.assertEqual(
			riga["text"], "<b>Anna Notifiche</b> ti ha menzionato in un commento su <b>Laura Notifica</b>"
		)
		self.assertEqual(riga["excerpt"], "@Bruno, puoi richiamarla?")
		self.assertEqual(riga["from"]["name"], ANNA)
		self.assertEqual(
			riga["route"],
			{"name": "Lead", "params": {"leadId": self.laura.name}, "hash": "#" + commento.name},
		)
		# and in English, for whoever reads DottorCloud in English
		self.come(BRUNO, "en")
		self.assertIn("mentioned you in a comment on", self.pannello()["rows"][0]["text"])

	def test_salvato_di_nuovo_non_menziona_ancora(self):
		commento = self.menziona()
		self.come(BRUNO)
		api.mark_as_read()
		frappe.set_user("Administrator")
		commento.content = commento.content.replace("richiamarla", "richiamarla oggi")
		commento.save(ignore_permissions=True)
		commenti.notify_mentions(commento)
		self.assertEqual(frappe.db.count(NOTIFICA, {"to_user": BRUNO, "type": "Mention"}), 1)


class UnaConversazione(NotificheCase):
	def test_tre_messaggi_una_notifica(self):
		self.whatsapp("Buongiorno")
		self.whatsapp("Posso spostare?")
		ultimo = self.whatsapp("Grazie")
		self.assertEqual(frappe.db.count(NOTIFICA, {"to_user": BRUNO, "type": "WhatsApp"}), 1)
		self.come(BRUNO)
		riga = self.pannello()["rows"][0]
		self.assertEqual(riga["name"], ultimo)
		self.assertEqual(riga["count"], 3)
		self.assertEqual(riga["text"], "You received <b>3</b> WhatsApp messages from <b>Laura Notifica</b>")
		self.assertEqual(riga["excerpt"], "Grazie")
		messaggio = frappe.db.get_value(NOTIFICA, ultimo, "notification_type_doc")
		self.assertEqual(riga["route"]["hash"], "#" + messaggio)

	def test_letta_il_messaggio_dopo_e_nuovo(self):
		self.whatsapp("Buongiorno")
		self.come(BRUNO)
		api.mark_as_read()
		frappe.set_user("Administrator")
		self.whatsapp("Ci sono ancora?")
		self.assertEqual(frappe.db.count(NOTIFICA, {"to_user": BRUNO, "type": "WhatsApp"}), 2)
		self.come(BRUNO)
		self.assertEqual(self.pannello()["rows"][0]["count"], 1)

	def test_le_parole_solo_a_chi_legge_le_conversazioni(self):
		self.whatsapp("Ho la febbre")
		self.come(BRUNO)
		with patch("crm.notifiche.api._legge_le_conversazioni", return_value=False):
			self.assertEqual(self.pannello()["rows"][0]["excerpt"], "")


class DoveSiApre(NotificheCase):
	def test_un_attivita_apre_le_attivita_finche_e_sua(self):
		compito = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": "Richiamare Laura",
				"reference_doctype": "CRM Lead",
				"reference_docname": self.laura.name,
			}
		).insert(ignore_permissions=True)
		# Laura is Anna's: her tasks are Anna's to give
		assign_to.add({"doctype": "CRM Lead", "name": self.laura.name, "assign_to": [ANNA]})
		self.come(ANNA)
		assign_to.add({"doctype": "CRM Task", "name": compito.name, "assign_to": [BRUNO]})
		self.come(BRUNO, "it")
		riga = self.pannello()["rows"][0]
		self.assertEqual(riga["kind"], "task")
		self.assertEqual(
			riga["text"], "<b>Anna Notifiche</b> ti ha assegnato l'attività <b>Richiamare Laura</b>"
		)
		self.assertEqual(riga["route"]["hash"], "#tasks")
		# taken back, the notification of the task no longer opens the tasks
		self.come(ANNA)
		assign_to.remove("CRM Task", compito.name, BRUNO)
		self.come(BRUNO)
		righe = {r["kind"]: r for r in self.pannello()["rows"]}
		self.assertEqual(righe["task_removed"]["route"]["hash"], "")
		self.assertEqual(righe["task"]["route"]["hash"], "")

	def test_l_agenda_e_la_fatturazione(self):
		avvisa(BRUNO, "Agenda", R.ESITI_OGGI, [3], oggetto=("CRM Appointment", "APP-1"))
		avvisa(
			BRUNO,
			"Invoicing",
			testo="Invoice 12 was rejected - Centro & figli",
			oggetto=("CRM Invoicing Company", "Centro"),
			messaggio="It counts as not issued.",
		)
		self.come(BRUNO)
		righe = {r["kind"]: r for r in self.pannello()["rows"]}
		self.assertEqual(righe["agenda"]["route"], {"name": "Today"})
		self.assertEqual(
			righe["agenda"]["text"], "<b>3</b> appointments today have no outcome: did they come?"
		)
		self.assertEqual(righe["invoicing"]["route"], {"name": "Invoices"})
		self.assertEqual(righe["invoicing"]["text"], "Invoice 12 was rejected - Centro &amp; figli")
		self.assertEqual(righe["invoicing"]["excerpt"], "It counts as not issued.")
		self.assertIsNone(righe["agenda"]["from"])

	def test_una_persona_tolta_non_apre_niente(self):
		self.whatsapp("Buongiorno")
		frappe.db.delete("CRM Lead", {"name": self.laura.name})
		self.come(BRUNO)
		self.assertIsNone(self.pannello()["rows"][0]["route"])

	def test_scritte_prima_si_leggono_allo_stesso_modo(self):
		frappe.get_doc(
			{
				"doctype": NOTIFICA,
				"to_user": BRUNO,
				"type": "Mention",
				"notification_text": '<div class="mb-2 text-ink-gray-5"><span class="font-medium '
				'text-ink-gray-9">Anna</span> mentioned you</div>',
			}
		).insert(ignore_permissions=True)
		self.come(BRUNO)
		self.assertEqual(self.pannello()["rows"][0]["text"], "<b>Anna</b> mentioned you")


class LeggerleTutte(NotificheCase):
	def setUp(self):
		super().setUp()
		for _ in range(3):
			avvisa(BRUNO, "Automation", testo=frappe.generate_hash(length=8))

	def test_una_tutte_nessuna_e_di_nuovo(self):
		self.come(BRUNO)
		righe = self.pannello()["rows"]
		self.assertEqual(api.mark_as_read([righe[0]["name"]])["unread"], 2)
		# an empty list is no notification, never all of them
		self.assertEqual(api.mark_as_read([])["unread"], 2)
		self.assertEqual(api.mark_as_read()["unread"], 0)
		self.assertEqual(api.mark_as_unread([righe[1]["name"]])["unread"], 1)
		self.assertEqual([r["name"] for r in self.pannello(unread=1)["rows"]], [righe[1]["name"]])

	def test_solo_le_proprie(self):
		avvisa(ANNA, "Automation", testo="per Anna")
		self.come(BRUNO)
		nome_di_anna = frappe.get_all(NOTIFICA, filters={"to_user": ANNA}, pluck="name")[0]
		api.mark_as_read([nome_di_anna])
		self.assertEqual(frappe.db.get_value(NOTIFICA, nome_di_anna, "read"), 0)

	def test_una_pagina_alla_volta(self):
		self.come(BRUNO)
		pagina = self.pannello(limit=2)
		self.assertEqual(len(pagina["rows"]), 2)
		self.assertTrue(pagina["more"])
		self.assertFalse(self.pannello(limit=3)["more"])

	def test_chi_legge_soltanto_legge_le_sue(self):
		avvisa(CARLO, "Automation", testo="per Carlo")
		nome = frappe.get_all(NOTIFICA, filters={"to_user": CARLO}, pluck="name")[0]
		self.come(CARLO)
		self.assertTrue(documenti.sola_lettura(frappe.get_doc(NOTIFICA, nome), "write"))
		self.assertEqual(api.mark_as_read([nome])["unread"], 0)


class ChiNonLaRiceve(NotificheCase):
	def test_ne_se_stessi_ne_un_utente_spento(self):
		self.assertIsNone(avvisa(BRUNO, "Mention", R.MENZIONE, ["Bruno", "Laura"], da=BRUNO))
		frappe.db.set_value("User", ANNA, "enabled", 0)
		self.assertIsNone(avvisa(ANNA, "Automation", testo="spenta"))

	def test_la_stessa_non_letta_una_volta(self):
		for _ in range(2):
			avvisa(BRUNO, "Agenda", R.ESITI_IERI, [2], oggetto=("CRM Appointment", "APP-2"))
		self.assertEqual(frappe.db.count(NOTIFICA, {"to_user": BRUNO, "type": "Agenda"}), 1)


class DopoSeiMesi(NotificheCase):
	def test_se_ne_vanno(self):
		vecchia = avvisa(BRUNO, "Automation", testo="vecchia")
		nuova = avvisa(BRUNO, "Automation", testo="nuova")
		frappe.db.set_value(
			NOTIFICA, vecchia, "creation", add_to_date(now_datetime(), days=-200), update_modified=False
		)
		CRMNotification.clear_old_logs(days=180)
		self.assertFalse(frappe.db.exists(NOTIFICA, vecchia))
		self.assertTrue(frappe.db.exists(NOTIFICA, nuova))
		self.assertIn("CRM Notification", frappe.get_hooks("default_log_clearing_doctypes"))
