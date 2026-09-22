# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The same seam, on a document only the healthcare register can produce.

An exempt session under art. 10 with the stamp duty re-charged: the re-charge
takes a line of its own and follows the exemption of the service rather than
sitting outside VAT. Which line is exempt is a fact about the qualification, so
the case belongs here and not with the sector-agnostic reconciliation.

Originally:

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


from crm.invoicing.tests.test_riconciliazione import RiconciliazioneTest


class RiconciliazioneSanitariaTest(RiconciliazioneTest):
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
