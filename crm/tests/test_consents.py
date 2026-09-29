# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The consent register, on a real site.

/prenota checked the privacy tick and wrote nothing down: nobody could say what a
person had read, or when. Now every answer is in the register, on its own words,
and a withdrawal is as easy to record as a consent.
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import service_booking as SB
from crm.api.doc import get_linked_docs_of_document
from crm.moduli import consensi
from crm.moduli.registro import DATO, REVOCATO, RIFIUTATO
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.scheduling.availability import forget_settings

# the module, not the class: a TestCase imported here would run here too
from crm.tests import test_service_booking as prenotazioni
from crm.tests.test_scheduling import SchedulingCase

DESK = "consents.desk@example.com"
SALES = "consents.sales@example.com"
MANAGER = "consents.manager@example.com"


class ConsentCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		consensi.assicura_tipi()
		self.anna = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Anna", "last_name": "Consenso"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def marketing_della_persona(self, lead):
		return frappe.db.get_value("CRM Lead", lead, "marketing_consent")


class IlRegistro(ConsentCase):
	def test_la_risposta_tiene_le_sue_parole_e_la_versione(self):
		nome = consensi.registra_risposta(
			self.anna.name, "marketing", canale="On paper", nota="modulo nell'armadio"
		)
		riga = frappe.get_doc("CRM Consent", nome)
		self.assertEqual(riga.text, consensi.testo_attuale("marketing"))
		self.assertEqual(
			riga.text_version, frappe.db.get_value("CRM Consent Type", "marketing", "text_version")
		)
		self.assertEqual(riga.recorded_by, "Administrator")
		self.assertEqual(self.marketing_della_persona(self.anna.name), DATO)

	def test_cambiare_il_testo_fa_una_versione_e_non_tocca_le_risposte(self):
		nome = consensi.registra_risposta(self.anna.name, "marketing")
		prima = frappe.db.get_value("CRM Consent", nome, "text")
		tipo = frappe.get_doc("CRM Consent Type", "marketing")
		versione = tipo.text_version
		tipo.text = "Un testo nuovo, rivisto dal DPO."
		tipo.save()
		self.assertEqual(tipo.text_version, versione + 1)
		self.assertEqual(frappe.db.get_value("CRM Consent", nome, "text"), prima)

	def test_la_revoca_timbra_la_riga_che_lo_aveva_dato(self):
		nome = consensi.registra_risposta(self.anna.name, "marketing")
		consensi.revoca(self.anna.name, "marketing", "By email", "ha scritto di smettere")
		riga = frappe.get_doc("CRM Consent", nome)
		self.assertEqual(riga.status, REVOCATO)
		self.assertEqual(riga.withdrawal_channel, "By email")
		self.assertTrue(riga.withdrawn_on)
		self.assertEqual(self.marketing_della_persona(self.anna.name), REVOCATO)
		self.assertEqual(frappe.db.count("CRM Consent", {"lead": self.anna.name}), 1)

	def test_ridarlo_scrive_una_riga_nuova(self):
		consensi.registra_risposta(self.anna.name, "marketing")
		consensi.revoca(self.anna.name, "marketing")
		consensi.registra_risposta(self.anna.name, "marketing")
		self.assertEqual(consensi.stato(self.anna.name, "marketing"), DATO)
		self.assertEqual(frappe.db.count("CRM Consent", {"lead": self.anna.name}), 2)

	def test_un_si_resta_uno_solo(self):
		"""A second yes writes nothing, a no after a yes withdraws it: one "Given" row,
		the current one - the clinical record asks the table that directly."""
		prima = consensi.registra_risposta(self.anna.name, "marketing")
		self.assertEqual(consensi.registra_risposta(self.anna.name, "marketing"), prima)
		consensi.registra_risposta(self.anna.name, "marketing", RIFIUTATO)
		self.assertEqual(frappe.db.get_value("CRM Consent", prima, "status"), REVOCATO)
		self.assertFalse(frappe.db.exists("CRM Consent", {"lead": self.anna.name, "status": DATO}))

	def test_non_si_revoca_quello_che_non_c_e(self):
		with self.assertRaises(frappe.ValidationError):
			consensi.revoca(self.anna.name, "marketing")
		consensi.registra_risposta(self.anna.name, "privacy_notice")
		with self.assertRaises(frappe.ValidationError):
			consensi.revoca(self.anna.name, "privacy_notice")

	def test_una_risposta_non_si_modifica(self):
		nome = consensi.registra_risposta(self.anna.name, "marketing")
		riga = frappe.get_doc("CRM Consent", nome)
		riga.text = "Tutt'altro"
		with self.assertRaises(frappe.ValidationError):
			riga.save(ignore_permissions=True)
		riga.reload()
		riga.status = RIFIUTATO
		with self.assertRaises(frappe.ValidationError):
			riga.save(ignore_permissions=True)

	def test_una_revoca_non_nasce_da_sola(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "CRM Consent",
					"lead": self.anna.name,
					"consent_type": "marketing",
					"status": REVOCATO,
					"answered_on": frappe.utils.now_datetime(),
					"channel": "At the desk",
				}
			).insert(ignore_permissions=True)

	def test_se_ne_va_con_la_persona(self):
		consensi.registra_risposta(self.anna.name, "marketing")
		self.assertNotIn(
			"CRM Consent", [d["doc"] for d in get_linked_docs_of_document("CRM Lead", self.anna.name)]
		)
		frappe.db.delete(
			"CRM Automation Enrollment", {"reference_doctype": "CRM Lead", "reference_name": self.anna.name}
		)
		frappe.delete_doc("CRM Lead", self.anna.name)
		self.assertFalse(frappe.db.exists("CRM Consent", {"lead": self.anna.name}))


