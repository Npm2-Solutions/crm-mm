# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Notifications on the phone and the computer (Web Push), with nobody in between
who reads them (docs/progetto-ghl/43).

- **Where**: each browser, or the app put on a phone's home screen, that somebody
  turns on in Settings > Your account > Notifications subscribes with its maker's
  push service and leaves here how to reach it (`CRM Push Subscription`, each
  person their own). On an iPhone only the app on the home screen can: Safari's
  rule. Only the makers' push services are written to (`SERVIZI`).
- **What**: every notification the panel receives (`avvisi.avvisa`), but the kinds
  the person turned off for their devices (the groups of `regole.GRUPPI_EMAIL`,
  all on until they say otherwise), in their language: the panel's sentence, the
  first words of the message where they may read them, the page it opens. Never
  about the demo data.
- **How**: in a job once the notification is written, encrypted for each browser
  and signed with the site's key (`spinta_regole`); a device the push service says
  is gone is forgotten, one that fails `TENTATIVI` times in a row too. A
  notification that reached a device does not go by email as well.
- **The page's side**: a service worker (`service_worker`) over /crm, which shows
  the notification and opens DottorCloud where it points; it keeps nothing in a
  cache and answers no request of the page.
"""

from __future__ import annotations

import hashlib
import json
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import frappe
import requests
from frappe import _
from frappe.utils import get_url, now_datetime
from frappe.utils.password import get_decrypted_password, set_encrypted_password

from crm.marchio import attivo
from crm.notifiche import posta
from crm.notifiche import regole as R
from crm.notifiche import spinta_regole as S

ABBONAMENTO = "CRM Push Subscription"
NOTIFICA = "CRM Notification"
IMPOSTAZIONI = "FCRM Settings"
#: Where a person's choices of kinds are kept: a default of theirs.
CHIAVE = "crm_notifications_by_push"
#: The pages the service worker looks after: DottorCloud's.
AMBITO = "/crm"
#: Seconds a notification waits at the push service for a phone switched off.
VITA = 12 * 60 * 60
#: Failures in a row after which a device is forgotten.
TENTATIVI = 5
#: The push services of the browsers' makers: the only addresses written to.
SERVIZI = (
	"fcm.googleapis.com",
	"android.googleapis.com",
	"push.apple.com",
	"push.services.mozilla.com",
	"notify.windows.com",
)
#: The longest title and text a notification carries: a phone shows less.
TITOLO = 120
TESTO = 240
CAMPI_NOTIFICA = [
	"name",
	"to_user",
	"from_user",
	"type",
	"sentence",
	"sentence_args",
	"notification_text",
	"message",
	"count",
	"read",
	"creation",
	"reference_doctype",
	"reference_name",
	"notification_type_doctype",
	"notification_type_doc",
	"comment",
]


# ------------------------------------------------------------------ the site's keys


def chiavi() -> tuple[str, str]:
	"""The site's pair, private and public, made the first time it is needed."""
	pubblica = frappe.db.get_single_value(IMPOSTAZIONI, "push_public_key")
	if pubblica:
		privata = get_decrypted_password(
			IMPOSTAZIONI, IMPOSTAZIONI, "push_private_key", raise_exception=False
		)
		if privata and S.pubblica_di(privata) == pubblica:
			return privata, pubblica
	privata, pubblica = S.nuove_chiavi()
	set_encrypted_password(IMPOSTAZIONI, IMPOSTAZIONI, privata, "push_private_key")
	frappe.db.set_single_value(IMPOSTAZIONI, "push_public_key", pubblica)
	return privata, pubblica


# ------------------------------------------------------------------ the choices


def preferenze(utente: str | None = None) -> dict:
	"""A person's choices for their devices: the groups they turned off or on."""
	valore = frappe.defaults.get_user_default(CHIAVE, user=utente or frappe.session.user)
	try:
		scelte = json.loads(valore) if valore else {}
	except ValueError:
		scelte = {}
	return {k: bool(v) for k, v in scelte.items() if k in R.GRUPPI_EMAIL} if isinstance(scelte, dict) else {}


def vuole(genere: str, scelte: dict | None = None) -> bool:
	"""Whether a kind reaches the person's devices: every group, unless turned off."""
	gruppo = R.gruppo_email(genere)
	return bool(gruppo) and bool((scelte or {}).get(gruppo, True))


# ------------------------------------------------------------------ a device


def impronta(endpoint: str) -> str:
	"""How a device is found again: its address, never shown."""
	return hashlib.sha256(endpoint.encode()).hexdigest()


def servizio_ammesso(endpoint: str) -> bool:
	"""Only a browser maker's push service: never any other address of the world."""
	try:
		S.origine(endpoint)
	except ValueError:
		return False
	host = (urlsplit(endpoint).hostname or "").lower()
	return any(host == nome or host.endswith("." + nome) for nome in SERVIZI)


def _del_centro() -> None:
	"""Only who works in DottorCloud: a client area's person has no panel to bring
	to a phone."""
	from crm.api import check_app_permission

	if frappe.session.user == "Guest" or not check_app_permission():
		raise frappe.PermissionError


