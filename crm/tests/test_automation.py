# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.automation import engine


def make_automation(title, steps, trigger_event="Lead Created", **kw):
	payload = {
		"doctype": "CRM Automation",
		"title": title,
		"enabled": 1,
		"trigger_event": trigger_event,
		"steps": json.dumps(steps),
	}
	payload.update(kw)
	return frappe.get_doc(payload).insert()


def make_lead(**kw):
	payload = {
		"doctype": "CRM Lead",
		"first_name": "Auto",
		"last_name": "Test",
		"email": "auto@example.com",
		"mobile_no": "+390000000001",
	}
	payload.update(kw)
	return frappe.get_doc(payload).insert()


def get_enrollment(automation, lead):
	name = frappe.db.get_value(
		"CRM Automation Enrollment",
		{"automation": automation, "reference_doctype": "CRM Lead", "reference_name": lead},
	)
	return frappe.get_doc("CRM Automation Enrollment", name) if name else None


class TestAutomation(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	# ---- validation ----

	def test_invalid_step_type_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_automation("bad-steps", [{"type": "explode"}])

	def test_wait_without_duration_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_automation("bad-wait", [{"type": "wait"}])

	def test_stop_if_requires_condition(self):
		with self.assertRaises(frappe.ValidationError):
			make_automation("bad-stop", [{"type": "stop_if"}])

	# ---- enrollment + execution ----

	def test_lead_created_enrolls_and_completes(self):
		auto = make_automation(
			"welcome-flow",
			[
				{"type": "add_tag_comment", "comment": "Ciao {{ first_name }}"},
				{"type": "notify", "message": "Nuovo lead {{ lead_name }}"},
			],
		)
		lead = make_lead()
		enr = get_enrollment(auto.name, lead.name)
		self.assertIsNotNone(enr)
		self.assertEqual(enr.status, "Completed")
		self.assertEqual(len(enr.logs), 2)
		self.assertEqual({log.status for log in enr.logs}, {"Success"})
		# the comment was rendered against the lead
		comment = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "CRM Lead", "reference_name": lead.name},
			pluck="content",
		)
		self.assertTrue(any("Auto" in c for c in comment))

	def test_wait_pauses_enrollment_and_scheduler_resumes(self):
		auto = make_automation(
			"drip-flow",
			[
				{"type": "add_tag_comment", "comment": "step 1"},
				{"type": "wait", "hours": 2},
				{"type": "add_tag_comment", "comment": "step 2"},
			],
		)
		lead = make_lead(email="drip@example.com")
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Waiting")
		self.assertEqual(enr.current_step, 1)
		self.assertIsNotNone(enr.wait_until)

		# force the wait to be due and tick the scheduler path
		enr.db_set("wait_until", frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-1))
		engine.advance_enrollment(enr.name)
		enr.reload()
		self.assertEqual(enr.status, "Completed")
		self.assertEqual(len(enr.logs), 2)

	def test_trigger_condition_filters_enrollment(self):
		auto = make_automation(
			"only-webform",
			[{"type": "add_tag_comment", "comment": "x"}],
			trigger_condition=json.dumps({"field": "email", "operator": "contains", "value": "@matchme.com"}),
		)
		lead = make_lead(email="nomatch@example.com")
		self.assertIsNone(get_enrollment(auto.name, lead.name))
		lead2 = make_lead(email="yes@matchme.com")
		self.assertIsNotNone(get_enrollment(auto.name, lead2.name))

	def test_no_reenrollment_by_default(self):
		auto = make_automation(
			"status-flow",
			[{"type": "add_tag_comment", "comment": "x"}],
			trigger_event="Lead Status Changed",
		)
		lead = make_lead()
		other_status = frappe.get_all(
			"CRM Lead Status", filters={"name": ["!=", lead.status]}, pluck="name", limit=1
		)
		self.assertTrue(other_status)
		lead.status = other_status[0]
		lead.save()
		first = get_enrollment(auto.name, lead.name)
		self.assertIsNotNone(first)
		lead.reload()
		lead.status = frappe.get_all(
			"CRM Lead Status", filters={"name": ["!=", lead.status]}, pluck="name", limit=1
		)[0]
		lead.save()
		count = frappe.db.count(
			"CRM Automation Enrollment",
			{"automation": auto.name, "reference_name": lead.name},
		)
		self.assertEqual(count, 1)

	def test_step_condition_skips(self):
		auto = make_automation(
			"conditional-step",
			[
				{
					"type": "add_tag_comment",
					"comment": "x",
					"condition": {"field": "email", "operator": "contains", "value": "@never.com"},
				}
			],
		)
		lead = make_lead()
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Completed")
		self.assertEqual(enr.logs[0].status, "Skipped")

	def test_stop_if_exits(self):
		auto = make_automation(
			"stop-flow",
			[
				{"type": "stop_if", "condition": {"field": "email", "operator": "is_set"}},
				{"type": "add_tag_comment", "comment": "never reached"},
			],
		)
		lead = make_lead()
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Exited")
		self.assertEqual(len(enr.logs), 1)

	def test_set_field_updates_reference(self):
		other_status = frappe.get_all("CRM Lead Status", pluck="name", limit=2)
		self.assertGreaterEqual(len(other_status), 2)
		auto = make_automation(
			"set-status",
			[{"type": "set_field", "field": "status", "value": other_status[1]}],
		)
		lead = make_lead(status=other_status[0])
		lead.reload()
		self.assertEqual(lead.status, other_status[1])
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Completed")

	def test_exit_on_reply(self):
		auto = make_automation(
			"reply-exit",
			[
				{"type": "add_tag_comment", "comment": "1"},
				{"type": "wait", "days": 1},
				{"type": "add_tag_comment", "comment": "2"},
			],
			exit_on_reply=1,
		)
		lead = make_lead(mobile_no="+390000000099")
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Waiting")

		sms = frappe.get_doc(
			{
				"doctype": "CRM SMS Message",
				"type": "Incoming",
				"from": "+390000000099",
				"to": "+390000000000",
				"message": "reply!",
				"status": "Received",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(sms)
		enr.reload()
		self.assertEqual(enr.status, "Exited")

	def test_failed_step_does_not_block_sequence(self):
		auto = make_automation(
			"resilient-flow",
			[
				{"type": "set_field", "field": "definitely_not_a_field", "value": "x"},
				{"type": "add_tag_comment", "comment": "still runs"},
			],
		)
		lead = make_lead()
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Completed")
		self.assertEqual(enr.logs[0].status, "Failed")
		self.assertEqual(enr.logs[1].status, "Success")


class TestAutomationV2(IntegrationTestCase):
	"""GHL-aligned blocks: branches, goal, tags, tracked links, webhook trigger."""

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_if_else_branching(self):
		auto = make_automation(
			"branch-flow",
			[
				{
					"type": "if_else",
					"branches": [
						{
							"condition_groups": [
								[{"field": "email", "operator": "contains", "value": "@vip.com"}]
							],
							"steps": [{"type": "add_note", "comment": "VIP"}],
						}
					],
					"else_steps": [{"type": "add_note", "comment": "standard"}],
				}
			],
		)
		lead = make_lead(email="boss@vip.com")
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Completed")
		comments = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "CRM Lead", "reference_name": lead.name},
			pluck="content",
		)
		self.assertTrue(any("VIP" in c for c in comments))
		self.assertFalse(any("standard" in c for c in comments))

	def test_goal_wait_released_by_reply(self):
		auto = make_automation(
			"goal-flow",
			[
				{"type": "add_note", "comment": "pre"},
				{"type": "goal", "event": "reply", "outcome": "wait"},
				{"type": "add_note", "comment": "post"},
			],
		)
		lead = make_lead(mobile_no="+390000000777")
		enr = get_enrollment(auto.name, lead.name)
		self.assertEqual(enr.status, "Waiting")

		frappe.get_doc(
			{
				"doctype": "CRM SMS Message",
				"type": "Incoming",
				"from": lead.mobile_no,
				"to": "+390000000000",
				"message": "sì!",
				"status": "Received",
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
			}
		).insert(ignore_permissions=True)
		enr.reload()
		self.assertEqual(enr.status, "Completed")

	def test_tag_actions_and_trigger(self):
		listener = make_automation(
			"tag-listener",
			[{"type": "add_note", "comment": "taggato"}],
			trigger_event="Tag Added",
			trigger_config=frappe.as_json({"tag": "hot"}),
		)
		tagger = make_automation(
			"tagger",
			[{"type": "add_tag", "tag": "hot"}],
		)
		lead = make_lead(email="tag@example.com")
		self.assertIsNotNone(get_enrollment(tagger.name, lead.name))
		lead.reload()
		self.assertIn("hot", lead.get("_user_tags") or "")
		self.assertIsNotNone(get_enrollment(listener.name, lead.name))

	def test_trigger_config_filters_by_payload(self):
		listener = make_automation(
			"tag-filtered",
			[{"type": "add_note", "comment": "x"}],
			trigger_event="Tag Added",
			trigger_config=frappe.as_json({"tag": "cold"}),
		)
		make_automation("tagger2", [{"type": "add_tag", "tag": "hot"}])
		lead = make_lead(email="tag2@example.com")
		self.assertIsNone(get_enrollment(listener.name, lead.name))

	def test_compiled_program_is_stored(self):
		auto = make_automation("compiled", [{"type": "add_note", "comment": "x"}])
		program = json.loads(auto.compiled_steps)
		self.assertEqual(program[-1]["op"], "end")
		self.assertEqual(program[0]["op"], "action")


