# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The agency's bucket, through `requests` (doc 57).

Five calls are all the archive needs: put an object, read it to a file, ask
whether it is there, delete it, and the link a browser follows. One object is one
PUT: the framework's uploads are far below the 5 GB a single PUT takes. The keys
travel in variables named `*_key`, the secret in `secret_key`: an error is logged
with the status and S3's code only, never the request.
"""

from __future__ import annotations

import datetime
import os
import re

import requests

from crm.archivio import regole
from crm.archivio.regole import Configurazione

#: Seconds before a call is given up: to connect, then between two pieces read.
TEMPO = (10, 120)
#: Bytes read at a time when an object comes back.
PEZZO = 1024 * 1024


class ErroreArchivio(Exception):
	"""The bucket said no, or could not be reached. ``stato``: the HTTP status,
	``codice``: S3's error code, when it gave one."""

	def __init__(self, messaggio: str, stato: int | None = None, codice: str | None = None):
		super().__init__(messaggio)
		self.stato = stato
		self.codice = codice


def _adesso() -> datetime.datetime:
	return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def _chiama(
	conf: Configurazione,
	metodo: str,
	chiave: str,
	*,
	parametri=None,
	intestazioni=None,
	payload=regole.VUOTO,
	dati=None,
	stream=False,
	accetta=(200, 204),
):
	host, percorso, base = conf.indirizzo(chiave)
	firmate = regole.firma_intestazioni(
		metodo,
		host,
		percorso,
		access_key=conf.access_key,
		secret_key=conf.secret_key,
		regione=conf.region,
		quando=_adesso(),
		parametri=parametri,
		intestazioni=intestazioni,
		payload=payload,
	)
	url = base + regole._codifica(percorso, barre=True)
	if parametri:
		url += "?" + regole._query(parametri)
	try:
		risposta = requests.request(metodo, url, headers=firmate, data=dati, stream=stream, timeout=TEMPO)
	except requests.RequestException as e:
		raise ErroreArchivio(f"The archive could not be reached: {type(e).__name__}") from None
	if risposta.status_code not in accetta:
		codice = None
		if not stream:
			trovato = re.search(r"<Code>([^<]+)</Code>", risposta.text or "")
			codice = trovato.group(1) if trovato else None
		risposta.close()
		raise ErroreArchivio(
			f"The archive answered {risposta.status_code}" + (f" ({codice})" if codice else ""),
			stato=risposta.status_code,
			codice=codice,
		)
	return risposta


def metti(conf: Configurazione, chiave: str, percorso: str, sha256: str, tipo: str | None = None) -> None:
	"""The file at ``percorso`` as the object ``chiave``. The body's hash is
	signed: the bucket refuses a body that arrived different."""
	intestazioni = {"content-type": tipo or "application/octet-stream"}
	# nosemgrep: frappe-security-file-traversal — the archive's own path (`archivio.percorso`)
	with open(percorso, "rb") as f:
		_chiama(
			conf,
			"PUT",
			chiave,
			intestazioni=intestazioni,
			payload=sha256,
			dati=f,
		).close()


def c_e(conf: Configurazione, chiave: str) -> int | None:
	"""The object's size, None where it is not there."""
	risposta = _chiama(conf, "HEAD", chiave, accetta=(200, 404))
	risposta.close()
	if risposta.status_code == 404:
		return None
	return int(risposta.headers.get("content-length") or 0)


def prendi(conf: Configurazione, chiave: str, percorso: str) -> int:
	"""The object written to ``percorso``, whole or not at all: to a file beside
	it, renamed over it at the end. Its size."""
	risposta = _chiama(conf, "GET", chiave, stream=True, accetta=(200,))
	provvisorio = f"{percorso}.archivio-{os.getpid()}"
	scritti = 0
	try:
		# nosemgrep: frappe-security-file-traversal — beside the archive's own path
		with open(provvisorio, "wb") as f:
			for pezzo in risposta.iter_content(PEZZO):
				f.write(pezzo)
				scritti += len(pezzo)
			f.flush()
			os.fsync(f.fileno())
		os.replace(provvisorio, percorso)
	finally:
		risposta.close()
		if os.path.exists(provvisorio):
			os.remove(provvisorio)
	return scritti


def togli(conf: Configurazione, chiave: str) -> None:
	"""The object deleted; one that is not there is not an error."""
	_chiama(conf, "DELETE", chiave, accetta=(200, 204, 404)).close()


def link(
	conf: Configurazione, chiave: str, nome: str, tipo: str | None = None, scade: int = regole.DURATA_DEL_LINK
) -> str:
	"""The link a browser follows to the object, for ``scade`` seconds, with the
	file's name and type in the answer."""
	host, percorso, base = conf.indirizzo(chiave)
	parametri = {"response-content-disposition": regole.disposizione(nome)}
	if tipo:
		parametri["response-content-type"] = tipo
	return regole.url_firmato(
		"GET",
		host,
		percorso,
		base,
		access_key=conf.access_key,
		secret_key=conf.secret_key,
		regione=conf.region,
		quando=_adesso(),
		scade=scade,
		parametri=parametri,
	)


def imposta_il_bucket(conf: Configurazione, origini=("*",)) -> None:
	"""The bucket as the archive wants it: its versions kept (a file deleted by
	mistake can be found again) and a browser allowed to read what a link opens."""
	import base64
	import hashlib

	for parametro, corpo in (("versioning", regole.VERSIONI), ("cors", regole.regole_cors(list(origini)))):
		dati = corpo.encode()
		_chiama(
			conf,
			"PUT",
			"",
			parametri={parametro: ""},
			intestazioni={
				"content-md5": base64.b64encode(hashlib.md5(dati, usedforsecurity=False).digest()).decode(),
				"content-type": "application/xml",
			},
			payload=hashlib.sha256(dati).hexdigest(),
			dati=dati,
		).close()
