# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Fiscal identifiers and document numbering.

The codice fiscale tests exist because a validator written by eye rejects omocodia
codes, which are valid, and accepts anything sixteen characters long, which is how
an expense lands in somebody else's pre-filled tax return.
"""

from __future__ import annotations

from datetime import date

from crm.invoicing.engine import codice_fiscale as cf
from crm.invoicing.engine.numerazione import (
	FORMATO_DEFAULT,
	FormatoNonCompatibile,
	componi,
	prossimo,
	valida_formato,
)
from crm.invoicing.tests.base import UnitTestCase


class CodiceFiscaleTest(UnitTestCase):
	def test_si_valida_il_carattere_di_controllo_non_la_lunghezza(self):
		self.assertTrue(cf.valido("RSSMRA80A01H501U"))
		self.assertFalse(cf.valido("RSSMRA80A01H501A"))
		self.assertFalse(cf.valido("AAAAAAAAAAAAAAAA"))

	def test_l_omocodia_e_valida_e_si_normalizza(self):
		omocodo = "RSSMRA80A01H50MM"
		self.assertTrue(cf.valido(omocodo))
		self.assertEqual(cf.normalizza(omocodo), "RSSMRA80A01H501U")
		self.assertTrue(cf.analizza(omocodo).omocodia)

	def test_il_codice_si_decodifica(self):
		dati = cf.analizza("RSSMRA80A01H501U")
		self.assertEqual(dati.data_nascita, date(1980, 1, 1))
		self.assertEqual(dati.sesso, "M")
		self.assertEqual(dati.codice_catastale, "H501")

	def test_il_confronto_con_l_anagrafica_intercetta_lo_scambio_di_persona(self):
		self.assertEqual(cf.coerente_con_anagrafica("RSSMRA80A01H501U", "Rossi", "Mario"), [])
		problemi = cf.coerente_con_anagrafica("RSSMRA80A01H501U", "Bianchi", "Luca")
		self.assertEqual(len(problemi), 2)

	def test_il_confronto_non_solleva_su_un_codice_rotto(self):
		self.assertEqual(len(cf.coerente_con_anagrafica("NONVALIDO", "Rossi")), 1)

	def test_la_partita_iva_ha_il_suo_check_digit(self):
		self.assertTrue(cf.partita_iva_valida("00743110157"))
		self.assertFalse(cf.partita_iva_valida("00743110158"))
		self.assertFalse(cf.partita_iva_valida("0074311015"))

	def test_il_codice_ts_di_undici_cifre_non_e_una_partita_iva(self):
		# Doctors without a VAT number get an eleven-digit code that does not carry
		# the check digit. Validating it as a VAT number rejects a legitimate sender.
		self.assertTrue(cf.identificativo_ts_valido("12345678901"))
		self.assertFalse(cf.partita_iva_valida("12345678901"))

	def test_le_partite_iva_europee_si_validano_nel_formato(self):
		self.assertTrue(cf.partita_iva_ue_valida("DE123456789"))
		self.assertTrue(cf.partita_iva_ue_valida("NL123456789B01"))
		self.assertTrue(cf.partita_iva_ue_valida("00743110157", "IT"))
		self.assertFalse(cf.partita_iva_ue_valida("DE12345"))
		self.assertFalse(cf.partita_iva_ue_valida("ZZ123456789"))

	def test_la_grecia_si_scrive_el_sulle_fatture(self):
		self.assertTrue(cf.partita_iva_ue_valida("EL123456789"))
		self.assertTrue(cf.partita_iva_ue_valida("123456789", "GR"))

	def test_l_intracomunitario_esclude_l_italia(self):
		self.assertTrue(cf.e_intracomunitario("DE"))
		self.assertFalse(cf.e_intracomunitario("IT"))
		self.assertFalse(cf.e_intracomunitario("US"))

	def test_l_iban_si_valida_con_lunghezza_e_mod97(self):
		self.assertTrue(cf.iban_valido("IT60X0542811101000000123456"))
		self.assertFalse(cf.iban_valido("IT60X054281110100000012345"))
		self.assertFalse(cf.iban_valido("IT60X0542811101000000123457"))


class NumerazioneTest(UnitTestCase):
	def test_il_formato_di_default_passa_il_tracciato(self):
		valida_formato(FORMATO_DEFAULT)
		self.assertEqual(componi(FORMATO_DEFAULT, "S", 2026, 128), "2026/S/128")

	def test_un_formato_senza_numero_non_e_progressivo(self):
		with self.assertRaises(FormatoNonCompatibile):
			valida_formato("{anno}/{serie}")

	def test_un_formato_senza_segnaposto_e_rifiutato(self):
		with self.assertRaises(FormatoNonCompatibile):
			valida_formato("FATTURA")

	def test_gli_spazi_non_passano_il_sistema_ts(self):
		with self.assertRaises(FormatoNonCompatibile):
			valida_formato("Fattura n. {numero} del {anno}")

	def test_i_due_punti_non_passano(self):
		with self.assertRaises(FormatoNonCompatibile):
			valida_formato("{anno}:{serie}:{numero}")

	def test_il_formato_si_valida_sul_caso_peggiore(self):
		# Fine at 1, twenty-one characters at 999999: document 100,000 arrives in
		# November, not in January.
		with self.assertRaises(FormatoNonCompatibile):
			valida_formato("PREFISSO-LUNGHISSIMO-{anno}-{numero}")

	def test_un_segnaposto_sconosciuto_e_un_errore_leggibile(self):
		with self.assertRaises(FormatoNonCompatibile):
			valida_formato("{anno}/{mese}/{numero}")

	def test_il_progressivo_parte_da_uno(self):
		self.assertEqual(prossimo(0), 1)
		self.assertEqual(prossimo(None), 1)
		self.assertEqual(prossimo(127), 128)
