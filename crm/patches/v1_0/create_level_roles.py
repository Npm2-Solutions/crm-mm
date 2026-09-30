# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The levels' roles, before the doctypes sync.

CRM Invoice gives Practitioner a permission of its own, and a DocPerm pointing at a
role that does not exist yet fails link validation during the sync. A site that
comes straight from before levels has never had the role.
"""


def execute():
	from crm.permissions.utenti import assicura_ruoli

	assicura_ruoli()
