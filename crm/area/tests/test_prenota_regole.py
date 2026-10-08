# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Booking again from the area, without a site."""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.area import prenota_regole as P

PRENOTABILI = {"pulizia": "pulizia-viso", "massaggio": None}


class IlLink(UnitTestCase):
	def test_l_ultimo_servizio_non_annullato(self):
		passati = [
			{"service": "massaggio", "service_name": "Massaggio", "status": "Cancelled"},
			{"service": "pulizia", "service_name": "Pulizia viso", "status": "Completed"},
		]
		self.assertEqual(
			P.link_per_prenotare(passati, PRENOTABILI, "CRM-LEAD-1"),
			{"url": "/prenota/pulizia-viso?persona=CRM-LEAD-1", "service": "Pulizia viso"},
		)

	def test_senza_indirizzo_il_nome_del_servizio(self):
		passati = [{"service": "massaggio", "service_name": "Massaggio", "status": "Completed"}]
		self.assertEqual(
			P.link_per_prenotare(passati, PRENOTABILI, "L")["url"], "/prenota/massaggio?persona=L"
		)

	def test_un_servizio_non_online_o_nessuno_il_catalogo(self):
		catalogo = {"url": "/prenota?persona=L", "service": None}
		self.assertEqual(
			P.link_per_prenotare([{"service": "laser", "status": "Completed"}], PRENOTABILI, "L"), catalogo
		)
		self.assertEqual(P.link_per_prenotare([], PRENOTABILI, "L"), catalogo)


LUCA = {"lead_name": "Luca Bianchi", "email": "", "phone": ""}
MARTA = {"lead_name": "Marta Bianchi", "email": "marta@example.com", "phone": "+39333"}


class ChiPrenota(UnitTestCase):

	def test_per_se_i_propri_dati(self):
		anna = {"lead_name": "Anna", "email": "anna@example.com", "phone": "+39 1"}
		self.assertEqual(
			P.chi_prenota(P.SE_STESSO, anna, {"email": "anna@example.com"}),
			{"full_name": "Anna", "email": "anna@example.com", "phone": "+39 1"},
		)

	def test_per_un_figlio_il_contatto_resta_del_genitore(self):
		dati = P.chi_prenota(P.TUTORE, LUCA, MARTA)
		self.assertEqual(
			dati,
			{
				"full_name": "Marta Bianchi",
				"email": "marta@example.com",
				"phone": "+39333",
				"for_name": "Luca Bianchi",
				"for_relation": "Parent",
			},
		)
		self.assertEqual(
			P.chi_prenota("Follows them", LUCA, MARTA)["for_relation"], "Family member"
		)
