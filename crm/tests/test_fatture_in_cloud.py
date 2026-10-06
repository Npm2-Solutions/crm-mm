# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Invoicing with Fatture in Cloud, on a real site and a fake Fatture in Cloud.

A centre that invoices with Fatture in Cloud connects it once; from then on an
invoice issued here is born there: added up there first, numbered there, sent to
the SdI from there, its state asked there. The network is a fake one (`FiCFinto`):
what is checked is what Fatture in Cloud is asked and what is kept of its answers.
"""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import frappe
from frappe.utils import now_datetime

from crm.invoicing import api, incassi, prova
from crm.invoicing.fic import collegamento, emissione
from crm.invoicing.fic.client import ErroreFiC
from crm.tests.test_invoicing import PIVA, InvoicingBase

DOCTYPE = "CRM Fatture in Cloud"
AZIENDA = "CRM Invoicing Company"
AZIENDA_FIC = 4242

TIPI_IVA = [
	{"id": 0, "value": 22, "description": "Ordinaria", "ei_type": "", "default": True},
	{"id": 12, "value": 0, "description": "Esente art. 10", "ei_type": "N4"},
	{"id": 21, "value": 0, "description": "Escluso art. 15", "ei_type": "N1"},
]
CONTI = [
	{"id": 1, "name": "Cassa", "type": "standard"},
	{"id": 2, "name": "POS", "type": "standard"},
	{"id": 3, "name": "Banca Intesa", "type": "bank"},
]


def _arrotonda(valore) -> float:
	return float(Decimal(str(valore)).quantize(Decimal("0.01")))


class FiCFinto:
	"""Fatture in Cloud, as far as these tests are concerned: it keeps the documents
	it is given, numbers them, adds them up, says how they are doing."""

	def __init__(self):
		self.documenti: dict[int, dict] = {}
		self.prossimo_id = 900
		self.numeri: dict[tuple[str, str], int] = {}
		self.chiamate: list[tuple] = []
		self.ei_status: dict[int, str] = {}
		self.verifica_xml: list[str] = []
		self.perde_la_risposta = False
		self.sconto_sui_totali = 0
		self.tokens = 0

	# ---- the two doors the code uses

	def chiedi_token(self, dati):
		self.chiamate.append(("TOKEN", dati["grant_type"], None, None))
		self.tokens += 1
		return {"access_token": f"a/{self.tokens}", "refresh_token": f"r/{self.tokens}", "expires_in": 86400}

	def chiama(self, metodo, percorso, access_token, json=None, params=None, testo=False):
		self.chiamate.append((metodo, percorso, json, params))
		parti = percorso.strip("/").split("/")
		if percorso == "/user/companies":
			return {
				"data": {
					"companies": [
						{
							"id": AZIENDA_FIC,
							"name": "Studio Test",
							"type": "company",
							"vat_number": f"IT{PIVA}",
						}
					]
				}
			}
		if parti[-1] == "info":
			return {
				"data": {
					"vat_types_list": TIPI_IVA,
					"payment_accounts_list": CONTI,
					"numerations": {str(now_datetime().year): {"": 7, "/S": 2}},
					"extra_data_default_values": {"ts_communication": False},
				}
			}
		if parti[-1] == "totals":
			return {"data": self.totali(json["data"])}
		if percorso.endswith("/issued_documents") and metodo == "GET":
			cercato = params["q"].split("'")[1]
			return {"data": [d for d in self.documenti.values() if cercato in (d.get("subject") or "")]}
		if percorso.endswith("/issued_documents") and metodo == "POST":
			return {"data": self.crea(json["data"])}
		if "e_invoice" in parti:
			identificativo = int(parti[3])
			if parti[-1] == "xml_verify":
				if self.verifica_xml:
					raise ErroreFiC("Validation XML", stato=422, rilievi=self.verifica_xml)
				return {"data": {"success": True}}
			if parti[-1] == "send":
				self.ei_status[identificativo] = "attempt"
				return {"data": {"name": "CARICATO", "date": "2026-10-06 10:00:00"}}
			if parti[-1] == "xml":
				return f"<FatturaElettronica><Numero>{self.documenti[identificativo]['number']}</Numero></FatturaElettronica>"
			if parti[-1] == "error_reason":
				return {
					"data": {
						"reason": "Il Codice Fiscale del cliente risulta sbagliato.",
						"solution": "Correggilo.",
					}
				}
		if parti[-2] == "issued_documents":
			identificativo = int(parti[-1])
			if metodo == "GET":
				return {"data": {"id": identificativo, "ei_status": self.ei_status.get(identificativo)}}
			if metodo == "PUT":
				self.documenti[identificativo].update(json["data"])
				return {"data": self.documenti[identificativo]}
			if metodo == "DELETE":
				self.documenti.pop(identificativo, None)
				return {}
		raise AssertionError(f"unexpected call {metodo} {percorso}")

	# ---- what it does with a document

	def totali(self, dati):
		aliquote = {tipo["id"]: tipo["value"] for tipo in TIPI_IVA}
		netto = cassa = iva = base_ritenuta = 0.0
		for voce in dati["items_list"]:
			importo = voce["qty"] * voce["net_price"] * (1 - voce.get("discount", 0) / 100)
			quota_cassa = importo * dati.get("cassa", 0) / 100 if voce.get("apply_withholding_taxes") else 0
			netto += importo
			cassa += quota_cassa
			iva += round((importo + quota_cassa) * aliquote[voce["vat"]["id"]] / 100, 2)
			if voce.get("apply_withholding_taxes"):
				base_ritenuta += importo
		cassa = _arrotonda(cassa)
		ritenuta = _arrotonda(base_ritenuta * dati.get("withholding_tax", 0) / 100)
		lordo = _arrotonda(netto + cassa + iva)
		bollo = 0 if dati["e_invoice"] else dati.get("stamp_duty", 0)
		return {
			"amount_net": _arrotonda(netto),
			"amount_cassa": cassa,
			"amount_vat": _arrotonda(iva),
			"amount_gross": lordo,
			"amount_withholding_tax": ritenuta,
			"stamp_duty": dati.get("stamp_duty", 0),
			"amount_due": _arrotonda(lordo + bollo - ritenuta - self.sconto_sui_totali),
		}

	def crea(self, dati):
		chiave = (dati["type"], dati.get("numeration") or "")
		self.numeri[chiave] = self.numeri.get(chiave, 0) + 1
		self.prossimo_id += 1
		documento = {
			**dati,
			"id": self.prossimo_id,
			"number": self.numeri[chiave],
			"numeration": dati.get("numeration") or "",
		}
		self.documenti[self.prossimo_id] = documento
		if self.perde_la_risposta:
			self.perde_la_risposta = False
			raise ErroreFiC("Fatture in Cloud did not answer in time.", incerto=True)
		return documento

	def fatte(self, metodo, fine):
		return [c for c in self.chiamate if c[0] == metodo and c[1].endswith(fine)]


class Base(InvoicingBase):
	def setUp(self):
		super().setUp()
		self.fic = FiCFinto()
		for bersaglio, sostituto in (
			("crm.invoicing.fic.collegamento.chiama", self.fic.chiama),
			("crm.invoicing.fic.collegamento.chiedi_token", self.fic.chiedi_token),
			("crm.invoicing.fic.emissione.chiama", self.fic.chiama),
		):
			patcher = patch(bersaglio, sostituto)
			patcher.start()
			self.addCleanup(patcher.stop)
		conf = patch.dict(
			frappe.conf, {"fic_client_id": "app-agenzia", "fic_client_secret": "segreto-agenzia"}
		)
		conf.start()
		self.addCleanup(conf.stop)
		self.addCleanup(frappe.clear_document_cache, AZIENDA, self.azienda.name)

	def collega(self, attiva=True, **altro):
		"""The connection as the sign-in leaves it, the company chosen and read."""
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE,
				"company": self.azienda.name,
				"access_token": "a/0",
				"refresh_token": "r/0",
				"access_expires_on": now_datetime() + timedelta(hours=20),
				"refreshed_on": now_datetime(),
				"fic_company_id": AZIENDA_FIC,
				"fic_company_name": "Studio Test",
				"fic_vat_number": f"IT{PIVA}",
				**altro,
			}
		).insert(ignore_permissions=True)
		collegamento.leggi_info(doc.name)
		doc.reload()
		doc.vat_map = json.dumps({"0|N4": 12})
		doc.active = 1 if attiva else 0
		doc.save(ignore_permissions=True)
		# what the connecting asked is not what the test is about
		self.fic.chiamate.clear()
		return doc

	def emessa(self, servizio=None, erogatore=None, pagata=False, **altro):
		documento = self.fattura(servizio or self.seduta.name, erogatore or self.psicologo.name, **altro)
		documento.flags.pagata_alla_cassa = pagata
		documento.submit()
		documento.reload()
		return documento

	def mandato(self):
		[chiamata] = self.fic.fatte("POST", "/issued_documents")
		return chiamata[2]["data"]


class CollegamentoTest(Base):
	def test_dal_pulsante_al_ritorno_la_connessione_c_e(self):
		indirizzo = collegamento.connect(self.azienda.name)["url"]
		parametri = parse_qs(urlparse(indirizzo).query)
		self.assertEqual(parametri["client_id"], ["app-agenzia"])
		self.assertEqual(parametri["scope"], [" ".join(collegamento.SCOPES)])
		# nothing of the centre travels through Fatture in Cloud
		self.assertNotIn(self.azienda.name, parametri["state"][0])

		collegamento.callback(code="c/123", state=parametri["state"][0])

		self.assertEqual(frappe.local.response["location"], "/oauth_connected?provider=fic")
		doc = frappe.get_doc(DOCTYPE, self.azienda.name)
		self.assertEqual(doc.get_password("access_token"), "a/1")
		self.assertEqual(doc.fic_company_id, AZIENDA_FIC)
		self.assertEqual(doc.connected_by, frappe.session.user)
		pagina = collegamento.get_fic(self.azienda.name)
		self.assertTrue(pagina["connected"])
		self.assertEqual(pagina["fic_company"]["name"], "Studio Test")
		esente = next(riga for riga in pagina["vat"] if riga["key"] == "0|N4")
		# the only exemption of its nature: matched by itself
		self.assertEqual(esente["value"], 12)
		self.assertEqual(pagina["missing"], [])
		# the till for cash, the POS for the card, the bank for a transfer
		conti = {riga["method"]: riga["value"] for riga in pagina["accounts"]}
		self.assertEqual((conti["MP01"], conti["MP08"], conti["MP05"]), (1, 2, 3))

	def test_uno_stato_che_non_viene_da_qui_non_collega(self):
		collegamento.callback(code="c/123", state="falso.firma")
		self.assertIn("error=", frappe.local.response["location"])
		self.assertFalse(frappe.db.exists(DOCTYPE, self.azienda.name))

	def test_un_altra_partita_iva_non_si_attiva(self):
		self.collega(attiva=False, fic_vat_number="IT09876543210")
		with self.assertRaises(frappe.ValidationError) as preso:
			collegamento.save_fic(self.azienda.name, {"active": True})
		self.assertIn("09876543210", str(preso.exception))

	def test_l_accesso_scaduto_si_rinnova_da_solo(self):
		self.collega()
		frappe.db.set_value(
			DOCTYPE, self.azienda.name, "access_expires_on", now_datetime() - timedelta(minutes=1)
		)
		self.assertEqual(collegamento.token(self.azienda.name), "a/1")
		self.assertEqual(self.fic.chiamate, [("TOKEN", "refresh_token", None, None)])
		self.assertEqual(frappe.get_doc(DOCTYPE, self.azienda.name).get_password("refresh_token"), "r/1")
		# good for the next minutes: not asked again
		self.assertEqual(collegamento.token(self.azienda.name), "a/1")
		self.assertEqual(len(self.fic.chiamate), 1)


class EmissioneTest(Base):
	def test_una_fattura_al_paziente_nasce_in_fatture_in_cloud(self):
		self.collega()
		documento = self.emessa(pagata=True)
		dati = self.mandato()
		self.assertEqual(documento.document_number, "1")
		self.assertEqual(documento.fic_document_id, str(self.fic.prossimo_id))
		self.assertEqual(documento.series, "")
		self.assertFalse(dati["e_invoice"])
		self.assertEqual(dati["items_list"][0]["vat"], {"id": 12})
		# the ENPAP fund, as the issuing company has it
		self.assertEqual((dati["cassa"], dati["ei_cassa_type"]), (2.0, "TC21"))
		self.assertEqual(dati["payments_list"][0]["status"], "paid")
		self.assertEqual(dati["payments_list"][0]["payment_account"], {"id": 2})
		self.assertIn(documento.name, dati["subject"])
		# added up there before it was made
		self.assertEqual(len(self.fic.fatte("POST", "/totals")), 1)
		# the Sistema TS is still reported from here
		self.assertEqual(documento.ts_status, "da_inviare")
		self.assertEqual(dati["extra_data"], {"ts_communication": False})

	def test_i_totali_diversi_non_fanno_niente(self):
		self.collega()
		self.fic.sconto_sui_totali = 1
		with self.assertRaises(frappe.ValidationError) as preso:
			self.emessa()
		self.assertIn("amount to pay", str(preso.exception))
		self.assertEqual(self.fic.fatte("POST", "/issued_documents"), [])

	def test_un_aliquota_senza_corrispondenza_ferma_prima(self):
		self.collega()
		frappe.db.set_value(DOCTYPE, self.azienda.name, "vat_map", "{}")
		frappe.db.set_value(DOCTYPE, self.azienda.name, "info", json.dumps({"vat_types": TIPI_IVA[:1]}))
		with self.assertRaises(frappe.ValidationError) as preso:
			self.emessa()
		self.assertIn("Fatture in Cloud", str(preso.exception))
		self.assertEqual(self.fic.chiamate, [])

	def test_in_prova_non_va_a_fatture_in_cloud(self):
		self.collega()
		frappe.db.set_value(AZIENDA, self.azienda.name, "provider_environment", "sandbox")
		frappe.clear_document_cache(AZIENDA, self.azienda.name)
		documento = self.emessa()
		self.assertEqual(documento.test_document, 1)
		self.assertFalse(documento.fic_document_id)
		self.assertEqual(self.fic.chiamate, [])

	def test_spento_numera_qui(self):
		self.collega(attiva=False)
		documento = self.emessa()
		self.assertIn("/S/", documento.document_number)
		self.assertEqual(self.fic.chiamate, [])

	def test_una_risposta_persa_si_ritrova_invece_di_rifarla(self):
		self.collega()
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		self.fic.perde_la_risposta = True
		with self.assertRaises(frappe.ValidationError) as preso:
			documento.submit()
		self.assertIn("looks for it there", str(preso.exception))
		self.assertEqual(len(self.fic.documenti), 1)
		documento.reload()
		documento.submit()
		# found by its mark and brought up to date: one invoice there, number 1
		self.assertEqual(len(self.fic.documenti), 1)
		self.assertEqual(len(self.fic.fatte("PUT", f"/issued_documents/{self.fic.prossimo_id}")), 1)
		self.assertEqual(documento.document_number, "1")

	def test_annullata_la_transazione_se_ne_va_anche_da_li(self):
		self.collega()
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		with patch("crm.invoicing.anagrafica.completa_da_fattura", side_effect=RuntimeError("dopo")):
			with self.assertRaises(RuntimeError):
				documento.submit()
		self.assertEqual(len(self.fic.documenti), 1)
		frappe.db.rollback()
		self.assertEqual(self.fic.documenti, {})
		self.assertEqual(
			self.fic.fatte("DELETE", f"/issued_documents/{self.fic.prossimo_id}")[0][1].split("/")[2],
			str(AZIENDA_FIC),
		)

	def test_un_accesso_rinnovato_non_fa_dimenticare_la_fattura_da_togliere(self):
		# the access renewed while issuing is kept after the rollback with a commit,
		# and a commit forgets what still waits for the rollback
		self.collega()
		frappe.db.set_value(
			DOCTYPE, self.azienda.name, "access_expires_on", now_datetime() - timedelta(minutes=1)
		)
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		with patch("crm.invoicing.anagrafica.completa_da_fattura", side_effect=RuntimeError("dopo")):
			with self.assertRaises(RuntimeError):
				documento.submit()
		self.assertEqual(len(self.fic.documenti), 1)
		salvati = []

		def commit_finto(**_):
			frappe.db.after_rollback.reset()

		with (
			patch.dict(frappe.local.flags, {"in_test": False}),
			patch.object(frappe.local.db, "commit", commit_finto),
			patch(
				"crm.invoicing.fic.collegamento._salva_token",
				lambda company, risposta: salvati.append(risposta["refresh_token"]),
			),
		):
			frappe.db.rollback()
		self.assertEqual(self.fic.documenti, {})
		self.assertEqual(salvati, ["r/1"])

	def test_il_sistema_ts_da_fatture_in_cloud(self):
		self.collega(ts_by="fatture_in_cloud")
		documento = self.emessa()
		self.assertEqual(documento.ts_status, "fatture_in_cloud")
		extra = self.mandato()["extra_data"]
		self.assertTrue(extra["ts_communication"])
		self.assertEqual(extra["ts_tipo_spesa"], "SP")
		self.assertTrue(extra["ts_pagamento_tracciato"])


class DopoTest(Base):
	def elettronica(self):
		self.collega()
		frappe.db.set_value(DOCTYPE, self.azienda.name, "vat_map", json.dumps({"0|N4": 12, "22": 0}))
		documento = self.emessa(self.trattamento.name, self.osteopata.name)
		self.assertEqual(documento.channel, "sdi")
		return documento

	def test_parte_per_lo_sdi_da_fatture_in_cloud(self):
		documento = self.elettronica()
		# its e-invoice is Fatture in Cloud's: none written here
		self.assertFalse(documento.xml_file)
		esito = api.trasmetti(documento)
		self.assertEqual(esito["mode"], "fatture_in_cloud")
		documento.reload()
		self.assertEqual(documento.sdi_status, "inviato")
		self.assertTrue(documento.sdi_sent_file)

	def test_quello_che_fatture_in_cloud_trova_si_dice_prima(self):
		documento = self.elettronica()
		self.fic.verifica_xml = ["Il CAP del cliente non è valido"]
		with self.assertRaises(frappe.ValidationError) as preso:
			api.trasmetti(documento)
		self.assertIn("Il CAP del cliente non è valido", str(preso.exception))
		self.assertEqual(self.fic.fatte("POST", "/send"), [])

	def test_gli_stati_si_chiedono_a_fatture_in_cloud(self):
		documento = self.elettronica()
		api.trasmetti(documento)
		identificativo = int(documento.fic_document_id)
		self.fic.ei_status[identificativo] = "sent"
		emissione.riconcilia()
		self.assertEqual(frappe.db.get_value("CRM Invoice", documento.name, "sdi_status"), "consegnata")

	def test_scartata_dice_perche(self):
		documento = self.elettronica()
		api.trasmetti(documento)
		self.fic.ei_status[int(documento.fic_document_id)] = "discarded"
		with patch("crm.invoicing.monitoraggio.avvisa") as avvisa:
			emissione.riconcilia()
		riga = frappe.db.get_value("CRM Invoice", documento.name, ["sdi_status", "sdi_message"], as_dict=True)
		self.assertEqual(riga.sdi_status, "scartata")
		self.assertIn("Codice Fiscale", riga.sdi_message)
		avvisa.assert_called_once()

	def test_un_incasso_segnato_qui_si_segna_li(self):
		self.collega()
		documento = self.emessa()
		incassi.set_collected(documento.name, str(documento.posting_date))
		[chiamata] = self.fic.fatte("PUT", f"/issued_documents/{documento.fic_document_id}")
		[pagamento] = chiamata[2]["data"]["payments_list"]
		self.assertEqual((pagamento["status"], pagamento["payment_account"]), ("paid", {"id": 2}))

	def test_annullata_qui_se_ne_va_da_li(self):
		self.collega()
		documento = self.emessa()
		documento.cancel()
		self.assertEqual(self.fic.documenti, {})

	def test_annullata_senza_accesso_lo_dice(self):
		self.collega()
		documento = self.emessa()
		frappe.db.set_value(DOCTYPE, self.azienda.name, "needs_reconnect", 1)
		documento.cancel()
		# cancelled here all the same, and the invoice says it is still there
		self.assertEqual(len(self.fic.documenti), 1)
		self.assertTrue(
			frappe.db.exists(
				"Comment",
				{
					"reference_doctype": "CRM Invoice",
					"reference_name": documento.name,
					"content": ["like", "%stays there%"],
				},
			)
		)


class MancanzeTest(Base):
	def test_l_accesso_perso_ferma_il_passaggio_al_reale(self):
		self.collega()
		frappe.db.set_value(DOCTYPE, self.azienda.name, "needs_reconnect", 1)
		righe = prova.mancanze(frappe.get_doc(AZIENDA, self.azienda.name).as_dict(), agenzia=False)
		riga = next(riga for riga in righe if riga["title"] == "Fatture in Cloud")
		self.assertTrue(riga["blocking"])
		self.assertEqual(riga["page"], "Fatture in Cloud")
		# nothing of Itala's is asked of a centre that does not use it
		self.assertFalse(any(riga["title"] == "Itala" for riga in righe))
