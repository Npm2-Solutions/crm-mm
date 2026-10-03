# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The notifications written before their sentences were kept apart (02/10/2026)
kept the words they were written with: in English, the first ones with the
record's ID ("You received a whatsapp message in lead CRM-LEAD-2026-00397").

Each one whose kind tells what it said - a message on a channel, a mention, an
assignment - gets today's sentence with today's names: whoever reads it reads it
in their language, the person by their name. One about something no longer
there, and the words somebody wrote (an automation's), stay as they are."""

import json

import frappe
from frappe import _

from crm.fcrm.doctype.crm_notification.crm_notification import nome_di
from crm.notifiche import regole as R
from crm.notifiche.avvisi import nome_utente

NOTIFICA = "CRM Notification"
#: The sentences that name who did it, before what it is about.
CON_AUTORE = frozenset(
	{
		R.MENZIONE,
		R.MENZIONE_TRATTATIVA,
		R.ASSEGNATA,
		R.ASSEGNATA_TRATTATIVA,
		R.TOLTA,
		R.TOLTA_TRATTATIVA,
		R.COMPITO,
		R.COMPITO_TOLTO,
	}
)
#: The ones about what was assigned, not the person or deal they open.
SU_COSA_ASSEGNATA = frozenset({R.ASSEGNATA, R.ASSEGNATA_TRATTATIVA, R.TOLTA, R.TOLTA_TRATTATIVA})


def execute():
	righe = frappe.get_all(
		NOTIFICA,
		filters={"sentence": ("is", "not set"), "type": ("in", R.DI_PRIMA)},
		fields=[
			"name",
			"type",
			"from_user",
			"notification_text",
			"reference_doctype",
			"reference_name",
			"notification_type_doctype",
			"notification_type_doc",
		],
	)
	for riga in righe:
		frase = R.frase_di_prima(
			riga.type, riga.notification_type_doctype, riga.reference_doctype, riga.notification_text
		)
		nomi = frase and nomi_di(frase, riga)
		if not nomi:
			continue
		frappe.db.set_value(
			NOTIFICA,
			riga.name,
			{
				"sentence": frase,
				"sentence_args": json.dumps(nomi),
				# the same words for the Desk's list, as `avvisa` writes them
				"notification_text": R.solo_testo(R.frase(_(frase), nomi, frase)),
			},
			update_modified=False,
		)


def nomi_di(frase: str, riga) -> list[str] | None:
	"""The names the sentence takes, as they read today; None when what it is
	about, or who did it, is no longer there."""
	if frase in (R.COMPITO, R.COMPITO_TOLTO):
		cosa = frappe.db.get_value("CRM Task", riga.notification_type_doc, "title")
	elif frase in SU_COSA_ASSEGNATA:
		cosa = _nome(riga.notification_type_doctype, riga.notification_type_doc)
	else:
		cosa = _nome(riga.reference_doctype, riga.reference_name)
	if not cosa:
		return None
	if frase not in CON_AUTORE:
		return [cosa]
	autore = nome_utente(riga.from_user)
	return [autore, cosa] if autore else None


def _nome(doctype: str | None, name: str | None) -> str | None:
	if not (doctype and name and frappe.db.exists(doctype, name)):
		return None
	return nome_di(doctype, name)
