# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""The settings pages, split between the centre and the agency (doc 30, PR 3).

A page the Manager opens can hold the agency's plumbing: keys, endpoints, the tag
to put on a website, the secret of a webhook. Those fields sit on permission level
1, System Manager's only, and the methods that act on them ask for
`tecnico.integrazioni`: a Manager's copy of the settings comes without them, and a
save leaves them as they were. The rest of the page is the centre's.
"""

import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.handler import run_doc_method
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request

import crm.tests.test_invoicing as fatturazione

MANAGER = "divise.manager@example.com"
AGENCY = "divise.agency@example.com"
FRONT_DESK = "divise.desk@example.com"

#: What is the agency's on each page, and what stays the centre's.
AGENZIA = {
	"FCRM Settings": ("access_key",),
	"CRM Twilio Settings": (
		"account_sid",
		"auth_token",
		"api_key",
		"api_secret",
		"twiml_sid",
		"app_name",
		"twilio_apps",
		"verify_webhook_signature",
		"webhook_base_url",
		"sip_trunks",
	),
	"CRM Exotel Settings": ("account_sid", "api_key", "api_token", "webhook_verify_token", "subdomain"),
	"CRM Transcription Settings": ("base_url", "model", "api_key", "max_recording_mb", "request_timeout"),
	"CRM Tracking Settings": ("retention_days", "allowed_origins", "excluded_ips"),
}
CENTRO = {
	"FCRM Settings": ("currency", "service_provider", "enable_forecasting"),
	"CRM Twilio Settings": ("enabled", "record_calls", "recording_notice"),
	"CRM Exotel Settings": ("enabled", "record_call"),
	"CRM Transcription Settings": (
		"enabled",
		"auto_transcribe",
		"language",
		"prompt",
		"transcript_retention_days",
		"recording_retention_days",
	),
	"CRM Tracking Settings": ("enabled", "track_anonymous", "require_consent", "store_ip_address"),
}

TWILIO = "crm.fcrm.doctype.crm_twilio_settings.crm_twilio_settings"


def valore(df):
	"""Something to write in a field of this type."""
	if df.fieldtype == "Int":
		return 7
	if df.fieldtype == "Check":
		return 1
	return "agency-value"


def make_user(email: str, *roles: str):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"roles": [{"role": role} for role in roles],
			}
		).insert(ignore_permissions=True)


class DiviseTestCase(IntegrationTestCase):
	def setUp(self):
		# the Manager level's roles, before any level is written on the profile
		make_user(MANAGER, "Sales Manager", "Sales User", "Invoicing Manager", "Invoicing User")
		make_user(AGENCY, "System Manager")
		make_user(FRONT_DESK, "Sales User")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		for doctype in AGENZIA:
			frappe.clear_document_cache(doctype, doctype)


class TestTheFieldsAreSplit(DiviseTestCase):
	def test_the_agencys_fields_sit_on_its_level(self):
		for doctype, campi in AGENZIA.items():
			meta = frappe.get_meta(doctype)
			for campo in campi:
				self.assertEqual(meta.get_field(campo).permlevel, 1, f"{doctype}.{campo}")
			for campo in CENTRO[doctype]:
				self.assertEqual(meta.get_field(campo).permlevel, 0, f"{doctype}.{campo}")

	def test_only_the_agency_holds_that_level(self):
		for doctype in AGENZIA:
			ruoli = {p.role for p in frappe.get_meta(doctype).permissions if p.permlevel == 1}
			self.assertEqual(ruoli, {"System Manager"}, doctype)

	def fill_the_agencys_part(self):
		for doctype, campi in AGENZIA.items():
			meta = frappe.get_meta(doctype)
			frappe.db.set_single_value(doctype, {campo: valore(meta.get_field(campo)) for campo in campi})

	def test_a_manager_reads_the_centres_part_only(self):
		self.fill_the_agencys_part()
		frappe.set_user(MANAGER)
		for doctype, campi in AGENZIA.items():
			# Frappe lists every field of the doctype, empty (0 for a check): the
			# value is what must not come
			doc = frappe.client.get(doctype)
			for campo in campi:
				self.assertFalse(doc.get(campo), f"{doctype}.{campo}")

	def test_the_agency_reads_the_whole_page(self):
		self.fill_the_agencys_part()
		frappe.set_user(AGENCY)
		for doctype, campi in AGENZIA.items():
			doc = frappe.client.get(doctype)
			for campo in campi:
				self.assertIsNotNone(doc.get(campo), f"{doctype}.{campo}")

	def test_a_manager_saving_the_page_leaves_the_agencys_part_alone(self):
		frappe.db.set_single_value(
			"CRM Transcription Settings",
			{"enabled": 0, "base_url": "https://whisper.example.com/v1", "model": "whisper-1"},
		)
		frappe.set_user(MANAGER)
		doc = frappe.get_doc(frappe.client.get("CRM Transcription Settings"))
		doc.language = "it"
		doc.base_url = "https://elsewhere.example.com/v1"
		doc.model = "another"
		doc.save()
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_single_value("CRM Transcription Settings", "language"), "it")
		self.assertEqual(
			frappe.db.get_single_value("CRM Transcription Settings", "base_url"),
			"https://whisper.example.com/v1",
		)
		self.assertEqual(frappe.db.get_single_value("CRM Transcription Settings", "model"), "whisper-1")


class TestTheCentreTurnsThingsOn(DiviseTestCase):
	def test_a_manager_turns_transcription_on_once_the_agency_set_it_up(self):
		frappe.db.set_single_value("CRM Transcription Settings", {"enabled": 0, "base_url": None})
		frappe.set_user(MANAGER)
		doc = frappe.get_doc(frappe.client.get("CRM Transcription Settings"))
		doc.enabled = 1
		with self.assertRaisesRegex(frappe.ValidationError, "agency"):
			doc.save()

		frappe.set_user("Administrator")
		frappe.db.set_single_value(
			"CRM Transcription Settings",
			{"base_url": "https://whisper.example.com/v1", "model": "whisper-1"},
		)
		frappe.set_user(MANAGER)
		doc = frappe.get_doc(frappe.client.get("CRM Transcription Settings"))
		doc.enabled = 1
		doc.save()
		self.assertEqual(frappe.db.get_single_value("CRM Transcription Settings", "enabled"), 1)

	def test_the_agency_is_told_what_to_set(self):
		frappe.db.set_single_value("CRM Transcription Settings", {"enabled": 0, "base_url": None})
		frappe.set_user(AGENCY)
		doc = frappe.get_single("CRM Transcription Settings")
		doc.enabled = 1
		with self.assertRaisesRegex(frappe.ValidationError, "Set the endpoint"):
			doc.save()


class TestTheTwilioMethods(DiviseTestCase):
	"""Frappe runs a document's whitelisted method for whoever can read it."""

	def setUp(self):
		super().setUp()
		self._request = getattr(frappe.local, "request", None)
		set_request(method="POST", path="/api/method/run_doc_method")

	def tearDown(self):
		frappe.local.request = self._request
		super().tearDown()

	def call(self, user: str, method: str, **kwargs):
		frappe.set_user(user)
		frappe.local.response = frappe._dict({"docs": []})
		run_doc_method(
			method,
			dt="CRM Twilio Settings",
			dn="CRM Twilio Settings",
			args=json.dumps(kwargs) if kwargs else None,
		)
		return frappe.response.get("message")

	def test_a_manager_does_not_touch_the_account(self):
		# the precondition that makes the methods reachable at all
		self.assertTrue(frappe.has_permission("CRM Twilio Settings", "read", user=MANAGER))
		with patch(f"{TWILIO}.Client") as client:
			for method in ("fetch_applications", "test_connection", "fetch_sip_trunks"):
				with self.assertRaises(frappe.PermissionError, msg=method):
					self.call(MANAGER, method)
		client.assert_not_called()

	def test_the_agency_tests_the_connection(self):
		from frappe.utils.password import set_encrypted_password

		set_encrypted_password("CRM Twilio Settings", "CRM Twilio Settings", "tok", "auth_token")
		with patch(f"{TWILIO}.Client") as client:
			client.return_value.api.accounts.return_value.fetch.return_value = MagicMock(
				friendly_name="Studio Rossi", status="active"
			)
			esito = self.call(AGENCY, "test_connection")
		self.assertTrue(esito["ok"])
		self.assertEqual(esito["account"], "Studio Rossi")

	def test_a_manager_manages_the_caller_ids(self):
		with patch("crm.telephony.caller_ids.sync", return_value={"added": 0}) as sync:
			self.call(MANAGER, "sync_caller_ids")
		sync.assert_called_once_with("twilio")

	def test_connecting_twilio_is_the_agencys(self):
		frappe.set_user(MANAGER)
		doc = frappe.get_doc(frappe.client.get("CRM Twilio Settings"))
		doc.enabled = 0 if doc.enabled else 1
		with self.assertRaises(frappe.PermissionError):
			doc.save()