def _miei() -> list[dict]:
	return frappe.get_all(
		ABBONAMENTO,
		filters={"user": frappe.session.user},
		fields=["name", "device", "endpoint_hash", "creation", "last_sent"],
		order_by="creation desc",
	)


@frappe.whitelist()
def get_push() -> dict:
	"""What the page needs: the key a browser subscribes with, the session's
	devices, and which kinds reach them."""
	_del_centro()
	_privata, pubblica = chiavi()
	scelte = preferenze()
	return {
		"public_key": pubblica,
		"devices": _miei(),
		"groups": [
			{"key": gruppo, "on": scelte.get(gruppo, True)}
			for gruppo in R.GRUPPI_EMAIL
			if posta.riceve(gruppo)
		],
	}


@frappe.whitelist(methods=["POST"])
def subscribe(subscription: dict | str, installed: int | str = 0) -> dict:
	"""This browser receives the session's notifications from now on; a browser
	somebody else had turned on on the same device becomes this person's."""
	_del_centro()
	dati = frappe.parse_json(subscription) if isinstance(subscription, str) else (subscription or {})
	endpoint = str(dati.get("endpoint") or "").strip()
	chiavi_browser = dati.get("keys") or {}
	p256dh = str(chiavi_browser.get("p256dh") or "").strip()
	auth = str(chiavi_browser.get("auth") or "").strip()
	if not servizio_ammesso(endpoint):
		frappe.throw(_("This browser does not receive notifications"))
	try:
		S.cifra(b"", p256dh, auth)
	except (ValueError, TypeError):
		frappe.throw(_("This browser does not receive notifications"))
	segno = impronta(endpoint)
	valori = {
		"user": frappe.session.user,
		"device": S.dispositivo(frappe.get_request_header("User-Agent") or "", bool(int(installed or 0))),
		"endpoint": endpoint,
		"p256dh": p256dh,
		"auth": auth,
		"failures": 0,
	}
	nome = frappe.db.get_value(ABBONAMENTO, {"endpoint_hash": segno})
	if nome:
		frappe.db.set_value(ABBONAMENTO, nome, valori)
	else:
		frappe.get_doc({"doctype": ABBONAMENTO, "endpoint_hash": segno, **valori}).insert(
			ignore_permissions=True
		)
	return get_push()


@frappe.whitelist(methods=["POST"])
def unsubscribe(name: str | None = None, endpoint_hash: str | None = None) -> dict:
	"""One of the session's devices no longer receives: this browser, or another
	from the list."""
	_del_centro()
	filtri = {"user": frappe.session.user}
	if name:
		filtri["name"] = name
	elif endpoint_hash:
		filtri["endpoint_hash"] = endpoint_hash
	else:
		frappe.throw(_("Which device?"))
	for nome in frappe.get_all(ABBONAMENTO, filters=filtri, pluck="name"):
		frappe.delete_doc(ABBONAMENTO, nome, ignore_permissions=True, force=True)
	return get_push()


@frappe.whitelist(methods=["POST"])
def save_push_preferences(groups: dict | str) -> dict:
	"""The session's choices: which groups reach its devices. Only one's own."""
	_del_centro()
	scelte = frappe.parse_json(groups) if isinstance(groups, str) else (groups or {})
	if not isinstance(scelte, dict):
		frappe.throw(_("Choose what reaches your devices"))
	pulite = {k: bool(v) for k, v in scelte.items() if k in R.GRUPPI_EMAIL}
	frappe.defaults.set_user_default(CHIAVE, json.dumps(pulite), user=frappe.session.user)
	return get_push()


@frappe.whitelist(methods=["POST"])
def send_test() -> dict:
	"""A notification to the session's own devices, to see that they arrive."""
	_del_centro()
	abbonamenti = _abbonamenti(frappe.session.user)
	if not abbonamenti:
		frappe.throw(_("No device of yours receives notifications yet"))
	contenuto = {
		"title": attivo().nome,
		"body": _("Notifications reach this device."),
		"url": f"{AMBITO}/notifications",
		"tag": "crm-test",
	}
	arrivate = _spedisci_a_tutti(abbonamenti, contenuto)
	return {"sent": arrivate, "devices": len(abbonamenti)}


# ------------------------------------------------------------------ sending


def accoda(notifica, solo_nel_pannello: bool = False) -> None:
	"""Once a notification is written: to the person's devices, in a job, if they
	have any and want its kind."""
	if solo_nel_pannello or not frappe.db.exists(ABBONAMENTO, {"user": notifica.to_user}):
		return
	genere = R.genere(notifica.type, notifica.notification_type_doctype, notifica.sentence)
	if not vuole(genere, preferenze(notifica.to_user)):
		return
	frappe.enqueue(
		"crm.notifiche.spinta.manda",
		queue="short",
		notifica=notifica.name,
		enqueue_after_commit=True,
	)


