# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The product's brand - the vertical's the plan has on - everywhere the framework
shows its own: the name, the logo, the favicon of the login page, the desk and
every public page (`crm.marchio.applica`). A name or a logo somebody wrote there
gives way: the centre's own mark leads where a person deals with the centre
(Settings > The centre > General > Name & logo, `crm.marchio`)."""


def execute():
	from crm import marchio

	marchio.applica()
