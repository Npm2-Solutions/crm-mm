# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The fiscal profile's rules, without a site.

What an invoice takes and what it gives back are the whole feature: taken wrong, a
correction made at the desk disappears; given back wrong, a parent's codice
fiscale ends up in a child's profile and on every invoice after.
"""

from __future__ import annotations

from datetime import date

from crm.invoicing.engine import anagrafica as a
from crm.invoicing.tests.base import UnitTestCase

CF = "RSSMRA80A01H501U"
CF_DONNA = "BNCLCU75B41F205Z"

INDIRIZZO = {
	"address_line": "Via Verdi",
	"civic_number": "3",
	"postal_code": "00100",
	"city": "Roma",
	"province": "RM",
	"country": "IT",
}


class DaCompilareTest(UnitTestCase):
	def test_prende_quello_che_la_fattura_ha_lasciato_vuoto(self):
		valori = a.da_compilare({"country": "IT"}, {"fiscal_code": CF, "pec": "m@pec.it", **INDIRIZZO})
		self.assertEqual(valori["fiscal_code"], CF)
		self.assertEqual(valori["pec"], "m@pec.it")
		self.assertEqual(valori["city"], "Roma")

	def test_quello_scritto_sulla_fattura_resta(self):
		valori = a.da_compilare({"fiscal_code": CF_DONNA}, {"fiscal_code": CF})
		self.assertNotIn("fiscal_code", valori)

	def test_l_indirizzo_viaggia_intero(self):
		"""A city typed on the invoice keeps the profile's street off it."""
		valori = a.da_compilare({"city": "Milano", "country": "IT"}, dict(INDIRIZZO))
		self.assertEqual(valori, {})

	def test_il_paese_da_solo_non_e_un_indirizzo(self):
		valori = a.da_compilare({"country": "IT"}, {**INDIRIZZO, "country": "DE", "postal_code": "10115"})
		self.assertEqual(valori["country"], "DE")

	def test_il_nome_solo_per_un_azienda(self):
		profilo = {"billing_name": "Studio Rossi Srl"}
		self.assertEqual(a.da_compilare({"recipient_type": "persona_fisica"}, profilo), {})
		self.assertEqual(
			a.da_compilare({"recipient_type": "soggetto_iva"}, profilo)["billing_name"], "Studio Rossi Srl"
		)


class DaCompletareTest(UnitTestCase):
	def test_riempie_solo_dove_il_profilo_e_vuoto(self):
		valori = a.da_completare({"fiscal_code": CF}, {"fiscal_code": CF_DONNA, "pec": "x@pec.it"})
		self.assertEqual(valori, {"pec": "x@pec.it"})

	def test_un_indirizzo_c_e_gia_e_resta(self):
		valori = a.da_completare(dict(INDIRIZZO), {**INDIRIZZO, "city": "Milano"})
		self.assertEqual(valori, {})

	def test_il_nome_di_una_persona_non_torna(self):
		fattura = {"recipient_type": "persona_fisica", "billing_name": "Mario Rossi", "fiscal_code": CF}
		self.assertEqual(a.da_completare({}, fattura), {"fiscal_code": CF})

	def test_la_ragione_sociale_torna(self):
		fattura = {"recipient_type": "soggetto_iva", "billing_name": "Acme Srl", "tax_id": "00743110157"}
		self.assertEqual(a.da_completare({}, fattura)["billing_name"], "Acme Srl")


