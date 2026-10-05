# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""DottorCloud speaks Italian and English, nothing else: whoever had chosen another
language for themselves reads the centre's (`crm.lingue`)."""

from crm import lingue


def execute():
	lingue.utenti_in_italiano_o_inglese()
