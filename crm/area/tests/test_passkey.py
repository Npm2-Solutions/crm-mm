# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A passkey to the client area, proved with a software authenticator: a P-256
key, the authenticator data and the signature a phone would make.

Anna enters with the code and adds a passkey; the next time she enters with it,
without a code, and it counts as entering again for a document. From outside no
passkey is added; a closed area does not open; a wrong signature, an old
challenge, a key that went back in its counter do not enter. She removes her
passkeys, not somebody else's.
"""

import base64
import hashlib
import json
import os
import struct

import cbor2
import frappe
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from crm.area import accesso, passkey
from crm.area.tests.test_area import ANNA, DESK, AreaCase


def b64(dati: bytes) -> str:
	return base64.urlsafe_b64encode(dati).rstrip(b"=").decode()


def da_b64(testo: str) -> bytes:
	return base64.urlsafe_b64decode(testo + "=" * (-len(testo) % 4))


class Autenticatore:
	"""What a phone does with a passkey, and nothing more."""

	UP, UV, AT = 0x01, 0x04, 0x40

	def __init__(self):
		self.chiave = ec.generate_private_key(ec.SECP256R1())
		self.id = os.urandom(16)
		self.contatore = 0
		self.utente = None

	def _cose(self) -> bytes:
		numeri = self.chiave.public_key().public_numbers()
		return cbor2.dumps(
			{1: 2, 3: -7, -1: 1, -2: numeri.x.to_bytes(32, "big"), -3: numeri.y.to_bytes(32, "big")}
		)

	def _dati(self, rp_id: str, flag: int, attestato: bytes = b"") -> bytes:
		self.contatore += 1
		return (
			hashlib.sha256(rp_id.encode()).digest()
			+ bytes([flag])
			+ struct.pack(">I", self.contatore)
			+ attestato
		)

	@staticmethod
	def _client(tipo: str, sfida: str, origine: str) -> bytes:
		return json.dumps(
			{"type": tipo, "challenge": sfida, "origin": origine, "crossOrigin": False}
		).encode()

	def crea(self, opzioni: dict) -> dict:
		rp_id, origine = passkey._rp()
		self.utente = da_b64(opzioni["user"]["id"])
		attestato = bytes(16) + struct.pack(">H", len(self.id)) + self.id + self._cose()
		dati = self._dati(rp_id, self.UP | self.UV | self.AT, attestato)
		client = self._client("webauthn.create", opzioni["challenge"], origine)
		return {
			"id": b64(self.id),
			"rawId": b64(self.id),
			"type": "public-key",
			"response": {
				"clientDataJSON": b64(client),
				"attestationObject": b64(cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": dati})),
				"transports": ["internal"],
			},
			"clientExtensionResults": {},
		}

	def firma(self, opzioni: dict, flag: int | None = None, guasta: bool = False) -> dict:
		rp_id, origine = passkey._rp()
		dati = self._dati(rp_id, self.UP | self.UV if flag is None else flag)
		client = self._client("webauthn.get", opzioni["challenge"], origine)
		firma = self.chiave.sign(dati + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
		if guasta:
			firma = firma[:-1] + bytes([firma[-1] ^ 0xFF])
		return {
			"id": b64(self.id),
			"rawId": b64(self.id),
			"type": "public-key",
			"response": {
				"clientDataJSON": b64(client),
				"authenticatorData": b64(dati),
				"signature": b64(firma),
				"userHandle": b64(self.utente or b""),
			},
			"clientExtensionResults": {},
		}


class PasskeyCase(AreaCase):
	def setUp(self):
		super().setUp()
		self.invita()
		self.telefono = Autenticatore()

	def aggiunge(self):
		self.entra(ANNA)
		opzioni = passkey.registration_options()
		self.assertEqual(opzioni["authenticatorSelection"]["userVerification"], "required")
		self.assertNotIn(ANNA, json.dumps(opzioni["user"]["id"]))
		return passkey.register(json.dumps(self.telefono.crea(opzioni)))

	def entra_con_la_passkey(self, **altro):
		frappe.set_user("Guest")
		sfida = passkey.authentication_options()
		return passkey.authenticate(
			json.dumps(self.telefono.firma(sfida["options"], **altro)), sfida["state"]
		)


class LaPasskey(PasskeyCase):
	def test_si_aggiunge_da_dentro_e_si_entra_senza_codice(self):
		[riga] = self.aggiunge()["passkeys"]
		self.assertTrue(riga["label"])
		self.entra_con_la_passkey()
		self.assertEqual(frappe.session.user, ANNA)
		# entering again, as with a code: a report can be downloaded
		self.assertTrue(accesso.verificato_da_poco())
		salvata = frappe.get_doc(passkey.PASSKEY, riga["name"])
		self.assertEqual(salvata.sign_count, 2)
		self.assertTrue(salvata.last_used_on)

	def test_da_fuori_non_si_aggiunge(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			passkey.registration_options()
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			passkey.registration_options()

	def test_un_area_chiusa_non_si_apre(self):
		self.aggiunge()
		self.come(DESK)
		accesso.revoke(self.anna.name, ANNA)
		with self.assertRaises(frappe.PermissionError):
			self.entra_con_la_passkey()
		self.assertEqual(frappe.session.user, "Guest")


class NonEntra(PasskeyCase):
	def test_una_firma_sbagliata(self):
		self.aggiunge()
		with self.assertRaises(frappe.PermissionError):
			self.entra_con_la_passkey(guasta=True)
		self.assertEqual(frappe.session.user, "Guest")

	def test_senza_il_viso_o_l_impronta(self):
		self.aggiunge()
		with self.assertRaises(frappe.PermissionError):
			self.entra_con_la_passkey(flag=Autenticatore.UP)

	def test_una_sfida_si_usa_una_volta(self):
		self.aggiunge()
		frappe.set_user("Guest")
		sfida = passkey.authentication_options()
		risposta = json.dumps(self.telefono.firma(sfida["options"]))
		passkey.authenticate(risposta, sfida["state"])
		frappe.set_user("Guest")
		with self.assertRaises(frappe.ValidationError):
			passkey.authenticate(risposta, sfida["state"])

	def test_un_contatore_che_torna_indietro(self):
		# a key copied elsewhere shows up with a counter already seen
		self.aggiunge()
		self.entra_con_la_passkey()
		self.telefono.contatore = 0
		with self.assertRaises(frappe.PermissionError):
			self.entra_con_la_passkey()

	def test_una_passkey_che_non_conosciamo(self):
		self.aggiunge()
		self.telefono = Autenticatore()
		with self.assertRaises(frappe.PermissionError):
			self.entra_con_la_passkey()


class LeMiePasskey(PasskeyCase):
	def test_si_toglie_la_propria_non_quella_degli_altri(self):
		[riga] = self.aggiunge()["passkeys"]
		self.assertEqual(passkey.remove_passkey(riga["name"]), {"passkeys": []})
		frappe.set_user("Administrator")
		estranea = frappe.get_doc(
			{
				"doctype": passkey.PASSKEY,
				"user": "Administrator",
				"credential_id": b64(os.urandom(16)),
				"public_key": b64(os.urandom(64)),
			}
		).insert(ignore_permissions=True)
		self.entra(ANNA)
		with self.assertRaises(frappe.PermissionError):
			passkey.remove_passkey(estranea.name)
