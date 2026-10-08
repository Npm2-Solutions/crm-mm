# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The one door a notification comes in by.

Every module tells somebody something here: who it is for, what kind, the sentence
(English, from `regole`) and its names, or the words somebody wrote (an
automation's message); who it comes from - nobody when DottorCloud itself says it;
the person or deal it opens; what it is about (the comment, the message, the task)
and the text it carries.

A notification already there and not yet read is not written twice. A message of
the same person, while the one before is unread, takes that one's place with how
many there are ("3 WhatsApp messages from Laura"): a conversation is one line of
the panel, not twenty. Once written, it reaches the person's phone and computer
where they turned notifications on (`spinta`).
"""

from __future__ import annotations

import html
import json

import frappe
from frappe import _
from frappe.utils import cint

from crm.demo import guardie
from crm.notifiche import posta, spinta
from crm.notifiche import regole as R

NOTIFICA = "CRM Notification"
#: Who stands for DottorCloud itself: the panel draws the kind, not a face.
SISTEMA = frozenset({"Administrator", "Guest"})


def avvisa(
	destinatario: str | None,
	tipo: str,
	frase: str | None = None,
	nomi: list | tuple = (),
	*,
	testo: str | None = None,
	testo_html: str | None = None,
	da: str | None = None,
	riguarda: tuple[str, str] | None = None,
	oggetto: tuple[str, str] | None = None,
	messaggio: str | None = None,
	frase_molti: str | None = None,
	una_volta: bool = False,
) -> str | None:
	"""A notification for `destinatario`. Returns its name, or None when there is
	nothing to write: nobody, themselves, a disabled user, the same one unread.

	- `frase` and `nomi`: the sentence (from `regole`) and its names; or `testo`,
	  the words somebody wrote, kept as they are (`testo_html` when they are
	  already HTML: what the CRM wrote before).
	- `riguarda`: (doctype, name) of the person or deal it opens.
	- `oggetto`: (doctype, name) of what it is about: the comment, the message.
	- `frase_molti`: the sentence for several ("{1} WhatsApp messages from {0}"):
	  a message adds to the one unread about the same person.
	- `una_volta`: once for the same thing, read or not (a comment saved again
	  does not mention anybody again).
	"""
	if not destinatario or (da and da == destinatario):
		return None
	if not frappe.db.get_value("User", destinatario, "enabled"):
		return None
	if da in SISTEMA:
		da = None

	doctype_oggetto, nome_oggetto = oggetto or (None, None)
	doctype_riguarda, nome_riguarda = riguarda or (None, None)
	parole = None if frase else (testo_html or html.escape(testo or "", quote=False))

	# the same one is not written twice while it is unread - or ever, `una_volta`
	stesso = {
		"to_user": destinatario,
		"type": tipo,
		"notification_type_doctype": doctype_oggetto,
		"notification_type_doc": nome_oggetto,
		"reference_doctype": doctype_riguarda,
		"reference_name": nome_riguarda,
		"sentence": frase,
		"notification_text": parole,
		"read": None if una_volta else 0,
	}
	if frappe.db.exists(NOTIFICA, {campo: valore for campo, valore in stesso.items() if valore is not None}):
		return None

	quanti = 1
	# never about the demo data, neither by email nor on a phone (crm.demo.guardie)
	solo_nel_pannello = guardie.solo_nel_pannello(riguarda or (None, None), oggetto or (None, None))
	# by email too, if it stays unread a few minutes and the person wants this kind
	per_email = (
		R.vuole_email(R.genere(tipo, doctype_oggetto, frase), posta.preferenze(destinatario))
		and not solo_nel_pannello
	)
	gia_per_email = None
	if frase_molti and nome_riguarda:
		# the one about the same person, not yet read, gives its place and its count
		prima = frappe.db.get_value(
			NOTIFICA,
			{
				"to_user": destinatario,
				"type": tipo,
				"reference_doctype": doctype_riguarda,
				"reference_name": nome_riguarda,
				# the same news: a kind tells other news too (the area: a message,
				# a quote signed), which never take each other's place
				"sentence": ("in", (frase, frase_molti)),
				"read": 0,
			},
			["name", "count", "emailed_on"],
			as_dict=True,
			order_by="creation desc",
		)
		if prima:
			quanti = (cint(prima.count) or 1) + 1
			# a conversation goes by email once while it is unread, not at every message
			gia_per_email = prima.emailed_on
			frappe.delete_doc(NOTIFICA, prima.name, ignore_permissions=True, force=True)
			frase, nomi = frase_molti, [*nomi, quanti]

	doc = frappe.get_doc(
		{
			"doctype": NOTIFICA,
			"to_user": destinatario,
			"from_user": da,
			"type": tipo,
			"sentence": frase,
			"sentence_args": json.dumps([str(n) for n in nomi]) if frase else None,
			"count": quanti,
			# the same words for the Desk's list, in the language they are written in
			"notification_text": R.solo_testo(R.frase(_(frase), nomi, frase)) if frase else parole,
			"message": messaggio,
			"comment": nome_oggetto if doctype_oggetto == "Comment" else None,
			"reference_doctype": doctype_riguarda,
			"reference_name": nome_riguarda,
			"notification_type_doctype": doctype_oggetto,
			"notification_type_doc": nome_oggetto,
			"email_due": 1 if per_email and not gia_per_email else 0,
			"emailed_on": gia_per_email,
		}
	)
	# written after what it is about: a message deleted meanwhile does not stop it,
	# the panel opens nothing where nothing is left
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True)
	# on the person's phone and computer at once, where they turned it on
	spinta.accoda(doc, solo_nel_pannello)
	return doc.name


#: A person's or deal's own field naming whoever follows them.
PROPRIETARIO = {"CRM Lead": "lead_owner", "CRM Deal": "deal_owner"}


def chi_segue(doctype: str, nome: str, banco: bool = True) -> list[str]:
	"""Who hears of a person's message: whoever the person or one of their deals is
	assigned to - the conversation is the same on each page -, else their owner,
	else - `banco` - the desk: everyone of the centre who reads its conversations and
	may open this person. A message never reaches nobody: a new number writing on
	WhatsApp has nobody assigned yet.

	Somebody chose whoever a record is assigned to, DottorCloud's own account
	(Administrator) too: assigned, it hears like anybody. It was left out with the
	owner, which stands for DottorCloud when it made the record, and whoever had
	assigned themselves working as Administrator never heard of a message."""
	from crm.api.doc import assigned_users_of
	from crm.permissions import livelli

	chi = []
	for seguito in stessa_conversazione(doctype, nome):
		chi += [u for u in assigned_users_of(*seguito) if u != "Guest" and u not in chi]
	if chi:
		return chi
	campo = PROPRIETARIO.get(doctype)
	proprietario = frappe.db.get_value(doctype, nome, campo) if campo else None
	if proprietario and proprietario not in SISTEMA:
		return [proprietario]
	if not banco:
		return []
	return [
		utente
		for utente in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
		if utente not in SISTEMA
		and livelli.nel_crm(utente)
		and not livelli.e_agenzia(utente)
		and livelli.puo("conversazioni.vedi", utente)
		and frappe.has_permission(doctype, "read", nome, user=utente)
	]


def stessa_conversazione(doctype: str, nome: str) -> list[tuple[str, str]]:
	"""The records one conversation is read on (`crm.api.whatsapp.whatsapp_thread_of`):
	a person and their deals, a deal and its person."""
	if doctype == "CRM Lead":
		from crm.api.lead import deal_names_of

		return [(doctype, nome), *(("CRM Deal", trattativa) for trattativa in sorted(deal_names_of(nome)))]
	if doctype == "CRM Deal":
		persona = frappe.db.get_value(doctype, nome, "lead")
		return [(doctype, nome), *((("CRM Lead", persona),) if persona else ())]
	return [(doctype, nome)]


def nome_utente(utente: str | None) -> str:
	"""Somebody of the centre by their name."""
	if not utente:
		return ""
	return frappe.get_cached_value("User", utente, "full_name") or utente
