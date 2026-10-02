# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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
	quotes,
	sales,
	sms_email,
	social,
	tasks,
	team,
	whatsapp,
)
