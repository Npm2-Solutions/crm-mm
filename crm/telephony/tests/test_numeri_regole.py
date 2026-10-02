# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Italian numbers in the centre's Twilio space, without a site: the kinds, whose
the number is, an area's prefix, the documents Twilio asks and its evaluation,
the files it takes, a month's price, approved documents good for the next number."""

import unittest
from decimal import Decimal

from crm.telephony import numeri_regole as R

PREZZI = [
	{"number_type": "mobile", "base_price": "45.00", "current_price": "40.00"},
	{"number_type": "local", "base_price": "4.25"},
	{"number_type": "toll free", "base_price": "27.00", "current_price": None},
]
RICHIESTE = [
	{"name": "r3", "status": R.IN_VERIFICA, "number_type": "mobile", "end_user_type": "business"},
	{
		"name": "r2",
		"status": R.APPROVATA,
		"number_type": "local",
		"end_user_type": "business",
		"area_code": "02",
	},
	{"name": "r1", "status": R.APPROVATA, "number_type": "mobile", "end_user_type": "business"},
]
DATI = {"business_name": "Centro Aurora srl", "vat_number": "01234567890", "email": "info@aurora.example"}


class ITipi(unittest.TestCase):
	def test_tre_e_cosa_fanno(self):
		self.assertEqual(list(R.TIPI), ["mobile", "local", "toll_free"])
		self.assertTrue(R.TIPI["mobile"].sms)
		self.assertFalse(R.TIPI["mobile"].chiama)
		self.assertTrue(R.TIPI["local"].chiama)
		self.assertTrue(R.TIPI["local"].zona)
		self.assertEqual(R.TIPI["toll_free"].twilio, "toll free")

	def test_un_numero_e_del_suo_tipo(self):
		self.assertTrue(R.del_tipo("+393331234567", "mobile"))
		self.assertFalse(R.del_tipo("+390212345678", "mobile"))
		self.assertTrue(R.del_tipo("+390212345678", "local"))
		self.assertTrue(R.del_tipo("+39800123456", "toll_free"))
		self.assertFalse(R.del_tipo("+4930123456", "local"))
		self.assertFalse(R.del_tipo("", "mobile"))


class LaZona(unittest.TestCase):
	def test_il_prefisso_come_si_scrive(self):
		for scritto in ("02", " 02 ", "+39 02", "0039 02", "39 02"):
			self.assertEqual(R.prefisso(scritto), "02", scritto)
		self.assertEqual(R.prefisso("011"), "011")
		self.assertEqual(R.prefisso("0471"), "0471")

	def test_non_e_un_prefisso(self):
		for scritto in ("", None, "2", "333", "01234", "abc"):
			self.assertEqual(R.prefisso(scritto), "", scritto)

	def test_un_numero_della_zona(self):
		self.assertTrue(R.nella_zona("+390212345678", "02"))
		self.assertFalse(R.nella_zona("+390612345678", "02"))
		# 02 is not 021…: the whole prefix, from the start
		self.assertFalse(R.nella_zona("+39331020000", "02"))
		self.assertFalse(R.nella_zona("+390212345678", ""))


class DiChi(unittest.TestCase):
	def test_una_societa(self):
		self.assertEqual(R.di_chi(DATI), R.AZIENDA)

	def test_un_professionista(self):
		self.assertEqual(R.di_chi({"first_name": "Anna", "last_name": "Bianchi"}), R.PERSONA)

	def test_senza_dati_una_societa(self):
		self.assertEqual(R.di_chi({}), R.AZIENDA)
		self.assertEqual(R.di_chi({"first_name": "Anna"}), R.AZIENDA)


