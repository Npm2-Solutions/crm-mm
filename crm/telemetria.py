# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""DottorCloud sends nothing about its use to anybody.

The framework counts what a site's people do and sends it to Frappe's servers
(pulse) wherever the site holds the key and System Settings leave it on, as Frappe
Cloud's do: a medical centre's software tells nobody what happens in it. Switched
off at install and at every migrate; in the browser frappe-ui's telemetry plugin
is not installed (`frontend/src/main.js`), so it neither asks for its settings nor
loads pulse's script.
"""

import frappe


def spegni():
	"""System Settings' «Enable telemetry», off: saved only when it is on."""
	if frappe.db.get_single_value("System Settings", "enable_telemetry"):
		frappe.db.set_single_value("System Settings", "enable_telemetry", 0)
