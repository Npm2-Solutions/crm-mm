# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Lead tracking, end to end: a beacon arrives, a lead comes out attributed."""

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from crm.api import tracking as T
from crm.fcrm.doctype.crm_visitor.crm_visitor import get_or_create as get_visitor
from crm.fcrm.doctype.crm_visitor_session.crm_visitor_session import start_or_continue

CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"


def set_request(body: dict | None = None, headers: dict | None = None, method: str = "POST"):
	"""Put a real request on `frappe.local` so the guest endpoint can read it."""
	builder = EnvironBuilder(
		method=method,
		path="/api/method/crm.api.tracking.collect",
		data=json.dumps(body or {}),
		content_type="text/plain",
		headers={"User-Agent": CHROME, **(headers or {})},
	)
	frappe.local.request = Request(builder.get_environ())
	frappe.local.request_ip = "203.0.113.7"
	return frappe.local.request


def beacon(events, vid=None, sid=None, **kwargs):
	set_request({"vid": vid, "sid": sid, "events": events, **kwargs})
	return T.collect()


def page_view(url, referrer=""):
	return {"type": "page_view", "url": url, "referrer": referrer, "title": "Prezzi"}


def new_lead(**kwargs):
	"""An uninserted lead — the shape every tracked entry point builds before it
	calls `attribute()`."""
	return frappe.get_doc({"doctype": "CRM Lead", "first_name": "Giulia", "status": "New", **kwargs})


def make_lead(**kwargs):
	return new_lead(**kwargs).insert(ignore_permissions=True)


def tracked_lead(vid, sid, **kwargs):
	"""A lead created the way the real entry points create one: attributed while
	still in memory, so the source is part of the inserted row."""
	lead = new_lead(**kwargs)
	T.attribute(lead, visitor_id=vid, session_id=sid)
	return lead.insert(ignore_permissions=True)


def set_settings(**values):
	for key, value in values.items():
		frappe.db.set_single_value("CRM Tracking Settings", key, value)
	frappe.clear_document_cache("CRM Tracking Settings", "CRM Tracking Settings")


class TrackingTestCase(IntegrationTestCase):
	def setUp(self):
		frappe.local.request = None
		set_settings(enabled=1, track_anonymous=1, exclude_bots=1, require_consent=0, allowed_origins="")

	def tearDown(self):
		frappe.local.request = None
		frappe.set_user("Administrator")
		frappe.db.rollback()
		frappe.clear_document_cache("CRM Tracking Settings", "CRM Tracking Settings")


