# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import social as S
from crm.social.accounts import sync_from_facebook_pages, upsert_account
from crm.social.publisher import process_due_posts


def make_account(name="Test FB", platform="Facebook"):
	if frappe.db.exists("CRM Social Account", name):
		return frappe.get_doc("CRM Social Account", name)
	return frappe.get_doc(
		{"doctype": "CRM Social Account", "account_name": name, "platform": platform, "enabled": 1}
	).insert()


class TestSocialPlanner(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_save_requires_content_and_targets(self):
		make_account()
		with self.assertRaises(frappe.ValidationError):
			S.save_post({"content": "hello", "targets": []})
		with self.assertRaises(frappe.ValidationError):
			S.save_post({"content": "  ", "targets": [{"account": "Test FB"}]})

	def test_schedule_requires_datetime(self):
		make_account()
		with self.assertRaises(frappe.ValidationError):
			S.save_post({"content": "ciao", "status": "Scheduled", "targets": [{"account": "Test FB"}]})

	def test_due_post_is_published(self):
		make_account()
		result = S.save_post(
			{
				"content": "post di prova",
				"status": "Scheduled",
				"scheduled_at": frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-1),
				"targets": [{"account": "Test FB"}],
			}
		)
		with patch("crm.social.publisher.publish_target", return_value="fb_1"):
			process_due_posts()
		doc = frappe.get_doc("CRM Social Post", result["name"])
		self.assertEqual(doc.status, "Published")
		self.assertEqual(doc.targets[0].status, "Published")
		self.assertEqual(doc.targets[0].provider_post_id, "fb_1")
		self.assertTrue(doc.published_at)

	def test_failed_target_marks_post_failed_with_error(self):
		make_account()
		result = S.save_post(
			{
				"content": "fallisce",
				"status": "Scheduled",
				"scheduled_at": frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-1),
				"targets": [{"account": "Test FB"}],
			}
		)
		with patch("crm.social.publisher.publish_target", side_effect=Exception("token scaduto")):
			process_due_posts()
		doc = frappe.get_doc("CRM Social Post", result["name"])
		self.assertEqual(doc.status, "Failed")
		self.assertEqual(doc.targets[0].status, "Failed")
		self.assertIn("token scaduto", doc.targets[0].error)

	def test_recurrence_clones_next_occurrence(self):
		make_account()
		result = S.save_post(
			{
				"content": "ricorrente",
				"status": "Scheduled",
				"recurrence": "Weekly",
				"scheduled_at": frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-1),
				"targets": [{"account": "Test FB"}],
			}
		)
		with patch("crm.social.publisher.publish_target", return_value="fb_2"):
			process_due_posts()
		clones = frappe.get_all(
			"CRM Social Post", filters={"content": "ricorrente", "status": "Scheduled"}, pluck="name"
		)
		self.assertEqual(len(clones), 1)
		self.assertNotEqual(clones[0], result["name"])

	def test_cancel_post(self):
		make_account()
		result = S.save_post({"content": "bozza", "targets": [{"account": "Test FB"}]})
		S.cancel_post(result["name"])
		self.assertEqual(frappe.db.get_value("CRM Social Post", result["name"], "status"), "Cancelled")

	def test_upsert_account_matches_by_provider_id(self):
		self.assertEqual(upsert_account("Facebook", "111", "Pagina Uno"), "created")
		self.assertEqual(upsert_account("Facebook", "111", "Pagina Uno"), "updated")
		self.assertEqual(
			frappe.db.count("CRM Social Account", {"platform": "Facebook", "provider_account_id": "111"}),
			1,
		)

	def test_sync_from_facebook_pages_creates_fb_and_ig_profiles(self):
		if not frappe.db.exists("Facebook Page", "5550001"):
			frappe.get_doc(
				{
					"doctype": "Facebook Page",
					"id": "5550001",
					"page_name": "Agenzia Demo",
					"instagram_account_id": "17840000001",
					"instagram_username": "agenzia.demo",
				}
			).insert(ignore_permissions=True)

		result = sync_from_facebook_pages()
		self.assertGreaterEqual(result["created"] + result["updated"], 2)
		fb = frappe.db.get_value(
			"CRM Social Account",
			{"platform": "Facebook", "provider_account_id": "5550001"},
			["account_name", "facebook_page"],
			as_dict=True,
		)
		self.assertEqual(fb.account_name, "Agenzia Demo")
		self.assertEqual(fb.facebook_page, "5550001")
		ig = frappe.db.get_value(
			"CRM Social Account",
			{"platform": "Instagram", "provider_account_id": "17840000001"},
			["account_name", "facebook_page"],
			as_dict=True,
		)
		self.assertEqual(ig.account_name, "@agenzia.demo")
		self.assertEqual(ig.facebook_page, "5550001")
		# idempotent
		again = sync_from_facebook_pages()
		self.assertEqual(again["created"], 0)

	def test_instagram_without_media_fails(self):
		account = make_account("Test IG", "Instagram")
		account.provider_account_id = "17840000009"
		account.facebook_page = None
		account.save()
		result = S.save_post(
			{
				"content": "senza media",
				"status": "Scheduled",
				"scheduled_at": frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-1),
				"targets": [{"account": "Test IG"}],
			}
		)
		process_due_posts()
		doc = frappe.get_doc("CRM Social Post", result["name"])
		self.assertEqual(doc.status, "Failed")
		self.assertTrue(doc.targets[0].error)


