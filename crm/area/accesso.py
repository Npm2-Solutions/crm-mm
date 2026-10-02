# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The door of the client area: an invitation from the centre, a code by email.

- **The invitation** is the centre's (`area.invita`): it opens the area of a
  person to their own address, or to whoever answers for them (a parent, a
  guardian) or follows them. A user of the site is made if there is none, with
  the area's role and no access to the desk; the email says only that the area is
  open.
- **The code**: six digits by email, ten minutes, five tries. Whoever asks gets
  the same answer, registered or not: the page does not tell which addresses
  have an area. Only an area's user enters this way, never staff.
- **Again, for a document**: a download asks for a code verified in the last
  fifteen minutes (design.md: "per scaricare un referto si rientra").
- **A passkey** is the other door, added from inside (`crm.area.passkey`).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, get_url, now_datetime, validate_email_address

from crm.permissions import livelli
from crm.posta.aspetto import codice as casella
from crm.posta.aspetto import pulsante

#: The role of whoever enters an area: a user of the site, never of the desk.
RUOLO = "Client Area User"
ACCESSO = "CRM Area Access"
SE_STESSO, TUTORE, SEGUE = "Self", "Parent or guardian", "Follows them"
RELAZIONI = (SE_STESSO, TUTORE, SEGUE)
MINUTI_CODICE = 10
TENTATIVI = 5
#: How long a verified code lets the area hand over a report.
MINUTI_VERIFICA = 15


def _impronta(testo: str) -> str:
	return hashlib.sha256(testo.encode("utf-8")).hexdigest()


def _uguali(a: str | None, b: str | None) -> bool:
	return bool(a) and bool(b) and hmac.compare_digest(a, b)


def _codice() -> str:
	return f"{secrets.randbelow(10**6):06d}"


def _chiave_codice(email: str) -> str:
	return f"crm-area-code:{_impronta(email)}"


def _chiave_verifica(sid: str) -> str:
	return f"crm-area-verified:{sid}"


def _normalizza(email: str | None) -> str:
	return (email or "").strip().lower()


def assicura_ruolo() -> None:
	"""The area's role: a user of the site, never of the desk."""
	if frappe.db.exists("Role", RUOLO):
		return
	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": RUOLO,
			"desk_access": 0,
			"is_custom": 1,
			"description": "Enters the client area of the centre: never the desk",
		}
	).insert(ignore_permissions=True)


def persone_di(user: str | None = None) -> list[dict]:
	"""The people whose area ``user`` enters."""
	return frappe.get_all(
		ACCESSO,
		filters={"user": user or frappe.session.user, "enabled": 1},
		fields=["lead", "lead_name", "relation"],
		order_by="relation asc, lead_name asc",
	)


def entra_nell_area(user: str) -> bool:
	"""Whether ``user`` is somebody who enters an area now: a user of the site, with
	the role, and at least one person given."""
	return (
		frappe.db.get_value("User", user, "user_type") == "Website User"
		and RUOLO in frappe.get_roles(user)
		and bool(persone_di(user))
	)


# ------------------------------------------------------------------ the centre's side


def _destinatario(lead: str, relazione: str) -> str | None:
	"""The person's own address; for who answers for them, the representative's."""
	if relazione == SE_STESSO:
		return frappe.db.get_value("CRM Lead", lead, "email")
	from crm.moduli import richieste

	return richieste.destinatario(lead).get("email")


def _utente_per(email: str, nome: str) -> str:
	utente = frappe.db.get_value("User", {"name": email})
	if utente:
		if frappe.db.get_value("User", utente, "user_type") != "Website User":
			# a colleague's address: staff never enter the area
			frappe.throw(
				_("{0} is a user of the centre: the area is for the people it looks after").format(email)
			)
		doc = frappe.get_doc("User", utente)
		if RUOLO not in [r.role for r in doc.roles]:
			doc.append("roles", {"role": RUOLO})
			doc.save(ignore_permissions=True)
		return utente
	primo, _spazio, resto = (nome or email).partition(" ")
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": primo or email,
			"last_name": resto or None,
			"user_type": "Website User",
			"send_welcome_email": 0,
			"roles": [{"role": RUOLO}],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist(methods=["POST"])
