# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The library's pictures on every server, with nobody asking (design.md, "Le librerie").

The exercises' pictures and animations are © Gym visual, at 180 by 180 pixels, with its
written authorisation to NPM2 Solutions; never in the code, never loaded by a
page from somebody else's server. Every server brings them onto itself: every
hour `assicura` looks whether it has them all and, when it has not, a job
(`scarica`) fetches the missing ones from the dataset, at the commit the library
was made from, into the bench's assets (`sites/assets/crm-esercizi`), which every
site of the server serves at `/assets/crm-esercizi`. One site's job at a time, at
most one a `GIRO`; the dataset out of reach stops the run, and the next hour tries
again. A site shows them from there (`indirizzo`), unless the agency wrote another
address in the Desk (`CRM Area Settings.exercise_media_url`: a CDN of its own).
"""

from __future__ import annotations

import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

import frappe
import requests

from crm.piani import dataset as D

#: The dataset's commit the library was made from (`dataset.py`).
COMMIT = "7455efae41b330c265e7cd4b78dfa848e7ce5ebd"
SORGENTE = "https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/{commit}/{percorso}"
CARTELLA = "crm-esercizi"
INDIRIZZO = f"/assets/{CARTELLA}"
LAVORO = "crm-immagini-esercizi"
#: A run starts at most once in this many seconds on a server, whichever site asks.
GIRO = 50 * 60
#: Failures in a row that say the dataset is out of reach: the run stops there.
DI_FILA = 25
#: Seconds to reach the dataset, and to read a file.
ATTESA = (5, 30)
#: In the folder, beside the pictures: one run at a time, and when the last began.
LUCCHETTO = ".in-corso"
ULTIMO_GIRO = ".ultimo-giro"


def cartella() -> Path:
	"""Where the server keeps them: beside the apps' assets, for every site."""
	return Path(frappe.local.sites_path).resolve() / "assets" / CARTELLA


def indirizzo() -> str | None:
	"""Where a page finds the server's own copy, once it has one."""
	return INDIRIZZO if (cartella() / "images").is_dir() else None


_letti: dict = {}


def percorsi() -> dict[str, list[str]]:
	"""The pictures and animations the library points to, as the dataset names
	them: only paths of its own shape (`dataset.indirizzo_media`). Read once per
	version of the file."""
	from crm.piani.librerie import LIBRERIA

	chiave = (str(LIBRERIA), LIBRERIA.stat().st_mtime_ns)
	if chiave not in _letti:
		_letti.clear()
		_letti[chiave] = _dal_file(LIBRERIA)
	return _letti[chiave]


def _dal_file(libreria: Path) -> dict[str, list[str]]:
	immagini, animazioni = [], []
	for voce in json.loads(libreria.read_bytes()):
		esercizio = D.esercizio(voce, "en")
		if not esercizio:
			continue
		if esercizio["media_path"]:
			immagini.append(esercizio["media_path"])
		if esercizio["animation_path"]:
			animazioni.append(esercizio["animation_path"])
	return {"images": sorted(set(immagini)), "animations": sorted(set(animazioni))}


def _presente(file: Path) -> bool:
	return file.is_file() and file.stat().st_size > 0


def stato() -> dict:
	"""How many of them this server has."""
	base = cartella()
	return {
		chiave: {"present": sum(_presente(base / p) for p in elenco), "of": len(elenco)}
		for chiave, elenco in percorsi().items()
	}


def mancanti() -> list[str]:
	"""The ones the server has not got yet."""
	base = cartella()
	return [p for elenco in percorsi().values() for p in elenco if not _presente(base / p)]


def _girato_da_poco() -> bool:
	segno = cartella() / ULTIMO_GIRO
	return segno.is_file() and time.time() - segno.stat().st_mtime < GIRO


def assicura() -> None:
	"""Every hour, on every site: a server that lacks some of the pictures fetches
	them, in the background, unless a run began a little while ago."""
	try:
		if _girato_da_poco() or not mancanti():
			return
	except OSError:
		frappe.log_error(title="DottorCloud: the exercises' pictures on this server")
		return
	frappe.enqueue(
		"crm.piani.immagini.scarica",
		queue="long",
		timeout=3600,
		job_id=LAVORO,
		deduplicate=True,
	)


@contextmanager
def _da_solo():
	"""One run at a time on the server: another site's job is fetching, this one goes."""
	base = cartella()
	base.mkdir(parents=True, exist_ok=True)
	descrittore = os.open(base / LUCCHETTO, os.O_CREAT | os.O_RDWR, 0o644)
	try:
		try:
			fcntl.flock(descrittore, fcntl.LOCK_EX | fcntl.LOCK_NB)
		except BlockingIOError:
			yield False
			return
		yield True
	finally:
		# closing it lets the lock go
		os.close(descrittore)


def scarica(sessione: requests.Session | None = None) -> dict:
	"""The pictures and animations the server has not got yet, from the dataset.
	What is there already is not fetched again, a file is written whole or not at
	all, and the dataset out of reach stops the run."""
	fatti = {"downloaded": 0, "failed": 0, "stopped": False, "busy": False}
	with _da_solo() as mio:
		if not mio:
			fatti["busy"] = True
			return fatti
		base = cartella()
		(base / ULTIMO_GIRO).touch()
		propria = sessione is None
		sessione = sessione or requests.Session()
		di_fila = 0
		try:
			for percorso in mancanti():
				if _prendi(sessione, base, percorso):
					fatti["downloaded"] += 1
					di_fila = 0
					continue
				fatti["failed"] += 1
				di_fila += 1
				if di_fila >= DI_FILA:
					fatti["stopped"] = True
					break
		finally:
			if propria:
				sessione.close()
	return fatti


def _prendi(sessione: requests.Session, base: Path, percorso: str) -> bool:
	# a path of the dataset's own shape, checked again: nothing outside the folder
	if not D.indirizzo_media(INDIRIZZO, percorso):
		return False
	try:
		risposta = sessione.get(SORGENTE.format(commit=COMMIT, percorso=percorso), timeout=ATTESA)
	except requests.RequestException:
		return False
	if risposta.status_code != 200 or not risposta.content:
		return False
	file = base / percorso
	file.parent.mkdir(parents=True, exist_ok=True)
	# its own name while it is written: another run never finds it half-way
	provvisorio = file.with_name(f"{file.name}.{os.getpid()}.parziale")
	provvisorio.write_bytes(risposta.content)
	provvisorio.replace(file)
	return True
