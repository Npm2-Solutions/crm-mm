# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A check-in of the person on a plan's item (`crm.piani.area`): done, partly,
skipped, one a day, with effort or pain if they say. Read with its plan."""

from frappe.model.document import Document


class CRMPersonalPlanLog(Document):
	pass