class IlFile(unittest.TestCase):
	def test_quelli_che_twilio_prende(self):
		for nome in ("visura.pdf", "bolletta.JPG", "documento.jpeg", "scan.png"):
			self.assertEqual(R.file_accettato(nome, 1000), "", nome)

	def test_gli_altri(self):
		self.assertIn("PDF", R.file_accettato("visura.docx", 1000))
		self.assertIn("PDF", R.file_accettato("senza-estensione", 1000))
		self.assertIn("5 MB", R.file_accettato("visura.pdf", R.MASSIMO + 1))
		self.assertEqual(R.file_accettato("visura.pdf", R.MASSIMO), "")


class IDocumenti(unittest.TestCase):
	def test_i_campi_con_le_parole_e_i_valori_del_centro(self):
		campi = R.campi_della_regola(
			[
				{"machine_name": "business_name", "friendly_name": "Business Name"},
				{"machine_name": "business_registration_number", "friendly_name": "Registration"},
				{
					"machine_name": "something_new",
					"friendly_name": "Something New",
					"description": "Twilio's",
				},
				{"machine_name": "address_sids", "friendly_name": "Address"},
			],
			DATI,
		)
		self.assertEqual(
			[c["name"] for c in campi], ["business_name", "business_registration_number", "something_new"]
		)
		self.assertEqual(
			campi[0],
			{
				"name": "business_name",
				"label": "Business name",
				"description": "",
				"known": True,
				"value": "Centro Aurora srl",
			},
		)
		self.assertEqual(campi[1]["value"], "01234567890")
		# a field DottorCloud does not know keeps Twilio's words
		self.assertEqual(
			(campi[2]["label"], campi[2]["description"], campi[2]["known"]),
			("Something New", "Twilio's", False),
		)

	def test_ogni_requisito_con_i_documenti_che_lo_soddisfano(self):
		documenti = R.documenti_della_regola(
			[
				[
					{
						"name": "Address",
						"requirement_name": "address_info",
						"accepted_documents": [
							{
								"name": "Address Validation",
								"type": "address",
								"detailed_fields": [{"machine_name": "address_sids"}],
							}
						],
					}
				],
				{
					"name": "Registration",
					"requirement_name": "registration_info",
					"accepted_documents": [
						{"name": "Mystery", "type": "mystery", "detailed_fields": []},
						{
							"name": "Business Registration",
							"type": "business_registration",
							"detailed_fields": [
								{"machine_name": "business_name"},
								{"machine_name": "document_number"},
							],
						},
					],
				},
			],
			DATI,
		)
		self.assertEqual([d["requirement"] for d in documenti], ["address_info", "registration_info"])
		(indirizzo,) = documenti[0]["accepted"]
		self.assertTrue(indirizzo["address"])
		self.assertEqual(indirizzo["fields"], ["address_sids"])
		self.assertEqual(indirizzo["inputs"], [])
		# what a centre has to hand first, in words
		visura, mistero = documenti[1]["accepted"]
		self.assertEqual(visura["label"], "Business register extract (visura camerale)")
		self.assertEqual(mistero["label"], "Mystery")
		self.assertEqual([c["name"] for c in visura["inputs"]], ["business_name", "document_number"])
		self.assertEqual(visura["inputs"][0]["value"], "Centro Aurora srl")
		self.assertTrue(R.chiede_l_indirizzo([indirizzo]))
		self.assertFalse(R.chiede_l_indirizzo([visura]))

	def test_due_documenti_con_lo_stesso_nome_sono_una_scelta(self):
		(registro,) = R.documenti_della_regola(
			[
				{
					"name": "Registration",
					"requirement_name": "registration_info",
					"accepted_documents": [
						{"name": "Business Registration", "type": "business_registration"},
						{"name": "Excerpt", "type": "commercial_registrar_excerpt"},
						{"name": "Tax Notice", "type": "tax_notice"},
					],
				}
			]
		)
		self.assertEqual([d["type"] for d in registro["accepted"]], ["business_registration", "tax_notice"])


