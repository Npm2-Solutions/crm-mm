# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Itala as its guides describe it (02/10/2026), on a real site with a fake network.

What the audit against the guides found, each in a test: the XML leaves as it is
(Itala signs what goes to a public body); the SdI's identifier is Itala's
`sdi_identificativo`, not its id; each notice is applied once by its own name, so
an invoice to a public body gets both of its notices; Itala's states become the
invoice's own; an update is kept before it is applied and tried again if it fails;
a row of another VAT number is not the company's; a copy of the site reads
nothing; a send whose answer was lost is not sent twice; Itala's Bearer reaches
the webhook; a centre that leaves is taken away from the agency's account.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.utils import add_to_date, now_datetime
from frappe.utils.password import set_encrypted_password

from crm.invoicing import api, connessione, prova
from crm.invoicing.sdi import itala, riconciliazione, webhook
from crm.tests import test_prova as P
from crm.tests.test_invoicing import PIVA

AZIENDA = P.AZIENDA
Risposta = P.Risposta

AGGIORNAMENTO = "CRM SdI Update"

CONSEGNA = b"""<?xml version="1.0" encoding="UTF-8"?>
<ns3:RicevutaConsegna xmlns:ns3="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/RicevutaConsegna_v1.0">
	<IdentificativoSdI>4400112233</IdentificativoSdI>
	<NomeFile>IT0123_abc12.xml</NomeFile>
	<DataOraRicezione>2026-10-02T09:12:33.000+01:00</DataOraRicezione>
	<DataOraConsegna>2026-10-02T09:15:00.000+01:00</DataOraConsegna>
</ns3:RicevutaConsegna>"""

ESITO_ACCETTATA = b"""<?xml version="1.0"?>
<ns:NotificaEsito xmlns:ns="http://x">
	<IdentificativoSdI>4400112233</IdentificativoSdI>
	<NomeFile>IT0123_abc12.xml</NomeFile>
	<EsitoCommittente><Esito>EC01</Esito></EsitoCommittente>
</ns:NotificaEsito>"""


class Grezza:
	"""An answer that is not JSON: a notice, with its headers."""

	def __init__(self, contenuto: bytes, testate=None, stato=200):
		self.status_code = stato
		self.headers = testate or {}
		self.content = contenuto
		self.text = contenuto.decode()

	def json(self):
		raise ValueError


class ConItala(P.Base):
	"""A company on the agency's account at Itala, the network a fake one. The
	module's attribute, not imported by name: the tests of test_prova stay there."""

	def setUp(self):
		super().setUp()
		self.imposta(
			provider_environment=connessione.SANDBOX,
			sdi_mode="provider",
			sdi_flow="entrambi",
			itala_id_test="5",
			itala_id="",
			itala_site="",
			sdi_username="",
		)
		agenzia = patch("crm.invoicing.connessione.account_agenzia", return_value=P.AGENZIA)
		agenzia.start()
		self.addCleanup(agenzia.stop)

	def con(self, risponde):
		sessione = P.Sessione(risponde)
		rete = patch("frappe.utils.get_request_session", return_value=sessione)
		rete.start()
		self.addCleanup(rete.stop)
		return sessione


