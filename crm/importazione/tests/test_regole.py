# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import datetime
import unittest

from crm.importazione import regole as R


class LeColonne(unittest.TestCase):
	def test_si_riconoscono_dal_nome_comunque_scritto(self):
		intestazione = [
			"ID",
			"Cognome",
			"Nome",
			"Data di Nascita",
			"C.F.",
			"Cellulare",
			"E-mail",
			"Città",
			"Colonna X",
		]
		self.assertEqual(
			R.riconosci(intestazione),
			{
				0: "external_id",
				1: "last_name",
				2: "first_name",
				3: "birth_date",
				4: "fiscal_code",
				5: "mobile_no",
				6: "email",
				7: "city",
			},
		)

	def test_ogni_campo_una_volta(self):
		self.assertEqual(R.riconosci(["Telefono", "Tel"]), {0: "phone"})


class IValori(unittest.TestCase):
	def test_le_date_come_le_scrive_un_foglio_italiano(self):
		self.assertEqual(R.data("02/01/1980"), datetime.date(1980, 1, 2))
		self.assertEqual(R.data("2-1-80"), datetime.date(1980, 1, 2))
		self.assertEqual(R.data("1980-01-02"), datetime.date(1980, 1, 2))
		self.assertEqual(R.data(29222), datetime.date(1980, 1, 2))
		self.assertIsNone(R.data(""))
		with self.assertRaises(ValueError):
			R.data("ieri")

	def test_i_numeri_col_prefisso(self):
		self.assertEqual(R.telefono("333 123 4567"), "+393331234567")
		self.assertEqual(R.telefono("3331234567.0"), "+393331234567")
		self.assertEqual(R.telefono("06 1234567"), "+39061234567")
		self.assertEqual(R.telefono("0041 79 123 45 67"), "+41791234567")
		self.assertEqual(R.telefono("+39 333-1234567"), "+393331234567")
		self.assertEqual(R.ultime_nove("+39 333 123 4567"), "331234567")

	def test_il_codice_fiscale_dice_sesso_e_nascita(self):
		# Mario Rossi, 1 gennaio 1980; Maria, 41 = 1 + 40
		self.assertEqual(R.nascita_dal_codice("RSSMRA80A01H501U"), datetime.date(1980, 1, 1))
		self.assertEqual(R.sesso("", "RSSMRA80A01H501U"), "M")
		self.assertEqual(R.sesso("", "RSSMRA80A41H501Y"), "F")
		self.assertEqual(R.sesso("Femmina"), "F")

	def test_i_nomi_in_maiuscolo(self):
		self.assertEqual(R.nome_proprio("ROSSI"), "Rossi")
		self.assertEqual(R.nome_proprio("de luca"), "De Luca")
		self.assertEqual(R.nome_proprio("McDonald"), "McDonald")
		self.assertEqual(R.nome_proprio("D'AMICO ROSA"), "D'Amico Rosa")
		self.assertEqual(R.nome_proprio("rossi-bianchi"), "Rossi-Bianchi")


class UnaRiga(unittest.TestCase):
	def test_il_nominativo_col_cognome_prima(self):
		intestazione = ["Nominativo", "Codice fiscale", "Telefono"]
		dati, problemi = R.persona(
			["ROSSI MARIA GRAZIA", "rssmra80a41h501y", "333 1234567"], R.riconosci(intestazione), intestazione
		)
		self.assertEqual((dati["first_name"], dati["last_name"]), ("Maria Grazia", "Rossi"))
		self.assertEqual(dati["fiscal_code"], "RSSMRA80A41H501Y")
		self.assertEqual(dati["birth_date"], datetime.date(1980, 1, 1))
		self.assertEqual(dati["sex"], "F")
		# a mobile in the only column of numbers
		self.assertEqual((dati["mobile_no"], dati["phone"]), ("+393331234567", ""))
		self.assertEqual(problemi, [])

	def test_quello_che_non_va_si_dice(self):
		intestazione = ["Nome", "Email", "Codice fiscale", "Data di nascita"]
		dati, problemi = R.persona(
			["", "non una mail", "ABC", "ieri"], R.riconosci(intestazione), intestazione
		)
		self.assertEqual(
			[frase for frase, _ in problemi],
			[R.SENZA_NOME, R.EMAIL_SBAGLIATA, R.CF_SBAGLIATO, R.DATA_SBAGLIATA],
		)
		self.assertEqual((dati["email"], dati["fiscal_code"]), ("", ""))

	def test_chi_c_e_gia_si_trova_dal_piu_sicuro(self):
		self.assertEqual(
			R.chiavi(
				{"fiscal_code": "RSSMRA80A01H501U", "email": "m@example.com", "mobile_no": "+393331234567"}
			),
			[("fiscal_code", "RSSMRA80A01H501U"), ("email", "m@example.com"), ("mobile_no", "331234567")],
		)
		self.assertEqual(R.chiavi({"email": "", "mobile_no": ""}), [])


if __name__ == "__main__":
	unittest.main()
