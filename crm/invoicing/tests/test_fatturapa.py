# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The XML, and the checks that stop it from being rejected.

Element order is the whole game: the schema is a sequence, so a block in the wrong
place comes back as code 00001 with no useful explanation. These tests read the
order out of the generated document rather than trusting the builder.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET

from crm.invoicing.engine.codici import CODICE_DESTINATARIO_ASSENTE, TipoDocumento
from crm.invoicing.engine.fatturapa import (
	NAMESPACE,
	Anagrafica,
	Cedente,
	Cessionario,
	DatiCassa,
	DatiRitenuta,
	DettaglioPagamento,
	DocumentoCollegato,
	FatturaElettronica,
	Linea,
	Riepilogo,
	Sede,
	codice_destinatario,
	progressivo_alfanumerico,
	valida,
)
from crm.invoicing.tests.base import UnitTestCase


def fattura(**kwargs) -> FatturaElettronica:
	base = {
		"cedente": Cedente(
			anagrafica=Anagrafica(denominazione="Studio Bianchi", id_paese="IT", id_codice="00743110157"),
			sede=Sede(indirizzo="Via Roma 1", cap="20100", comune="Milano", provincia="MI"),
		),
		"cessionario": Cessionario(
			anagrafica=Anagrafica(denominazione="Acme Srl", id_paese="IT", id_codice="00743110157"),
			sede=Sede(indirizzo="Via Torino 2", cap="10100", comune="Torino", provincia="TO"),
		),
		"numero": "2026/E/45",
		"data": date(2026, 3, 10),
		"linee": [
			Linea(
				numero=1,
				descrizione="Consulenza",
				prezzo_unitario=Decimal("1000.00"),
				prezzo_totale=Decimal("1000.00"),
				aliquota_iva=Decimal("22.00"),
			)
		],
		"riepiloghi": [
			Riepilogo(
				aliquota_iva=Decimal("22.00"),
				imponibile_importo=Decimal("1000.00"),
				imposta=Decimal("220.00"),
			)
		],
		"importo_totale": Decimal("1220.00"),
		"codice_destinatario": "ABC1234",
	}
	base.update(kwargs)
	return FatturaElettronica(**base)


def figli(elemento) -> list[str]:
	return [f.tag for f in elemento]


