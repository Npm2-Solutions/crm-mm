# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from crm.www.legal import legal_context

no_cache = 1


def get_context(context):
	legal_context(context)
	return context
