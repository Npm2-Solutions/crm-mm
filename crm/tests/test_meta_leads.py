# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import hashlib
import hmac
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.lead import find_person
from crm.integrations.meta import api
from crm.integrations.meta import leads as L
from crm.integrations.meta import relay as R
from crm.integrations.meta import webhook as W
from crm.integrations.meta.leads import (
	already_stored,
	describe_ad,
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


def _forget_user_token():
	settings = frappe.get_doc("CRM Meta Settings")
	settings.user_access_token = ""
	settings.save(ignore_permissions=True)


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

	def test_the_ad_is_named_not_numbered(self):
		"""A lead arrives with an ad id and nothing else, so the record could
		only say "ad 120210…" — true and useless."""
		make_form()
		lead = sample_lead("7770801")
		lead["ad_id"] = "120210999"

		described = {
			"name": "Promo Autunno",
			"adset": {"name": "Milano 25-45"},
			"campaign": {"id": "23850", "name": "Lead Settembre"},
		}
		with patch.object(L, "graph_get", return_value=described):
			store_lead(lead, "990001", token="page-token")

		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7770801"}, "name")
		doc = frappe.get_doc("CRM Lead", person)
		self.assertEqual(doc.first_touch_campaign, "Lead Settembre")
		self.assertEqual(doc.first_touch_content, "Promo Autunno")
		self.assertEqual(doc.first_touch_term, "Milano 25-45")

	def test_the_same_ad_is_asked_about_once(self):
		"""Many leads come from one ad and the answer does not change between
		them: a backfill must not ask Meta the same question a hundred times."""
		make_form()
		described = {"name": "Promo", "campaign": {"id": "1", "name": "Camp"}}

		with patch.object(L, "graph_get", return_value=described) as graph_get:
			for leadgen_id in ("7770901", "7770902", "7770903"):
				lead = sample_lead(leadgen_id)
				lead["ad_id"] = "120211000"
				lead["email"] = f"{leadgen_id}@example.com"
				store_lead(lead, "990001", token="page-token")

		self.assertEqual(graph_get.call_count, 1)
		self.assertEqual(frappe.db.get_value("Facebook Ad", "120211000", "ad_name"), "Promo")

	def test_the_lead_already_knows_the_name_of_its_ad(self):
		"""Meta puts ad_name/campaign_name on the lead itself, next to ad_id.
		That is one call instead of two, and it needs no ads token at all."""
		make_form()
		lead = sample_lead("7771401")
		lead.update(
			{
				"ad_id": "120211004",
				"ad_name": "Promo Autunno",
				"adset_name": "Milano 25-45",
				"campaign_id": "23850",
				"campaign_name": "Lead Settembre",
			}
		)

		with patch.object(L, "graph_get") as graph_get:
			store_lead(lead, "990001", token="page-token")
		graph_get.assert_not_called()

		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7771401"}, "name")
		doc = frappe.get_doc("CRM Lead", person)
		self.assertEqual(doc.first_touch_campaign, "Lead Settembre")
		self.assertEqual(doc.first_touch_term, "Milano 25-45")
		self.assertEqual(doc.first_touch_content, "Promo Autunno")

	def test_the_names_are_asked_for_with_the_lead(self):
		"""If we never ask, Meta never tells: the fields have to be in `fields`."""
		make_form()
		with patch.object(L, "graph_get", return_value=sample_lead("7771501")) as graph_get:
			L.fetch_lead("7771501", "page-token")
		asked = graph_get.call_args.args[2]["fields"]
		for field in ("ad_name", "adset_name", "campaign_name"):
			self.assertIn(field, asked)

	def test_an_unknown_field_does_not_cost_the_lead(self):
		"""An older Graph version refuses a field it does not know. Then we ask
		for less — never nothing."""
		make_form()
		answers = [
			L.MetaAPIError("unknown field", code=100),
			L.MetaAPIError("unknown field", code=100),
			sample_lead("7771601"),
		]
		with patch.object(L, "graph_get", side_effect=answers) as graph_get:
			self.assertEqual(L.fetch_lead("7771601", "page-token")["id"], "7771601")
		self.assertEqual(graph_get.call_count, 3)
		self.assertEqual(graph_get.call_args.args[2]["fields"], L.LEAD_FIELDS)

	def test_the_ad_is_asked_with_the_ads_token(self):
		"""The lead arrives on a page token, but an ad belongs to the ad account:
		only the user token carries ads_management, so that is the one that asks.
		Asking with the page token spent a call to be refused, every time."""
		make_form()
		settings = frappe.get_doc("CRM Meta Settings")
		settings.user_access_token = "user-token"
		settings.save(ignore_permissions=True)
		self.addCleanup(_forget_user_token)

		lead = sample_lead("7771201")
		lead["ad_id"] = "120211002"
		with patch.object(L, "graph_get", return_value={"name": "Promo"}) as graph_get:
			store_lead(lead, "990001", token="page-token")

		self.assertEqual(graph_get.call_args.args[1], "user-token")

	def test_the_page_token_is_the_fallback(self):
		"""No user token — expired, or a site connected before it was stored —
		is a reason to try anyway, not to give up on the name."""
		make_form()
		_forget_user_token()

		lead = sample_lead("7771301")
		lead["ad_id"] = "120211003"
		with patch.object(L, "graph_get", return_value={"name": "Promo"}) as graph_get:
			store_lead(lead, "990001", token="page-token")

		self.assertEqual(graph_get.call_args.args[1], "page-token")

	def test_a_refused_ad_does_not_cost_the_lead(self):
		"""Even the right token can be refused: whoever connected Facebook may
		not advertise on that account. A lead is worth more than its ad name."""
		make_form()
		lead = sample_lead("7771001")
		lead["ad_id"] = "120211001"

		with patch.object(L, "graph_get", side_effect=L.MetaAPIError("no permission")):
			self.assertEqual(store_lead(lead, "990001", token="page-token"), "created")

		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7771001"}, "name")
		# the id is the fallback: worse than a name, better than nothing
		self.assertEqual(frappe.db.get_value("CRM Lead", person, "first_touch_content"), "120211001")
		self.assertTrue(frappe.db.get_value("Facebook Ad", "120211001", "unreadable"))

		# and it is not asked again
		with patch.object(L, "graph_get") as graph_get:
			self.assertEqual(describe_ad("120211001", "page-token"), {})
		graph_get.assert_not_called()

	def test_an_organic_lead_asks_nobody(self):
		"""There is no ad behind it, so there is nothing to name."""
		make_form()
		lead = sample_lead("7771101")
		lead["is_organic"] = True
		lead["ad_id"] = ""

		with patch.object(L, "graph_get") as graph_get:
			store_lead(lead, "990001", token="page-token")
		graph_get.assert_not_called()

		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7771101"}, "name")
		self.assertEqual(frappe.db.get_value("CRM Lead", person, "first_touch_category"), "Organic Social")

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


class TestMetaPermissions(IntegrationTestCase):
	"""What the login dialog granted, and what it quietly did not."""

	def tearDown(self):
		frappe.db.rollback()
		frappe.clear_cache(doctype="CRM Meta Settings")

	def _record(self, granted: str):
		settings = frappe.get_doc("CRM Meta Settings")
		settings.granted_scopes = granted
		settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype="CRM Meta Settings")

	def test_a_missing_permission_is_named(self):
		"""Meta's own error names six permissions without saying which one is
		missing. This says which one."""
		from crm.integrations.meta.oauth import missing_scopes

		self._record("pages_show_list,leads_retrieval,public_profile")
		missing = missing_scopes()
		self.assertIn("pages_manage_metadata", missing)
		self.assertIn("pages_read_engagement", missing)
		self.assertNotIn("pages_show_list", missing)

	def test_a_complete_grant_complains_about_nothing(self):
		from crm.integrations.meta.oauth import SCOPES, missing_scopes

		self._record(",".join(SCOPES))
		self.assertEqual(missing_scopes(), [])

	def test_silence_is_not_an_accusation(self):
		"""A connection made before we recorded this, and no token to ask with,
		must not be reported as missing everything."""
		from crm.integrations.meta.oauth import missing_scopes

		settings = frappe.get_doc("CRM Meta Settings")
		settings.granted_scopes = ""
		settings.user_access_token = ""
		settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype="CRM Meta Settings")

		self.assertEqual(missing_scopes(), [])

	def test_the_login_survives_a_failed_diagnosis(self):
		"""Reading the scopes is a diagnostic. A diagnostic may not cost anybody
		their connection."""
		from crm.integrations.meta import oauth as O

		with patch.object(O, "debug_token", side_effect=Exception("nope"), create=True):
			self.assertEqual(O.granted_scopes("tok"), [])


