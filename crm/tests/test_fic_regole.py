# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Fatture in Cloud without a site (`crm.invoicing.fic.regole`): which of the
company's VAT rates and accounts stands for ours, what an invoice is handed over
as, the totals compared to the cent, the states."""

import unittest
from decimal import Decimal

from crm.invoicing.fic import regole as R

TIPI = [
	{"id": 0, "value": 22, "description": "Ordinaria", "ei_type": "", "default": True},
	{"id": 3, "value": 10, "description": "Ridotta", "ei_type": ""},
	{"id": 12, "value": 0, "description": "Esente art. 10", "ei_type": "N4"},
	{"id": 13, "value": 0, "description": "Esente art. 10 n. 18", "ei_type": "N4"},
	{"id": 21, "value": 0, "description": "Escluso art. 15", "ei_type": "N1"},
	{"id": 30, "value": 0, "description": "Non soggetto vecchio", "ei_type": "N2", "is_disabled": True},
]


class LeAliquote(unittest.TestCase):
	def test_la_chiave_dice_aliquota_e_natura(self):
		self.assertEqual(R.chiave_iva(22), "22")
		self.assertEqual(R.chiave_iva("22.00"), "22")
		self.assertEqual(R.chiave_iva(5.5), "5.5")
		self.assertEqual(R.chiave_iva(0, "N4"), "0|N4")
		self.assertEqual(R.dividi_chiave("0|N2.2"), (Decimal("0"), "N2.2"))

	def test_i_candidati_hanno_la_stessa_aliquota_e_senza_imposta_la_stessa_natura(self):
		self.assertEqual([t["id"] for t in R.candidati("22", TIPI)], [0])
		self.assertEqual([t["id"] for t in R.candidati("0|N4", TIPI)], [12, 13])
		self.assertEqual([t["id"] for t in R.candidati("0|N1", TIPI)], [21])
		# a switched-off one is never offered
		self.assertEqual(R.candidati("0|N2", TIPI), [])

	def test_si_sceglie_da_soli_solo_dove_uno_solo_puo_essere(self):
		self.assertEqual(R.scegli_tipo("22", TIPI), 0)
		self.assertEqual(R.scegli_tipo("0|N1", TIPI), 21)
		# two exemptions and neither the default: the centre chooses
		self.assertIsNone(R.scegli_tipo("0|N4", TIPI))
		self.assertEqual(R.scegli_tipo("0|N4", TIPI, scelto=13), 13)
		# a choice no longer among them is not kept
		self.assertIsNone(R.scegli_tipo("0|N4", TIPI, scelto=0))
		self.assertIsNone(R.scegli_tipo("4", TIPI))


CONTI = [
	{"id": 1, "name": "Cassa contanti", "type": "standard"},
	{"id": 2, "name": "POS Nexi", "type": "standard"},
	{"id": 3, "name": "Intesa", "type": "bank"},
]


class IConti(unittest.TestCase):
	def test_il_conto_dal_suo_nome(self):
		self.assertEqual(R.conto_suggerito("MP01", CONTI), 1)
		self.assertEqual(R.conto_suggerito("MP08", CONTI), 2)
		# a bank account by its kind, where its name says nothing
		self.assertEqual(R.conto_suggerito("MP05", CONTI), 3)
		self.assertIsNone(R.conto_suggerito("MP16", CONTI))

	def test_un_conto_solo_va_bene_per_tutto(self):
		self.assertEqual(R.conto_suggerito("MP08", [{"id": 9, "name": "Unico"}]), 9)

	def test_la_scelta_del_centro_vince(self):
		self.assertEqual(R.conto_suggerito("MP08", CONTI, scelto=3), 3)
		self.assertEqual(R.conto_suggerito("MP08", CONTI, scelto=99), 2)


class LeNumerazioni(unittest.TestCase):
	def test_la_principale_prima(self):
		info = {"numerations": {"2026": {"/S": 4, "": 12, "/E": 2}}}
		self.assertEqual(R.numerazioni(info, 2026), ["", "/E", "/S"])
		self.assertEqual(R.numerazioni({}, 2026), [""])

	def test_il_numero_come_lo_stampa(self):
		self.assertEqual(R.numero_stampato(12, ""), "12")
		self.assertEqual(R.numero_stampato(12, "/S"), "12/S")


MAPPA = {
	"iva": {"22": 0, "0|N4": 12, "0|N1": 21},
	"conti": {"MP08": 2, "MP01": 1},
	"numerazioni": {"sdi": "/E", "carta": "", "note": "/NC"},
}


def fattura(**altro):
	base = {
		"tipo": "TD01",
		"data": "2026-10-06",
		"elettronica": False,
		"marcatore": "DottorCloud · centro.example.com · FATT-0001",
		"destinatario": {
			"tipo": "persona_fisica",
			"nome": "Maria Rossi",
			"nome_proprio": "Maria",
			"cognome": "Rossi",
			"codice_fiscale": "RSSMRA80A41H501U",
			"indirizzo": "Via Roma",
			"civico": "1",
			"cap": "20100",
			"citta": "Milano",
			"provincia": "MI",
			"paese": "IT",
		},
		"righe": [
			{
				"descrizione": "Visita fisiatrica\nPrima visita",
				"quantita": 1,
				"prezzo": 80,
				"sconto": 0,
				"importo": 80,
				"chiave_iva": "0|N4",
				"tipo_spesa": "SP",
				"al_ts": True,
			}
		],
		"chiave_iva_bollo": "0|N4",
		"iva_in_parole": {"0|N4": "Esente (art. 10)", "22": "IVA 22%"},
		"metodi_in_parole": {"MP05": "Bonifico"},
		"bollo": Decimal("2.00"),
		"bollo_riaddebitato": Decimal("2.00"),
		"metodo_pagamento": "MP08",
		"pagamento": {"importo": Decimal("82.00"), "scadenza": "2026-10-06", "pagato_il": "2026-10-06"},
	}
	base.update(altro)
	return base


class LaFattura(unittest.TestCase):
	def test_una_fattura_a_un_paziente_pagata_al_banco(self):
		dati, problemi = R.documento(fattura(), MAPPA)
		self.assertEqual(problemi, [])
		self.assertEqual(dati["type"], "invoice")
		self.assertFalse(dati["e_invoice"])
		self.assertEqual(dati["numeration"], "")
		self.assertEqual(dati["subject"], "DottorCloud · centro.example.com · FATT-0001")
		self.assertEqual(dati["entity"]["type"], "person")
		self.assertEqual((dati["entity"]["first_name"], dati["entity"]["last_name"]), ("Maria", "Rossi"))
		self.assertEqual(dati["entity"]["address_street"], "Via Roma 1")
		self.assertEqual(dati["entity"]["country"], "Italia")
		[voce] = dati["items_list"]
		self.assertEqual((voce["name"], voce["description"]), ("Visita fisiatrica", "Prima visita"))
		self.assertEqual(voce["vat"], {"id": 12})
		# on paper the re-charged duty is what the client is charged
		self.assertEqual(dati["stamp_duty"], 2.0)
		[pagamento] = dati["payments_list"]
		self.assertEqual(pagamento["status"], "paid")
		self.assertEqual(pagamento["payment_account"], {"id": 2})
		self.assertEqual(pagamento["amount"], 82.0)
		# reported from here: Fatture in Cloud sends nothing to the Sistema TS
		self.assertEqual(dati["extra_data"], {"ts_communication": False})
		self.assertNotIn("ei_data", dati)

	def test_elettronica_il_bollo_ripreso_e_una_riga_del_compenso(self):
		dati, problemi = R.documento(
			fattura(
				elettronica=True, metodo_pagamento="MP05", pagamento={"importo": 82, "scadenza": "2026-11-05"}
			),
			MAPPA,
		)
		self.assertEqual(problemi, [])
		self.assertEqual(dati["numeration"], "/E")
		self.assertEqual(dati["stamp_duty"], 2.0)
		bollo = dati["items_list"][-1]
		self.assertEqual(bollo["name"], R.RIGA_BOLLO)
		# Risposta AdE 428/2022: it follows the VAT of the service, not art. 15
		self.assertEqual(bollo["vat"], {"id": 12})
		self.assertFalse(bollo["not_taxable"])
		self.assertEqual(dati["ei_data"], {"payment_method": "MP05"})
		self.assertEqual(dati["payments_list"][0]["status"], "not_paid")

	def test_una_nota_di_credito_dice_quale_fattura_corregge(self):
		dati, _problemi = R.documento(
			fattura(tipo="TD04", elettronica=True, riferimento={"numero": "12/E", "data": "2026-10-01"}),
			MAPPA,
		)
		self.assertEqual(dati["type"], "credit_note")
		self.assertEqual(dati["numeration"], "/NC")
		self.assertEqual(dati["ei_data"]["invoice_number"], "12/E")
		self.assertEqual(dati["ei_data"]["invoice_date"], "2026-10-01")

	def test_un_tipo_che_fatture_in_cloud_non_riceve(self):
		dati, problemi = R.documento(fattura(tipo="TD06"), MAPPA)
		self.assertEqual(dati, {})
		self.assertIn("make this document in Fatture in Cloud", problemi[0].testo())

	def test_un_aliquota_senza_corrispondenza_si_dice_con_le_sue_parole(self):
		_dati, problemi = R.documento(fattura(), {**MAPPA, "iva": {}})
		self.assertEqual(
			[problema.testo() for problema in problemi],
			[
				"Choose the VAT rate of Fatture in Cloud that stands for Esente (art. 10): Settings > Invoicing > Fatture in Cloud"
			],
		)

	def test_pagata_con_un_metodo_senza_conto(self):
		_dati, problemi = R.documento(fattura(metodo_pagamento="MP05"), {**MAPPA, "conti": {"MP08": 2}})
		self.assertEqual(len(problemi), 1)
		self.assertIn("payments made by Bonifico", problemi[0].testo())

	def test_la_cassa_e_la_ritenuta(self):
		dati, _problemi = R.documento(
			fattura(
				elettronica=True,
				cassa={"tipo": "TC09", "percentuale": Decimal("2.00")},
				ritenuta={"percentuale": Decimal("20.00"), "tipo": "RT01", "causale": "A"},
			),
			MAPPA,
		)
		self.assertEqual((dati["cassa"], dati["ei_cassa_type"]), (2.0, "TC09"))
		self.assertEqual((dati["withholding_tax"], dati["ei_withholding_tax_causal"]), (20.0, "A"))
		# the fund is not on the re-charged duty: Fatture in Cloud would put it there
		self.assertFalse(dati["items_list"][-1]["apply_withholding_taxes"])

	def test_la_rivalsa_inps_e_la_sua(self):
		dati, _problemi = R.documento(fattura(cassa={"tipo": "TC22", "percentuale": 4}), MAPPA)
		self.assertEqual(dati["rivalsa"], 4.0)
		self.assertNotIn("cassa", dati)

	def test_un_anticipazione_non_e_compenso(self):
		riga = {**fattura()["righe"][0], "anticipazione": True, "chiave_iva": "0|N1"}
		dati, _problemi = R.documento(fattura(righe=[riga]), MAPPA)
		voce = dati["items_list"][0]
		self.assertTrue(voce["not_taxable"])
		self.assertFalse(voce["apply_withholding_taxes"])

	def test_uno_sconto_in_euro(self):
		riga = {**fattura()["righe"][0], "quantita": 2, "prezzo": 40, "sconto_importo": 10, "importo": 70}
		voce = R.documento(fattura(righe=[riga]), MAPPA)[0]["items_list"][0]
		self.assertEqual((voce["qty"], voce["net_price"], voce["discount"]), (2.0, 35.0, 0.0))
		riga = {**riga, "quantita": 3, "importo": 100}
		voce = R.documento(fattura(righe=[riga]), MAPPA)[0]["items_list"][0]
		# 33,333…: the line goes as one of its amount
		self.assertEqual((voce["qty"], voce["net_price"]), (1.0, 100.0))

	def test_un_azienda_con_partita_iva(self):
		destinatario = {
			"tipo": "soggetto_iva",
			"nome": "Acme Srl",
			"partita_iva": "01234567890",
			"codice_destinatario": "M5UXCR1",
			"pec": "acme@pec.it",
			"paese": "IT",
		}
		entita = R.documento(fattura(destinatario=destinatario), MAPPA)[0]["entity"]
		self.assertEqual(entita["type"], "company")
		self.assertEqual((entita["ei_code"], entita["certified_email"]), ("M5UXCR1", "acme@pec.it"))
		self.assertNotIn("first_name", entita)


class IlSistemaTSDaFattureInCloud(unittest.TestCase):
	def test_un_tipo_di_spesa_per_fattura(self):
		dati, problemi = R.documento(fattura(ts={"tracciato": True, "opposizione": False}), MAPPA)
		self.assertEqual(problemi, [])
		self.assertEqual(
			dati["extra_data"],
			{
				"ts_communication": True,
				"ts_tipo_spesa": "SP",
				"ts_pagamento_tracciato": True,
				"ts_opposizione": False,
				"ts_full_amount": True,
			},
		)

	def test_due_tipi_di_spesa_non_si_possono_dire(self):
		righe = [
			fattura()["righe"][0],
			{**fattura()["righe"][0], "descrizione": "Plantare", "tipo_spesa": "AD"},
		]
		_dati, problemi = R.documento(fattura(righe=righe, ts={"tracciato": True}), MAPPA)
		self.assertEqual(len(problemi), 1)
		self.assertIn("AD, SP", problemi[0].testo())

	def test_una_riga_che_non_va_al_sistema_ts(self):
		righe = [
			fattura()["righe"][0],
			{**fattura()["righe"][0], "descrizione": "Certificato", "al_ts": False, "tipo_spesa": None},
		]
		_dati, problemi = R.documento(fattura(righe=righe, ts={"tracciato": True}), MAPPA)
		self.assertIn("«Certificato» does not go there", problemi[0].testo())


class ITotali(unittest.TestCase):
	def test_al_centesimo(self):
		nostri = {"iva": Decimal("0"), "ritenuta": Decimal("0"), "da_pagare": Decimal("82.00")}
		loro = {"amount_gross": 80, "amount_vat": 0, "amount_withholding_tax": 0, "amount_due": 82}
		# the total is Fatture in Cloud's own way of counting a paper stamp duty
		self.assertEqual(R.totali_diversi(nostri, loro), [])
		problemi = R.totali_diversi(nostri, {**loro, "amount_vat": 1, "amount_due": 80})
		self.assertEqual(
			[p.argomenti for p in problemi],
			[(Decimal("1.00"), Decimal("0.00")), (Decimal("80.00"), Decimal("82.00"))],
		)
		self.assertIn("makes the VAT", problemi[0].testo())
		self.assertIn("makes the amount to pay", problemi[1].testo())


class GliStati(unittest.TestCase):
	def test_gli_stati_di_fatture_in_cloud_nei_nostri(self):
		self.assertEqual(R.stato_sdi("processing"), "inviato")
		self.assertEqual(R.stato_sdi("sent"), "consegnata")
		self.assertEqual(R.stato_sdi("not_delivered"), "mancata_consegna")
		self.assertEqual(R.stato_sdi("discarded"), "scartata")
		self.assertEqual(R.stato_sdi("no_response"), "decorrenza_termini")
		self.assertIsNone(R.stato_sdi("not_sent"))
		self.assertTrue(R.da_correggere("rejected"))
		self.assertFalse(R.da_correggere("accepted"))


class LeAziende(unittest.TestCase):
	def test_le_proprie_e_quelle_seguite_da_un_commercialista(self):
		risposta = {
			"data": {
				"companies": [
					{"id": 7, "name": "Studio Bianchi", "type": "company", "vat_number": "IT01234567890"},
					{
						"id": 9,
						"name": "Commercialista",
						"type": "accountant",
						"controlled_companies": [
							{"id": 11, "name": "Centro Aurora", "vat_number": "09876543210"}
						],
					},
				]
			}
		}
		self.assertEqual([a["id"] for a in R.aziende(risposta)], [11, 7])

	def test_la_stessa_partita_iva_col_paese_o_senza(self):
		self.assertTrue(R.stessa_partita_iva("01234567890", "IT01234567890"))
		self.assertFalse(R.stessa_partita_iva("01234567890", "09876543210"))
		self.assertTrue(R.stessa_partita_iva("", "IT01234567890"))


if __name__ == "__main__":
	unittest.main()
