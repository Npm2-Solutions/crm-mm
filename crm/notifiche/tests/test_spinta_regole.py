# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Web Push without a site: the body encrypted as RFC 8291 writes its own
example, byte for byte, and opened again with the browser's keys; the signature
of RFC 8292 checked with the site's public key."""

from __future__ import annotations

import time
import unittest

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from crm.notifiche import spinta_regole as S

# RFC 8291, Appendix A
TESTO = b"When I grow up, I want to be a watermelon"
PRIVATA_SERVER = "yfWPiYE-n46HLnH0KqZOF1fJJU3MYrct3AELtAQ-oRw"
PUBBLICA_SERVER = "BP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A8"
PRIVATA_BROWSER = "q1dXpw3UpT5VOmu_cf_v6ih07Aems3njxI-JWgLcM94"
PUBBLICA_BROWSER = "BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcxaOzi6-AYWXvTBHm4bjyPjs7Vd8pZGH6SRpkNtoIAiw4"
SALE = "DGv6ra1nlYgDCS1FRnbzlw"
AUTH = "BTBZMqHH6r4Tts7J_aSIgg"
CORPO = "DGv6ra1nlYgDCS1FRnbzlwAAEABBBP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A_yl95bQpu6cVPTpK4Mqgkf1CXztLVBSt2Ks3oZwbuwXPXLWyouBWLVWGNWQexSgSxsj_Qulcy4a-fN"


def apri(corpo: bytes, privata_browser: str, auth: str) -> bytes:
	"""What the browser does with the body: the other side of RFC 8291."""
	import hashlib
	import hmac

	from cryptography.hazmat.primitives.ciphers.aead import AESGCM

	def h(chiave, dati):
		return hmac.new(chiave, dati, hashlib.sha256).digest()

	sale, lunghezza = corpo[:16], corpo[20]
	server = corpo[21 : 21 + lunghezza]
	sigillato = corpo[21 + lunghezza :]
	browser = S._privata(privata_browser)
	pubblica_browser = S._pubblica(browser)
	segreto = browser.exchange(
		ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), server)
	)
	ikm = h(h(S.da_b64u(auth), segreto), b"WebPush: info\x00" + pubblica_browser + server + b"\x01")
	prk = h(sale, ikm)
	cek = h(prk, b"Content-Encoding: aes128gcm\x00\x01")[:16]
	nonce = h(prk, b"Content-Encoding: nonce\x00\x01")[:12]
	chiaro = AESGCM(cek).decrypt(nonce, sigillato, None)
	return chiaro.rstrip(b"\x00")[:-1]


class IlMessaggioCifrato(unittest.TestCase):
	def test_l_esempio_della_rfc_byte_per_byte(self):
		self.assertEqual(S.pubblica_di(PRIVATA_SERVER), PUBBLICA_SERVER)
		corpo = S.cifra(
			TESTO,
			PUBBLICA_BROWSER,
			AUTH,
			sale=S.da_b64u(SALE),
			privata_del_momento=PRIVATA_SERVER,
		)
		self.assertEqual(S.b64u(corpo), CORPO)

	def test_lo_apre_solo_il_suo_browser(self):
		corpo = S.cifra(b'{"title": "Anna"}', PUBBLICA_BROWSER, AUTH)
		self.assertEqual(apri(corpo, PRIVATA_BROWSER, AUTH), b'{"title": "Anna"}')
		# a new salt and a new key at every message
		self.assertNotEqual(S.cifra(TESTO, PUBBLICA_BROWSER, AUTH), S.cifra(TESTO, PUBBLICA_BROWSER, AUTH))
		altro_privata, _altra_pubblica = S.nuove_chiavi()
		with self.assertRaises(Exception):
			apri(corpo, altro_privata, AUTH)

	def test_chiavi_che_non_sono_di_un_abbonamento(self):
		with self.assertRaises(ValueError):
			S.cifra(TESTO, "AAAA", AUTH)
		with self.assertRaises(ValueError):
			S.cifra(TESTO, PUBBLICA_BROWSER, "AAAA")
		with self.assertRaises(ValueError):
			S.cifra(b"x" * 5000, PUBBLICA_BROWSER, AUTH)


