# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The client area's other door: a passkey (design.md, "Come si entra": "dalla
volta dopo, se il paziente vuole, una passkey: viso o impronta, che restano sul
telefono").

- **Only after a code**: a passkey is added from inside the area, by whoever
  entered it, never from outside.
- **The key stays on the phone**: the centre keeps the public half (`CRM Area
  Passkey`) and the counter the phone increases at each use; the phone asks for
  the face, the fingerprint or its PIN every time (user verification).
- **The same door as the code**: a passkey opens only an area that is open
  (`accesso.entra_nell_area`); closed, it opens nothing. Entering with it
  counts as entering again for a document, as a code does.
- **No address to type**: the page asks the phone which passkeys it has for the
  site (discoverable credentials), so it tells nobody which addresses have an area.
- Each one is listed in the area with the device it was added from, and removed
  there.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import get_url, now_datetime

from crm.area import accesso

PASSKEY = "CRM Area Passkey"
#: How long the phone has to answer a challenge.
MINUTI_SFIDA = 5
MAX_PASSKEY = 10
#: A credential id as the centre keeps it, base64url: the phones' own are 20-64 bytes.
MAX_ID = 255


def _rp() -> tuple[str, str]:
	"""Who the relying party is: the site's host, and its origin."""
	indirizzo = urlparse(get_url())
	return indirizzo.hostname, f"{indirizzo.scheme}://{indirizzo.netloc}"


def _chiave(scopo: str, token: str) -> str:
	return f"crm:area:passkey:{scopo}:{token}"


def _id_utente(user: str) -> bytes:
	# not the address: a stable handle the phone keeps with the key
	return hashlib.sha256(f"crm-area:{user}".encode()).digest()[:16]


def _utente() -> str:
	utente = frappe.session.user
	if utente == "Guest" or not accesso.entra_nell_area(utente):
		frappe.throw(_("Enter the area first"), frappe.PermissionError)
	return utente


def _dispositivo() -> str:
	"""Which device, in words the person recognises: from the browser's name."""
	richiesta = getattr(frappe.local, "request", None)
	agente = ((richiesta and frappe.get_request_header("User-Agent")) or "").lower()
	for chiave, nome in (
		("iphone", "iPhone"),
		("ipad", "iPad"),
		("android", "Android"),
		("macintosh", "Mac"),
		("windows", "Windows"),
		("linux", "Linux"),
	):
		if chiave in agente:
			return nome
	return _("This device")


def _righe(user: str) -> list[dict]:
	return frappe.get_all(
		PASSKEY,
		filters={"user": user},
		fields=["name", "label", "created_on", "last_used_on"],
		order_by="created_on desc",
	)


@frappe.whitelist()
def my_passkeys() -> dict:
	"""The session's passkeys, to see and remove."""
	return {"passkeys": _righe(_utente())}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def registration_options() -> dict:
	"""What the phone needs to make a passkey for this area."""
	from webauthn import generate_registration_options, options_to_json
	from webauthn.helpers import base64url_to_bytes
	from webauthn.helpers.structs import (
		AuthenticatorSelectionCriteria,
		PublicKeyCredentialDescriptor,
		ResidentKeyRequirement,
		UserVerificationRequirement,
	)

	from crm.moduli.richieste import nome_del_centro

	utente = _utente()
	gia = frappe.get_all(PASSKEY, filters={"user": utente}, pluck="credential_id")
	if len(gia) >= MAX_PASSKEY:
		frappe.throw(_("Remove a passkey first: an area keeps {0}").format(MAX_PASSKEY))
	rp_id, _origine = _rp()
	opzioni = generate_registration_options(
		rp_id=rp_id,
		rp_name=nome_del_centro() or _("Your area"),
		user_id=_id_utente(utente),
		user_name=utente,
		user_display_name=frappe.utils.get_fullname(utente),
		authenticator_selection=AuthenticatorSelectionCriteria(
			resident_key=ResidentKeyRequirement.REQUIRED,
			user_verification=UserVerificationRequirement.REQUIRED,
		),
		exclude_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(c)) for c in gia],
	)
	frappe.cache.set_value(
		_chiave("registra", frappe.session.sid), opzioni.challenge, expires_in_sec=MINUTI_SFIDA * 60
	)
	return json.loads(options_to_json(opzioni))


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def register(credential: str | dict) -> dict:
	"""The passkey the phone made: its public half is kept, the rest stays there."""
	from webauthn import verify_registration_response
	from webauthn.helpers import bytes_to_base64url

	utente = _utente()
	chiave = _chiave("registra", frappe.session.sid)
	sfida = frappe.cache.get_value(chiave)
	frappe.cache.delete_value(chiave)
	if not sfida:
		frappe.throw(_("Too slow: try again"))
	rp_id, origine = _rp()
	dati = frappe.parse_json(credential) if isinstance(credential, str) else credential
	try:
		verificata = verify_registration_response(
			credential=dati,
			expected_challenge=sfida,
			expected_rp_id=rp_id,
			expected_origin=origine,
			require_user_verification=True,
		)
	except Exception:
		frappe.throw(_("The passkey could not be added: try again"))
	credenziale = bytes_to_base64url(verificata.credential_id)
	if len(credenziale) > MAX_ID:
		frappe.throw(_("This passkey cannot be kept here: use another device"))
	trasporti = ((dati.get("response") or {}).get("transports")) or []
	frappe.get_doc(
		{
			"doctype": PASSKEY,
			"user": utente,
			"label": _dispositivo(),
			"created_on": now_datetime(),
			"credential_id": credenziale,
			"public_key": bytes_to_base64url(verificata.credential_public_key),
			"sign_count": verificata.sign_count,
			"transports": ",".join(str(t) for t in trasporti)[:140] or None,
		}
	).insert(ignore_permissions=True)
	return {"passkeys": _righe(utente)}


