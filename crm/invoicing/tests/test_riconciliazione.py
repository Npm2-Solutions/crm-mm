# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The seam where a wrong total actually happens.

Classification, arithmetic and XML are each correct on their own; what goes wrong
is the join. The fund levy lives in `DatiCassaPrevidenziale` and not on a line, the
re-charged stamp duty lives on a line and not in the summary, and the SdI checks
00421, 00422 and 00423 measure exactly that arrangement.

So these tests run the whole chain - classify, compute, serialise - and read the
result back with the SdI's own checks.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from crm.invoicing.engine.calcolo import calcola
from crm.invoicing.engine.classificazione import RigaDaClassificare, classifica
from crm.invoicing.engine.codici import RegimeFiscale, TipoCassa, TipoDestinatario
from crm.invoicing.engine.fatturapa import (
	Anagrafica,
	Cedente,
	Cessionario,
	FatturaElettronica,
	Sede,
	bloccanti,
	casse_da_calcolo,
	linee_da_calcolo,
	riepiloghi_da_calcolo,
	ritenute_da_calcolo,
	valida,
)
from crm.invoicing.tests.base import UnitTestCase


def riga(importo, qualifica, *, sanitaria=False, esente=False, aliquota="22.00", servizio="SRV", **kw):
	return RigaDaClassificare(
		servizio_id=servizio,
		descrizione_fiscale="Prestazione",
		is_sanitaria=sanitaria,
		esente_iva=esente,
		erogatore_id="ERO",
		erogatore_qualifica=qualifica,
		imponibile=Decimal(importo),
		aliquota_catalogo=Decimal(aliquota) if aliquota else None,
		**kw,
	)


def componi(calcolo, *, ritenuta_su_righe=False, ritenuta_su_cassa=False, **kwargs) -> FatturaElettronica:
	dettagli = [
		{
			"descrizione": r.esito.riga.descrizione_fiscale,
			"quantita": 1,
			"prezzo_unitario": r.imponibile,
			"ritenuta": ritenuta_su_righe,
		}
		for r in calcolo.righe
	]
	valori = {
		"cedente": Cedente(
			anagrafica=Anagrafica(denominazione="Studio", id_paese="IT", id_codice="00743110157"),
			sede=Sede(indirizzo="Via Roma 1", cap="20100", comune="Milano", provincia="MI"),
		),
		"cessionario": Cessionario(
			anagrafica=Anagrafica(denominazione="Acme Srl", id_paese="IT", id_codice="00743110157"),
			sede=Sede(indirizzo="Via Torino 2", cap="10100", comune="Torino", provincia="TO"),
		),
		"numero": "2026/E/1",
		"data": date(2026, 3, 10),
		"codice_destinatario": "ABC1234",
		"linee": linee_da_calcolo(calcolo, dettagli),
		"riepiloghi": riepiloghi_da_calcolo(calcolo),
		"dati_cassa": casse_da_calcolo(calcolo, ritenuta_su_cassa),
		"dati_ritenuta": ritenute_da_calcolo(calcolo),
		"importo_totale": calcolo.totale,
		"bollo_virtuale": calcolo.bollo_dovuto,
		"importo_bollo": calcolo.bollo if calcolo.bollo_dovuto else None,
	}
	valori.update(kwargs)
	return FatturaElettronica(**valori)