def invite(lead: str, relation: str = SE_STESSO, email: str | None = None) -> dict:
	"""Open a person's area: to them, or to who answers for them or follows them."""
	livelli.verifica("area.invita")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	if relation not in RELAZIONI:
		frappe.throw(_("{0} is not a way to enter an area").format(relation))
	indirizzo = _normalizza(email) or _normalizza(_destinatario(lead, relation))
	if not indirizzo:
		frappe.throw(_("There is no email address to open the area to"))
	validate_email_address(indirizzo, throw=True)
	assicura_ruolo()
	nome = frappe.db.get_value("CRM Lead", lead, "lead_name")
	utente = _utente_per(indirizzo, nome if relation == SE_STESSO else "")
	riga = frappe.db.get_value(ACCESSO, {"user": utente, "lead": lead}, "name")
	adesso = now_datetime()
	if riga:
		frappe.db.set_value(
			ACCESSO,
			riga,
			{
				"enabled": 1,
				"relation": relation,
				"granted_by": frappe.session.user,
				"granted_on": adesso,
				"revoked_by": None,
				"revoked_on": None,
			},
		)
	else:
		frappe.get_doc(
			{
				"doctype": ACCESSO,
				"user": utente,
				"lead": lead,
				"relation": relation,
				"enabled": 1,
				"granted_by": frappe.session.user,
				"granted_on": adesso,
			}
		).insert(ignore_permissions=True)
	_manda_l_invito(indirizzo)
	return {"user": utente, "email": indirizzo, "accesses": accessi(lead)}


def _manda_l_invito(email: str) -> None:
	from crm.moduli.richieste import nome_del_centro

	centro = nome_del_centro() or _("your centre")
	esc = frappe.utils.escape_html
	try:
		frappe.sendmail(
			recipients=[email],
			subject=_("Your area at {0}").format(centro),
			header=_("Your area at {0}").format(esc(centro)),
			with_container=True,
			message="".join(
				[
					"<p>{}</p>".format(
						esc(
							_(
								"{0} opened your area: your appointments, the documents they give you, "
								"your invoices."
							).format(centro)
						)
					),
					pulsante(get_url("/area"), _("Enter your area")),
					'<p class="text-muted text-small">{}</p>'.format(
						esc(_("You enter with this address: we send you a code each time."))
					),
				]
			),
		)
	except frappe.OutgoingEmailError:
		# no mail from this site: the person is told at the desk
		frappe.clear_last_message()


@frappe.whitelist(methods=["POST"])
def revoke(lead: str, user: str) -> dict:
	"""Close an area to somebody: at once, and it stays in the trace."""
	livelli.verifica("area.invita")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	riga = frappe.db.get_value(ACCESSO, {"user": user, "lead": lead}, "name")
	if not riga:
		frappe.throw(_("This person does not enter this area"))
	frappe.db.set_value(
		ACCESSO,
		riga,
		{"enabled": 0, "revoked_by": frappe.session.user, "revoked_on": now_datetime()},
	)
	return {"accesses": accessi(lead)}


def accessi_aperti(lead: str) -> list[dict]:
	"""Who enters this person's area now."""
	return frappe.get_all(ACCESSO, filters={"lead": lead, "enabled": 1}, fields=["user", "relation"])


def accessi(lead: str) -> list[dict]:
	return frappe.get_all(
		ACCESSO,
		filters={"lead": lead},
		fields=["user", "relation", "enabled", "granted_on", "revoked_on", "last_seen_on"],
		order_by="enabled desc, granted_on desc",
	)


