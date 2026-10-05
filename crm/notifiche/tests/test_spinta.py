# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Notifications on the phone, on a real site, through a fake push service.

Bruno turns them on on his iPhone's app: the server keeps where to reach it, his
own. A mention reaches it at once, encrypted so that only that browser opens it,
signed with the site's key, in Bruno's words, opening Laura's page; it does not
go by email as well. A kind he turned off stays in the panel, and so does what is
about the demo. A browser the push service says is gone is forgotten, one that
keeps failing too. Nobody else's device is his to remove, and no address but a
browser maker's push service is ever written to.
"""

import json
from unittest.mock import patch

import frappe
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from crm.notifiche import spinta
from crm.notifiche import spinta_regole as S
from crm.notifiche.tests.test_api import ANNA, BRUNO, NOTIFICA
from crm.notifiche.tests.test_posta import PostaCase
from crm.notifiche.tests.test_spinta_regole import apri

ENDPOINT = "https://web.push.apple.com/QGuQyavXutnMnAh2UCqGlYxPzI8"
IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"


class Risposta:
	def __init__(self, stato):
		self.status_code = stato


class ServizioFinto:
	"""A push service: what it was sent, and what it answers."""

	def __init__(self, stato=201):
		self.stato = stato
		self.mandati = []

	def post(self, indirizzo, data=None, headers=None, timeout=None):
		self.mandati.append({"url": indirizzo, "corpo": data, "intestazioni": headers})
		return Risposta(self.stato)

	def close(self):
		pass


class SpintaCase(PostaCase):
	def setUp(self):
		super().setUp()
		frappe.db.delete(spinta.ABBONAMENTO, {"user": ("in", [ANNA, BRUNO])})
		frappe.defaults.clear_user_default(spinta.CHIAVE, BRUNO)
		# the browser's own keys: it alone opens what it receives
		self.privata_browser, self.pubblica_browser = S.nuove_chiavi()
		self.auth = S.b64u(b"0123456789abcdef")
		# the jobs are run here, by hand
		accoda = patch.object(frappe, "enqueue")
		self.accodati = accoda.start()
		self.addCleanup(accoda.stop)

	def iscrive(self, utente=BRUNO, endpoint=ENDPOINT, installata=1):
		self.come(utente)
		with patch.object(frappe, "get_request_header", return_value=IPHONE):
			return spinta.subscribe(
				json.dumps(
					{"endpoint": endpoint, "keys": {"p256dh": self.pubblica_browser, "auth": self.auth}}
				),
				installata,
			)


class IlTelefonoDiBruno(SpintaCase):
	def test_lo_attiva_e_resta_suo(self):
		stato = self.iscrive()
		self.assertEqual(len(stato["devices"]), 1)
		dispositivo = stato["devices"][0]
		self.assertEqual(dispositivo["device"], "iPhone · app")
		self.assertEqual(dispositivo["endpoint_hash"], spinta.impronta(ENDPOINT))
		self.assertTrue(stato["public_key"])
		# the same browser again is the same device, not a second one
		self.assertEqual(len(self.iscrive()["devices"]), 1)
		# Anna signs in on the same phone: from now on it is hers
		self.iscrive(utente=ANNA)
		self.come(BRUNO)
		self.assertEqual(spinta.get_push()["devices"], [])

	def test_solo_il_servizio_di_chi_fa_il_browser(self):
		for indirizzo in (
			"https://evil.example.com/push",
			"http://fcm.googleapis.com/fcm/send/x",
			"https://fcm.googleapis.com.evil.example.com/x",
		):
			with self.subTest(indirizzo=indirizzo), self.assertRaises(frappe.ValidationError):
				self.iscrive(endpoint=indirizzo)
		self.assertTrue(spinta.servizio_ammesso("https://fcm.googleapis.com/fcm/send/abc"))
		self.assertTrue(spinta.servizio_ammesso("https://updates.push.services.mozilla.com/wpush/v2/x"))
		self.assertTrue(spinta.servizio_ammesso("https://wns2-par02p.notify.windows.com/w/?token=x"))

	def test_chiavi_che_non_sono_di_un_browser(self):
		self.come(BRUNO)
		with self.assertRaises(frappe.ValidationError):
			spinta.subscribe(json.dumps({"endpoint": ENDPOINT, "keys": {"p256dh": "AAAA", "auth": "BBBB"}}))

	def test_solo_chi_lavora_nel_centro(self):
		# a client area's person has no panel to bring to a phone
		paziente = "spinta.paziente@example.com"
		if not frappe.db.exists("User", paziente):
			frappe.get_doc(
				{"doctype": "User", "email": paziente, "first_name": "Pia", "user_type": "Website User"}
			).insert(ignore_permissions=True)
		frappe.set_user(paziente)
		with self.assertRaises(frappe.PermissionError):
			spinta.get_push()
		with self.assertRaises(frappe.PermissionError):
			spinta.subscribe(json.dumps({"endpoint": ENDPOINT, "keys": {}}))

	def test_il_dispositivo_di_un_altro_non_si_toglie(self):
		self.iscrive()
		nome = frappe.db.get_value(spinta.ABBONAMENTO, {"user": BRUNO})
		self.come(ANNA)
		spinta.unsubscribe(name=nome)
		self.assertTrue(frappe.db.exists(spinta.ABBONAMENTO, nome))
		self.come(BRUNO)
		self.assertEqual(spinta.unsubscribe(endpoint_hash=spinta.impronta(ENDPOINT))["devices"], [])


class LaNotificaArriva(SpintaCase):
	def test_cifrata_firmata_nelle_sue_parole(self):
		self.iscrive()
		frappe.set_user("Administrator")
		nome = self.menziona()
		self.assertTrue(self.accodati.called)
		self.assertEqual(self.accodati.call_args.kwargs["notifica"], nome)

		servizio = ServizioFinto()
		self.assertEqual(spinta.manda(nome, servizio), 1)
		mandato = servizio.mandati[0]
		self.assertEqual(mandato["url"], ENDPOINT)
		intestazioni = mandato["intestazioni"]
		self.assertEqual(intestazioni["Content-Encoding"], "aes128gcm")
		self.assertEqual(intestazioni["TTL"], str(spinta.VITA))
		# signed with the site's key, for Apple's push service
		token, chiave = intestazioni["Authorization"][len("vapid t=") :].split(", k=")
		_privata, pubblica = spinta.chiavi()
		self.assertEqual(chiave, pubblica)
		verifica = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), S.da_b64u(pubblica))
		pem = verifica.public_bytes(
			serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
		)
		self.assertEqual(
			jwt.decode(token, pem, algorithms=["ES256"], audience="https://web.push.apple.com")["sub"],
			frappe.utils.get_url(),
		)
		# only Bruno's browser opens it: the sentence, the first words, Laura's page
		dati = json.loads(apri(mandato["corpo"], self.privata_browser, self.auth))
		self.assertIn("Anna", dati["title"])
		self.assertIn(self.laura.lead_name, dati["title"])
		self.assertEqual(dati["body"], "Puoi richiamarla?")
		self.assertTrue(dati["url"].startswith(f"/crm/leads/{self.laura.name}"))
		self.assertIn(f"notifica={nome}", dati["url"])
		# it reached his phone: no email as well
		self.assertEqual(frappe.db.get_value(NOTIFICA, nome, "email_due"), 0)

	def test_letta_prima_non_parte(self):
		self.iscrive()
		frappe.set_user("Administrator")
		nome = self.menziona()
		frappe.db.set_value(NOTIFICA, nome, "read", 1)
		servizio = ServizioFinto()
		self.assertEqual(spinta.manda(nome, servizio), 0)
		self.assertEqual(servizio.mandati, [])

	def test_un_genere_spento_resta_nel_pannello(self):
		self.iscrive()
		self.come(BRUNO)
		gruppi = {g["key"]: g["on"] for g in spinta.save_push_preferences({"mentions": False})["groups"]}
		self.assertFalse(gruppi["mentions"])
		self.assertTrue(gruppi["assignments"])
		frappe.set_user("Administrator")
		self.accodati.reset_mock()
		self.menziona()
		self.assertFalse(self.accodati.called)

	def test_senza_dispositivi_niente(self):
		frappe.set_user("Administrator")
		self.menziona()
		self.assertFalse(self.accodati.called)

	def test_mai_sui_dati_di_prova(self):
		self.iscrive()
		frappe.set_user("Administrator")
		with patch("crm.demo.guardie.solo_nel_pannello", return_value=True):
			self.menziona()
		self.assertFalse(self.accodati.called)


class IDispositiviPersi(SpintaCase):
	def test_quello_che_il_servizio_non_conosce_piu(self):
		self.iscrive()
		frappe.set_user("Administrator")
		nome = self.menziona()
		self.assertEqual(spinta.manda(nome, ServizioFinto(410)), 0)
		self.assertFalse(frappe.db.exists(spinta.ABBONAMENTO, {"user": BRUNO}))
		# not delivered: the email still goes
		self.assertEqual(frappe.db.get_value(NOTIFICA, nome, "email_due"), 1)

	def test_quello_che_continua_a_sbagliare(self):
		self.iscrive()
		frappe.set_user("Administrator")
		nome = self.menziona()
		for _volta in range(spinta.TENTATIVI - 1):
			spinta.manda(nome, ServizioFinto(500))
		self.assertEqual(
			frappe.db.get_value(spinta.ABBONAMENTO, {"user": BRUNO}, "failures"), spinta.TENTATIVI - 1
		)
		spinta.manda(nome, ServizioFinto(500))
		self.assertFalse(frappe.db.exists(spinta.ABBONAMENTO, {"user": BRUNO}))


class LaProvaEIlServiceWorker(SpintaCase):
	def test_la_prova_ai_propri_dispositivi(self):
		self.come(BRUNO)
		with self.assertRaises(frappe.ValidationError):
			spinta.send_test()
		self.iscrive()
		servizio = ServizioFinto()
		with patch.object(spinta.requests, "Session", return_value=servizio):
			self.assertEqual(spinta.send_test(), {"sent": 1, "devices": 1})
		dati = json.loads(apri(servizio.mandati[0]["corpo"], self.privata_browser, self.auth))
		self.assertEqual(dati["url"], "/crm/notifications")

	def test_il_service_worker_su_crm(self):
		spinta.service_worker()
		self.assertEqual(frappe.local.response["content_type"], "text/javascript")
		self.assertIn("showNotification", frappe.local.response["filecontent"])
		self.assertEqual(frappe.local.response_headers["Service-Worker-Allowed"], "/crm")

	def test_le_chiavi_del_sito_restano(self):
		prima = spinta.chiavi()
		self.assertEqual(spinta.chiavi(), prima)
		self.assertEqual(S.pubblica_di(prima[0]), prima[1])
