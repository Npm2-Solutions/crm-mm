# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An event of Stripe's, kept before it is applied (`crm.pagamenti.webhook`)."""

from frappe.model.document import Document


class CRMStripeEvent(Document):
	pass
