# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The rules of linked people, without a site: sides, names, ages."""

from __future__ import annotations

from datetime import date

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.persone import legami as l


class LatiTest(UnitTestCase):
	def test_ogni_relazione_ha_la_sua_inversa(self):
		for relazione in l.RELAZIONI:
			self.assertEqual(l.inversa(l.inversa(relazione)), relazione)
		self.assertEqual(l.inversa(l.GENITORE), l.FIGLIO)
		self.assertEqual(l.inversa(l.TUTORE), l.TUTELATO)
		self.assertEqual(l.inversa(l.PARTNER), l.PARTNER)

	def test_una_relazione_sconosciuta_si_ferma(self):
		with self.assertRaises(ValueError):
			l.inversa("Cousin")

	def test_si_scrive_dal_lato_di_chi_e_seguito(self):
		# on Luca's page: Maria is his parent, and acts for him
		self.assertEqual(
			l.orienta("LUCA", "MARIA", l.GENITORE, l.LORO_PER_ME),
			l.Legame(persona="LUCA", collegata="MARIA", relazione=l.GENITORE),
		)
		# on Maria's page: Luca is her child, and she acts for him - the same row
		self.assertEqual(
			l.orienta("MARIA", "LUCA", l.FIGLIO, l.IO_PER_LORO),
			l.Legame(persona="LUCA", collegata="MARIA", relazione=l.GENITORE),
		)

	def test_il_figlio_che_segue_la_madre_anziana(self):
		# on Paolo's page: Anna is his mother, and he books and pays for her
		self.assertEqual(
			l.orienta("PAOLO", "ANNA", l.GENITORE, l.IO_PER_LORO),
			l.Legame(persona="ANNA", collegata="PAOLO", relazione=l.FIGLIO),
		)

	def test_senza_nessuno_che_agisce_resta_dal_lato_scritto(self):
		self.assertEqual(
			l.orienta("MARIA", "PAOLO", l.PARTNER),
			l.Legame(persona="MARIA", collegata="PAOLO", relazione=l.PARTNER),
		)

	def test_nessuno_e_legato_a_se_stesso(self):
		with self.assertRaises(ValueError):
			l.orienta("MARIA", "MARIA", l.FAMILIARE)
		with self.assertRaises(ValueError):
			l.orienta("MARIA", "", l.FAMILIARE)
		with self.assertRaises(ValueError):
			l.orienta("MARIA", "LUCA", l.FIGLIO, "sideways")

	def test_la_riga_letta_dai_due_lati(self):
		riga = {"person": "LUCA", "related_person": "MARIA", "relation": l.GENITORE, "pays": 1}
		self.assertEqual(
			l.dal_lato_di(riga, "LUCA"), {"other": "MARIA", "relation": l.GENITORE, "acts": l.LORO_PER_ME}
		)
		self.assertEqual(
			l.dal_lato_di(riga, "MARIA"), {"other": "LUCA", "relation": l.FIGLIO, "acts": l.IO_PER_LORO}
		)
		with self.assertRaises(ValueError):
			l.dal_lato_di(riga, "PAOLO")

	def test_senza_verso_nessuno_paga_ne_prenota(self):
		self.assertEqual(
			l.azioni({"pays": 1, "books": 1}, l.NESSUNO), {"pays": 0, "books": 0, "represents": 0}
		)
		self.assertEqual(
			l.azioni({"pays": 1, "represents": True}, l.LORO_PER_ME),
			{"pays": 1, "books": 0, "represents": 1},
		)