class TestTheTrackingTag(DiviseTestCase):
	def test_a_manager_gets_the_numbers_not_the_tag(self):
		from crm.api import tracking

		frappe.set_user(MANAGER)
		dati = tracking.get_snippet()
		self.assertIn("stats", dati)
		self.assertNotIn("snippet", dati)

	def test_the_agency_gets_the_tag(self):
		from crm.api import tracking

		frappe.set_user(AGENCY)
		dati = tracking.get_snippet()
		self.assertIn("<script", dati["snippet"])


class TestTheInvoicingWebhookSecret(DiviseTestCase):
	def test_a_manager_does_not_mint_it(self):
		from crm.invoicing import api

		azienda = fatturazione.InvoicingBase.crea_azienda()
		frappe.set_user(MANAGER)
		# the precondition: the Manager writes the company
		self.assertTrue(frappe.has_permission("CRM Invoicing Company", "write", doc=azienda.name))
		with self.assertRaises(frappe.PermissionError):
			api.generate_webhook_secret(azienda.name)

	def test_the_agency_mints_it(self):
		from crm.invoicing import api

		azienda = fatturazione.InvoicingBase.crea_azienda()
		frappe.set_user(AGENCY)
		esito = api.generate_webhook_secret(azienda.name)
		self.assertEqual(len(esito["secret"]), 48)


class TestTheHierarchy(DiviseTestCase):
	"""The Manager builds the sales hierarchy: it used to be System Manager's."""

	def test_a_manager_places_someone(self):
		frappe.set_user(MANAGER)
		nodo = frappe.get_doc({"doctype": "CRM Sales Hierarchy", "user": FRONT_DESK}).insert()
		self.assertTrue(frappe.db.exists("CRM Sales Hierarchy", nodo.name))

	def test_the_front_desk_does_not(self):
		frappe.set_user(FRONT_DESK)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc({"doctype": "CRM Sales Hierarchy", "user": MANAGER}).insert()
