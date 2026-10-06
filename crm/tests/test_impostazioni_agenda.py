# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# See license.txt

"""The agenda's settings say what the agenda does
(`crm.patches.v1_0.the_agenda_settings_say_what_it_does`): a centre saved before
the grid's step existed read «Choose…» over a grid that moved by 15 minutes."""

import frappe
from frappe.tests import IntegrationTestCase

from crm.patches.v1_0 import the_agenda_settings_say_what_it_does as patch

IMPOSTAZIONI = "FCRM Settings"


def letti():
	return tuple(
		frappe.db.get_single_value(IMPOSTAZIONI, campo)
		for campo in ("calendar_grid_step", "default_calendar_view")
	)


class LeImpostazioniDellAgenda(IntegrationTestCase):
	def test_dove_niente_e_scritto_vale_il_predefinito(self):
		frappe.db.set_single_value(IMPOSTAZIONI, {"calendar_grid_step": "", "default_calendar_view": ""})
		patch.execute()
		self.assertEqual(letti(), ("15", "Daily"))

	def test_quello_che_il_centro_ha_scelto_resta(self):
		frappe.db.set_single_value(
			IMPOSTAZIONI, {"calendar_grid_step": "30", "default_calendar_view": "Monthly"}
		)
		patch.execute()
		self.assertEqual(letti(), ("30", "Monthly"))
