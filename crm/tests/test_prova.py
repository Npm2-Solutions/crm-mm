# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Invoicing in test, then live, through Itala - on a real site.

A company starts in test: its invoices are numbered PROVA, the electronic ones go
to Itala's test environment, the Sistema TS receives nothing, a test invoice makes
nobody a client and never reaches the patient's area. Going live takes the test
invoices away and numbers the real ones from where the real series stands. Itala
is reached on the agency's account, each company registered under it once per
environment, and the network is a fake one: what is checked is what we ask Itala
and what we keep of its answers.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import frappe

from crm.invoicing import api, connessione, emissione, prova
from crm.invoicing.sdi import itala, riconciliazione
from crm.tests.test_invoicing import PIVA, InvoicingBase

AZIENDA = "CRM Invoicing Company"
AGENZIA = ("id-agenzia", "segreto-agenzia")


class Risposta:
	def __init__(self, stato=200, corpo=None, testate=None):
		self.status_code = stato
		self.headers = testate or {}
		self.content = json.dumps(corpo).encode() if corpo is not None else b""
		self.text = self.content.decode()

	def json(self):
		return json.loads(self.content)


class Sessione:
	"""Itala, as far as these tests are concerned: it answers what it is told to."""

	def __init__(self, risponde):
		self.risponde = risponde
		self.chiamate = []

	def request(self, metodo, url, **argomenti):
		self.chiamate.append({"metodo": metodo, "url": url, **argomenti})
		return self.risponde(metodo, url, argomenti)


class Base(InvoicingBase):
	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.clear_document_cache, AZIENDA, self.azienda.name)
		frappe.cache().delete_value(f"provider:token:agenzia:{connessione.SANDBOX}")
		frappe.cache().delete_value(f"provider:token:agenzia:{connessione.PRODUZIONE}")

	def imposta(self, **valori):
		frappe.db.set_value(AZIENDA, self.azienda.name, valori)
		frappe.clear_document_cache(AZIENDA, self.azienda.name)

	def emittente(self):
		return frappe.get_doc(AZIENDA, self.azienda.name).as_dict()

	def emessa(self, servizio=None, erogatore=None, **altro):
		documento = self.fattura(servizio or self.seduta.name, erogatore or self.psicologo.name, **altro)
		documento.submit()
		documento.reload()
		return documento


class InProvaTest(Base):
	def setUp(self):
		super().setUp()
		self.imposta(provider_environment=connessione.SANDBOX, sdi_mode="export")

	def test_la_fattura_e_di_prova_e_ha_la_sua_serie(self):
		documento = self.emessa()
		self.assertEqual(documento.test_document, 1)
		self.assertIn("PROVA-S", documento.document_number)
		self.assertEqual(documento.series, "PROVA-S")
		# checked when it was issued, never sent
		self.assertEqual(documento.ts_status, "prova")

	def test_il_sistema_ts_non_la_riceve(self):
		from crm.tessera_sanitaria import trasporto

		documento = self.emessa()
		with self.assertRaises(frappe.ValidationError) as errore:
			trasporto.invia_documento(documento.name)
		self.assertIn("test invoice", str(errore.exception))

	def test_la_finestra_dice_che_e_di_prova(self):
		documento = self.emessa()
		vista = emissione.get_invoice(documento.name)
		self.assertTrue(vista["test"])
		self.assertEqual(vista["states"]["ts"], "Test: checked, not sent")
		# a draft says it will be one
		self.assertTrue(emissione.preview({"items": []})["test"])

	def test_non_fa_un_cliente_e_non_va_nell_area(self):
		from crm.area import api as area
		from crm.clienti import eventi

		documento = self.emessa()
		documento.db_set({"party_type": "CRM Lead", "party": "PERSONA-DI-PROVA"})
		with (
			patch("crm.clienti.cliente.regole_del_crm", return_value=True),
			patch("crm.clienti.cliente.diventa_cliente") as diventa,
		):
			eventi.fattura_confermata(documento)
		diventa.assert_not_called()
		self.assertEqual(area._fatture("PERSONA-DI-PROVA"), [])

	def test_dal_vivo_una_prova_non_parte_e_non_si_corregge(self):
		documento = self.emessa(self.trattamento.name, self.osteopata.name)
		self.assertEqual(documento.channel, "sdi")
		self.imposta(provider_environment=connessione.PRODUZIONE)
		with self.assertRaises(frappe.ValidationError):
			api.send_to_sdi(documento.name)
		with self.assertRaises(frappe.ValidationError):
			emissione.credit_note(documento.name)
		self.assertFalse(emissione.get_invoice(documento.name)["can"]["transmit"])