@frappe.whitelist()
def get_accesses(lead: str) -> dict:
	"""Who enters this person's area: for the person's page."""
	livelli.verifica("area.invita")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	return {
		"accesses": accessi(lead),
		"email": frappe.db.get_value("CRM Lead", lead, "email"),
		"url": get_url("/area"),
	}


# ------------------------------------------------------------------ the person's side


def _mandalo(email: str, codice: str) -> None:
	from crm.moduli.richieste import nome_del_centro

	centro = nome_del_centro() or _("your centre")
	esc = frappe.utils.escape_html
	posta = frappe.sendmail(
		recipients=[email],
		subject=_("Your code: {0}").format(codice),
		header=_("Your code"),
		with_container=True,
		message="".join(
			[
				"<p>{}</p>".format(esc(_("Here is the code to enter the area of {0}:").format(centro))),
				casella(codice),
				'<p class="text-muted text-small">{}</p>'.format(
					esc(
						_("It is valid for {0} minutes. If you did not ask for it, ignore this email.")
					).format(MINUTI_CODICE)
				),
			]
		),
	)
	if posta:
		from crm.moduli.richieste import _subito

		frappe.db.after_commit.add(lambda: _subito(posta))


# nosemgrep: guest-whitelisted-method — says nothing of who is registered; 5 codes an hour
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def send_code(email: str | None = None) -> dict:
	"""A code to this address, if it has an area. The answer is the same either way.
	Logged in, it is the session's own address: a code again, for a report."""
	indirizzo = frappe.session.user if frappe.session.user != "Guest" else _normalizza(email)
	if not indirizzo:
		frappe.throw(_("Write your email address"))
	if entra_nell_area(indirizzo):
		chiave = _chiave_codice(indirizzo)
		precedente = frappe.cache.get_value(chiave) or {}
		inviati = cint(precedente.get("sent")) + 1
		if inviati <= TENTATIVI:
			codice = _codice()
			frappe.cache.set_value(
				chiave,
				{"hash": _impronta(indirizzo + codice), "attempts": 0, "sent": inviati},
				expires_in_sec=MINUTI_CODICE * 60,
			)
			try:
				_mandalo(indirizzo, codice)
			except frappe.OutgoingEmailError:
				frappe.clear_last_message()
				frappe.log_error(title="Area code not sent: no outgoing email account")
	return {"sent": True, "minutes": MINUTI_CODICE}


# nosemgrep: guest-whitelisted-method — the code is the credential, five tries
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=60, seconds=60 * 60)
def verify_code(code: str, email: str | None = None) -> dict:
	"""The right code enters the area; logged in already, it clears a download."""
	indirizzo = frappe.session.user if frappe.session.user != "Guest" else _normalizza(email)
	chiave = _chiave_codice(indirizzo)
	salvato = frappe.cache.get_value(chiave)
	if not salvato:
		frappe.throw(_("The code has expired: ask for a new one"))
	if cint(salvato.get("attempts")) >= TENTATIVI:
		frappe.throw(_("Too many wrong codes: ask for a new one"))
	if not _uguali(_impronta(indirizzo + (code or "").strip()), salvato.get("hash")):
		salvato["attempts"] = cint(salvato.get("attempts")) + 1
		frappe.cache.set_value(chiave, salvato, expires_in_sec=MINUTI_CODICE * 60)
		frappe.throw(_("The code is not right"))
	frappe.cache.delete_value(chiave)
	if not entra_nell_area(indirizzo):
		frappe.throw(_("This area is closed: ask the centre"), frappe.PermissionError)
	if frappe.session.user == "Guest":
		frappe.local.login_manager.login_as(indirizzo)
	segna_verificato()
	return {"ok": True}


def segna_verificato() -> None:
	"""The session entered again just now, by a code or a passkey: a report may be
	downloaded for a while."""
	frappe.cache.set_value(_chiave_verifica(frappe.session.sid), 1, expires_in_sec=MINUTI_VERIFICA * 60)


def verificato_da_poco() -> bool:
	return bool(frappe.cache.get_value(_chiave_verifica(frappe.session.sid)))
