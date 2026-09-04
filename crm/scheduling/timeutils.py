# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Timezone plumbing shared by the scheduling engine and the booking pages.

One rule, applied everywhere: **all slot math happens on timezone-aware UTC
datetimes**, while rows persist naive datetimes in the site's system timezone
(the framework-wide convention). Cross the boundary only through the two
converters below.
"""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import get_system_timezone

UTC = datetime.timezone.utc


def system_tz() -> ZoneInfo:
	return ZoneInfo(get_system_timezone())


def scheduling_tz() -> ZoneInfo:
	"""Timezone the weekly working hours are expressed in.

	Configurable in CRM Scheduling Settings so an agency in Rome can run a site
	stored in UTC without every availability row being off by an hour.
	"""
	configured = None
	if frappe.db.exists("DocType", "CRM Scheduling Settings"):
		configured = frappe.db.get_single_value("CRM Scheduling Settings", "timezone")
	if configured:
		try:
			return ZoneInfo(configured)
		except Exception:
			frappe.log_error(f"Invalid scheduling timezone: {configured}", "Scheduling")
	return system_tz()


def to_system_naive(aware: datetime.datetime) -> datetime.datetime:
	return aware.astimezone(system_tz()).replace(tzinfo=None)


def from_system_naive(naive) -> datetime.datetime:
	from frappe.utils import get_datetime

	value = get_datetime(naive)
	if value.tzinfo is not None:
		return value.astimezone(UTC)
	return value.replace(tzinfo=system_tz()).astimezone(UTC)


def as_time(value) -> datetime.time:
	"""Time fields load as ``timedelta`` from the DB but as ``time`` from forms."""
	if isinstance(value, datetime.timedelta):
		total = int(value.total_seconds())
		return datetime.time(hour=total // 3600 % 24, minute=total // 60 % 60, second=total % 60)
	if isinstance(value, str):
		return datetime.time.fromisoformat(value)
	if isinstance(value, datetime.datetime):
		return value.time()
	return value


def day_bounds(day: datetime.date, tz: ZoneInfo) -> tuple[datetime.datetime, datetime.datetime]:
	"""Midnight-to-midnight of a calendar day in ``tz``, as aware UTC."""
	start = datetime.datetime.combine(day, datetime.time.min, tzinfo=tz).astimezone(UTC)
	end = datetime.datetime.combine(
		day + datetime.timedelta(days=1), datetime.time.min, tzinfo=tz
	).astimezone(UTC)
	return start, end


def parse_utc(value) -> datetime.datetime:
	"""Accept an ISO string (with or without offset) or a datetime; return aware UTC."""
	if isinstance(value, datetime.datetime):
		return value.astimezone(UTC) if value.tzinfo else from_system_naive(value)
	try:
		parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
	except ValueError:
		frappe.throw(frappe._("Invalid datetime: {0}").format(value))
	return parsed.astimezone(UTC) if parsed.tzinfo else from_system_naive(parsed)


def parse_date(value) -> datetime.date:
	if isinstance(value, datetime.datetime):
		return value.date()
	if isinstance(value, datetime.date):
		return value
	try:
		return datetime.date.fromisoformat(str(value)[:10])
	except ValueError:
		frappe.throw(frappe._("Invalid date: {0}").format(value))
