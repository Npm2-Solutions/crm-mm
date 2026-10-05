# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The language of DottorCloud's own words on a site, without a site."""

from __future__ import annotations

from unittest.mock import patch

import frappe

try:
	from frappe.tests import IntegrationTestCase, UnitTestCase
except ImportError:  # no bench: the rule is still testable
	from unittest import TestCase as IntegrationTestCase
	from unittest import TestCase as UnitTestCase

from crm import lingue


class LaLinguaDelCentro(UnitTestCase):
	def test_in_italiano_se_il_sito_non_ha_scelto(self):
		# English is the framework's default, not a choice of a centre in Italy
		self.assertEqual(lingue.scegli("en", "Italy"), "it")
		self.assertEqual(lingue.scegli("en", None), "it")
		self.assertEqual(lingue.scegli("en-US", ""), "it")
		self.assertEqual(lingue.scegli(None, None), "it")
		self.assertEqual(lingue.scegli("it", "Italy"), "it")

	def test_la_lingua_scelta_altrove_resta(self):
		self.assertEqual(lingue.scegli("en-GB", "United Kingdom"), "en")
		self.assertEqual(lingue.scegli("it", "Germany"), "it")

	def test_solo_italiano_o_inglese(self):
		# a language DottorCloud has no words in: English out of Italy, Italian in it
		self.assertEqual(lingue.scegli("de", "Germany"), "en")
		self.assertEqual(lingue.scegli("fr", "Italy"), "it")
		self.assertEqual(lingue.scegli("fr", None), "it")


# what the framework leaves on a site before anybody chose
MAI_IMPOSTATO = {
	"country": "",
	"language": None,
	"time_zone": None,
	"currency": None,
	"date_format": "yyyy-mm-dd",
	"number_format": "#,###.##",
	"first_day_of_the_week": "Sunday",
}


class UnSitoCheNessunoHaImpostato(UnitTestCase):
	"""Where the setup wizard never ran: Rome's clock and Italy's formats, never
	over what somebody chose."""

	def test_dove_nessuno_ha_detto_il_paese_e_l_italia(self):
		self.assertEqual(
			lingue.per_l_italia(MAI_IMPOSTATO),
			{
				"country": "Italy",
				"language": "it",
				"time_zone": "Europe/Rome",
				"currency": "EUR",
				"date_format": "dd/mm/yyyy",
				"number_format": "#.###,##",
				"first_day_of_the_week": "Monday",
			},
		)

	def test_quello_che_qualcuno_ha_scelto_resta(self):
		scelti = {
			**MAI_IMPOSTATO,
			"language": "en",
			"time_zone": "Europe/Zurich",
			"date_format": "dd.mm.yyyy",
			"number_format": "#'###.##",
		}
		self.assertEqual(
			lingue.per_l_italia(scelti),
			{
				"country": "Italy",
				"currency": "EUR",
				"first_day_of_the_week": "Monday",
			},
		)

	def test_in_italia_solo_quello_che_e_vuoto(self):
		# the wizard ran with Italy: its formats are the centre's, its Sunday is not
		italia = {
			"country": "Italy",
			"language": "en",
			"time_zone": None,
			"currency": "EUR",
			"date_format": "yyyy-mm-dd",
			"number_format": "#,###.##",
			"first_day_of_the_week": "Sunday",
		}
		self.assertEqual(
			lingue.per_l_italia(italia), {"time_zone": "Europe/Rome", "first_day_of_the_week": "Monday"}
		)
		# nothing left to write: nothing written, at every migrate
		self.assertEqual(
			lingue.per_l_italia({**italia, "time_zone": "Europe/Rome", "first_day_of_the_week": "Monday"}), {}
		)
		self.assertEqual(
			lingue.per_l_italia({**MAI_IMPOSTATO, **lingue.ITALIA, "country": "Italy", "language": "it"}), {}
		)

	def test_un_altro_paese_tiene_tutto_ma_la_settimana(self):
		# the week starts on Monday everywhere in Europe
		self.assertEqual(
			lingue.per_l_italia({**MAI_IMPOSTATO, "country": "Switzerland"}),
			{"first_day_of_the_week": "Monday"},
		)
		self.assertEqual(
			lingue.per_l_italia(
				{**MAI_IMPOSTATO, "country": "Switzerland", "first_day_of_the_week": "Monday"}
			),
			{},
		)


