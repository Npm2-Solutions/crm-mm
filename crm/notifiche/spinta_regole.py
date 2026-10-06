# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A notification on the phone without anybody in between who reads it: Web Push
as the standards write it, without a site.

- **The message** is encrypted for the one browser that subscribed (RFC 8291,
  "aes128gcm" of RFC 8188): the push service of its maker (Google, Apple, Mozilla)
  carries it and cannot read it. `cifra` makes the body: the salt, the record
  size, the server's key of the moment, the words sealed with AES-128-GCM.
- **Who sends** signs every request (VAPID, RFC 8292): a JWT with ES256 over the
  push service's origin, a day at most, and whom to write to - the site's own
  address, never a person's email. `firma` makes the Authorization header.
- **The keys** of a site are one P-256 pair (`nuove_chiavi`), the public one given
  to the browsers that subscribe.
- **A device** is named the way its person knows it (`dispositivo`): "iPhone ·
  app" for the one on the home screen, "Windows · Edge" for a computer's browser.

Pure, tested with plain `unittest` on the RFC's own example.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import struct
import time
from urllib.parse import urlsplit

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

#: The record size the body declares: one record holds a notification.
RS = 4096
#: A signature lasts at most a day (RFC 8292 §2); twelve hours is what is sent.
DURATA = 12 * 60 * 60
#: The most a body may carry once encrypted: what every push service accepts.
MASSIMO = 4096


def b64u(dati: bytes) -> str:
	"""Base64 for URLs, without the padding, as the standards write keys."""
	return base64.urlsafe_b64encode(dati).rstrip(b"=").decode("ascii")


def da_b64u(testo: str) -> bytes:
	testo = (testo or "").strip()
	return base64.urlsafe_b64decode(testo + "=" * (-len(testo) % 4))


def _hmac(chiave: bytes, dati: bytes) -> bytes:
	return hmac.new(chiave, dati, hashlib.sha256).digest()


def _pubblica(privata: ec.EllipticCurvePrivateKey) -> bytes:
	return privata.public_key().public_bytes(
		serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
	)


def _privata(testo: str) -> ec.EllipticCurvePrivateKey:
	return ec.derive_private_key(int.from_bytes(da_b64u(testo), "big"), ec.SECP256R1())


def nuove_chiavi() -> tuple[str, str]:
	"""A site's pair: the private key and the public one, each in base64url."""
	privata = ec.generate_private_key(ec.SECP256R1())
	numero = privata.private_numbers().private_value.to_bytes(32, "big")
	return b64u(numero), b64u(_pubblica(privata))


def pubblica_di(privata: str) -> str:
	"""The public key that goes with a private one."""
	return b64u(_pubblica(_privata(privata)))


def cifra(
	contenuto: bytes,
	p256dh: str,
	auth: str,
	*,
	sale: bytes | None = None,
	privata_del_momento: str | None = None,
) -> bytes:
	"""The body of a push for the browser whose keys are `p256dh` and `auth`
	(RFC 8291 §3.4): only that browser opens it. `sale` and the key of the moment
	are new at every message; a test passes the RFC's."""
	chiave_browser = da_b64u(p256dh)
	segreto_auth = da_b64u(auth)
	if len(chiave_browser) != 65 or chiave_browser[0] != 4 or len(segreto_auth) != 16:
		raise ValueError("not the keys of a push subscription")
	sale = sale or os.urandom(16)
	momento = (
		_privata(privata_del_momento) if privata_del_momento else ec.generate_private_key(ec.SECP256R1())
	)
	pubblica_momento = _pubblica(momento)
	browser = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), chiave_browser)
	segreto = momento.exchange(ec.ECDH(), browser)

	# the browser's secret and the shared one make the key material (§3.3)
	prk_chiave = _hmac(segreto_auth, segreto)
	ikm = _hmac(prk_chiave, b"WebPush: info\x00" + chiave_browser + pubblica_momento + b"\x01")
	prk = _hmac(sale, ikm)
	cek = _hmac(prk, b"Content-Encoding: aes128gcm\x00\x01")[:16]
	nonce = _hmac(prk, b"Content-Encoding: nonce\x00\x01")[:12]

	# one record, the last: the words, then the delimiter 2 (RFC 8188 §2)
	sigillato = AESGCM(cek).encrypt(nonce, contenuto + b"\x02", None)
	intestazione = sale + struct.pack("!IB", RS, len(pubblica_momento)) + pubblica_momento
	corpo = intestazione + sigillato
	if len(corpo) > MASSIMO:
		raise ValueError("too long for a push")
	return corpo


def origine(endpoint: str) -> str:
	"""The push service a subscription points to, as the signature names it."""
	parti = urlsplit(endpoint)
	if parti.scheme != "https" or not parti.netloc:
		raise ValueError("a push service answers on https")
	return f"{parti.scheme}://{parti.netloc}"


