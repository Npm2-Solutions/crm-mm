# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Testing a whole centre before production (e2e/simulazione).

A centre made ready on an empty test site (`prepara.centro`), a clock that moves a
week forward (`tempo`), what the people of the simulation read in their mail
(`api`): the pieces the simulation of a real centre's week stands on, played by
its staff and patients through the real screens.

Never reachable on a site in production: every call refuses unless the site's own
config says ``"dottorcloud_collaudo": 1`` (`attivo`), and only the agency (System
Manager) calls them. The records it makes are no demo's: the simulation goes
through the real paths, guards included.
"""

from __future__ import annotations


def attivo() -> bool:
	"""Whether this site is a test bench for the simulation: its own config says so."""
	import frappe

	return bool(frappe.conf.get("dottorcloud_collaudo"))


def verifica() -> None:
	"""Only on a test bench, only for the agency."""
	import frappe
	from frappe import _

	if not attivo():
		frappe.throw(
			_(
				"This site is not a test bench: set dottorcloud_collaudo to 1 in its site_config.json "
				"to prepare or move it"
			),
			frappe.PermissionError,
		)
	frappe.only_for("System Manager")
