# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Create the invoicing roles before the doctypes that grant them are synced.

It has to run in `pre_model_sync`: a DocPerm pointing at a Role that does not
exist fails link validation, and the failure lands in the middle of a migration.
"""

from crm.invoicing.install import crea_ruoli


def execute():
	crea_ruoli()
