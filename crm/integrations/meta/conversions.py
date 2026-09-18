# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Telling Meta what became of the leads it sent.

Everything else in this integration reads. This writes back, and it is the only
part that makes the ads *better* rather than better understood: with the funnel
stages of each lead returned to it, Meta can optimise a lead-ads campaign for
the people who end up buying instead of the people who end up submitting. That
is the Conversion Leads performance goal, and it is the same mechanism the big
CRMs sell as a feature.

We are unusually well placed for it. Meta asks that each event carry its own
lead id — `user_data.lead_id`, the 15-17 digit id of the submission — and we
store exactly that on every lead (`facebook_lead_id`). No email hashing, no
click ids, no matching to guess at.

Three things Meta insists on, and we obey:

- **send the raw lead stage too**, not only the good news. Without the first
  event the model cannot tell a reported funnel from a silent one.
- **send stages as they happen**, at least daily.
- **cover at least 60%** of the leads. That is why every send is recorded: the
  coverage can only be read off what was actually sent.

The events say `action_source: "system_generated"`, which is the value the CRM
integration requires — not the one the web pixel uses.
"""

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from crm.integrations.meta.client import GRAPH_VERSION, graph_post_body

# The first event of every lead. Meta needs it to know the lead was received and
# processed at all; without it the later stages cannot be put in proportion.
RAW_LEAD = "Raw Lead"

# what we call ourselves in the payload, for Meta's own diagnostics
LEAD_EVENT_SOURCE = "Frappe CRM"

MAX_ATTEMPTS = 5
BATCH = 200


def settings():
	return frappe.get_cached_doc("CRM Meta Settings")


def enabled() -> bool:
	config = settings()
	return bool(config.conversions_enabled and config.conversions_dataset_id)


# --- filling the queue ------------------------------------------------------


def queue(lead: str, event_name: str, when=None, facebook_lead_id: str | None = None) -> str | None:
	"""Remember that this stage happened, once.

	The same stage twice is noise, not information — a status flipped back and
	forth by hand would otherwise become a second "Qualified" — so a stage
	already queued or sent for this lead is not queued again.
	"""
	if not enabled() or not lead or not event_name:
		return None

	lead_id = facebook_lead_id or frappe.db.get_value("CRM Lead", lead, "facebook_lead_id")
	if not lead_id:
		# not a lead Meta gave us: there is nothing it could match this to
		return None
	if frappe.db.exists("Meta Conversion Event", {"lead": lead, "event_name": event_name}):
		return None

	event = frappe.get_doc(
		{
			"doctype": "Meta Conversion Event",
			"lead": lead,
			"facebook_lead_id": lead_id,
			"event_name": event_name,
			"event_time": get_datetime(when) if when else now_datetime(),
			"state": "Pending",
		}
	).insert(ignore_permissions=True)
	return event.name


def on_lead_created(doc, method=None) -> None:
	"""The raw lead stage, the moment the lead lands."""
	if doc.get("facebook_lead_id"):
		queue(doc.name, RAW_LEAD, when=doc.get("creation"), facebook_lead_id=doc.facebook_lead_id)


def on_lead_updated(doc, method=None) -> None:
	if doc.get("facebook_lead_id") and doc.has_value_changed("status") and doc.get("status"):
		queue(doc.name, doc.status, facebook_lead_id=doc.facebook_lead_id)


def on_deal_updated(doc, method=None) -> None:
	"""A deal's stages belong to the lead it came from.

	The lead id is what Meta matches on, so a deal with no lead behind it — one
	typed in by hand — has nothing to report, and reporting it against the wrong
	lead would be worse than reporting nothing.
	"""
	if not doc.get("lead") or not doc.has_value_changed("status") or not doc.get("status"):
		return
	lead_id = frappe.db.get_value("CRM Lead", doc.lead, "facebook_lead_id")
	if lead_id:
		queue(doc.lead, doc.status, facebook_lead_id=lead_id)


# --- emptying it ------------------------------------------------------------


def send_pending(limit: int = BATCH) -> dict:
	"""Hand Meta everything still waiting, in one call.

	One call for many events on purpose: this runs every hour, and a lead's whole
	history can be several stages. A failure is the batch's, not one event's, so
	every row in it is retried — Meta de-duplicates on the lead id and the event
	name, so a retry cannot inflate anybody's funnel.
	"""
	if not enabled():
		return {"sent": 0, "skipped": "not enabled"}

	rows = frappe.get_all(
		"Meta Conversion Event",
		filters={"state": "Pending"},
		fields=["name", "facebook_lead_id", "event_name", "event_time", "attempts"],
		order_by="creation asc",
		limit=cint(limit) or BATCH,
	)
	if not rows:
		return {"sent": 0}

	config = settings()
	token = config.get_password("user_access_token", raise_exception=False)
	if not token:
		_remember_error(_("Facebook is not connected, so no lead stage can be sent."))
		return {"sent": 0, "error": "no token"}

	# the payload goes in the body: two hundred events do not fit in a URL
	payload = {"data": frappe.as_json([_event(row) for row in rows])}
	if config.conversions_test_code:
		payload["test_event_code"] = config.conversions_test_code

	try:
		answer = graph_post_body(f"{config.conversions_dataset_id}/events", token, payload)
	except Exception as exc:
		_failed(rows, str(exc))
		_remember_error(str(exc))
		return {"sent": 0, "error": str(exc)}

	received = cint(answer.get("events_received"))
	_sent(rows, f"events_received={received}")
	_remember_error("")
	return {"sent": len(rows), "events_received": received}


def _event(row: dict) -> dict:
	"""One event, in the shape the CRM integration requires.

	`action_source` is `system_generated` here — the web, app and offline flavours
	of this API use different values, and the wrong one is silently ignored.
	"""
	return {
		"event_name": row["event_name"],
		"event_time": int(get_datetime(row["event_time"]).timestamp()),
		"action_source": "system_generated",
		"user_data": {"lead_id": int(row["facebook_lead_id"])}
		if str(row["facebook_lead_id"]).isdigit()
		else {"lead_id": row["facebook_lead_id"]},
		"custom_data": {"lead_event_source": LEAD_EVENT_SOURCE, "event_source": "crm"},
	}


def _sent(rows: list[dict], response: str) -> None:
	for row in rows:
		frappe.db.set_value(
			"Meta Conversion Event",
			row["name"],
			{
				"state": "Sent",
				"sent_on": now_datetime(),
				"attempts": cint(row["attempts"]) + 1,
				"response": response,
			},
			update_modified=False,
		)


def _failed(rows: list[dict], response: str) -> None:
	"""Retry, but not forever: a payload Meta will never accept would otherwise
	block the queue behind it for good."""
	for row in rows:
		attempts = cint(row["attempts"]) + 1
		frappe.db.set_value(
			"Meta Conversion Event",
			row["name"],
			{
				"state": "Failed" if attempts >= MAX_ATTEMPTS else "Pending",
				"attempts": attempts,
				"response": response[:500],
			},
			update_modified=False,
		)


def _remember_error(message: str) -> None:
	frappe.db.set_single_value("CRM Meta Settings", "conversions_last_error", message[:500])


def flush() -> None:
	"""Hourly job. Nothing to send is the normal case and costs one query."""
	if enabled():
		send_pending()


# --- how are we doing? ------------------------------------------------------


def coverage(days: int = 30) -> dict:
	"""The share of Meta's leads whose story we actually told back.

	Meta grades the integration on this — below 60% it will not trust the data
	enough to optimise on it — so it belongs on the screen, not in a log.
	"""
	total = frappe.db.count(
		"CRM Lead",
		{
			"facebook_lead_id": ["!=", ""],
			"creation": [">", frappe.utils.add_days(frappe.utils.nowdate(), -cint(days))],
		},
	)
	reported = frappe.db.sql(
		"""
		select count(distinct e.lead)
		from `tabMeta Conversion Event` e
		inner join `tabCRM Lead` l on l.name = e.lead
		where e.state = 'Sent'
			and ifnull(l.facebook_lead_id, '') != ''
			and date(l.creation) > date_sub(curdate(), interval %(days)s day)
		""",
		{"days": cint(days)},
	)[0][0]
	pending = frappe.db.count("Meta Conversion Event", {"state": "Pending"})
	failed = frappe.db.count("Meta Conversion Event", {"state": "Failed"})
	stages = frappe.db.sql(
		"""
		select event_name, count(*) as events
		from `tabMeta Conversion Event`
		where state = 'Sent'
		group by event_name
		order by events desc
		""",
		as_dict=True,
	)
	return {
		"days": cint(days),
		"leads": total,
		"reported": cint(reported),
		"percent": round(100.0 * cint(reported) / total, 1) if total else None,
		"pending": pending,
		"failed": failed,
		"stages": stages,
		"enough": bool(total and (100.0 * cint(reported) / total) >= 60),
		"graph_version": GRAPH_VERSION,
	}