class NomiTest(UnitTestCase):
	def test_le_parole_contano_non_l_ordine_ne_gli_accenti(self):
		self.assertTrue(l.stesso_nome("Mario Rossi", "ROSSI mario"))
		self.assertTrue(l.stesso_nome("Nicolò D'Amico", "nicolo d'amico"))

	def test_scritto_meno_per_intero_e_la_stessa_persona(self):
		self.assertTrue(l.stesso_nome("Mario", "Mario Rossi"))
		self.assertTrue(l.stesso_nome("Maria Grazia Rossi", "Maria Rossi"))

	def test_un_nome_diverso_e_un_altro(self):
		self.assertFalse(l.stesso_nome("Luca Rossi", "Maria Rossi"))
		# never by likeness: a brother and a sister
		self.assertFalse(l.stesso_nome("Luca Rossi", "Lucia Rossi"))
		# nor by initials: "M. Rossi" could be the mother Maria or her son Marco
		self.assertFalse(l.stesso_nome("M. Rossi", "Marco Rossi"))
		self.assertFalse(l.stesso_nome("M. Rossi", "Maria Rossi"))

	def test_un_nome_vuoto_non_e_nessuno(self):
		self.assertFalse(l.stesso_nome("", "Mario Rossi"))
		self.assertFalse(l.stesso_nome(None, None))

	def test_un_email_o_un_numero_non_sono_un_nome(self):
		self.assertFalse(l.nome_noto("maria.rossi@example.com"))
		self.assertFalse(l.nome_noto("+39 333 123 4567"))
		self.assertFalse(l.nome_noto("  "))
		self.assertTrue(l.nome_noto("Maria Rossi"))

	def test_dividi_come_la_cassa(self):
		self.assertEqual(l.dividi("Maria Grazia Rossi"), ("Maria", "Grazia Rossi"))
		self.assertEqual(l.dividi("Luca"), ("Luca", ""))
		self.assertEqual(l.dividi(""), ("", ""))


class PerChiTest(UnitTestCase):
	MARIA = ("MARIA", "Maria Rossi")
	FIGLI = (("LUCA", "Luca Rossi"), ("ANNA", "Anna Rossi"))

	def test_nessuno_col_contatto_e_qualcuno_di_nuovo(self):
		self.assertIsNone(l.per_chi("Maria Rossi", None, []))

	def test_il_suo_nome_e_il_titolare(self):
		self.assertEqual(l.per_chi("Maria Rossi", self.MARIA, self.FIGLI), "MARIA")
		self.assertEqual(l.per_chi("Rossi Maria", self.MARIA, self.FIGLI), "MARIA")

	def test_senza_nome_o_con_un_titolare_senza_nome_e_il_titolare(self):
		self.assertEqual(l.per_chi("", self.MARIA, self.FIGLI), "MARIA")
		self.assertEqual(l.per_chi("Luca Rossi", ("MARIA", "maria@example.com"), []), "MARIA")

	def test_il_nome_di_uno_dei_suoi_e_quello(self):
		self.assertEqual(l.per_chi("Luca Rossi", self.MARIA, self.FIGLI), "LUCA")
		self.assertEqual(l.per_chi("Anna", self.MARIA, self.FIGLI), "ANNA")

	def test_un_nome_nuovo_e_una_persona_nuova(self):
		self.assertIsNone(l.per_chi("Paolo Bianchi", self.MARIA, self.FIGLI))

	def test_due_possibili_nessuno(self):
		# "Rossi" alone would be Maria herself; among the children it is a guess
		self.assertIsNone(l.scegli("Rossi", self.FIGLI))

	def test_le_stesse_parole_battono_le_parole_in_piu(self):
		candidati = [("LUCA", "Luca Rossi"), ("LUCA2", "Luca Rossi Bianchi")]
		self.assertEqual(l.scegli("Luca Rossi", candidati), "LUCA")


class EtaTest(UnitTestCase):
	def test_il_compleanno_non_ancora_arrivato_non_conta(self):
		self.assertEqual(l.eta(date(2008, 10, 1), date(2026, 9, 29)), 17)
		self.assertEqual(l.eta(date(2008, 9, 29), date(2026, 9, 29)), 18)

	def test_minorenne_o_non_si_sa(self):
		self.assertTrue(l.minorenne(date(2015, 1, 1), date(2026, 9, 29)))
		self.assertFalse(l.minorenne(date(1980, 1, 1), date(2026, 9, 29)))
		self.assertIsNone(l.minorenne(None, date(2026, 9, 29)))