class TestCollect(TrackingTestCase):
	def test_first_beacon_creates_visitor_session_and_event(self):
		result = beacon([page_view("https://example.it/prezzi?utm_source=newsletter&utm_medium=email")])

		self.assertTrue(result["ok"])
		self.assertTrue(frappe.db.exists("CRM Visitor", result["vid"]))

		session = frappe.get_doc("CRM Visitor Session", {"session_id": result["sid"]})
		self.assertEqual(session.source_category, "Email")
		self.assertEqual(session.utm_source, "newsletter")
		self.assertEqual(session.page_view_count, 1)
		self.assertEqual(session.device_type, "Desktop")

		event = frappe.get_doc("CRM Tracking Event", {"session": session.name})
		self.assertEqual(event.event_type, "Page View")
		self.assertEqual(event.path, "/prezzi?utm_source=newsletter&utm_medium=email")

	def test_second_beacon_continues_the_same_session(self):
		first = beacon([page_view("https://example.it/")])
		second = beacon([page_view("https://example.it/prezzi")], vid=first["vid"], sid=first["sid"])

		self.assertEqual(second["vid"], first["vid"])
		self.assertEqual(second["sid"], first["sid"])
		self.assertEqual(frappe.db.count("CRM Visitor Session", {"visitor": first["vid"]}), 1)
		self.assertEqual(
			frappe.db.get_value("CRM Visitor Session", {"session_id": first["sid"]}, "page_view_count"), 2
		)

	def test_a_new_campaign_starts_a_new_session(self):
		"""Someone mid-visit who clicks an ad has started something new; crediting
		that click to the session already running would lose it."""
		first = beacon([page_view("https://example.it/")])
		second = beacon(
			[page_view("https://example.it/offerta?utm_source=adwords&utm_medium=cpc&gclid=xyz")],
			vid=first["vid"],
			sid=first["sid"],
		)

		self.assertNotEqual(second["sid"], first["sid"])
		self.assertEqual(frappe.db.count("CRM Visitor Session", {"visitor": first["vid"]}), 2)
		new_session = frappe.get_doc("CRM Visitor Session", {"session_id": second["sid"]})
		self.assertEqual(new_session.source_category, "Paid Search")
		self.assertEqual(new_session.gclid, "xyz")

	def test_counters_are_written_once_per_beacon(self):
		result = beacon(
			[
				page_view("https://example.it/"),
				page_view("https://example.it/prezzi"),
				{"type": "link_click", "url": "tel:+39055", "label": "Chiama"},
			]
		)
		session = frappe.get_doc("CRM Visitor Session", {"session_id": result["sid"]})
		self.assertEqual(session.page_view_count, 2)
		self.assertEqual(session.event_count, 3)
		self.assertEqual(frappe.db.get_value("CRM Visitor", result["vid"], "page_view_count"), 2)

	def test_unknown_event_types_are_dropped(self):
		result = beacon([{"type": "definitely_not_an_event", "url": "https://example.it/"}])
		self.assertEqual(frappe.db.count("CRM Tracking Event", {"visitor": result["vid"]}), 0)

	def test_a_forged_visitor_id_is_replaced_not_trusted(self):
		"""Ids are minted server-side; anything else gets a fresh one."""
		result = beacon([page_view("https://example.it/")], vid="../../etc/passwd")
		self.assertNotEqual(result["vid"], "../../etc/passwd")
		self.assertEqual(len(result["vid"]), 32)

	def test_beacon_is_capped(self):
		events = [page_view(f"https://example.it/{i}") for i in range(50)]
		result = beacon(events)
		self.assertEqual(
			frappe.db.count("CRM Tracking Event", {"visitor": result["vid"]}), T.MAX_EVENTS_PER_BEACON
		)

	# -- the gates --

	def test_disabled_collects_nothing(self):
		set_settings(enabled=0)
		self.assertFalse(beacon([page_view("https://example.it/")])["ok"])
		self.assertEqual(frappe.db.count("CRM Visitor Session"), 0)

	def test_bots_are_ignored(self):
		set_request({"events": [page_view("https://example.it/")]}, headers={"User-Agent": "Googlebot/2.1"})
		self.assertFalse(T.collect()["ok"])

	def test_do_not_track_is_respected(self):
		set_settings(respect_do_not_track=1)
		set_request({"events": [page_view("https://example.it/")]}, headers={"DNT": "1"})
		self.assertFalse(T.collect()["ok"])

	def test_consent_is_required_when_configured(self):
		set_settings(require_consent=1)
		self.assertFalse(beacon([page_view("https://example.it/")])["ok"])
		self.assertTrue(beacon([page_view("https://example.it/")], consent=True)["ok"])

	def test_an_origin_outside_the_allow_list_is_refused(self):
		set_settings(allowed_origins="https://example.it")
		set_request({"events": [page_view("https://altrove.it/")]}, headers={"Origin": "https://altrove.it"})
		self.assertFalse(T.collect()["ok"])

		set_request({"events": [page_view("https://example.it/")]}, headers={"Origin": "https://example.it"})
		self.assertTrue(T.collect()["ok"])

	def test_a_subdomain_of_an_allowed_origin_is_accepted(self):
		set_settings(allowed_origins="https://example.it")
		set_request(
			{"events": [page_view("https://shop.example.it/")]},
			headers={"Origin": "https://shop.example.it"},
		)
		self.assertTrue(T.collect()["ok"])

	def test_excluded_ip_is_ignored(self):
		set_settings(excluded_ips="203.0.113.0", anonymize_ip=1)
		self.assertFalse(beacon([page_view("https://example.it/")])["ok"])

	def test_ip_is_anonymised_by_default(self):
		result = beacon([page_view("https://example.it/")])
		self.assertEqual(
			frappe.db.get_value("CRM Visitor Session", {"session_id": result["sid"]}, "ip_address"),
			"203.0.113.0",
		)


