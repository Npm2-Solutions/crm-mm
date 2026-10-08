# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Appointments from the previous software, without a site: the columns, a day and
an hour as an Italian sheet writes them, how it went, the key that brings a row in
once, a professional found by name."""

import datetime
import unittest

from crm.importazione import appuntamenti_regole as R
from crm.importazione import regole

ADESSO = datetime.datetime(2026, 10, 8, 12, 0)
INTESTAZIONE = [
	"Paziente",
	"Codice Fiscale",
	"Data",
	"Ora",
	"Durata",
	"Prestazione",
	"Medico",
	"Stato",
	"Note",
]


class LeColonne(unittest.TestCase):
	def test_dell_appuntamento_e_della_persona(self):
		mappa = R.riconosci([*INTESTAZIONE, "Ambulatorio", "Ora fine", "ID"])
		self.assertEqual(
			sorted(mappa.values()),
			sorted(
				[
					"full_name",
					"fiscal_code",
					"date",
					"start",
					"duration",
					"service",
					"professional",
					"status",
					"notes",
					"room",
					"end",
					"external_id",
				]
			),
		)

	def test_le_note_sono_dell_appuntamento(self):
		self.assertEqual(R.riconosci(["Nome", "Cognome", "Note"])[2], "notes")


class LOra(unittest.TestCase):
	def test_come_la_scrive_un_foglio(self):
		for valore, atteso in (
			("9:30", (9, 30)),
			("09.30", (9, 30)),
			("9,30", (9, 30)),
			("9h30", (9, 30)),
			("09:30:00", (9, 30)),
			("930", (9, 30)),
			("16", (16, 0)),
			(0.375, (9, 0)),
			(14, (14, 0)),
			(datetime.time(10, 15, 20), (10, 15)),
			(datetime.datetime(2025, 3, 2, 11, 45), (11, 45)),
			(datetime.timedelta(hours=8, minutes=5), (8, 5)),
		):
			self.assertEqual(R.ora(valore), datetime.time(*atteso), valore)

	def test_vuota_o_sbagliata(self):
		self.assertIsNone(R.ora(""))
		for valore in ("25:00", "9:75", "mattina", 30):
			with self.assertRaises(ValueError):
				R.ora(valore)


class LaDurata(unittest.TestCase):
	def test_in_minuti(self):
		for valore, atteso in (
			("45", 45),
			("45 min", 45),
			("45'", 45),
			("1h", 60),
			("1h30", 90),
			("1:30", 90),
			("1 ora", 60),
			("90 minuti", 90),
			(30, 30),
			(30.0, 30),
			(1 / 48, 30),
			(datetime.time(0, 50), 50),
		):
			self.assertEqual(R.durata(valore), atteso, valore)

	def test_vuota_o_sbagliata(self):
		self.assertIsNone(R.durata(None))
		for valore in ("tanto", "0", -5, "2 giorni"):
			with self.assertRaises(ValueError):
				R.durata(valore)


class LoStato(unittest.TestCase):
	def test_dalle_parole(self):
		self.assertEqual(R.stato("Disdetto dal paziente", True), R.ANNULLATO)
		self.assertEqual(R.stato("NON PRESENTATO", True), R.ASSENTE)
		self.assertEqual(R.stato("Non si è presentata", True), R.ASSENTE)
		self.assertEqual(R.stato("Annullata", False), R.ANNULLATO)

	def test_dall_orologio(self):
		self.assertEqual(R.stato("Eseguito", True), R.SVOLTO)
		self.assertEqual(R.stato("Prenotato", True), R.SVOLTO)
		self.assertEqual(R.stato("", True), R.SVOLTO)
		self.assertEqual(R.stato("Eseguito", False), R.PRENOTATO)
		self.assertEqual(R.stato(None, False), R.PRENOTATO)


class LaRiga(unittest.TestCase):
	mappa = R.riconosci(INTESTAZIONE)

	def riga(self, *valori):
		return R.appuntamento(list(valori), self.mappa, INTESTAZIONE, ADESSO)

	def test_una_visita_passata(self):
		dati, problemi = self.riga(
			"ROSSI MARIA",
			"RSSMRA80A41H501Y",
			"02/03/2025",
			"9.30",
			"45 min",
			"Visita",
			"Dott. Bianchi",
			"",
			"ok",
		)
		self.assertEqual(problemi, [])
		self.assertEqual(dati["person"]["last_name"], "Rossi")
		self.assertEqual(dati["starts_on"], datetime.datetime(2025, 3, 2, 9, 30))
		self.assertEqual(dati["ends_on"], datetime.datetime(2025, 3, 2, 10, 15))
		self.assertEqual(dati["status"], R.SVOLTO)
		self.assertEqual(
			(dati["service"], dati["professional"], dati["notes"]), ("Visita", "Dott. Bianchi", "ok")
		)

	def test_una_da_venire_senza_durata(self):
		dati, problemi = self.riga("Bianchi Luca", "", "15/12/2026", "16:00", "", "Controllo", "", "", "")
		self.assertEqual(problemi, [])
		self.assertEqual(dati["status"], R.PRENOTATO)
		self.assertEqual(dati["starts_on"], datetime.datetime(2026, 12, 15, 16, 0))
		self.assertIsNone(dati["ends_on"])

	def test_data_e_ora_in_una_colonna(self):
		dati, _p = self.riga("Bianchi Luca", "", datetime.datetime(2025, 1, 7, 8, 0), "", "", "", "", "", "")
		self.assertEqual(dati["starts_on"], datetime.datetime(2025, 1, 7, 8, 0))
		dati, _p = self.riga("Bianchi Luca", "", "07/01/2025 08:15", "", "", "", "", "", "")
		self.assertEqual(dati["starts_on"], datetime.datetime(2025, 1, 7, 8, 15))

	def test_quello_che_non_va(self):
		dati, problemi = self.riga("", "", "31/02/2025", "mattina", "tanto", "", "", "", "")
		self.assertIn((regole.SENZA_NOME, ""), problemi)
		self.assertIn((regole.DATA_SBAGLIATA, "31/02/2025"), problemi)
		self.assertIn((R.ORA_SBAGLIATA, "mattina"), problemi)
		self.assertIn((R.DURATA_SBAGLIATA, "tanto"), problemi)
		self.assertTrue(R.da_lasciare(dati, problemi))

	def test_senza_ora_resta_fuori(self):
		dati, problemi = self.riga("Bianchi Luca", "", "07/01/2025", "", "", "", "", "", "")
		self.assertIn((R.SENZA_ORA, ""), problemi)
		self.assertTrue(R.da_lasciare(dati, problemi))

	def test_una_durata_sbagliata_non_ferma(self):
		dati, problemi = self.riga("Bianchi Luca", "", "07/01/2025", "9", "tanto", "", "", "", "")
		self.assertFalse(R.da_lasciare(dati, problemi))

	def test_finisce_prima_di_cominciare(self):
		intestazione = ["Nome", "Cognome", "Data", "Dalle", "Alle"]
		dati, problemi = R.appuntamento(
			["Luca", "Bianchi", "07/01/2025", "10:00", "09:00"],
			R.riconosci(intestazione),
			intestazione,
			ADESSO,
		)
		self.assertIn((R.FINE_PRIMA, ""), problemi)
		self.assertIsNone(dati["ends_on"])
		self.assertFalse(R.da_lasciare(dati, problemi))


class LaChiave(unittest.TestCase):
	def test_il_codice_di_prima_vince(self):
		a = {"external_id": "A-12", "starts_on": datetime.datetime(2025, 1, 1, 9)}
		b = {"external_id": "a 12", "starts_on": datetime.datetime(2025, 2, 1, 9)}
		self.assertEqual(R.chiave(a), R.chiave(b))

	def test_persona_momento_servizio(self):
		base = {
			"person": {"fiscal_code": "RSSMRA80A41H501Y", "first_name": "Maria"},
			"starts_on": datetime.datetime(2025, 3, 2, 9, 30),
			"service": "Visita",
		}
		self.assertEqual(R.chiave(base), R.chiave({**base, "service": "VISITA"}))
		self.assertNotEqual(
			R.chiave(base), R.chiave({**base, "starts_on": datetime.datetime(2025, 3, 2, 10)})
		)
		solo_nome = {**base, "person": {"first_name": "Maria", "last_name": "Rossi"}}
		self.assertNotEqual(R.chiave(base), R.chiave(solo_nome))
		self.assertEqual(len(R.chiave(base)), 32)


UTENTI = {
	"mario@x.it": ["Mario Rossi", "mario@x.it"],
	"anna@x.it": ["Anna Bianchi", "anna@x.it"],
	"paolo@x.it": ["Paolo Bianchi", "paolo@x.it"],
}


class LAbbinamento(unittest.TestCase):
	def test_per_nome_intero_email_o_cognome(self):
		self.assertEqual(R.abbina("Dott. Mario Rossi", UTENTI), "mario@x.it")
		self.assertEqual(R.abbina("DOTT.SSA ANNA BIANCHI", UTENTI), "anna@x.it")
		self.assertEqual(R.abbina("anna@x.it", UTENTI), "anna@x.it")
		self.assertEqual(R.abbina("Rossi", UTENTI), "mario@x.it")

	def test_mai_tra_due(self):
		self.assertIsNone(R.abbina("Bianchi", UTENTI))
		self.assertIsNone(R.abbina("Dott.", UTENTI))
		self.assertIsNone(R.abbina("Verdi", UTENTI))


class LaPersonaPerNomeENascita(unittest.TestCase):
	def test_una_chiave_in_piu(self):
		chiavi = regole.chiavi(
			{"first_name": "Maria", "last_name": "Rossi", "birth_date": datetime.date(1980, 1, 2)}
		)
		self.assertEqual(chiavi, [("name_birth", "maria|rossi|1980-01-02")])


if __name__ == "__main__":
	unittest.main()