class TestMetaPageGrants(IntegrationTestCase):
	"""A Page kept without being granted has to say so."""

	def tearDown(self):
		frappe.db.rollback()

	def test_a_page_left_out_of_the_login_is_flagged(self):
		"""It survives because somebody switched it on, but nothing works on it
		and reconnecting blindly does not help."""
		from crm.integrations.meta.oauth import mark_ungranted_pages

		make_form(form_id="990500", page_id="880500")
		frappe.db.set_value("Facebook Page", "880500", "sync_enabled", 1)

		mark_ungranted_pages({"880999"})

		self.assertEqual(frappe.db.get_value("Facebook Page", "880500", "granted"), 0)
		self.assertEqual(frappe.db.get_value("Facebook Page", "880500", "token_valid"), 0)

	def test_a_page_that_came_back_is_granted_again(self):
		from crm.integrations.meta.oauth import mark_ungranted_pages

		make_form(form_id="990501", page_id="880501")
		frappe.db.set_value("Facebook Page", "880501", "granted", 0)

		mark_ungranted_pages({"880501"})

		self.assertEqual(frappe.db.get_value("Facebook Page", "880501", "granted"), 1)

	def test_the_error_says_why_and_what_to_do(self):
		"""'Reconnect Facebook' was true and useless: the dialog may not even
		offer that Page."""
		from crm.integrations.meta.api import no_token_message

		make_form(form_id="990502", page_id="880502")
		frappe.db.set_value("Facebook Page", "880502", "granted", 0)

		message = no_token_message("880502")
		self.assertIn("did not include this Page", message)
		self.assertIn("Business portfolio", message)


