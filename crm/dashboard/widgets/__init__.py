# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Every widget the dashboard offers, one module per part of the product.

Importing this package registers them all (see ``crm.dashboard.registry``).
"""

from crm.dashboard.widgets import (
	agenda,
	automations,
	calls,
	conversations,
	invoicing,
	marketing,
	people,
	sales,
	sms_email,
	social,
	tasks,
	team,
	whatsapp,
)
