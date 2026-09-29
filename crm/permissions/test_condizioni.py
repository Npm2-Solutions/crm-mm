# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The guided conditions, written in Python by the server, proved without a site.

What the screen builds must come out as the browser wrote it; what it cannot build
must not come out at all.
"""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the conversion is pure
	from unittest import TestCase as UnitTestCase

from crm.permissions.condizioni import CondizioneNonValida, in_python

CAMPI = {"status", "source", "email", "lead_name", "annual_revenue", "converted", "no_of_employees"}


def valuta(espressione: str, **campi) -> bool:
	"""The expression evaluated as a rule would, with nothing else in reach."""
	return bool(eval(espressione, {"__builtins__": {}}, campi))


class ComeLoSchermo(UnitTestCase):
	"""The same Python the browser wrote, for everything the screen builds."""

	def test_one_condition(self):
		self.assertEqual(in_python([["status", "==", "Open"]], CAMPI), 'status == "Open"')
		self.assertEqual(in_python([["status", "equals", "Open"]], CAMPI), 'status == "Open"')
		self.assertEqual(in_python([["status", "not equals", "Lost"]], CAMPI), 'status != "Lost"')

	def test_joined_and_grouped(self):
		condizioni = [
			[["status", "==", "Open"], "or", ["status", "==", "New"]],
			"and",
			["source", "==", "Web"],
		]
		self.assertEqual(
			in_python(condizioni, CAMPI), '(status == "Open" or status == "New") and source == "Web"'
		)

	def test_a_list_of_values(self):
		self.assertEqual(
			in_python([["source", "in", "Web, Ads"]], CAMPI), '(source and source in ["Web", "Ads"])'
		)
		self.assertEqual(
			in_python([["source", "not in", ["Web", "Ads"]]], CAMPI),
			'(source and source not in ["Web", "Ads"])',
		)

	def test_checks_and_empty_fields(self):
		self.assertEqual(in_python([["converted", "==", "Yes"]], CAMPI), "converted")
		self.assertEqual(in_python([["converted", "!=", "yes"]], CAMPI), "not converted")
		self.assertEqual(in_python([["converted", "==", "No"]], CAMPI), "not converted")
		self.assertEqual(in_python([["email", "is", "set"]], CAMPI), "email")
		self.assertEqual(in_python([["email", "is", "not set"]], CAMPI), "not email")
		self.assertEqual(in_python([["email", "is not", "set"]], CAMPI), "not email")
		self.assertEqual(in_python([["email", "==", None]], CAMPI), "not email")

	def test_text_and_ranges(self):
		self.assertEqual(
			in_python([["lead_name", "like", "Rossi"]], CAMPI), '(lead_name and "Rossi" in lead_name)'
		)
		self.assertEqual(
			in_python([["lead_name", "not like", "Test"]], CAMPI),
			'(lead_name and "Test" not in lead_name)',
		)
		self.assertEqual(
			in_python([["annual_revenue", "between", "10, 20"]], CAMPI),
			'(annual_revenue >= "10" and annual_revenue <= "20")',
		)

	def test_numbers(self):
		self.assertEqual(in_python([["annual_revenue", ">", 100]], CAMPI), "annual_revenue > 100")
		self.assertEqual(in_python([["annual_revenue", "<=", 2.5]], CAMPI), "annual_revenue <= 2.5")

	def test_the_sla_reaches_the_document_through_doc(self):
		self.assertEqual(in_python([["status", "==", "Open"]], CAMPI, prefisso="doc"), 'doc.status == "Open"')

	def test_nothing_is_nothing(self):
		self.assertEqual(in_python([], CAMPI), "")
		self.assertEqual(in_python(None, CAMPI), "")


class MegliodelloSchermo(UnitTestCase):
	"""Where the browser wrote Python that does not run, or runs what it should not."""

	def test_a_boolean_is_pythons(self):
		# the browser wrote `true`, which is not a name in Python
		self.assertEqual(in_python([["converted", "==", True]], CAMPI), "converted == True")

	def test_a_quote_stays_inside_the_value(self):
		espressione = in_python([["lead_name", "==", 'Rossi" or True or "']], CAMPI)
		self.assertFalse(valuta(espressione, lead_name="Bianchi"))
		self.assertTrue(valuta(espressione, lead_name='Rossi" or True or "'))

	def test_quotes_stay_inside_lists_and_ranges_too(self):
		for condizione in (
			["source", "in", ['Web"] or True or ["']],
			["lead_name", "like", '" or True or "'],
			["annual_revenue", "between", '1" or True or ", 2'],
		):
			espressione = in_python([condizione], CAMPI)
			self.assertFalse(
				valuta(espressione, source="Ads", lead_name="Bianchi", annual_revenue="5"), espressione
			)


class NonLoCostruisce(UnitTestCase):
	"""What the screen cannot build is refused: that is where Python would come in."""

	def assert_refused(self, condizioni, **kwargs):
		with self.assertRaises(CondizioneNonValida, msg=repr(condizioni)):
			in_python(condizioni, CAMPI, **kwargs)

	def test_only_and_or_between_conditions(self):
		self.assert_refused([["status", "==", "Open"], "or __import__('os')", ["status", "==", "New"]])
		self.assert_refused([["status", "==", "Open"], ["status", "==", "New"]])
		self.assert_refused([["status", "==", "Open"], "and"])

	def test_only_fields_of_the_document(self):
		self.assert_refused([["__import__('os').system('x')", "==", "1"]])
		self.assert_refused([["password", "==", "x"]])
		self.assert_refused([["status.__class__", "==", "x"]])

	def test_only_the_screens_operators(self):
		self.assert_refused([["status", "== 1 or 1 ==", "x"]])
		self.assert_refused([["status", "is", "Open"]])
		self.assert_refused([["annual_revenue", "between", "10"]])

	def test_only_plain_values(self):
		self.assert_refused([["status", "==", {"a": 1}]])
		self.assert_refused([["status", "=="]])
		self.assert_refused("status == 'Open'")

	def test_the_prefix_is_a_name(self):
		self.assert_refused([["status", "==", "Open"]], prefisso="__import__('os')")
