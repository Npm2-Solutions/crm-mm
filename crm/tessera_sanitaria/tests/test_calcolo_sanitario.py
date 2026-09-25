# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Calculation where the numbers depend on the healthcare register.

The arithmetic itself is invoicing's and is tested there. What is here is the
part that only has an answer once qualifications exist: an ENPAP contribution,
an exempt re-charge, and the invariant that the document total and the sum
reported to the Sistema TS coincide.

Original notes: The arithmetic, and above all its boundaries.

Every number in here is a case somebody got wrong: the stamp-duty threshold that
is passed and not reached, the fund levy that enters the VAT base but not the
withholding, the re-charged stamp duty that follows the service instead of sitting
outside VAT.
"""

from __future__ import annotations

from decimal import Decimal

from crm.invoicing.engine.calcolo import SOGLIA_BOLLO, calcola
from crm.invoicing.engine.classificazione import RigaDaClassificare, classifica
from crm.invoicing.engine.codici import (
	ModalitaBollo,
	RegimeFiscale,
	TipoCassa,
	TipoDestinatario,
)
from crm.invoicing.tests.base import UnitTestCase


def riga(
	importo: str,
	qualifica: str = "psicologo",
	*,
	sanitaria: bool = True,
	esente: bool = True,
	aliquota: str | None = None,
	natura: str | None = None,
	anticipazione: bool = False,
	servizio: str = "SRV-1",
) -> RigaDaClassificare:
	return RigaDaClassificare(
		servizio_id=servizio,
		descrizione_fiscale="Seduta",
		is_sanitaria=sanitaria,
		esente_iva=esente,
		erogatore_id="ERO-1",
		erogatore_qualifica=qualifica,
		imponibile=Decimal(importo),
		aliquota_catalogo=Decimal(aliquota) if aliquota else None,
		natura_iva_catalogo=natura,
		e_anticipazione=anticipazione,
	)


def sanitario(*righe: RigaDaClassificare):
	return classifica(
		list(righe), TipoDestinatario.PERSONA_FISICA, soggetto_emittente="professionista_sanitario"
	)


class SogliaBolloTest(UnitTestCase):
	"""77.47 is passed, not reached."""

	def test_settantasei_euro_con_enpap_supera_la_soglia(self):
		calcolo = calcola(sanitario(riga("76.00")), tipo_cassa=TipoCassa.ENPAP)
		self.assertEqual(calcolo.cassa, Decimal("1.52"))
		self.assertEqual(calcolo.base_bollo, Decimal("77.52"))
		self.assertTrue(calcolo.bollo_dovuto)

	def test_settantacinque_euro_con_enpap_non_la_supera(self):
		calcolo = calcola(sanitario(riga("75.00")), tipo_cassa=TipoCassa.ENPAP)
		self.assertEqual(calcolo.base_bollo, Decimal("76.50"))
		self.assertFalse(calcolo.bollo_dovuto)

	def test_esattamente_alla_soglia_il_bollo_non_e_dovuto(self):
		calcolo = calcola(sanitario(riga(str(SOGLIA_BOLLO))))
		self.assertEqual(calcolo.base_bollo, SOGLIA_BOLLO)
		self.assertFalse(calcolo.bollo_dovuto)

	def test_un_centesimo_oltre_la_soglia_lo_rende_dovuto(self):
		calcolo = calcola(sanitario(riga("77.48")))
		self.assertTrue(calcolo.bollo_dovuto)
		self.assertEqual(calcolo.bollo, Decimal("2.00"))

	def test_le_righe_imponibili_non_entrano_nella_soglia(self):
		# A 22% line is charged with VAT, so it does not feed the threshold at all.
		calcolo = calcola(
			classifica(
				[riga("500.00", "osteopata", esente=False, aliquota="22.00")],
				TipoDestinatario.PERSONA_FISICA,
			)
		)
		self.assertEqual(calcolo.base_bollo, Decimal("0.00"))
		self.assertFalse(calcolo.bollo_dovuto)

	def test_il_servizio_esentato_dal_bollo_non_lo_paga(self):
		calcolo = calcola(sanitario(riga("500.00")), soggetto_a_bollo=False)
		self.assertFalse(calcolo.bollo_dovuto)


class BolloRiaddebitatoTest(UnitTestCase):
	def test_il_riaddebito_segue_il_regime_della_prestazione(self):
		calcolo = calcola(sanitario(riga("200.00")), bollo_riaddebitato=True)
		self.assertTrue(calcolo.bollo_dovuto)
		self.assertEqual(calcolo.bollo_riaddebitato, Decimal("2.00"))
		self.assertEqual(calcolo.totale, Decimal("202.00"))
		# One summary block only: the re-charge folded into the exempt one.
		self.assertEqual(len(calcolo.riepiloghi), 1)
		self.assertEqual(calcolo.riepiloghi[0].natura, "N4")
		self.assertEqual(calcolo.riepiloghi[0].imponibile, Decimal("202.00"))

	def test_il_riaddebito_non_si_autoalimenta(self):
		# 76.00 alone stays under the threshold; adding the re-charge must not push
		# a later document over it.
		calcolo = calcola(sanitario(riga("76.00")), bollo_riaddebitato=True)
		self.assertEqual(calcolo.base_bollo, Decimal("76.00"))
		self.assertFalse(calcolo.bollo_dovuto)
		self.assertEqual(calcolo.bollo_riaddebitato, Decimal("0.00"))

	def test_bollo_su_originale_avvisa_del_contrassegno(self):
		calcolo = calcola(sanitario(riga("200.00")), modalita_bollo=ModalitaBollo.SU_ORIGINALE)
		self.assertTrue(any("14-digit" in a for a in calcolo.avvisi))


class SistemaTsTest(UnitTestCase):
	def test_il_totale_del_pdf_e_quello_comunicato_coincidono(self):
		calcolo = calcola(sanitario(riga("200.00")), tipo_cassa=TipoCassa.ENPAP, bollo_riaddebitato=True)
		self.assertTrue(calcolo.quadra)
		self.assertEqual(calcolo.totale, calcolo.totale_ts)

	def test_il_bollo_in_contanti_e_l_unica_divergenza_ammessa(self):
		calcolo = calcola(sanitario(riga("200.00")), bollo_riaddebitato=True, bollo_pagato_in_contanti=True)
		self.assertEqual(calcolo.totale - calcolo.totale_ts, Decimal("2.00"))
		self.assertTrue(any("cash" in a for a in calcolo.avvisi))

	def test_le_voci_ts_sono_aggregate_per_tipo_spesa(self):
		calcolo = calcola(sanitario(riga("100.00"), riga("50.00", servizio="SRV-2")))
		self.assertEqual(calcolo.voci_ts(), [("SP", Decimal("150.00"))])

	def test_la_ripartizione_non_perde_centesimi(self):
		calcolo = calcola(
			sanitario(riga("33.33"), riga("33.33", servizio="SRV-2"), riga("33.34", servizio="SRV-3")),
			tipo_cassa=TipoCassa.ENPAP,
		)
		quote = sum(r.cassa for r in calcolo.righe)
		self.assertEqual(quote, calcolo.cassa)
		self.assertEqual(calcolo.totale, calcolo.totale_ts)
