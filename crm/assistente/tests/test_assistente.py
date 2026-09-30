# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The assistant: it runs only where the contract says the provider keeps nothing,
every request is written down, and a paper form becomes a draft a person checks.

The manager uploads the centre's paper consent form. The assistant - a model
behind a mocked endpoint - proposes a schema, the engine says what is still wrong,
the manager changes a label and creates the draft template: the register keeps
the model, the provider, the region, the fingerprints, the draft and how far the
template went from it. A scan with no text is refused, a failure is written down
as a failure, and sales neither asks nor reads.
"""

import json
from unittest import mock

import frappe
import requests
from frappe.tests import IntegrationTestCase

from crm.assistente import modello, modulo_di_carta, regole
from crm.moduli import consensi
from crm.moduli.pdf import pdf_da_html
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

MANAGER = "assistente.manager@example.com"
SALES = "assistente.sales@example.com"

PROPOSTA = {
	"title": "Consenso al trattamento",
	"sections": [
		{
			"id": "dati",
			"title": "I tuoi dati",
			"fields": [
				{"id": "nome", "type": "text", "label": "Nome e cognome", "required": True},
				{"id": "nato_il", "type": "date", "label": "Data di nascita"},
				{
					"id": "informativa",
					"type": "paragraph",
					"text": "Il centro tratta i tuoi dati per curarti.",
				},
				{
					"id": "firma",
					"type": "signature",
					"label": "Firma",
					"signer": "patient",
					"level": "simple",
				},
			],
		}
	],
}


def risposta_anthropic(testo, entrati=120, usciti=80):
	finta = mock.Mock()
	finta.raise_for_status = mock.Mock()
	finta.json = mock.Mock(
		return_value={
			"content": [{"type": "text", "text": testo}],
			"usage": {"input_tokens": entrati, "output_tokens": usciti},
		}
	)
	return finta


class AssistenteCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "assistente", "status": "Active"}])
		piano.save()
		livelli.dimentica_cache()
		utenti.sincronizza()
		consensi.assicura_tipi()
		for user, livello in ((MANAGER, "manager"), (SALES, "commerciale")):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		self.configura()
		livelli.dimentica_cache()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()
		frappe.clear_document_cache(modello.IMPOSTAZIONI, modello.IMPOSTAZIONI)

	def configura(self, **altro):
		cfg = frappe.get_single(modello.IMPOSTAZIONI)
		cfg.update(
			{
				"enabled": 1,
				"paper_forms": 1,
				"provider": regole.ANTHROPIC,
				"base_url": "https://llm.example.eu",
				"model": "claude-prova",
				"api_key": "chiave-segreta",
				"region": "EU (Milano)",
				"no_retention": 1,
				**altro,
			}
		)
		cfg.save()
		frappe.clear_document_cache(modello.IMPOSTAZIONI, modello.IMPOSTAZIONI)

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def carica_pdf(
		self, html="<h1>Consenso</h1><p>Nome e cognome ______ Data di nascita ______</p><p>Firma ______</p>"
	):
		# the manager uploads the paper form: a private file of theirs
		self.come(MANAGER)
		file = frappe.get_doc(
			{"doctype": "File", "file_name": "consenso.pdf", "is_private": 1, "content": pdf_da_html(html)}
		).insert()
		return file.file_url


class IlContratto(AssistenteCase):
	def test_senza_il_contratto_non_parte(self):
		with self.assertRaises(frappe.ValidationError):
			self.configura(no_retention=0)
		with self.assertRaises(frappe.ValidationError):
			self.configura(base_url="http://llm.example.eu")
		# a model on the centre's own machine may speak plain http
		self.configura(provider=regole.COMPATIBILE_OPENAI, base_url="http://localhost:8080/v1")

	def test_spento_non_si_chiede(self):
		self.configura(enabled=0)
		self.come(MANAGER)
		self.assertFalse(modello.get_status()["enabled"])
		with self.assertRaises(frappe.ValidationError):
			modello.chiedi("form_from_paper", "istruzioni", "testo")


class IlRegistro(AssistenteCase):
	def test_ogni_richiesta_si_scrive(self):
		self.come(MANAGER)
		with mock.patch.object(requests, "post", return_value=risposta_anthropic('{"a": 1}')) as post:
			risposta = modello.chiedi("form_from_paper", "istruzioni", "testo", json_atteso=True)
		self.assertEqual(risposta.dati, {"a": 1})
		chiamata = post.call_args
		self.assertEqual(chiamata.args[0], "https://llm.example.eu/v1/messages")
		self.assertEqual(chiamata.kwargs["headers"]["x-api-key"], "chiave-segreta")
		self.assertEqual(chiamata.kwargs["json"]["system"], "istruzioni")
		frappe.set_user("Administrator")
		evento = frappe.get_doc(modello.EVENTO, risposta.evento)
		self.assertEqual(
			(evento.function, evento.user, evento.provider, evento.model, evento.region),
			("form_from_paper", MANAGER, regole.ANTHROPIC, "claude-prova", "EU (Milano)"),
		)
		self.assertEqual((evento.input_tokens, evento.output_tokens, evento.status), (120, 80, regole.BOZZA))
		self.assertEqual(evento.output_hash, regole.impronta('{"a": 1}'))
		self.assertEqual(evento.input_hash, regole.impronta("istruzioni\n\ntesto"))

	def test_compatibile_openai(self):
		self.configura(provider=regole.COMPATIBILE_OPENAI, base_url="http://localhost:8080/v1")
		finta = mock.Mock()
		finta.raise_for_status = mock.Mock()
		finta.json = mock.Mock(
			return_value={
				"choices": [{"message": {"content": "Ciao"}}],
				"usage": {"prompt_tokens": 7, "completion_tokens": 2},
			}
		)
		self.come(MANAGER)
		with mock.patch.object(requests, "post", return_value=finta) as post:
			risposta = modello.chiedi("form_from_paper", "istruzioni", "testo")
		self.assertEqual(risposta.testo, "Ciao")
		self.assertEqual(post.call_args.args[0], "http://localhost:8080/v1/chat/completions")
		self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer chiave-segreta")

	def test_un_errore_resta_scritto(self):
		self.come(MANAGER)
		with mock.patch.object(requests, "post", side_effect=requests.Timeout()):
			risposta = modello.chiedi("form_from_paper", "istruzioni", "testo")
		self.assertEqual(risposta.errore, "The model did not answer in time")
		with mock.patch.object(requests, "post", return_value=risposta_anthropic("Non so")):
			strana = modello.chiedi("form_from_paper", "istruzioni", "testo", json_atteso=True)
		self.assertEqual(strana.errore, "The answer is not what was asked")
		frappe.set_user("Administrator")
		self.assertEqual(
			frappe.db.get_value(modello.EVENTO, risposta.evento, ["status", "error"]),
			(regole.FALLITA, "The model did not answer in time"),
		)

	def test_non_si_cancella_e_lo_legge_chi_deve(self):
		self.come(MANAGER)
		with mock.patch.object(requests, "post", return_value=risposta_anthropic("{}")):
			risposta = modello.chiedi("form_from_paper", "istruzioni", "testo")
		self.assertIn(risposta.evento, [e["name"] for e in modello.get_events()["events"]])
		letto = modello.mark_reviewed(risposta.evento, "Tutto in ordine")
		self.assertEqual((letto["reviewed_by"], letto["review_note"]), (MANAGER, "Tutto in ordine"))
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			modello.get_events()
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(modello.EVENTO, risposta.evento, ignore_permissions=True)


class DalModuloDiCarta(AssistenteCase):
	def test_la_proposta_diventa_una_bozza_controllata(self):
		url = self.carica_pdf()
		self.come(MANAGER)
		with mock.patch.object(
			requests,
			"post",
			return_value=risposta_anthropic("Ecco:\n```json\n" + json.dumps(PROPOSTA) + "\n```"),
		) as post:
			proposta = modulo_di_carta.propose(url)
		# the model read the paper's words, and was told the engine's components
		inviato = post.call_args.kwargs["json"]
		self.assertIn("Nome e cognome", inviato["messages"][0]["content"])
		self.assertIn("signature", inviato["system"])
		self.assertEqual(proposta["title"], "Consenso al trattamento")
		self.assertEqual(
			[c["id"] for c in proposta["schema"]["sections"][0]["fields"]][:2], ["nome", "nato_il"]
		)
		self.assertIsInstance(proposta["problems"], list)
		# the manager puts a label right, and creates the draft
		schema = proposta["schema"]
		schema["sections"][0]["fields"][0]["label"] = "Nome e cognome del paziente"
		fatto = modulo_di_carta.create_draft(proposta["event"], proposta["title"], json.dumps(schema))
		frappe.set_user("Administrator")
		modello_creato = frappe.get_doc("CRM Form Template", fatto["template"])
		self.assertFalse(modello_creato.current_version)
		self.assertIn("Nome e cognome del paziente", modello_creato.schema)
		evento = frappe.get_doc(modello.EVENTO, proposta["event"])
		self.assertEqual((evento.status, evento.checked_by), (regole.ACCETTATA, MANAGER))
		self.assertEqual(
			(evento.reference_doctype, evento.reference_name), ("CRM Form Template", fatto["template"])
		)
		self.assertIn("+", evento.difference)
		self.assertGreater(evento.change_ratio, 0)
		# the model's own words stay as they came
		self.assertTrue(evento.draft.startswith("Ecco:"))

	def test_una_scansione_non_ha_testo(self):
		url = self.carica_pdf("<div style='height: 200px'></div>")
		self.come(MANAGER)
		with mock.patch.object(requests, "post") as post:
			with self.assertRaises(frappe.ValidationError):
				modulo_di_carta.propose(url)
		post.assert_not_called()

	def test_chi_non_costruisce_moduli_non_chiede(self):
		url = self.carica_pdf()
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			modulo_di_carta.propose(url)

	def test_scartata_resta_nel_registro(self):
		url = self.carica_pdf()
		self.come(MANAGER)
		with mock.patch.object(requests, "post", return_value=risposta_anthropic(json.dumps(PROPOSTA))):
			proposta = modulo_di_carta.propose(url)
		modulo_di_carta.discard(proposta["event"])
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(modello.EVENTO, proposta["event"], "status"), regole.SCARTATA)
