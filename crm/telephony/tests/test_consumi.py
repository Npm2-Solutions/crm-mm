# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the centre's Twilio space spends, and what went wrong in it (doc 52, fifth
part), on a real site with Twilio simulated.

Twilio's page shows this month by kind and the last days' problems in words, to
whoever pays for the space. The amount the centre writes as its alert becomes a
usage trigger in the space - replaced when it changes, put back every hour - and
when Twilio calls, whoever pays is told. An SMS Twilio refuses, or that does not
arrive, says why in words and keeps Twilio's code.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from twilio.base.exceptions import TwilioRestException

from crm.api import sms as sms_api
from crm.integrations.twilio import api
from crm.telephony import collegamento, consumi, errori
from crm.telephony.tests.test_collegamento import TwilioCase
from crm.tests.test_documenti_del_core import AGENCY, FRONT_DESK, MANAGER


class ConsumiCase(TwilioCase):
	def setUp(self):
		super().setUp()
		self.collega()
		self.space = self.spazio().sid
		frappe.cache.delete_value(f"crm:twilio:consumi:{self.space}")
		self.addCleanup(frappe.cache.delete_value, f"crm:twilio:consumi:{self.space}")

	def come(self, utente):
		frappe.set_user(utente)
		self.addCleanup(frappe.set_user, "Administrator")

	def avviso(self, valore):
		"""The manager writes the alert on Twilio's page and saves it."""
		self.come(MANAGER)
		impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
		impostazioni.spend_alert = valore
		impostazioni.save()
		frappe.set_user("Administrator")

	def soglie(self):
		return self.mondo.soglie[self.space]


class IlMese(ConsumiCase):
	def test_per_voce_e_i_problemi_in_parole(self):
		self.mondo.spende(self.space, "calls", "12.30", count=40, usage=310, usage_unit="minutes")
		self.mondo.spende(self.space, "sms", "9.30", count=100, usage=100, usage_unit="messages")
		self.mondo.spende(self.space, "totalprice", "70")
		adesso = datetime.now(UTC)
		self.mondo.problema(
			self.space, "30003", "Unreachable destination handset", adesso - timedelta(hours=2)
		)
		self.mondo.problema(
			self.space, "30003", "Unreachable destination handset", adesso - timedelta(hours=1)
		)
		self.mondo.problema(self.space, "45999", "Something Twilio says", adesso - timedelta(days=1))
		self.mondo.problema(self.space, "82002", "Only a warning", adesso, livello="warning")
		self.come(MANAGER)
		dati = consumi.get_twilio_usage()
		self.assertTrue(dati["visible"])
		self.assertEqual((dati["month"]["total"], dati["month"]["currency"]), ("70.00", "USD"))
		voci = {voce["key"]: voce for voce in dati["month"]["items"]}
		self.assertEqual((voci["calls"]["count"], voci["calls"]["minutes"]), (40, 310))
		self.assertEqual(voci["other"]["price"], "48.40")
		# the errors only, one line per code, the most recent first
		[irraggiungibile, sconosciuto] = dati["problems"]
		self.assertEqual((irraggiungibile["code"], irraggiungibile["count"]), (30003, 2))
		self.assertEqual(irraggiungibile["sentence"], errori.in_parole(30003))
		# a code DottorCloud has no sentence for keeps Twilio's words
		self.assertIn("Something Twilio says", sconosciuto["sentence"])

	def test_twilio_si_chiede_una_volta_ogni_dieci_minuti(self):
		self.come(MANAGER)
		consumi.get_twilio_usage()
		self.mondo.spende(self.space, "totalprice", "5")
		self.assertEqual(consumi.get_twilio_usage()["month"]["total"], "0.00")

	def test_un_twilio_che_non_risponde(self):
		self.come(MANAGER)
		with patch.object(
			consumi, "_chiedi", side_effect=TwilioRestException(401, "/Usage", "Unauthorized", code=20003)
		):
			dati = consumi.get_twilio_usage()
		self.assertTrue(dati["visible"])
		self.assertTrue(dati["error"])


class ChiLoVede(ConsumiCase):
	def test_paga_il_centro_lo_vede_il_responsabile(self):
		self.come(MANAGER)
		self.assertTrue(consumi.get_twilio_usage()["visible"])
		self.come(FRONT_DESK)
		with self.assertRaises(frappe.PermissionError):
			consumi.get_twilio_usage()

	def test_paga_l_agenzia_lo_vede_l_agenzia(self):
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, "account_owner", "Agency")
		self.come(MANAGER)
		self.assertFalse(consumi.get_twilio_usage()["visible"])
		self.come(AGENCY)
		self.assertTrue(consumi.get_twilio_usage()["visible"])


