# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The arithmetic, and above all its boundaries.

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


class CassaTest(UnitTestCase):
	def test_enpam_non_espone_alcuna_rivalsa(self):
		calcolo = calcola(
			classifica(
				[riga("200.00", "medico_chirurgo")],
				TipoDestinatario.PERSONA_FISICA,
				soggetto_emittente="medico_odontoiatra",
			),
			tipo_cassa=TipoCassa.ENPAM,
		)
		self.assertEqual(calcolo.cassa, Decimal("0.00"))
		self.assertIsNone(calcolo.percentuale_cassa)

	def test_una_rivalsa_configurata_su_enpam_avvisa(self):
		calcolo = calcola(
			classifica(
				[riga("200.00", "medico_chirurgo")],
				TipoDestinatario.PERSONA_FISICA,
				soggetto_emittente="medico_odontoiatra",
			),
			tipo_cassa=TipoCassa.ENPAM,
			percentuale_cassa=Decimal("2.00"),
			cassa_obbligatoria=True,
		)
		self.assertTrue(any("ENPAM" in a for a in calcolo.avvisi))

	def test_la_rivalsa_inps_e_facoltativa_e_spenta_di_default(self):
		spenta = calcola(sanitario(riga("100.00", "fisioterapista")), tipo_cassa=TipoCassa.INPS)
		accesa = calcola(
			sanitario(riga("100.00", "fisioterapista")),
			tipo_cassa=TipoCassa.INPS,
			applica_rivalsa_facoltativa=True,
		)
		self.assertEqual(spenta.cassa, Decimal("0.00"))
		self.assertEqual(accesa.cassa, Decimal("4.00"))

	def test_il_contributo_integrativo_entra_nella_base_iva(self):
		calcolo = calcola(
			classifica(
				[riga("1000.00", "avvocato", sanitaria=False, esente=False, aliquota="22.00")],
				TipoDestinatario.SOGGETTO_IVA,
			),
			tipo_cassa=TipoCassa.AVVOCATI,
		)
		self.assertEqual(calcolo.cassa, Decimal("40.00"))
		# 22% of 1040, not of 1000.
		self.assertEqual(calcolo.iva, Decimal("228.80"))
		self.assertEqual(calcolo.totale, Decimal("1268.80"))


class RitenutaTest(UnitTestCase):
	def _fattura_avvocato(self, **kwargs):
		return calcola(
			classifica(
				[riga("1000.00", "avvocato", sanitaria=False, esente=False, aliquota="22.00")],
				TipoDestinatario.SOGGETTO_IVA,
			),
			tipo_cassa=TipoCassa.AVVOCATI,
			applica_ritenuta=True,
			**kwargs,
		)

	def test_il_contributo_integrativo_resta_fuori_dalla_ritenuta(self):
		calcolo = self._fattura_avvocato()
		self.assertEqual(calcolo.base_ritenuta, Decimal("1000.00"))
		self.assertEqual(calcolo.ritenuta, Decimal("200.00"))

	def test_la_rivalsa_inps_entra_nella_ritenuta(self):
		calcolo = calcola(
			classifica(
				[riga("1000.00", "consulente", sanitaria=False, esente=False, aliquota="22.00")],
				TipoDestinatario.SOGGETTO_IVA,
			),
			tipo_cassa=TipoCassa.INPS,
			applica_rivalsa_facoltativa=True,
			cassa_soggetta_a_ritenuta=True,
			applica_ritenuta=True,
		)
		self.assertEqual(calcolo.cassa, Decimal("40.00"))
		self.assertEqual(calcolo.base_ritenuta, Decimal("1040.00"))
		self.assertEqual(calcolo.ritenuta, Decimal("208.00"))

	def test_la_ritenuta_non_tocca_il_totale_ma_il_netto_a_pagare(self):
		calcolo = self._fattura_avvocato()
		self.assertEqual(calcolo.totale, Decimal("1268.80"))
		self.assertEqual(calcolo.netto_a_pagare, Decimal("1068.80"))

	def test_senza_ritenuta_il_netto_coincide_col_totale(self):
		calcolo = calcola(sanitario(riga("100.00")))
		self.assertEqual(calcolo.netto_a_pagare, calcolo.totale)


