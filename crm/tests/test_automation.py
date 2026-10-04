# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

import datetime
import json
from unittest import mock

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

	def test_le_iscrizioni_se_ne_vanno_con_la_persona(self):
		# an enrollment is the person's way through an automation: deleting them
		# takes it away, and the delete dialog never offers it, nor anything by
		# its code
		from crm.api.doc import get_linked_docs_of_document

		auto = make_automation("goodbye-flow", [{"type": "wait", "hours": 2}])
		lead = make_lead(email="goodbye@example.com")
		self.assertEqual(get_enrollment(auto.name, lead.name).status, "Waiting")
		collegati = get_linked_docs_of_document("CRM Lead", lead.name)
		self.assertNotIn("CRM Automation Enrollment", [d["doc"] for d in collegati])
		self.assertFalse([d for d in collegati if d["title"] == d["reference_docname"]])
		frappe.delete_doc("CRM Lead", lead.name)
		self.assertFalse(
			frappe.db.exists(
				"CRM Automation Enrollment", {"reference_doctype": "CRM Lead", "reference_name": lead.name}
			)
		)

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
		# a trigger that can fire again on a record already in: the second tag is
		# a second "Tag Added" on the same lead. It used to be the second status
		# change, but the sale state left the person in a000171 and the trigger
		# went with it.
		from frappe.desk.doctype.tag.tag import add_tag

		auto = make_automation(
			"tag-flow",
			[{"type": "add_tag_comment", "comment": "x"}],
			trigger_event="Tag Added",
		)
		lead = make_lead()
		self.assertIsNone(get_enrollment(auto.name, lead.name))  # nothing before the tag

		add_tag("interested", "CRM Lead", lead.name)
		first = get_enrollment(auto.name, lead.name)
		self.assertIsNotNone(first)

		add_tag("hot", "CRM Lead", lead.name)
		lead.reload()
		self.assertIn("hot", lead.get("_user_tags") or "")  # the second event really happened
		self.assertEqual(
			get_enrollment(auto.name, lead.name).name,
			first.name,
			"the second trigger must not open a second enrollment",
		)
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


class LaFinestraOraria(IntegrationTestCase):
	"""The hours an automation may write in: Time fields come from the database
	as a timedelta, «9:00:00», and compared as text «9:00» sorts after «10:30»."""

	def finestra(self, inizio, fine):
		return frappe._dict(
			time_window_enabled=1,
			window_days="[]",
			window_start=datetime.timedelta(hours=inizio),
			window_end=datetime.timedelta(hours=fine),
		)

	def test_una_finestra_che_apre_alle_nove(self):
		for ora, dentro in ((8, False), (9, True), (10, True), (17, True), (19, False)):
			adesso = datetime.datetime(2026, 10, 5, ora, 30)
			with mock.patch.object(engine, "now_datetime", return_value=adesso):
				self.assertEqual(engine.within_time_window(self.finestra(9, 18)), dentro, ora)

	def test_la_prossima_apertura(self):
		adesso = datetime.datetime(2026, 10, 5, 20, 0)
		with mock.patch.object(engine, "now_datetime", return_value=adesso):
			self.assertEqual(
				engine.next_window_open(self.finestra(9, 18)), datetime.datetime(2026, 10, 6, 9, 0)
			)


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

	def test_trigger_condition_accepts_or_groups(self):
		auto = make_automation(
			"segmented",
			[{"type": "add_note", "comment": "x"}],
			trigger_condition=json.dumps(
				[
					[{"field": "email", "operator": "contains", "value": "@vip.test"}],
					[{"field": "mobile_no", "operator": "contains", "value": "+39999"}],
				]
			),
		)
		out = make_lead(email="no@example.com", mobile_no="+390000000123")
		self.assertIsNone(get_enrollment(auto.name, out.name))
		by_email = make_lead(email="ceo@vip.test", mobile_no="+390000000124")
		self.assertIsNotNone(get_enrollment(auto.name, by_email.name))
		by_phone = make_lead(email="x@example.com", mobile_no="+39999123456")
		self.assertIsNotNone(get_enrollment(auto.name, by_phone.name))

	def test_second_copy_gets_its_own_title(self):
		from crm.api.automation import duplicate_automation

		auto = make_automation("popular", [{"type": "add_note", "comment": "x"}])
		first = duplicate_automation(auto.name)["name"]
		second = duplicate_automation(auto.name)["name"]
		self.assertNotEqual(first, second)
		self.assertTrue(frappe.db.exists("CRM Automation", second))

	def test_creating_two_automations_with_the_same_title_is_refused(self):
		from crm.api.automation import save_automation

		payload = {"title": "same name", "trigger_event": "Lead Created", "steps": [{"type": "exit"}]}
		save_automation(automation=payload)
		with self.assertRaises(frappe.ValidationError):
			save_automation(automation=dict(payload))


