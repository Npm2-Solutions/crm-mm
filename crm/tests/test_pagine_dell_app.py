# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The SPA's shells are served before the framework's cached lists of web forms
and dynamic Web Pages (`crm.pagine_dell_app`): one of them answering None while
its cache fills again made /crm/accoglienza a 500 now and then."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.website.path_resolver import PathResolver
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from crm.pagine_dell_app import PaginaDellApp


class TestPagineDellApp(IntegrationTestCase):
	def setUp(self):
		self.richiesta = getattr(frappe.local, "request", None)

	def tearDown(self):
		frappe.local.request = self.richiesta

	def _risolvi(self, percorso: str):
		frappe.set_user("Administrator")
		frappe.local.request = Request(EnvironBuilder(path=f"/{percorso}").get_environ())
		return PathResolver(percorso).resolve()

	def test_i_gusci_sono_dell_app(self):
		for percorso, gusci in (
			("crm/accoglienza", "crm"),
			("crm/organizations/view/list", "crm"),
			("area/home", "area"),
		):
			endpoint, pagina = self._risolvi(percorso)
			self.assertEqual(endpoint, gusci)
			self.assertIsInstance(pagina, PaginaDellApp)

	def test_una_lista_della_cache_che_risponde_none_non_li_ferma(self):
		# what `redis_cache` answers to the second of two requests while it fills
		with (
			patch("frappe.website.doctype.web_page.web_page.get_dynamic_web_pages", return_value=None),
			patch("frappe.website.doctype.web_form.web_form.get_published_web_forms", return_value=None),
		):
			endpoint, pagina = self._risolvi("crm/accoglienza")
		self.assertEqual(endpoint, "crm")
		self.assertIsInstance(pagina, PaginaDellApp)

	def test_le_altre_pagine_restano_del_framework(self):
		_endpoint, pagina = self._risolvi("prenota")
		self.assertNotIsInstance(pagina, PaginaDellApp)
