# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Bookings read from notification emails — for platforms that keep their API closed.

Treatwell (Uala), Fresha, Elty, iDoctors, Doctolib, Top Doctors, Pazienti.it and
MioDottore without partner status all e-mail the practice on every booking,
change and cancellation. Adding a CRM mailbox as a (secondary) notification
address, or forwarding those emails to it, is the one integration they cannot
refuse.

The parser is heuristic by necessity — no platform publishes its templates —
but it is strict about what it accepts: without a recognisable date *and* time
it returns nothing rather than guess. It reads Italian and English:

* dates: ``25/09/2026``, ``25-09-26``, ``2026-09-25``, ``giovedì 25 settembre 2026``,
  ``25 settembre``, ``September 25, 2026``, ``25 Sep 2026``
* times: ``alle 10:30``, ``ore 10.30``, ``dalle 10:30 alle 11:15``, ``10:30 - 11:15``, ``3:30 PM``
* labelled fields: ``Cliente:``, ``Paziente:``, ``Servizio:``, ``Trattamento:``,
  ``Prestazione:``, ``Operatore:``, ``Dottore:``, ``Telefono:``, ``Codice prenotazione:``…
* intent: cancelled (annullata, cancellata, disdetta…), moved (spostata, modificata…)

A notification without a booking reference gets a stable id from its content,
and is flagged so the sync can find a cancellation's original by client instead.
"""

from __future__ import annotations

import datetime
import hashlib
import html
import re
from email.utils import parseaddr
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

from crm.booking_platforms.base import (
	STATUS_CANCELLED,
	STATUS_CONFIRMED,
	STATUS_PENDING,
	BookingPlatform,
	ExternalBooking,
	InvalidSignature,
	PlatformError,
	header,
	load_json,
	safe_equal,
)
from crm.booking_platforms.ical import EMAIL_RE, PHONE_RE, ICalFeed

MONTHS = {
	# italiano
	"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
	"luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
	"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12,
	# english
	"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
	"august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
	"jan": 1, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "dec": 12,
}  # fmt: skip
MONTH_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))

CANCEL_RE = re.compile(
	r"\b(annullat\w*|cancellat\w*|disdett\w*|disdic\w*|cancel(?:l)?ed|cancel(?:l)?ation|rifiutat\w*|declined)\b",
	re.I,
)
MOVED_RE = re.compile(
	r"\b(spostat\w*|modificat\w*|riprogrammat\w*|cambiat\w*|rescheduled|changed|moved)\b", re.I
)
PENDING_RE = re.compile(
	r"\b(richiesta di prenotazione|in attesa di conferma|da confermare|booking request|awaiting confirmation)\b",
	re.I,
)

LABELS = {
	"client": r"cliente|paziente|nome(?: e cognome)?(?: (?:del )?cliente)?|client(?:e)?|customer|patient|name|prenotato da|booked by",
	"service": r"servizio|servizi|trattamento|trattamenti|prestazione|visita|tipo di visita|motivo della visita|service|services|treatment",
	"staff": r"operatore|operatrice|professionista|dottore|dottoressa|dott\.?(?:ssa)?|medico|specialista|collaboratore|staff|stylist|with|con",
	"phone": r"telefono|cellulare|tel\.?|phone|mobile|numero di telefono",
	"email": r"e-?mail|indirizzo email",
	"ref": r"codice(?: (?:di )?prenotazione)?|riferimento|rif\.?|id prenotazione|numero (?:di )?prenotazione|n\.? prenotazione|prenotazione n\.?|booking (?:reference|ref\.?|id|number|code)|reference|order",
	"notes": r"note|nota|commento|messaggio|notes|comment|message",
	"price": r"prezzo|importo|totale|costo|price|total|amount",
	"location": r"indirizzo|sede|luogo|dove|address|location|where",
	"duration": r"durata|duration",
}


def html_to_text(value: str) -> str:
	value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value or "")
	value = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h\d|td)>", "\n", value)
	value = re.sub(r"<[^>]+>", " ", value)
	value = html.unescape(value)
	lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in value.splitlines()]
	return "\n".join(line for line in lines if line)


def labelled(text: str, key: str) -> str:
	"""The value after ``Label:`` (same line), or on the next line when the label stands alone."""
	pattern = re.compile(rf"^\s*(?:{LABELS[key]})\s*[:：]\s*(.*)$", re.I | re.M)
	for match in pattern.finditer(text):
		value = match.group(1).strip()
		if not value:
			rest = text[match.end() :].lstrip("\n").split("\n", 1)[0].strip()
			value = rest
		if value:
			return value[:200]
	return ""


def _year(value: str | None, today: datetime.date) -> int:
	if not value:
		return today.year
	year = int(value)
	return year + 2000 if year < 100 else year


def find_date(text: str, today: datetime.date) -> tuple[datetime.date, int] | None:
	"""The first plausible date and where it ends in the text."""
	candidates = []
	for match in re.finditer(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text):
		candidates.append(
			(match.start(), match.end(), int(match.group(1)), int(match.group(2)), int(match.group(3)))
		)
	for match in re.finditer(r"\b(\d{1,2})[/.\-](\d{1,2})(?:[/.\-](\d{2,4}))?\b", text):
		# skip times like 10.30 that the pattern would read as a date without a year
		if not match.group(3) and "." in match.group(0):
			continue
		candidates.append(
			(
				match.start(),
				match.end(),
				_year(match.group(3), today),
				int(match.group(2)),
				int(match.group(1)),
			)
		)
	for match in re.finditer(rf"\b(\d{{1,2}})(?:°|º)?\s+({MONTH_ALT})\.?(?:\s+(\d{{2,4}}))?\b", text, re.I):
		candidates.append(
			(
				match.start(),
				match.end(),
				_year(match.group(3), today),
				MONTHS[match.group(2).lower()],
				int(match.group(1)),
			)
		)
	for match in re.finditer(
		rf"\b({MONTH_ALT})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?(?:\s+(\d{{4}}))?\b", text, re.I
	):
		candidates.append(
			(
				match.start(),
				match.end(),
				_year(match.group(3), today),
				MONTHS[match.group(1).lower()],
				int(match.group(2)),
			)
		)
	for start, end, year, month, day in sorted(candidates):
		try:
			found = datetime.date(year, month, day)
		except ValueError:
			continue
		# a date without a year that already passed means next year
		if found < today - datetime.timedelta(days=60) and not re.search(r"\d{4}", text[start:end]):
			found = found.replace(year=found.year + 1)
		return found, end
	return None


TIME_RE = re.compile(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\s*(am|pm|a\.m\.|p\.m\.)?", re.I)


def _to_time(match) -> datetime.time:
	hour, minute = int(match.group(1)), int(match.group(2))
	suffix = (match.group(3) or "").lower().replace(".", "")
	if suffix == "pm" and hour < 12:
		hour += 12
	if suffix == "am" and hour == 12:
		hour = 0
	return datetime.time(hour, minute)


def find_times(text: str, after: int = 0) -> tuple[datetime.time | None, datetime.time | None]:
	"""Start (and end, when given as a range) — searched after the date first."""
	for segment in (text[after:], text):
		matches = list(TIME_RE.finditer(segment))
		# a date like 25.09 must not be read as a time: require a plausible context
		matches = [m for m in matches if not re.match(r"[/.\-]\d", segment[m.end() : m.end() + 2])]
		if not matches:
			continue
		start = _to_time(matches[0])
		end = None
		if len(matches) > 1 and matches[1].start() - matches[0].end() < 12:
			end = _to_time(matches[1])
		return start, end
	return None, None


def find_duration(text: str) -> int:
	# hours first: in "1h 15min" the minutes are only the remainder
	match = re.search(
		r"\b(\d)\s*(?:h|ore|ora|hours?)\b(?:\s*(?:e\s*)?(\d{1,2})\s*(?:min\w*|m)?)?", text, re.I
	)
	if match:
		return int(match.group(1)) * 60 + int(match.group(2) or 0)
	match = re.search(r"(\d{1,3})\s*(?:min|minuti|minutes|')", text, re.I)
	if match:
		return int(match.group(1))
	return 0


def parse_notification(
	subject: str,
	body: str,
	sender: str = "",
	tz: str = "Europe/Rome",
	today: datetime.date | None = None,
	default_minutes: int = 30,
) -> ExternalBooking | None:
	"""One notification email → one booking, or ``None`` when it is not one."""
	text = body if "<" not in (body or "")[:2000] else html_to_text(body)
	text = f"{subject or ''}\n{text or ''}"
	today = today or datetime.date.today()
	found = find_date(text, today)
	if not found:
		return None
	day, date_end = found
	start_time, end_time = find_times(text, after=date_end)
	if not start_time:
		return None
	try:
		zone = ZoneInfo(tz)
	except Exception:
		zone = ZoneInfo("Europe/Rome")
	start = datetime.datetime.combine(day, start_time, tzinfo=zone)
	if end_time and end_time > start_time:
		end = datetime.datetime.combine(day, end_time, tzinfo=zone)
	else:
		minutes = find_duration(labelled(text, "duration") or text) or default_minutes
		end = start + datetime.timedelta(minutes=minutes)

	status = STATUS_CONFIRMED
	if CANCEL_RE.search(subject or "") or (
		not MOVED_RE.search(subject or "") and CANCEL_RE.search(text[:600])
	):
		status = STATUS_CANCELLED
	elif PENDING_RE.search(text[:800]):
		status = STATUS_PENDING

	own_domain = parseaddr(sender or "")[1].split("@")[-1].lower()
	email = labelled(text, "email")
	if not email:
		for candidate in EMAIL_RE.findall(text):
			if not candidate.lower().endswith(own_domain) and "noreply" not in candidate.lower():
				email = candidate
				break
	email_match = EMAIL_RE.search(email or "")
	phone = labelled(text, "phone")
	phone_match = PHONE_RE.search(phone or "")
	price_text = labelled(text, "price")
	price_match = re.search(
		r"(\d+(?:[.,]\d{1,2})?)",
		price_text.replace(".", "").replace(",", ".") if "," in price_text else price_text,
	)
	client = labelled(text, "client")
	service = labelled(text, "service")
	reference = labelled(text, "ref")
	reference = re.sub(r"[^\w\-/#]", "", reference.split()[0]) if reference else ""
	if reference and not re.search(r"\d", reference):
		reference = ""  # "Codice: vedi app" is not a code

	booking = ExternalBooking(
		external_id=reference
		or hashlib.sha1(
			f"{own_domain}|{start.isoformat()}|{client.lower()}|{service.lower()}".encode()
		).hexdigest()[:20],
		start=start,
		end=end,
		status=status,
		service_name=service,
		staff_name=labelled(text, "staff"),
		customer_name=client,
		email=email_match.group(0) if email_match else "",
		phone=re.sub(r"[\s./-]", "", phone_match.group(0)) if phone_match else "",
		notes=labelled(text, "notes"),
		location=labelled(text, "location"),
		price=float(price_match.group(1)) if price_match else 0.0,
		raw={
			"subject": subject,
			"sender": sender,
			"reference": reference,
			"moved": bool(MOVED_RE.search(subject or "")),
		},
	)
	if not reference:
		# no reference: the sync must find the original by client when it is cancelled or moved
		booking.raw["match_by_customer"] = True
	return booking


class NotificationEmail(ICalFeed):
	"""Any platform through the emails it sends (and its calendar feed, if it has one)."""

	key = "email"
	label = "Notification email (any platform)"
	sector = "general"
	api_access = "none"
	# heuristic by nature: beta until proven on each platform's real emails
	stability = "beta"
	capabilities = frozenset({"email", "webhook", "pull", "feed"})
	required_fields = ()
	fields = ("inbound_email_account", "sender_filter", "ical_url", "webhook_secret")
	#: feeds are optional here; a missing feed is not an authoritative empty window
	authoritative_window = False
	sender_domains: tuple = ()
	setup_help = (
		"Create an Email Account in the CRM for a dedicated mailbox (e.g. prenotazioni@…), "
		"pick it here, and add that address as a notification (or secondary) email on the "
		"platform, or set up a forward. Booking, change and cancellation emails become "
		"appointments. Alternatively send the email as JSON {from, subject, text|html} to the "
		"webhook address (Zapier Email Parser, Make Mailhook, Mailgun routes). If the platform "
		"offers a calendar export link, paste it too."
	)

	def sender_matches(self, sender: str) -> bool:
		domains = [d.strip().lower() for d in (self.value("sender_filter") or "").split(",") if d.strip()]
		domains = domains or list(self.sender_domains)
		if not domains:
			return True
		address = parseaddr(sender or "")[1].lower()
		return any(address.endswith("@" + d) or address.endswith("." + d) or d in address for d in domains)

	def parse_email(self, subject: str, body: str, sender: str) -> list[ExternalBooking]:
		if not self.sender_matches(sender):
			return []
		try:
			from crm.scheduling.timeutils import scheduling_tz

			tz = str(scheduling_tz())
		except Exception:
			tz = "Europe/Rome"
		booking = parse_notification(subject, body, sender, tz)
		return [booking] if booking else []

	def fetch_bookings(self, since, until):
		return super().fetch_bookings(since, until) if self.value("ical_url") else []

	def parse_webhook(self, headers, body, url=""):
		secret = self.secret("webhook_secret")
		if secret and not safe_equal(header(headers, "X-Webhook-Secret"), secret):
			raise InvalidSignature("Email webhook without the agreed secret header")
		content_type = header(headers, "Content-Type").lower()
		if "application/x-www-form-urlencoded" in content_type:
			# Mailgun / SendGrid style inbound routes
			form = {k: v[0] for k, v in parse_qs(body.decode("utf-8", errors="replace")).items()}
			subject, sender = form.get("subject", ""), form.get("from") or form.get("sender", "")
			text = (
				form.get("body-plain")
				or form.get("text")
				or form.get("stripped-text")
				or form.get("body-html")
				or form.get("html", "")
			)
		else:
			payload = load_json(body)
			if not isinstance(payload, dict):
				raise PlatformError("Expected {from, subject, text|html}")
			subject, sender = payload.get("subject", ""), payload.get("from") or payload.get("sender", "")
			text = (
				payload.get("text")
				or payload.get("body_plain")
				or payload.get("html")
				or payload.get("body")
				or ""
			)
		return self.parse_email(subject, text, sender)

	def test(self):
		return "Waiting for the first notification email"


def email_preset(key: str, label: str, sector: str, website: str, domains: tuple, note: str = ""):
	return type(
		f"{key.title().replace('_', '')}Email",
		(NotificationEmail,),
		{
			"key": key,
			"label": label,
			"sector": sector,
			"website": website,
			"api_access": "partner",
			"sender_domains": domains,
			"setup_help": (note + " " if note else "") + NotificationEmail.setup_help,
		},
	)
