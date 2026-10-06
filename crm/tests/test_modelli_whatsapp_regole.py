# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A WhatsApp template without a site (`modelli_regole`): which numbers send it,
its buttons by Meta's rules, Meta's description of it read into our fields."""

import unittest

from crm.integrations.whatsapp import modelli_regole as R

NUMERI = [
	{"name": "Centro", "waba": "111"},
	{"name": "Centro bis", "waba": "111"},
	{"name": "Studio", "waba": "222"},
	{"name": "A mano", "waba": ""},
]


class UnModelloStaSullAccount(unittest.TestCase):
	def test_lo_mandano_tutti_i_numeri_del_suo_account(self):
		self.assertEqual(R.numeri_che_possono("Centro", NUMERI, "Studio"), ["Centro", "Centro bis"])
		self.assertEqual(R.numeri_che_possono("Studio", NUMERI, "Centro"), ["Studio"])

	def test_senza_account_scritto_parte_dal_numero_che_invia(self):
		self.assertEqual(R.numeri_che_possono(None, NUMERI, "Studio"), ["Studio"])
		self.assertEqual(R.numeri_che_possono("", NUMERI, None), [])

	def test_un_numero_senza_account_noto_manda_solo_i_suoi(self):
		self.assertEqual(R.numeri_che_possono("A mano", NUMERI, None), ["A mano"])

	def test_un_numero_che_non_c_e_non_manda_niente(self):
		self.assertEqual(R.numeri_che_possono("Sparito", NUMERI, "Centro"), [])

	def test_due_numeri_dello_stesso_account_mandano_gli_stessi(self):
		self.assertTrue(R.stesso_account("Centro", "Centro bis", NUMERI))
		self.assertTrue(R.stesso_account("Studio", "Studio", NUMERI))
		self.assertFalse(R.stesso_account("Centro", "Studio", NUMERI))
		# nobody wrote it down: it goes out from whichever number sends
		self.assertTrue(R.stesso_account(None, "Studio", NUMERI))


class IPulsanti(unittest.TestCase):
	def frasi(self, pulsanti):
		return [problema.testo() for problema in R.problemi_dei_pulsanti(pulsanti)]

	def test_una_risposta_un_link_e_una_chiamata_vanno_bene(self):
		pulsanti = [
			{"type": "QUICK_REPLY", "text": "Confermo"},
			{"type": "URL", "text": "Gestisci", "url": "https://centro.example.com/prenota"},
			{"type": "PHONE_NUMBER", "text": "Chiama", "phone": "+39 02 1234567"},
		]
		self.assertEqual(self.frasi(pulsanti), [])

	def test_le_parole_ci_sono_e_stanno_in_venticinque_caratteri(self):
		self.assertEqual(
			self.frasi([{"type": "QUICK_REPLY", "text": "  "}]), ["Button 1: write what it says"]
		)
		self.assertEqual(
			self.frasi([{"type": "QUICK_REPLY", "text": "x" * 26}]), ["Button 1: at most 25 characters"]
		)

	def test_due_pulsanti_con_le_stesse_parole_non_si_distinguono(self):
		self.assertEqual(
			self.frasi([{"type": "QUICK_REPLY", "text": "Sì"}, {"type": "QUICK_REPLY", "text": "sì"}]),
			["Two buttons say «sì»"],
		)

	def test_i_limiti_di_meta(self):
		self.assertIn(
			"A template has at most 10 buttons",
			self.frasi([{"type": "QUICK_REPLY", "text": str(numero)} for numero in range(11)]),
		)
		link = {"type": "URL", "url": "https://example.com"}
		self.assertIn(
			"At most 2 buttons open a link",
			self.frasi([{**link, "text": "a"}, {**link, "text": "b"}, {**link, "text": "c"}]),
		)
		chiama = {"type": "PHONE_NUMBER", "phone": "+390212345678"}
		self.assertIn(
			"Only one button can call", self.frasi([{**chiama, "text": "a"}, {**chiama, "text": "b"}])
		)

	def test_un_link_e_un_numero_scritti_come_vuole_meta(self):
		self.assertEqual(
			self.frasi([{"type": "URL", "text": "Apri", "url": "centro.example.com"}]),
			["Button 1: the link starts with https://"],
		)
		self.assertEqual(
			self.frasi([{"type": "PHONE_NUMBER", "text": "Chiama", "phone": "02 1234567"}]),
			["Button 1: write the number with its country code, as +39 02 1234567"],
		)

	def test_un_link_che_cambia_vuole_il_suo_esempio(self):
		self.assertEqual(
			self.frasi([{"type": "URL", "text": "Apri", "url": "https://e.it/{{1}}"}]),
			["Button 1: Meta wants an example of the link"],
		)
		self.assertEqual(
			self.frasi(
				[{"type": "URL", "text": "Apri", "url": "https://e.it/{{1}}", "example": "https://e.it/a"}]
			),
			[],
		)

	def test_un_tipo_che_non_si_scrive_qui(self):
		self.assertEqual(self.frasi([{"type": "FLOW", "text": "Prenota"}]), ["Button 1: choose what it does"])

	def test_le_risposte_rapide_vengono_prima(self):
		pulsanti = [
			{"type": "URL", "text": "Link"},
			{"type": "QUICK_REPLY", "text": "Sì"},
			{"type": "PHONE_NUMBER", "text": "Chiama"},
			{"type": "QUICK_REPLY", "text": "No"},
		]
		self.assertEqual(
			[pulsante["text"] for pulsante in R.pulsanti_in_ordine(pulsanti)], ["Sì", "No", "Link", "Chiama"]
		)

	def test_andata_e_ritorno_dalle_righe_di_frappe_whatsapp(self):
		pulsanti = [
			{"type": "PHONE_NUMBER", "text": "Chiama", "phone": "+39 02 1234567"},
			{"type": "QUICK_REPLY", "text": "Confermo"},
			{"type": "URL", "text": "Gestisci", "url": "https://example.com/p"},
		]
		righe = R.righe_dei_pulsanti(pulsanti)
		self.assertEqual(
			[riga["button_type"] for riga in righe], ["Quick Reply", "Call Phone", "Visit Website"]
		)
		self.assertEqual(righe[1]["phone_number"], "+39021234567")
		self.assertEqual(righe[2]["url_type"], "Static")
		self.assertEqual(
			R.pulsanti_delle_righe(righe),
			[
				{"type": "QUICK_REPLY", "text": "Confermo"},
				{"type": "PHONE_NUMBER", "text": "Chiama", "phone": "+39021234567"},
				{"type": "URL", "text": "Gestisci", "url": "https://example.com/p", "dynamic": False},
			],
		)

	def test_un_link_che_cambia_resta_com_e(self):
		"""One brought in from Meta, its last part a variable: kept with its example."""
		righe = R.righe_dei_pulsanti(
			[
				{
					"type": "URL",
					"text": "Gestisci",
					"url": "https://example.com/{{1}}",
					"dynamic": True,
					"example": "https://example.com/abc",
				}
			]
		)
		self.assertEqual(righe[0]["url_type"], "Dynamic")
		self.assertEqual(righe[0]["example_url"], "https://example.com/abc")


#: a template as `GET /<WABA>/message_templates` describes it
MODELLO = {
	"id": "9001",
	"name": "promemoria",
	"status": "APPROVED",
	"category": "UTILITY",
	"language": "it",
	"components": [
		{"type": "HEADER", "format": "TEXT", "text": "Promemoria"},
		{
			"type": "BODY",
			"text": "Ciao {{1}}, domani alle {{2}}.",
			"example": {"body_text": [["Marco", "10:00"]]},
		},
		{"type": "FOOTER", "text": "Centro Aurora"},
		{
			"type": "BUTTONS",
			"buttons": [
				{"type": "QUICK_REPLY", "text": "Confermo"},
				{
					"type": "URL",
					"text": "Gestisci",
					"url": "https://e.it/{{1}}",
					"example": ["https://e.it/x"],
				},
				{"type": "PHONE_NUMBER", "text": "Chiama", "phone_number": "+39021234567"},
				{"type": "OTP", "text": "Copia"},
			],
		},
	],
}


class DaMeta(unittest.TestCase):
	def test_si_legge_nei_nostri_campi(self):
		valori = R.da_meta(MODELLO)
		self.assertEqual(valori["id"], "9001")
		self.assertEqual(valori["actual_name"], "promemoria")
		self.assertEqual(valori["language_code"], "it")
		self.assertEqual((valori["header_type"], valori["header"]), ("TEXT", "Promemoria"))
		self.assertEqual(valori["template"], "Ciao {{1}}, domani alle {{2}}.")
		self.assertEqual(valori["sample_values"], "Marco,10:00")
		self.assertEqual(valori["footer"], "Centro Aurora")

	def test_i_pulsanti_come_le_righe_di_frappe_whatsapp(self):
		righe = R.da_meta(MODELLO)["buttons"]
		# a kind frappe_whatsapp has no row for is left out
		self.assertEqual(
			[riga["button_type"] for riga in righe], ["Quick Reply", "Visit Website", "Call Phone"]
		)
		self.assertEqual(righe[1]["url_type"], "Dynamic")
		self.assertEqual(righe[1]["example_url"], "https://e.it/x")
		self.assertEqual(righe[2]["phone_number"], "+39021234567")

	def test_senza_esempi_le_variabili_hanno_il_loro_numero(self):
		"""frappe_whatsapp sends as many values as there are examples: none would
		leave {{1}} empty and Meta refuse the message."""
		self.assertEqual(R.esempi("Ciao {{1}} e {{2}}, {{1}}", None), "1,2")
		self.assertEqual(R.esempi("Ciao", []), "")

	def test_un_immagine_in_testa(self):
		valori = R.da_meta({"components": [{"type": "HEADER", "format": "IMAGE"}]})
		self.assertEqual((valori["header_type"], valori["header"]), ("IMAGE", ""))

	def test_la_lingua_come_la_chiama_il_framework(self):
		lingue = {"it", "en-US", "pt-BR", "de"}
		self.assertEqual(R.lingua("it", lingue), "it")
		self.assertEqual(R.lingua("en_US", lingue), "en-US")
		self.assertEqual(R.lingua("de_DE", lingue), "de")
		self.assertIsNone(R.lingua("xx_YY", lingue))
		self.assertIsNone(R.lingua("", lingue))


class ISpariti(unittest.TestCase):
	def test_solo_quelli_che_meta_conosceva_e_non_ha_piu(self):
		locali = [
			{"name": "a", "id": "1", "status": "APPROVED"},
			{"name": "b", "id": "2", "status": "APPROVED"},
			{"name": "c", "id": None, "status": "PENDING"},
			{"name": "d", "id": "4", "status": "DELETED"},
		]
		self.assertEqual(R.spariti(locali, {"1"}), ["b"])


if __name__ == "__main__":
	unittest.main()
