# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A supplier's invoice read out of its own XML: who, how much, how much of it is
VAT, by when. The file is the one inserted at Itala's test door on 05/10/2026,
with a payment term added."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from crm.invoicing.engine import fornitori
from crm.invoicing.tests.base import UnitTestCase

FATTURA = """<?xml version="1.0" encoding="UTF-8"?>
<p:FatturaElettronica xmlns:p="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2" versione="FPR12">
  <FatturaElettronicaHeader>
    <CedentePrestatore>
      <DatiAnagrafici>
        <IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>00743110157</IdCodice></IdFiscaleIVA>
        <Anagrafica><Denominazione>Fornitore Prova Srl</Denominazione></Anagrafica>
        <RegimeFiscale>RF01</RegimeFiscale>
      </DatiAnagrafici>
    </CedentePrestatore>
  </FatturaElettronicaHeader>
  <FatturaElettronicaBody>
    <DatiGenerali>
      <DatiGeneraliDocumento>
        <TipoDocumento>TD01</TipoDocumento><Divisa>EUR</Divisa><Data>2026-10-05</Data>
        <Numero>F-2026-17</Numero><ImportoTotaleDocumento>61.00</ImportoTotaleDocumento>
      </DatiGeneraliDocumento>
    </DatiGenerali>
    <DatiBeniServizi>
      <DettaglioLinee>
        <NumeroLinea>1</NumeroLinea><Descrizione>Materiale di consumo</Descrizione>
        <Quantita>1.00</Quantita><PrezzoUnitario>50.00</PrezzoUnitario>
        <PrezzoTotale>50.00</PrezzoTotale><AliquotaIVA>22.00</AliquotaIVA>
      </DettaglioLinee>
      <DatiRiepilogo>
        <AliquotaIVA>22.00</AliquotaIVA><ImponibileImporto>50.00</ImponibileImporto>
        <Imposta>11.00</Imposta><EsigibilitaIVA>I</EsigibilitaIVA>
      </DatiRiepilogo>
    </DatiBeniServizi>
    <DatiPagamento>
      <CondizioniPagamento>TP02</CondizioniPagamento>
      <DettaglioPagamento>
        <ModalitaPagamento>MP05</ModalitaPagamento>
        <DataScadenzaPagamento>2026-11-04</DataScadenzaPagamento>
        <ImportoPagamento>61.00</ImportoPagamento>
      </DettaglioPagamento>
    </DatiPagamento>
  </FatturaElettronicaBody>
</p:FatturaElettronica>"""


class LetturaTest(UnitTestCase):
	def test_chi_quanto_e_quando(self):
		fattura = fornitori.leggi(FATTURA)
		self.assertEqual(fattura.fornitore, "Fornitore Prova Srl")
		self.assertEqual(fattura.partita_iva, "00743110157")
		self.assertEqual((fattura.tipo_documento, fattura.numero), ("TD01", "F-2026-17"))
		self.assertEqual(fattura.data, date(2026, 10, 5))
		self.assertEqual(fattura.totale, Decimal("61.00"))
		self.assertEqual((fattura.imponibile, fattura.iva), (Decimal("50.00"), Decimal("11.00")))
		self.assertEqual(fattura.scadenza, date(2026, 11, 4))
		self.assertEqual(len(fattura.righe), 1)
		self.assertEqual(fattura.righe[0].descrizione, "Materiale di consumo")

	def test_i_campi_che_si_tengono(self):
		campi = fornitori.leggi(FATTURA).campi()
		self.assertEqual(campi["vat_amount"], 11.0)
		self.assertEqual(campi["due_date"], "2026-11-04")
		self.assertEqual(campi["document_date"], "2026-10-05")

	def test_senza_prefisso_ne_spazio_dei_nomi(self):
		semplice = FATTURA.replace("p:FatturaElettronica", "FatturaElettronica").replace(
			' xmlns:p="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"', ""
		)
		self.assertEqual(fornitori.leggi(semplice).numero, "F-2026-17")

	def test_un_fornitore_estero_tiene_il_suo_paese(self):
		estero = FATTURA.replace("<IdPaese>IT</IdPaese>", "<IdPaese>DE</IdPaese>")
		self.assertEqual(fornitori.leggi(estero).partita_iva, "DE00743110157")

	def test_il_totale_mancante_e_la_somma_dei_riepiloghi(self):
		senza = FATTURA.replace("<ImportoTotaleDocumento>61.00</ImportoTotaleDocumento>", "")
		self.assertEqual(fornitori.leggi(senza).totale, Decimal("61.00"))

	def test_quello_che_non_e_una_fattura_non_si_legge(self):
		self.assertIsNone(fornitori.leggi(b""))
		self.assertIsNone(fornitori.leggi(b"non xml"))
		self.assertIsNone(fornitori.leggi(b"<altro/>"))
		bomba = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><FatturaElettronica/>'
		self.assertIsNone(fornitori.leggi(bomba))
