# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a notification says, without a site: the sentences, a sentence with its
names, the words of a notification written before, the first words of a message,
what kind of notification it is. Tested with plain `unittest`.

A sentence is kept in English, the way the catalogue knows it, with its names
apart: whoever reads it reads it in their own language, the names in bold. Each
sentence is whole - a person by their name, "the deal {1}" - never a DocType's
name glued into it (AGENTS.md, "The language").
"""

from __future__ import annotations

import html
import re

from bs4 import BeautifulSoup

# ------------------------------------------------------------------ the sentences
# The catalogue (crm/locale/it.po) has every one: a test reads them from here.

MENZIONE = "{0} mentioned you in a comment on {1}"
MENZIONE_TRATTATIVA = "{0} mentioned you in a comment on the deal {1}"

ASSEGNATA = "{0} assigned {1} to you"
ASSEGNATA_TRATTATIVA = "{0} assigned you the deal {1}"
TOLTA = "{0} removed your assignment on {1}"
TOLTA_TRATTATIVA = "{0} removed your assignment on the deal {1}"
COMPITO = "{0} assigned you the task {1}"
COMPITO_TOLTO = "{0} removed your assignment on the task {1}"

WHATSAPP = "You received a WhatsApp message from {0}"
WHATSAPP_MOLTI = "You received {1} WhatsApp messages from {0}"
WHATSAPP_TRATTATIVA = "You received a WhatsApp message on the deal {0}"
WHATSAPP_TRATTATIVA_MOLTI = "You received {1} WhatsApp messages on the deal {0}"
SMS = "You received an SMS from {0}"
SMS_MOLTI = "You received {1} SMS from {0}"
SMS_TRATTATIVA = "You received an SMS on the deal {0}"
SMS_TRATTATIVA_MOLTI = "You received {1} SMS on the deal {0}"
EMAIL = "You received an email from {0}"
EMAIL_MOLTI = "You received {1} emails from {0}"
EMAIL_TRATTATIVA = "You received an email on the deal {0}"
EMAIL_TRATTATIVA_MOLTI = "You received {1} emails on the deal {0}"

ESITI_OGGI = "{0} appointments today have no outcome: did they come?"
ESITI_IERI = "{0} appointments yesterday have no outcome: did they come?"

DOMANDA_AREA = "{0} asked the centre a question in their area"

#: Every sentence of this module, for the catalogue's test.
FRASI = (
	MENZIONE,
	MENZIONE_TRATTATIVA,
	ASSEGNATA,
	ASSEGNATA_TRATTATIVA,
	TOLTA,
	TOLTA_TRATTATIVA,
	COMPITO,
	COMPITO_TOLTO,
	WHATSAPP,
	WHATSAPP_MOLTI,
	WHATSAPP_TRATTATIVA,
	WHATSAPP_TRATTATIVA_MOLTI,
	SMS,
	SMS_MOLTI,
	SMS_TRATTATIVA,
	SMS_TRATTATIVA_MOLTI,
	EMAIL,
	EMAIL_MOLTI,
	EMAIL_TRATTATIVA,
	EMAIL_TRATTATIVA_MOLTI,
	ESITI_OGGI,
	ESITI_IERI,
	DOMANDA_AREA,
)

#: The sentences that take something away: the panel draws them apart.
TOLTE = frozenset({TOLTA, TOLTA_TRATTATIVA, COMPITO_TOLTO})

# ------------------------------------------------------------------ what kind it is

#: A notification's type (`CRM Notification.type`) as the panel draws it.
GENERI = {
	"Mention": "mention",
	"WhatsApp": "whatsapp",
	"SMS": "sms",
	"Email": "email",
	"Agenda": "agenda",
	"Area": "area",
	"Invoicing": "invoicing",
	"Automation": "automation",
	"Task": "task",
}


def genere(tipo: str | None, oggetto_doctype: str | None = None, frase: str | None = None) -> str:
	"""What the panel draws: a mention, an assignment or its removal, a task or its
	removal, a message of a channel, the agenda, the client area, invoicing, an
	automation."""
	if tipo == "Assignment":
		if oggetto_doctype == "CRM Task":
			return "task_removed" if frase in TOLTE else "task"
		return "unassigned" if frase in TOLTE else "assigned"
	return GENERI.get(tipo or "", "other")


# ------------------------------------------------------------------ by email too

#: What somebody may receive by email too, when they have not read it in the panel
#: within a few minutes, and the kinds in each.
GRUPPI_EMAIL = {
	"mentions": ("mention",),
	"assignments": ("assigned", "unassigned", "task", "task_removed"),
	"area": ("area",),
	"messages": ("whatsapp", "sms", "email"),
	"agenda": ("agenda",),
	"invoicing": ("invoicing",),
	"automations": ("automation",),
}
#: On until the person says otherwise: what is for them alone. A conversation and
#: the day's question about the agenda are read in DottorCloud.
EMAIL_DI_SOLITO = frozenset({"mentions", "assignments", "area", "invoicing", "automations"})


def gruppo_email(genere: str) -> str | None:
	"""The group of the preferences a kind belongs to."""
	return next((gruppo for gruppo, generi in GRUPPI_EMAIL.items() if genere in generi), None)


def vuole_email(genere: str, scelte: dict | None = None) -> bool:
	"""Whether a kind goes by email too, by the person's choices or the usual ones."""
	gruppo = gruppo_email(genere)
	if not gruppo:
		return False
	if scelte and gruppo in scelte:
		return bool(scelte[gruppo])
	return gruppo in EMAIL_DI_SOLITO


