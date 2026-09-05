# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Turning a call recording into text.

The endpoint is anything that speaks the OpenAI audio-transcription API. That is
one adapter for three very different deployments — a Whisper server the practice
runs itself, OpenAI, or Azure OpenAI — which matters here because the choice is
not really a technical one: a practice handling health data may need the audio
never to leave its own machine, and that decision should be a URL in a settings
page rather than a different branch of this file.

Transcription runs in a background job. A recording arrives on a webhook while
the provider waits for a reply, and a minute spent talking to a speech model is
a minute that webhook is not answering.
"""

from __future__ import annotations

import frappe
import requests
from frappe import _
from frappe.utils import add_to_date, cint, now_datetime

PENDING = "Pending"
IN_PROGRESS = "In Progress"
COMPLETED = "Completed"
FAILED = "Failed"
SKIPPED = "Skipped"

OPEN_STATUSES = (PENDING, IN_PROGRESS)

_EXTENSIONS = {
	"audio/mpeg": "mp3",
	"audio/mp3": "mp3",
	"audio/wav": "wav",
	"audio/x-wav": "wav",
	"audio/wave": "wav",
	"audio/ogg": "ogg",
	"audio/mp4": "mp4",
	"audio/m4a": "m4a",
	"audio/webm": "webm",
}


def settings():
	"""Cached per request."""
	if not hasattr(frappe.local, "crm_transcription_settings"):
		frappe.local.crm_transcription_settings = frappe.get_cached_doc("CRM Transcription Settings")
	return frappe.local.crm_transcription_settings


def is_enabled(config=None) -> bool:
	config = config if config is not None else settings()
	return bool(config.enabled and config.base_url and config.model)


def transcribes_automatically(config=None) -> bool:
	config = config if config is not None else settings()
	return is_enabled(config) and bool(cint(config.auto_transcribe))


# --------------------------------------------------------------------------
# queueing
# --------------------------------------------------------------------------


def request_transcription(call_log_name: str, force: bool = False, config=None) -> bool:
	"""Queue a call for transcription. Returns whether anything was queued.

	The status is moved to ``Pending`` here rather than inside the job, so a second
	request for the same call finds it already claimed instead of paying the
	provider twice for the same audio.
	"""
	config = config if config is not None else settings()
	if not is_enabled(config):
		return False

	row = frappe.db.get_value(
		"CRM Call Log",
		call_log_name,
		["recording_url", "transcription_status"],
		as_dict=True,
	)
	if not row or not row.recording_url:
		return False
	if not force and (row.transcription_status in OPEN_STATUSES or row.transcription_status == COMPLETED):
		return False

	frappe.db.set_value(
		"CRM Call Log",
		call_log_name,
		{"transcription_status": PENDING, "transcription_error": None},
		update_modified=False,
	)
	frappe.enqueue(
		"crm.telephony.transcription.transcribe_call",
		queue="long",
		timeout=cint(config.request_timeout) + 120,
		call_log_name=call_log_name,
		enqueue_after_commit=True,
	)
	return True


def on_call_log_update(doc, method=None) -> None:
	"""Doc hook: a recording that has just landed gets queued.

	Only fires on a real change, so re-saving a call for any other reason does not
	send the same audio off again.
	"""
	if not doc.get("recording_url") or not doc.has_value_changed("recording_url"):
		return
	if not transcribes_automatically():
		return
	request_transcription(doc.name)


# --------------------------------------------------------------------------
# the job
# --------------------------------------------------------------------------


def transcribe_call(call_log_name: str) -> str | None:
	"""Fetch the recording, transcribe it, store the text.

	Never raises: a call whose transcription failed is still a call, and the
	failure belongs on the record where somebody can see it and retry.
	"""
	config = settings()
	if not is_enabled(config):
		return None

	call_log = frappe.get_doc("CRM Call Log", call_log_name)
	if not call_log.recording_url:
		_finish(call_log_name, SKIPPED, error=_("The call has no recording."))
		return None

	frappe.db.set_value(
		"CRM Call Log", call_log_name, "transcription_status", IN_PROGRESS, update_modified=False
	)
	frappe.db.commit()

	try:
		from crm.integrations.api import download_recording

		audio, content_type = download_recording(
			call_log, max_bytes=cint(config.max_recording_mb) * 1024 * 1024
		)
		text = _post_audio(config, audio, _filename(call_log_name, content_type), content_type)
	except Exception as exc:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "CRM Transcription: failed")
		_finish(call_log_name, FAILED, error=_short(exc))
		return None

	_finish(call_log_name, COMPLETED, text=text, language=config.language)
	_announce(call_log_name)
	return text


def _post_audio(config, audio: bytes, filename: str, content_type: str) -> str:
	endpoint = f"{config.base_url.rstrip('/')}/audio/transcriptions"
	data = {"model": config.model, "response_format": "json"}
	if config.language:
		data["language"] = config.language
	if config.prompt:
		data["prompt"] = config.prompt

	headers = {}
	if api_key := config.get_password("api_key", raise_exception=False):
		headers["Authorization"] = f"Bearer {api_key}"

	response = requests.post(
		endpoint,
		files={"file": (filename, audio, content_type)},
		data=data,
		headers=headers,
		timeout=cint(config.request_timeout) or 300,
	)
	response.raise_for_status()

	payload = response.json()
	text = (payload or {}).get("text")
	if not isinstance(text, str):
		raise ValueError(f"Unexpected transcription response: {str(payload)[:200]}")
	return text.strip()


def _filename(call_log_name: str, content_type: str) -> str:
	extension = _EXTENSIONS.get((content_type or "").split(";")[0].strip().lower(), "mp3")
	return f"{call_log_name}.{extension}"


def _short(exc: Exception, limit: int = 500) -> str:
	return f"{type(exc).__name__}: {exc}"[:limit]


def _finish(call_log_name: str, status: str, text: str | None = None, language=None, error=None) -> None:
	values = {"transcription_status": status, "transcription_error": error}
	if status == COMPLETED:
		values.update({"transcript": text, "transcribed_on": now_datetime(), "transcript_language": language})
	frappe.db.set_value("CRM Call Log", call_log_name, values, update_modified=False)
	frappe.db.commit()


def _announce(call_log_name: str) -> None:
	"""Let the automations know there is something to read.

	This is the seam an external agent hangs off: the transcript is on the call and
	an event says so, without this file having to know what anyone wants to do with it.
	"""
	try:
		from crm.automation.engine import process_event

		process_event("call_transcribed", frappe.get_doc("CRM Call Log", call_log_name))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM Transcription: automation event failed")


# --------------------------------------------------------------------------
# retention
# --------------------------------------------------------------------------


def expire_transcripts() -> dict:
	"""Nightly: forget what there is no longer a reason to keep.

	Call content is personal data and, in a health practice, a special category of
	it. Retention is a setting because the right answer differs per practice, but
	forgetting has to be automatic — nobody remembers to prune by hand.
	"""
	config = settings()
	cleared = {"transcripts": 0, "recordings": 0}

	if days := cint(config.transcript_retention_days):
		cutoff = add_to_date(now_datetime(), days=-days)
		names = frappe.get_all(
			"CRM Call Log",
			filters={"transcript": ["is", "set"], "creation": ["<", cutoff]},
			pluck="name",
		)
		for name in names:
			frappe.db.set_value(
				"CRM Call Log",
				name,
				{"transcript": None, "transcript_language": None, "transcription_status": None},
				update_modified=False,
			)
		cleared["transcripts"] = len(names)

	if days := cint(config.recording_retention_days):
		cutoff = add_to_date(now_datetime(), days=-days)
		names = frappe.get_all(
			"CRM Call Log",
			filters={"recording_url": ["is", "set"], "creation": ["<", cutoff]},
			pluck="name",
		)
		for name in names:
			frappe.db.set_value("CRM Call Log", name, "recording_url", None, update_modified=False)
		cleared["recordings"] = len(names)

	frappe.db.commit()
	return cleared


# --------------------------------------------------------------------------
# api
# --------------------------------------------------------------------------


@frappe.whitelist()
def transcribe_now(call_log: str) -> dict:
	"""Ask for a transcription from the call's own screen."""
	if not frappe.has_permission("CRM Call Log", "write", call_log):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if not is_enabled():
		frappe.throw(_("Transcription is not configured."), title=_("Not Configured"))

	queued = request_transcription(call_log, force=True)
	return {"queued": queued, "status": PENDING if queued else None}


@frappe.whitelist()
def get_transcript(call_log: str) -> dict:
	"""The transcript of one call, for a person or an agent reading over the API."""
	if not frappe.has_permission("CRM Call Log", "read", call_log):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	row = frappe.db.get_value(
		"CRM Call Log",
		call_log,
		[
			"name",
			"transcript",
			"transcription_status",
			"transcription_error",
			"transcribed_on",
			"transcript_language",
			"duration",
			"type",
			"reference_doctype",
			"reference_docname",
		],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)
	return row


@frappe.whitelist()
def is_transcription_enabled() -> bool:
	return is_enabled()