class TestMetaTimestamps(IntegrationTestCase):
	"""Meta's timestamps, and the day they took the imports down with them."""

	def tearDown(self):
		frappe.db.rollback()

	def test_the_offset_timestamp_is_accepted(self):
		"""Graph answers "2026-09-21T11:02:23+0000"; MariaDB refuses it outright,
		and it threw in the middle of saving the lead."""
		make_form()
		lead = sample_lead("7772001")
		lead["created_time"] = "2026-09-21T11:02:23+0000"

		self.assertEqual(store_lead(lead, "990001"), "created")

		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7772001"}, "name")
		row = frappe.get_doc("CRM Lead", person).facebook_submissions[0]
		self.assertTrue(row.submitted_on)
		# the instant is kept: 11:02 UTC is 13:02 in Rome, and the record is read
		# by somebody who lives in one timezone, not in UTC
		self.assertIn("2026-09-21", str(row.submitted_on))

	def test_an_unreadable_timestamp_does_not_cost_the_lead(self):
		make_form()
		lead = sample_lead("7772002")
		lead["created_time"] = "not a date at all"

		self.assertEqual(store_lead(lead, "990001"), "created")
		self.assertTrue(frappe.db.exists("CRM Lead", {"facebook_lead_id": "7772002"}))

	def test_a_failed_import_leaves_nothing_behind(self):
		"""Half a lead is worse than none: the person was in the CRM, the
		submission and the ledger row were not, and the reconciliation kept
		bringing it back."""
		make_form()
		lead = sample_lead("7772003")

		with patch.object(L, "record_import", side_effect=Exception("boom")):
			self.assertEqual(store_lead(lead, "990001"), "failed")

		self.assertFalse(frappe.db.exists("CRM Lead", {"facebook_lead_id": "7772003"}))
		self.assertTrue(frappe.db.exists("Failed Lead Sync Log", {"form": "990001"}))


class TestMetaTestLeads(IntegrationTestCase):
	"""Meta's own testing tool, which every App Review reviewer uses."""

	def tearDown(self):
		frappe.db.rollback()

	def test_the_dummy_answers_survive_the_sanitiser(self):
		"""The testing tool answers "<test lead: dummy data for nome>". Frappe
		sees a tag and removes it, so the name arrived empty and the lead died
		on a mandatory field — blaming Meta for a name Meta had sent."""
		make_form()
		lead = sample_lead("7773001")
		lead["field_data"] = [
			{"name": "full_name", "values": ["<test lead: dummy data for full_name>"]},
			{"name": "email", "values": ["<test lead: dummy data for email>"]},
			{"name": "phone_number", "values": ["<test lead: dummy data for phone_number>"]},
		]

		self.assertEqual(store_lead(lead, "990001"), "created")

		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7773001"}, "name")
		self.assertTrue(frappe.db.get_value("CRM Lead", person, "first_name"))

	def test_angle_brackets_never_eat_an_answer(self):
		"""Anything else arriving wrapped in brackets would vanish just as
		quietly: keep the text, lose the brackets."""
		self.assertEqual(normalize_value("first_name", "<Mario>"), "Mario")
		self.assertEqual(normalize_value("first_name", "Mario"), "Mario")

	def test_a_real_answer_is_left_alone(self):
		self.assertEqual(normalize_value("first_name", "  Mario  "), "Mario")
		self.assertEqual(normalize_value("mobile_no", "p:+39 333 1234567"), "+393331234567")


