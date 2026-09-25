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
