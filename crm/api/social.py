import json

import frappe
from frappe import _

from crm.integrations.meta.redact import redact

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _is_manager() -> bool:
	return bool(MANAGER_ROLES & set(frappe.get_roles()))


def _check_manager():
	if not _is_manager():
		frappe.throw(_("Only sales managers can do this"), frappe.PermissionError)


@frappe.whitelist()
def get_accounts() -> list[dict]:
	"""The profiles the composer offers: a name and a platform is all it shows."""
	return frappe.get_list(
		"CRM Social Account",
		filters={"enabled": 1},
		fields=["name", "account_name", "platform"],
		order_by="platform asc",
	)


@frappe.whitelist()
def get_posts(start: str, end: str) -> list[dict]:
	"""Posts in a date range (calendar view) plus undated drafts."""
	posts = frappe.get_list(
		"CRM Social Post",
		filters={"scheduled_at": ["between", [start, end]]},
		fields=["name", "status", "scheduled_at", "published_at", "content", "media", "recurrence"],
		order_by="scheduled_at asc",
		page_length=500,
	)
	drafts = frappe.get_list(
		"CRM Social Post",
		filters={"scheduled_at": ["is", "not set"], "status": ["in", ["Draft", "Pending Approval"]]},
		fields=["name", "status", "scheduled_at", "published_at", "content", "media", "recurrence"],
		page_length=100,
	)
	rows = posts + drafts
	targets = frappe.get_all(
		"CRM Social Post Target",
		filters={"parent": ["in", [r.name for r in rows]]},
		fields=["parent", "account", "platform", "status", "error", "override_content"],
	)
	# Why a profile refused the post is Meta's answer, written for whoever runs
	# the connection — and, before it was redacted, it could quote the URL of the
	# call with the page token in it. The author learns that it did not go out;
	# the reason is for a manager, who can do something about it.
	manager = _is_manager()
	by_post: dict[str, list] = {}
	for t in targets:
		if t.error:
			t.error = redact(t.error) if manager else _("Not published. A manager can see why.")
		by_post.setdefault(t.parent, []).append(t)
	for row in rows:
		row["targets"] = by_post.get(row.name, [])
	return rows


@frappe.whitelist(methods=["POST"])
def save_post(post: dict | str, name: str | None = None) -> dict:
	if isinstance(post, str):
		post = json.loads(post)

	targets = post.get("targets") or []
	if not targets:
		frappe.throw(_("Select at least one social account"))
	values = {
		"content": (post.get("content") or "").strip(),
		"scheduled_at": post.get("scheduled_at") or None,
		"media": post.get("media") or "",
		"recurrence": post.get("recurrence") or "None",
		"targets": [
			{
				"account": t.get("account"),
				"override_content": t.get("override_content") or "",
				"status": "Pending",
			}
			for t in targets
		],
	}
	if not values["content"]:
		frappe.throw(_("Content is required"))

	requested_status = post.get("status") or "Draft"
	if requested_status in ("Scheduled", "Published") and not _is_manager():
		requested_status = "Pending Approval"
	if requested_status == "Scheduled" and not values["scheduled_at"]:
		frappe.throw(_("Pick a date and time to schedule"))

	if name:
		doc = frappe.get_doc("CRM Social Post", name)
		if doc.status == "Published":
			frappe.throw(_("Published posts cannot be edited"))
		doc.update(values)
	else:
		doc = frappe.get_doc({"doctype": "CRM Social Post", **values})

	doc.status = requested_status
	if requested_status == "Pending Approval":
		doc.requested_by = frappe.session.user
	if requested_status == "Scheduled":
		doc.approved_by = frappe.session.user
	doc.save() if name else doc.insert()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def approve_post(name: str) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Social Post", name)
	if doc.status != "Pending Approval":
		frappe.throw(_("Post is not pending approval"))
	if not doc.scheduled_at:
		frappe.throw(_("Set a schedule date before approving"))
	doc.status = "Scheduled"
	doc.approved_by = frappe.session.user
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def publish_now(name: str) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Social Post", name)
	if doc.status in ("Published",):
		frappe.throw(_("Already published"))
	doc.status = "Scheduled"
	doc.scheduled_at = doc.scheduled_at or frappe.utils.now_datetime()
	doc.approved_by = frappe.session.user
	doc.save()
	from crm.social.publisher import publish_post

	publish_post(doc.name)
	doc.reload()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def cancel_post(name: str) -> dict:
	doc = frappe.get_doc("CRM Social Post", name)
	if doc.status == "Published":
		frappe.throw(_("Already published"))
	if not _is_manager() and doc.owner != frappe.session.user:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc.status = "Cancelled"
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}


# --- Settings-modal administration -----------------------------------------


@frappe.whitelist()
def get_sources() -> list[dict]:
	"""Every source the planner publishes through, how it stands, and its profiles.

	The profiles are not typed in here: each source brings its own. So the
	settings page starts from the sources — connected or not, as whom — and a
	source's connection lives with the integration it belongs to.
	"""
	_check_manager()
	from crm.social.sources import SOURCES

	counts: dict[str, list[int]] = {}
	for row in frappe.get_all("CRM Social Account", fields=["platform", "enabled"]):
		total_enabled = counts.setdefault(row.platform, [0, 0])
		total_enabled[0] += 1
		total_enabled[1] += 1 if row.enabled else 0

	sources = []
	for source in SOURCES:
		sources.append(
			{
				"key": source.key,
				"label": source.label,
				"description": source.description(),
				"platforms": list(source.platforms),
				"settings_page": source.settings_page,
				"profiles": sum(counts.get(p, [0, 0])[0] for p in source.platforms),
				"enabled_profiles": sum(counts.get(p, [0, 0])[1] for p in source.platforms),
				**source.status(),
			}
		)
	return sources


@frappe.whitelist(methods=["POST"])
def sync_profiles() -> dict:
	"""Bring the profiles in line with every connected source.

	Idempotent: a profile is matched by platform and id, so pressing it twice
	changes nothing, and a profile that was switched off stays off.
	"""
	_check_manager()
	from crm.social.sources import SOURCES

	totals = {"created": 0, "updated": 0, "removed": 0, "refreshing": False}
	for source in SOURCES:
		if not source.status().get("connected"):
			continue
		result = source.sync()
		for key in ("created", "updated", "removed"):
			totals[key] += result.get(key) or 0
		totals["refreshing"] = totals["refreshing"] or bool(result.get("refreshing"))
	totals["accounts"] = list_accounts_admin()
	return totals


@frappe.whitelist()
def list_accounts_admin() -> list[dict]:
	_check_manager()
	from crm.social.sources import SOURCES

	source_of = {platform: source.key for source in SOURCES for platform in source.platforms}
	accounts = frappe.get_all(
		"CRM Social Account",
		fields=["name", "account_name", "platform", "enabled"],
		order_by="platform asc, account_name asc",
	)
	for account in accounts:
		account["source"] = source_of.get(account.platform, "")
	return accounts


@frappe.whitelist(methods=["POST"])
def set_account_enabled(name: str, enabled: bool) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Social Account", name)
	doc.enabled = 1 if frappe.utils.sbool(enabled) else 0
	doc.save()
	return {"name": doc.name, "enabled": doc.enabled}