class FlussoItala(ConItala):
	def inviata(self, **valori):
		"""An invoice that left through Itala, as the send leaves it."""
		documento = self.emessa(self.trattamento.name, self.osteopata.name)
		documento.db_set(
			{
				"sdi_status": "inviato",
				"sdi_provider_id": "991",
				"sdi_filename": "IT0123_abc12.xml",
				"sdi_sent_on": now_datetime(),
				**valori,
			}
		)
		return documento

	# ------------------------------------------------------------- sending

	def test_l_xml_parte_com_e_e_l_identificativo_e_quello_dello_sdi(self):
		trasmesso = "<FatturaElettronica><DatiTrasmissione>di Itala</DatiTrasmissione></FatturaElettronica>"

		def risponde(metodo, url, argomenti):
			return Risposta(
				200,
				{
					"id": 991,
					"sdi_identificativo": None,
					"sdi_nome_file": "IT0123_abc12.xml",
					"sdi_stato": "PREN",
					"sdi_fattura": trasmesso,
				},
			)

		sessione = self.con(risponde)
		documento = self.emessa(self.trattamento.name, self.osteopata.name)
		firmato = frappe.get_doc(
			{"doctype": "File", "file_name": "firmato.p7m", "is_private": 1, "content": b"P7M"}
		).insert(ignore_permissions=True)
		documento.db_set("sdi_signed_file", firmato.file_url)

		api.send_to_sdi(documento.name)

		inviato = sessione.chiamate[-1]
		self.assertNotEqual(inviato["data"], b"P7M")
		self.assertTrue(inviato["data"].lstrip().startswith(b"<"))
		documento.reload()
		# PREN: the SdI has not taken it yet, and Itala's id is not the SdI's
		self.assertFalse(documento.sdi_identifier)
		self.assertEqual(documento.sdi_provider_id, "991")
		self.assertTrue(documento.sdi_sent_file)
		contenuto = frappe.get_doc("File", {"file_url": documento.sdi_sent_file}).get_content()
		self.assertIn("di Itala", contenuto if isinstance(contenuto, str) else contenuto.decode())

	def test_un_invio_senza_risposta_non_si_rifa_due_volte(self):
		import requests

		documento = self.emessa(self.trattamento.name, self.osteopata.name)

		def scaduto(metodo, url, argomenti):
			if url.endswith("/aziende"):
				return Risposta(200, {"id": "5"})
			raise requests.exceptions.ReadTimeout("read timed out")

		self.con(scaduto)
		with self.assertRaises(frappe.ValidationError):
			api.send_to_sdi(documento.name)
		self.assertTrue(
			frappe.db.exists(
				"CRM Invoice Log", {"invoice": documento.name, "event": "sdi_sent", "status": "incerto"}
			)
		)

		def ce_l_ha(metodo, url, argomenti):
			if metodo == "GET" and url.endswith("/fatture"):
				# every value as text, as Itala's API answers (not its guide): "0"
				# is true in Python, and the invoice went out twice (05/10/2026)
				return Risposta(
					200,
					[
						{
							"id": "777",
							"ricezione": "0",
							"numero_documento": documento.document_number,
							"sdi_identificativo": "4400112233",
							"sdi_nome_file": "IT0123_xyz.xml",
							"sdi_stato": "INVI",
						}
					],
				)
			return Risposta(500, {"error": "non doveva inviare"})

		sessione = self.con(ce_l_ha)
		api.send_to_sdi(documento.name)
		self.assertFalse([c for c in sessione.chiamate if c["metodo"] == "POST"])
		ricerca = sessione.chiamate[-1]["params"]
		self.assertEqual(ricerca["numero_documento"], documento.document_number)
		self.assertEqual(ricerca["partita_iva"], PIVA)
		documento.reload()
		self.assertEqual(documento.sdi_status, "inviato")
		self.assertEqual(documento.sdi_provider_id, "777")
		self.assertEqual(documento.sdi_identifier, "4400112233")

	# ------------------------------------------------------------- updates

	def test_ogni_notifica_si_applica_una_volta_per_il_suo_nome(self):
		documento = self.inviata(recipient_type="pubblica_amministrazione")
		notifiche = {
			"CONS": (CONSEGNA, "IT0123_abc12_RC_001.xml"),
			"ACCE": (ESITO_ACCETTATA, "IT0123_abc12_NE_001.xml"),
		}
		stato = {"attuale": "CONS"}

		def risponde(metodo, url, argomenti):
			if url.endswith("/notifica"):
				contenuto, nome = notifiche[stato["attuale"]]
				return Grezza(contenuto, {"Content-Disposition": f'attachment; filename="{nome}"'})
			return Risposta(200, [])

		sessione = self.con(risponde)
		riconciliazione.riconcilia(
			self.emittente(),
			[{"id": 991, "ricezione": 0, "sdi_stato": "CONS", "sdi_identificativo": 4400112233}],
		)
		documento.reload()
		self.assertEqual(documento.sdi_status, "consegnata")
		self.assertEqual(documento.sdi_identifier, "4400112233")
		self.assertEqual(
			next(c for c in sessione.chiamate if c["url"].endswith("/notifica"))["headers"]["Accept"],
			"application/xml",
		)

		stato["attuale"] = "ACCE"
		esito = riconciliazione.riconcilia(
			self.emittente(), [{"id": 991, "ricezione": 0, "sdi_stato": "ACCE"}]
		)
		documento.reload()
		# the public body's answer is applied too: it is another notice, not the same one
		self.assertEqual(esito["notices"], 1)
		self.assertEqual(documento.sdi_status, "esito_pa")
		self.assertEqual(
			documento.sdi_notices.split("\n"), ["IT0123_abc12_RC_001.xml", "IT0123_abc12_NE_001.xml"]
		)

	def test_senza_notifica_lo_stato_di_itala_diventa_quello_della_fattura(self):
		documento = self.inviata(recipient_type="pubblica_amministrazione", sdi_status="consegnata")
		self.con(lambda metodo, url, argomenti: Risposta(404, {"error": "non trovata"}))
		with patch("crm.invoicing.monitoraggio.avvisa") as avvisa:
			riconciliazione.riconcilia(
				self.emittente(),
				[{"id": 991, "ricezione": 0, "sdi_stato": "RIFI", "sdi_messaggio": "Importi errati"}],
			)
		documento.reload()
		self.assertEqual(documento.sdi_status, "esito_pa")
		self.assertIn("RIFI", documento.sdi_message)
		# who has to correct it hears it
		self.assertTrue(avvisa.called)

	def test_un_aggiornamento_che_non_si_applica_resta_per_il_giro_dopo(self):
		documento = self.inviata()
		guasto = {"ora": True}

		def risponde(metodo, url, argomenti):
			if url.endswith("/notifica"):
				if guasto["ora"]:
					raise ConnectionError("rete giu")
				return Grezza(
					CONSEGNA, {"Content-Disposition": 'attachment; filename="IT0123_abc12_RC_001.xml"'}
				)
			return Risposta(200, [])

		self.con(risponde)
		voce = {"id": 991, "ricezione": 0, "sdi_stato": "CONS"}
		esito = riconciliazione.riconcilia(self.emittente(), [voce])
		self.assertTrue(esito["problems"])
		riga = frappe.get_all(AGGIORNAMENTO, filters={"provider_id": "991"}, fields=["done", "attempts"])[0]
		self.assertEqual((riga.done, riga.attempts), (0, 1))
		documento.reload()
		self.assertEqual(documento.sdi_status, "inviato")

		# Itala does not give it again: the next round finds it kept
		guasto["ora"] = False
		riconciliazione.riconcilia(self.emittente(), [])
		documento.reload()
		self.assertEqual(documento.sdi_status, "consegnata")
		riga = frappe.get_all(AGGIORNAMENTO, filters={"provider_id": "991"}, fields=["done", "payload"])[0]
		self.assertEqual(riga.done, 1)
		self.assertFalse(riga.payload)

	def test_lo_stesso_aggiornamento_due_volte_e_uno(self):
		self.inviata()
		self.con(lambda metodo, url, argomenti: Risposta(404, {}))
		voce = {"id": 991, "ricezione": 0, "sdi_stato": "INVI"}
		riconciliazione.riconcilia(self.emittente(), [voce])
		riconciliazione.riconcilia(self.emittente(), [voce])
		self.assertEqual(frappe.db.count(AGGIORNAMENTO, {"provider_id": "991"}), 1)

	def test_la_riga_di_un_altra_partita_iva_non_e_della_societa(self):
		self.inviata()
		self.con(lambda metodo, url, argomenti: Risposta(404, {}))
		esito = riconciliazione.riconcilia(
			self.emittente(), [{"id": 991, "ricezione": 0, "sdi_stato": "CONS", "partita_iva": "09876543210"}]
		)
		self.assertEqual(esito["skipped"], 1)
		self.assertFalse(frappe.db.exists(AGGIORNAMENTO, {"provider_id": "991"}))

	def test_una_fattura_in_silenzio_da_un_giorno_si_chiede_per_nome(self):
		documento = self.inviata(sdi_sent_on=add_to_date(now_datetime(), days=-2))
		frappe.cache().delete_value(f"itala:chiesta:{documento.name}")

		def risponde(metodo, url, argomenti):
			if url.endswith("/fatture/991"):
				return Risposta(200, {"id": 991, "ricezione": 0, "sdi_stato": "NONC"})
			if url.endswith("/notifica"):
				return Risposta(404, {})
			return Risposta(200, [])

		sessione = self.con(risponde)
		with patch("crm.invoicing.monitoraggio.avvisa"):
			riconciliazione.riconcilia(self.emittente())
		self.assertTrue([c for c in sessione.chiamate if c["url"].endswith("/fatture/991")])
		documento.reload()
		self.assertEqual(documento.sdi_status, "mancata_consegna")

	def test_una_copia_del_sito_non_legge_gli_aggiornamenti(self):
		self.imposta(itala_site="un-altro-sito.example.com")
		sessione = self.con(lambda metodo, url, argomenti: Risposta(200, []))
		self.assertEqual(itala.aggiornamenti(self.emittente()), [])
		self.assertFalse(sessione.chiamate)
		righe = prova.mancanze(self.emittente(), agenzia=True)
		self.assertIn("itala_site", [r["field"] for r in righe])

	def test_il_primo_sito_che_legge_e_quello(self):
		self.con(lambda metodo, url, argomenti: Risposta(200, []))
		itala.aggiornamenti(self.emittente())
		self.assertEqual(frappe.db.get_value(AZIENDA, self.azienda.name, "itala_site"), frappe.local.site)

	# ------------------------------------------------------------- the centre's part

	def test_il_codice_destinatario_si_registra_all_agenzia(self):
		with patch("crm.invoicing.connessione.codice_destinatario", return_value=""):
			righe = prova.mancanze(self.emittente(), agenzia=True)
			self.assertIn("itala_recipient_code", [r["field"] for r in righe])
		with patch("crm.invoicing.connessione.codice_destinatario", return_value="M5UXCR1"):
			riga = next(
				r
				for r in prova.mancanze(self.emittente(), agenzia=False)
				if r["field"] == "recipient_code_registered"
			)
			self.assertIn("M5UXCR1", riga["consequence"])
			self.assertFalse(riga["blocking"])
			self.imposta(recipient_code_registered=1)
			campi = [r["field"] for r in prova.mancanze(self.emittente(), agenzia=False)]
			self.assertNotIn("recipient_code_registered", campi)

	def test_la_societa_si_registra_con_la_ricezione(self):
		self.imposta(itala_id_test="")
		sessione = self.con(lambda metodo, url, argomenti: Risposta(200, {"id": "5"}))
		itala.registra_azienda(self.emittente(), connessione.SANDBOX)
		self.assertEqual(sessione.chiamate[0]["json"]["abilita_ricezione"], 1)

	def test_chi_se_ne_va_si_toglie_da_itala(self):
		self.imposta(itala_id="42")
		sessione = self.con(lambda metodo, url, argomenti: Risposta(200, {"id": "42"}))
		self.assertTrue(itala.rimuovi_azienda(self.emittente(), connessione.PRODUZIONE))
		self.assertEqual(sessione.chiamate[-1]["metodo"], "DELETE")
		self.assertTrue(sessione.chiamate[-1]["url"].endswith("/ws2.0/prod/aziende/42"))
		self.assertFalse(frappe.db.get_value(AZIENDA, self.azienda.name, "itala_id"))


