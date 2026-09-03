# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.pipeline import (
	create_default_pipeline,
	create_pipeline,
	delete_pipeline,
	delete_stage,
	get_pipelines,
	save_stages,
	set_default_pipeline,
)
from crm.fcrm.doctype.crm_deal.test_crm_deal import create_test_deal
from crm.fcrm.doctype.crm_pipeline.crm_pipeline import (
	get_default_pipeline,
	get_first_stage,
	get_pipeline_stages,
)
from crm.utils import get_kanban_column_options


class TestCRMPipeline(IntegrationTestCase):
	def setUp(self) -> None:
		self.pipeline = create_default_pipeline()

	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_default_pipeline_has_stages(self):
		self.assertTrue(self.pipeline)
		self.assertEqual(get_default_pipeline(), self.pipeline)
		self.assertTrue(get_pipeline_stages(self.pipeline))

	def test_new_deal_lands_in_the_default_pipeline(self):
		deal = create_test_deal(organization="Pipeline Org")

		self.assertEqual(deal.pipeline, self.pipeline)
		self.assertEqual(deal.status, get_first_stage(self.pipeline))

	def test_stage_decides_the_pipeline(self):
		other = create_pipeline("Onboarding")
		deal = create_test_deal(organization="Stage Decides Org")

		deal.status = other["stages"][0]["name"]
		deal.save()

		self.assertEqual(deal.pipeline, "Onboarding")

	def test_switching_pipeline_moves_the_deal_to_its_first_stage(self):
		create_pipeline("Onboarding")
		deal = create_test_deal(organization="Switching Org")

		deal.pipeline = "Onboarding"
		deal.save()

		self.assertEqual(deal.pipeline, "Onboarding")
		self.assertEqual(deal.status, get_first_stage("Onboarding"))

	def test_default_stages_get_names_that_do_not_clash(self):
		other = create_pipeline("Onboarding")
		names = [stage["name"] for stage in other["stages"]]

		self.assertIn("Qualification (Onboarding)", names)
		self.assertEqual(len(names), len(set(names)))

	def test_stage_name_taken_by_another_pipeline_is_refused(self):
		create_pipeline("Onboarding", stages=[{"stage": "Discovery", "type": "Open"}])

		with self.assertRaises(frappe.ValidationError):
			create_pipeline("Support", stages=[{"stage": "Discovery", "type": "Open"}])

	def test_save_stages_renames_and_reorders(self):
		create_pipeline("Onboarding", stages=[{"stage": "Discovery", "type": "Open"}])

		# add a stage, put it first, and rename the one that was there
		reordered = [
			{"stage": "Kickoff", "type": "Ongoing", "color": "blue"},
			{"name": "Discovery", "stage": "Deep Dive", "type": "Open"},
		]
		saved = save_stages("Onboarding", reordered)

		self.assertEqual([stage["name"] for stage in saved], ["Kickoff", "Deep Dive"])
		self.assertEqual([stage["position"] for stage in saved], [1, 2])

	def test_moving_a_stage_takes_its_deals_along(self):
		create_pipeline("Onboarding", stages=[{"stage": "Discovery", "type": "Open"}])
		deal = create_test_deal(organization="Moving Stage Org", status="Discovery")
		self.assertEqual(deal.pipeline, "Onboarding")

		stage = frappe.get_doc("CRM Deal Status", "Discovery")
		stage.pipeline = self.pipeline
		stage.save()

		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "pipeline"), self.pipeline)

	def test_deleting_a_stage_moves_its_deals(self):
		create_pipeline(
			"Onboarding",
			stages=[{"stage": "Discovery", "type": "Open"}, {"stage": "Kickoff", "type": "Ongoing"}],
		)
		deal = create_test_deal(organization="Deleting Stage Org", status="Discovery")

		delete_stage("Discovery", move_deals_to="Kickoff")

		deal.reload()
		self.assertEqual(deal.status, "Kickoff")
		self.assertEqual(deal.pipeline, "Onboarding")
		self.assertFalse(frappe.db.exists("CRM Deal Status", "Discovery"))

	def test_last_stage_of_a_pipeline_cannot_be_deleted(self):
		create_pipeline("Onboarding", stages=[{"stage": "Discovery", "type": "Open"}])

		with self.assertRaises(frappe.ValidationError):
			delete_stage("Discovery")

	def test_default_pipeline_cannot_be_deleted(self):
		with self.assertRaises(frappe.ValidationError):
			delete_pipeline(self.pipeline)

	def test_deleting_a_pipeline_moves_its_deals_and_stages(self):
		create_pipeline("Onboarding", stages=[{"stage": "Discovery", "type": "Open"}])
		deal = create_test_deal(organization="Deleting Pipeline Org", status="Discovery")

		delete_pipeline("Onboarding", move_deals_to=self.pipeline)

		deal.reload()
		self.assertEqual(deal.pipeline, self.pipeline)
		self.assertFalse(frappe.db.exists("CRM Pipeline", "Onboarding"))
		self.assertFalse(frappe.db.exists("CRM Deal Status", "Discovery"))

	def test_only_one_pipeline_is_the_default_one(self):
		create_pipeline("Onboarding")
		set_default_pipeline("Onboarding")

		self.assertEqual(get_default_pipeline(), "Onboarding")
		self.assertFalse(frappe.db.get_value("CRM Pipeline", self.pipeline, "is_default"))

	def test_kanban_columns_follow_the_pipeline_filter(self):
		other = create_pipeline("Onboarding")

		columns = get_kanban_column_options("CRM Deal", "status", {"pipeline": "Onboarding"})

		self.assertEqual([column["name"] for column in columns], [stage["name"] for stage in other["stages"]])

	def test_get_pipelines_reports_deal_counts(self):
		create_test_deal(organization="Counting Org")

		pipelines = {pipeline["name"]: pipeline for pipeline in get_pipelines()}

		self.assertIn(self.pipeline, pipelines)
		self.assertTrue(pipelines[self.pipeline]["deal_count"] >= 1)
		self.assertTrue(pipelines[self.pipeline]["stages"])
