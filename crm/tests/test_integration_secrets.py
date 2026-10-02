# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""Integration secrets are Password fields: kept encrypted, handed out masked.

Whoever can read a settings document gets the mask, through REST and frappe.client
alike (and FCRM Settings is loaded in every browser). Only the code that talks to
the provider decrypts them. For a Single, a field permission level would not do
it: frappe.client.get_value and get_single_value check the doctype, not the field.

The agency's keys also sit on permission level 1, System Manager's only (doc 30): a
Manager's copy of the settings comes without them, and a save leaves them as they
were. The mask stays underneath, for the paths that do not look at the level.
"""

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request
from frappe.utils.password import remove_encrypted_password

from crm.fcrm.doctype.crm_booking_connection.crm_booking_connection import connection_for_token

MANAGER = "secrets.manager@example.com"
SALES_USER = "secrets.user@example.com"

SECRETS = {
	"FCRM Settings": ("access_key",),
	"CRM Meta Settings": ("webhook_verify_token",),
	"CRM Exotel Settings": ("api_key", "webhook_verify_token"),
	"CRM Booking Connection": ("webhook_token",),
}


# what an existing site has in its columns before the patch
PLAIN_TEXT = {
	("FCRM Settings", "access_key"): "plain-exchange-key",
	("CRM Meta Settings", "webhook_verify_token"): "plain-meta-token",
	("CRM Exotel Settings", "api_key"): "plain-exotel-key",
	("CRM Exotel Settings", "webhook_verify_token"): "plain-exotel-token",
}


def make_user(email: str, role: str):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"roles": [{"role": role}],
			}
		).insert(ignore_permissions=True)


def save_single(doctype: str, **values):
	doc = frappe.get_single(doctype)
	doc.update(values)
	doc.save()
	frappe.clear_document_cache(doctype, doctype)


def make_connection(name: str = "Secrets Webhook", enabled: int = 1):
	return frappe.get_doc(
		{
			"doctype": "CRM Booking Connection",
			"connection_name": name,
			"platform": "Generic webhook (Zapier, Make, n8n)",
			"enabled": enabled,
		}
	).insert()


class SecretsTestCase(IntegrationTestCase):
	def setUp(self):
		make_user(MANAGER, "Sales Manager")
		make_user(SALES_USER, "Sales User")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		for doctype in SECRETS:
			frappe.clear_document_cache(doctype, doctype)

	def assert_masked(self, value, secret: str):
		self.assertNotEqual(value, secret)
		self.assertTrue(not value or set(value) == {"*"}, value)

	def assert_single_masked_for(self, user: str, doctype: str, fieldname: str, secret: str):
		frappe.set_user(user)
		self.assert_masked(frappe.client.get(doctype).get(fieldname), secret)
		self.assert_masked(frappe.client.get_single_value(doctype, fieldname), secret)
		self.assert_masked(frappe.client.get_value(doctype, fieldname)[fieldname], secret)
		frappe.set_user("Administrator")


class TestSecretsAreNotHandedOut(SecretsTestCase):
	def test_every_secret_is_a_password_field(self):
		for doctype, fieldnames in SECRETS.items():
			for fieldname in fieldnames:
				field = frappe.get_meta(doctype).get_field(fieldname)
				self.assertEqual(field.fieldtype, "Password", f"{doctype}.{fieldname}")

	def test_the_exchange_rate_key_is_masked_for_everyone_who_loads_the_settings(self):
		save_single("FCRM Settings", access_key="exchange-live-key")
		for user in (SALES_USER, MANAGER, "Administrator"):
			self.assert_single_masked_for(user, "FCRM Settings", "access_key", "exchange-live-key")

	def test_the_meta_verify_token_is_masked_for_a_manager(self):
		save_single("CRM Meta Settings")  # validate() generates the token
		from crm.integrations.meta.client import get_webhook_verify_token

		token = get_webhook_verify_token()
		self.assertEqual(len(token), 32)
		self.assert_single_masked_for(MANAGER, "CRM Meta Settings", "webhook_verify_token", token)

	def test_the_exotel_credentials_are_masked_for_a_manager(self):
		save_single("CRM Exotel Settings", enabled=0, api_key="exotel-key", webhook_verify_token="exo-verify")
		self.assert_single_masked_for(MANAGER, "CRM Exotel Settings", "api_key", "exotel-key")
		self.assert_single_masked_for(MANAGER, "CRM Exotel Settings", "webhook_verify_token", "exo-verify")

	def test_the_agency_keys_do_not_reach_a_manager_at_all(self):
		save_single("FCRM Settings", access_key="exchange-live-key")
		save_single("CRM Exotel Settings", enabled=0, api_key="exotel-key", account_sid="exo-sid")
		frappe.set_user(MANAGER)
		# Frappe lists every field of the doctype: the value is what must not come
		self.assertIsNone(frappe.client.get("FCRM Settings").get("access_key"))
		exotel = frappe.client.get("CRM Exotel Settings")
		self.assertIsNone(exotel.get("api_key"))
		self.assertIsNone(exotel.get("account_sid"))

	def test_a_manager_saving_the_settings_leaves_the_agency_keys_alone(self):
		save_single("CRM Exotel Settings", enabled=0, account_sid="exo-sid", subdomain="api.exotel.com")
		frappe.set_user(MANAGER)
		exotel = frappe.get_doc(frappe.client.get("CRM Exotel Settings"))
		exotel.record_call = 1
		exotel.account_sid = "someone-else"
		exotel.subdomain = "evil.example.com"
		exotel.save()
		frappe.set_user("Administrator")
		frappe.clear_document_cache("CRM Exotel Settings", "CRM Exotel Settings")
		saved = frappe.get_single("CRM Exotel Settings")
		self.assertEqual(saved.record_call, 1)
		self.assertEqual(saved.account_sid, "exo-sid")
		self.assertEqual(saved.subdomain, "api.exotel.com")

	def test_connecting_a_provider_is_the_agencys(self):
		frappe.set_user(MANAGER)
		exotel = frappe.get_doc(frappe.client.get("CRM Exotel Settings"))
		exotel.enabled = 1
		with self.assertRaises(frappe.PermissionError):
			exotel.save()

	def test_the_booking_webhook_token_is_masked_for_a_manager(self):
		conn = make_connection()
		token = conn.get_password("webhook_token")
		self.assertEqual(len(token), 32)

		frappe.set_user(MANAGER)
		self.assert_masked(frappe.client.get("CRM Booking Connection", conn.name)["webhook_token"], token)
		self.assert_masked(
			frappe.client.get_value("CRM Booking Connection", "webhook_token", conn.name)["webhook_token"],
			token,
		)
		rows = frappe.client.get_list(
			"CRM Booking Connection", fields=["name", "webhook_token"], filters={"name": conn.name}
		)
		self.assert_masked(rows[0]["webhook_token"], token)

		# and a Sales User does not reach the connection at all
		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			frappe.client.get("CRM Booking Connection", conn.name)

	def test_a_second_connection_can_be_saved(self):
		"""Every mask of a 32-character token is the same: no unique index on it."""
		make_connection("Secrets Webhook A")
		make_connection("Secrets Webhook B")
		self.assertEqual(
			frappe.db.count("CRM Booking Connection", {"connection_name": ["like", "Secrets%"]}), 2
		)


class TestSecretsStillWork(SecretsTestCase):
	def test_the_exchange_rate_provider_gets_the_key(self):
		from crm.api.exchange_rate import _fetch_exchange_rate

		save_single("FCRM Settings", service_provider="exchangerate.host", access_key="exchange-live-key")
		response = MagicMock(ok=True)
		response.json.return_value = {"result": 1.08}
		with patch("crm.api.exchange_rate.requests.get", return_value=response) as get:
			rate, provider = _fetch_exchange_rate("EUR", "USD", "latest")
		self.assertEqual((rate, provider), (1.08, "exchangerate.host"))
		self.assertEqual(get.call_args.kwargs["params"]["access_key"], "exchange-live-key")

	def test_the_meta_and_whatsapp_handshakes_answer_the_right_token_only(self):
		from crm.integrations.meta import webhook as meta_webhook
		from crm.integrations.meta.client import get_webhook_verify_token
		from crm.integrations.whatsapp import webhook as whatsapp_webhook

		save_single("CRM Meta Settings")
		token = get_webhook_verify_token()
		for module in (meta_webhook, whatsapp_webhook):
			ok = module._verify_subscription(
				frappe._dict({"hub.mode": "subscribe", "hub.verify_token": token, "hub.challenge": "4242"})
			)
			self.assertEqual((ok.status_code, ok.get_data(as_text=True)), (200, "4242"))
			for offered in ("*" * len(token), "wrong", "", "tökèn"):
				refused = module._verify_subscription(
					frappe._dict({"hub.mode": "subscribe", "hub.verify_token": offered, "hub.challenge": "1"})
				)
				self.assertEqual(refused.status_code, 403, offered)

	def test_exotel_gets_the_key_and_checks_its_webhook(self):
		from crm.integrations.exotel import handler

		save_single(
			"CRM Exotel Settings",
			enabled=0,
			api_key="exotel-key",
			api_token="exotel-token",
			subdomain="api.exotel.com",
			account_sid="acme",
			webhook_verify_token="exo-verify",
		)
		self.assertIn("exotel-key:exotel-token@", handler.get_exotel_endpoint("Calls/connect"))
		self.assertIn("key=exo-verify", handler.get_status_updater_url())

		original = getattr(frappe.local, "request", None)
		try:
			set_request(method="POST", path="/api/method/x", query_string="key=exo-verify")
			handler.validate_request()
			for key in ("*" * 10, "wrong", "", "clé"):
				set_request(method="POST", path="/api/method/x", query_string={"key": key})
				with self.assertRaises(frappe.PermissionError, msg=key):
					handler.validate_request()
		finally:
			frappe.local.request = original

	def test_the_booking_token_names_its_connection(self):
		conn = make_connection()
		token = conn.get_password("webhook_token")
		self.assertEqual(connection_for_token(token), conn.name)
		for wrong in (None, "", "*" * len(token), token[:-1], "tökèn"):
			self.assertIsNone(connection_for_token(wrong), wrong)

		frappe.db.set_value("CRM Booking Connection", conn.name, "enabled", 0)
		self.assertIsNone(connection_for_token(token))

	def test_a_manager_still_gets_the_urls_to_paste_into_the_platform(self):
		from crm.api import booking_platforms as API

		conn = make_connection()
		token = conn.get_password("webhook_token")
		frappe.set_user(MANAGER)
		data = API.get_connection(conn.name)
		self.assertIn(f"token={token}", data["webhook_url"])
		self.assertIn(f"token={token}", data["busy_feed_url"])


class TestTheMigrationPatch(SecretsTestCase):
	"""What an existing site has in its columns: the secrets in plain text."""

	def seed_plain_text(self):
		for (doctype, fieldname), value in PLAIN_TEXT.items():
			remove_encrypted_password(doctype, doctype, fieldname)
			frappe.db.set_single_value(doctype, fieldname, value)
		conn = make_connection()
		remove_encrypted_password("CRM Booking Connection", conn.name, "webhook_token")
		frappe.db.set_value("CRM Booking Connection", conn.name, "webhook_token", "plain-booking-token")
		return conn.name

	def assert_encrypted(self, connection: str):
		for (doctype, fieldname), value in PLAIN_TEXT.items():
			stored = frappe.db.get_single_value(doctype, fieldname)
			self.assertEqual(stored, "*" * len(value), f"{doctype}.{fieldname}")
			self.assertEqual(frappe.get_single(doctype).get_password(fieldname), value)
		stored = frappe.db.get_value("CRM Booking Connection", connection, "webhook_token")
		self.assertEqual(stored, "*" * len("plain-booking-token"))
		self.assertEqual(connection_for_token("plain-booking-token"), connection)

	def test_plain_text_secrets_move_to_the_encrypted_store(self):
		from crm.patches.v1_0.encrypt_integration_secrets import execute

		connection = self.seed_plain_text()
		execute()
		self.assert_encrypted(connection)

		# a second run finds only masks and changes nothing
		execute()
		self.assert_encrypted(connection)

	def test_nothing_stored_stays_nothing(self):
		from crm.patches.v1_0.encrypt_integration_secrets import execute

		remove_encrypted_password("CRM Exotel Settings", "CRM Exotel Settings", "api_key")
		frappe.db.set_single_value("CRM Exotel Settings", "api_key", None)
		execute()
		self.assertFalse(frappe.db.get_single_value("CRM Exotel Settings", "api_key"))
		self.assertIsNone(
			frappe.get_single("CRM Exotel Settings").get_password("api_key", raise_exception=False)
		)
