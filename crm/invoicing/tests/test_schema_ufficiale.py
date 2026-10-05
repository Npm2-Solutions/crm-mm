# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The XML against the Agenzia's own schema, FatturaPA v1.2.3 (from 01/04/2025).

`valida()` says the SdI's content checks in words; the schema is what the SdI (and
Itala before it) reads first, and a file it refuses comes back as 00200 with no
sentence anybody can act on. Found on Itala's test door on 05/10/2026: «1» in
`Quantita` - the schema wants two decimals - refused every invoice with a quantity.

The schemas are the published ones, in `xsd/` (the signature's import pointed at the
copy beside it, so nothing is fetched). lxml comes with the framework: without a
bench these are skipped.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest import skipUnless

from crm.invoicing.engine.codici import TipoDocumento
from crm.invoicing.engine.fatturapa import (
	Anagrafica,
	Cessionario,
	DatiCassa,
	DatiRitenuta,
	DettaglioPagamento,
	DocumentoCollegato,
	Linea,
	Riepilogo,
	Sede,
)
from crm.invoicing.tests.base import UnitTestCase
from crm.invoicing.tests.test_fatturapa import fattura

try:
	from lxml import etree
except ImportError:  # no bench: plain Python has no lxml
	etree = None

SCHEMA = Path(__file__).parent / "xsd" / "Schema_VFPR12_v1.2.3.xsd"


@skipUnless(etree, "lxml is the framework's: run on a bench")
class SchemaUfficialeTest(UnitTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		lettore = etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False)
		cls.schema = etree.XMLSchema(etree.parse(str(SCHEMA), lettore))

	def assertValida(self, documento):
		albero = etree.fromstring(documento.xml().encode())
		if not self.schema.validate(albero):
			self.fail("\n".join(str(errore) for errore in self.schema.error_log))

	def test_una_fattura_semplice(self):
		self.assertValida(fattura())

	def test_una_quantita_intera_ha_i_suoi_decimali(self):
		documento = fattura(
			linee=[
				Linea(
					numero=1,
					descrizione="Consulenza",
					quantita=Decimal("1"),
					prezzo_unitario=Decimal("1000.00"),
					prezzo_totale=Decimal("1000.00"),
					aliquota_iva=Decimal("22.00"),
				)
			]
		)
		self.assertValida(documento)
		self.assertEqual(documento.elemento().find(".//Quantita").text, "1.00")

	def test_una_quantita_con_piu_decimali_li_tiene(self):
		documento = fattura(
			linee=[
				Linea(
					numero=1,
					descrizione="Consulenza",
					quantita=Decimal("0.125"),
					prezzo_unitario=Decimal("8000.00"),
					prezzo_totale=Decimal("1000.00"),
					aliquota_iva=Decimal("22.00"),
				)
			]
		)
		self.assertValida(documento)
		self.assertEqual(documento.elemento().find(".//Quantita").text, "0.125")

	def test_una_riga_scontata_porta_il_suo_sconto(self):
		# 3 sessions at 33.33 with 9.99 off: before, the total did not follow the price
		# and the SdI refused it (00423)
		from crm.invoicing.engine.fatturapa import _sconto_della_riga

		sconti = _sconto_della_riga(Decimal("33.33"), Decimal("3"), Decimal("90.00"))
		documento = fattura(
			linee=[
				Linea(
					numero=1,
					descrizione="Ciclo di sedute",
					quantita=Decimal("3"),
					prezzo_unitario=Decimal("33.33"),
					sconti=sconti,
					prezzo_totale=Decimal("90.00"),
					aliquota_iva=Decimal("22.00"),
				)
			]
		)
		self.assertValida(documento)
		self.assertEqual(documento.elemento().find(".//ScontoMaggiorazione/Tipo").text, "SC")
		self.assertEqual(documento.elemento().find(".//ScontoMaggiorazione/Importo").text, "3.33")

	def test_ritenuta_bollo_cassa_e_pagamento(self):
		self.assertValida(
			fattura(
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
				],
				dati_ritenuta=[DatiRitenuta("RT01", Decimal("200.00"), Decimal("20.00"), "A")],
				bollo_virtuale=True,
				importo_bollo=Decimal("2.00"),
				dati_cassa=[DatiCassa("TC22", Decimal("4.00"), Decimal("40.00"), Decimal("22.00"))],
				causale=["Prestazione professionale"],
				pagamenti=[
					DettaglioPagamento(
						"MP05",
						Decimal("1068.80"),
						data_scadenza=date(2026, 4, 10),
						iban="IT60X0542811101000000123456",
					)
				],
			)
		)

	def test_una_seduta_esente_a_una_persona(self):
		self.assertValida(
			fattura(
				cessionario=Cessionario(
					anagrafica=Anagrafica(nome="Mario", cognome="Rossi", codice_fiscale="RSSMRA80A01H501U"),
					sede=Sede(indirizzo="Via Verdi 3", cap="00100", comune="Roma", provincia="RM"),
				),
				codice_destinatario="0000000",
				linee=[
					Linea(
						numero=1,
						descrizione="Seduta",
						quantita=Decimal("1"),
						prezzo_unitario=Decimal("100.00"),
						prezzo_totale=Decimal("100.00"),
						aliquota_iva=Decimal("0.00"),
						natura="N4",
					)
				],
				riepiloghi=[
					Riepilogo(
						aliquota_iva=Decimal("0.00"),
						imponibile_importo=Decimal("100.00"),
						imposta=Decimal("0.00"),
						natura="N4",
						riferimento_normativo="art. 10, n. 18, DPR 633/72",
					)
				],
				importo_totale=Decimal("100.00"),
			)
		)

	def test_una_nota_di_credito(self):
		self.assertValida(
			fattura(
				tipo_documento=TipoDocumento.NOTA_CREDITO,
				documenti_collegati=[DocumentoCollegato("2026/E/44", date(2026, 2, 1))],
			)
		)

	def test_una_fattura_alla_pubblica_amministrazione(self):
		self.assertValida(
			fattura(
				codice_destinatario="UF1234",
				documenti_collegati=[DocumentoCollegato("2026/E/44", codice_cig="1234567890")],
			)
		)
