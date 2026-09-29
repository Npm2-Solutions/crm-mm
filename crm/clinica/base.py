# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What every clinical document does, once, in one place.

Rule 1 of becoming a patient: the first clinical information saved about a person
makes them one. Every clinical DocType inherits from `DocumentoClinico`, so a new
one is covered without anybody remembering to - and `tests/test_confine.py`
checks that they all do.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from crm.clinica import paziente, regole


class DocumentoClinico(Document):
	def after_insert(self):
		paziente.assicura_paziente(
			self.get("lead"),
			regole.INFORMAZIONE_MEDICA,
			fonte=(self.doctype, self.name),
			da=self.get("practitioner") or frappe.session.user,
		)
