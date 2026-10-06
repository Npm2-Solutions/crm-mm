# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How an issuing company invoices with Fatture in Cloud: the access its manager
gave, which company there it is, and which of its VAT rates, accounts and
numerations stand for the ones here (`crm.invoicing.fic`).

Read and written only through `crm.invoicing.fic.collegamento`, which asks for
`fatture.configura`: the tokens never leave the server."""

from frappe.model.document import Document


class CRMFattureinCloud(Document):
	pass