class TestSocialPlannerRoles(IntegrationTestCase):
	"""Who may put a post on the schedule, and who reads why it failed."""

	MANAGER = "crm.manager@example.com"
	USER = "crm.user1@example.com"

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def post(self, **values):
		return frappe.get_doc(
			{
				"doctype": "CRM Social Post",
				"content": "ciao",
				"scheduled_at": frappe.utils.add_to_date(frappe.utils.now_datetime(), days=1),
				"targets": [{"account": "Test FB"}],
				**values,
			}
		)

	def test_a_user_cannot_schedule_past_the_approval(self):
		"""The doctype is writable by Sales Users: a post saved over the REST API,
		without `save_post`, went on the schedule with nobody approving it."""
		make_account()
		frappe.set_user(self.USER)
		doc = self.post(status="Scheduled").insert()
		self.assertEqual(doc.status, "Pending Approval")
		self.assertEqual(doc.requested_by, self.USER)

	def test_an_approved_post_edited_by_a_user_goes_back_for_approval(self):
		make_account()
		doc = self.post(status="Scheduled").insert()
		self.assertEqual(doc.status, "Scheduled")

		frappe.set_user(self.USER)
		doc = frappe.get_doc("CRM Social Post", doc.name)
		doc.content = "altro testo"
		doc.save()
		self.assertEqual(doc.status, "Pending Approval")
		self.assertFalse(doc.approved_by)

	def test_a_manager_schedules(self):
		make_account()
		frappe.set_user(self.MANAGER)
		doc = self.post(status="Scheduled").insert()
		self.assertEqual(doc.status, "Scheduled")

	def test_why_a_post_failed_is_for_managers_and_never_holds_a_token(self):
		make_account()
		doc = self.post(status="Failed").insert()
		doc.targets[0].status = "Failed"
		doc.targets[0].error = "Meta: Network error, url: /v23.0/1/feed?access_token=SECRET"
		doc.save()
		start = frappe.utils.add_to_date(frappe.utils.now_datetime(), days=-1)
		end = frappe.utils.add_to_date(frappe.utils.now_datetime(), days=2)

		def error_seen_by(user):
			frappe.set_user(user)
			rows = S.get_posts(str(start), str(end))
			return next(r for r in rows if r.name == doc.name)["targets"][0].error

		manager_sees = error_seen_by(self.MANAGER)
		self.assertIn("Network error", manager_sees)
		self.assertNotIn("SECRET", manager_sees)
		user_sees = error_seen_by(self.USER)
		self.assertNotIn("Network error", user_sees)
		self.assertNotIn("SECRET", user_sees)
