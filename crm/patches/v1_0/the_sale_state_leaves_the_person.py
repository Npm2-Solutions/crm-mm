# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The person stops carrying a stage of their own (doc 26).

The sale has one scale of states and it lives on the deal. What the person used
to carry -- `status`, and the lost reason that went with it -- is written onto
them as a comment before it stops being shown, because somebody chose those
values one by one and they are not ours to drop in silence.

**No deals are created.** Decided deliberately: the pipeline restarts empty and
fills from here on, rather than being born full of history of uncertain
provenance. The price, known and accepted: the Monday after the release, nobody
finds in the board what they were working on -- it is in the comment on the
person, and reopening it is one click on "New Deal".

The field itself is left in the table. It stops being shown and stops being
written, but a saved view that names it does not explode, and a change of mind
does not need a restore.

Automations triggered by `Lead Status Changed` are disabled rather than left to
stop firing quietly: a trigger that no longer exists would make them look alive
while doing nothing, which is the worst of the two.
"""

import frappe
from frappe import _

CLOSED_BY_HAND = ("Unqualified", "Junk")


def execute():
	remember_what_the_person_carried()
	retire_the_status_automations()


def remember_what_the_person_carried() -> None:
	people = frappe.get_all(
		"CRM Lead",
		filters={"status": ["is", "set"]},
		fields=["name", "status", "lost_reason", "lost_notes"],
	)
	for person in people:
		try:
			lines = [_("Status: {0}").format(person.status)]
			if person.lost_reason:
				lines.append(_("Lost reason: {0}").format(person.lost_reason))
			if person.lost_notes:
				lines.append(_("Notes: {0}").format(person.lost_notes))

			frappe.get_doc("CRM Lead", person.name).add_comment(
				"Comment",
				_("The sale state moved onto the deal. What this person carried until now:")
				+ "<ul>"
				+ "".join(f"<li>{frappe.utils.escape_html(line)}</li>" for line in lines)
				+ "</ul>",
			)
		except Exception:
			# one person's comment failing must not stop the rest of the migration
			frappe.log_error(
				title="Could not record the old status of a person",
				message=f"person: {person.name}\n\n{frappe.get_traceback()}",
			)


TRIGGER = "Lead Status Changed"


def automations_on_the_lead_status() -> list[str]:
	"""Both places a trigger can live.

	Triggers are a child table -- an automation can wait for a new lead *and* for
	a tag *and* for a stage change -- while `CRM Automation.trigger_event` is the
	single field kept for the ones saved before that table existed. Asking only
	the parent field finds the old automations and silently misses every modern
	one, which is the failure this whole function exists to prevent.
	"""
	names = set(
		frappe.get_all(
			"CRM Automation",
			filters={"trigger_event": TRIGGER, "enabled": 1},
			pluck="name",
		)
	)
	names.update(
		frappe.get_all(
			"CRM Automation Trigger",
			filters={"trigger_event": TRIGGER, "parenttype": "CRM Automation"},
			pluck="parent",
		)
	)
	# a child row does not know whether its automation is on
	return sorted(name for name in names if frappe.db.get_value("CRM Automation", name, "enabled"))


def retire_the_status_automations() -> None:
	"""Disable what can no longer fire, and say which ones, by name."""
	automations = automations_on_the_lead_status()
	if not automations:
		return

	for automation in automations:
		frappe.db.set_value("CRM Automation", automation, "enabled", 0, update_modified=False)

	frappe.log_error(
		title="Automations disabled: Lead Status Changed no longer exists",
		message=(
			"The sale state moved onto the deal (doc 26), so a person's status no longer "
			"changes and these automations could never fire again. They have been disabled "
			"rather than left looking alive:\n\n"
			+ "\n".join(f"- {name}" for name in automations)
			+ "\n\nRebuild them on 'Deal Status Changed' if the intent still applies."
		),
	)
