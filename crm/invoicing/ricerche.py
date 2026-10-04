# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a link field finds, in words.

A professional's qualification is stored by its code («societa_servizi»), and a
link's search showed the code under each name. The search for professionals gives
the qualification's name instead («Società di servizi»), and finds one by it too.
"""

from __future__ import annotations

import frappe
from frappe import _

PROFESSIONISTA = "CRM Service Provider"
QUALIFICA = "CRM Professional Qualification"


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def professionisti(
	doctype: str, txt: str, searchfield: str, start: int, page_len: int, filters: dict | list | None
):
	"""Who performs a service: the name, and the qualification in its words."""
	nomi = dict(frappe.get_all(QUALIFICA, fields=["name", "qualification_name"], as_list=True))
	altri = None
	if txt:
		testo = txt.casefold()
		codici = [codice for codice, nome in nomi.items() if testo in (nome or "").casefold()]
		altri = [["provider_name", "like", f"%{txt}%"], ["qualification", "like", f"%{txt}%"]]
		if codici:
			altri.append(["qualification", "in", codici])
	righe = frappe.get_list(
		PROFESSIONISTA,
		filters=filters or None,
		or_filters=altri,
		fields=["name", "qualification"],
		order_by="provider_name asc",
		limit_start=start,
		limit_page_length=page_len,
	)
	return [(riga.name, _(nomi.get(riga.qualification) or "")) for riga in righe]
