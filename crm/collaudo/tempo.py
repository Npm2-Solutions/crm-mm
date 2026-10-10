# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The test bench's clock, moved forward so that a week passes in an hour
(e2e/simulazione).

Frappe asks the hour of Python's ``datetime`` and ``time`` (`frappe.utils.
now_datetime`, ``nowdate``, ``now``): ``frappe.flags.current_date`` moves only
``now()``. So the clock moves with freezegun - Frappe's own tests' - ticking: the
bench reads its real time plus a gap (``scarto``, seconds) the simulation sets.
Every process applies it before it serves anything of the site (``before_request``,
``before_job``): the web server's threads read the same hour, and so does a job a
request enqueued, each in the worker that runs it. The scheduler stays paused on a
test bench (a new site's is off): the simulation runs a scheduled job at the hour
it wants, in the request that asks (`esegui`).

Only where the site's config says ``"dottorcloud_collaudo": 1``: on any other site
the hook does nothing but put a moved clock back - a process serving two sites
never carries the bench's hour into the other. The database's own ``NOW()`` keeps
the real hour: DottorCloud asks Python's.
"""

from __future__ import annotations

import datetime
import threading

import frappe
from frappe import _
from frappe.utils import cint, get_datetime

from crm.collaudo import attivo, verifica

#: Where the gap is kept: the site's defaults, which survive a cache cleared.
SCARTO = "crm_collaudo_scarto"
#: What freezegun leaves to the real clock: Redis, the job queue and the web
#: server time their own waits and expiries.
REALI = ["rq", "redis", "werkzeug", "gunicorn", "socketio", "engineio"]

_blocco = threading.Lock()
#: (gap, freezer) of this process, while its clock is moved
_spostato: tuple[float, object] | None = None


def _utc_reale() -> datetime.datetime:
	"""The real hour, in UTC, whatever this process's clock says."""
	from freezegun.api import real_datetime

	return real_datetime.now(datetime.UTC).replace(tzinfo=None)


def _applica(scarto: float | None) -> None:
	"""This process's clock moved by ``scarto`` seconds, or back to the real one."""
	global _spostato
	if (_spostato[0] if _spostato else None) == scarto:
		return
	with _blocco:
		if (_spostato[0] if _spostato else None) == scarto:
			return
		if _spostato:
			_spostato[1].stop()
			_spostato = None
		if scarto is None:
			return
		from freezegun import freeze_time

		congelatore = freeze_time(
			_utc_reale() + datetime.timedelta(seconds=scarto), tick=True, ignore=list(REALI)
		)
		congelatore.start()
		_spostato = (scarto, congelatore)


def _scarto() -> float | None:
	valore = frappe.db.get_default(SCARTO)
	return float(valore) if valore not in (None, "") else None


def allinea(*args, **kwargs) -> None:
	"""Before every request and job: the bench's hour on a test bench, the real one
	elsewhere. Accepts and ignores arguments, as a ``before_job`` hook is given the
	job's method."""
	if not _spostato and not attivo():
		return
	if not attivo():
		_applica(None)
		return
	try:
		_applica(_scarto())
	except ImportError:
		# freezegun is a development requirement of the framework: without it the
		# clock stays real, and `imposta` says why
		pass


def _centro(quando: datetime.datetime) -> datetime.datetime:
	"""A moment in the centre's clock as UTC, without a zone."""
	from zoneinfo import ZoneInfo

	from frappe.utils.data import get_system_timezone

	return (
		quando.replace(tzinfo=ZoneInfo(get_system_timezone())).astimezone(datetime.UTC).replace(tzinfo=None)
	)


def _stato() -> dict:
	from frappe.utils import now_datetime

	scarto = _scarto()
	return {
		"now": str(now_datetime()),
		"offset": scarto or 0,
		"moved": scarto is not None,
		"real_utc": str(_utc_reale()),
	}


@frappe.whitelist(methods=["POST"])
def imposta(quando: str) -> dict:
	"""Move the bench's clock to ``quando`` (the centre's hour, ``YYYY-MM-DD HH:MM``):
	from now on it ticks from there. Never backwards past what the bench already
	lived, or a record would come before the one it follows."""
	verifica()
	try:
		import freezegun
	except ImportError:
		frappe.throw(
			_(
				"The clock of a test bench moves with freezegun: install the framework's development requirements (bench setup requirements --dev)"
			)
		)
	scarto = (_centro(get_datetime(quando)) - _utc_reale()).total_seconds()
	precedente = _scarto() or 0
	if scarto < precedente - 60 and not cint(frappe.form_dict.get("indietro")):
		frappe.throw(_("The clock of a test bench only moves forward"))
	frappe.db.set_default(SCARTO, str(round(scarto, 3)))
	frappe.db.commit()
	_applica(_scarto())
	return _stato()


@frappe.whitelist()
def adesso() -> dict:
	"""The bench's hour, and how far it is from the real one."""
	verifica()
	return _stato()


@frappe.whitelist(methods=["POST"])
def azzera() -> dict:
	"""The bench back on the real clock."""
	verifica()
	frappe.db.set_default(SCARTO, "")
	frappe.db.commit()
	_applica(None)
	return _stato()


def lavori_programmati() -> set[str]:
	"""Every scheduled job the installed apps declare."""
	lavori = set()
	for eventi in frappe.get_hooks("scheduler_events").values():
		if isinstance(eventi, dict):
			for metodi in eventi.values():
				lavori.update(metodi)
		else:
			lavori.update(eventi)
	return lavori


@frappe.whitelist(methods=["POST"])
def esegui(metodo: str) -> dict:
	"""Run a scheduled job now, at the bench's hour, as the scheduler would: what
	the simulation asks at the moment the week reaches (reminders every quarter of an
	hour, the daily rounds of subscriptions, instalments and payment reminders)."""
	verifica()
	if metodo not in lavori_programmati():
		frappe.throw(_("{0} is not a scheduled job").format(metodo))
	from frappe.utils import now_datetime

	inizio = now_datetime()
	frappe.set_user("Administrator")
	frappe.get_attr(metodo)()
	frappe.db.commit()
	return {"method": metodo, "at": str(inizio), "seconds": (now_datetime() - inizio).total_seconds()}
