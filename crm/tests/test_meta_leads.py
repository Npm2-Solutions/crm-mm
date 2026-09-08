# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import hashlib
import hmac
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.lead import find_person
from crm.integrations.meta import api
from crm.integrations.meta import relay as R
from crm.integrations.meta import webhook as W
from crm.integrations.meta.leads import (
	already_stored,
	forget_person,
	ingest_leadgen_entry,
	normalize_value,
	reconcile_synced_pages,
	store_lead,
)
from crm.integrations.meta.oauth import _parse_state, _sign_state, merge_questions


def make_form(form_id="990001", page_id="880001"):
	if not frappe.db.exists("Facebook Page", page_id):
		frappe.get_doc(
			{
				"doctype": "Facebook Page",
				"id": page_id,
				"page_name": "Test Page",
				"sync_enabled": 1,
				"access_token": "tok",
			}
		).insert(ignore_permissions=True)
	if frappe.db.exists("Facebook Lead Form", form_id):
		return frappe.get_doc("Facebook Lead Form", form_id)
	doc = frappe.get_doc(
		{
			"doctype": "Facebook Lead Form",
			"id": form_id,
			"form_name": "Test Form",
			"page": page_id,
			"questions": [
				{"key": "full_name", "type": "FULL_NAME", "mapped_to_crm_field": "first_name"},
				{"key": "email", "type": "EMAIL", "mapped_to_crm_field": "email"},
				{"key": "phone_number", "type": "PHONE", "mapped_to_crm_field": "mobile_no"},
				{"key": "custom_q", "type": "CUSTOM", "mapped_to_crm_field": ""},
			],
		}
	)
	doc.flags.ignore_validate = True
	doc.insert(ignore_permissions=True)
	return doc


def sample_lead(lead_id="7770001"):
	return {
		"id": lead_id,
		"created_time": "2026-08-31T10:00:00+0000",
		"form_id": "990001",
		"field_data": [
			{"name": "full_name", "values": ["Mario Rossi"]},
			{"name": "email", "values": ["mario@example.com"]},
			{"name": "phone_number", "values": ["p:+39 333 1234567"]},
			{"name": "custom_q", "values": ["risposta"]},
		],
	}