@frappe.whitelist(methods=["POST"])
def remove_passkey(name: str) -> dict:
	utente = _utente()
	if frappe.db.get_value(PASSKEY, name, "user") != utente:
		frappe.throw(_("This is not your passkey"), frappe.PermissionError)
	frappe.delete_doc(PASSKEY, name, ignore_permissions=True)
	return {"passkeys": _righe(utente)}


# nosemgrep: guest-whitelisted-method — a challenge, nothing about anybody
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=60, seconds=60 * 60)
def authentication_options() -> dict:
	"""A challenge for the phone: which passkey answers, the phone decides."""
	from webauthn import generate_authentication_options, options_to_json
	from webauthn.helpers.structs import UserVerificationRequirement

	rp_id, _origine = _rp()
	opzioni = generate_authentication_options(
		rp_id=rp_id, user_verification=UserVerificationRequirement.REQUIRED
	)
	stato = secrets.token_urlsafe(24)
	frappe.cache.set_value(_chiave("entra", stato), opzioni.challenge, expires_in_sec=MINUTI_SFIDA * 60)
	return {"options": json.loads(options_to_json(opzioni)), "state": stato}


# nosemgrep: guest-whitelisted-method — the signature of the phone's key is the credential
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=60, seconds=60 * 60)
def authenticate(credential: str | dict, state: str) -> dict:
	"""The phone's answer: the right key of an open area enters it."""
	from webauthn import verify_authentication_response
	from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
	from webauthn.helpers.parse_authentication_credential_json import parse_authentication_credential_json

	chiave = _chiave("entra", state or "")
	sfida = frappe.cache.get_value(chiave)
	frappe.cache.delete_value(chiave)
	if not sfida:
		frappe.throw(_("Too slow: try again"))
	dati = frappe.parse_json(credential) if isinstance(credential, str) else credential
	try:
		letta = parse_authentication_credential_json(dati)
	except Exception:
		frappe.throw(_("This passkey does not open an area here"), frappe.PermissionError)
	riga = frappe.db.get_value(
		PASSKEY,
		{"credential_id": bytes_to_base64url(letta.raw_id)},
		["name", "user", "public_key", "sign_count"],
		as_dict=True,
	)
	if not riga:
		frappe.throw(_("This passkey does not open an area here"), frappe.PermissionError)
	rp_id, origine = _rp()
	try:
		verificata = verify_authentication_response(
			credential=letta,
			expected_challenge=sfida,
			expected_rp_id=rp_id,
			expected_origin=origine,
			credential_public_key=base64url_to_bytes(riga.public_key),
			credential_current_sign_count=riga.sign_count or 0,
			require_user_verification=True,
		)
	except Exception:
		frappe.throw(_("This passkey does not open an area here"), frappe.PermissionError)
	if not accesso.entra_nell_area(riga.user):
		frappe.throw(_("This area is closed: ask the centre"), frappe.PermissionError)
	frappe.db.set_value(
		PASSKEY,
		riga.name,
		{"sign_count": verificata.new_sign_count, "last_used_on": now_datetime()},
		update_modified=False,
	)
	if frappe.session.user != riga.user:
		frappe.local.login_manager.login_as(riga.user)
	# as a code does: entering again clears a report's download
	accesso.segna_verificato()
	return {"ok": True}