class LaValutazione(unittest.TestCase):
	def test_cosa_manca_riga_per_riga(self):
		righe = R.errori_della_valutazione(
			[
				{"passed": True, "requirement_friendly_name": "Business"},
				{
					"passed": False,
					"requirement_friendly_name": "Business",
					"invalid": [
						{
							"friendly_name": "Business Name",
							"object_field": "business_name",
							"failure_reason": "It is missing.",
						},
						{
							"friendly_name": "Odd Field",
							"object_field": "odd_field",
							"failure_reason": "Wrong.",
						},
					],
				},
				{
					"passed": False,
					"requirement_friendly_name": "Address",
					"failure_reason": "A document is missing.",
				},
				{
					"passed": False,
					"requirement_friendly_name": "Address",
					"failure_reason": "A document is missing.",
				},
			],
			{"business_name": "Ragione sociale"},
		)
		self.assertEqual(
			righe,
			[
				"Business · Ragione sociale · It is missing.",
				"Business · Odd Field · Wrong.",
				"Address · A document is missing.",
			],
		)

	def test_niente_quando_passa(self):
		self.assertEqual(R.errori_della_valutazione([{"passed": True}]), [])
		self.assertEqual(R.errori_della_valutazione(None), [])


class LoStato(unittest.TestCase):
	def test_dagli_stati_di_twilio(self):
		self.assertEqual(R.stato_della_richiesta("draft"), R.BOZZA)
		self.assertEqual(R.stato_della_richiesta("pending-review"), R.IN_VERIFICA)
		self.assertEqual(R.stato_della_richiesta("in-review"), R.IN_VERIFICA)
		self.assertEqual(R.stato_della_richiesta("twilio-approved"), R.APPROVATA)
		self.assertEqual(R.stato_della_richiesta("provisionally-approved"), R.APPROVATA)
		self.assertEqual(R.stato_della_richiesta("twilio-rejected"), R.RIFIUTATA)
		self.assertEqual(R.stato_della_richiesta(None), R.BOZZA)

	def test_cosa_si_fa_in_ogni_stato(self):
		self.assertTrue(R.si_compra(R.APPROVATA))
		self.assertFalse(R.si_compra(R.IN_VERIFICA))
		self.assertTrue(R.si_rimanda(R.BOZZA))
		self.assertTrue(R.si_rimanda(R.RIFIUTATA))
		self.assertFalse(R.si_rimanda(R.IN_VERIFICA))
		self.assertFalse(R.si_rimanda(R.APPROVATA))


class IlPrezzo(unittest.TestCase):
	def test_il_prezzo_di_oggi_altrimenti_quello_di_base(self):
		self.assertEqual(R.prezzo_al_mese(PREZZI, "mobile"), Decimal("40.00"))
		self.assertEqual(R.prezzo_al_mese(PREZZI, "local"), Decimal("4.25"))
		self.assertEqual(R.prezzo_al_mese(PREZZI, "toll_free"), Decimal("27.00"))

	def test_nessun_prezzo(self):
		self.assertIsNone(R.prezzo_al_mese([], "mobile"))
		self.assertIsNone(R.prezzo_al_mese([{"number_type": "national", "base_price": "1"}], "mobile"))


class IDocumentiGiaApprovati(unittest.TestCase):
	def test_valgono_per_un_altro_numero_dello_stesso_tipo(self):
		self.assertEqual(R.riusabile(RICHIESTE, "mobile", "business")["name"], "r1")

	def test_non_per_un_altro_tipo_o_un_altro_titolare(self):
		self.assertIsNone(R.riusabile(RICHIESTE, "toll_free", "business"))
		self.assertIsNone(R.riusabile(RICHIESTE, "mobile", "individual"))

	def test_un_geografico_solo_della_stessa_zona(self):
		self.assertEqual(R.riusabile(RICHIESTE, "local", "business", "+39 02")["name"], "r2")
		self.assertIsNone(R.riusabile(RICHIESTE, "local", "business", "06"))
