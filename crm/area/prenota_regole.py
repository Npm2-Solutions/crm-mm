# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Booking again from the client area, without a site.

The link goes to the booking page on the service of the person's last appointment
that was not cancelled, when that service is still booked online, else to the
page's catalogue; it carries only who is in the area for (``persona``), never a
name, an email or a number: the page asks the session who that is (`chi_prenota`).
"""

from __future__ import annotations

from urllib.parse import quote, urlencode

#: who is in the area, as `crm.area.accesso` writes it
SE_STESSO = "Self"
TUTORE = "Parent or guardian"


def link_per_prenotare(
	passati: list[dict], prenotabili: dict[str, str], persona: str, base: str = "/prenota"
) -> dict:
	"""``passati``: ``{"service", "service_name", "status"}`` the newest first;
	``prenotabili``: the services booked online, by name, with their address's
	slug. ``{"url", "service"}``: ``service`` the name of the one booked again, or
	``None`` for the catalogue."""
	ultimo = next((voce for voce in passati if voce.get("status") != "Cancelled"), None)
	query = "?" + urlencode({"persona": persona})
	servizio = ultimo and ultimo.get("service")
	if servizio and servizio in prenotabili:
		slug = prenotabili[servizio] or servizio
		return {"url": f"{base}/{quote(slug, safe='')}{query}", "service": ultimo.get("service_name")}
	return {"url": base + query, "service": None}


def chi_prenota(relazione: str, persona: dict, chi_entra: dict) -> dict:
	"""What the booking page writes in for somebody in the area: ``persona`` is
	whose area it is (``lead_name``, ``email``, ``phone``), ``chi_entra`` who is in
	it (the same fields). Their own area: their own details. Somebody else's (a
	child's, a parent's they follow): the booking is for that person, the contact
	details stay whoever books, as the page asks."""
	if relazione == SE_STESSO:
		return {
			"full_name": persona.get("lead_name") or chi_entra.get("lead_name") or "",
			"email": persona.get("email") or chi_entra.get("email") or "",
			"phone": persona.get("phone") or chi_entra.get("phone") or "",
		}
	return {
		"full_name": chi_entra.get("lead_name") or "",
		"email": chi_entra.get("email") or "",
		"phone": chi_entra.get("phone") or "",
		"for_name": persona.get("lead_name") or "",
		"for_relation": "Parent" if relazione == TUTORE else "Family member",
	}