class TestAttribution(TrackingTestCase):
	def track(self, url, referrer=""):
		result = beacon([page_view(url, referrer)])
		frappe.local.request = None
		return result

	def test_a_lead_takes_the_visit_that_produced_it(self):
		ids = self.track("https://example.it/prezzi?utm_source=adwords&utm_medium=cpc&utm_campaign=estate")
		lead = tracked_lead(ids["vid"], ids["sid"])

		self.assertEqual(lead.first_touch_category, "Paid Search")
		self.assertEqual(lead.first_touch_source, "adwords")
		self.assertEqual(lead.first_touch_campaign, "estate")
		self.assertEqual(lead.last_touch_category, "Paid Search")
		self.assertEqual(lead.visitor, ids["vid"])

	def test_first_touch_survives_a_later_visit(self):
		"""The campaign that introduced someone cannot be claimed by a later one."""
		first = self.track("https://example.it/?utm_source=adwords&utm_medium=cpc")
		lead = tracked_lead(first["vid"], first["sid"])

		# same browser, new campaign → new session
		second = beacon(
			[page_view("https://example.it/?utm_source=newsletter&utm_medium=email")],
			vid=first["vid"],
			sid=first["sid"],
		)
		frappe.local.request = None
		T.attribute(lead, visitor_id=first["vid"], session_id=second["sid"])
		lead.reload()

		self.assertEqual(lead.first_touch_category, "Paid Search")
		self.assertEqual(lead.first_touch_source, "adwords")
		self.assertEqual(lead.last_touch_category, "Email")
		self.assertEqual(lead.last_touch_source, "newsletter")

	def test_identifying_backfills_the_whole_history(self):
		"""The pages read before the form was ever submitted are the point."""
		ids = self.track("https://example.it/prezzi")
		beacon([page_view("https://example.it/casi-studio")], vid=ids["vid"], sid=ids["sid"])
		frappe.local.request = None

		lead = tracked_lead(ids["vid"], ids["sid"])

		self.assertEqual(frappe.db.count("CRM Tracking Event", {"lead": lead.name}), 2)
		self.assertEqual(frappe.db.count("CRM Visitor Session", {"lead": lead.name}), 1)
		self.assertEqual(frappe.db.get_value("CRM Visitor", ids["vid"], "status"), "Identified")

	def test_a_visitor_already_bound_is_not_stolen(self):
		"""Two people on one browser: the second submission must not hand the
		first one's history to a different lead."""
		ids = self.track("https://example.it/")
		first_lead = tracked_lead(ids["vid"], ids["sid"], first_name="Anna")
		tracked_lead(ids["vid"], ids["sid"], first_name="Marco")

		self.assertEqual(frappe.db.get_value("CRM Visitor", ids["vid"], "lead"), first_lead.name)

	def test_an_origin_with_no_session_still_gets_a_source(self):
		lead = new_lead()
		T.attribute(
			lead,
			category="Paid Social",
			dimensions={"source": "facebook", "medium": "paid_social", "campaign": "Lead Ads"},
		)
		lead.insert(ignore_permissions=True)
		self.assertEqual(lead.first_touch_category, "Paid Social")
		self.assertEqual(lead.first_touch_source, "facebook")
		self.assertEqual(lead.first_touch_campaign, "Lead Ads")

	def test_a_lead_typed_into_the_crm_is_attributed_to_the_crm(self):
		lead = make_lead()
		self.assertEqual(lead.first_touch_category, "CRM UI")
		self.assertEqual(lead.last_touch_category, "CRM UI")

	def test_attribution_survives_conversion_to_a_deal(self):
		ids = self.track("https://example.it/?utm_source=adwords&utm_medium=cpc")
		lead = tracked_lead(ids["vid"], ids["sid"], email="giulia@example.it", last_name="Rossi")

		deal_name = lead.create_deal(contact=lead.create_contact(throw=False), organization=None)
		deal = frappe.get_doc("CRM Deal", deal_name)

		self.assertEqual(deal.first_touch_category, "Paid Search")
		self.assertEqual(deal.first_touch_source, "adwords")
		self.assertEqual(frappe.db.get_value("CRM Visitor", ids["vid"], "deal"), deal_name)
		self.assertEqual(frappe.db.count("CRM Tracking Event", {"deal": deal_name}), 1)

	def test_visitor_for_mints_one_when_the_record_has_none(self):
		lead = make_lead()
		visitor_id = T.visitor_for(lead)
		self.assertEqual(len(visitor_id), 32)
		self.assertEqual(frappe.db.get_value("CRM Visitor", visitor_id, "lead"), lead.name)
		# idempotent
		self.assertEqual(T.visitor_for(lead), visitor_id)