class TestAutomationTriggers(IntegrationTestCase):
	"""One automation, several triggers — each with its own filters and conditions."""

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_single_trigger_becomes_a_row(self):
		auto = make_automation(
			"legacy-shape",
			[{"type": "add_note", "comment": "x"}],
			trigger_event="Tag Added",
			trigger_config=frappe.as_json({"tag": "hot"}),
		)
		self.assertEqual(len(auto.triggers), 1)
		self.assertEqual(auto.triggers[0].trigger_event, "Tag Added")
		self.assertEqual(json.loads(auto.triggers[0].trigger_config), {"tag": "hot"})
		# the single field keeps mirroring the first row
		self.assertEqual(auto.trigger_event, "Tag Added")

	def test_automation_listens_to_every_trigger_it_has(self):
		from frappe.desk.doctype.tag.tag import add_tag

		auto = make_automation(
			"two-ways",
			[{"type": "add_note", "comment": "in"}],
			triggers=[
				{
					"trigger_event": "Lead Created",
					"trigger_condition": frappe.as_json(
						[[{"field": "email", "operator": "contains", "value": "@first.test"}]]
					),
				},
				{
					"trigger_event": "Tag Added",
					"trigger_config": frappe.as_json({"tag": "vip"}),
				},
			],
		)
		self.assertEqual(len(auto.triggers), 2)

		# first trigger: only the leads its own condition allows
		matching = make_lead(email="a@first.test")
		self.assertIsNotNone(get_enrollment(auto.name, matching.name))
		other = make_lead(email="b@second.test", mobile_no="+390000000002")
		self.assertIsNone(get_enrollment(auto.name, other.name))

		# second trigger: the same automation, entered by a tag
		add_tag("vip", "CRM Lead", other.name)
		self.assertIsNotNone(get_enrollment(auto.name, other.name))

		# a tag the trigger does not watch changes nothing
		third = make_lead(email="c@third.test", mobile_no="+390000000003")
		add_tag("cold", "CRM Lead", third.name)
		self.assertIsNone(get_enrollment(auto.name, third.name))

	def test_overlapping_triggers_enrol_once(self):
		auto = make_automation(
			"overlapping",
			[{"type": "add_note", "comment": "in"}],
			triggers=[
				{"trigger_event": "Lead Created"},
				{"trigger_event": "Lead Created"},
			],
		)
		lead = make_lead(email="once@example.com")
		self.assertEqual(
			frappe.db.count(
				"CRM Automation Enrollment", {"automation": auto.name, "reference_name": lead.name}
			),
			1,
		)

	def test_api_round_trip_keeps_the_triggers(self):
		from crm.api.automation import get_automation, save_automation

		payload = {
			"title": "multi via api",
			"steps": [{"type": "add_note", "comment": "x"}],
			"triggers": [
				{"event": "Deal Created", "config": {}, "condition": None},
				{"event": "Tag Added", "config": {"tag": "vip"}, "condition": None},
			],
		}
		saved = save_automation(automation=payload)
		self.assertEqual([t["event"] for t in saved["triggers"]], ["Deal Created", "Tag Added"])
		self.assertEqual(saved["trigger_event"], "Deal Created")

		fetched = get_automation(saved["name"])
		self.assertEqual(fetched["triggers"][1]["config"], {"tag": "vip"})

	def test_unknown_trigger_is_refused(self):
		from crm.api.automation import save_automation

		with self.assertRaises(frappe.ValidationError):
			save_automation(
				automation={
					"title": "bad trigger",
					"steps": [{"type": "exit"}],
					"triggers": [{"event": "Volcano Erupted"}],
				}
			)

	def test_two_triggers_on_one_event_keep_their_own_conditions(self):
		auto = make_automation(
			"per-source",
			[{"type": "add_note", "comment": "in"}],
			triggers=[
				{
					"trigger_event": "Lead Created",
					"trigger_condition": frappe.as_json(
						[[{"field": "email", "operator": "contains", "value": "@web.test"}]]
					),
				},
				{
					"trigger_event": "Lead Created",
					"trigger_condition": frappe.as_json(
						[[{"field": "email", "operator": "contains", "value": "@ads.test"}]]
					),
				},
			],
		)
		# the second trigger still gets its turn when the first one says no
		from_ads = make_lead(email="a@ads.test")
		self.assertIsNotNone(get_enrollment(auto.name, from_ads.name))
		from_web = make_lead(email="b@web.test", mobile_no="+390000000004")
		self.assertIsNotNone(get_enrollment(auto.name, from_web.name))
		neither = make_lead(email="c@shop.test", mobile_no="+390000000005")
		self.assertIsNone(get_enrollment(auto.name, neither.name))


