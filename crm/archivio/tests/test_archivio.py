# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's files on the agency's archive, on a real site, with a bucket in
memory (doc 57).

A signed consent of Centro Aurora is written as a private file. An hour later it
is on the archive and the server keeps an empty file with its name; whoever reads
it in code finds it whole, and an hour after that it leaves again without being
sent twice. Opening its address sends whoever may read it to the bucket, and
nobody else. The logo stays on the server. Deleted, its object goes with it; a
file deleted by the database leaves nothing behind at night. The space counts
each address once.
"""

import os
import types
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime
from werkzeug.exceptions import HTTPException

from crm.archivio import archivio, regole, s3

CONF = {
	"endpoint": "https://fsn1.your-objectstorage.com",
	"region": "fsn1",
	"bucket": "dottorcloud-archivio",
	"access_key": "chiave-di-prova",
	"secret_key": "segreto-di-prova",
	"prefix": "dottorcloud",
}
CONTENUTO = b"Consenso firmato da Anna Bianchi, 06/10/2026"


class Bucket:
	"""The bucket, in memory: what `crm.archivio.s3` would do on Hetzner."""

	def __init__(self):
		self.oggetti = {}
		self.messi = 0

	def metti(self, conf, chiave, percorso, sha256, tipo=None):
		with open(percorso, "rb") as f:
			self.oggetti[chiave] = f.read()
		self.messi += 1

	def c_e(self, conf, chiave):
		valore = self.oggetti.get(chiave)
		return None if valore is None else len(valore)

	def prendi(self, conf, chiave, percorso):
		if chiave not in self.oggetti:
			raise s3.ErroreArchivio("The archive answered 404", stato=404, codice="NoSuchKey")
		with open(percorso, "wb") as f:
			f.write(self.oggetti[chiave])
		return len(self.oggetti[chiave])

	def togli(self, conf, chiave):
		self.oggetti.pop(chiave, None)

	def link(self, conf, chiave, nome, tipo=None, scade=regole.DURATA_DEL_LINK):
		return f"https://bucket.test/{chiave}?nome={nome}"


class TestArchivio(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.bucket = Bucket()
		for nome in ("metti", "c_e", "prendi", "togli", "link"):
			patcher = patch.object(s3, nome, getattr(self.bucket, nome))
			patcher.start()
			self.addCleanup(patcher.stop)
		self.conf = patch.dict(frappe.local.conf, {archivio.CONF: CONF})
		self.conf.start()
		self.addCleanup(self.conf.stop)
		frappe.cache.delete_value(archivio.CHIAVE_SPAZIO)
		frappe.cache.delete_value(archivio.RIPORTATI)
		self.file = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for nome in self.file:
			if frappe.db.exists("File", nome):
				frappe.delete_doc("File", nome, ignore_permissions=True, force=True)
		frappe.db.delete("CRM Archived File", {"file_url": ["like", "%consenso-archivio%"]})
		frappe.db.commit()

	def nuovo(self, nome="consenso-archivio.txt", privato=1, contenuto=CONTENUTO, ore_fa=2):
		doc = frappe.get_doc(
			{"doctype": "File", "file_name": nome, "is_private": privato, "content": contenuto}
		).insert(ignore_permissions=True)
		self.file.append(doc.name)
		frappe.db.set_value(
			"File", doc.name, "creation", add_to_date(now_datetime(), hours=-ore_fa), update_modified=False
		)
		frappe.db.commit()
		return doc

	def locale(self, doc):
		return archivio.percorso(doc.file_url) if doc.is_private else doc.get_full_path()

	def test_senza_archivio_non_si_sposta_niente(self):
		doc = self.nuovo()
		with patch.dict(frappe.local.conf, {archivio.CONF: None}):
			self.assertEqual(archivio.sposta()["moved"], 0)
		self.assertEqual(os.path.getsize(self.locale(doc)), len(CONTENUTO))
		self.assertFalse(archivio.archiviato(doc.file_url))

	def test_un_file_privato_va_nell_archivio_e_torna_quando_si_legge(self):
		doc = self.nuovo()
		esito = archivio.sposta()
		self.assertGreaterEqual(esito["moved"], 1)

		record = archivio.archiviato(doc.file_url)
		self.assertEqual(record.size, len(CONTENUTO))
		self.assertTrue(record.object_key.startswith(f"dottorcloud/{frappe.local.site}/"))
		self.assertEqual(self.bucket.oggetti[record.object_key], CONTENUTO)
		# on the server, an empty file keeps the name
		self.assertTrue(os.path.exists(self.locale(doc)))
		self.assertEqual(os.path.getsize(self.locale(doc)), 0)

		# whoever reads it finds it whole
		letto = frappe.get_doc("File", doc.name).get_content()
		self.assertEqual(letto.encode() if isinstance(letto, str) else letto, CONTENUTO)
		self.assertTrue(archivio.archiviato(doc.file_url).restored_on)

		# an hour later it leaves again, without being sent twice
		messi = self.bucket.messi
		passato = (now_datetime() - add_to_date(now_datetime(), hours=-2)).total_seconds()
		os.utime(self.locale(doc), (os.path.getatime(self.locale(doc)) - passato,) * 2)
		frappe.db.set_value(
			"CRM Archived File",
			record.name,
			"restored_on",
			add_to_date(now_datetime(), hours=-2),
			update_modified=False,
		)
		archivio.sposta()
		self.assertEqual(self.bucket.messi, messi)
		self.assertEqual(os.path.getsize(self.locale(doc)), 0)
		self.assertFalse(archivio.archiviato(doc.file_url).restored_on)

	def test_un_file_appena_scritto_aspetta(self):
		doc = self.nuovo(ore_fa=0)
		archivio.sposta()
		self.assertFalse(archivio.archiviato(doc.file_url))
		self.assertEqual(os.path.getsize(self.locale(doc)), len(CONTENUTO))

	def test_un_file_pubblico_resta_sul_server(self):
		doc = self.nuovo(nome="orari-consenso-archivio.txt", privato=0, contenuto=b"Orari del centro")
		archivio.sposta()
		self.assertFalse(archivio.archiviato(doc.file_url))
		self.assertGreater(os.path.getsize(self.locale(doc)), 0)

	def test_aprirlo_porta_al_bucket_chi_puo_leggerlo(self):
		doc = self.nuovo()
		archivio.sposta()
		record = archivio.archiviato(doc.file_url)
		richiesta = types.SimpleNamespace(method="GET", path=doc.file_url, headers={})
		with patch.object(frappe.local, "request", richiesta, create=True):
			with self.assertRaises(HTTPException) as preso:
				archivio.prima_della_richiesta()
			risposta = preso.exception.response
			self.assertEqual(risposta.status_code, 302)
			self.assertTrue(
				risposta.headers["Location"].startswith(f"https://bucket.test/{record.object_key}")
			)
			self.assertEqual(risposta.headers["Cache-Control"], "private, no-store")

			# a guest is the framework's to refuse
			frappe.set_user("Guest")
			self.assertIsNone(archivio.prima_della_richiesta())

	def test_un_file_ancora_sul_server_lo_serve_il_framework(self):
		doc = self.nuovo(ore_fa=0)
		richiesta = types.SimpleNamespace(method="GET", path=doc.file_url, headers={})
		with patch.object(frappe.local, "request", richiesta, create=True):
			self.assertIsNone(archivio.prima_della_richiesta())

	def test_tolto_il_file_l_oggetto_va(self):
		doc = self.nuovo()
		archivio.sposta()
		chiave = archivio.archiviato(doc.file_url).object_key
		frappe.delete_doc("File", doc.name, ignore_permissions=True)
		frappe.db.commit()
		self.assertFalse(archivio.archiviato(doc.file_url))
		self.assertNotIn(chiave, self.bucket.oggetti)

	def test_tolto_dal_database_la_notte_lo_porta_via(self):
		doc = self.nuovo()
		archivio.sposta()
		chiave = archivio.archiviato(doc.file_url).object_key
		frappe.db.delete("File", {"name": doc.name})
		frappe.db.commit()
		self.assertGreaterEqual(archivio.orfani(), 1)
		self.assertFalse(archivio.archiviato(doc.file_url))
		self.assertNotIn(chiave, self.bucket.oggetti)

	def test_lo_spazio_conta_ogni_indirizzo_una_volta(self):
		prima = archivio.spazio()["used"]
		frappe.cache.delete_value(archivio.CHIAVE_SPAZIO)
		doc = self.nuovo()
		copia = doc.create_attachment_copy("User", "Administrator", ignore_permissions=True)
		self.file.append(copia.name)
		frappe.cache.delete_value(archivio.CHIAVE_SPAZIO)
		self.assertEqual(archivio.spazio()["used"] - prima, len(CONTENUTO))
