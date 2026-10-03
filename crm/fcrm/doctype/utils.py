# Modifications copyright (c) 2026, NPM2 Solutions Srl

"""The deal's lost reason in its side panel.

The section used to be added to the side panel shared by every deal when one
deal was marked lost, and taken away when another moved on: whether a deal
showed it depended on the last deal that changed stage, and every change of
stage rewrote the layout. Now the layout keeps the section once, after the
contacts, and a deal's page shows it only while that deal is lost.
"""

LOST_REASON_SECTION = "lost_reason_section"


def lost_reason_section() -> dict:
	return {
		"label": "Lost Reason",
		"name": LOST_REASON_SECTION,
		"opened": True,
		"columns": [{"name": "lost_reason_column", "fields": ["lost_reason", "lost_notes"]}],
	}


def with_lost_reason_section(sections: list) -> list:
	"""The side panel's sections with the lost reason once: after the contacts,
	else first. Pure: the same list back when it is there already."""
	if any(section.get("name") == LOST_REASON_SECTION for section in sections):
		return sections
	if sections and sections[0].get("name") == "contacts_section":
		return [*sections[:1], lost_reason_section(), *sections[1:]]
	return [lost_reason_section(), *sections]
