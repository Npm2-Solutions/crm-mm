# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

MANAGER_ROLES = {"System Manager", "Sales Manager"}


class CRMSocialPost(Document):
	def validate(self):
		self.hold_for_approval()

	def hold_for_approval(self):
		"""Only a manager puts a post on the schedule.

		`save_post` already turns a user's "Schedule" into a request for approval,
		but the doctype itself is writable by Sales Users: a post saved without
		going through it — over the REST API — went on the schedule, and out,
		without anybody approving it. So the rule lives here too.

		Once approved, a post that a user edits goes back for approval, as it does
		through `save_post`: what was approved is what goes out. A published post
		is left alone — there is nothing left to approve.
		"""
		if self.status not in ("Scheduled", "Published"):
			return
		if MANAGER_ROLES & set(frappe.get_roles()):
			return
		before = self.get_doc_before_save()
		if self.status == "Published" and before and before.status == "Published":
			return
		self.status = "Pending Approval"
		self.requested_by = frappe.session.user
		self.approved_by = None
