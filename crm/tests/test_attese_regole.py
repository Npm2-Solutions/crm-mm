# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A waiting list, without a site: when a place suits the person, who gets which
place and how many at once, how long an offer waits, what frees a place, and which
channel an offer takes."""

from __future__ import annotations

import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.scheduling import attese_regole as R

UTC = datetime.UTC
OGGI = datetime.date(2026, 10, 5)  # a Monday


def ora(giorno: int, h: int, m: int = 0) -> datetime.datetime:
	"""A moment of the week of 5 October 2026: 0 is Monday."""
	return datetime.datetime(2026, 10, 5 + giorno, h, m, tzinfo=UTC)


def posto(giorno, h, m=0, minuti=60, staff=("dott.rossi",), sessione=None, capienza=1) -> R.Posto:
	inizio = ora(giorno, h, m)
	return R.Posto(inizio, inizio + datetime.timedelta(minutes=minuti), tuple(staff), sessione, capienza)


class QuandoPuo(UnitTestCase):
	def test_le_mattine_del_lunedi_e_del_mercoledi(self):
		finestre = R.fasce(R.righe_da(["Monday", "Wednesday"], ["morning"]))
		self.assertTrue(R.adatto(finestre, ora(0, 9), ora(0, 10)))
		self.assertTrue(R.adatto(finestre, ora(2, 12), ora(2, 13)))
		# runs into the afternoon, or on a day they did not pick
		self.assertFalse(R.adatto(finestre, ora(0, 12, 30), ora(0, 13, 30)))
		self.assertFalse(R.adatto(finestre, ora(1, 9), ora(1, 10)))

	def test_mattina_e_pomeriggio_sono_una_fascia_sola(self):
		finestre = R.fasce(R.righe_da(["Monday"], ["morning", "afternoon"]))
		self.assertEqual(finestre, {0: [(0, 18 * 60)]})
		self.assertTrue(R.adatto(finestre, ora(0, 12, 30), ora(0, 13, 30)))

	def test_la_sera_arriva_a_fine_giornata(self):
		finestre = R.fasce(R.righe_da(["Friday"], ["evening"]))
		self.assertTrue(R.adatto(finestre, ora(4, 23), ora(4, 23, 59)))
		self.assertFalse(R.adatto(finestre, ora(4, 17), ora(4, 18)))

	def test_niente_scelto_va_sempre_bene(self):
		self.assertEqual(R.righe_da([], []), [])
		self.assertTrue(R.adatto(R.fasce([]), ora(6, 3), ora(6, 4)))

	def test_le_ore_scritte_a_mano(self):
		righe = [{"workday": "Tuesday", "start_time": "15:00:00", "end_time": "17:00:00"}]
		finestre = R.fasce(righe)
		self.assertTrue(R.adatto(finestre, ora(1, 15), ora(1, 16)))
		self.assertFalse(R.adatto(finestre, ora(1, 16, 30), ora(1, 17, 30)))
		# a time as the database hands it back
		self.assertEqual(
			R.fasce(
				[{"workday": "Tuesday", "start_time": datetime.timedelta(hours=15), "end_time": "17:00"}]
			),
			{1: [(900, 1020)]},
		)
		# a row that ends before it starts, or on no day, says nothing
		self.assertEqual(R.fasce([{"workday": "Tuesday", "start_time": "17:00", "end_time": "15:00"}]), {})

	def test_ogni_giorno_una_parte(self):
		righe = R.righe_da([], ["evening"])
		self.assertEqual(len(righe), 7)
		self.assertEqual({r["start_time"] for r in righe}, {"18:00:00"})

	def test_le_righe_tornano_scelte(self):
		for giorni, parti in (
			(["Monday", "Wednesday"], ["morning"]),
			(["Saturday"], ["morning", "evening"]),
			(["Tuesday"], []),
			([], ["afternoon"]),
		):
			scelte = R.scelte_da(R.righe_da(giorni, parti))
			self.assertEqual(scelte["days"], giorni or list(R.GIORNI))
			self.assertEqual(scelte["parts"], parti)
		self.assertEqual(R.scelte_da([]), {"days": [], "parts": []})
		# hours of one's own, or different days with different parts: shown as they are
		self.assertIsNone(R.scelte_da([{"workday": "Tuesday", "start_time": "15:00", "end_time": "17:00"}]))
		self.assertIsNone(
			R.scelte_da(R.righe_da(["Monday"], ["morning"]) + R.righe_da(["Tuesday"], ["evening"]))
		)


class ChiPrendeCosa(UnitTestCase):
	def test_il_primo_della_fila_prende_il_primo_posto(self):
		alle_9, alle_10 = posto(0, 9), posto(0, 10)
		fatto = R.scegli(
			[R.Attesa("A", [alle_9, alle_10]), R.Attesa("B", [alle_9, alle_10])], [], per_volta=1
		)
		# one at a time: B gets the next place, not the one A holds
		self.assertEqual(fatto, [("A", alle_9), ("B", alle_10)])

	def test_a_tre_alla_volta_il_primo_che_conferma(self):
		alle_9 = posto(0, 9)
		attese = [R.Attesa(nome, [alle_9]) for nome in "ABCD"]
		fatto = R.scegli(attese, [], per_volta=3)
		self.assertEqual([nome for nome, _p in fatto], ["A", "B", "C"])

	def test_le_proposte_in_corso_contano(self):
		alle_9 = posto(0, 9)
		fatto = R.scegli([R.Attesa("B", [alle_9])], [alle_9], per_volta=1)
		self.assertEqual(fatto, [])
		# another professional at the same hour is another place
		dalla_bianchi = posto(0, 9, staff=("dott.bianchi",))
		fatto = R.scegli([R.Attesa("B", [alle_9, dalla_bianchi])], [alle_9], per_volta=1)
		self.assertEqual(fatto, [("B", dalla_bianchi)])

	def test_ore_che_si_accavallano_sono_lo_stesso_posto(self):
		# a place at 9 and one at 9:30 of the same professional: one of them
		fatto = R.scegli([R.Attesa("A", [posto(0, 9)]), R.Attesa("B", [posto(0, 9, 30)])], [], per_volta=1)
		self.assertEqual([nome for nome, _p in fatto], ["A"])

	def test_una_lezione_con_due_posti(self):
		lezione = posto(2, 18, sessione="APPT-00007", capienza=2)
		attese = [R.Attesa(nome, [lezione]) for nome in "ABC"]
		self.assertEqual([n for n, _p in R.scegli(attese, [], per_volta=1)], ["A", "B"])

	def test_un_posto_si_propone_una_volta(self):
		alle_9, alle_10 = posto(0, 9), posto(0, 10)
		fatto = R.scegli([R.Attesa("A", [alle_9, alle_10], gia={alle_9.chiave})], [], per_volta=1)
		self.assertEqual(fatto, [("A", alle_10)])
		self.assertEqual(R.scegli([R.Attesa("A", [])], [], per_volta=1), [])

	def test_si_toccano(self):
		self.assertTrue(R.si_toccano(posto(0, 9), posto(0, 9, minuti=30)))
		self.assertFalse(R.si_toccano(posto(0, 9), posto(0, 10)))
		self.assertFalse(R.si_toccano(posto(0, 9), posto(0, 9, staff=("dott.bianchi",))))
		self.assertTrue(R.si_toccano(posto(0, 9, sessione="S1"), posto(0, 9, sessione="S1")))
		self.assertFalse(R.si_toccano(posto(0, 9, sessione="S1"), posto(0, 9)))


class IlTempo(UnitTestCase):
	def test_la_finestra_di_una_voce(self):
		self.assertEqual(R.finestra(OGGI, 30), (OGGI, OGGI + datetime.timedelta(days=30)))
		dal = OGGI + datetime.timedelta(days=5)
		fino = OGGI + datetime.timedelta(days=10)
		self.assertEqual(R.finestra(OGGI, 30, dal, fino), (dal, fino))
		self.assertEqual(R.finestra(OGGI, 7, None, fino), (OGGI, OGGI + datetime.timedelta(days=7)))
		self.assertIsNone(R.finestra(OGGI, 30, None, OGGI - datetime.timedelta(days=1)))
		self.assertIsNone(R.finestra(OGGI, 3, OGGI + datetime.timedelta(days=5)))

	def test_scaduta(self):
		self.assertTrue(R.scaduta(OGGI - datetime.timedelta(days=1), OGGI))
		self.assertFalse(R.scaduta(OGGI, OGGI))
		self.assertFalse(R.scaduta(None, OGGI))

	def test_una_proposta_aspetta_le_sue_ore(self):
		adesso = ora(0, 8)
		self.assertEqual(R.scadenza(adesso, ora(2, 9), 2), ora(0, 10))
		# never past an hour before the start
		self.assertEqual(R.scadenza(adesso, ora(0, 10), 2), ora(0, 9))
		# too close to answer: not offered
		self.assertIsNone(R.scadenza(adesso, ora(0, 9, 10), 2))

	def test_i_numeri_del_centro(self):
		self.assertEqual(R.entro(None, R.PER_VOLTA), 3)
		self.assertEqual(R.entro(50, R.PER_VOLTA), 10)
		self.assertEqual(R.entro("2", R.ORE_PER_RISPONDERE), 2)
		self.assertEqual(R.entro("x", R.GIORNI_AVANTI), 30)
		self.assertEqual(R.entro(-4, R.GIORNI_AVANTI), 1)


class CosaLiberaUnPosto(UnitTestCase):
	def base(self, **cambi):
		dati = {
			"status": "Confirmed",
			"inizio": ora(1, 9),
			"fine": ora(1, 10),
			"staff": ["dott.rossi"],
			"risorse": ["Studio 1"],
			"persone": 1,
		}
		dati.update(cambi)
		return dati

	def test_annullato_spostato_o_eliminato(self):
		adesso = ora(0, 8)
		prima = self.base()
		self.assertTrue(R.libera(prima, self.base(status="Cancelled"), adesso))
		self.assertTrue(R.libera(prima, None, adesso))
		self.assertTrue(R.libera(prima, self.base(inizio=ora(1, 11), fine=ora(1, 12)), adesso))
		self.assertTrue(R.libera(prima, self.base(staff=["dott.bianchi"]), adesso))
		self.assertTrue(R.libera(prima, self.base(risorse=["Studio 2"]), adesso))

	def test_un_posto_in_meno_in_una_lezione(self):
		adesso = ora(0, 8)
		self.assertTrue(R.libera(self.base(persone=8), self.base(persone=7), adesso))
		self.assertFalse(R.libera(self.base(persone=7), self.base(persone=8), adesso))

	def test_niente_si_libera(self):
		adesso = ora(0, 8)
		self.assertFalse(R.libera(self.base(), self.base(), adesso))
		# already over, or already cancelled, or new
		self.assertFalse(R.libera(self.base(inizio=ora(0, 7)), self.base(status="Cancelled"), adesso))
		self.assertFalse(R.libera(self.base(status="Cancelled"), None, adesso))
		self.assertFalse(R.libera(None, self.base(), adesso))


class ComeSiDice(UnitTestCase):
	def test_i_canali_del_centro(self):
		self.assertEqual(R.canali_offerti(True, True), ["WhatsApp", "SMS", "Email"])
		self.assertEqual(R.canali_offerti(False, False), ["Email"])

	def test_il_canale_scelto_poi_l_email(self):
		tutti = R.canali_offerti(True, True)
		self.assertEqual(R.come_mandare("WhatsApp", tutti, email=True, numero=True), ["WhatsApp", "Email"])
		# no number on file: the email only
		self.assertEqual(R.come_mandare("SMS", tutti, email=True, numero=False), ["Email"])
		# a channel the centre no longer offers
		self.assertEqual(R.come_mandare("SMS", ["Email"], email=True, numero=True), ["Email"])
		# nothing at all: the desk calls
		self.assertEqual(R.come_mandare("WhatsApp", tutti, email=False, numero=False), [])
		self.assertEqual(R.come_mandare("SMS", tutti, email=False, numero=True), ["SMS"])

	def test_le_variabili_del_modello(self):
		self.assertEqual(
			R.variabili(4, "Giulia", "Pilates", "mar 6 ott, 18:00", "https://x/l"),
			["Giulia", "Pilates", "mar 6 ott, 18:00", "https://x/l"],
		)
		self.assertEqual(R.variabili(2, "Giulia", "Pilates", "…", "…"), ["Giulia", "Pilates"])
		self.assertEqual(R.variabili(0, "Giulia", "Pilates", "…", "…"), [])
