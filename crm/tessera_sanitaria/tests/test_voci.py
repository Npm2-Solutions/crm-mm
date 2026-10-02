# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The Sistema TS choices in words, as the specification says them.

The expense types' descriptions are pinned to the specification (730 - Spese
Sanitarie, WS sincrono v1.3, Tabella 4): before, `SR` read "intramoenia" and `CT`
"certificazione medica", which is how a centre picks the wrong code for every visit.
"""

from __future__ import annotations

import json
import pathlib

from crm.invoicing.engine import voci
from crm.invoicing.tests.base import UnitTestCase
from crm.invoicing.tests.test_voci import msgid_tradotti
from crm.tessera_sanitaria.engine import codici
from crm.tessera_sanitaria.engine import voci as voci_ts

RADICE = pathlib.Path(__file__).resolve().parents[3]

CAMPI = {
	("crm/invoicing/doctype/crm_billable_service", "ts_expense_type"): "tipo_spesa",
	("crm/invoicing/doctype/crm_billable_service", "ts_expense_flag"): "flag_tipo_spesa",
	("crm/invoicing/doctype/crm_invoice_item", "ts_expense_type"): "tipo_spesa",
	("crm/invoicing/doctype/crm_invoice_item", "ts_expense_flag"): "flag_tipo_spesa",
	("crm/invoicing/doctype/crm_invoicing_company", "sender_category"): "soggetto_inviante",
	("crm/invoicing/doctype/crm_professional_qualification", "sender_category"): "soggetto_inviante",
	("crm/invoicing/doctype/crm_invoicing_company", "ts_mode"): "modalita_invio_ts",
	("crm/invoicing/doctype/crm_invoicing_company", "ts_delegation_status"): "stato_delega",
	("crm/invoicing/doctype/crm_invoice", "ts_operation"): "operazione_ts",
}


class LeParoleDelSistemaTS(UnitTestCase):
	def setUp(self):
		voci_ts.registra()

	def test_ogni_valore_ammesso_ha_un_nome(self):
		for (cartella, campo), famiglia in CAMPI.items():
			nome = cartella.rsplit("/", 1)[-1]
			dati = json.loads((RADICE / cartella / f"{nome}.json").read_text())
			definizione = next(f for f in dati["fields"] if f.get("fieldname") == campo)
			ammessi = {v for v in (definizione.get("options") or "").split("\n") if v}
			nominati = {voce.valore for voce in voci.tutte(famiglia)}
			self.assertEqual(ammessi - nominati, set(), f"{nome}.{campo}")

	def test_ogni_tipo_di_spesa_della_matrice_ha_un_nome(self):
		usati = set().union(*codici.TIPI_SPESA_PER_SOGGETTO.values())
		self.assertEqual(usati - {voce.valore for voce in voci_ts.TIPO_SPESA}, set())

	def test_le_descrizioni_sono_quelle_della_specifica(self):
		self.assertEqual(codici.DESCRIZIONE_TIPO_SPESA["CT"], "Cure termali")
		self.assertTrue(codici.DESCRIZIONE_TIPO_SPESA["SR"].startswith("Prestazioni sanitarie: assistenza"))
		self.assertIn("ECG, spirometria", codici.DESCRIZIONE_TIPO_SPESA["AS"])
		self.assertIn("medicina estetica", codici.DESCRIZIONE_TIPO_SPESA["IC"])
		self.assertEqual(codici.DESCRIZIONE_TIPO_SPESA["AA"], "Altre spese")

	def test_nel_profilo_sanitario_non_c_e_non_sanitario(self):
		valori = [voce.valore for voce in voci.voci("soggetto_inviante", voci.SANITARIO)]
		self.assertNotIn("non_sanitario", valori)
		self.assertEqual(valori[0], "professionista_sanitario")

	def test_un_fisioterapista_ha_un_solo_tipo_di_spesa(self):
		ammessi = codici.tipi_spesa_ammessi("professionista_sanitario")
		valori = [voce.valore for voce in voci.voci("tipo_spesa", voci.SANITARIO, ammessi=ammessi)]
		self.assertEqual(valori, ["SP"])

	def test_ogni_parola_e_tradotta(self):
		tradotti = msgid_tradotti()
		mancanti = sorted(
			{
				testo
				for famiglia in voci_ts.FAMIGLIE.values()
				for voce in famiglia
				for testo in (voce.etichetta, voce.spiegazione)
				if testo and testo not in tradotti
			}
		)
		self.assertEqual(mancanti, [])
