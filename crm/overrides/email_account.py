# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A mailbox, as DottorCloud reads it (doc 51).

From somebody's own mailbox only what is the centre's is taken: the answers to what
was written from DottorCloud and the emails of the people the centre knows
(`crm.posta.personale.da_tenere`). The rest is that person's own post: it is left
in their mailbox and never stored here. The centre's mailboxes are read whole.
"""

from frappe.email.doctype.email_account.email_account import EmailAccount

from crm.posta import personale


class CasellaDiDottorCloud(EmailAccount):
	def get_inbound_mails(self):
		mails = super().get_inbound_mails()
		if not self.get(personale.CAMPO):
			return mails
		return [mail for mail in mails if personale.da_tenere(mail)]
