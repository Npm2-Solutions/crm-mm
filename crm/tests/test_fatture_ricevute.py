# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The suppliers' invoices, from Itala to the «Received» tab - on a real site with a
fake Itala.

One arrives as Itala listed it at its test door (every value as text), is filed
with its own XML and the amounts read out of it, and whoever manages invoicing is
told. The desk marks it seen, passed to the accountant or disputed, and paid; Itala's
PDF is asked once; the month's files leave as one ZIP for the accountant.
"""

from __future__ import annotations

import base64
import io
import random
import zipfile
from unittest.mock import patch

import frappe

from crm.invoicing import ricevute
from crm.invoicing.sdi import riconciliazione
from crm.invoicing.tests.test_fornitori import FATTURA
from crm.tests import test_prova as P
from crm.tests.test_invoicing import PIVA
from crm.tests.test_itala_flusso import ConItala

FORNITORE = "CRM Supplier Invoice"


def riga_di_itala(identificativo: str = "551096") -> dict:
	"""A supplier's invoice as Itala's list gives it: the XML addressed to the company."""
	xml = FATTURA.replace("Fornitore Prova Srl", "Forniture Mediche Srl")
	xml = xml.replace(
		"</CedentePrestatore>",
		"</CedentePrestatore><CessionarioCommittente><DatiAnagrafici><IdFiscaleIVA>"
		f"<IdPaese>IT</IdPaese><IdCodice>{PIVA}</IdCodice></IdFiscaleIVA></DatiAnagrafici>"
		"</CessionarioCommittente>",
	)
	return {
		"id": identificativo,
		"ricezione": "1",
		"partita_iva": PIVA,
		"sdi_identificativo": "5510960",
		"sdi_stato": "",
		"sdi_nome_file": f"IT00743110157_{identificativo[-5:]}.xml",
		"sdi_fattura_base64": base64.b64encode(xml.encode()).decode(),
		"data": "2026-10-05 12:57:34",
		"numero_documento": "F-2026-17",
		"data_documento": "2026-10-05",
		"tipo_documento": "TD01",
		"dati_documento": {"mittente": {"Denominazione": "Forniture Mediche Srl"}},
	}


class RicevuteTest(ConItala):
	def ricevuta(self, identificativo: str | None = None) -> str:
		# never one a site already holds (a dev site keeps what came from Itala)
		identificativo = identificativo or str(900000000 + random.randint(1, 99999999))
		self.identificativo = identificativo
		with patch("crm.invoicing.ricevute.annuncia") as annuncia:
			esito = riconciliazione.riconcilia(self.emittente(), [riga_di_itala(identificativo)])
		self.assertEqual(esito["incoming"], 1)
		annuncia.assert_called_once()
		return frappe.db.get_value(FORNITORE, {"provider_id": identificativo}, "name")

	def test_arriva_con_i_suoi_importi_letti_dall_xml(self):
		nome = self.ricevuta()
		doc = frappe.get_doc(FORNITORE, nome)
		self.assertEqual(doc.supplier_name, "Forniture Mediche Srl")
		self.assertEqual(doc.supplier_tax_id, "00743110157")
		self.assertEqual((doc.total_amount, doc.taxable_amount, doc.vat_amount), (61.0, 50.0, 11.0))
		self.assertEqual(str(doc.due_date), "2026-11-04")
		self.assertEqual(doc.status, "ricevuta")
		self.assertTrue(doc.xml_file)

	def test_l_elenco_e_il_dettaglio(self):
		nome = self.ricevuta()
		elenco = ricevute.get_received(company=self.azienda.name)
		self.assertIn(nome, [r.name for r in elenco["rows"]])
		self.assertGreaterEqual(elenco["to_see"], 1)
		self.assertIn(nome, [r.name for r in ricevute.get_received(search="Mediche")["rows"]])
		dettaglio = ricevute.get_received_invoice(nome)
		self.assertEqual(dettaglio["lines"][0]["description"], "Materiale di consumo")
		self.assertTrue(dettaglio["can"]["write"])

	def test_vista_registrata_contestata_pagata(self):
		nome = self.ricevuta()
		self.assertEqual(ricevute.set_received_status(nome, "letta")["status"], "letta")
		with self.assertRaises(frappe.ValidationError):
			# disputed says why: the supplier will ask
			ricevute.set_received_status(nome, "rifiutata")
		vista = ricevute.set_received_status(nome, "rifiutata", "Merce non arrivata")
		self.assertEqual((vista["status"], vista["notes"]), ("rifiutata", "Merce non arrivata"))
		self.assertEqual(str(ricevute.set_received_paid(nome, "2026-10-20")["paid_on"]), "2026-10-20")
		self.assertIsNone(ricevute.set_received_paid(nome)["paid_on"])
		with self.assertRaises(frappe.ValidationError):
			ricevute.set_received_status(nome, "inventata")

	def test_da_pagare(self):
		nome = self.ricevuta()
		self.assertIn(nome, [r.name for r in ricevute.get_received(status="da_pagare")["rows"]])
		ricevute.set_received_paid(nome, "2026-10-20")
		self.assertNotIn(nome, [r.name for r in ricevute.get_received(status="da_pagare")["rows"]])

	def test_il_pdf_si_chiede_a_itala_una_volta(self):
		nome = self.ricevuta()
		sessione = self.con(lambda metodo, url, argomenti: P_pdf(url))
		primo = ricevute.make_received_pdf(nome)["file"]
		self.assertTrue(primo)
		self.assertTrue(sessione.chiamate[-1]["url"].endswith(f"/fatture/{self.identificativo}/pdf"))
		chiamate = len(sessione.chiamate)
		self.assertEqual(ricevute.make_received_pdf(nome)["file"], primo)
		self.assertEqual(len(sessione.chiamate), chiamate)

	def test_chi_gestisce_la_fatturazione_lo_sa(self):
		nome = self.ricevuta()
		with patch("crm.notifiche.avvisi.avvisa") as avvisa:
			ricevute.annuncia(nome)
		for chiamata in avvisa.call_args_list:
			self.assertEqual(chiamata.args[1], "Invoicing")
			self.assertEqual(chiamata.args[3][0], "Forniture Mediche Srl")
			self.assertEqual(chiamata.kwargs["oggetto"], (FORNITORE, nome))

	def test_il_mese_per_il_commercialista(self):
		self.ricevuta()
		emessa = self.emessa(self.trattamento.name, self.osteopata.name)
		emessa.db_set("test_document", 0)
		ricevute.export_month(self.azienda.name, 2026, 10)
		archivio = zipfile.ZipFile(io.BytesIO(frappe.local.response.filecontent))
		nomi = archivio.namelist()
		self.assertTrue(any(n.startswith("ricevute/") for n in nomi))
		self.assertTrue(any(n.startswith("emesse/") for n in nomi))
		self.assertEqual(frappe.local.response.filename, "fatture-2026-10.zip")


def P_pdf(url: str):
	if url.endswith("/pdf"):
		from pypdf import PdfWriter

		pagina = io.BytesIO()
		scrittore = PdfWriter()
		scrittore.add_blank_page(width=100, height=100)
		scrittore.write(pagina)
		risposta = P.Risposta(200)
		risposta.content = pagina.getvalue()
		return risposta
	return P.Risposta(404, {"error": "no"})
