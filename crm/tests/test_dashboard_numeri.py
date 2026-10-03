# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who reads which numbers on the dashboard (doc 30, "Dashboard e numeri").

Marketing's crawl on a phone opened the Overview on today's appointments, the
missed calls and the people waiting for an answer, and Accounting had no
invoicing numbers at all: the dashboard asked only whether a widget was for
managers. Now each widget asks for the capability that reads its numbers.
"""

import json

import frappe

from crm.api import dashboard as api
from crm.dashboard import features, registry, store
from crm.tests.test_livelli_facoltativi import (
	AMMINISTRAZIONE,
	MANAGER,
	MARKETING,
	OPERATORE,
	SEGRETERIA,
	FacoltativiTestCase,
)


class TestWhoReadsWhichNumbers(FacoltativiTestCase):
	def setUp(self):
		super().setUp()
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "marketing", "status": "Active"}])
		piano.save()
		features.forget()

	def legge(self, user: str, widget_id: str) -> bool:
		self.come(user)
		return store.reads(registry.get(widget_id))

	def offerti(self, user: str) -> set[str]:
		self.come(user)
		return {widget["id"] for widget in api.get_widget_catalog()["widgets"]}

	def test_every_category_says_who_reads_it(self):
		self.assertEqual(set(registry.READERS), set(registry.CATEGORIES))

	def test_marketing_reads_no_agenda_and_no_calls(self):
		for widget_id in ("appointments_today", "calls_missed", "conversations_waiting"):
			self.assertFalse(self.legge(MARKETING, widget_id), widget_id)
		offerti = self.offerti(MARKETING)
		self.assertNotIn("appointments_today", offerti)
		self.assertNotIn("invoiced_revenue", offerti)

	def test_marketing_reads_its_own_numbers(self):
		for widget_id in ("website_visitors", "meta_spend", "social_published", "won_deals"):
			self.assertTrue(self.legge(MARKETING, widget_id), widget_id)

	def test_accounting_reads_the_invoices_not_the_desk(self):
		self.assertTrue(self.legge(AMMINISTRAZIONE, "invoiced_revenue"))
		self.assertTrue(self.legge(AMMINISTRAZIONE, "appointments_revenue"))
		self.assertFalse(self.legge(AMMINISTRAZIONE, "appointments_today"))
		self.assertIn("invoicing", self.template_offerti(AMMINISTRAZIONE))

	def test_the_front_desk_reads_the_day_not_the_revenue(self):
		self.assertTrue(self.legge(SEGRETERIA, "appointments_today"))
		self.assertFalse(self.legge(SEGRETERIA, "invoiced_revenue"))
		self.assertFalse(self.legge(SEGRETERIA, "appointments_revenue"))
		self.assertNotIn("invoicing", self.template_offerti(SEGRETERIA))

	def test_one_s_own_numbers_are_not_the_centre_s(self):
		# a practitioner reads their own revenue: never the whole centre's
		self.assertTrue(self.legge(OPERATORE, "appointments_revenue"))
		self.assertFalse(self.legge(OPERATORE, "invoiced_revenue"))
		self.assertTrue(store.own_numbers_only(registry.get("appointments_today")))

	def test_the_manager_reads_them_all(self):
		for widget_id in ("appointments_today", "invoiced_revenue", "website_visitors"):
			self.assertTrue(self.legge(MANAGER, widget_id), widget_id)

	def test_a_widget_asked_for_anyway_says_why_not(self):
		self.come(MARKETING)
		answer = api.get_widgets_data(json.dumps([{"i": "a", "name": "appointments_today"}]))
		self.assertEqual(answer["a"]["unavailable"]["reason"], "level")

	def test_a_shared_dashboard_with_nothing_to_read_is_not_listed(self):
		store.ensure_defaults()
		self.come(SEGRETERIA)
		self.assertNotIn("invoicing", self.dashboards())
		self.come(AMMINISTRAZIONE)
		self.assertIn("invoicing", self.dashboards())

	def test_a_dashboard_is_for_whoever_reads_what_it_is_about(self):
		# the Agenda holds the new clients, which Marketing reads: it is still the agenda's
		store.ensure_defaults()
		self.come(MARKETING)
		self.assertNotIn("agenda", self.dashboards())
		self.assertIn("marketing", self.dashboards())
		self.assertNotIn("agenda", self.template_offerti(MARKETING))

	def test_what_is_left_of_a_dashboard_is_what_one_reads(self):
		store.ensure_defaults()
		self.come(MARKETING)
		layout = store.load(store.MANAGER_DASHBOARD)["layout"]
		nomi = {item["name"] for item in layout}
		self.assertNotIn("appointments_today", nomi)
		self.assertFalse([item for item in layout if "unavailable" in item])

	def template_offerti(self, user: str) -> set[str]:
		self.come(user)
		return {template["id"] for template in api.get_widget_catalog()["templates"]}

	def dashboards(self) -> list[str]:
		return [row["template"] for row in api.get_dashboards()["dashboards"] if not row["private"]]
