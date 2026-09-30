# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A passkey to the client area (`crm.area.passkey`): the public half of a key that
stays on the person's phone, and the counter the phone increases at each use. The
door, not the record: nothing about the person is here."""

from frappe.model.document import Document


class CRMAreaPasskey(Document):
	pass
