# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The triple, and the two symmetrical mistakes it exists to prevent.

Sending a healthcare invoice for a natural person to the SdI is a privacy breach.
Not sending an osteopath's is the violation in reverse. Both are here.
"""

from __future__ import annotations

from decimal import Decimal

from crm.invoicing.engine.classificazione import (
	GuardiaSdI,
	RigaDaClassificare,
	classifica,
	guardia_sdi,
	natura_territoriale,
)
from crm.invoicing.engine.codici import Canale, RegolaSdI, TipoDestinatario
from crm.invoicing.tests.base import UnitTestCase


def riga(qualifica: str, *, sanitaria=True, esente=True, importo="100.00", servizio="SRV-1", **kwargs):
	return RigaDaClassificare(
		servizio_id=servizio,
		descrizione_fiscale="Prestazione",
		is_sanitaria=sanitaria,
		esente_iva=esente,
		erogatore_id="ERO-1",
		erogatore_qualifica=qualifica,
		imponibile=Decimal(importo),
		**kwargs,
	)


class RisoluzioneNoveTest(UnitTestCase):
	"""Risoluzione AdE n. 9 del 24 febbraio 2026, the four counter-intuitive cases."""

	def _paziente(self, *righe, emittente="professionista_sanitario"):
		return classifica(list(righe), TipoDestinatario.PERSONA_FISICA, soggetto_emittente=emittente)

	def test_il_massoterapista_e_esente_vietato_sdi_e_va_al_ts(self):
		esito = self._paziente(riga("massoterapista", tipo_spesa_catalogo="SP"))
		self.assertEqual(esito.canale, Canale.PDF_TS)
		self.assertFalse(esito.sdi_consentito)
		self.assertTrue(esito.ts_richiesto)
		self.assertEqual(esito.righe[0].tipo_spesa, "SP")
		self.assertEqual(esito.righe[0].natura_iva, "N4")

	def test_l_osteopata_e_imponibile_e_deve_passare_da_sdi(self):
		esito = self._paziente(riga("osteopata", esente=False))
		self.assertEqual(esito.canale, Canale.SDI)
		self.assertTrue(esito.sdi_consentito)
		self.assertFalse(esito.ts_richiesto)
		self.assertEqual(esito.righe[0].aliquota, Decimal("22.00"))

	def test_il_chinesiologo_non_e_professione_sanitaria(self):
		esito = self._paziente(riga("chinesiologo", esente=False))
		self.assertEqual(esito.canale, Canale.SDI)
		self.assertIsNone(esito.righe[0].natura_iva)

	def test_dichiarare_esente_un_osteopata_e_un_errore_bloccante(self):
		esito = self._paziente(riga("osteopata", esente=True))
		self.assertFalse(esito.valido)
		self.assertTrue(any("Risoluzione AdE n. 9" in e for e in esito.tutti_errori))


class GuardiaTest(UnitTestCase):
	def test_la_guardia_blocca_il_sanitario_verso_persona_fisica(self):
		esito = classifica(
			[riga("psicologo")],
			TipoDestinatario.PERSONA_FISICA,
			soggetto_emittente="professionista_sanitario",
		)
		with self.assertRaises(GuardiaSdI) as blocco:
			guardia_sdi(esito)
		self.assertIn("D.Lgs. 12 giugno 2025 n. 81", str(blocco.exception))
		self.assertTrue(blocco.exception.righe)

	def test_la_guardia_e_una_permission_error_non_un_input_malformato(self):
		esito = classifica([riga("psicologo")], TipoDestinatario.PERSONA_FISICA)
		self.assertTrue(issubclass(GuardiaSdI, PermissionError))
		with self.assertRaises(PermissionError):
			guardia_sdi(esito)

	def test_la_guardia_lascia_passare_l_osteopata(self):
		esito = classifica([riga("osteopata", esente=False)], TipoDestinatario.PERSONA_FISICA)
		guardia_sdi(esito)  # must not raise

	def test_la_guardia_lascia_passare_il_sanitario_verso_soggetto_iva(self):
		esito = classifica([riga("medico_competente", esente=False)], TipoDestinatario.SOGGETTO_IVA)
		guardia_sdi(esito)


class DocumentoMistoTest(UnitTestCase):
	def test_sanitario_piu_osteopata_non_e_emettibile(self):
		esito = classifica(
			[riga("psicologo"), riga("osteopata", esente=False, servizio="SRV-2")],
			TipoDestinatario.PERSONA_FISICA,
			soggetto_emittente="professionista_sanitario",
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("two separate documents" in e for e in esito.tutti_errori))

	def test_una_riga_sanitaria_porta_fuori_da_sdi_tutto_il_documento(self):
		esito = classifica(
			[riga("psicologo"), riga("consulente", sanitaria=False, esente=False, servizio="SRV-2")],
			TipoDestinatario.PERSONA_FISICA,
			soggetto_emittente="professionista_sanitario",
		)
		self.assertEqual(esito.canale, Canale.PDF_TS)
		self.assertFalse(esito.sdi_consentito)
		self.assertTrue(any("separate document" in a for a in esito.tutti_avvisi))

	def test_al_sistema_ts_va_solo_la_quota_sanitaria(self):
		esito = classifica(
			[riga("psicologo"), riga("consulente", sanitaria=False, esente=False, servizio="SRV-2")],
			TipoDestinatario.PERSONA_FISICA,
			soggetto_emittente="professionista_sanitario",
		)
		self.assertEqual(len(esito.righe_ts), 1)
		self.assertEqual(esito.righe_ts[0].riga.erogatore_qualifica, "psicologo")


class TipoSpesaTest(UnitTestCase):
	"""The expense type follows the register of whoever issues, not the service."""

	def test_una_struttura_non_puo_usare_sp(self):
		esito = classifica(
			[riga("fisioterapista", tipo_spesa_catalogo="SP")],
			TipoDestinatario.PERSONA_FISICA,
			soggetto_emittente="struttura_autorizzata",
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("not admitted to whoever issues" in e for e in esito.tutti_errori))

	def test_il_professionista_in_proprio_non_deve_scegliere(self):
		esito = classifica(
			[riga("fisioterapista")],
			TipoDestinatario.PERSONA_FISICA,
			soggetto_emittente="professionista_sanitario",
		)
		self.assertEqual(esito.righe[0].tipo_spesa, "SP")

	def test_la_struttura_con_piu_codici_deve_scegliere(self):
		esito = classifica(
			[riga("fisioterapista")],
			TipoDestinatario.PERSONA_FISICA,
			soggetto_emittente="struttura_autorizzata",
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("not determinable" in e for e in esito.tutti_errori))

	def test_la_quota_non_a_carico_va_in_aa(self):
		esito = classifica(
			[riga("medico_chirurgo", quota_non_a_carico=Decimal("30.00"))],
			TipoDestinatario.PERSONA_FISICA,
			soggetto_emittente="medico_odontoiatra",
		)
		self.assertEqual(esito.righe[0].tipo_spesa, "AA")

	def test_il_flag_tipo_spesa_deve_accompagnare_il_codice_giusto(self):
		esito = classifica(
			[riga("medico_chirurgo", tipo_spesa_catalogo="SR", flag_tipo_spesa="1")],
			TipoDestinatario.PERSONA_FISICA,
			soggetto_emittente="medico_odontoiatra",
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("flagTipoSpesa=1" in e for e in esito.tutti_errori))


class SenzaSchedaTest(UnitTestCase):
	def test_un_servizio_senza_scheda_non_e_fatturabile(self):
		esito = classifica([riga("psicologo", servizio=None)], TipoDestinatario.PERSONA_FISICA)
		self.assertFalse(esito.valido)
		self.assertTrue(any("without a card" in e for e in esito.tutti_errori))

	def test_una_riga_senza_erogatore_non_si_classifica(self):
		linea = riga("psicologo")
		linea.erogatore_qualifica = None
		esito = classifica([linea], TipoDestinatario.PERSONA_FISICA)
		self.assertFalse(esito.valido)
		self.assertTrue(any("no performer" in e for e in esito.tutti_errori))

	def test_una_qualifica_non_censita_non_si_indovina(self):
		esito = classifica([riga("rabdomante")], TipoDestinatario.PERSONA_FISICA)
		self.assertFalse(esito.valido)
		self.assertTrue(any("never infers" in e for e in esito.tutti_errori))

	def test_un_documento_senza_righe_non_esiste(self):
		esito = classifica([], TipoDestinatario.PERSONA_FISICA)
		self.assertFalse(esito.valido)
		self.assertEqual(esito.canale, Canale.PDF_SOLO)


class EuropaTest(UnitTestCase):
	"""Cross-border clients are the ordinary case here, not an exception."""

	def test_il_cliente_estero_passa_comunque_da_sdi(self):
		esito = classifica([riga("consulente", sanitaria=False, esente=False)], TipoDestinatario.ESTERO)
		self.assertEqual(esito.canale, Canale.SDI)
		self.assertTrue(esito.sdi_consentito)

	def test_la_regola_territoriale_suggerisce_ma_non_decide(self):
		natura, avviso = natura_territoriale(TipoDestinatario.ESTERO, "DE", True)
		self.assertEqual(natura, "N2.1")
		self.assertIn("7-quater", avviso)

	def test_verso_un_privato_estero_non_propone_nulla(self):
		natura, avviso = natura_territoriale(TipoDestinatario.ESTERO, "ES", False)
		self.assertIsNone(natura)
		self.assertIn("OSS", avviso)

	def test_in_italia_non_c_e_questione_territoriale(self):
		self.assertEqual(natura_territoriale(TipoDestinatario.SOGGETTO_IVA, "IT", True), (None, ""))

	def test_il_reverse_charge_dichiarato_in_catalogo_e_rispettato(self):
		esito = classifica(
			[riga("societa_servizi", sanitaria=False, esente=False, natura_iva_catalogo="N6.7")],
			TipoDestinatario.SOGGETTO_IVA,
		)
		self.assertTrue(esito.righe[0].reverse_charge)
		self.assertEqual(esito.righe[0].aliquota, Decimal("0.00"))
		self.assertEqual(esito.righe[0].regola_sdi, RegolaSdI.OBBLIGATORIO)
