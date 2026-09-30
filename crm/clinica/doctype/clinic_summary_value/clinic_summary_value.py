# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A line of the patient's summary (`crm.clinica.sintesi`): proposed, then decided.

Health data like the record: it inherits rule 1 of becoming a patient."""

from crm.clinica.base import DocumentoClinico


class ClinicSummaryValue(DocumentoClinico):
	pass