KEY_MANAGER = "automation.key.manager@example.com"
KEY_SALES_USER = "automation.key.user@example.com"


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


class TestInboundWebhookKey(IntegrationTestCase):
	"""The key in an Inbound Webhook URL fires the automation for whoever holds it:
	kept encrypted, handed to the managers who build the automation, to nobody else."""

	def setUp(self):
		make_user(KEY_MANAGER, "Sales Manager")
		make_user(KEY_SALES_USER, "Sales User")
		self.auto = make_automation(
			"inbound", [{"type": "add_note", "comment": "hooked"}], trigger_event="Inbound Webhook"
		)
		self.key = self.auto.get_password("webhook_key")
		self._form_dict = frappe.local.form_dict

	def tearDown(self):
		frappe.local.form_dict = self._form_dict
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def post(self, key: str, **payload):
		from crm.api.automation import inbound_webhook

		frappe.set_user("Guest")  # resets form_dict: the payload goes in after
		frappe.local.form_dict = frappe._dict(payload)
		try:
			return inbound_webhook(automation=self.auto.name, key=key)
		finally:
			frappe.set_user("Administrator")

	def test_the_key_is_made_once_and_kept_encrypted(self):
		self.assertEqual(len(self.key), 32)
		self.assertEqual(set(frappe.db.get_value("CRM Automation", self.auto.name, "webhook_key")), {"*"})
		self.auto.reload()
		self.auto.save()
		self.assertEqual(self.auto.get_password("webhook_key"), self.key)

	def test_a_sales_user_cannot_read_the_key(self):
		from crm.api.automation import get_automation

		frappe.set_user(KEY_SALES_USER)
		self.assertNotEqual(frappe.client.get("CRM Automation", self.auto.name)["webhook_key"], self.key)
		self.assertEqual(get_automation(self.auto.name)["webhook_key"], "")

	def test_a_manager_gets_the_key_for_the_url(self):
		from crm.api.automation import get_automation

		frappe.set_user(KEY_MANAGER)
		self.assertEqual(get_automation(self.auto.name)["webhook_key"], self.key)
		# REST still gets the mask, even for them
		self.assertNotEqual(frappe.client.get("CRM Automation", self.auto.name)["webhook_key"], self.key)

	def test_the_webhook_accepts_its_key_only(self):
		for wrong in ("wrong", "*" * len(self.key), "", "chiavé-sbagliata"):
			with self.assertRaises(frappe.PermissionError, msg=wrong):
				self.post(wrong, email="hook@example.com")
		lead = self.post(self.key, email="hook@example.com")["lead"]
		self.assertIsNotNone(get_enrollment(self.auto.name, lead))

	def test_a_duplicate_gets_a_key_of_its_own(self):
		from crm.api.automation import duplicate_automation

		copy = duplicate_automation(self.auto.name)
		copy_key = frappe.get_doc("CRM Automation", copy["name"]).get_password("webhook_key")
		self.assertEqual(len(copy_key), 32)
		self.assertNotEqual(copy_key, self.key)

	def test_a_plain_text_key_from_before_is_encrypted_by_the_patch(self):
		from frappe.utils.password import remove_encrypted_password

		from crm.patches.v1_0.encrypt_integration_secrets import execute

		remove_encrypted_password("CRM Automation", self.auto.name, "webhook_key")
		frappe.db.set_value("CRM Automation", self.auto.name, "webhook_key", "plain-automation-key")
		execute()

		self.assertEqual(frappe.db.get_value("CRM Automation", self.auto.name, "webhook_key"), "*" * 20)
		saved = frappe.get_doc("CRM Automation", self.auto.name)
		self.assertEqual(saved.get_password("webhook_key"), "plain-automation-key")
		# the URL an external system already has keeps working
		self.assertTrue(self.post("plain-automation-key", email="old.url@example.com")["lead"])