class SplitPaymentTest(UnitTestCase):
	def test_la_pa_non_paga_l_iva_al_fornitore(self):
		calcolo = calcola(
			classifica(
				[riga("1000.00", "societa_servizi", sanitaria=False, esente=False, aliquota="22.00")],
				TipoDestinatario.PUBBLICA_AMMINISTRAZIONE,
			),
			split_payment=True,
		)
		self.assertEqual(calcolo.iva, Decimal("220.00"))
		self.assertEqual(calcolo.totale, Decimal("1220.00"))
		self.assertEqual(calcolo.netto_a_pagare, Decimal("1000.00"))
		self.assertEqual(calcolo.riepiloghi[0].esigibilita, "S")


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


class AnticipazioniTest(UnitTestCase):
	def test_l_anticipazione_resta_fuori_dalla_base_iva(self):
		calcolo = calcola(
			classifica(
				[
					riga("1000.00", "avvocato", sanitaria=False, esente=False, aliquota="22.00"),
					riga(
						"145.00",
						"avvocato",
						sanitaria=False,
						esente=False,
						anticipazione=True,
						servizio="SRV-2",
					),
				],
				TipoDestinatario.SOGGETTO_IVA,
			)
		)
		self.assertEqual(calcolo.imponibile, Decimal("1000.00"))
		self.assertEqual(calcolo.anticipazioni, Decimal("145.00"))
		self.assertEqual(calcolo.iva, Decimal("220.00"))
		self.assertEqual(calcolo.totale, Decimal("1365.00"))

	def test_l_anticipazione_entra_nella_soglia_del_bollo_e_lo_dice(self):
		calcolo = calcola(
			classifica(
				[
					riga("50.00", "avvocato", sanitaria=False, esente=False, aliquota="22.00"),
					riga(
						"40.00",
						"avvocato",
						sanitaria=False,
						esente=False,
						anticipazione=True,
						servizio="SRV-2",
					),
				],
				TipoDestinatario.SOGGETTO_IVA,
			)
		)
		self.assertEqual(calcolo.base_bollo, Decimal("40.00"))
		self.assertFalse(calcolo.bollo_dovuto)

	def test_l_anticipazione_che_fa_scattare_il_bollo_avvisa(self):
		calcolo = calcola(
			classifica(
				[
					riga("50.00", "avvocato", sanitaria=False, esente=False, aliquota="22.00"),
					riga(
						"100.00",
						"avvocato",
						sanitaria=False,
						esente=False,
						anticipazione=True,
						servizio="SRV-2",
					),
				],
				TipoDestinatario.SOGGETTO_IVA,
			)
		)
		self.assertTrue(calcolo.bollo_dovuto)
		self.assertTrue(any("prevailing reading" in a for a in calcolo.avvisi))

	def test_si_puo_tenere_l_anticipazione_fuori_dalla_soglia(self):
		calcolo = calcola(
			classifica(
				[riga("100.00", "avvocato", sanitaria=False, esente=False, anticipazione=True)],
				TipoDestinatario.SOGGETTO_IVA,
			),
			anticipazioni_nella_base_bollo=False,
		)
		self.assertFalse(calcolo.bollo_dovuto)


class ForfettarioTest(UnitTestCase):
	def test_il_forfettario_usa_n2_2_anche_quando_non_lo_stampa(self):
		calcolo = calcola(
			classifica(
				[riga("1000.00", "consulente", sanitaria=False, esente=False)],
				TipoDestinatario.SOGGETTO_IVA,
				regime=RegimeFiscale.FORFETTARIO,
			)
		)
		self.assertEqual(calcolo.iva, Decimal("0.00"))
		self.assertEqual(calcolo.riepiloghi[0].natura, "N2.2")
		self.assertEqual(calcolo.totale, Decimal("1000.00"))
