# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Frappe 16.50's desk opens a module in its shell, a `Sidebar` the app ships
(`fcrm/sidebar/dottorcloud`, synced before this runs): the one the conversion of
the old Workspace Sidebars made for the CRM's module, under the old product's name
or the module's, goes, and a rail entry that named it opens DottorCloud's. The
framework's app icon, named after its hooks' title, is the desk's administration."""


def execute():
	from crm import marchio

	marchio.applica()