class RiconciliazioneTest(UnitTestCase):
	def _controlla(self, fattura):
		problemi = valida(fattura)
		self.assertEqual(bloccanti(problemi), [], problemi)
		return problemi

	def test_una_parcella_con_cassa_e_ritenuta_quadra(self):
		calcolo = calcola(
			classifica([riga("1000.00", "avvocato")], TipoDestinatario.SOGGETTO_IVA),
			tipo_cassa=TipoCassa.AVVOCATI,
			applica_ritenuta=True,
		)
		fattura = componi(calcolo, ritenuta_su_righe=True)
		self._controlla(fattura)
		# The levy is not on a line, so lines total 1000 and the summary 1040.
		self.assertEqual(sum(linea.prezzo_totale for linea in fattura.linee), Decimal("1000.00"))
		self.assertEqual(fattura.riepiloghi[0].imponibile_importo, Decimal("1040.00"))
		self.assertEqual(fattura.dati_cassa[0].importo_contributo, Decimal("40.00"))
		self.assertEqual(fattura.importo_totale, Decimal("1268.80"))

	def test_il_riaddebito_del_bollo_prende_una_riga_sua(self):
		calcolo = calcola(
			classifica(
				[riga("200.00", "psicologo", sanitaria=True, esente=True, aliquota=None)],
				TipoDestinatario.PERSONA_FISICA,
				soggetto_emittente="professionista_sanitario",
			),
			bollo_riaddebitato=True,
		)
		fattura = componi(calcolo)
		self._controlla(fattura)
		self.assertEqual(len(fattura.linee), 2)
		self.assertEqual(fattura.linee[1].prezzo_totale, Decimal("2.00"))
		self.assertEqual(fattura.linee[1].natura, "N4")
		self.assertEqual(fattura.riepiloghi[0].imponibile_importo, Decimal("202.00"))
		self.assertEqual(fattura.importo_totale, Decimal("202.00"))

	def test_un_documento_multi_aliquota_produce_un_riepilogo_per_gruppo(self):
		calcolo = calcola(
			classifica(
				[
					riga("1000.00", "consulente"),
					riga("500.00", "consulente", aliquota="10.00", servizio="SRV2"),
				],
				TipoDestinatario.SOGGETTO_IVA,
			)
		)
		fattura = componi(calcolo)
		self._controlla(fattura)
		self.assertEqual(len(fattura.riepiloghi), 2)
		self.assertEqual(fattura.importo_totale, Decimal("1770.00"))

	def test_le_anticipazioni_hanno_il_loro_riepilogo(self):
		calcolo = calcola(
			classifica(
				[
					riga("1000.00", "avvocato"),
					riga("145.00", "avvocato", aliquota=None, e_anticipazione=True, servizio="SRV2"),
				],
				TipoDestinatario.SOGGETTO_IVA,
			)
		)
		fattura = componi(calcolo)
		self._controlla(fattura)
		nature = {r.natura for r in fattura.riepiloghi}
		self.assertIn("N1", nature)
		self.assertEqual(fattura.importo_totale, Decimal("1365.00"))

	def test_il_forfettario_esce_senza_iva_e_con_n2_2(self):
		calcolo = calcola(
			classifica(
				[riga("2000.00", "consulente")],
				TipoDestinatario.SOGGETTO_IVA,
				regime=RegimeFiscale.FORFETTARIO,
			)
		)
		fattura = componi(calcolo)
		self._controlla(fattura)
		self.assertEqual(fattura.riepiloghi[0].natura, "N2.2")
		self.assertEqual(fattura.importo_totale, Decimal("2000.00"))

	def test_lo_split_payment_marca_l_esigibilita(self):
		calcolo = calcola(
			classifica([riga("1000.00", "societa_servizi")], TipoDestinatario.PUBBLICA_AMMINISTRAZIONE),
			split_payment=True,
		)
		fattura = componi(calcolo, codice_destinatario="UF1234")
		self._controlla(fattura)
		self.assertEqual(fattura.formato, "FPA12")
		self.assertEqual(fattura.riepiloghi[0].esigibilita_iva, "S")
		self.assertEqual(fattura.importo_totale, Decimal("1220.00"))
		self.assertEqual(calcolo.netto_a_pagare, Decimal("1000.00"))

	def test_il_reverse_charge_non_espone_imposta(self):
		calcolo = calcola(
			classifica(
				[riga("5000.00", "societa_servizi", aliquota=None, natura_iva_catalogo="N6.7")],
				TipoDestinatario.SOGGETTO_IVA,
			)
		)
		fattura = componi(calcolo)
		self._controlla(fattura)
		self.assertEqual(fattura.riepiloghi[0].natura, "N6.7")
		self.assertEqual(fattura.riepiloghi[0].imposta, Decimal("0.00"))
		self.assertEqual(fattura.importo_totale, Decimal("5000.00"))

	def test_il_cliente_tedesco_esce_fuori_campo(self):
		calcolo = calcola(
			classifica(
				[riga("3000.00", "consulente", aliquota=None, natura_iva_catalogo="N2.1")],
				TipoDestinatario.ESTERO,
			)
		)
		fattura = componi(
			calcolo,
			codice_destinatario="XXXXXXX",
			cessionario=Cessionario(
				anagrafica=Anagrafica(denominazione="Muster GmbH", id_paese="DE", id_codice="123456789"),
				sede=Sede(indirizzo="Hauptstrasse 1", cap="10115", comune="Berlin", nazione="DE"),
			),
		)
		self.assertEqual(valida(fattura), [])
		self.assertEqual(fattura.riepiloghi[0].natura, "N2.1")

	def test_ogni_caso_si_riserializza(self):
		calcolo = calcola(
			classifica([riga("1000.00", "avvocato")], TipoDestinatario.SOGGETTO_IVA),
			tipo_cassa=TipoCassa.AVVOCATI,
			applica_ritenuta=True,
		)
		xml = componi(calcolo, ritenuta_su_righe=True).xml()
		self.assertIn("<DatiCassaPrevidenziale>", xml)
		self.assertIn("<DatiRitenuta>", xml)
		self.assertIn("<ImportoTotaleDocumento>1268.80</ImportoTotaleDocumento>", xml)
