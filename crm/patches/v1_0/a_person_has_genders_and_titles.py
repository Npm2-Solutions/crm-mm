# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The genders and titles a person is given, on a site set up without the
framework's setup wizard: its «Gender» was an empty list on every person."""

from crm.install import add_genders_and_titles


def execute():
	add_genders_and_titles()
