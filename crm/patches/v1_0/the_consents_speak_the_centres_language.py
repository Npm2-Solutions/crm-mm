# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""DottorCloud's words of the consents in the centre's language (03/10/2026).

A site set up in English before DottorCloud was installed gave its kinds of
consent English words, and the forms published since froze them: an Italian
centre's patients read "I agree to receive news, offers and reminders". The kinds
still on DottorCloud's words take the centre's language, and a form frozen on them
gets a new version with the words of today, asked of nobody who signed before.
Words a centre wrote are never touched."""

from crm.moduli import consensi, modelli


def execute():
	consensi.assicura_tipi()
	modelli.consensi_nella_lingua_del_centro()
