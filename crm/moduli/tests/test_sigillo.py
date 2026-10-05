# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's seal and the time stamp on the PDFs it keeps.

With the centre's certificate installed, a PDF comes out sealed: the seal covers
the whole file and names the centre, and with a time-stamping authority it
carries the stamp. An authority that does not answer leaves the seal without the
stamp, and says so; a certificate that cannot be read leaves the PDF as it was.
Without a certificate nothing changes. A signed form's PDF is sealed before its
fingerprint is taken, so the fingerprint is the sealed file's.
"""

import datetime
import hashlib
from unittest import mock

import frappe
from asn1crypto import keys as akeys
from asn1crypto import x509 as ax509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from frappe.tests import IntegrationTestCase

from crm.moduli import compilazioni, sigillo
from crm.moduli.pdf import pdf_da_html
from crm.moduli.tests.test_compilazioni import DESK, CompilazioniCase

PAROLA = b"parola-del-sigillo"


def certificato(nome="Centro Prova", uso=None, dal=-1, al=365):
	chiave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
	soggetto = x509.Name(
		[
			x509.NameAttribute(NameOID.COMMON_NAME, nome),
			x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Centro Prova Srl"),
			x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
		]
	)
	adesso = datetime.datetime.now(datetime.UTC)
	costruttore = (
		x509.CertificateBuilder()
		.subject_name(soggetto)
		.issuer_name(soggetto)
		.public_key(chiave.public_key())
		.serial_number(x509.random_serial_number())
		.not_valid_before(adesso + datetime.timedelta(days=dal))
		.not_valid_after(adesso + datetime.timedelta(days=al))
		.add_extension(
			x509.KeyUsage(
				digital_signature=True,
				content_commitment=True,
				key_encipherment=False,
				data_encipherment=False,
				key_agreement=False,
				key_cert_sign=False,
				crl_sign=False,
				encipher_only=False,
				decipher_only=False,
			),
			critical=True,
		)
	)
	if uso:
		costruttore = costruttore.add_extension(x509.ExtendedKeyUsage([uso]), critical=True)
	return chiave, costruttore.sign(chiave, hashes.SHA256())


def imposta(**valori):
	cfg = frappe.get_single(sigillo.IMPOSTAZIONI)
	cfg.update(valori)
	cfg.flags.ignore_mandatory = True
	cfg.save(ignore_permissions=True)
	frappe.clear_document_cache(sigillo.IMPOSTAZIONI, sigillo.IMPOSTAZIONI)


def installa_sigillo(**validita):
	"""The centre's certificate, as the agency installs it: a private PKCS#12."""
	frappe.set_user("Administrator")
	chiave, cert = certificato(**validita)
	contenuto = pkcs12.serialize_key_and_certificates(
		b"sigillo", chiave, cert, None, serialization.BestAvailableEncryption(PAROLA)
	)
	file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": "sigillo.p12",
			"is_private": 1,
			"content": contenuto,
			"attached_to_doctype": sigillo.IMPOSTAZIONI,
			"attached_to_name": sigillo.IMPOSTAZIONI,
		}
	).insert(ignore_permissions=True)
	imposta(
		seal_enabled=1,
		seal_certificate=file.file_url,
		seal_password=PAROLA.decode(),
		seal_location="Milano",
		tsa_url=None,
	)


class SigilloCase(IntegrationTestCase):
	def setUp(self):
		installa_sigillo()
		self.pdf = pdf_da_html("<h1>Consenso</h1><p>Firmato da Anna.</p>")

	def tearDown(self):
		frappe.db.rollback()
		frappe.clear_document_cache(sigillo.IMPOSTAZIONI, sigillo.IMPOSTAZIONI)

	def imposta(self, **valori):
		imposta(**valori)


class LaConformitaInParole(IntegrationTestCase):
	"""What is stored stays English, being evidence; a screen reads it in its words."""

	def test_le_parole_conservate_si_leggono_tradotte(self):
		italiano = {
			"PDF/A-3b (structure verified)": "PDF/A-3b (struttura verificata)",
			"{0}, sealed by the centre": "{0}, sigillato dal centro",
			"{0}, sealed by the centre with a time stamp": "{0}, sigillato dal centro con marca temporale",
			"Signed by {0} (PAdES)": "Firmato da {0} (PAdES)",
		}
		with mock.patch.object(sigillo, "_", side_effect=lambda testo: italiano.get(testo, testo)):
			self.assertEqual(
				sigillo.in_parole("PDF/A-3b (structure verified)"), "PDF/A-3b (struttura verificata)"
			)
			self.assertEqual(
				sigillo.in_parole("PDF/A-3b (structure verified), sealed by the centre"),
				"PDF/A-3b (struttura verificata), sigillato dal centro",
			)
			self.assertEqual(
				sigillo.in_parole("PDF/A-3b (structure verified), sealed by the centre with a time stamp"),
				"PDF/A-3b (struttura verificata), sigillato dal centro con marca temporale",
			)
			self.assertEqual(sigillo.in_parole("Signed by Namirial (PAdES)"), "Firmato da Namirial (PAdES)")
			# written in another language already, or unknown: as it was
			gia = "PDF/A-3b (struttura verificata), sigillato dal centro"
			self.assertEqual(sigillo.in_parole(gia), gia)
		self.assertEqual(sigillo.in_parole(None), "")


