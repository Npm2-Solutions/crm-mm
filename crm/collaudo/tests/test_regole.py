# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre the simulation plays, without a site: its team, its services, its
week, and what makes it whole."""

from __future__ import annotations

import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.collaudo import regole as R


class LaSquadra(UnitTestCase):
	def test_ogni_ruolo_ha_il_suo_collega(self):
		self.assertEqual(tuple(c.ruolo for c in R.SQUADRA), R.RUOLI)

	def test_gli_indirizzi_sono_della_simulazione(self):
		utenti = R.utenti()
		self.assertEqual(utenti["medico"]["email"], "andrea.conti@example.com")
		self.assertTrue(all(R.della_simulazione(u["email"]) for u in utenti.values()))
		self.assertTrue(all(R.della_simulazione(p.email) for p in R.PERSONE))

	def test_le_persone_vere_dello_staging(self):
		"""The staging guide's JSON names the real team: what it leaves out stays the
		simulation's."""
		utenti = R.utenti(
			{"segreteria": {"email": " Anna.Front@Centro.it ", "first_name": "Anna", "last_name": "Front"}}
		)
		self.assertEqual(
			utenti["segreteria"],
			{"email": "anna.front@centro.it", "first_name": "Anna", "last_name": "Front"},
		)
		self.assertEqual(utenti["dentista"]["email"], "stefano.bruno@example.com")

	def test_un_json_sbagliato_e_rifiutato(self):
		with self.assertRaises(ValueError):
			R.utenti({"chirurgo": {"email": "x@y.it"}})
		with self.assertRaises(ValueError):
			R.utenti({"medico": {"first_name": "Senza indirizzo"}})
		with self.assertRaises(ValueError):
			R.utenti({"medico": {"email": "uno@y.it"}, "dentista": {"email": "uno@y.it"}})

	def test_i_codici_fiscali_sono_validi_e_di_nessuno(self):
		from crm.invoicing.engine import codice_fiscale as cf

		codici = [R.codice_fiscale(p) for p in R.PERSONE]
		self.assertEqual(len(set(codici)), len(codici))
		for codice in codici:
			self.assertTrue(cf.valido(codice), codice)
			# born at «Y»: no town nor country
			self.assertEqual(codice[11], "Y")
		self.assertEqual(R.codice_fiscale(R.persona("giulia"))[9:11], "52")

	def test_della_simulazione(self):
		self.assertTrue(R.della_simulazione("x@example.com"))
		self.assertTrue(R.della_simulazione("x@pec.example.com"))
		self.assertFalse(R.della_simulazione("x@example.com.evil.it"))
		self.assertFalse(R.della_simulazione("mario@gmail.com"))
		self.assertFalse(R.della_simulazione(None))

	def test_chi_lavora_dove(self):
		"""The medical director visits in Monza on Tuesdays and Thursdays: the week
		sends patients there."""
		turni = R.turni_del_giorno(datetime.date(2026, 10, 13))
		self.assertEqual({sede for _i, _f, sede in turni["medico"]}, {"monza"})
		self.assertNotIn("dentista", turni)
		self.assertIn("dietista", turni)


class IServizi(UnitTestCase):
	def test_quello_che_la_settimana_prova(self):
		self.assertEqual(R.servizio("visita").pagamento, "Deposit")
		self.assertGreater(R.servizio("visita").acconto, 0)
		self.assertEqual(R.servizio("nutrizione").pagamento, "Full price")
		self.assertTrue(R.servizio("nutrizione_online").visita_online)
		self.assertGreater(R.servizio("pilates").posti, 1)
		self.assertTrue(R.servizio("pilates").orari)

	def test_ogni_servizio_ha_chi_lo_fa_e_una_stanza(self):
		stanze = {chiave for chiave, *_resto in R.STANZE}
		for servizio in R.SERVIZI:
			self.assertTrue(set(servizio.chi) <= set(R.RUOLI), servizio.nome)
			self.assertIn(servizio.stanza, stanze, servizio.nome)

	def test_la_convenzione_ha_i_prezzi_di_servizi_che_esistono(self):
		chiavi = {s.chiave for s in R.SERVIZI}
		self.assertTrue(set(R.CONVENZIONE["prezzi"]) <= chiavi)


class LaSettimana(UnitTestCase):
	def test_il_lunedi_dopo(self):
		self.assertEqual(R.lunedi_dopo(datetime.date(2026, 10, 10)), datetime.date(2026, 10, 12))
		# a Monday is never its own week: the next one
		self.assertEqual(R.lunedi_dopo(datetime.date(2026, 10, 12)), datetime.date(2026, 10, 19))
		self.assertEqual(R.lunedi_dopo(datetime.date(2026, 10, 18)), datetime.date(2026, 10, 19))

	def test_una_settimana_senza_feste(self):
		"""The centre is closed on a holiday: the week skips one that has it."""
		# the 8th of December 2026 is a Tuesday: the week of the 7th is skipped
		self.assertEqual(R.lunedi_dopo(datetime.date(2026, 12, 1)), datetime.date(2026, 12, 14))
		# Easter Monday 2027 is the 29th of March
		self.assertEqual(R.pasquetta(2027), datetime.date(2027, 3, 29))
		self.assertEqual(R.lunedi_dopo(datetime.date(2027, 3, 25)), datetime.date(2027, 4, 5))

	def test_i_giorni(self):
		giorni = R.settimana(datetime.date(2026, 10, 12))
		self.assertEqual(list(giorni), list(R.SETTIMANA))
		self.assertEqual(giorni["sabato"], datetime.date(2026, 10, 17))
		with self.assertRaises(ValueError):
			R.settimana(datetime.date(2026, 10, 13))


class IlCentroIntero(UnitTestCase):
	def _foto(self) -> dict:
		utenti = R.utenti()
		return {
			"livelli": {c.ruolo: list(c.livelli) for c in R.SQUADRA},
			"turni": {c.ruolo: bool(c.turni) for c in R.SQUADRA},
			"servizi": {
				s.nome: {
					"staff": [utenti[r]["email"] for r in s.chi],
					"stanze": [s.stanza],
					"online": int(s.online),
					"pagamento": s.pagamento,
					"scheda": s.nome,
				}
				for s in R.SERVIZI
			},
			"azienda": {"nome": "X", "ambiente": "sandbox"},
			"accesi": dict.fromkeys(
				("clinica", "promemoria", "solleciti", "attese", "prenotazione_online", "stripe"), 1
			),
			"sedi": ["a", "b"],
		}

	def test_un_centro_intero_non_ha_problemi(self):
		self.assertEqual(R.problemi(self._foto()), [])

	def test_cosa_manca_e_detto(self):
		foto = self._foto()
		foto["livelli"]["medico"] = ["operatore"]
		foto["turni"]["dentista"] = False
		del foto["servizi"]["Pilates di gruppo"]
		foto["servizi"]["Visita medica"]["pagamento"] = ""
		foto["azienda"]["ambiente"] = "production"
		foto["accesi"]["stripe"] = 0
		problemi = R.problemi(foto)
		self.assertIn("medico: levels ['operatore'] instead of ['direzione', 'operatore']", problemi)
		self.assertIn("dentista: no shifts", problemi)
		self.assertIn("Pilates di gruppo: missing", problemi)
		self.assertIn("Visita medica: paid online ''", problemi)
		self.assertIn("the issuing company is not in test", problemi)
		self.assertIn("stripe: off", problemi)
		# staging connects its own Stripe from the screens
		self.assertNotIn("stripe: off", R.problemi(foto, finti=False))