class AttivazioneTest(Base):
	def setUp(self):
		super().setUp()
		self.imposta(provider_environment=connessione.SANDBOX, sdi_mode="export")

	def test_attivare_toglie_le_prove_e_numera_dal_vero(self):
		prima = self.emessa()
		seconda = self.emessa()
		esito = prova.go_live(self.azienda.name)

		self.assertEqual(esito["removed"], 2)
		self.assertFalse(frappe.db.exists("CRM Invoice", prima.name))
		self.assertFalse(frappe.db.exists("CRM Invoice", seconda.name))
		self.assertFalse(frappe.db.exists("CRM Invoice Log", {"invoice": prima.name}))
		self.assertFalse(
			frappe.db.exists("CRM Invoice Series", {"company": self.azienda.name, "series": "PROVA-S"})
		)
		emittente = self.emittente()
		self.assertEqual(emittente.provider_environment, connessione.PRODUZIONE)
		self.assertTrue(emittente.live_since)

		vera = self.emessa()
		self.assertEqual(vera.test_document, 0)
		self.assertEqual(vera.series, "S")
		self.assertNotIn("PROVA", vera.document_number)
		self.assertEqual(vera.ts_status, "da_inviare")

	def test_senza_partita_iva_non_si_attiva(self):
		self.imposta(tax_id="")
		with self.assertRaises(frappe.ValidationError) as errore:
			prova.go_live(self.azienda.name)
		self.assertIn("VAT number", str(errore.exception))

	def test_quello_che_manca_dice_chi_lo_fa(self):
		self.imposta(tax_id="", conservation_service="")
		righe = {riga["title"]: riga for riga in prova.mancanze(self.emittente(), agenzia=True)}
		self.assertTrue(righe["VAT number"]["blocking"])
		self.assertTrue(righe["Preservation of the SdI documents"]["agency"])
		# the centre does not see what it cannot do
		del_centro = {riga["title"] for riga in prova.mancanze(self.emittente(), agenzia=False)}
		self.assertIn("VAT number", del_centro)
		self.assertNotIn("Preservation of the SdI documents", del_centro)

	def test_in_prova_si_torna_solo_senza_fatture_vere(self):
		self.imposta(provider_environment=connessione.PRODUZIONE)
		self.emessa()
		with self.assertRaises(frappe.ValidationError):
			prova.back_to_test(self.azienda.name)