class IlPannello(ConsentCase):
	def setUp(self):
		super().setUp()
		utenti.sincronizza()
		for user in (DESK, SALES, MANAGER):
			make_user(user)
		utenti.assegna_livelli(DESK, ["segreteria"])
		utenti.assegna_livelli(SALES, ["commerciale"])
		utenti.assegna_livelli(MANAGER, ["manager"])
		self.sua = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Bea", "last_name": "Vendite", "lead_owner": SALES}
		).insert(ignore_permissions=True)
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def test_chi_sente_smettete_di_scrivermi_lo_registra(self):
		self.come(SALES)
		dati = consensi.record_consent(self.sua.name, "marketing", DATO, "By phone", "al telefono")
		marketing = next(t for t in dati["types"] if t["key"] == "marketing")
		self.assertEqual(marketing["current"]["status"], DATO)
		self.assertTrue(marketing["can_withdraw"])
		dati = consensi.withdraw_consent(self.sua.name, "marketing", "By phone")
		marketing = next(t for t in dati["types"] if t["key"] == "marketing")
		self.assertEqual(marketing["current"]["status"], REVOCATO)

	def test_un_no_da_chi_aveva_detto_si_e_una_revoca(self):
		self.come(SALES)
		consensi.record_consent(self.sua.name, "marketing", DATO, "By phone")
		consensi.record_consent(self.sua.name, "marketing", RIFIUTATO, "By phone")
		self.assertEqual(consensi.stato(self.sua.name, "marketing"), REVOCATO)
		self.assertEqual(frappe.db.count("CRM Consent", {"lead": self.sua.name}), 1)

	def test_i_consensi_seguono_la_persona(self):
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			consensi.get_consents(self.anna.name)

	def test_a_mano_solo_i_canali_a_mano(self):
		self.come(SALES)
		with self.assertRaises(frappe.ValidationError):
			consensi.record_consent(self.sua.name, "marketing", DATO, "Online booking")

	def test_i_testi_li_cambia_il_manager(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			consensi.consent_types()
		self.come(MANAGER)
		self.assertIn("marketing", [t.name for t in consensi.consent_types()])
		nuovo = consensi.new_consent_type("Foto sui social", "Acconsento alla pubblicazione delle mie foto.")
		self.assertEqual(nuovo["name"], "foto_sui_social")
		cambiato = consensi.save_consent_type(nuovo["name"], text="Acconsento, rivisto.")
		self.assertEqual(cambiato["text_version"], 2)


class DaPrenota(SchedulingCase):
	"""The ticks of the booking page, in the register."""

	online_service = prenotazioni.TestServiceBooking.online_service
	book = prenotazioni.TestServiceBooking.book

	def setUp(self):
		super().setUp()
		self.with_settings(
			online_booking_enabled=1,
			require_privacy_consent=0,
			ask_marketing_consent=0,
			max_active_per_customer=0,
			default_min_notice_hours=0,
			default_max_horizon_days=30,
			default_require_phone=0,
			default_online_confirmation="Automatic",
		)
		self.anna = self.make_user("anna.online@example.com")
		self.bruno = self.make_user("bruno.online@example.com")
		# emails are queued, never sent; keep them out of the way
		self._mail = patch("frappe.sendmail")
		self._mail.start()

	def tearDown(self):
		self._mail.stop()
		super().tearDown()

	def with_settings(self, **values):
		settings = frappe.get_doc("CRM Scheduling Settings")
		settings.update(values)
		settings.save()
		forget_settings()

	def appointment_of(self, result):
		parent = frappe.db.get_value(
			"CRM Appointment Participant", {"access_token": result["token"]}, "parent"
		)
		return frappe.get_doc("CRM Appointment", parent)

	def test_la_spunta_della_privacy_si_registra_con_le_sue_parole(self):
		consensi.assicura_tipi()
		self.with_settings(require_privacy_consent=1, privacy_policy_url="https://example.com/privacy")
		result = self.book(
			self.online_service(),
			self.tomorrow(10),
			consent=1,
			consent_text="Ho letto e accetto l'informativa sulla privacy",
		)
		appuntamento = self.appointment_of(result)
		persona = appuntamento.participants[0].party
		riga = frappe.get_all(
			"CRM Consent",
			filters={"lead": persona, "consent_type": "privacy_notice"},
			fields=["status", "channel", "text", "source_doctype", "source_name", "text_version"],
		)[0]
		self.assertEqual(riga.status, DATO)
		self.assertEqual(riga.channel, "Online booking")
		self.assertEqual(riga.source_name, appuntamento.name)
		self.assertIn("informativa sulla privacy", riga.text)
		self.assertIn("https://example.com/privacy", riga.text)
		# the page's own words are not a version of the kind's text
		self.assertFalse(riga.text_version)

	def test_il_marketing_solo_se_chiesto_e_spuntato(self):
		consensi.assicura_tipi()
		self.with_settings(require_privacy_consent=0, ask_marketing_consent=0)
		self.assertIsNone(SB.get_catalog()["marketing_consent"])
		self.with_settings(ask_marketing_consent=1)
		self.assertTrue(SB.get_catalog()["marketing_consent"]["text"])
		# not ticked: nothing given
		result = self.book(self.online_service(), self.tomorrow(10), email="nessuno@example.com")
		persona = self.appointment_of(result).participants[0].party
		self.assertFalse(frappe.db.exists("CRM Consent", {"lead": persona}))
		# ticked: given, on the kind's own words and version
		result = self.book(
			self.online_service("Online Massage"),
			self.tomorrow(11),
			email="si@example.com",
			marketing_consent=1,
		)
		persona = self.appointment_of(result).participants[0].party
		self.assertEqual(consensi.stato(persona, "marketing"), DATO)
		self.assertEqual(frappe.db.get_value("CRM Lead", persona, "marketing_consent"), DATO)
		self.assertTrue(
			frappe.db.get_value("CRM Consent", {"lead": persona, "consent_type": "marketing"}, "text_version")
		)

	def test_una_pagina_vecchia_senza_parole_non_ferma_la_prenotazione(self):
		consensi.assicura_tipi()
		self.with_settings(require_privacy_consent=1, privacy_policy_url="")
		with patch.object(frappe, "get_request_header", return_value=None):
			result = self.book(self.online_service(), self.tomorrow(12), consent=1)
		persona = self.appointment_of(result).participants[0].party
		self.assertEqual(consensi.stato(persona, "privacy_notice"), DATO)
