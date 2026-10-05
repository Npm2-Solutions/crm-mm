# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMPushSubscription(Document):
	"""A browser or an installed app that receives somebody's notifications
	(crm/notifiche/spinta.py): written and read only there, each person their own."""