class ItalaTest(Base):
	def setUp(self):
		super().setUp()
		self.imposta(
			provider_environment=connessione.SANDBOX,
			sdi_mode="provider",
			sdi_flow="uscita",
			itala_id_test="",
			itala_id="",
			sdi_username="",
		)
		agenzia = patch("crm.invoicing.connessione.account_agenzia", return_value=AGENZIA)
		agenzia.start()
		self.addCleanup(agenzia.stop)

	def con(self, risponde):
		sessione = Sessione(risponde)
		rete = patch("frappe.utils.get_request_session", return_value=sessione)
		rete.start()
		self.addCleanup(rete.stop)
		return sessione

	def test_l_account_dell_agenzia_per_ambiente(self):
		emittente = self.emittente()
		self.assertEqual(connessione.accesso(emittente).base, connessione.BASE[connessione.SANDBOX])
		self.assertFalse(connessione.accesso(emittente).proprio)
		in_produzione = connessione.accesso(emittente, connessione.PRODUZIONE)
		self.assertEqual(in_produzione.base, "https://fattura-elettronica-api.it/ws2.0/prod")

	def test_senza_account_lo_dice(self):
		with patch("crm.invoicing.connessione.account_agenzia", return_value=None):
			with self.assertRaises(connessione.ErroreProvider) as errore:
				connessione.accesso(self.emittente())
		self.assertIn("Itala is not connected yet", str(errore.exception))

	def test_si_registra_una_volta_per_ambiente(self):
		sessione = self.con(lambda metodo, url, argomenti: Risposta(200, {"id": "77"}))
		self.assertEqual(itala.registra_azienda(self.emittente()), "77")
		self.assertEqual(itala.registra_azienda(self.emittente()), "77")
		posts = [c for c in sessione.chiamate if c["metodo"] == "POST"]
		self.assertEqual(len(posts), 1)
		self.assertTrue(posts[0]["url"].endswith("/ws2.0/test/aziende"))
		self.assertEqual(posts[0]["json"]["piva"], PIVA)
		self.assertEqual(self.emittente().itala_id_test, "77")
		# production is another registration
		itala.registra_azienda(self.emittente(), connessione.PRODUZIONE)
		self.assertEqual(len([c for c in sessione.chiamate if c["metodo"] == "POST"]), 2)

	def test_registrata_prima_si_ritrova_dalla_partita_iva(self):
		def risponde(metodo, url, argomenti):
			if metodo == "POST":
				return Risposta(400, {"error": "azienda gia presente"})
			return Risposta(200, [{"id": "12", "piva": PIVA}] if argomenti["params"]["page"] == 1 else [])

		self.con(risponde)
		self.assertEqual(itala.registra_azienda(self.emittente()), "12")

	def test_la_prova_parte_per_l_ambiente_di_prova_e_si_tiene_il_nome_di_itala(self):
		def risponde(metodo, url, argomenti):
			if url.endswith("/aziende"):
				return Risposta(200, {"id": "5"})
			return Risposta(
				200,
				{
					"id": 991,
					"sdi_identificativo": None,
					"sdi_nome_file": "IT0123_abc12.xml",
					"sdi_stato": "PREN",
				},
			)

		sessione = self.con(risponde)
		documento = self.emessa(self.trattamento.name, self.osteopata.name)
		esito = api.send_to_sdi(documento.name)

		invio = sessione.chiamate[-1]
		self.assertEqual(invio["url"], "https://fattura-elettronica-api.it/ws2.0/test/fatture")
		self.assertEqual(invio["headers"]["Content-Type"], "application/xml")
		self.assertTrue(esito["sent"])
		documento.reload()
		self.assertEqual(documento.sdi_status, "inviato")
		# the notices answer to Itala's file name, and its updates carry its id
		self.assertEqual(documento.sdi_filename, "IT0123_abc12.xml")
		self.assertEqual(documento.sdi_provider_id, "991")
		self.assertEqual(documento.sdi_environment, connessione.SANDBOX)
		self.assertIn("[TEST", documento.sdi_message)

	def test_il_token_si_raccoglie_e_si_riusa(self):
		scade = (datetime.now() + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
		sessione = self.con(
			lambda metodo, url, argomenti: Risposta(
				200, [], {"X-auth-token": "tok-1", "X-auth-expires": scade}
			)
		)
		itala.aggiornamenti(self.emittente())
		itala.aggiornamenti(self.emittente())
		prima, seconda = sessione.chiamate
		self.assertTrue(prima["headers"]["Authorization"].startswith("Basic "))
		self.assertEqual(seconda["headers"]["Authorization"], "Bearer tok-1")

	def test_chi_emette_soltanto_chiede_le_sue_trasmissioni(self):
		sessione = self.con(lambda metodo, url, argomenti: Risposta(200, [{"ricezione": 1, "id": 4}]))
		esito = riconciliazione.riconcilia(self.emittente())
		parametri = sessione.chiamate[-1]["params"]
		self.assertEqual(parametri["partita_iva"], PIVA)
		self.assertEqual(parametri["unread"], "true")
		self.assertEqual(parametri["solo_trasmissioni"], "true")
		# a supplier's invoice is not filed for a company that does not receive them
		self.assertEqual(esito["incoming"], 0)
		self.assertEqual(esito["skipped"], 1)

		self.imposta(sdi_flow="entrambi")
		riconciliazione.riconcilia(self.emittente())
		self.assertNotIn("solo_trasmissioni", sessione.chiamate[-1]["params"])

	def test_si_chiede_solo_quando_qualcosa_aspetta(self):
		self.assertFalse(riconciliazione.da_chiedere({"name": "Nessuna fattura", "sdi_flow": "uscita"}))
		# who receives its suppliers' invoices always has something to ask
		self.assertTrue(riconciliazione.da_chiedere({"name": "Nessuna fattura", "sdi_flow": "entrambi"}))
		documento = self.emessa(self.trattamento.name, self.osteopata.name)
		documento.db_set("sdi_status", "inviato")
		self.assertTrue(riconciliazione.da_chiedere(self.emittente()))


class CampiDellAgenziaTest(Base):
	def test_il_centro_non_vede_i_campi_dell_agenzia(self):
		from crm.api.doc import get_fields

		utente = "fatture.centro@example.com"
		if not frappe.db.exists("User", utente):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": utente,
					"first_name": "Centro",
					"send_welcome_email": 0,
					"roles": [{"role": "Invoicing Manager"}],
				}
			).insert(ignore_permissions=True)
		campi = {campo.fieldname for campo in get_fields(AZIENDA, True)}
		self.assertIn("sdi_mode", campi)
		frappe.set_user(utente)
		self.addCleanup(frappe.set_user, "Administrator")
		campi = {campo.fieldname for campo in get_fields(AZIENDA, True)}
		self.assertNotIn("sdi_mode", campi)
		self.assertNotIn("provider_environment", campi)
		self.assertNotIn("number_format", campi)
		self.assertIn("ts_username", campi)
		self.assertIn("tax_id", campi)
