# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""With the two-step login on, an authenticator app showed «Frappe Framework»
beside its codes, and the emails with the code said «from Frappe Framework»: the
brand puts the product's name there too (`crm.marchio._nome_e_piede`), unless the
centre chose a name of its own."""


def execute():
	from crm import marchio

	marchio.applica()