class TestAutomationBuilder(IntegrationTestCase):
	"""What the visual editor leans on: stable node ids, statistics, dry run."""

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_steps_get_stable_ids_and_compile_to_nodes(self):
		auto = make_automation(
			"identified",
			[
				{"type": "add_note", "comment": "one"},
				{
					"type": "if_else",
					"branches": [
						{
							"condition_groups": [[{"field": "email", "operator": "is_set"}]],
							"steps": [{"type": "add_note", "comment": "has email"}],
						}
					],
					"else_steps": [{"type": "add_note", "comment": "no email"}],
				},
			],
		)
		steps = json.loads(auto.steps)
		first_id = steps[0]["id"]
		self.assertTrue(first_id)
		self.assertTrue(steps[1]["branches"][0]["id"])
		self.assertTrue(steps[1]["branches"][0]["steps"][0]["id"])
		self.assertTrue(steps[1]["else_steps"][0]["id"])

		program = json.loads(auto.compiled_steps)
		self.assertIn(first_id, [op.get("node") for op in program])
		self.assertEqual(engine.program_nodes(program)[0], first_id)

		# ids survive an edit of the flow
		steps[0]["comment"] = "one, edited"
		auto.steps = json.dumps(steps)
		auto.save()
		self.assertEqual(json.loads(auto.steps)[0]["id"], first_id)

	def test_duplicate_ids_are_replaced(self):
		auto = make_automation(
			"twins",
			[
				{"id": "same", "type": "add_note", "comment": "one"},
				{"id": "same", "type": "add_note", "comment": "two"},
			],
		)
		ids = [step["id"] for step in json.loads(auto.steps)]
		self.assertEqual(len(set(ids)), 2)

	def test_step_stats_are_keyed_by_node(self):
		from crm.api.automation import get_step_stats

		auto = make_automation(
			"counted",
			[
				{"type": "add_note", "comment": "runs"},
				{
					"type": "add_note",
					"comment": "skipped",
					"condition": {"field": "email", "operator": "contains", "value": "@never.test"},
				},
			],
		)
		lead = make_lead(email="stats@example.com")
		self.assertIsNotNone(get_enrollment(auto.name, lead.name))

		steps = json.loads(auto.steps)
		stats = get_step_stats(auto.name)
		self.assertEqual(stats["nodes"][steps[0]["id"]]["success"], 1)
		self.assertEqual(stats["nodes"][steps[1]["id"]]["skipped"], 1)
		self.assertEqual(stats["totals"].get("Completed"), 1)

	def test_simulate_walks_the_flow_without_side_effects(self):
		steps = [
			{"type": "add_note", "comment": "ciao {{ first_name }}"},
			{"type": "wait", "hours": 3},
			{
				"type": "if_else",
				"branches": [
					{
						"label": "VIP",
						"condition_groups": [
							[{"field": "email", "operator": "contains", "value": "@vip.test"}]
						],
						"steps": [{"type": "add_tag", "tag": "vip"}],
					}
				],
				"else_steps": [{"type": "add_tag", "tag": "standard"}],
			},
		]
		lead = make_lead(email="boss@vip.test", first_name="Marco")
		trace = engine.simulate(steps, lead)

		self.assertEqual(trace[0]["status"], "Would run")
		self.assertIn("Marco", trace[0]["detail"])
		self.assertEqual(trace[1]["status"], "Wait")
		self.assertEqual(trace[2]["status"], "Branch")
		self.assertIn("VIP", trace[2]["detail"])
		self.assertIn("vip", trace[3]["detail"])
		self.assertEqual(trace[-1]["status"], "End")

		# nothing was written: no comment, no tag
		self.assertFalse(
			frappe.get_all("Comment", filters={"reference_doctype": "CRM Lead", "reference_name": lead.name})
		)
		lead.reload()
		self.assertNotIn("vip", lead.get("_user_tags") or "")

	def test_simulate_reports_stop_and_skips(self):
		steps = [
			{
				"type": "add_note",
				"comment": "never",
				"condition": {"field": "email", "operator": "contains", "value": "@never.test"},
			},
			{"type": "stop_if", "condition": {"field": "email", "operator": "is_set"}},
			{"type": "add_note", "comment": "unreachable"},
		]
		lead = make_lead(email="stop@example.com")
		trace = engine.simulate(steps, lead)
		self.assertEqual(trace[0]["status"], "Skipped")
		self.assertEqual(trace[1]["status"], "Exited")
		self.assertEqual(len(trace), 2)

	def test_duplicate_automation_is_a_fresh_draft(self):
		from crm.api.automation import duplicate_automation

		auto = make_automation("original", [{"type": "add_note", "comment": "x"}])
		copy_name = duplicate_automation(auto.name)["name"]
		copy = frappe.get_doc("CRM Automation", copy_name)
		self.assertFalse(copy.enabled)
		self.assertIn("copy", copy.title)
		self.assertNotEqual(
			json.loads(copy.steps)[0]["id"],
			json.loads(auto.steps)[0]["id"],
		)
