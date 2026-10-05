# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What leaves by itself, where the centre switched it on - on a real site, with a
fake Itala and a fake Sistema TS.

Both switches start off: an issued invoice waits for «Send to the SdI», an expense
for «Report». On, the invoice leaves after its issue is committed, and the night
reports what the Sistema TS has not had yet; what stops is told, never retried in
a loop.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe

from crm.invoicing import automatico, connessione
from crm.tessera_sanitaria import automatico as ts_automatico
from crm.tests import test_prova as P
from crm.tests.test_itala_flusso import ConItala

IMPOSTAZIONI = "CRM Invoicing Settings"


class SpentiDiPartenzaTest(P.Base):
	def test_i_due_interruttori_partono_spenti(self):
		meta = frappe.get_meta(IMPOSTAZIONI)
		self.assertEqual(meta.get_field("auto_send_sdi").default, "0")
		self.assertEqual(meta.get_field("auto_send_ts").default, "0")


class SdiAllEmissioneTest(ConItala):
	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.db.set_single_value, IMPOSTAZIONI, "auto_send_sdi", 0)

	def test_spento_la_fattura_aspetta_il_pulsante(self):
		frappe.db.set_single_value(IMPOSTAZIONI, "auto_send_sdi", 0)
		with patch("frappe.enqueue") as accoda:
			documento = self.emessa(self.trattamento.name, self.osteopata.name)
		accoda.assert_not_called()
		self.assertFalse(automatico.da_inviare_allo_sdi(documento))

	def test_acceso_parte_dopo_l_emissione(self):
		frappe.db.set_single_value(IMPOSTAZIONI, "auto_send_sdi", 1)
		with patch("frappe.enqueue") as accoda:
			documento = self.emessa(self.trattamento.name, self.osteopata.name)
		accoda.assert_called_once()
		self.assertEqual(accoda.call_args.kwargs["invoice"], documento.name)
		# after the issue is committed: the issue never waits on Itala
		self.assertTrue(accoda.call_args.kwargs["enqueue_after_commit"])

		sessione = self.con(
			lambda metodo, url, argomenti: P.Risposta(
				200, {"id": "991", "sdi_nome_file": "IT0123_abc12.xml", "sdi_stato": "INVI"}
			)
		)
		automatico.invia_allo_sdi(documento.name)
		documento.reload()
		self.assertEqual(documento.sdi_status, "inviato")
		self.assertEqual(documento.sdi_provider_id, "991")
		# sent once: the job again finds nothing to send
		chiamate = len(sessione.chiamate)
		automatico.invia_allo_sdi(documento.name)
		self.assertEqual(len(sessione.chiamate), chiamate)

	def test_una_seduta_a_una_persona_non_va_allo_sdi(self):
		frappe.db.set_single_value(IMPOSTAZIONI, "auto_send_sdi", 1)
		with patch("frappe.enqueue") as accoda:
			self.emessa(self.seduta.name, self.psicologo.name)
		accoda.assert_not_called()

	def test_quello_che_non_parte_si_dice_e_aspetta(self):
		frappe.db.set_single_value(IMPOSTAZIONI, "auto_send_sdi", 1)
		with patch("frappe.enqueue"):
			documento = self.emessa(self.trattamento.name, self.osteopata.name)
		self.con(lambda metodo, url, argomenti: P.Risposta(400, {"error": "Cedente non abilitato"}))
		with patch("crm.invoicing.monitoraggio.avvisa") as avvisa, patch("frappe.db.rollback"):
			self.assertIsNone(automatico.invia_allo_sdi(documento.name))
		avvisa.assert_called_once()
		self.assertIn("Cedente non abilitato", avvisa.call_args.args[2])
		documento.reload()
		self.assertEqual(documento.sdi_status, "da_inviare")


class SistemaTsDiNotteTest(P.Base):
	def setUp(self):
		super().setUp()
		self.imposta(
			provider_environment=connessione.PRODUZIONE,
			sdi_mode="export",
			sender_category="professionista_sanitario",
			ts_mode="credenziali_studio",
		)
		self.addCleanup(frappe.db.set_single_value, IMPOSTAZIONI, "auto_send_ts", 0)

	def test_spento_di_notte_non_parte_niente(self):
		frappe.db.set_single_value(IMPOSTAZIONI, "auto_send_ts", 0)
		self.emessa()
		with patch("crm.tessera_sanitaria.trasporto.invia_documento") as invia:
			self.assertEqual(ts_automatico.ogni_notte(), {})
		invia.assert_not_called()

	def test_acceso_parte_quello_che_aspetta(self):
		frappe.db.set_single_value(IMPOSTAZIONI, "auto_send_ts", 1)
		seduta = self.emessa()
		self.assertEqual(seduta.ts_status, "da_inviare")
		with (
			patch(
				"crm.tessera_sanitaria.trasporto.invia_documento",
				return_value={"accepted": True, "summary": "ok"},
			) as invia,
			patch("frappe.db.commit"),
		):
			esiti = ts_automatico.ogni_notte()
		invia.assert_any_call(seduta.name)
		self.assertGreaterEqual(esiti[self.azienda.name]["sent"], 1)

	def test_uno_rifiutato_si_dice_e_non_si_rimanda(self):
		frappe.db.set_single_value(IMPOSTAZIONI, "auto_send_ts", 1)
		seduta = self.emessa()
		with (
			patch(
				"crm.tessera_sanitaria.trasporto.invia_documento",
				return_value={"accepted": False, "summary": "Codice fiscale non valido"},
			),
			patch("frappe.db.commit"),
			patch("crm.invoicing.monitoraggio.avvisa") as avvisa,
		):
			esiti = ts_automatico.ogni_notte()
		self.assertTrue(esiti[self.azienda.name]["stopped"])
		avvisa.assert_called_once()
		# refused, it is the desk's to correct: the night does not send it again
		seduta.db_set("ts_status", "scartato")
		self.assertNotIn(seduta.name, ts_automatico.da_comunicare(self.azienda.name))

	def test_una_fattura_di_prova_non_parte_mai(self):
		seduta = self.emessa()
		seduta.db_set("test_document", 1)
		self.assertNotIn(seduta.name, ts_automatico.da_comunicare(self.azienda.name))
