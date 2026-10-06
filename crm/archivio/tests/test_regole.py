# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The archive without a site (doc 57): the signature on AWS's own examples, the
bucket's address, the keys, what the plan includes, which files move."""

import datetime
import hashlib
import unittest
from urllib.parse import parse_qs, urlsplit

from crm.archivio import regole as R

# AWS's examples of Signature Version 4 for S3 ("Authenticating Requests: Using
# the Authorization Header" and "Using Query Parameters")
ACCESSO = "AKIAIOSFODNN7EXAMPLE"
SEGRETO = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
QUANDO = datetime.datetime(2013, 5, 24)
HOST = "examplebucket.s3.amazonaws.com"


def firma(intestazioni):
	return intestazioni["authorization"].rsplit("Signature=", 1)[1]


class LaFirma(unittest.TestCase):
	def firma(self, metodo, percorso, **kw):
		return R.firma_intestazioni(
			metodo,
			HOST,
			percorso,
			access_key=ACCESSO,
			secret_key=SEGRETO,
			regione="us-east-1",
			quando=QUANDO,
			**kw,
		)

	def test_get_con_un_intervallo(self):
		h = self.firma("GET", "/test.txt", intestazioni={"Range": "bytes=0-9"})
		self.assertEqual(firma(h), "f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41")
		self.assertIn("SignedHeaders=host;range;x-amz-content-sha256;x-amz-date", h["authorization"])
		self.assertEqual(h["x-amz-content-sha256"], R.VUOTO)
		self.assertNotIn("host", h)

	def test_put_con_il_suo_corpo(self):
		corpo = hashlib.sha256(b"Welcome to Amazon S3.").hexdigest()
		h = self.firma(
			"PUT",
			"/test$file.text",
			intestazioni={
				"Date": "Fri, 24 May 2013 00:00:00 GMT",
				"x-amz-storage-class": "REDUCED_REDUNDANCY",
			},
			payload=corpo,
		)
		self.assertEqual(firma(h), "98ad721746da40c64f1a55b78f14c238d841ea1380cd77a1b5971af0ece108bd")

	def test_un_parametro_senza_valore(self):
		h = self.firma("GET", "/", parametri={"lifecycle": ""})
		self.assertEqual(firma(h), "fea454ca298b7da1c68078a5d1bdbfbbe0d65c699e0f91ac7a200a0136783543")

	def test_il_link(self):
		url = R.url_firmato(
			"GET",
			HOST,
			"/test.txt",
			f"https://{HOST}",
			access_key=ACCESSO,
			secret_key=SEGRETO,
			regione="us-east-1",
			quando=QUANDO,
			scade=86400,
		)
		self.assertTrue(url.startswith(f"https://{HOST}/test.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&"))
		self.assertTrue(url.endswith("aeeed9bbccd4d02ee5c0109b86d86835f995330da4c265957d157751f604d404"))

	def test_il_link_porta_il_nome_e_il_tipo(self):
		url = R.url_firmato(
			"GET",
			HOST,
			"/a b/referto è.pdf",
			f"https://{HOST}",
			access_key=ACCESSO,
			secret_key=SEGRETO,
			regione="us-east-1",
			quando=QUANDO,
			parametri={"response-content-disposition": R.disposizione("referto è.pdf")},
		)
		parti = urlsplit(url)
		self.assertEqual(parti.path, "/a%20b/referto%20%C3%A8.pdf")
		domanda = parse_qs(parti.query)
		self.assertEqual(
			domanda["response-content-disposition"], ["inline; filename*=UTF-8''referto%20%C3%A8.pdf"]
		)
		self.assertEqual(domanda["X-Amz-Expires"], [str(R.DURATA_DEL_LINK)])