class StessaPersonaTest(UnitTestCase):
	def test_lo_stesso_nome(self):
		self.assertTrue(
			a.stessa_persona(
				{"first_name": "Mario", "last_name": "Rossi"}, {"first_name": "mario", "last_name": "ROSSI"}
			)
		)

	def test_il_nome_intero_nel_campo_del_nome(self):
		"""A web form writes 'Mario Rossi' in the first name; the desk splits it."""
		self.assertTrue(
			a.stessa_persona({"first_name": "Mario", "last_name": "Rossi"}, {"first_name": "Mario Rossi"})
		)

	def test_il_cognome_che_mancava(self):
		self.assertTrue(
			a.stessa_persona({"first_name": "Mario", "last_name": "Rossi"}, {"first_name": "Mario"})
		)

	def test_gli_accenti_non_fanno_un_altra_persona(self):
		self.assertTrue(
			a.stessa_persona(
				{"first_name": "Nicolò", "last_name": "Rè"}, {"first_name": "Nicolo", "last_name": "Re"}
			)
		)

	def test_il_genitore_che_paga_e_un_altra_persona(self):
		self.assertFalse(
			a.stessa_persona(
				{"first_name": "Luca", "last_name": "Rossi"}, {"first_name": "Giulia", "last_name": "Rossi"}
			)
		)

	def test_senza_nome_non_si_puo_dire(self):
		self.assertFalse(a.stessa_persona({}, {"first_name": "Mario"}))


class ValoriTest(UnitTestCase):
	def test_si_scrivono_sempre_allo_stesso_modo(self):
		valori = a.normalizza(
			{
				"fiscal_code": " rss mra80a01h501u ",
				"province": "rm",
				"pec": " Mario@PEC.it",
				"city": "  Roma  ",
				"note": "x",
			}
		)
		self.assertEqual(valori["fiscal_code"], CF)
		self.assertEqual(valori["province"], "RM")
		self.assertEqual(valori["pec"], "mario@pec.it")
		self.assertEqual(valori["city"], "Roma")
		self.assertNotIn("note", valori)

	def test_vuoto_e_none(self):
		self.assertEqual(a.normalizza({"city": "  "}), {"city": None})

	def test_gli_errori_che_la_fattura_troverebbe_dopo(self):
		self.assertEqual(a.errori({"fiscal_code": CF, **INDIRIZZO}), [])
		self.assertIn("fiscal_code", a.errori({"fiscal_code": "RSSMRA80A01H501A"}))
		self.assertIn("fiscal_code", a.errori({"fiscal_code": "12345"}))
		self.assertIn("tax_id", a.errori({"tax_id": "00743110158"}))
		self.assertIn("recipient_code", a.errori({"recipient_code": "ABC"}))
		self.assertIn("postal_code", a.errori({"postal_code": "0010"}))
		self.assertIn("province", a.errori({"province": "Roma"}))

	def test_il_codice_fiscale_di_un_azienda_ha_undici_cifre(self):
		self.assertEqual(a.errori({"fiscal_code": "00743110157"}), [])

	def test_all_estero_non_si_indovina(self):
		"""A foreign tax number has any shape, and a format nobody listed is not checked."""
		self.assertEqual(
			a.errori({"fiscal_code": "123-45-6789", "country": "US", "tax_id": "12-3456789"}), []
		)
		self.assertIn("tax_id", a.errori({"tax_id": "DE12345", "country": "DE"}))


class CodiceTest(UnitTestCase):
	def test_data_di_nascita_e_sesso_dal_codice(self):
		self.assertEqual(a.dati_dal_codice(CF), {"birth_date": date(1980, 1, 1), "sex": "M"})
		self.assertEqual(a.dati_dal_codice(CF_DONNA)["sex"], "F")

	def test_un_codice_che_non_e_di_una_persona_non_dice_niente(self):
		self.assertEqual(a.dati_dal_codice("00743110157"), {"birth_date": None, "sex": None})
		self.assertEqual(a.dati_dal_codice("RSSMRA80A01H501A"), {"birth_date": None, "sex": None})

	def test_le_incoerenze_con_la_persona(self):
		self.assertEqual(a.incoerenze(CF, cognome="Rossi", nome="Mario", sesso="M"), [])
		self.assertEqual(a.incoerenze(CF, cognome="Bianchi", nome="Mario", sesso="F"), ["cognome", "sesso"])

	def test_senza_dati_non_c_e_niente_da_confrontare(self):
		self.assertEqual(a.incoerenze(CF), [])
