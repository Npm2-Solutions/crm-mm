# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the person writes to the centre from their area, without a site: the
words, and one file - a photo or a PDF, told by its first bytes, never by the name
it came with - and how big. Tested with plain `unittest`."""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass

#: The most a message holds, as the desk's board.
MAX_TESTO = 4000
#: A photo from a phone or a scanned page: five megabytes at most.
MAX_MB = 5
MAX_ALLEGATO = MAX_MB * 1024 * 1024
#: What a file may be, by its first bytes: its extension.
FIRME = (
	(b"%PDF", "pdf"),
	(b"\x89PNG\r\n\x1a\n", "png"),
	(b"\xff\xd8\xff", "jpg"),
)


@dataclass(frozen=True)
class Problema:
	"""What is wrong, in English words to translate, with their arguments."""

	messaggio: str
	argomenti: tuple = ()

	def testo(self, traduci=lambda s: s) -> str:
		return traduci(self.messaggio).format(*self.argomenti)


def tipo_del_file(contenuto: bytes | None) -> str | None:
	"""The extension a file's first bytes say it is: a PDF, a PNG, a JPEG, a WebP
	or an iPhone's HEIC photo; None for anything else."""
	if not contenuto:
		return None
	for firma, estensione in FIRME:
		if contenuto.startswith(firma):
			return estensione
	if contenuto[:4] == b"RIFF" and contenuto[8:12] == b"WEBP":
		return "webp"
	if contenuto[4:8] == b"ftyp" and contenuto[8:12] in (b"heic", b"heix", b"mif1", b"msf1"):
		return "heic"
	return None


def dal_data_url(valore: str | None) -> bytes | None:
	"""The bytes of a file the browser read (`data:…;base64,…`); None when there is
	none, or it is not one."""
	if not valore or not isinstance(valore, str):
		return None
	_testa, virgola, dati = valore.partition(",")
	if not virgola or ";base64" not in _testa:
		return None
	try:
		return base64.b64decode(dati, validate=True)
	except (binascii.Error, ValueError):
		return None


def nome_del_file(nome: str | None, estensione: str) -> str:
	"""A name to keep the file by: the one it came with, without a path or odd
	signs, ending with what it really is."""
	base = re.split(r"[\\/]", (nome or "").strip())[-1]
	base = base.rsplit(".", 1)[0] if "." in base else base
	base = re.sub(r"[^\w\- ]+", "", base, flags=re.UNICODE).strip()[:60] or "file"
	return f"{base}.{estensione}"


def problemi(testo: str | None, allegato: bytes | None, c_era_un_file: bool = False) -> list[Problema]:
	"""What stops a message: nothing written and nothing attached, words beyond
	the board's, a file too big or not a photo nor a PDF. ``c_era_un_file``: the
	browser sent one that could not be read."""
	parole = (testo or "").strip()
	fatto = []
	if c_era_un_file and allegato is None:
		fatto.append(Problema("The file could not be read: attach it again"))
	if not parole and not allegato and not c_era_un_file:
		fatto.append(Problema("Write the message or attach a file"))
	if len(parole) > MAX_TESTO:
		fatto.append(Problema("A message is at most {0} characters", (MAX_TESTO,)))
	if allegato is not None:
		if len(allegato) > MAX_ALLEGATO:
			fatto.append(Problema("The file is larger than {0} MB", (MAX_MB,)))
		elif not tipo_del_file(allegato):
			fatto.append(Problema("Only a photo or a PDF can be attached"))
	return fatto
