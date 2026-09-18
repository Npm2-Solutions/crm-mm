# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""One thing that happened to one lead, on its way to Meta.

A queue rather than a direct call, for three reasons: a sales person changing a
status must not wait for Facebook, an event refused at 11pm has to be retried
rather than lost, and the coverage number Meta grades the integration on ("what
share of your leads did you report back?") can only be read off a record of what
was actually sent.
"""

from frappe.model.document import Document


class MetaConversionEvent(Document):
	pass
