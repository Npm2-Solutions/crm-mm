# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

"""Reading an envelope sent by somebody who has not proved who they are yet.

These run without a site because the decision they cover - who gets in - should be
provable wherever this is checked out. The payload contract is unverified, so what
is pinned here is the *defensive* behaviour: what happens when the shape is not the
one that was guessed.
"""

import base64
import unittest

from crm.invoicing.engine import busta
from crm.invoicing.tests.base import UnitTestCase


class TokenTest(UnitTestCase):
	def test_legge_l_intestazione_dedicata(self):
		self.assertEqual(busta.token_presentato({"X-Provider-Token": "abc"}, {}), "abc")

	def test_sbuccia_bearer(self):
		# A provider told to use a header named Bearer sends "Authorization: Bearer x".
		self.assertEqual(busta.token_presentato({"Authorization": "Bearer x"}, {}), "x")

	def test_accetta_authorization_nudo(self):
		self.assertEqual(busta.token_presentato({"Authorization": "soloilsegreto"}, {}), "soloilsegreto")

	def test_legge_la_query_quando_non_c_e_intestazione(self):
		self.assertEqual(busta.token_presentato({}, {"token": "q"}), "q")

	def test_l_intestazione_vince_sulla_query(self):
		self.assertEqual(busta.token_presentato({"X-Provider-Token": "h"}, {"token": "q"}), "h")

	def test_niente_token_e_stringa_vuota(self):
		self.assertEqual(busta.token_presentato({}, {}), "")

	def test_spazi_non_contano(self):
		self.assertEqual(busta.token_presentato({"X-Provider-Token": "  abc  "}, {}), "abc")


class SegretoTest(UnitTestCase):
	def test_uguali_passano(self):
		self.assertTrue(busta.segreto_corrisponde("abc", "abc"))

	def test_diversi_non_passano(self):
		self.assertFalse(busta.segreto_corrisponde("abc", "abd"))

	def test_un_segreto_non_configurato_non_apre_niente(self):
		# The case that matters: a company that never generated a secret must not be
		# opened by a caller that presents nothing.
		self.assertFalse(busta.segreto_corrisponde("", ""))
		self.assertFalse(busta.segreto_corrisponde("", None))
		self.assertFalse(busta.segreto_corrisponde("qualcosa", None))

	def test_un_prefisso_non_basta(self):
		self.assertFalse(busta.segreto_corrisponde("abc", "abcdef"))


class CercaTest(UnitTestCase):
	def test_trova_in_superficie(self):
		self.assertEqual(busta.cerca({"uuid": "u1"}, busta.CHIAVI_UUID), "u1")

	def test_trova_annidato(self):
		self.assertEqual(busta.cerca({"data": {"invoice": {"uuid": "u2"}}}, busta.CHIAVI_UUID), "u2")

	def test_attraversa_le_liste(self):
		self.assertEqual(busta.cerca({"items": [{"uuid": "u3"}]}, busta.CHIAVI_UUID), "u3")

	def test_rispetta_l_ordine_delle_chiavi(self):
		# uuid comes before id, so an envelope carrying both answers with uuid.
		self.assertEqual(busta.cerca({"id": "b", "uuid": "a"}, busta.CHIAVI_UUID), "a")

	def test_si_ferma_in_profondita(self):
		profondo = {"a": {"b": {"c": {"d": {"e": {"uuid": "troppo"}}}}}}
		self.assertIsNone(busta.cerca(profondo, busta.CHIAVI_UUID))

	def test_ignora_i_valori_non_stringa(self):
		self.assertIsNone(busta.cerca({"uuid": 12}, busta.CHIAVI_UUID))

	def test_ignora_le_stringhe_vuote(self):
		self.assertEqual(busta.cerca({"uuid": "   ", "id": "vero"}, busta.CHIAVI_UUID), "vero")


class ContenutoTest(UnitTestCase):
	def test_xml_diretto(self):
		self.assertEqual(busta.forse_xml("<RC>ok</RC>"), b"<RC>ok</RC>")

	def test_base64(self):
		codificato = base64.b64encode(b"<RC>ok</RC>").decode()
		self.assertEqual(busta.forse_xml(codificato), b"<RC>ok</RC>")

	def test_base64_che_non_e_un_documento_viene_rifiutato(self):
		# The guard that matters: base64 is not a licence to hand arbitrary bytes to
		# the notice parser.
		self.assertIsNone(busta.forse_xml(base64.b64encode(b"non un documento").decode()))

	def test_testo_qualunque_viene_rifiutato(self):
		self.assertIsNone(busta.forse_xml("ciao"))

	def test_vuoto_viene_rifiutato(self):
		self.assertIsNone(busta.forse_xml(""))
		self.assertIsNone(busta.forse_xml("   "))


class FormaTest(UnitTestCase):
	def test_descrive_senza_citare(self):
		corpo = {"event": "customer-notification", "uuid": "u1", "attachment": "PHNlZ3JldG8+"}
		descritta = busta.forma(corpo)
		self.assertEqual(descritta["event"], "customer-notification")
		self.assertEqual(descritta["uuid"], "u1")
		self.assertIn("attachment", descritta["keys"])
		# The point of the whole function: the names travel, the values never do.
		self.assertNotIn("PHNlZ3JldG8+", str(descritta))

	def test_corpo_vuoto_non_esplode(self):
		self.assertEqual(busta.forma({}), {"keys": [], "event": None, "uuid": None})


class EventoTest(UnitTestCase):
	def test_la_notifica_doveva_portare_qualcosa(self):
		self.assertTrue(busta.porta_una_notifica(busta.EVENTO_NOTIFICA))

	def test_anche_i_guasti(self):
		for evento in busta.EVENTI_GUASTO:
			self.assertTrue(busta.porta_una_notifica(evento))

	def test_una_fattura_inviata_e_solo_una_notizia(self):
		self.assertFalse(busta.porta_una_notifica(busta.EVENTO_INVIATA))
		self.assertFalse(busta.porta_una_notifica(busta.EVENTO_RICEVUTA))

	def test_nessun_evento(self):
		self.assertFalse(busta.porta_una_notifica(None))
		self.assertFalse(busta.porta_una_notifica(""))


if __name__ == "__main__":
	unittest.main()