class IlBucket(unittest.TestCase):
	def test_senza_le_chiavi_l_archivio_e_spento(self):
		self.assertIsNone(R.configurazione(None))
		self.assertIsNone(R.configurazione({"endpoint": "https://x", "bucket": "b", "access_key": "k"}))
		pieno = {"endpoint": "https://x", "bucket": "b", "access_key": "k", "secret_key": "s"}
		self.assertIsNotNone(R.configurazione(pieno))
		self.assertIsNone(R.configurazione({**pieno, "enabled": 0}))

	def test_il_prefisso_e_il_sito_dove_non_e_detto(self):
		pieno = {"endpoint": "https://x", "bucket": "b", "access_key": "k", "secret_key": "s"}
		self.assertEqual(R.configurazione(pieno, "aurora.dottorcloud.it").prefisso, "aurora.dottorcloud.it")
		self.assertEqual(R.configurazione({**pieno, "prefix": "/clienti/"}, "a").prefisso, "clienti")

	def test_nel_percorso_o_nel_nome_del_host(self):
		c = R.Configurazione(
			endpoint="https://fsn1.your-objectstorage.com",
			bucket="dc",
			access_key="k",
			secret_key="s",
			region="fsn1",
		)
		self.assertEqual(
			c.indirizzo("a/b.pdf"),
			("fsn1.your-objectstorage.com", "/dc/a/b.pdf", "https://fsn1.your-objectstorage.com"),
		)
		v = R.Configurazione(
			endpoint="https://fsn1.your-objectstorage.com/",
			bucket="dc",
			access_key="k",
			secret_key="s",
			virtual=True,
		)
		self.assertEqual(
			v.indirizzo("a/b.pdf"),
			("dc.fsn1.your-objectstorage.com", "/a/b.pdf", "https://dc.fsn1.your-objectstorage.com"),
		)


class LeChiavi(unittest.TestCase):
	def test_la_cartella_del_sito_l_impronta_il_nome(self):
		sha = "ab" + "0" * 62
		self.assertEqual(R.chiave("aurora", sha, "consenso.pdf"), f"aurora/ab/{sha}/consenso.pdf")
		self.assertEqual(R.chiave("", sha, "a/b.pdf"), f"ab/{sha}/a_b.pdf")

	def test_si_spostano_solo_i_file_privati(self):
		self.assertTrue(R.da_spostare("/private/files/referto.pdf"))
		self.assertFalse(R.da_spostare("/files/logo.png"))
		self.assertFalse(R.da_spostare("https://example.com/private/files/x.pdf"))
		self.assertFalse(R.da_spostare("/private/files/"))
		self.assertFalse(R.da_spostare("/private/files/../site_config.json"))
		self.assertFalse(R.da_spostare(None))

	def test_si_scarica_quello_che_il_framework_scarica(self):
		self.assertTrue(R.disposizione("pagina.html").startswith("attachment;"))
		self.assertTrue(R.disposizione("fattura.XML").startswith("attachment;"))
		self.assertTrue(R.disposizione("foto.jpg").startswith("inline;"))
		self.assertTrue(R.disposizione("").startswith("inline; filename*=UTF-8''file"))


class LoSpazio(unittest.TestCase):
	def test_quello_che_include_il_piano(self):
		self.assertEqual(R.compreso("Solo"), R.TB)
		self.assertEqual(R.compreso("Centre"), R.TB)
		self.assertEqual(R.compreso("Polyclinic"), 2 * R.TB)
		self.assertEqual(R.compreso("Large"), 2 * R.TB)
		self.assertEqual(R.compreso(None), R.TB)
		self.assertEqual(R.compreso("Solo", 3072), 3 * R.TB)
		self.assertEqual(R.compreso("Large", 0), 2 * R.TB)

	def test_l_avviso_all_ottanta_per_cento(self):
		self.assertFalse(R.avviso(int(0.79 * R.TB), R.TB))
		self.assertTrue(R.avviso(int(0.81 * R.TB), R.TB))
		self.assertFalse(R.avviso(10, 0))

	def test_il_bucket_lo_legge_un_browser(self):
		cors = R.regole_cors()
		self.assertIn("<AllowedOrigin>*</AllowedOrigin>", cors)
		self.assertIn("<AllowedMethod>GET</AllowedMethod>", cors)
		self.assertNotIn("PUT", cors)


if __name__ == "__main__":
	unittest.main()
