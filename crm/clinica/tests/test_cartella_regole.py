# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a visit copies of the last one, without a site."""

import unittest

from crm.clinica import cartella_regole as R

SCHEDA = {
	"sections": [
		{
			"id": "s",
			"title": "Visita",
			"fields": [
				{"id": "allergie", "type": "text", "label": "Allergie"},
				{"id": "peso", "type": "number", "label": "Peso"},
				{"id": "bmi", "type": "calc", "label": "BMI", "formula": "peso / 2"},
				{"id": "fumo", "type": "yesno", "label": "Fuma"},
				{"id": "foto", "type": "attachment", "label": "Foto"},
				{"id": "firma", "type": "signature", "label": "Firma", "signer": "patient"},
				{"id": "ok", "type": "consent", "label": "Consenso", "consent_type": "privacy"},
			],
		}
	]
}


class DallUltimaVisita(unittest.TestCase):
	def test_le_risposte_si_ma_mai_le_prove_della_visita(self):
		ultima = {
			"allergie": "Nichel",
			"peso": 64.5,
			"bmi": 32.25,
			"fumo": False,
			"foto": ["/private/files/a.jpg"],
			"firma": "data:image/png;base64,AAA",
			"ok": True,
		}
		copia = R.da_ricopiare(SCHEDA, ultima)
		# the calculation is worked out again, never copied
		self.assertEqual(copia, {"allergie": "Nichel", "peso": 64.5, "bmi": 32.25, "fumo": False})

	def test_quello_che_la_nuova_versione_non_chiede_cade(self):
		copia = R.da_ricopiare(SCHEDA, {"allergie": "Nichel", "esame": "Nella norma", "peso": "molto"})
		self.assertEqual(copia, {"allergie": "Nichel"})

	def test_niente_da_copiare(self):
		self.assertEqual(R.da_ricopiare(SCHEDA, None), {})


if __name__ == "__main__":
	unittest.main()