class LAvviso(ConsumiCase):
	def test_diventa_un_trigger_dello_spazio(self):
		self.avviso(50)
		[trigger] = self.soglie()
		self.assertEqual(
			(trigger.trigger_value, trigger.usage_category, trigger.trigger_by, trigger.recurring),
			("50.00", "totalprice", "price", "monthly"),
		)
		self.assertTrue(trigger.callback_url.endswith(consumi.QUANDO_SPESO))
		self.assertEqual(
			frappe.db.get_single_value(collegamento.IMPOSTAZIONI, "spend_alert_trigger"), trigger.sid
		)

	def test_cambiato_un_altro_al_suo_posto_tolto_niente(self):
		self.avviso(50)
		[primo] = self.soglie()
		self.avviso(80)
		[secondo] = self.soglie()
		self.assertNotEqual(primo.sid, secondo.sid)
		self.assertEqual(secondo.trigger_value, "80.00")
		self.avviso(0)
		self.assertEqual(self.soglie(), [])
		self.assertFalse(frappe.db.get_single_value(collegamento.IMPOSTAZIONI, "spend_alert_trigger"))

	def test_un_importo_che_non_va(self):
		with self.assertRaises(frappe.ValidationError):
			self.avviso(500000)

	def test_ogni_ora_lo_rimette(self):
		self.avviso(50)
		self.soglie().clear()
		collegamento.assicura()
		[trigger] = self.soglie()
		self.assertEqual(trigger.trigger_value, "50.00")

	def test_sull_account_dell_agenzia_lo_mette_l_agenzia(self):
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, "account_owner", "Agency")
		with self.assertRaises(frappe.PermissionError):
			self.avviso(50)


class TwilioChiama(ConsumiCase):
	def setUp(self):
		super().setUp()
		finto = patch("crm.integrations.twilio.api.validate_twilio_request", return_value=None)
		finto.start()
		self.addCleanup(finto.stop)
		frappe.db.delete("CRM Notification", {"type": "Phone"})

	def test_lo_sa_chi_paga(self):
		self.avviso(50)
		[trigger] = self.soglie()
		api.spend_reached(UsageTriggerSid=trigger.sid, CurrentValue="51.20", TriggerValue="50.00")
		avvisati = frappe.get_all("CRM Notification", filters={"type": "Phone"}, pluck="to_user")
		self.assertIn(MANAGER, avvisati)
		self.assertNotIn(AGENCY, avvisati)

	def test_un_trigger_che_non_e_il_nostro(self):
		self.avviso(50)
		self.assertEqual(consumi.speso("UTaltro", "99", "50"), [])


class GliSmsInParole(ConsumiCase):
	def setUp(self):
		super().setUp()
		self.persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Ugo", "last_name": "Errori", "mobile_no": "+390212345000"}
		).insert(ignore_permissions=True)

	def sms(self, **campi):
		return sms_api.create_sms(
			type="Outgoing",
			from_number="+393331234567",
			to="+390212345000",
			message="Ci vediamo domani",
			reference_doctype="CRM Lead",
			reference_name=self.persona.name,
			**campi,
		)

	def test_rifiutato_da_twilio(self):
		doc = self.sms()

		def rifiuta(**_valori):
			raise TwilioRestException(
				400, "/Messages.json", "'To' number is not a valid mobile number", code=21614
			)

		twilio = SimpleNamespace(twilio_client=SimpleNamespace(messages=SimpleNamespace(create=rifiuta)))
		with patch("crm.api.sms.Twilio.connect", return_value=twilio):
			sms_api.deliver_via_twilio(doc)
		doc.reload()
		self.assertEqual((doc.status, doc.error_code), ("Failed", 21614))
		self.assertEqual(doc.error_message, errori.in_parole(21614))

	def test_partito_ma_non_arrivato(self):
		doc = self.sms(status="Sent")
		doc.db_set("message_sid", "SMnonarrivato")
		with patch("crm.integrations.twilio.api.validate_twilio_request", return_value=None):
			api.update_sms_status_info(
				MessageSid="SMnonarrivato", MessageStatus="undelivered", ErrorCode="30003"
			)
		doc.reload()
		self.assertEqual((doc.status, doc.error_code), ("Undelivered", 30003))
		self.assertEqual(doc.error_message, errori.in_parole(30003))
