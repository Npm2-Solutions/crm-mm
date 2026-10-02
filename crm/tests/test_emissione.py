# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The invoice made inside DottorCloud, on a real site.

A psychotherapy session for Mario Rossi: while it is typed the dialog says where it
goes - a PDF to him and the expense to the Sistema TS - and what it adds up to,
and nothing is saved until somebody says so. Issued, it has its number; corrected,
a credit note says which invoice it corrects and goes to the Sistema TS as the
refund of that invoice, with the original's identifier.
"""

from __future__ import annotations

import frappe

from crm.invoicing import api, documento, emissione
from crm.invoicing.engine.messaggi import Messaggio
from crm.invoicing.sdi import ricezione
from crm.tests.test_invoicing import CF_PAZIENTE, PIVA, InvoicingBase


class LaFatturaDentroDottorCloud(InvoicingBase):
	def dati(self, **altro):
		return {
			"billing_name": "Mario Rossi",
			"first_name": "Mario",
			"last_name": "Rossi",
			"fiscal_code": CF_PAZIENTE,
			"recipient_type": "persona_fisica",
			"payment_method": "MP08",
			"items": [
				{
					"billable_service": self.seduta.name,
					"service_provider": self.psicologo.name,
					"qty": 1,
					"rate": 100,
				}
			],
			**altro,
		}

	def test_l_anteprima_dice_dove_va_e_non_salva_niente(self):
		prima = frappe.db.count("CRM Invoice")
		vista = emissione.preview(self.dati())
		self.assertIsNone(vista["name"])
		self.assertEqual(vista["destination"]["value"], "pdf_ts")
		self.assertTrue(vista["destination"]["label"])
		self.assertEqual(vista["errors"], [])
		self.assertEqual(vista["totals"]["grand_total"], 102.0)
		self.assertEqual(vista["items"][0]["service_label"], self.seduta.name)
		self.assertIn("MP08", [s["value"] for s in vista["options"]["payment_method"]])
		self.assertEqual(frappe.db.count("CRM Invoice"), prima)

	def test_senza_righe_dice_cosa_manca(self):
		vista = emissione.preview(self.dati(items=[]))
		self.assertTrue(vista["errors"])
		self.assertFalse(vista["can"]["issue"] and not vista["errors"])

	def test_si_salva_si_emette_e_si_corregge(self):
		bozza = emissione.save(self.dati())
		self.assertTrue(bozza["name"])
		self.assertEqual(bozza["docstatus"], 0)
		bozza = emissione.save(self.dati(payment_method="MP01"), invoice=bozza["name"])
		self.assertEqual(bozza["payment"]["payment_method"], "MP01")

		emessa = emissione.issue(self.dati(), invoice=bozza["name"])
		self.assertEqual(emessa["docstatus"], 1)
		self.assertTrue(emessa["document_number"])
		self.assertTrue(emessa["can"]["credit_note"])
		self.assertFalse(emessa["can"]["issue"])

		nota = emissione.credit_note(emessa["name"])
		self.assertEqual(nota["document_type"]["value"], "TD04")
		self.assertTrue(nota["is_note"])
		self.assertEqual(nota["reference"]["number"], emessa["document_number"])
		self.assertEqual(len(nota["items"]), 1)
		self.assertFalse(nota["can"]["credit_note"])

		# to the Sistema TS: the refund of the original, which it names
		from crm.tessera_sanitaria import documento as ts

		doc = frappe.get_doc("CRM Invoice", nota["name"])
		self.assertEqual(doc.ts_operation, "R")
		spesa = ts.documento_spesa(doc, documento.azienda(doc))
		self.assertEqual(spesa.id_rimborso.num_documento, emessa["document_number"])

	def test_una_bozza_si_butta_una_fattura_emessa_no(self):
		bozza = emissione.save(self.dati())
		emissione.delete_draft(bozza["name"])
		self.assertFalse(frappe.db.exists("CRM Invoice", bozza["name"]))
		emessa = emissione.issue(self.dati())
		with self.assertRaises(frappe.ValidationError):
			emissione.delete_draft(emessa["name"])

	def test_una_riga_senza_chi_l_ha_eseguita_lo_dice(self):
		vista = emissione.preview(
			self.dati(items=[{"billable_service": self.seduta.name, "qty": 1, "rate": 0}])
		)
		self.assertTrue(any("Line 1" in errore for errore in vista["errors"]))
		# no total and no destination while a line is incomplete: neither would be the invoice's
		self.assertIsNone(vista["totals"])
		self.assertIsNone(vista["destination"])
		# the card's price comes with the service, while who performed it is chosen
		self.assertEqual(vista["items"][0]["rate"], 100)
		self.assertEqual(vista["items"][0]["amount"], 100)

	def test_a_una_persona_la_fattura_col_suo_nome(self):
		persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Giulia", "last_name": "Neri", "organization": "Acme Srl"}
		).insert(ignore_permissions=True)
		dati = self.dati(party_type="CRM Lead", party=persona.name)
		for campo in ("billing_name", "first_name", "last_name"):
			dati.pop(campo)
		self.assertEqual(emissione.preview(dati)["client"]["billing_name"], "Giulia Neri")
		# a company with a VAT number is invoiced in the company's name
		dati.update(recipient_type="soggetto_iva", tax_id=PIVA)
		self.assertEqual(emissione.preview(dati)["client"]["billing_name"], "Acme Srl")

	def test_chi_riceve_decide_la_ritenuta(self):
		frappe.db.set_value("CRM Invoicing Company", self.azienda.name, "apply_withholding_by_default", 1)
		frappe.clear_document_cache("CRM Invoicing Company", self.azienda.name)
		self.addCleanup(frappe.clear_document_cache, "CRM Invoicing Company", self.azienda.name)
		righe = [
			{
				"billable_service": self.consulenza.name,
				"service_provider": self.consulente.name,
				"qty": 1,
				"rate": 100,
			}
		]
		bozza = emissione.save(
			self.dati(recipient_type="soggetto_iva", billing_name="Rossi Srl", tax_id=PIVA, items=righe)
		)
		self.assertGreater(bozza["totals"]["withholding"], 0)
		# the same draft made out to a private person: they are not a withholding agent
		bozza = emissione.save(self.dati(items=righe), invoice=bozza["name"])
		self.assertEqual(bozza["totals"]["withholding"], 0)
		self.assertFalse(frappe.db.get_value("CRM Invoice", bozza["name"], "apply_withholding"))

	def test_i_messaggi_del_motore_si_traducono_col_loro_modello(self):
		messaggio = Messaggio("{0!r} is not a health profession", "Massaggiatore")
		self.assertEqual(messaggio, "'Massaggiatore' is not a health profession")
		self.assertEqual(documento.in_parole(messaggio), "'Massaggiatore' is not a health profession")
		self.assertEqual(documento.in_parole("plain words"), "plain words")


class UnaScartataSiCorregge(InvoicingBase):
	"""Refused by the SdI it counts as never issued: the dialog says why, offers to
	correct it instead of sending the same file again, and the draft keeps its number."""

	def _scartata(self):
		fattura = self.fattura(self.trattamento.name, self.osteopata.name)
		fattura.submit()
		fattura.reload()
		corpo = f"""<RicevutaScarto><NomeFile>{fattura.sdi_filename}</NomeFile>
			<ListaErrori><Errore><Codice>00423</Codice><Descrizione>x</Descrizione></Errore>
			</ListaErrori></RicevutaScarto>""".encode()
		ricezione.applica_file(corpo, fattura.sdi_filename.replace(".xml", "_NS_001.xml"))
		fattura.reload()
		return fattura

	def test_si_corregge_con_lo_stesso_numero_e_non_si_butta(self):
		fattura = self._scartata()
		vista = emissione.get_invoice(fattura.name)
		self.assertTrue(vista["rejection"])
		self.assertTrue(vista["can"]["reopen"])
		self.assertFalse(vista["can"]["transmit"])

		api.reopen_rejected(fattura.name)
		vista = emissione.get_invoice(fattura.name)
		self.assertEqual(vista["docstatus"], 0)
		self.assertEqual(vista["document_number"], fattura.document_number)
		# a hole in the numbering is not a way of correcting it
		self.assertFalse(vista["can"]["delete"])
		with self.assertRaises(frappe.ValidationError):
			emissione.delete_draft(fattura.name)

		emessa = emissione.issue({}, invoice=fattura.name)
		self.assertEqual(emessa["document_number"], fattura.document_number)
		self.assertTrue(emessa["can"]["transmit"])
