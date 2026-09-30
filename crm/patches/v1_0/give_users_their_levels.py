# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The users from before levels get the levels that stand for their roles (doc 30).

Sales Manager becomes Manager; Sales User becomes Front Desk, or Sales where the site
turned the sales hierarchy on. The agency's users, anyone with another app's roles
and anyone the levels would not fully cover are left as they are: nobody loses a
role to the migration, and they keep counting as the levels their roles imply.
Worth a look site by site afterwards, in Settings > Users.
"""

import frappe


def execute():
	from crm.permissions.utenti import migra_utenti

	for user, levels in migra_utenti():
		frappe.logger("crm").info(f"levels for {user}: {', '.join(levels)}")