class IlSigillo(SigilloCase):
	def test_senza_certificato_il_pdf_resta_com_e(self):
		self.imposta(seal_enabled=0)
		esito = sigillo.sigilla(self.pdf)
		self.assertEqual((esito.dati, esito.sigillo, esito.marca), (self.pdf, False, False))

	def test_il_sigillo_copre_tutto_il_documento(self):
		esito = sigillo.sigilla(self.pdf, motivo="Modulo firmato")
		self.assertTrue(esito.sigillo)
		self.assertFalse(esito.marca)
		self.assertNotEqual(esito.dati, self.pdf)
		[firma] = sigillo.verifica(esito.dati)
		self.assertEqual(
			(firma["field"], firma["intact"], firma["covers_all"]), (sigillo.CAMPO_FIRMA, True, True)
		)
		self.assertIn("Centro Prova", firma["signer"])
		self.assertFalse(firma["timestamped"])

	def test_con_la_marca_temporale(self):
		from pyhanko.sign import timestamps

		chiave, cert = certificato("Autorità di prova", ExtendedKeyUsageOID.TIME_STAMPING)
		marcatore = timestamps.DummyTimeStamper(
			tsa_cert=ax509.Certificate.load(cert.public_bytes(serialization.Encoding.DER)),
			tsa_key=akeys.PrivateKeyInfo.load(
				chiave.private_bytes(
					serialization.Encoding.DER,
					serialization.PrivateFormat.PKCS8,
					serialization.NoEncryption(),
				)
			),
		)
		with mock.patch.object(sigillo, "marcatore", return_value=marcatore):
			esito = sigillo.sigilla(self.pdf)
		self.assertTrue(esito.marca)
		[firma] = sigillo.verifica(esito.dati)
		self.assertTrue(firma["intact"])
		self.assertTrue(firma["timestamped"])

	def test_se_la_marca_non_arriva_si_sigilla_senza(self):
		originale = sigillo._firma

		def autorita_giu(pdf, chi, tempo, motivo, luogo):
			if tempo is not None:
				raise RuntimeError("TSA down")
			return originale(pdf, chi, None, motivo, luogo)

		with (
			mock.patch.object(sigillo, "marcatore", return_value=object()),
			mock.patch.object(sigillo, "_firma", side_effect=autorita_giu),
		):
			esito = sigillo.sigilla(self.pdf)
		self.assertEqual((esito.sigillo, esito.marca), (True, False))
		self.assertEqual(esito.avviso, "The time stamp did not come: sealed without it")

	def test_un_certificato_scaduto_non_sigilla(self):
		installa_sigillo(dal=-400, al=-35)
		esito = sigillo.sigilla(self.pdf)
		self.assertEqual((esito.dati, esito.sigillo), (self.pdf, False))
		self.assertEqual(esito.avviso, "The seal's certificate is not valid today")

	def test_un_certificato_illeggibile_non_perde_il_documento(self):
		self.imposta(seal_password="sbagliata")
		esito = sigillo.sigilla(self.pdf)
		self.assertEqual((esito.dati, esito.sigillo), (self.pdf, False))
		self.assertEqual(esito.avviso, "The seal's certificate cannot be read")


class SigilloNelCrmCase(CompilazioniCase):
	def setUp(self):
		super().setUp()
		installa_sigillo()

	def tearDown(self):
		super().tearDown()
		frappe.clear_document_cache(sigillo.IMPOSTAZIONI, sigillo.IMPOSTAZIONI)


class IlModuloFirmatoSigillato(SigilloNelCrmCase):
	def test_l_impronta_e_quella_del_file_sigillato(self):
		self.come(DESK)
		modulo = compilazioni.start_form(self.giulia.name, self.privacy)
		firmato = self.firma(modulo["name"])
		frappe.set_user("Administrator")
		contenuto = frappe.get_doc("File", {"file_url": firmato["pdf_file"]}).get_content(encodings=[])
		self.assertEqual(hashlib.sha256(contenuto).hexdigest(), firmato["pdf_hash"])
		[firma] = sigillo.verifica(contenuto)
		self.assertTrue(firma["intact"])
		# still PDF/A after the seal, and the register says it was sealed
		self.assertEqual(firmato["pdf_conformance"], "PDF/A-3b (structure verified), sealed by the centre")
		eventi = frappe.get_all(
			"CRM Audit Log",
			filters={"reference_doctype": "CRM Form", "reference_name": modulo["name"]},
			pluck="event",
			order_by="creation asc",
		)
		self.assertEqual(eventi[eventi.index("pdf_generated") + 1], "sealed")

	def test_un_sigillo_che_non_riesce_resta_nel_registro(self):
		imposta(seal_password="sbagliata")
		self.come(DESK)
		modulo = compilazioni.start_form(self.giulia.name, self.privacy)
		firmato = self.firma(modulo["name"])
		self.assertEqual(firmato["pdf_conformance"], "PDF/A-3b (structure verified)")
		frappe.set_user("Administrator")
		self.assertEqual(
			frappe.db.get_value(
				"CRM Audit Log",
				{"reference_doctype": "CRM Form", "reference_name": modulo["name"], "event": "seal_failed"},
				"detail",
			),
			"The seal's certificate cannot be read",
		)


class LaPaginaDelSigillo(SigilloNelCrmCase):
	"""The seal is the agency's: whose certificate, and a test page, only for it."""

	def test_chi_non_e_l_agenzia_non_vede_il_sigillo(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			sigillo.get_seal_status()
		with self.assertRaises(frappe.PermissionError):
			sigillo.try_seal()

	def test_l_agenzia_vede_il_certificato_e_prova(self):
		frappe.set_user("Administrator")
		stato = sigillo.get_seal_status()
		self.assertTrue(stato["enabled"])
		self.assertEqual(stato["subject"], "Centro Prova · Centro Prova Srl")
		self.assertEqual((stato["self_signed"], stato["valid_now"]), (True, True))
		self.assertIn(stato["days_left"], (363, 364))
		prova = sigillo.try_seal()
		self.assertEqual((prova["sealed"], prova["timestamped"]), (True, False))
		self.assertTrue(prova["signatures"][0]["intact"])