class TestMetaLeads(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_store_lead_maps_fields_and_splits_full_name(self):
		make_form()
		result = store_lead(sample_lead(), "990001")
		self.assertEqual(result, "created")
		name = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7770001"})
		lead = frappe.get_doc("CRM Lead", name)
		self.assertEqual(lead.first_name, "Mario")
		self.assertEqual(lead.last_name, "Rossi")
		self.assertEqual(lead.email, "mario@example.com")
		self.assertEqual(lead.mobile_no, "+393331234567")
		self.assertEqual(lead.source, "Facebook")
		self.assertEqual(lead.facebook_form_id, "990001")

	def test_unmapped_answers_are_kept_as_a_note(self):
		make_form()
		lead = sample_lead("7770010")
		store_lead(lead, "990001")
		name = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7770010"})
		# custom_q has no mapped field: its answer must survive somewhere
		comments = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "CRM Lead", "reference_name": name},
			pluck="content",
		)
		self.assertTrue(any("risposta" in (c or "") for c in comments))

	def test_a_second_form_is_a_submission_not_a_second_person(self):
		"""The same human being answering two ads is one person with two
		submissions — in every CRM the person is deduplicated on email/phone."""
		make_form()
		self.assertEqual(store_lead(sample_lead("7770201"), "990001"), "created")
		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7770201"})

		again = sample_lead("7770202")
		self.assertEqual(store_lead(again, "990001"), "merged")

		self.assertEqual(frappe.db.count("CRM Lead", {"email": "mario@example.com"}), 1)
		doc = frappe.get_doc("CRM Lead", person)
		self.assertEqual([row.leadgen_id for row in doc.facebook_submissions], ["7770201", "7770202"])

	def test_a_merged_submission_is_not_imported_twice(self):
		"""Meta re-delivers, and the hourly reconciliation re-reads two days."""
		make_form()
		store_lead(sample_lead("7770301"), "990001")
		store_lead(sample_lead("7770302"), "990001")
		self.assertTrue(already_stored("7770302"))
		self.assertEqual(store_lead(sample_lead("7770302"), "990001"), "duplicate")
		self.assertEqual(frappe.db.count("CRM Lead", {"email": "mario@example.com"}), 1)

	def test_merging_never_overwrites_what_somebody_typed(self):
		make_form()
		store_lead(sample_lead("7770401"), "990001")
		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7770401"})
		frappe.db.set_value("CRM Lead", person, "job_title", "Titolare")

		second = sample_lead("7770402")
		second["field_data"].append({"name": "custom_q", "values": ["Impiegato"]})
		store_lead(second, "990001")
		self.assertEqual(frappe.db.get_value("CRM Lead", person, "job_title"), "Titolare")

	def test_a_deleted_lead_does_not_come_back(self):
		"""Deleting a lead has to mean deleting it. The reconciliation re-reads
		two days of every form, so without the ledger it returned within the
		hour — which is exactly what was happening on the live site."""
		make_form()
		self.assertEqual(store_lead(sample_lead("7770601"), "990001"), "created")
		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7770601"})

		frappe.delete_doc("CRM Lead", person, force=True, ignore_permissions=True)

		self.assertTrue(already_stored("7770601"))
		self.assertEqual(store_lead(sample_lead("7770601"), "990001"), "duplicate")
		self.assertFalse(frappe.db.exists("CRM Lead", {"facebook_lead_id": "7770601"}))

	def test_deleting_a_person_stamps_their_submissions(self):
		make_form()
		store_lead(sample_lead("7770701"), "990001")
		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7770701"})

		forget_person(frappe.get_doc("CRM Lead", person))

		self.assertTrue(frappe.db.get_value("Facebook Lead Import", "7770701", "deleted_on"))

	def test_store_lead_is_idempotent(self):
		make_form()
		self.assertEqual(store_lead(sample_lead("7770002"), "990001"), "created")
		self.assertEqual(store_lead(sample_lead("7770002"), "990001"), "duplicate")

	def test_store_lead_instagram_platform_sets_source(self):
		make_form()
		lead = sample_lead("7770003")
		lead["platform"] = "ig"
		store_lead(lead, "990001")
		name = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7770003"})
		self.assertEqual(frappe.db.get_value("CRM Lead", name, "source"), "Instagram")

	def test_store_lead_without_first_name_logs_failure(self):
		make_form()
		lead = {"id": "7770004", "form_id": "990001", "field_data": [{"name": "custom_q", "values": ["x"]}]}
		self.assertEqual(store_lead(lead, "990001"), "failed")
		self.assertTrue(frappe.db.exists("Failed Lead Sync Log", {"lead_data": ["like", "%7770004%"]}))

	def test_normalize_phone(self):
		self.assertEqual(normalize_value("mobile_no", "p:+39 333 123 4567"), "+393331234567")
		self.assertEqual(normalize_value("email", "  a@b.com "), "a@b.com")

	def test_merge_questions_keeps_manual_mapping(self):
		form = make_form()
		for q in form.questions:
			if q.key == "custom_q":
				q.mapped_to_crm_field = "job_title"
		merge_questions(
			form,
			[
				{"key": "custom_q", "label": "Nuova label", "type": "CUSTOM"},
				{"key": "nuova", "label": "Nuova domanda", "type": "CUSTOM"},
			],
		)
		by_key = {q.key: q for q in form.questions}
		self.assertEqual(by_key["custom_q"].mapped_to_crm_field, "job_title")
		self.assertIn("nuova", by_key)

	def test_ingest_skips_a_page_that_no_longer_syncs(self):
		make_form()
		frappe.db.set_value("Facebook Page", "880001", "sync_enabled", 0)
		ingest_leadgen_entry("7770099", page_id="880001", form_id="990001")
		self.assertFalse(frappe.db.exists("CRM Lead", {"facebook_lead_id": "7770099"}))

	def test_ingest_finds_the_page_through_the_form(self):
		"""A notification without the page id must not bypass the switch."""
		make_form()
		frappe.db.set_value("Facebook Page", "880001", "sync_enabled", 0)
		ingest_leadgen_entry("7770098", form_id="990001")
		self.assertFalse(frappe.db.exists("CRM Lead", {"facebook_lead_id": "7770098"}))

	def test_disconnect_stops_every_page(self):
		"""Disconnecting used to clear the user token and nothing else, so the
		pages kept their token, their webhook and their hourly polling."""
		make_form()
		frappe.set_user("Administrator")
		with patch.object(api, "graph_post") as graph_post:
			api.disconnect()
		# every page it knows is unsubscribed from the leadgen webhook
		self.assertIn("880001/subscribed_apps", [call[0][0] for call in graph_post.call_args_list])

		page = frappe.get_doc("Facebook Page", "880001")
		self.assertEqual(page.sync_enabled, 0)
		self.assertEqual(page.webhook_subscribed, 0)
		self.assertIsNone(page.get_password("access_token", raise_exception=False))
		self.assertIsNone(
			frappe.get_doc("CRM Meta Settings").get_password("user_access_token", raise_exception=False)
		)

	def test_disconnected_pages_are_left_out_of_the_reconciliation(self):
		make_form()
		frappe.set_user("Administrator")
		with patch.object(api, "graph_post"):
			api.disconnect()
		with patch("crm.integrations.meta.leads.backfill_form") as backfill:
			reconcile_synced_pages()
		backfill.assert_not_called()

	def test_find_person_ignores_whether_they_have_a_deal(self):
		"""Looking a customer up with `converted = 0` is what made a second
		record for somebody who came back after a deal was opened."""
		make_form()
		store_lead(sample_lead("7770501"), "990001")
		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7770501"})
		frappe.db.set_value("CRM Lead", person, "converted", 1)

		self.assertEqual(find_person(email="mario@example.com"), person)
		self.assertEqual(find_person(phone="+39 333 1234567"), person)
		self.assertIsNone(find_person(email="nessuno@example.com"))

	def test_webhook_signature_validation(self):
		settings = frappe.get_doc("CRM Meta Settings")
		settings.app_secret = "topsecret"
		settings.save()
		frappe.clear_document_cache("CRM Meta Settings", "CRM Meta Settings")

		body = b'{"object":"page","entry":[]}'
		good = "sha256=" + hmac.new(b"topsecret", body, hashlib.sha256).hexdigest()
		self.assertTrue(W._valid_signature(good, body))
		self.assertFalse(W._valid_signature("sha256=deadbeef", body))
		self.assertFalse(W._valid_signature(None, body))


