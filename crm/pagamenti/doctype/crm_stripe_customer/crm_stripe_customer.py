# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person as a customer on the centre's Stripe account (`crm.pagamenti.addebiti`):
only Stripe's id, by which a card saved for a monthly charge is found again. Written
by DottorCloud, read with the person, gone with them."""

from frappe.model.document import Document


class CRMStripeCustomer(Document):
	pass
