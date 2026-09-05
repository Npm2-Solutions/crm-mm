import frappe
from frappe import _

from crm.telephony import callbacks

DISPOSITIONS = ["Interested", "Not Interested", "No Answer", "Callback", "Voicemail", "Wrong Number"]

SOURCE_RECORDS = "Records"
SOURCE_CALLBACKS = "Callbacks"

UNREACHED = {"No Answer", "Voicemail"}
"""Outcomes where the caller was never actually spoken to.

A queued callback survives these: the promise was to reach the person, and
hearing their answering machine is not reaching them.
"""


def _get_session(name: str):
	doc = frappe.get_doc("CRM Dial Session", name)
	if doc.agent != frappe.session.user and "Sales Manager" not in frappe.get_roles():
		frappe.throw(_("This dial session belongs to another agent"), frappe.PermissionError)
	return doc


def _session_payload(doc) -> dict:
	entries = [
		{
			"idx": e.idx,
			"reference_doctype": e.reference_doctype,
			"reference_name": e.reference_name,
			"display_name": e.display_name,
			"number": e.number,
			"status": e.status,
			"disposition": e.disposition,
			"note": e.note,
			"call_log": e.call_log,
		}
		for e in doc.entries
	]
	done = len([e for e in entries if e["status"] != "Pending"])
	current = next((e for e in entries if e["status"] == "Pending"), None)
	return {
		"name": doc.name,
		"title": doc.title,
		"status": doc.status,
		"source": doc.source or SOURCE_RECORDS,
		"source_doctype": doc.source_doctype,
		"total": len(entries),
		"done": done,
		"current": current,
		"entries": entries,
		"dispositions": DISPOSITIONS,
	}


@frappe.whitelist()
def get_active_session() -> dict | None:
	name = frappe.db.get_value("CRM Dial Session", {"agent": frappe.session.user, "status": "In Progress"})
	return _session_payload(frappe.get_doc("CRM Dial Session", name)) if name else None


@frappe.whitelist()
def get_callback_summary() -> dict:
	"""What the callback queue owes right now — drives the round's badge."""
	return callbacks.pending_summary()


@frappe.whitelist(methods=["POST"])
def create_session(
	doctype: str = "CRM Lead",
	status: str | None = None,
	limit: int = 20,
	title: str | None = None,
	source: str = SOURCE_RECORDS,
	include_upcoming: bool = False,
) -> dict:
	"""Build a call queue, either from records or from the callbacks owed to callers."""
	if source not in (SOURCE_RECORDS, SOURCE_CALLBACKS):
		frappe.throw(_("Invalid source"))
	if frappe.db.exists("CRM Dial Session", {"agent": frappe.session.user, "status": "In Progress"}):
		frappe.throw(_("You already have a dial session in progress. Finish or cancel it first."))

	if source == SOURCE_CALLBACKS:
		return _create_callback_session(limit, title, frappe.utils.sbool(include_upcoming))
	return _create_record_session(doctype, status, limit, title)


def _create_record_session(doctype: str, status: str | None, limit: int, title: str | None) -> dict:
	"""A queue from the newest records (with a phone number) of a status."""
	if doctype not in ("CRM Lead", "CRM Deal"):
		frappe.throw(_("Invalid doctype"))

	filters = {"mobile_no": ["is", "set"]}
	if doctype == "CRM Lead":
		filters["converted"] = 0
	if status:
		filters["status"] = status
	name_field = "lead_name" if doctype == "CRM Lead" else "organization"
	rows = frappe.get_list(
		doctype,
		filters=filters,
		fields=["name", "mobile_no", name_field],
		order_by="modified desc",
		page_length=min(int(limit), 100),
	)
	if not rows:
		frappe.throw(_("No records with a phone number match the selection"))

	doc = frappe.get_doc(
		{
			"doctype": "CRM Dial Session",
			"agent": frappe.session.user,
			"status": "In Progress",
			"source": SOURCE_RECORDS,
			"source_doctype": doctype,
			"title": title or _("{0} · {1} records").format(status or _("All"), len(rows)),
			"entries": [
				{
					"reference_doctype": doctype,
					"reference_name": row.name,
					"display_name": row.get(name_field) or row.name,
					"number": row.mobile_no,
					"status": "Pending",
				}
				for row in rows
			],
		}
	)
	doc.insert()
	return _session_payload(doc)