class GliUtentiSulFusoDelCentro(IntegrationTestCase):
	"""Who was made while the site had no zone follows the centre's; a zone somebody
	chose stays."""

	def tearDown(self):
		frappe.db.rollback()
		frappe.clear_cache()

	def utente(self, email: str, fuso: str) -> str:
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": "Fuso", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		frappe.db.set_value("User", email, "time_zone", fuso, update_modified=False)
		return email

	def test_kolkata_diventa_roma_il_resto_resta(self):
		da_prima = self.utente("fuso.kolkata@example.com", lingue.FUSO_DEL_FRAMEWORK)
		scelto = self.utente("fuso.londra@example.com", "Europe/London")
		self.assertGreaterEqual(lingue.utenti_sul_fuso_del_centro("Europe/Rome"), 1)
		self.assertEqual(frappe.db.get_value("User", da_prima, "time_zone"), "Europe/Rome")
		self.assertEqual(frappe.db.get_value("User", scelto, "time_zone"), "Europe/London")


def _utente(email: str, *ruoli: str, **campi) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"roles": [{"role": ruolo} for ruolo in ruoli],
			}
		).insert(ignore_permissions=True)
	if campi:
		frappe.db.set_value("User", email, campi, update_modified=False)
	return email


class LaLinguaDelCentroInImpostazioni(IntegrationTestCase):
	"""Settings > The centre > General > Language & time: Italian or English, a
	zone of Europe; whoever has not chosen reads the centre's."""

	def setUp(self):
		self.lingua = frappe.local.lang
		self.responsabile = _utente("lingua.responsabile@example.com", "Sales Manager", "Sales User")
		self.accoglienza = _utente("lingua.accoglienza@example.com", "Sales User")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		frappe.local.lang = self.lingua
		frappe.clear_cache()

	@staticmethod
	def rifatte(coda) -> int:
		"""How many times DottorCloud's own words were sent to follow the language."""
		return sum(
			1 for chiamata in coda.call_args_list if chiamata.args[:1] == ("crm.lingue.dopo_il_cambio",)
		)

	def test_la_sceglie_chi_imposta_il_centro(self):
		frappe.set_user(self.accoglienza)
		with self.assertRaises(frappe.PermissionError):
			lingue.get_centre_language()
		with self.assertRaises(frappe.PermissionError):
			lingue.save_centre_language("en")
		frappe.set_user(self.responsabile)
		stato = lingue.get_centre_language()
		self.assertEqual([lingua["value"] for lingua in stato["languages"]], ["it", "en"])
		self.assertIn("Europe/Rome", stato["time_zones"])
		self.assertIn("Atlantic/Canary", stato["time_zones"])
		self.assertNotIn("America/New_York", stato["time_zones"])

	def test_l_inglese_scelto_in_italia_resta(self):
		frappe.db.set_single_value("System Settings", "country", "Italy")
		frappe.set_user(self.responsabile)
		with patch("frappe.enqueue") as coda:
			lingue.save_centre_language("it")
			coda.reset_mock()
			stato = lingue.save_centre_language("en")
			# DottorCloud's own words follow it, in the background, once
			self.assertEqual(self.rifatte(coda), 1)
			coda.reset_mock()
			lingue.save_centre_language("en")
			self.assertEqual(self.rifatte(coda), 0)
		self.assertEqual(stato["language"], "en")
		self.assertEqual(frappe.db.get_single_value("System Settings", "language"), "en")
		self.assertEqual(frappe.db.get_default("lang"), "en")
		# the centre chose it: in Italy too, and after a migrate
		lingue.solo_italiano_e_inglese()
		self.assertEqual(lingue.del_centro(), "en")
		self.assertEqual(frappe.db.get_single_value("System Settings", "language"), "en")

	def test_solo_italiano_o_inglese_e_un_fuso_d_europa(self):
		frappe.set_user(self.responsabile)
		with self.assertRaises(frappe.ValidationError):
			lingue.save_centre_language("de")
		with self.assertRaises(frappe.ValidationError):
			lingue.save_centre_language("it", "America/New_York")

	def test_chi_teneva_l_ora_del_centro_la_segue(self):
		frappe.db.set_single_value("System Settings", "time_zone", "Europe/Rome")
		del_centro = _utente("lingua.ora.centro@example.com", time_zone="Europe/Rome")
		sua = _utente("lingua.ora.sua@example.com", time_zone="Europe/London")
		frappe.set_user(self.responsabile)
		with patch("frappe.enqueue"):
			stato = lingue.save_centre_language(lingue.del_centro(), "Europe/Lisbon")
		self.assertEqual(stato["time_zone"], "Europe/Lisbon")
		self.assertEqual(frappe.db.get_value("User", del_centro, "time_zone"), "Europe/Lisbon")
		self.assertEqual(frappe.db.get_value("User", sua, "time_zone"), "Europe/London")

	def test_chi_non_ha_scelto_legge_la_lingua_del_centro(self):
		# the framework's English left on a centre in Italy, nobody chose in Settings
		frappe.defaults.clear_default(lingue.SCELTA)
		frappe.db.set_single_value("System Settings", {"language": "en", "country": "Italy"})
		lingue.solo_italiano_e_inglese()
		self.assertEqual(frappe.db.get_single_value("System Settings", "language"), "it")
		self.assertEqual(frappe.db.get_default("lang"), "it")

	def test_chi_leggeva_un_altra_lingua_legge_quella_del_centro(self):
		tedesco = _utente("lingua.tedesco@example.com", language="de")
		inglese = _utente("lingua.inglese@example.com", language="en")
		self.assertGreaterEqual(lingue.utenti_in_italiano_o_inglese(), 1)
		self.assertFalse(frappe.db.get_value("User", tedesco, "language"))
		self.assertEqual(frappe.db.get_value("User", inglese, "language"), "en")


