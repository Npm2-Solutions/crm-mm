# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The link by email that enters the client area: every email of the area's says
only that there is something new, and its button enters the area without a code.

- **Once, within seven days.** Only the link's fingerprint is kept (`CRM Area
  Link`); the first entry spends it. An old or used link is not an error page:
  the door asks for the email and sends a code, the same answer for everybody.
- **A tap, never the opening.** The link opens the door, and the door's «Enter»
  sends it back (a POST): the programs that open every link of an email, to look
  for viruses, never spend it.
- **Entering by it counts as a code just read**: the email reached the address,
  and a document may be downloaded at once (`accesso.segna_verificato`).
- **The email never says what**: no health data, no amount, no attachment. The
  document stays in the area, where the person enters.
- **A new document**, where the centre wants it (`CRM Area Settings.email_new_documents`,
  off to start with): an invoice issued to a person. A document given online has
  its own link and code (`crm.documenti.consegna`).
  Whoever has no area yet gets it then: the person, or the parent or guardian
  for a minor, as the forms' links do (`richieste.destinatario`). A test invoice,
  a demo person, an address the centre's own users have: never.
"""

from __future__ import annotations

import hashlib
import secrets
from urllib.parse import urlencode

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days, add_to_date, cint, escape_html, get_datetime, get_url, now_datetime

from crm.area import accesso

LINK = "CRM Area Link"
GIORNI = 7
#: A new document while the email of the one before is still unread: that email's
#: link is there to use, and a second «news in your area» says nothing more - two
#: arrived four seconds apart, a visit's balance and the next visit's deposit.
ANCORA_DA_LEGGERE = 24
#: Where a link may land in the area: the router's pages.
PAGINE = ("", "documents", "messages", "appointments", "plans")


def _impronta(token: str) -> str:
	return hashlib.sha256(token.encode("utf-8")).hexdigest()


def crea(user: str, lead: str | None = None, motivo: str = "", pagina: str = "") -> str:
	"""A link that enters ``user``'s area once, within seven days, on ``pagina``."""
	token = secrets.token_urlsafe(32)
	frappe.get_doc(
		{
			"doctype": LINK,
			"user": user,
			"lead": lead,
			"reason": motivo,
			"page": pagina if pagina in PAGINE else "",
			"token_hash": _impronta(token),
			"expires_on": add_days(now_datetime(), GIORNI),
		}
	).insert(ignore_permissions=True)
	return get_url("/area/login?" + urlencode({"link": token}))


# nosemgrep: guest-whitelisted-method — the link is the credential, spent once; 60 tries an hour
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=60, seconds=60 * 60)
def enter(link: str) -> dict:
	"""The door's «Enter» with a link: the area's session, and the page it was for."""
	riga = frappe.db.get_value(
		LINK,
		{"token_hash": _impronta((link or "").strip())},
		["name", "user", "page", "expires_on", "used_on"],
		as_dict=True,
	)
	if not riga or riga.used_on or get_datetime(riga.expires_on) < now_datetime():
		frappe.throw(_("This link no longer works: write your email and we send you a code"))
	# spent before anything else: two taps never enter twice
	frappe.db.set_value(LINK, riga.name, "used_on", now_datetime(), update_modified=False)
	if not accesso.entra_nell_area(riga.user):
		frappe.throw(_("This area is closed: ask the centre"), frappe.PermissionError)
	if frappe.session.user != riga.user:
		frappe.local.login_manager.login_as(riga.user)
	accesso.segna_verificato()
	return {"page": riga.page or ""}


# ------------------------------------------------------------------ telling


def manda(user: str, lead: str | None, motivo: str, pagina: str = "") -> bool:
	"""The email that says there is something new in the area, with its link.
	Never raises: what caused it matters more than the email about it."""
	from crm.moduli.richieste import nome_del_centro
	from crm.posta.aspetto import pulsante

	centro = nome_del_centro() or _("your centre")
	try:
		indirizzo = crea(user, lead, motivo, pagina)
		frappe.sendmail(
			recipients=[user],
			subject=_("News in your area at {0}").format(centro),
			header=_("News in your area"),
			with_container=True,
			message="".join(
				[
					"<p>{}</p>".format(
						escape_html(_("There is news for you in your area at {0}.").format(centro))
					),
					pulsante(indirizzo, _("Open your area")),
					'<p class="text-muted text-small">{}</p>'.format(
						escape_html(
							_(
								"The button enters your area without a code, once, within {0} days. Then you enter with your email, as always."
							).format(GIORNI)
						)
					),
				]
			),
		)
	except frappe.OutgoingEmailError:
		frappe.clear_last_message()
		return False
	except Exception:
		frappe.clear_last_message()
		frappe.log_error(title=f"Area link not sent: {motivo}")
		return False
	return True


def attivo() -> bool:
	return bool(cint(frappe.db.get_single_value("CRM Area Settings", "email_new_documents")))


def _della_demo(lead: str) -> bool:
	from crm.demo import guardie, registro

	return guardie.attiva() and (
		registro.raccolta() is not None or lead in registro.nomi_di_prova("CRM Lead")
	)


def apri_se_serve(lead: str) -> list[str]:
	"""Whoever enters this person's area; nobody yet, it is opened for them: to the
	person, or to whoever answers for them. Nobody to open it to: nobody."""
	aperti = sorted({riga.user for riga in accesso.accessi_aperti(lead)})
	if aperti:
		return aperti
	from crm.moduli import richieste

	dove = richieste.destinatario(lead)
	indirizzo = (dove.get("email") or "").strip().lower()
	if not indirizzo:
		return []
	tipo = frappe.db.get_value("User", indirizzo, "user_type")
	if tipo and tipo != "Website User":
		# a colleague's address on the person: staff never enter the area
		return []
	relazione = accesso.SE_STESSO if dove.get("lead") == lead else accesso.TUTORE
	accesso.apri(lead, relazione, indirizzo, invito=False)
	return [indirizzo]


def documento_nuovo(lead: str, motivo: str) -> list[str]:
	"""A new document for ``lead`` in the area: each who enters it gets the email
	with their own link, if the centre wants it. Returns who was told."""
	if not lead or not attivo() or _della_demo(lead):
		return []
	try:
		utenti = apri_se_serve(lead)
	except Exception:
		frappe.clear_last_message()
		frappe.log_error(title=f"Area not opened for {lead}")
		return []
	return [
		utente
		for utente in utenti
		if not _ancora_da_leggere(utente, motivo) and manda(utente, lead, motivo, "documents")
	]


def _ancora_da_leggere(utente: str, motivo: str) -> bool:
	"""Whether ``utente`` has the email of a new document still unread: its link
	not used, sent in the last `ANCORA_DA_LEGGERE` hours."""
	return bool(
		frappe.db.exists(
			LINK,
			{
				"user": utente,
				"reason": motivo,
				"used_on": ["is", "not set"],
				"creation": [">", add_to_date(now_datetime(), hours=-ANCORA_DA_LEGGERE)],
			},
		)
	)


def fattura_emessa(doc, method=None) -> None:
	"""`CRM Invoice` on_submit: an invoice to a person, or the credit note that
	corrects one, is a new document of theirs. A test invoice is the centre's
	rehearsal: never."""
	if doc.get("test_document") or doc.get("party_type") != "CRM Lead" or not doc.get("party"):
		return
	documento_nuovo(doc.party, "invoice")