class TestJourney(TrackingTestCase):
	def test_journey_returns_the_snapshots_sessions_and_events(self):
		result = beacon([page_view("https://example.it/prezzi?utm_source=newsletter&utm_medium=email")])
		frappe.local.request = None
		lead = tracked_lead(result["vid"], result["sid"])

		journey = T.get_journey("CRM Lead", lead.name)
		self.assertEqual(journey["visitor"], result["vid"])
		self.assertEqual(journey["first_touch"]["category"], "Email")
		self.assertEqual(len(journey["sessions"]), 1)
		self.assertEqual(len(journey["events"]), 1)

	def test_journey_refuses_a_doctype_it_does_not_track(self):
		with self.assertRaises(frappe.ValidationError):
			T.get_journey("User", "Administrator")

	def test_source_report_groups_by_category(self):
		make_lead(first_name="A")
		make_lead(first_name="B")
		rows = T.source_report("CRM Lead", group_by="category")
		self.assertTrue(any(r["label"] == "CRM UI" and r["total"] >= 2 for r in rows))

	def test_source_report_rejects_an_arbitrary_group_by(self):
		with self.assertRaises(frappe.ValidationError):
			T.source_report("CRM Lead", group_by="password")


class TestRetention(TrackingTestCase):
	def _age(self, doctype, name, field, days):
		frappe.db.set_value(doctype, name, field, add_days(now(), -days), update_modified=False)

	def test_old_anonymous_traffic_is_purged(self):
		result = beacon([page_view("https://example.it/")])
		frappe.local.request = None
		set_settings(retention_days=30)

		session = frappe.db.get_value("CRM Visitor Session", {"session_id": result["sid"]}, "name")
		event = frappe.db.get_value("CRM Tracking Event", {"visitor": result["vid"]}, "name")
		self._age("CRM Tracking Event", event, "occurred_on", 60)
		self._age("CRM Visitor Session", session, "started_on", 60)
		self._age("CRM Visitor", result["vid"], "last_seen_on", 60)

		T.purge_old_data()

		self.assertFalse(frappe.db.exists("CRM Tracking Event", event))
		self.assertFalse(frappe.db.exists("CRM Visitor Session", session))
		self.assertFalse(frappe.db.exists("CRM Visitor", result["vid"]))

	def test_history_attached_to_a_lead_is_kept(self):
		"""Once it belongs to a lead it is CRM data, not traffic to tidy away."""
		result = beacon([page_view("https://example.it/")])
		frappe.local.request = None
		tracked_lead(result["vid"], result["sid"])
		set_settings(retention_days=30)

		session = frappe.db.get_value("CRM Visitor Session", {"session_id": result["sid"]}, "name")
		event = frappe.db.get_value("CRM Tracking Event", {"visitor": result["vid"]}, "name")
		self._age("CRM Tracking Event", event, "occurred_on", 60)
		self._age("CRM Visitor Session", session, "started_on", 60)
		self._age("CRM Visitor", result["vid"], "last_seen_on", 60)

		T.purge_old_data()

		self.assertTrue(frappe.db.exists("CRM Tracking Event", event))
		self.assertTrue(frappe.db.exists("CRM Visitor Session", session))
		self.assertTrue(frappe.db.exists("CRM Visitor", result["vid"]))

	def test_retention_zero_purges_nothing(self):
		result = beacon([page_view("https://example.it/")])
		frappe.local.request = None
		set_settings(retention_days=0)
		self._age("CRM Visitor", result["vid"], "last_seen_on", 5000)
		T.purge_old_data()
		self.assertTrue(frappe.db.exists("CRM Visitor", result["vid"]))


class TestSessionLifecycle(TrackingTestCase):
	def test_an_idle_session_is_replaced(self):
		visitor = get_visitor(frappe.generate_hash(length=32))
		first = start_or_continue(visitor, None, "https://example.it/", "", timeout_minutes=30)
		frappe.db.set_value(
			"CRM Visitor Session",
			first.name,
			"last_activity_on",
			add_days(now(), -1),
			update_modified=False,
		)
		visitor.reload()
		second = start_or_continue(
			visitor, first.session_id, "https://example.it/prezzi", "", timeout_minutes=30
		)
		self.assertNotEqual(second.name, first.name)

	def test_a_session_id_from_another_visitor_is_not_adopted(self):
		one = get_visitor(frappe.generate_hash(length=32))
		other = get_visitor(frappe.generate_hash(length=32))
		session = start_or_continue(one, None, "https://example.it/", "")

		stolen = start_or_continue(other, session.session_id, "https://example.it/", "")
		self.assertNotEqual(stolen.name, session.name)
		self.assertEqual(stolen.visitor, other.name)
