# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The product's name where the framework shows its own: the login page, the
desk's title and help menu, the public pages' footer, the desk's workspace and
icons (`crm.marchio`). What a centre already wrote in those settings stays."""


def execute():
	from crm import marchio

	marchio.applica()
