# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A line of the patient's summary (`crm.clinica.sintesi`): proposed, then decided.

Health data like the record: it inherits rule 1 of becoming a patient."""

from crm.clinica.base import DocumentoClinico


class ClinicSummaryValue(DocumentoClinico):
	pass
