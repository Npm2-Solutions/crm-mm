# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A call's recording, kept by DottorCloud (doc 65).

Twilio keeps a recording and lets its owner fetch it; Telnyx hands over a link
that works for ten minutes after the call. So the recording is fetched at once,
in a job, and kept as a private file of the call (`CRM Call Log.recording_url` is
then the file's address): the player and the transcription read it through its
`File`, as every private file is read (it may be in the centre's archive). When
the centre forgets recordings after some days, the file goes with the link.
"""

from __future__ import annotations

import frappe
from frappe.utils import cint

REGISTRO = "CRM Call Log"
#: The largest recording DottorCloud keeps, in megabytes: a call of hours.
MASSIMO_MB = 200


def e_un_file(indirizzo: str | None) -> bool:
	"""Whether a recording's address is a file of the site's, not a carrier's link."""
	return (indirizzo or "").startswith(("/private/files/", "/files/"))


def accoda(chiamata: str, indirizzo: str, messaggio: bool = False) -> None:
	"""Fetch the recording in a job, after this request's commit: the link holds
	ten minutes."""
	frappe.enqueue(
		"crm.telephony.telnyx.registrazioni.scarica",
		queue="short",
		chiamata=chiamata,
		indirizzo=indirizzo,
		messaggio=messaggio,
		enqueue_after_commit=True,
	)


def scarica(chiamata: str, indirizzo: str, messaggio: bool = False) -> str | None:
	"""The recording of ``chiamata`` from Telnyx's link, as a private file of the
	call; transcribed when the centre transcribes. A message left on the answering
	service is said to whoever follows the caller once it is there. Returns the
	file's address."""
	from crm.integrations.api import _fetch_recording

	if not frappe.db.exists(REGISTRO, chiamata):
		return None
	risposta = _fetch_recording(indirizzo, None, {})
	try:
		risposta.raise_for_status()
		parti, totale = [], 0
		for parte in risposta.iter_content(chunk_size=64 * 1024):
			totale += len(parte)
			if totale > MASSIMO_MB * 1024 * 1024:
				frappe.throw(frappe._("Recording is larger than the configured limit"))
			parti.append(parte)
		tipo = (risposta.headers.get("Content-Type") or "audio/mpeg").split(";")[0].strip()
	finally:
		risposta.close()
		sessione = getattr(risposta, "_pinned_session", None)
		if sessione is not None:
			sessione.close()

	estensione = "wav" if "wav" in tipo else "mp3"
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{chiamata.replace(':', '-')}.{estensione}"[-140:],
			"attached_to_doctype": REGISTRO,
			"attached_to_name": chiamata,
			"is_private": 1,
			"content": b"".join(parti),
		}
	).insert(ignore_permissions=True)
	valori = {"recording_url": file_doc.file_url}
	if messaggio:
		valori["left_message"] = 1
	frappe.db.set_value(REGISTRO, chiamata, valori)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — a job: the file and its call go together

	if messaggio:
		from crm.telephony import messaggi

		messaggi.avvisa_del_messaggio(chiamata)
	# set_value bypasses document hooks, so the transcription is asked for here
	from crm.telephony import transcription

	if transcription.transcribes_automatically():
		transcription.request_transcription(chiamata)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — the queued job runs elsewhere and must find the row
	return file_doc.file_url


def contenuto(chiamata, intervallo: str | None = None) -> tuple[bytes, str, int, tuple[int, int] | None]:
	"""A kept recording's bytes for the player: all of it, or the part a Range
	header asks (``bytes=a-b``). Returns the bytes, their type, the whole size and
	the part's (start, end), or None for the whole."""
	file_doc = _file_di(chiamata)
	tutto = file_doc.get_content(encodings=[])
	if isinstance(tutto, str):
		tutto = tutto.encode()
	tipo = "audio/wav" if (file_doc.file_name or "").endswith(".wav") else "audio/mpeg"
	parte = _intervallo(intervallo, len(tutto))
	if parte:
		inizio, fine = parte
		return tutto[inizio : fine + 1], tipo, len(tutto), parte
	return tutto, tipo, len(tutto), None


def _file_di(chiamata):
	nome = frappe.db.get_value(
		"File",
		{
			"file_url": chiamata.recording_url,
			"attached_to_doctype": REGISTRO,
			"attached_to_name": chiamata.name,
		},
		"name",
	)
	if not nome:
		frappe.throw(frappe._("Recording URL not found"), frappe.DoesNotExistError)
	return frappe.get_doc("File", nome)


def _intervallo(intestazione: str | None, totale: int) -> tuple[int, int] | None:
	"""A single ``bytes=a-b`` range within ``totale``; None for anything else."""
	valore = (intestazione or "").strip().lower()
	if not valore.startswith("bytes=") or "," in valore or not totale:
		return None
	inizio, _trattino, fine = valore[6:].partition("-")
	if not inizio and fine:
		# the last bytes
		quanti = min(cint(fine), totale)
		return (totale - quanti, totale - 1) if quanti else None
	if not inizio.isdigit():
		return None
	inizio = int(inizio)
	fine = int(fine) if fine.isdigit() else totale - 1
	fine = min(fine, totale - 1)
	return (inizio, fine) if inizio <= fine else None


def togli(chiamata: str, indirizzo: str | None) -> None:
	"""A kept recording forgotten: its file goes with its link."""
	if not e_un_file(indirizzo):
		return
	for nome in frappe.get_all(
		"File",
		filters={"file_url": indirizzo, "attached_to_doctype": REGISTRO, "attached_to_name": chiamata},
		pluck="name",
	):
		frappe.delete_doc("File", nome, ignore_permissions=True)
