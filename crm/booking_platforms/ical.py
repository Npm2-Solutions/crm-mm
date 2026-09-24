# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The universal fallback: a private iCalendar (.ics) feed.

Almost every booking platform that keeps its API for partners — Treatwell,
Fresha, Booksy, Planity, MioDottore's agenda, iDoctors — still lets the
professional sync the agenda to Google or Apple Calendar through a secret
``.ics`` address. Reading that address gives the CRM every booking, near real
time (as often as the scheduler polls), without any partnership.

What a feed cannot carry reliably is the client: most platforms put the name in
the event title and sometimes a phone or email in the description, so both are
fished out with patterns; nothing else is guessed.

The parser is pure and dependency-free (RFC 5545 subset: unfolding, escaping,
TZID/UTC/floating/all-day times, DURATION), so it is tested without a network.
"""

from __future__ import annotations

import datetime
import re
from zoneinfo import ZoneInfo

from crm.booking_platforms.base import (
	STATUS_CANCELLED,
	STATUS_CONFIRMED,
	STATUS_PENDING,
	UTC,
	BookingPlatform,
	ExternalBooking,
	PlatformError,
)

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?:(?:\+|00)\d{1,3}[\s./-]?)?(?:\d[\s./-]?){8,12}\d")
DURATION_RE = re.compile(r"^(-)?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")


def unfold(text: str) -> list[str]:
	"""Undo RFC 5545 line folding: a line starting with space/tab continues the previous."""
	lines: list[str] = []
	for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
		if raw[:1] in (" ", "\t") and lines:
			lines[-1] += raw[1:]
		elif raw:
			lines.append(raw)
	return lines


def split_line(line: str) -> tuple[str, dict, str]:
	"""``DTSTART;TZID=Europe/Rome:20260925T100000`` → name, params, value.

	Colons inside quoted parameter values (``CN="Dr. X: Y"``) do not split.
	"""
	in_quotes = False
	for index, char in enumerate(line):
		if char == '"':
			in_quotes = not in_quotes
		elif char == ":" and not in_quotes:
			head, value = line[:index], line[index + 1 :]
			break
	else:
		return line.upper(), {}, ""
	parts = head.split(";")
	params = {}
	for part in parts[1:]:
		if "=" in part:
			key, val = part.split("=", 1)
			params[key.upper()] = val.strip('"')
	return parts[0].upper(), params, value


def unescape(value: str) -> str:
	out, i = [], 0
	while i < len(value):
		char = value[i]
		if char == "\\" and i + 1 < len(value):
			nxt = value[i + 1]
			out.append("\n" if nxt in "nN" else nxt)
			i += 2
			continue
		out.append(char)
		i += 1
	return "".join(out)


def parse_duration(value: str) -> datetime.timedelta | None:
	match = DURATION_RE.match((value or "").strip())
	if not match:
		return None
	sign, weeks, days, hours, minutes, seconds = match.groups()
	delta = datetime.timedelta(
		weeks=int(weeks or 0),
		days=int(days or 0),
		hours=int(hours or 0),
		minutes=int(minutes or 0),
		seconds=int(seconds or 0),
	)
	return -delta if sign else delta


def parse_ical_time(value: str, params: dict, default_tz: ZoneInfo) -> tuple[datetime.datetime, bool]:
	"""Returns (aware UTC datetime, is_all_day)."""
	value = value.strip()
	if params.get("VALUE") == "DATE" or (len(value) == 8 and value.isdigit()):
		day = datetime.datetime.strptime(value[:8], "%Y%m%d")
		return day.replace(tzinfo=default_tz).astimezone(UTC), True
	utc = value.endswith("Z")
	stamp = datetime.datetime.strptime(value.rstrip("Z")[:15], "%Y%m%dT%H%M%S")
	if utc:
		return stamp.replace(tzinfo=UTC), False
	tz = default_tz
	if params.get("TZID"):
		try:
			tz = ZoneInfo(params["TZID"].strip("/"))
		except Exception:
			tz = WINDOWS_ZONES.get(params["TZID"], default_tz)
	return stamp.replace(tzinfo=tz).astimezone(UTC), False


#: Outlook/Exchange feeds name zones the Windows way
WINDOWS_ZONES = {
	"W. Europe Standard Time": ZoneInfo("Europe/Rome"),
	"Central Europe Standard Time": ZoneInfo("Europe/Budapest"),
	"Romance Standard Time": ZoneInfo("Europe/Paris"),
	"GMT Standard Time": ZoneInfo("Europe/London"),
	"UTC": ZoneInfo("UTC"),
}


def parse_events(text: str, default_tz: str = "Europe/Rome") -> list[dict]:
	"""Every VEVENT as a dict of its (unescaped) properties plus parsed times."""
	try:
		tz = ZoneInfo(default_tz)
	except Exception:
		tz = ZoneInfo("Europe/Rome")
	events, current, depth = [], None, 0
	for line in unfold(text):
		name, params, value = split_line(line)
		if name == "X-WR-TIMEZONE" and current is None:
			try:
				tz = ZoneInfo(value.strip())
			except Exception:
				pass
		if name == "BEGIN":
			if value.upper() == "VEVENT":
				current, depth = {"attendees": []}, 0
			elif current is not None:
				depth += 1  # VALARM inside the event: ignore its properties
			continue
		if name == "END":
			if value.upper() == "VEVENT" and current is not None:
				events.append(current)
				current = None
			elif current is not None:
				depth -= 1
			continue
		if current is None or depth:
			continue
		if name in ("DTSTART", "DTEND"):
			try:
				moment, all_day = parse_ical_time(value, params, tz)
			except ValueError:
				continue
			current[name.lower()] = moment
			if name == "DTSTART":
				current["all_day"] = all_day
		elif name == "ATTENDEE":
			current["attendees"].append(
				{
					"email": value.split(":", 1)[-1] if value.lower().startswith("mailto:") else "",
					"name": params.get("CN", ""),
				}
			)
		elif name == "ORGANIZER":
			current["organizer"] = value.split(":", 1)[-1] if value.lower().startswith("mailto:") else value
			current["organizer_name"] = params.get("CN", "")
		else:
			current[name.lower()] = unescape(value)
	for event in events:
		if "dtstart" in event and "dtend" not in event:
			delta = parse_duration(event.get("duration", "")) or (
				datetime.timedelta(days=1) if event.get("all_day") else datetime.timedelta(minutes=30)
			)
			event["dtend"] = event["dtstart"] + delta
	return events


def find_contact(text: str) -> tuple[str, str]:
	"""(email, phone) mentioned anywhere in a free text, if any."""
	text = text or ""
	email = EMAIL_RE.search(text)
	phone = PHONE_RE.search(EMAIL_RE.sub(" ", text))
	return (email.group(0) if email else "", re.sub(r"[\s./-]", "", phone.group(0)) if phone else "")


def event_to_booking(event: dict, organizer_emails: set[str] | None = None) -> ExternalBooking | None:
	"""A VEVENT → ExternalBooking. All-day events and events without UID are skipped."""
	if event.get("all_day") or not event.get("uid") or "dtstart" not in event:
		return None
	summary = event.get("summary", "").strip()
	description = event.get("description", "")
	status = {"CANCELLED": STATUS_CANCELLED, "TENTATIVE": STATUS_PENDING}.get(
		event.get("status", "").upper(), STATUS_CONFIRMED
	)
	email, phone = find_contact(description + "\n" + summary)
	name = ""
	own = {e.lower() for e in organizer_emails or set()} | {(event.get("organizer") or "").lower()}
	for attendee in event.get("attendees", []):
		if attendee["email"] and attendee["email"].lower() not in own:
			email = email or attendee["email"]
			name = attendee["name"] or name
			break
	service_name = ""
	if not name:
		# "Mario Rossi - Pulizia viso" / "Pulizia viso: Mario Rossi" / "Mario Rossi (Taglio)"
		for sep in (" - ", " – ", " | ", ": "):
			if sep in summary:
				left, right = (p.strip() for p in summary.split(sep, 1))
				name, service_name = left, right
				break
		else:
			match = re.match(r"^(.*?)\s*\((.+)\)\s*$", summary)
			name, service_name = (match.group(1), match.group(2)) if match else (summary, "")
	return ExternalBooking(
		external_id=event["uid"],
		start=event["dtstart"],
		end=event["dtend"],
		status=status,
		service_name=service_name,
		customer_name=name or summary,
		email=email,
		phone=phone,
		notes=description.strip(),
		location=event.get("location", ""),
		url=event.get("url", ""),
		raw={k: (v.isoformat() if isinstance(v, datetime.datetime) else v) for k, v in event.items()},
	)


def parse_feed(
	text: str,
	since: datetime.datetime | None = None,
	until: datetime.datetime | None = None,
	default_tz: str = "Europe/Rome",
) -> list[ExternalBooking]:
	if "BEGIN:VCALENDAR" not in (text or "").upper():
		raise PlatformError("The address does not return an iCalendar feed")
	out = []
	for event in parse_events(text, default_tz):
		booking = event_to_booking(event)
		if not booking:
			continue
		if since and booking.end < since:
			continue
		if until and booking.start > until:
			continue
		out.append(booking)
	return out


class ICalFeed(BookingPlatform):
	"""Any platform through its private calendar export."""

	key = "ical"
	label = "iCal feed"
	sector = "general"
	api_access = "none"
	capabilities = frozenset({"pull", "feed"})
	required_fields = ("ical_url",)
	fields = ("ical_url",)
	setup_help = (
		"Copy the private calendar address (.ics / iCal / 'sync with Google Calendar') "
		"from the platform's agenda settings and paste it here. Bookings are read every "
		"15 minutes; a booking that disappears from the feed is cancelled in the CRM."
	)
	#: feeds carry the full window they know about — missing events mean deleted ones
	authoritative_window = True

	def feed_url(self) -> str:
		url = self.value("ical_url")
		# webcal:// is http(s) for every server we will ever meet
		return "https://" + url[len("webcal://") :] if url.lower().startswith("webcal://") else url

	def fetch_bookings(self, since, until):
		import requests

		url = self.feed_url()
		if not url:
			raise PlatformError("No iCal address configured")
		try:
			response = requests.get(url, timeout=self.timeout, headers={"Accept": "text/calendar"})
		except requests.RequestException as exc:
			raise PlatformError(f"iCal: {exc.__class__.__name__}") from exc
		if not response.ok:
			raise PlatformError(f"iCal HTTP {response.status_code}")
		response.encoding = response.encoding or "utf-8"
		from crm.scheduling.timeutils import scheduling_tz

		return parse_feed(response.text, since, until, str(scheduling_tz()))


def ical_preset(key: str, label: str, sector: str, website: str, docs_url: str = "", help_text: str = ""):
	"""A named platform whose only open door is its calendar export."""
	return type(
		f"{key.title().replace('_', '')}ICal",
		(ICalFeed,),
		{
			"key": key,
			"label": label,
			"sector": sector,
			"website": website,
			"docs_url": docs_url,
			"api_access": "partner",
			"setup_help": help_text or ICalFeed.setup_help,
		},
	)
