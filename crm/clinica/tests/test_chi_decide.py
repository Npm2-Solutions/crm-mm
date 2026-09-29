# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Who signs and decides for a patient, and the minor who needs somebody.

The links between people are the CRM's (`crm.persone`); what the clinic makes of
them - a minor with nobody to decide for them - is the clinic's, and tested here:
the CRM's own tests do not import the clinic (`test_confine`).
"""

import frappe

from crm.clinica import paziente
from crm.persone import legami

# the module, not the class: a TestCase imported here would run here too
from crm.tests import test_billing_profile as profili


def legame(figlio, genitore, relazione=legami.GENITORE, **azioni):
	return frappe.get_doc(
		{
			"doctype": "CRM Related Person",
			"person": figlio,
			"related_person": genitore,
			"relation": relazione,
			**azioni,
		}
	).insert(ignore_permissions=True)


class IlPazienteMinorenne(profili.ProfileBase):
	def test_minorenne_senza_chi_decide_lo_si_dice(self):
		giulia = self.persona("Giulia", "Rossi")
		self.profilo(giulia.name, fiscal_code=profili.CF_GIULIA)
		stato = paziente._stato(giulia.name)
		self.assertTrue(stato["minor"])
		self.assertEqual(stato["representatives"], [])
		legame(giulia.name, self.mario.name, represents=1)
		self.assertEqual(
			[r["name"] for r in paziente._stato(giulia.name)["representatives"]], [self.mario.name]
		)

	def test_senza_codice_fiscale_non_si_sa(self):
		self.assertIsNone(paziente._stato(self.mario.name)["minor"])
