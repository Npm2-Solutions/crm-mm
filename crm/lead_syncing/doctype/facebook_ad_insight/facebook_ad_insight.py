# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What one ad spent on one day.

One row per ad per day, named `{ad_id}-{date}`, so re-reading a day overwrites
it instead of adding it up twice — Meta keeps revising the last few days, and a
report that double counts is worse than no report.
"""

from frappe.model.document import Document


class FacebookAdInsight(Document):
	pass