def _create_callback_session(limit: int, title: str | None, include_upcoming: bool) -> dict:
	"""A round of the callbacks the answering service promised, oldest promise first."""
	rows = callbacks.pending_callbacks(only_due=not include_upcoming, limit=min(int(limit), 100))
	if not rows:
		frappe.throw(
			_("No callbacks are waiting right now.")
			if include_upcoming
			else _("No callbacks are due yet. Include the upcoming ones to work ahead.")
		)

	names = _display_names(rows)
	doc = frappe.get_doc(
		{
			"doctype": "CRM Dial Session",
			"agent": frappe.session.user,
			"status": "In Progress",
			"source": SOURCE_CALLBACKS,
			"title": title or _("Callbacks · {0} waiting").format(len(rows)),
			"entries": [
				{
					# a callback whose number matched nothing has no record to point at,
					# which is fine — the number is what the agent needs
					"reference_doctype": row.get("reference_doctype") or None,
					"reference_name": row.get("reference_docname") or None,
					"display_name": names.get((row.get("reference_doctype"), row.get("reference_docname")))
					or row.get("from"),
					"number": row.get("from"),
					"status": "Pending",
					"call_log": row.name,
				}
				for row in rows
			],
		}
	)
	doc.insert()
	return _session_payload(doc)


def _display_names(rows) -> dict:
	"""Lead/deal titles for the queue — one query per doctype, not one per row."""
	wanted: dict[str, set] = {}
	for row in rows:
		doctype, docname = row.get("reference_doctype"), row.get("reference_docname")
		if doctype in ("CRM Lead", "CRM Deal") and docname:
			wanted.setdefault(doctype, set()).add(docname)

	out = {}
	for doctype, docnames in wanted.items():
		field = "lead_name" if doctype == "CRM Lead" else "organization"
		for row in frappe.get_all(doctype, filters={"name": ["in", list(docnames)]}, fields=["name", field]):
			out[(doctype, row.name)] = row.get(field)
	return out


@frappe.whitelist(methods=["POST"])
def complete_entry(
	session: str, idx: int, disposition: str | None = None, note: str | None = None, skipped: bool = False
) -> dict:
	"""Record the outcome of the current call and move on."""
	if disposition and disposition not in DISPOSITIONS:
		frappe.throw(_("Invalid disposition"))
	doc = _get_session(session)
	entry = next((e for e in doc.entries if e.idx == int(idx)), None)
	if not entry:
		frappe.throw(_("Entry not found"))
	entry.status = "Skipped" if frappe.utils.sbool(skipped) else "Done"
	entry.disposition = disposition or ""
	entry.note = (note or "").strip()

	if entry.status == "Done" and (entry.disposition or entry.note):
		_log_outcome_on_record(entry)

	_advance_callback(entry)

	if all(e.status != "Pending" for e in doc.entries):
		doc.status = "Completed"
	doc.save(ignore_permissions=True)
	return _session_payload(doc)


def _advance_callback(entry) -> None:
	"""Move the queued callback to match the outcome the agent recorded.

	Skipping is deliberately inert: passing someone over in a round doesn't
	discharge the promise made to them, it just defers it to the next one.
	"""
	if not entry.call_log or entry.status == "Skipped":
		return

	try:
		if entry.disposition in UNREACHED:
			callbacks.record_attempt(entry.call_log)
		elif entry.disposition == "Callback":
			callbacks.reschedule_callback(entry.call_log)
		elif entry.disposition == "Wrong Number":
			callbacks.cancel_callback(entry.call_log)
		else:
			callbacks.resolve_callback(entry.call_log)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM Dialer: failed to advance callback")


def _log_outcome_on_record(entry) -> None:
	if not (entry.reference_doctype and entry.reference_name):
		return
	try:
		ref = frappe.get_doc(entry.reference_doctype, entry.reference_name)
		parts = [_("Call outcome: {0}").format(_(entry.disposition or "-"))]
		if entry.note:
			parts.append(frappe.utils.escape_html(entry.note))
		ref.add_comment("Comment", "<br>".join(parts))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM Dialer: failed to log outcome")


@frappe.whitelist(methods=["POST"])
def end_session(session: str, cancel: bool = False) -> dict:
	doc = _get_session(session)
	doc.status = "Cancelled" if frappe.utils.sbool(cancel) else "Completed"
	doc.save(ignore_permissions=True)
	return _session_payload(doc)