def _abbonamenti(utente: str) -> list[dict]:
	return frappe.get_all(
		ABBONAMENTO,
		filters={"user": utente},
		fields=["name", "endpoint", "p256dh", "auth", "failures"],
	)


def messaggio(riga: dict, notifica: str) -> dict:
	"""What a device shows of a panel's row: the sentence, the first words of the
	message, the page it opens - which marks it read - and one place for a
	conversation, which a newer message takes."""
	indirizzo = urlsplit(posta.indirizzo(riga.get("route")))
	parametri = [*parse_qsl(indirizzo.query), ("notifica", notifica)]
	pagina = urlunsplit(("", "", indirizzo.path, urlencode(parametri), indirizzo.fragment))
	route = riga.get("route") or {}
	return {
		"title": R.solo_testo(riga.get("text"))[:TITOLO] or attivo().nome,
		"body": R.solo_testo(riga.get("excerpt"))[:TESTO],
		"url": pagina,
		"tag": f"{riga.get('kind')}:{json.dumps(route.get('params') or {}, sort_keys=True)}"
		if riga.get("kind") in R.GRUPPI_EMAIL["messages"]
		else notifica,
	}


def manda(notifica: str, sessione: requests.Session | None = None) -> int:
	"""A notification to its person's devices; how many it reached. One that
	reached a device does not go by email too."""
	from crm.notifiche import api

	riga = frappe.db.get_value(NOTIFICA, notifica, CAMPI_NOTIFICA, as_dict=True)
	if not riga or riga.read:
		return 0
	abbonamenti = _abbonamenti(riga.to_user)
	if not abbonamenti:
		return 0
	with posta.nella_lingua_di(riga.to_user):
		pannello = api.righe_del_pannello([riga], riga.to_user)
		contenuto = messaggio(pannello[0], notifica)
	arrivate = _spedisci_a_tutti(abbonamenti, contenuto, sessione)
	if arrivate:
		frappe.db.set_value(NOTIFICA, notifica, "email_due", 0, update_modified=False)
	return arrivate


def _spedisci_a_tutti(abbonamenti: list[dict], contenuto: dict, sessione=None) -> int:
	privata, _pubblica = chiavi()
	dati = json.dumps({k: v for k, v in contenuto.items() if v is not None}, ensure_ascii=False).encode()
	propria = sessione is None
	sessione = sessione or requests.Session()
	try:
		return sum(_spedisci(sessione, a, dati, privata) for a in abbonamenti)
	finally:
		if propria:
			sessione.close()


def _spedisci(sessione, abbonamento: dict, dati: bytes, privata: str) -> bool:
	if not servizio_ammesso(abbonamento["endpoint"]):
		_dimentica(abbonamento["name"])
		return False
	try:
		corpo = S.cifra(dati, abbonamento["p256dh"], abbonamento["auth"])
		intestazioni = {
			**S.firma(abbonamento["endpoint"], privata, get_url()),
			"TTL": str(VITA),
			"Urgency": "normal",
			"Content-Encoding": "aes128gcm",
			"Content-Type": "application/octet-stream",
		}
		risposta = sessione.post(abbonamento["endpoint"], data=corpo, headers=intestazioni, timeout=(5, 15))
	except (ValueError, requests.RequestException):
		_fallita(abbonamento)
		return False
	if risposta.status_code in (200, 201, 202):
		frappe.db.set_value(
			ABBONAMENTO,
			abbonamento["name"],
			{"last_sent": now_datetime(), "failures": 0},
			update_modified=False,
		)
		return True
	if risposta.status_code in (404, 410):
		# the browser let it go: the push service no longer knows it
		_dimentica(abbonamento["name"])
		return False
	_fallita(abbonamento)
	return False


def _fallita(abbonamento: dict) -> None:
	volte = int(abbonamento.get("failures") or 0) + 1
	if volte >= TENTATIVI:
		_dimentica(abbonamento["name"])
	else:
		frappe.db.set_value(ABBONAMENTO, abbonamento["name"], "failures", volte, update_modified=False)


def _dimentica(nome: str) -> None:
	frappe.delete_doc(ABBONAMENTO, nome, ignore_permissions=True, force=True)


# ------------------------------------------------------------------ the page's side


# nosemgrep: guest-whitelisted-method — static code without secrets, fetched by the browser on its own to update it
@frappe.whitelist(allow_guest=True)
def service_worker() -> None:
	"""The service worker over DottorCloud's pages: it shows a notification and
	opens the page it points to. Code without secrets, for whoever asks."""
	frappe.local.response.update(
		{
			"type": "download",
			"filename": "spinta-sw.js",
			"filecontent": frappe.read_file(frappe.get_app_path("crm", "notifiche", "spinta_sw.js")),
			"content_type": "text/javascript",
			"display_content_as": "inline",
		}
	)
	# registered by /crm's pages over /crm, though it is served from /api
	frappe.local.response_headers["Service-Worker-Allowed"] = AMBITO
	frappe.local.response_headers["Cache-Control"] = "no-cache"
