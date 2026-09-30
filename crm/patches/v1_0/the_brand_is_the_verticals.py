# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The product's brand - the vertical's the plan has on - everywhere the framework
shows its own: the name, the logo, the favicon of the login page, the desk and
every public page (`crm.marchio.applica`). A name or a logo somebody wrote there
gives way: the centre's own logo goes beside the product's (Settings > Brand)."""


def execute():
	from crm import marchio

	marchio.applica()