class WebhookItala(ConItala):
	def test_il_bearer_di_itala_arriva_al_webhook(self):
		set_encrypted_password(AZIENDA, self.azienda.name, "segreto-del-webhook", "sdi_webhook_secret")
		richiesta = frappe._dict(
			path=webhook.PERCORSO,
			environ={"HTTP_AUTHORIZATION": "Bearer segreto-del-webhook"},
			headers={},
			args={"company": self.azienda.name},
		)
		prima = getattr(frappe.local, "request", None)
		frappe.local.request = richiesta
		try:
			webhook.prima_della_richiesta()
			# taken away before Frappe reads it as one of its own tokens...
			self.assertNotIn("HTTP_AUTHORIZATION", richiesta.environ)
			# ...and still the secret the company is known by
			self.assertEqual(webhook.autentica(richiesta), self.azienda.name)
		finally:
			frappe.local.request = prima
			frappe.local.flags.pop("autorizzazione_del_provider", None)

	def test_un_altro_indirizzo_tiene_il_suo_bearer(self):
		richiesta = frappe._dict(
			path="/api/method/frappe.auth.get_logged_user", environ={"HTTP_AUTHORIZATION": "Bearer x"}
		)
		prima = getattr(frappe.local, "request", None)
		frappe.local.request = richiesta
		try:
			webhook.prima_della_richiesta()
			self.assertEqual(richiesta.environ["HTTP_AUTHORIZATION"], "Bearer x")
		finally:
			frappe.local.request = prima

	def test_un_segreto_sbagliato_non_entra(self):
		set_encrypted_password(AZIENDA, self.azienda.name, "segreto-del-webhook", "sdi_webhook_secret")
		richiesta = frappe._dict(
			headers={"Authorization": "Bearer altro"}, args={"company": self.azienda.name}
		)
		frappe.local.flags.pop("autorizzazione_del_provider", None)
		with self.assertRaises(webhook.Rifiutata):
			webhook.autentica(richiesta)

	def test_il_corpo_di_itala_e_una_lista_di_aggiornamenti(self):
		richiesta = frappe._dict(get_data=lambda: json.dumps([{"id": 1, "sdi_stato": "INVI"}]).encode())
		self.assertEqual(webhook._corpo(richiesta), {"data": [{"id": 1, "sdi_stato": "INVI"}]})


class QuelloCheEraStatoScrittoMale(ConItala):
	def test_gli_stati_e_l_identificativo_si_rimettono_a_posto(self):
		from crm.patches.v1_0 import itala_states_are_the_invoices as patch_

		consegnata = self.emessa(self.trattamento.name, self.osteopata.name)
		frappe.db.set_value(
			"CRM Invoice",
			consegnata.name,
			{"sdi_status": "consegnato", "sdi_provider_id": "991", "sdi_identifier": "991"},
		)
		vera = self.emessa(self.trattamento.name, self.osteopata.name)
		frappe.db.set_value(
			"CRM Invoice",
			vera.name,
			{"sdi_status": "accettato", "sdi_provider_id": "992", "sdi_identifier": "4400112233"},
		)
		patch_.execute()
		consegnata.reload()
		vera.reload()
		self.assertEqual(consegnata.sdi_status, "consegnata")
		self.assertFalse(consegnata.sdi_identifier)
		self.assertEqual(vera.sdi_status, "esito_pa")
		self.assertEqual(vera.sdi_identifier, "4400112233")
