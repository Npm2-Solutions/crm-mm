# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""One booking system: every Calendly-style calendar becomes a service on /prenota.

See ``crm.scheduling.unify``. Old /book links redirect; nothing is deleted.
"""

from crm.scheduling.unify import migrate_all


def execute():
	migrate_all()
