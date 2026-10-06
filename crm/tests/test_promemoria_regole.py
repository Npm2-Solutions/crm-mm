# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The reminders' rules without a site: when one leaves, by which way, what an
answer means."""

import datetime
import unittest

from crm.scheduling import promemoria_regole as R


def ora(giorno: int, ore: int, minuti: int = 0) -> datetime.datetime:
	# October 2026: Tuesday 6, Wednesday 7, Thursday 8
	return datetime.datetime(2026, 10, giorno, ore, minuti)


class QuandoParte(unittest.TestCase):
	def test_il_giorno_prima_alla_stessa_ora(self):
		self.assertEqual(R.momento_di_invio(ora(7, 9, 30), 24), ora(6, 9, 30))

	def test_di_notte_parte_la_mattina(self):
		# an appointment at 7:00: its reminder would leave at 7:00 the day before
		self.assertEqual(R.momento_di_invio(ora(7, 7), 24), ora(6, 8))
		# an evening class: 22:00 the day before is night, the morning of the day
		self.assertEqual(R.momento_di_invio(ora(7, 22), 24), ora(7, 8))

	def test_la_mattina_troppo_vicina_va_alla_sera_prima(self):
		# two hours before 8:30 is 6:30; the morning would be half an hour before
		self.assertEqual(R.momento_di_invio(ora(7, 8, 30), 2), ora(6, 20))
		self.assertEqual(R.momento_di_invio(ora(7, 7, 30), 2), ora(6, 20))

	def test_dovuto_dal_suo_momento_fino_all_ultima_ora(self):
		inizio = ora(7, 9, 30)
		self.assertFalse(R.dovuto(inizio, ora(6, 9, 29), 24))
		self.assertTrue(R.dovuto(inizio, ora(6, 9, 30), 24))
		# missed by a server that was off: it still leaves, until the last hour
		self.assertTrue(R.dovuto(inizio, ora(7, 8, 29), 24))
		self.assertFalse(R.dovuto(inizio, ora(7, 8, 31), 24))

	def test_appena_prenotato_non_si_ricorda(self):
		inizio = ora(7, 18)
		# booked the evening before: the booking said it all
		self.assertFalse(R.dovuto(inizio, ora(6, 18), 24, prenotato_il=ora(6, 17)))
		self.assertFalse(R.dovuto(inizio, ora(6, 20), 24, prenotato_il=ora(6, 19)))
		# booked in the morning, the evening's reminder leaves
		self.assertTrue(R.dovuto(inizio, ora(6, 18), 24, prenotato_il=ora(6, 9)))

	def test_dove_cercare_copre_la_notte(self):
		dal, al = R.da_cercare(ora(6, 20), 24)
		self.assertEqual(dal, ora(6, 21))
		# a reminder moved to 20:00 the evening before reaches the morning after next
		self.assertTrue(al >= ora(7, 20) + datetime.timedelta(hours=12))
		for inizio in (ora(7, 7, 30), ora(7, 8, 30)):
			momento = R.momento_di_invio(inizio, 2)
			dal, al = R.da_cercare(momento, 2)
			self.assertTrue(dal <= inizio <= al, inizio)

	def test_le_ore_scelte_restano_nei_limiti(self):
		self.assertEqual(R.ore_prima(None), 24)
		self.assertEqual(R.ore_prima(1), 2)
		self.assertEqual(R.ore_prima(500), 72)
		self.assertEqual(R.ore_prima("48"), 48)


class Come(unittest.TestCase):
	def test_whatsapp_poi_sms_poi_email(self):
		self.assertEqual(R.canali(True, True, True, True, True), [R.WHATSAPP, R.SMS, R.EMAIL])
		self.assertEqual(R.canali(False, True, True, True, False), [R.SMS])
		self.assertEqual(R.canali(True, True, True, False, True), [R.EMAIL])
		self.assertEqual(R.canali(True, True, False, False, True), [])

	def test_chi_ha_scritto_stop_non_riceve_sms(self):
		self.assertEqual(R.canali(False, True, True, True, True, fermato=True), [R.EMAIL])
		self.assertEqual(R.canali(True, True, False, True, False, fermato=True), [R.WHATSAPP])

	def test_le_variabili_del_modello(self):
		self.assertEqual(
			R.variabili(4, "Anna", "Visita", "mercoledì alle 9:30", "Centro"),
			["Anna", "Visita", "mercoledì alle 9:30", "Centro"],
		)
		self.assertEqual(R.variabili(2, "Anna", "Visita", "x", "y"), ["Anna", "Visita"])
		# Meta refuses an empty variable
		self.assertEqual(R.variabili(4, "", "Visita", "x", None), ["-", "Visita", "x", "-"])


class LaRisposta(unittest.TestCase):
	def test_i_pulsanti_del_modello(self):
		for lingua in ("it", "en"):
			confermo, disdico, sposto = R.modello(lingua)["buttons"]
			self.assertEqual(R.risposta(confermo, pulsante=True), R.CONFERMA, lingua)
			self.assertEqual(R.risposta(disdico, pulsante=True), R.NON_VIENE, lingua)
			self.assertEqual(R.risposta(sposto, pulsante=True), R.SPOSTA, lingua)

	def test_i_pulsanti_di_un_modello_del_centro(self):
		self.assertEqual(R.risposta("Sì, ci sarò", pulsante=True), R.CONFERMA)
		self.assertEqual(R.risposta("Non ci sarò", pulsante=True), R.NON_VIENE)
		self.assertEqual(R.risposta("Non posso venire", pulsante=True), R.NON_VIENE)
		self.assertEqual(R.risposta("Annulla l'appuntamento", pulsante=True), R.NON_VIENE)
		self.assertEqual(R.risposta("Cambia orario", pulsante=True), R.SPOSTA)
		self.assertEqual(R.risposta("Informazioni", pulsante=True), None)

	def test_un_sms_che_dice_solo_quello(self):
		self.assertEqual(R.risposta("SI"), R.CONFERMA)
		self.assertEqual(R.risposta("Sì, grazie!"), R.CONFERMA)
		self.assertEqual(R.risposta("ok perfetto grazie"), R.CONFERMA)
		self.assertEqual(R.risposta("👍"), R.CONFERMA)
		self.assertEqual(R.risposta("No grazie"), R.NON_VIENE)
		self.assertEqual(R.risposta("Disdico"), R.NON_VIENE)
		self.assertEqual(R.risposta("sposta"), R.SPOSTA)

	def test_un_messaggio_resta_un_messaggio(self):
		# whatever says more is read by the desk
		self.assertIsNone(R.risposta("Sì ma arrivo 10 minuti in ritardo"))
		self.assertIsNone(R.risposta("No problem, ci sarò"))
		self.assertIsNone(R.risposta(""))
		self.assertIsNone(R.risposta(None))
		# STOP is the SMS's own: it never answers a reminder
		self.assertIsNone(R.risposta("STOP"))

	def test_un_modello_con_i_pulsanti_giusti(self):
		self.assertTrue(R.ha_i_pulsanti(R.modello("it")["buttons"]))
		self.assertTrue(R.ha_i_pulsanti(["Confermo", "Non posso"]))
		self.assertFalse(R.ha_i_pulsanti(["Confermo"]))
		self.assertFalse(R.ha_i_pulsanti([]))


class ChiRisponde(unittest.TestCase):
	def test_lo_stesso_numero_scritto_in_ogni_modo(self):
		self.assertTrue(R.stesso_numero("+39 333 123 4567", "393331234567"))
		self.assertTrue(R.stesso_numero("whatsapp:+393331234567", "333-1234567"))
		self.assertFalse(R.stesso_numero("+393331234567", "+393331234568"))
		self.assertFalse(R.stesso_numero("", ""))
		self.assertFalse(R.stesso_numero("12", "12"))

	def test_una_risposta_vale_finche_l_appuntamento_e_quello(self):
		inizio, adesso = ora(7, 9), ora(6, 10)
		self.assertTrue(R.vale("Scheduled", inizio, inizio, adesso))
		self.assertTrue(R.vale("Confirmed", inizio, inizio, adesso))
		self.assertFalse(R.vale("Cancelled", inizio, inizio, adesso))
		# moved after the reminder: the answer was about another time
		self.assertFalse(R.vale("Scheduled", ora(8, 9), inizio, adesso))
		self.assertFalse(R.vale("Scheduled", inizio, inizio, ora(7, 9, 5)))
		self.assertFalse(R.vale("Scheduled", inizio, inizio, adesso, partecipa=False))


if __name__ == "__main__":
	unittest.main()
