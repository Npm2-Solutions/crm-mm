# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

"""The provider's vocabulary, and where it is easy to misread.

These run without a site because they cover translation, not transport: what the
provider's words mean here, and which of them means the SdI has actually answered.
The contract they are written against is in `.pi/vendor/itala.md`.

They exercise `engine.busta`, where the translation lives; the adapter re-exports
the same names so a reader finds them where they look.
"""

from __future__ import annotations

import base64

from crm.invoicing.engine import busta as itala
from crm.invoicing.tests.base import UnitTestCase


class StatiTest(UnitTestCase):
	def test_prenotato_e_inviato_sono_entrambi_partiti(self):
		# PREN means taken in charge but not yet at the SdI. From here both are the
		# same thing: it left, nobody has answered.
		self.assertEqual(itala.STATO_PROVIDER["PREN"], "inviato")
		self.assertEqual(itala.STATO_PROVIDER["INVI"], "inviato")

	def test_mancata_consegna_non_e_un_fallimento(self):
		"""The one that gets misread.

		NONC means the SdI has the invoice and filed it in the client's reserved
		area. The invoice is issued and the obligation discharged - what is owed is
		telling the client, not resending.
		"""
		self.assertEqual(itala.STATO_PROVIDER["NONC"], "mancata_consegna")
		self.assertNotEqual(itala.STATO_PROVIDER["NONC"], "errore")

	def test_gli_stati_pa_restano_distinti(self):
		self.assertEqual(itala.STATO_PROVIDER["ACCE"], "accettato")
		self.assertEqual(itala.STATO_PROVIDER["RIFI"], "rifiutato")
		self.assertEqual(itala.STATO_PROVIDER["DECO"], "decorrenza_termini")

	def test_solo_gli_stati_conclusi_hanno_una_notifica_da_scaricare(self):
		# Going to fetch a notice for something still in flight is a wasted call and
		# a 404 to explain.
		self.assertNotIn("INVI", itala.STATI_CON_NOTIFICA)
		self.assertNotIn("PREN", itala.STATI_CON_NOTIFICA)
		for concluso in ("CONS", "NONC", "ACCE", "RIFI", "DECO"):
			self.assertIn(concluso, itala.STATI_CON_NOTIFICA)

	def test_ogni_stato_dichiarato_ha_una_traduzione(self):
		for codice in ("INVI", "PREN", "ERRO", "CONS", "NONC", "ACCE", "RIFI", "DECO"):
			self.assertIn(codice, itala.STATO_PROVIDER, f"{codice} has no meaning here")


class IdentificativoTest(UnitTestCase):
	def test_il_campo_del_provider_viene_prima(self):
		# Their own name for it wins over the generic shapes kept for other providers.
		corpo = {"id": 7, "sdi_identificativo": 12345}
		self.assertEqual(itala.identificativo(corpo), "12345")

	def test_ripiega_sulle_forme_generiche(self):
		self.assertEqual(itala.identificativo({"uuid": "u-1"}), "u-1")

	def test_cerca_anche_annidato(self):
		self.assertEqual(itala.identificativo({"data": {"sdi_identificativo": 9}}), "9")

	def test_niente_identificativo_non_e_un_errore(self):
		self.assertIsNone(itala.identificativo({"sdi_stato": "PREN"}))
		self.assertIsNone(itala.identificativo(None))


class IngressoTest(UnitTestCase):
	def test_legge_l_xml_in_chiaro(self):
		voce = {"sdi_fattura_xml": "<p:FatturaElettronica/>"}
		self.assertEqual(itala.xml_in_ingresso(voce), b"<p:FatturaElettronica/>")

	def test_legge_l_xml_in_base64(self):
		voce = {"sdi_fattura_base64": base64.b64encode(b"<p:FatturaElettronica/>").decode()}
		self.assertEqual(itala.xml_in_ingresso(voce), b"<p:FatturaElettronica/>")

	def test_preferisce_il_chiaro_quando_ci_sono_entrambi(self):
		voce = {
			"sdi_fattura_xml": "<chiaro/>",
			"sdi_fattura_base64": base64.b64encode(b"<codificato/>").decode(),
		}
		self.assertEqual(itala.xml_in_ingresso(voce), b"<chiaro/>")

	def test_base64_illeggibile_non_esplode(self):
		self.assertIsNone(itala.xml_in_ingresso({"sdi_fattura_base64": "non-base64!!"}))

	def test_una_voce_senza_documento_non_ne_inventa_uno(self):
		self.assertIsNone(itala.xml_in_ingresso({"ricezione": 1, "id": 4}))