class TestMetaSharedApp(IntegrationTestCase):
	"""One agency app serving many client sites: signed state + page routing."""

	def tearDown(self):
		frappe.local.conf.pop("meta_relay_secret", None)
		frappe.local.conf.pop("meta_hub_url", None)
		frappe.local.conf.pop("meta_relay_sites", None)
		frappe.db.rollback()

	def test_state_roundtrip_and_tamper(self):
		import base64
		import json as _json
		import time as _time

		payload = _json.dumps({"t": int(_time.time()), "site": "https://cliente.it"})
		state = f"{base64.urlsafe_b64encode(payload.encode()).decode()}.{_sign_state(payload)}"
		parsed = _parse_state(state)
		self.assertEqual(parsed["site"], "https://cliente.it")
		# a forged destination does not verify
		forged = _json.dumps({"t": int(_time.time()), "site": "https://evil.example"})
		bad = f"{base64.urlsafe_b64encode(forged.encode()).decode()}.{_sign_state(payload)}"
		self.assertIsNone(_parse_state(bad))
		self.assertIsNone(_parse_state("garbage"))

	def test_expired_state_is_rejected(self):
		import base64
		import json as _json

		payload = _json.dumps({"t": 1, "site": "https://cliente.it"})
		state = f"{base64.urlsafe_b64encode(payload.encode()).decode()}.{_sign_state(payload)}"
		self.assertIsNone(_parse_state(state))

	def test_relay_signature(self):
		frappe.local.conf["meta_relay_secret"] = "shared"
		body = b'{"object":"page"}'
		self.assertTrue(R.valid_relay_signature(R.sign(body), body))
		self.assertFalse(R.valid_relay_signature("nope", body))
		self.assertFalse(R.valid_relay_signature(None, body))

	def test_relay_signature_needs_configured_secret(self):
		body = b'{"object":"page"}'
		signature = "a" * 64
		self.assertFalse(R.valid_relay_signature(signature, body))

	def test_route_for_returns_none_for_own_site(self):
		frappe.get_doc(
			{
				"doctype": "Meta Page Route",
				"page_id": "880777",
				"site_url": frappe.utils.get_url(),
			}
		).insert(ignore_permissions=True)
		self.assertIsNone(R.route_for("880777"))
		self.assertIsNone(R.route_for(""))

	def test_claim_refuses_takeover_of_another_site(self):
		frappe.local.conf["meta_relay_secret"] = "shared"
		frappe.get_doc(
			{"doctype": "Meta Page Route", "page_id": "880999", "site_url": "https://primo.it"}
		).insert(ignore_permissions=True)

		ts = str(int(__import__("time").time()))
		signature = R.sign(f"880999|https://ladro.it|{ts}".encode())
		response = R.register_page_route("880999", "https://ladro.it", ts, signature)
		self.assertEqual(response.status_code, 409)
		self.assertEqual(frappe.db.get_value("Meta Page Route", "880999", "site_url"), "https://primo.it")

	def test_claim_refuses_site_outside_allowlist(self):
		frappe.local.conf["meta_relay_secret"] = "shared"
		frappe.local.conf["meta_relay_sites"] = ["https://buono.it"]
		ts = str(int(__import__("time").time()))
		signature = R.sign(f"881000|https://ignoto.it|{ts}".encode())
		response = R.register_page_route("881000", "https://ignoto.it", ts, signature)
		self.assertEqual(response.status_code, 403)
		self.assertFalse(frappe.db.exists("Meta Page Route", "881000"))

	def test_release_frees_the_page_for_another_site(self):
		frappe.local.conf["meta_relay_secret"] = "shared"
		site = frappe.utils.get_url().rstrip("/")
		frappe.get_doc({"doctype": "Meta Page Route", "page_id": "881100", "site_url": site}).insert(
			ignore_permissions=True
		)

		ts = str(int(__import__("time").time()))
		signature = R.sign(f"release|881100|{site}|{ts}".encode())
		response = R.unregister_page_route("881100", site, ts, signature)
		self.assertEqual(response.status_code, 200)
		self.assertFalse(frappe.db.exists("Meta Page Route", "881100"))

	def test_release_refuses_another_site_route(self):
		frappe.local.conf["meta_relay_secret"] = "shared"
		frappe.get_doc(
			{"doctype": "Meta Page Route", "page_id": "881200", "site_url": "https://primo.it"}
		).insert(ignore_permissions=True)

		ts = str(int(__import__("time").time()))
		signature = R.sign(f"release|881200|https://ladro.it|{ts}".encode())
		response = R.unregister_page_route("881200", "https://ladro.it", ts, signature)
		self.assertEqual(response.status_code, 409)
		self.assertTrue(frappe.db.exists("Meta Page Route", "881200"))

	def test_a_claim_signature_cannot_be_replayed_as_a_release(self):
		frappe.local.conf["meta_relay_secret"] = "shared"
		site = frappe.utils.get_url().rstrip("/")
		frappe.get_doc({"doctype": "Meta Page Route", "page_id": "881300", "site_url": site}).insert(
			ignore_permissions=True
		)

		ts = str(int(__import__("time").time()))
		claim_signature = R.sign(f"881300|{site}|{ts}".encode())
		response = R.unregister_page_route("881300", site, ts, claim_signature)
		self.assertEqual(response.status_code, 403)
		self.assertTrue(frappe.db.exists("Meta Page Route", "881300"))

	def test_route_for_returns_other_site(self):
		frappe.get_doc(
			{"doctype": "Meta Page Route", "page_id": "880888", "site_url": "https://cliente.it/"}
		).insert(ignore_permissions=True)
		self.assertEqual(R.route_for("880888"), "https://cliente.it")