class LaFirma(unittest.TestCase):
	def test_chi_manda_firma_per_il_servizio(self):
		privata, pubblica = S.nuove_chiavi()
		self.assertEqual(S.pubblica_di(privata), pubblica)
		adesso = time.time()
		intestazione = S.firma(
			"https://fcm.googleapis.com/fcm/send/abc:def", privata, "https://centro.example.com", adesso
		)["Authorization"]
		self.assertTrue(intestazione.startswith("vapid t="))
		token, chiave = intestazione[len("vapid t=") :].split(", k=")
		self.assertEqual(chiave, pubblica)
		verifica = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), S.da_b64u(pubblica))
		pem = verifica.public_bytes(
			serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
		)
		dati = jwt.decode(token, pem, algorithms=["ES256"], audience="https://fcm.googleapis.com")
		self.assertEqual(dati["sub"], "https://centro.example.com")
		self.assertLessEqual(dati["exp"] - adesso, 24 * 60 * 60)

	def test_solo_un_servizio_su_https(self):
		privata, _pubblica = S.nuove_chiavi()
		with self.assertRaises(ValueError):
			S.firma("http://push.example.com/x", privata, "https://centro.example.com")
		self.assertEqual(S.origine("https://web.push.apple.com/QGuQyavXut"), "https://web.push.apple.com")


class IlNomeDelDispositivo(unittest.TestCase):
	def test_come_lo_conosce_chi_lo_usa(self):
		casi = {
			"Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1": "iPhone · Safari",
			"Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36": "Android · Chrome",
			"Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/26.0 Chrome/122.0.0.0 Mobile Safari/537.36": "Android · Samsung Internet",
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0": "Windows · Edge",
			"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15": "Mac · Safari",
			"Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0": "Linux · Firefox",
		}
		for ua, nome in casi.items():
			with self.subTest(nome=nome):
				self.assertEqual(S.dispositivo(ua), nome)

	def test_l_app_sulla_schermata_home(self):
		ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
		self.assertEqual(S.dispositivo(ua, installata=True), "iPhone · app")
		self.assertEqual(S.dispositivo("", installata=True), "app")
		self.assertEqual(S.dispositivo(""), "?")


class ChiFirma(unittest.TestCase):
	"""The signature's `sub`: the site as the world reaches it, as https. A job's
	own address is a local name with a port, which Apple refuses."""

	def test_l_indirizzo_pubblico_prima(self):
		self.assertEqual(
			S.contatto(None, "", "https://crm.centro.it/crm/notifications", "http://site:8000"),
			"https://crm.centro.it",
		)
		self.assertEqual(S.contatto("http://localhost:8000", "crm.centro.it"), "https://crm.centro.it")
		self.assertEqual(
			S.contatto("http://10.0.0.5:8000", "http://crm.centro.it:8000"), "https://crm.centro.it"
		)

	def test_senza_un_pubblico_il_primo_senza_porta(self):
		self.assertEqual(S.contatto("http://dottorcloud.local:8000"), "https://dottorcloud.local")
		self.assertEqual(S.contatto(), "")
		self.assertEqual(S.contatto(None, "  "), "")

	def test_pubblico(self):
		for indirizzo in ("https://crm.centro.it", "crm.centro.it", "http://app.dottorcloud.com:443/x"):
			with self.subTest(indirizzo=indirizzo):
				self.assertTrue(S.pubblico(indirizzo))
		for indirizzo in (
			"http://dottorcloud.local",
			"http://localhost:8000",
			"http://192.168.1.10",
			"https://test_site",
			"http://[::1]:8000",
			"https://frontend.internal",
			"",
			None,
		):
			with self.subTest(indirizzo=indirizzo):
				self.assertFalse(S.pubblico(indirizzo))


class IlTitoloDiUnMessaggio(unittest.TestCase):
	"""A person's message on the phone is titled as a messenger titles it: the
	channel's mark and who wrote."""

	def test_il_segno_del_canale_e_chi_ha_scritto(self):
		self.assertEqual(S.titolo_di_un_messaggio("whatsapp", "Laura Bassi"), "💬 Laura Bassi")
		self.assertEqual(S.titolo_di_un_messaggio("sms", "Laura Bassi"), "📱 Laura Bassi")
		self.assertEqual(S.titolo_di_un_messaggio("email", "Laura Bassi"), "✉️ Laura Bassi")
		self.assertEqual(S.titolo_di_un_messaggio("call", "+39 333 123 4567"), "📞 +39 333 123 4567")

	def test_quanti_mentre_non_e_letto(self):
		self.assertEqual(S.titolo_di_un_messaggio("whatsapp", "Laura Bassi", 3), "💬 Laura Bassi (3)")
		self.assertEqual(S.titolo_di_un_messaggio("whatsapp", "Laura Bassi", 1), "💬 Laura Bassi")
		self.assertEqual(S.titolo_di_un_messaggio("whatsapp", "Laura Bassi", None), "💬 Laura Bassi")

	def test_altrimenti_la_frase(self):
		# another kind, or no name: the panel's sentence stays the title
		self.assertEqual(S.titolo_di_un_messaggio("mention", "Anna"), "")
		self.assertEqual(S.titolo_di_un_messaggio("whatsapp", " "), "")
		self.assertEqual(S.titolo_di_un_messaggio(None, "Laura Bassi"), "")