#: Names no push service can reach: a server's own, a network's at home.
_LOCALI = (".local", ".localhost", ".internal", ".lan", ".home", ".test", ".invalid")
_IP = re.compile(r"^[\d.]+$|:")


def pubblico(indirizzo: str | None) -> bool:
	"""Whether an address names the site as the world reaches it: a name with a
	dot that is no local one, nor a number."""
	nome = (urlsplit(_con_schema(indirizzo)).hostname or "").lower()
	return "." in nome and not _IP.search(nome) and not nome.endswith(_LOCALI)


def _con_schema(indirizzo: str | None) -> str:
	indirizzo = (indirizzo or "").strip()
	return indirizzo if "://" in indirizzo else f"https://{indirizzo}" if indirizzo else ""


def contatto(*indirizzi: str | None) -> str:
	"""Whom the push services write to about what the site sends (RFC 8292 §2.1,
	the signature's `sub`): the first of `indirizzi` that names the site as the
	world reaches it, as https, without a port or a path; the first one at all
	when none does.

	A job has no request: there the site's own address is its local name with
	the server's port (`http://dottorcloud.local:8000`), and Apple's push service
	refuses a signature with it (403 BadJwtToken), so an iPhone received the test
	sent from the page and never what a job sent."""
	scritti = [_con_schema(i) for i in indirizzi if (i or "").strip()]
	scelto = next((i for i in scritti if pubblico(i)), scritti[0] if scritti else "")
	nome = urlsplit(scelto).hostname
	return f"https://{nome}" if nome else ""


def firma(endpoint: str, privata: str, contatto: str, adesso: float | None = None) -> dict:
	"""The header that says who sends (RFC 8292 §3): a JWT signed with the site's
	key for the push service's origin, valid `DURATA`, with whom to write to."""
	chiave = _privata(privata)
	pem = chiave.private_bytes(
		serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
	)
	adesso = int(adesso if adesso is not None else time.time())
	token = jwt.encode(
		{"aud": origine(endpoint), "exp": adesso + DURATA, "sub": contatto},
		pem,
		algorithm="ES256",
		headers={"typ": "JWT"},
	)
	return {"Authorization": f"vapid t={token}, k={b64u(_pubblica(chiave))}"}


# ------------------------------------------------------------------ a person's message

#: The mark of a person's message by its channel, before the name of who wrote,
#: the way a messenger titles one. WhatsApp has no emoji of its own: its speech
#: balloon; an SMS the phone it came to, an email its envelope, a message on the
#: answering service the receiver.
SEGNI = {"whatsapp": "💬", "sms": "📱", "email": "✉️", "call": "📞"}


def titolo_di_un_messaggio(genere: str | None, chi: str | None, quanti: int | None = 1) -> str:
	"""The title a device shows for a person's message: its channel's mark and who
	wrote, how many while unread ("💬 Laura Bassi (3)"); nothing for another kind,
	or without a name - the sentence stays the title."""
	segno = SEGNI.get(genere or "")
	chi = (chi or "").strip()
	if not segno or not chi:
		return ""
	quanti = int(quanti or 1)
	return f"{segno} {chi}" + (f" ({quanti})" if quanti > 1 else "")


# ------------------------------------------------------------------ a device's name

#: What a browser says it runs on, in the order that tells them apart: an iPad
#: says "Macintosh" when it asks for the desk's pages, but not when it is an app.
_SISTEMI = (
	("iPhone", re.compile(r"iPhone|iPod")),
	("iPad", re.compile(r"iPad")),
	("Android", re.compile(r"Android")),
	("Windows", re.compile(r"Windows")),
	("Mac", re.compile(r"Macintosh|Mac OS X")),
	("ChromeOS", re.compile(r"CrOS")),
	("Linux", re.compile(r"Linux")),
)
#: The browser, the ones that carry another's name first: Edge and Opera say
#: "Chrome", Chrome says "Safari", Samsung's says both.
_BROWSER = (
	("Edge", re.compile(r"Edg(e|A|iOS)?/")),
	("Opera", re.compile(r"OPR/|Opera")),
	("Samsung Internet", re.compile(r"SamsungBrowser")),
	("Firefox", re.compile(r"Firefox|FxiOS")),
	("Chrome", re.compile(r"Chrome|CriOS")),
	("Safari", re.compile(r"Safari")),
)


def dispositivo(user_agent: str, installata: bool = False) -> str:
	"""A device by the name its person knows it: the system, then "app" for the one
	put on the home screen, else the browser."""
	ua = user_agent or ""
	sistema = next((nome for nome, segno in _SISTEMI if segno.search(ua)), "")
	if installata:
		browser = "app"
	else:
		browser = next((nome for nome, segno in _BROWSER if segno.search(ua)), "")
	return " · ".join(parte for parte in (sistema, browser) if parte)[:140] or "?"