class StrutturaTest(UnitTestCase):
	def test_la_radice_e_qualificata_e_i_figli_no(self):
		radice = fattura().elemento()
		self.assertEqual(radice.tag, f"{{{NAMESPACE}}}FatturaElettronica")
		# elementFormDefault is unqualified: only the root carries the namespace.
		self.assertEqual(figli(radice), ["FatturaElettronicaHeader", "FatturaElettronicaBody"])

	def test_la_versione_segue_il_codice_destinatario(self):
		self.assertEqual(fattura().formato, "FPR12")
		self.assertEqual(fattura(codice_destinatario="UF1234").formato, "FPA12")

	def test_l_ordine_dei_dati_generali_e_quello_dello_schema(self):
		radice = fattura(
			dati_ritenuta=[DatiRitenuta("RT01", Decimal("200.00"), Decimal("20.00"), "A")],
			bollo_virtuale=True,
			importo_bollo=Decimal("2.00"),
			dati_cassa=[DatiCassa("TC22", Decimal("4.00"), Decimal("40.00"), Decimal("22.00"))],
			causale=["Prestazione professionale"],
		).elemento()
		documento = radice.find("./FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento")
		self.assertEqual(
			figli(documento),
			[
				"TipoDocumento",
				"Divisa",
				"Data",
				"Numero",
				"DatiRitenuta",
				"DatiBollo",
				"DatiCassaPrevidenziale",
				"ImportoTotaleDocumento",
				"Causale",
			],
		)

	def test_l_ordine_della_linea_e_quello_dello_schema(self):
		radice = fattura(
			linee=[
				Linea(
					numero=1,
					descrizione="Consulenza",
					quantita=Decimal("2"),
					unita_misura="ORE",
					prezzo_unitario=Decimal("500.00"),
					prezzo_totale=Decimal("1000.00"),
					aliquota_iva=Decimal("22.00"),
					ritenuta=True,
				)
			]
		).elemento()
		linea = radice.find("./FatturaElettronicaBody/DatiBeniServizi/DettaglioLinee")
		self.assertEqual(
			figli(linea),
			[
				"NumeroLinea",
				"Descrizione",
				"Quantita",
				"UnitaMisura",
				"PrezzoUnitario",
				"PrezzoTotale",
				"AliquotaIVA",
				"Ritenuta",
			],
		)

	def test_natura_segue_aliquota_nel_riepilogo(self):
		radice = fattura(
			linee=[
				Linea(
					numero=1,
					descrizione="Seduta",
					prezzo_unitario=Decimal("100.00"),
					prezzo_totale=Decimal("100.00"),
					aliquota_iva=Decimal("0.00"),
					natura="N4",
				)
			],
			riepiloghi=[
				Riepilogo(
					aliquota_iva=Decimal("0.00"),
					natura="N4",
					imponibile_importo=Decimal("100.00"),
					imposta=Decimal("0.00"),
					riferimento_normativo="art. 10 n. 18 DPR 633/72",
				)
			],
			importo_totale=Decimal("100.00"),
		).elemento()
		riepilogo = radice.find("./FatturaElettronicaBody/DatiBeniServizi/DatiRiepilogo")
		self.assertEqual(
			figli(riepilogo),
			[
				"AliquotaIVA",
				"Natura",
				"ImponibileImporto",
				"Imposta",
				"EsigibilitaIVA",
				"RiferimentoNormativo",
			],
		)

	def test_un_elemento_vuoto_non_viene_scritto(self):
		radice = fattura(
			cessionario=Cessionario(
				anagrafica=Anagrafica(nome="Mario", cognome="Rossi", codice_fiscale="RSSMRA80A01H501U"),
				sede=Sede(indirizzo="Via Verdi 3", cap="00100", comune="Roma", provincia=""),
			)
		).elemento()
		sede = radice.find("./FatturaElettronicaHeader/CessionarioCommittente/Sede")
		self.assertEqual(figli(sede), ["Indirizzo", "CAP", "Comune", "Nazione"])

	def test_la_pec_viaggia_solo_col_codice_assente(self):
		con_pec = fattura(
			codice_destinatario=CODICE_DESTINATARIO_ASSENTE, pec_destinatario="acme@pec.it"
		).elemento()
		self.assertIsNotNone(con_pec.find(".//PECDestinatario"))
		con_codice = fattura(codice_destinatario="ABC1234", pec_destinatario="acme@pec.it").elemento()
		self.assertIsNone(con_codice.find(".//PECDestinatario"))

	def test_la_causale_lunga_si_spezza_invece_di_troncarsi(self):
		testo = "A" * 450
		radice = fattura(causale=[testo]).elemento()
		pezzi = radice.findall(".//Causale")
		self.assertEqual(len(pezzi), 3)
		self.assertEqual("".join(p.text for p in pezzi), testo)

	def test_l_xml_si_riparsa(self):
		documento = fattura().xml()
		self.assertTrue(documento.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
		radice = ET.fromstring(documento)
		self.assertEqual(radice.tag, f"{{{NAMESPACE}}}FatturaElettronica")

	def test_il_nome_file_segue_la_convenzione(self):
		self.assertEqual(fattura().nome_file("00001"), "IT00743110157_00001.xml")


class ValidazioneTest(UnitTestCase):
	def test_una_fattura_corretta_non_ha_rilievi(self):
		self.assertEqual(valida(fattura()), [])

	def test_aliquota_zero_senza_natura_e_bloccante(self):
		problemi = valida(
			fattura(
				linee=[
					Linea(
						numero=1,
						descrizione="Seduta",
						prezzo_unitario=Decimal("100.00"),
						prezzo_totale=Decimal("100.00"),
						aliquota_iva=Decimal("0.00"),
					)
				],
				riepiloghi=[
					Riepilogo(
						aliquota_iva=Decimal("0.00"),
						imponibile_importo=Decimal("100.00"),
						imposta=Decimal("0.00"),
					)
				],
				importo_totale=Decimal("100.00"),
			)
		)
		self.assertTrue(any(p.startswith("00400") for p in problemi))
		self.assertTrue(any(p.startswith("00429") for p in problemi))

	def test_natura_con_aliquota_non_nulla_e_bloccante(self):
		problemi = valida(
			fattura(
				linee=[
					Linea(
						numero=1,
						descrizione="Consulenza",
						prezzo_unitario=Decimal("1000.00"),
						prezzo_totale=Decimal("1000.00"),
						aliquota_iva=Decimal("22.00"),
						natura="N4",
					)
				]
			)
		)
		self.assertTrue(any(p.startswith("00401") for p in problemi))

	def test_le_nature_ritirate_sono_rifiutate(self):
		problemi = valida(
			fattura(
				linee=[
					Linea(
						numero=1,
						descrizione="Seduta",
						prezzo_unitario=Decimal("100.00"),
						prezzo_totale=Decimal("100.00"),
						aliquota_iva=Decimal("0.00"),
						natura="N2",
					)
				],
				riepiloghi=[
					Riepilogo(
						aliquota_iva=Decimal("0.00"),
						natura="N2",
						imponibile_importo=Decimal("100.00"),
						imposta=Decimal("0.00"),
					)
				],
				importo_totale=Decimal("100.00"),
			)
		)
		self.assertTrue(any(p.startswith("00445") for p in problemi))

	def test_il_numero_senza_cifre_viene_scartato(self):
		problemi = valida(fattura(numero="FATTURA/ANNO"))
		self.assertTrue(any(p.startswith("00425") for p in problemi))

	def test_l_imposta_deve_tornare_col_suo_imponibile(self):
		problemi = valida(
			fattura(
				riepiloghi=[
					Riepilogo(
						aliquota_iva=Decimal("22.00"),
						imponibile_importo=Decimal("1000.00"),
						imposta=Decimal("200.00"),
					)
				]
			)
		)
		self.assertTrue(any(p.startswith("00421") for p in problemi))

	def test_una_riga_senza_riepilogo_viene_notata(self):
		problemi = valida(
			fattura(
				linee=[
					Linea(
						numero=1,
						descrizione="Consulenza",
						prezzo_unitario=Decimal("1000.00"),
						prezzo_totale=Decimal("1000.00"),
						aliquota_iva=Decimal("10.00"),
					)
				]
			)
		)
		self.assertTrue(any(p.startswith("00419") for p in problemi))

	def test_il_totale_deve_reggere_i_riepiloghi(self):
		problemi = valida(fattura(importo_totale=Decimal("999.00")))
		self.assertTrue(any(p.startswith("00422") for p in problemi))

	def test_il_cessionario_senza_identificativo_e_bloccante(self):
		problemi = valida(
			fattura(
				cessionario=Cessionario(
					anagrafica=Anagrafica(denominazione="Acme Srl"),
					sede=Sede(indirizzo="Via Torino 2", cap="10100", comune="Torino"),
				)
			)
		)
		self.assertTrue(any(p.startswith("00417") for p in problemi))

	def test_la_nota_di_credito_deve_dire_cosa_corregge(self):
		problemi = valida(fattura(tipo_documento=TipoDocumento.NOTA_CREDITO))
		self.assertTrue(any("DatiFattureCollegate" in p for p in problemi))

	def test_la_nota_di_credito_col_riferimento_e_valida(self):
		documento = fattura(
			tipo_documento=TipoDocumento.NOTA_CREDITO,
			documenti_collegati=[DocumentoCollegato("2026/E/44", date(2026, 2, 1))],
		)
		self.assertEqual(valida(documento), [])
		radice = documento.elemento()
		self.assertIsNotNone(radice.find(".//DatiFattureCollegate/IdDocumento"))

	def test_il_cap_italiano_deve_essere_di_cinque_cifre(self):
		problemi = valida(
			fattura(
				cessionario=Cessionario(
					anagrafica=Anagrafica(denominazione="Acme Srl", id_paese="IT", id_codice="00743110157"),
					sede=Sede(indirizzo="Via Torino 2", cap="101", comune="Torino"),
				)
			)
		)
		self.assertTrue(any("CAP" in p for p in problemi))

	def test_un_cap_estero_non_deve_essere_italiano(self):
		documento = fattura(
			cessionario=Cessionario(
				anagrafica=Anagrafica(denominazione="Muster GmbH", id_paese="DE", id_codice="123456789"),
				sede=Sede(indirizzo="Hauptstrasse 1", cap="10115", comune="Berlin", nazione="DE"),
			),
			codice_destinatario="XXXXXXX",
		)
		self.assertEqual(valida(documento), [])

	def test_la_ritenuta_vuole_sapere_su_cosa_si_calcola(self):
		problemi = valida(
			fattura(dati_ritenuta=[DatiRitenuta("RT01", Decimal("200.00"), Decimal("20.00"), "A")])
		)
		self.assertTrue(any(p.startswith("00415") for p in problemi))

	def test_senza_codice_e_senza_pec_la_fattura_si_ferma_allo_sdi(self):
		problemi = valida(fattura(codice_destinatario=CODICE_DESTINATARIO_ASSENTE))
		self.assertTrue(any("never receives it" in p for p in problemi))


class CodiceDestinatarioTest(UnitTestCase):
	def test_sette_caratteri_per_i_privati(self):
		self.assertEqual(codice_destinatario("abc1234", None), ("ABC1234", None))

	def test_senza_codice_si_ripiega_su_zeri_e_pec(self):
		self.assertEqual(
			codice_destinatario(None, "acme@pec.it"), (CODICE_DESTINATARIO_ASSENTE, "acme@pec.it")
		)

	def test_l_estero_ha_il_suo_codice(self):
		self.assertEqual(codice_destinatario(None, None, estero=True), ("XXXXXXX", None))

	def test_la_pa_vuole_sei_caratteri(self):
		self.assertEqual(codice_destinatario("UF1234", None, pubblica_amministrazione=True), ("UF1234", None))
		with self.assertRaises(ValueError):
			codice_destinatario("ABC1234", None, pubblica_amministrazione=True)

	def test_il_progressivo_e_alfanumerico_a_cinque_cifre(self):
		self.assertEqual(progressivo_alfanumerico(1), "00001")
		self.assertEqual(progressivo_alfanumerico(35), "0000Z")
		self.assertEqual(progressivo_alfanumerico(36), "00010")


class RilieviBloccantiTest(UnitTestCase):
	"""A finding with an SdI code stops the file; the rest are worth saying anyway."""

	def test_i_codici_sdi_sono_bloccanti(self):
		from crm.invoicing.engine.fatturapa import bloccanti

		problemi = ["00421: imposta", "the recipient has nowhere to receive it", "00400: natura"]
		self.assertEqual(bloccanti(problemi), ["00421: imposta", "00400: natura"])

	def test_una_fattura_senza_recapito_e_valida_ma_non_recapitabile(self):
		from crm.invoicing.engine.fatturapa import bloccanti

		problemi = valida(fattura(codice_destinatario=CODICE_DESTINATARIO_ASSENTE))
		self.assertTrue(problemi)
		self.assertEqual(bloccanti(problemi), [])
