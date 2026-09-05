# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The answering service: what an incoming call hears, and when it is owed a call back.

A practice runs its phone the other way round from a call centre. Nobody sits
waiting to pick up: an announcement tells the caller they will be rung back
within a stated time, and the front desk works the queue in rounds a few hours
apart. So the decisions here are not routing ones — they are *what to say* and
*by when the promise falls due*.

Whether the announcement answers at all is a stored setting, never a look at who
happens to be online. Availability-driven behaviour would make the same number
behave differently from one minute to the next depending on whether somebody
left a browser tab open, which is precisely what a practice cannot explain to
its patients.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import cint, get_url, now_datetime

from crm.scheduling import availability
from crm.scheduling.timeutils import from_system_naive, to_system_naive

MODE_ALWAYS = "Always Answering Service"
MODE_RING_FIRST = "Ring Agents First"

SOURCE_TEXT = "Text to Speech"
SOURCE_AUDIO = "Audio File"


def settings():
	"""Cached per request — the inbound webhook reads it several times per call."""
	if not hasattr(frappe.local, "crm_answering_settings"):
		frappe.local.crm_answering_settings = frappe.get_cached_doc("CRM Answering Settings")
	return frappe.local.crm_answering_settings


def is_enabled(config=None) -> bool:
	config = config if config is not None else settings()
	return bool(config.enabled)


def takes_every_call(config=None) -> bool:
	"""Does the announcement answer instead of ringing anyone?

	Read straight off ``answer_mode``. ``Ring Agents First`` keeps the historical
	behaviour and only falls through to the announcement when no agent takes the
	call; ``Always Answering Service`` never rings anyone at all.
	"""
	config = config if config is not None else settings()
	return is_enabled(config) and config.answer_mode == MODE_ALWAYS


def rings_agents_first(config=None) -> bool:
	config = config if config is not None else settings()
	return is_enabled(config) and config.answer_mode == MODE_RING_FIRST


# --------------------------------------------------------------------------
# opening hours
# --------------------------------------------------------------------------


def honours_working_hours(config=None) -> bool:
	config = config if config is not None else settings()
	return bool(cint(config.use_working_hours))


def is_open(config=None, at: datetime.datetime | None = None) -> bool:
	"""Is the practice open? Always ``True`` when working hours are switched off."""
	config = config if config is not None else settings()
	if not honours_working_hours(config):
		return True
	return availability.is_open(availability.company_working_hours(), at)


def callback_due(config=None, at: datetime.datetime | None = None):
	"""When the callback promised to a caller falls due, as a system-naive datetime.

	Counted in *working* hours unless that is switched off, so an evening call is
	due the next morning rather than at midnight.
	"""
	config = config if config is not None else settings()
	start = from_system_naive(at or now_datetime())
	hours = cint(config.callback_hours) or 3
	if honours_working_hours(config):
		due = availability.add_working_time(start, hours * 3600, availability.company_working_hours())
	else:
		due = start + datetime.timedelta(hours=hours)
	return to_system_naive(due)


def retry_due(config=None, at: datetime.datetime | None = None):
	"""When an unanswered callback should come back around."""
	config = config if config is not None else settings()
	start = from_system_naive(at or now_datetime())
	hours = cint(config.retry_after_hours)
	if not hours:
		return to_system_naive(start)
	if honours_working_hours(config):
		due = availability.add_working_time(start, hours * 3600, availability.company_working_hours())
	else:
		due = start + datetime.timedelta(hours=hours)
	return to_system_naive(due)


# --------------------------------------------------------------------------
# the announcement
# --------------------------------------------------------------------------


def default_greeting(open_now: bool) -> str:
	if open_now:
		return _(
			"Thank you for calling. We cannot take your call right now, "
			"but we will call you back within {hours} hours."
		)
	return _(
		"Thank you for calling. We are closed at the moment. We will call you back as soon as we reopen."
	)


def _format_due(due) -> str:
	"""``{time}`` as something a speech engine reads sensibly.

	Time alone when the callback lands today, day and time otherwise. Numeric on
	purpose: month names would have to be localised for every language a practice
	might greet in, and get it wrong out loud.
	"""
	if not due:
		return ""
	due = frappe.utils.get_datetime(due)
	if due.date() == frappe.utils.getdate():
		return frappe.utils.format_datetime(due, "HH:mm")
	return frappe.utils.format_datetime(due, "dd/MM HH:mm")


def render_greeting(config=None, open_now: bool | None = None, due=None) -> str:
	config = config if config is not None else settings()
	if open_now is None:
		open_now = is_open(config)

	template = (config.greeting_text if open_now else config.after_hours_greeting_text) or ""
	template = template.strip() or default_greeting(open_now)

	try:
		return template.format(hours=cint(config.callback_hours) or 3, time=_format_due(due))
	except (KeyError, IndexError, ValueError):
		# an unknown placeholder shouldn't answer the call with a traceback
		frappe.log_error(
			f"Unsupported placeholder in answering greeting: {template!r}", "CRM Answering Service"
		)
		return template


def greeting_audio_url(config=None, open_now: bool | None = None) -> str | None:
	"""Absolute URL of the announcement audio, or ``None`` when there is none to play.

	Private files are refused rather than handed over: the provider fetches the
	URL anonymously and would get a login page, which the caller hears as silence.
	"""
	config = config if config is not None else settings()
	if config.greeting_source != SOURCE_AUDIO:
		return None
	if open_now is None:
		open_now = is_open(config)

	# a practice that never recorded a closed-hours file still gets the open one,
	# which is better than answering with nothing
	path = (config.greeting_audio if open_now else config.after_hours_greeting_audio) or config.greeting_audio
	if not path:
		return None
	if path.startswith("/private/"):
		frappe.log_error(
			f"Answering announcement {path} is a private file and cannot be fetched by the "
			"telephony provider; falling back to text to speech.",
			"CRM Answering Service",
		)
		return None
	return path if path.startswith("http") else get_url(path)
