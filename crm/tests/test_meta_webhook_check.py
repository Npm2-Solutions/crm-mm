# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.meta.api import get_webhook_subscription


class TestWebhookCheck(IntegrationTestCase):
	"""The settings page asks for the webhook as soon as an administrator opens
	it, with or without a Meta app: no app is an answer, not an error."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_no_app_is_an_answer_not_an_error(self):
		with (
			patch("crm.integrations.meta.api.is_hub", return_value=True),
			patch("crm.integrations.meta.api.get_app_id", return_value=""),
			patch("crm.integrations.meta.api.get_app_secret", return_value=""),
			patch("crm.integrations.meta.api.graph_get") as graph,
		):
			result = get_webhook_subscription()
		self.assertEqual(result, {"configured": False, "app_missing": True})
		graph.assert_not_called()

	def test_with_an_app_meta_is_asked(self):
		subscriptions = {"data": [{"object": "page", "active": True, "fields": [{"name": "leadgen"}]}]}
		with (
			patch("crm.integrations.meta.api.is_hub", return_value=True),
			patch("crm.integrations.meta.api.get_app_id", return_value="123"),
			patch("crm.integrations.meta.api.get_app_secret", return_value="secret"),
			patch("crm.integrations.meta.api.graph_get", return_value=subscriptions) as graph,
		):
			result = get_webhook_subscription()
		graph.assert_called_once()
		self.assertTrue(result["configured"])