class LApostrofoDavantiAUnaData(UnitTestCase):
	"""«fino all'11 ottobre»: the server's filled sentences elide as the SPA's do
	(`conLApostrofo`, utils/locale.js)."""

	def test_davanti_al_giorno_1_8_11_di_una_data(self):
		c = lingue.con_l_apostrofo
		self.assertEqual(
			c("Il link vale fino al 1 ottobre, 14:00.", "it"), "Il link vale fino all'1 ottobre, 14:00."
		)
		self.assertEqual(c("Puoi aprirlo fino al 11/10/2026.", "it"), "Puoi aprirlo fino all'11/10/2026.")
		self.assertEqual(c("Fino al 8-10-2026", "it"), "Fino all'8-10-2026")
		self.assertEqual(c("prima del 1/1/2021", "it"), "prima dell'1/1/2021")
		self.assertEqual(c("Il 11 ott", "it"), "L'11 ott")
		# Italy's format writes the day with its zero
		self.assertEqual(c("Puoi aprirlo fino al 08/10/2026.", "it"), "Puoi aprirlo fino all'08/10/2026.")
		self.assertEqual(c("il 01/10/2026", "it"), "l'01/10/2026")

	def test_altrimenti_resta_com_e(self):
		c = lingue.con_l_apostrofo
		# another day, a day without a date, a rate, a year, a day read with no vowel
		for testo in (
			"al 12 ottobre",
			"il 11",
			"il riepilogo IVA al 10%",
			"nel 2026",
			"il 09/10/2026",
			"dal 10/01/2026",
		):
			self.assertEqual(c(testo, "it"), testo)
		# other languages, and what is not a sentence
		self.assertEqual(c("until al 11/10", "en"), "until al 11/10")
		self.assertIsNone(c(None, "it"))
