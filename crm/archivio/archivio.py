# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's private files on the agency's archive (doc 57).

- **Moving** (`sposta`, every hour): a private file written more than
  `regole.ATTESA` minutes ago goes to the bucket, checked there by its size, and
  `CRM Archived File` says where; on the server an empty file keeps its name, so
  the framework never gives that name to another file and still finds it "on
  disk". A file brought back to be read leaves again the same way.
- **Opening** (`prima_della_richiesta`): `/private/files/…` of an archived file is
  answered by a link to the bucket that lasts minutes, after the framework's own
  check (`find_file_by_url`) and its access log.
- **Reading** (`riporta`, from `crm.overrides.file`): code that reads a file's
  content finds it on the disk again, brought back whole.
- **Deleting** (`al_cestino`, `orfani`): the last File with that address gone, the
  object goes once the transaction is committed; what a deletion by the database
  left behind (the demo data's) goes every night.

Without `dottorcloud_archivio` nothing moves and everything works as before.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import time

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, get_files_path, now_datetime

from crm.archivio import regole, s3

CONF = "dottorcloud_archivio"
#: Where the files brought back wait, besides the database: a request that
#: brought one back and then failed rolled its date back with it.
RIPORTATI = "crm:archivio:riportati"
#: The space used, kept ten minutes.
CHIAVE_SPAZIO = "crm:archivio:spazio"
TITOLO = "Archive"


def conf() -> regole.Configurazione | None:
	return regole.configurazione(frappe.conf.get(CONF), getattr(frappe.local, "site", "") or "")


def nome_di(file_url: str) -> str:
	"""A record's name: its address's fingerprint, which the database finds at once."""
	return hashlib.sha256((file_url or "").encode()).hexdigest()[:32]


def archiviato(file_url: str | None):
	"""The record of an archived file, None for one that is only on the server."""
	if not regole.da_spostare(file_url):
		return None
	return frappe.db.get_value(
		"CRM Archived File",
		nome_di(file_url),
		["name", "file_url", "object_key", "sha256", "size", "restored_on"],
		as_dict=True,
	)


def percorso(file_url: str) -> str:
	"""Where a private file is on the server: inside the site's private files,
	never outside them (`regole.da_spostare` refuses a "..")."""
	if not regole.da_spostare(file_url):
		raise ValueError("not a private file of the site")
	return get_files_path(*file_url[len("/private/files/") :].split("/"), is_private=1)


def _impronta(percorso_locale: str) -> str:
	h = hashlib.sha256()
	# nosemgrep: frappe-security-file-traversal — a path from `percorso()`, inside the private files
	with open(percorso_locale, "rb") as f:
		for pezzo in iter(lambda: f.read(1024 * 1024), b""):
			h.update(pezzo)
	return h.hexdigest()


def _svuota(percorso_locale: str) -> None:
	"""The file left empty, in one step: whoever is reading it keeps reading the
	whole one it opened."""
	provvisorio = f"{percorso_locale}.archivio-vuoto-{os.getpid()}"
	# nosemgrep: frappe-security-file-traversal — beside a path from `percorso()`
	open(provvisorio, "wb").close()
	os.replace(provvisorio, percorso_locale)


def _pieno(percorso_locale: str) -> bool:
	return os.path.isfile(percorso_locale) and os.path.getsize(percorso_locale) > 0


# Moving


def sposta() -> dict:
	"""Every hour: the private files written a while ago, then the ones brought
	back to be read, to the bucket. A file that fails is logged and tried at the
	next round; the bucket unreachable stops the round."""
	c = conf()
	esito = {"moved": 0, "emptied": 0, "bytes": 0, "failed": 0}
	if not c:
		return esito
	soglia = add_to_date(now_datetime(), minutes=-regole.ATTESA)
	budget = [regole.FILE_PER_GIRO, regole.BYTE_PER_GIRO]
	try:
		for riga in _da_archiviare(soglia):
			if budget[0] <= 0 or budget[1] <= 0:
				break
			_archivia_uno(c, riga.file_url, esito, budget)
		for riga in _da_svuotare(soglia):
			if budget[0] <= 0 or budget[1] <= 0:
				break
			_archivia_uno(c, riga.file_url, esito, budget, riportato=True)
	except s3.ErroreArchivio as e:
		if e.stato is None or e.stato >= 500 or e.stato in (401, 403):
			# the bucket itself: unreachable, or the keys refused. Next hour
			frappe.log_error(title=TITOLO, message=str(e))
		else:
			raise
	if esito["moved"]:
		frappe.cache.delete_value(CHIAVE_SPAZIO)
	return esito


def _da_archiviare(soglia):
	"""The private files on the server only, oldest first, one row per address."""
	return frappe.db.sql(
		"""
		select f.file_url, min(f.creation) as creation
		from `tabFile` f
		left join `tabCRM Archived File` a on a.name = left(sha2(f.file_url, 256), 32)
		where f.is_folder = 0 and f.is_private = 1
			and f.file_url like %(privati)s
			and f.creation < %(soglia)s
			and a.name is null
		group by f.file_url
		order by creation
		limit %(quanti)s
		""",
		{"soglia": soglia, "quanti": regole.FILE_PER_GIRO, "privati": "/private/files/%"},
		as_dict=True,
	)


def _da_svuotare(soglia):
	"""The archived files brought back to be read a while ago."""
	nomi = set()
	try:
		nomi = {n.decode() if isinstance(n, bytes) else n for n in frappe.cache.smembers(RIPORTATI)}
	except Exception:
		nomi = set()
	righe = frappe.get_all(
		"CRM Archived File",
		filters={"restored_on": ["<", soglia]},
		fields=["name", "file_url"],
		limit=regole.FILE_PER_GIRO,
	)
	visti = {r.name for r in righe}
	altri = [n for n in nomi if n not in visti]
	if altri:
		righe += frappe.get_all(
			"CRM Archived File", filters={"name": ["in", altri]}, fields=["name", "file_url"]
		)
	return righe


def _archivia_uno(c, file_url: str, esito: dict, budget: list, riportato: bool = False) -> None:
	if not regole.da_spostare(file_url):
		return
	locale = percorso(file_url)
	if not _pieno(locale):
		if riportato:
			_dimentica_riportato(nome_di(file_url))
		return
	if riportato and os.path.getmtime(locale) > time.time() - regole.ATTESA * 60:
		return
	try:
		dimensione = os.path.getsize(locale)
		impronta = _impronta(locale)
		record = archiviato(file_url)
		vecchia = None
		if not record or record.sha256 != impronta:
			nome = file_url.rsplit("/", 1)[-1]
			chiave = regole.chiave(c.prefisso, impronta, nome)
			s3.metti(c, chiave, locale, impronta, mimetypes.guess_type(nome)[0])
			if s3.c_e(c, chiave) != dimensione:
				raise s3.ErroreArchivio("The archive holds a different size", stato=0)
			if record:
				vecchia = record.object_key
				frappe.db.set_value(
					"CRM Archived File",
					record.name,
					{
						"object_key": chiave,
						"sha256": impronta,
						"size": dimensione,
						"archived_on": now_datetime(),
						"restored_on": None,
					},
					update_modified=False,
				)
			else:
				frappe.get_doc(
					{
						"doctype": "CRM Archived File",
						"file_url": file_url,
						"object_key": chiave,
						"sha256": impronta,
						"size": dimensione,
						"archived_on": now_datetime(),
					}
				).insert(ignore_permissions=True)
			esito["moved"] += 1
			esito["bytes"] += dimensione
			budget[1] -= dimensione
		elif record.restored_on:
			frappe.db.set_value("CRM Archived File", record.name, "restored_on", None, update_modified=False)
		# the record first, then the disk: a file emptied with no record would be lost
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — each file is its own step
		_svuota(locale)
		_dimentica_riportato(nome_di(file_url))
		esito["emptied"] += 1
		budget[0] -= 1
		if vecchia and not frappe.db.exists("CRM Archived File", {"object_key": vecchia}):
			s3.togli(c, vecchia)
	except s3.ErroreArchivio as e:
		frappe.db.rollback()
		if e.stato is None or (e.stato and (e.stato >= 500 or e.stato in (401, 403))):
			raise
		esito["failed"] += 1
		frappe.log_error(title=TITOLO, message=f"{file_url}: {e}")
	except OSError as e:
		frappe.db.rollback()
		esito["failed"] += 1
		frappe.log_error(title=TITOLO, message=f"{file_url}: {type(e).__name__}")


def _dimentica_riportato(nome: str) -> None:
	try:
		frappe.cache.srem(RIPORTATI, nome)
	except Exception:
		pass


# Reading


def riporta(file_url: str | None) -> bool:
	"""An archived file whose content somebody's code reads, back on the server,
	whole: its fingerprint checked. True where it was brought back."""
	record = archiviato(file_url)
	if not record:
		return False
	locale = percorso(file_url)
	if _pieno(locale) or not record.size:
		return False
	c = conf()
	if not c:
		frappe.throw(
			_("This file is in the archive, which this site cannot reach. The agency can tell why."),
			title=_("File in the archive"),
		)
	try:
		s3.prendi(c, record.object_key, locale)
	except s3.ErroreArchivio:
		frappe.log_error(title=TITOLO, message=f"{file_url}: could not be brought back")
		frappe.throw(_("The file could not be brought back from the archive. Try again in a minute."))
	if record.sha256 and _impronta(locale) != record.sha256:
		_svuota(locale)
		frappe.log_error(title=TITOLO, message=f"{file_url}: the archive gave back another content")
		frappe.throw(_("The file could not be brought back from the archive. Try again in a minute."))
	frappe.db.set_value(
		"CRM Archived File", record.name, "restored_on", now_datetime(), update_modified=False
	)
	try:
		frappe.cache.sadd(RIPORTATI, record.name)
	except Exception:
		pass
	return True


# Opening


def prima_della_richiesta() -> None:
	"""`/private/files/…` of an archived file: whoever may read it, as the
	framework decides, goes to the bucket by a link that lasts minutes. Anybody
	else, and any file still on the server, is the framework's to answer."""
	richiesta = getattr(frappe.local, "request", None)
	if not richiesta or richiesta.method != "GET" or not richiesta.path.startswith("/private/files/"):
		return
	file_url = richiesta.path
	record = archiviato(file_url)
	if not record or _pieno(percorso(file_url)):
		return

	if frappe.session.user == "Guest" and richiesta.headers.get("Authorization"):
		# an API key: the framework checks it after this hook, so here first
		from frappe.auth import validate_auth

		validate_auth()
	if frappe.session.user == "Guest":
		return
	from frappe.core.doctype.file.utils import find_file_by_url

	file = find_file_by_url(file_url, name=frappe.form_dict.fid)
	if not file:
		return

	from frappe.core.doctype.access_log.access_log import make_access_log
	from werkzeug.exceptions import HTTPException, NotFound
	from werkzeug.utils import redirect

	make_access_log(doctype="File", document=file.name, file_type=os.path.splitext(file_url)[-1][1:])
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — the access log stays, whatever the answer
	c = conf()
	if not c:
		raise NotFound
	nome = file.file_name or file_url.rsplit("/", 1)[-1]
	risposta = redirect(s3.link(c, record.object_key, nome, mimetypes.guess_type(nome)[0]), code=302)
	risposta.headers["Cache-Control"] = "private, no-store"
	risposta.headers["Referrer-Policy"] = "no-referrer"
	raise HTTPException(response=risposta)


# Deleting


def al_cestino(doc, method=None) -> None:
	"""File on_trash: the last File with this address gone, the record goes, and
	the object once the deletion is committed."""
	if not regole.da_spostare(doc.file_url):
		return
	if frappe.db.exists("File", {"file_url": doc.file_url, "name": ["!=", doc.name]}):
		return
	record = archiviato(doc.file_url)
	if not record:
		return
	frappe.db.delete("CRM Archived File", {"name": record.name})
	chiave = record.object_key
	frappe.db.after_commit.add(lambda: _togli_dopo(chiave))
	frappe.cache.delete_value(CHIAVE_SPAZIO)


def _togli_dopo(chiave: str) -> None:
	c = conf()
	if not c or frappe.db.exists("CRM Archived File", {"object_key": chiave}):
		return
	try:
		s3.togli(c, chiave)
	except s3.ErroreArchivio as e:
		frappe.log_error(title=TITOLO, message=f"{chiave}: {e}")


def orfani() -> int:
	"""Every night: the records whose files are gone without passing through
	their deletion (by the database: the demo data's), and their objects."""
	righe = frappe.db.sql(
		"""
		select a.name, a.object_key from `tabCRM Archived File` a
		where not exists (select 1 from `tabFile` f where f.file_url = a.file_url)
		limit 5000
		""",
		as_dict=True,
	)
	if not righe:
		return 0
	frappe.db.delete("CRM Archived File", {"name": ["in", [r.name for r in righe]]})
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — the records before the objects
	c = conf()
	if c:
		for riga in righe:
			if not frappe.db.exists("CRM Archived File", {"object_key": riga.object_key}):
				try:
					s3.togli(c, riga.object_key)
				except s3.ErroreArchivio as e:
					frappe.log_error(title=TITOLO, message=f"{riga.object_key}: {e}")
	frappe.cache.delete_value(CHIAVE_SPAZIO)
	return len(righe)


# The space


def spazio() -> dict:
	"""Bytes the centre's files take, each address once, and how many are on the
	archive. Kept ten minutes."""
	valore = frappe.cache.get_value(CHIAVE_SPAZIO)
	if valore:
		return valore
	usato = frappe.db.sql(
		"""
		select coalesce(sum(dimensione), 0) from (
			select max(file_size) as dimensione from `tabFile`
			where is_folder = 0 and file_url like %(nostri)s
			group by file_url
		) t
		""",
		{"nostri": "/%"},
	)[0][0]
	archiviati = frappe.db.sql("select coalesce(sum(size), 0) from `tabCRM Archived File`")[0][0]
	valore = {"used": cint(usato), "archived": cint(archiviati)}
	frappe.cache.set_value(CHIAVE_SPAZIO, valore, expires_in_sec=600)
	return valore


# The agency's (bench --site … execute)


def imposta_il_bucket(origini: list | None = None) -> str:
	"""The bucket's versions on and its CORS for the browsers: once, when the
	agency creates it (`bench execute crm.archivio.archivio.imposta_il_bucket`)."""
	c = conf()
	if not c:
		return "dottorcloud_archivio is not configured"
	s3.imposta_il_bucket(c, tuple(origini or ("*",)))
	return "ok"


def riporta_tutto() -> int:
	"""Every archived file back on the server and its record gone, leaving the
	objects in the bucket: before switching the archive off, or moving the site
	where it cannot reach it."""
	quanti = 0
	for riga in frappe.get_all("CRM Archived File", fields=["name", "file_url"]):
		riporta(riga.file_url)
		frappe.db.delete("CRM Archived File", {"name": riga.name})
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — one file at a time
		quanti += 1
	frappe.cache.delete_value(CHIAVE_SPAZIO)
	return quanti
