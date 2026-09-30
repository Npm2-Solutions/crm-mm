# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""One answer of one person about one consent: the register only grows.

What was answered, when, how and on which words is never edited afterwards. The
one change a row accepts is its withdrawal, stamped on it; giving the consent
again writes a new row. Proof of consent (art. 7(1) GDPR) that could be edited
would prove nothing.
"""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.moduli import registro

#: The answer: fixed when it is written. A withdrawal writes only its own fields,
#: and the person's name is a display field that follows the person.
RISPOSTA = (
	"lead",
	"consent_type",
	"answered_on",
	"channel",
	"recorded_by",
	"source_doctype",
	"source_name",
	"ip_address",
	"user_agent",
	"text",
	"text_version",
	"note",
	"attachment",
)


class CRMConsent(Document):
	def validate(self):
		if self.is_new():
			if self.status == registro.REVOCATO:
				frappe.throw(_("A consent is withdrawn on the row that gave it, not on a new one"))
			return
		before = self.get_doc_before_save()
		if not before:
			return
		for campo in RISPOSTA:
			if str(before.get(campo) or "") != str(self.get(campo) or ""):
				frappe.throw(
					_("An answer in the consent register is not edited: {0} cannot change").format(
						_(self.meta.get_label(campo))
					)
				)
		if before.status != self.status and not (
			before.status == registro.DATO and self.status == registro.REVOCATO
		):
			frappe.throw(_("Only a consent given can be withdrawn"))
