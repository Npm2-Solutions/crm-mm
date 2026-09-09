# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The issuer.

Most of these fields are checked here rather than at the first invoice, because a
misconfiguration surfaces at the worst possible moment otherwise: the numbering
format that the Sistema TS refuses is discovered in January, with thousands of
rows behind it, and the missing stamp-duty authorisation is discovered by whoever
receives the invoice.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from crm.invoicing.engine import codice_fiscale as cf
from crm.invoicing.engine.codici import SOGGETTI_CON_CODICE_PROPRIETARIO, SoggettoInviante
from crm.invoicing.engine.numerazione import FormatoNonCompatibile, valida_formato


class CRMInvoicingCompany(Document):
	def validate(self):
		self.valida_identificativi()
		self.valida_numerazione()
		self.valida_bollo()
		self.valida_sistema_ts()
		self.unica_predefinita()

	def valida_identificativi(self):
		if self.tax_id and not cf.partita_iva_ue_valida(self.tax_id, self.country):
			frappe.throw(
				_("The VAT number {0} is not well formed for country {1}").format(
					self.tax_id, self.country or "IT"
				)
			)
		if self.fiscal_code and not (
			cf.valido(self.fiscal_code) or cf.identificativo_ts_valido(self.fiscal_code)
		):
			frappe.throw(_("The codice fiscale {0} fails its check character").format(self.fiscal_code))
		if self.iban and not cf.iban_valido(self.iban):
			frappe.throw(
				_(
					"The IBAN does not check out. A wrong IBAN on an invoice is a payment that never "
					"arrives, with nobody being told"
				)
			)

	def valida_numerazione(self):
		"""The format is validated now, not at the first submission to the Sistema TS.

		It is checked on the worst case - a six-digit counter - because document
		number 100,000 arrives in November, not in January.
		"""
		for serie in filter(None, (self.series_electronic, self.series_healthcare)):
			try:
				valida_formato(self.number_format or "{anno}/{serie}/{numero}", serie, 2026)
			except FormatoNonCompatibile as errore:
				frappe.throw(str(errore), title=_("Numbering format"))
		if self.series_electronic and self.series_electronic == self.series_healthcare:
			frappe.msgprint(
				_(
					"The electronic and healthcare series are the same. That is allowed, but the two "
					"flows end up in the same sequence and in the same retention system."
				),
				indicator="orange",
			)

	def valida_bollo(self):
		if self.stamp_duty_mode == "virtuale" and not (
			self.stamp_authorization_number and self.stamp_authorization_date
		):
			frappe.throw(
				_(
					"A virtual stamp duty needs the authorisation number and date: the annotation does "
					"not satisfy art. 15 DPR 642/72 without them. Until the authorisation is issued, "
					"issue with a physical stamp on the original."
				)
			)

	def valida_sistema_ts(self):
		categoria = self.sender_category or SoggettoInviante.NON_SANITARIO
		if categoria == SoggettoInviante.NON_SANITARIO:
			return
		if categoria in SOGGETTI_CON_CODICE_PROPRIETARIO:
			if not (self.region_code and self.asl_code and self.ssa_code):
				frappe.throw(
					_(
						"A {0} needs the full Codice Proprietario (codiceRegione-codiceAsl-codiceSSA) "
						"from its 'Abilitazione al Sistema TS' document"
					).format(categoria)
				)
		elif any((self.region_code, self.asl_code, self.ssa_code)):
			frappe.throw(
				_(
					"A {0} transmits as a natural person: codiceRegione, codiceAsl and codiceSSA have "
					"to be empty, only the codice fiscale is used"
				).format(categoria)
			)
		if self.ts_mode != "export" and not self.ts_username:
			frappe.throw(
				_(
					"Submission mode {0} needs Sistema TS credentials. Leave it on export until they "
					"arrive - export is the plan B, not the bottom rung."
				).format(self.ts_mode)
			)
		if not self.fiscal_code and not self.tax_id:
			frappe.throw(_("The Sistema TS needs a codice fiscale or a VAT number for the owner"))

	def unica_predefinita(self):
		if not self.is_default:
			return
		altre = frappe.get_all(
			"CRM Invoicing Company", filters={"is_default": 1, "name": ["!=", self.name]}, pluck="name"
		)
		for altra in altre:
			frappe.db.set_value("CRM Invoicing Company", altra, "is_default", 0)