# ------------------------------------------------------------------ the words


def frase(tradotta: str, nomi: list | tuple = (), inglese: str | None = None) -> str:
	"""The sentence with its names in bold, as HTML: the words escaped, the names
	escaped. A translation whose places do not match its names reads in English."""
	valori = [f"<b>{html.escape(str(nome), quote=False)}</b>" for nome in nomi]
	for testo in (tradotta, inglese):
		if not testo:
			continue
		try:
			return html.escape(testo, quote=False).format(*valori)
		except (IndexError, KeyError, ValueError):
			continue
	return html.escape(tradotta or "", quote=False)


def testo_vecchio(testo: str | None) -> str:
	"""The words of a notification written before the sentences were kept apart:
	its names in bold, nothing of the classes it was drawn with, one line."""
	if not testo:
		return ""
	zuppa = BeautifulSoup(testo, "html.parser")
	for nodo in zuppa.find_all(True):
		classi = nodo.get("class") or []
		if nodo.name in ("b", "strong") or "font-medium" in classi or "font-semibold" in classi:
			nodo.name = "b"
			nodo.attrs = {}
		else:
			nodo.unwrap()
	return re.sub(r"\s+", " ", str(zuppa)).strip()


#: Where one block of text ends and another begins: a space between their words.
_FINE_BLOCCO = re.compile(r"<br\s*/?>|</(?:p|div|li|h[1-6]|tr|blockquote)>", re.I)


def solo_testo(testo: str | None) -> str:
	"""Words without their markup, on one line: a space where a paragraph ends,
	none inside a sentence ("@Anna," stays whole)."""
	if not testo:
		return ""
	piano = BeautifulSoup(_FINE_BLOCCO.sub(" ", testo), "html.parser").get_text()
	return re.sub(r"\s+", " ", piano).strip()


def anteprima(testo: str | None, quanto: int = 160) -> str:
	"""A message's first words, without its markup, on one line: cut at a word."""
	piano = solo_testo(testo)
	if len(piano) <= quanto:
		return piano
	taglio = piano[:quanto].rsplit(" ", 1)[0] or piano[:quanto]
	return taglio.rstrip(" ,.;:") + "…"