class TestMetaSyncResilience(IntegrationTestCase):
	"""One page, or one form, must never cost all the others."""

	def tearDown(self):
		frappe.db.rollback()

	def test_a_form_name_longer_than_the_column_is_cut(self):
		"""A lead form can be named with a whole advertisement, and a Data column
		refuses anything past 140 characters — which used to raise inside the
		page sync and take the whole sync down with it."""
		from crm.integrations.meta.oauth import short

		long_name = (
			"Grazie per l'interesse! Per accedere al beneficio, prosegui. "
			"Trattamento osteopatico avanzato a soli 59 euro anziche 80, "
			"nessun vincolo a proseguire, rispondi di seguito per sbloccare l'offerta"
		)
		cut = short(long_name)
		self.assertLessEqual(len(cut), 140)
		self.assertTrue(cut.endswith("…"))
		self.assertTrue(cut.startswith("Grazie per l'interesse!"))

	def test_a_short_name_is_left_exactly_as_it_is(self):
		from crm.integrations.meta.oauth import short

		self.assertEqual(short("Modulo contatti"), "Modulo contatti")
		self.assertEqual(short(None), "")

	def test_one_bad_page_does_not_cost_the_others_their_token(self):
		"""This is why pages ended up without a token: the loop stopped at the
		first exception and every page after it was never stored."""
		from crm.integrations.meta import oauth as O

		pages = [
			{"id": "880600", "name": "Prima", "access_token": "tok-1", "tasks": ["ADVERTISE"]},
			{"id": "880601", "name": "Seconda", "access_token": "tok-2", "tasks": ["ADVERTISE"]},
		]
		boom = {"count": 0}

		def explode_on_the_first(page_id, token):
			boom["count"] += 1
			if page_id == "880600":
				raise ValueError("a form name nobody could store")
			return ""

		with (
			patch.object(O, "discover_pages", return_value=pages),
			patch.object(O, "sync_forms_recording_failure", side_effect=explode_on_the_first),
			patch.object(O, "forget_ungranted_pages"),
		):
			O.sync_pages_and_forms("user-token")

		# the second page still has its token, which is the whole point
		self.assertTrue(frappe.db.exists("Facebook Page", "880601"))
		self.assertEqual(boom["count"], 2)


class TestMetaUnusableAnswers(IntegrationTestCase):
	"""An answer that cannot go in its field must not cost the whole person."""

	def tearDown(self):
		frappe.db.rollback()

	def test_a_phone_that_is_not_a_phone_does_not_kill_the_lead(self):
		"""Frappe refuses "Test" as a phone number and raises on save. That is
		how every test lead died the moment it stopped being eaten by the
		sanitiser."""
		make_form()
		lead = sample_lead("7774001")
		lead["field_data"] = [
			{"name": "full_name", "values": ["<test lead: dummy data for full_name>"]},
			{"name": "phone_number", "values": ["<test lead: dummy data for phone_number>"]},
			{"name": "email", "values": ["<test lead: dummy data for email>"]},
		]

		self.assertEqual(store_lead(lead, "990001"), "created")

		person = frappe.db.get_value("CRM Lead", {"facebook_lead_id": "7774001"}, "name")
		doc = frappe.get_doc("CRM Lead", person)
		self.assertTrue(doc.first_name)
		self.assertFalse(doc.mobile_no)
		self.assertFalse(doc.email)

	def test_a_real_phone_is_still_a_phone(self):
		self.assertEqual(normalize_value("mobile_no", "p:+39 333 1234567"), "+393331234567")
		self.assertEqual(normalize_value("mobile_no", "Test"), "")
		self.assertEqual(normalize_value("email", "mario@example.com"), "mario@example.com")
		self.assertEqual(normalize_value("email", "Test"), "")
