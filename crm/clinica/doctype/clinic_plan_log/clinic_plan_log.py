# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A check-in of the patient on a plan's item (`crm.clinica.area.piani`): done,
partly, skipped, one a day, with effort or pain if they say. Read with its plan."""

from crm.clinica.base import DocumentoClinico


class ClinicPlanLog(DocumentoClinico):
	dice_che_e_venuto = False
