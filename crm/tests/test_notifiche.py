# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# Sentences that name where something happened: a person by their name, a deal as
# "the deal" - never a doctype's English name glued into another language - and the
# words the code reads back, which are not the sentence's.

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.todo import get_notification_text
from crm.booking_platforms.sync import _dalla_piattaforma
from crm.integrations.whatsapp.templates import check_placeholders


def _assegnazione(doctype):
	return frappe._dict(reference_type=doctype, reference_name="CRM-0001")


class TestNotifiche(FrappeTestCase):
	def test_a_person_is_named_by_their_name(self):
		testo = get_notification_text(
			"Anna Bianchi", _assegnazione("CRM Lead"), frappe._dict(lead_name="Giulia Rossi")
		)
		self.assertIn("Anna Bianchi", testo)
		self.assertIn("Giulia Rossi", testo)
		self.assertNotRegex(testo, r"\blead\b")
		self.assertNotIn("CRM-0001", testo)

	def test_a_deal_is_the_deal_with_its_company(self):
		testo = get_notification_text(
			"Anna Bianchi",
			_assegnazione("CRM Deal"),
			frappe._dict(organization="Studio Verdi", lead_name="Giulia Rossi"),
			is_cancelled=True,
		)
		self.assertIn("Studio Verdi", testo)
		self.assertIn("removed your assignment on the deal", testo)
		self.assertNotIn("CRM Deal", testo)

	def test_names_are_escaped(self):
		testo = get_notification_text(
			"<b>Anna</b>", _assegnazione("CRM Lead"), frappe._dict(lead_name="<img src=x>")
		)
		self.assertNotIn("<img", testo)
		self.assertNotIn("<b>Anna", testo)

	def test_a_platform_cancellation_is_recognised_whatever_the_language(self):
		self.assertTrue(_dalla_piattaforma("Cancelled on MioDottore", "MioDottore"))
		# synced in the site's language, read back by a job in English
		italiano = frappe._("Cancelled on {0}", lang="it").format("MioDottore")
		with patch.object(frappe.db, "get_single_value", return_value="it"):
			self.assertTrue(_dalla_piattaforma(italiano, "MioDottore"))
		self.assertFalse(_dalla_piattaforma("Cancelled online by the client", "MioDottore"))
		self.assertFalse(_dalla_piattaforma("", "MioDottore"))

	def test_the_placeholders_message_shows_the_placeholder(self):
		with self.assertRaises(frappe.ValidationError) as errore:
			check_placeholders({"template": "Ciao {{1}}, il {{3}}"})
		self.assertIn("{{1}}", str(errore.exception))
		self.assertIn("{{3}}", str(errore.exception))
