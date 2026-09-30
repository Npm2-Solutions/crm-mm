# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The assistant in the clinic: drafts from a signed note, checked and signed.

The doctor signs Anna's visit and asks for a letter to her family doctor: the
model gets the note, never Anna's name, and the draft leaves the gaps for the
doctor to fill. Kept, it is a note added to the visit, still to sign, with the
mark of who checked it; the instructions may also go on Anna's board. Without
Anna's consent, from a draft or from somebody else's note there is no draft. The
register's clinical events are the medical director's to read, not the manager's.
"""

import json
from unittest import mock

import frappe
import requests

from crm.assistente import modello, regole
from crm.clinica import ASSISTENTE, assistente, cartella
from crm.clinica.tests.test_cartella import DIRECTOR, DOC1, DOC2, MANAGER, RecordCase
from crm.moduli import consensi
from crm.permissions import livelli

NOTA = "<p>Lombalgia acuta. Esercizi di mobilità per due settimane. Controllo tra un mese.</p>"
LETTERA = "Gentile collega,\nho visitato [patient's name] per una lombalgia acuta.\nControllo tra un mese.\n[practitioner's name]"


def risposta(testo):
	finta = mock.Mock()
	finta.raise_for_status = mock.Mock()
	finta.json = mock.Mock(
		return_value={
			"content": [{"type": "text", "text": testo}],
			"usage": {"input_tokens": 90, "output_tokens": 40},
		}
	)
	return finta


class AssistenteClinicoCase(RecordCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set(
			"modules",
			[{"module": "clinica", "status": "Active"}, {"module": "assistente", "status": "Active"}],
		)
		piano.save()
		consensi.assicura_tipi()
		cfg = frappe.get_single(modello.IMPOSTAZIONI)
		cfg.update(
			{
				"enabled": 1,
				"paper_forms": 1,
				"note_drafts": 1,
				"dictation": 1,
				"summaries": 1,
				"provider": regole.ANTHROPIC,
				"base_url": "https://llm.example.eu",
				"model": "claude-prova",
				"api_key": "chiave",
				"region": "EU",
				"no_retention": 1,
			}
		)
		cfg.save()
		frappe.clear_document_cache(modello.IMPOSTAZIONI, modello.IMPOSTAZIONI)
		livelli.dimentica_cache()
		self.visita = self.scrive(DOC1, content=NOTA, sign=1)

	def tearDown(self):
		super().tearDown()
		frappe.clear_document_cache(modello.IMPOSTAZIONI, modello.IMPOSTAZIONI)

	def consenso(self):
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, ASSISTENTE.chiave)

	def bozza(self, kind="letter", testo=LETTERA, user=DOC1, record=None):
		self.come(user)
		with mock.patch.object(requests, "post", return_value=risposta(testo)) as post:
			fatto = assistente.draft_from_note(record or self.visita["name"], kind)
		return fatto, post


class LaBozza(AssistenteClinicoCase):
	def test_la_lettera_dalla_nota_senza_il_nome_della_paziente(self):
		self.consenso()
		fatto, post = self.bozza()
		self.assertEqual((fatto["draft"], fatto["error"]), (LETTERA, None))
		inviato = post.call_args.kwargs["json"]
		self.assertIn("Lombalgia acuta", inviato["messages"][0]["content"])
		for parola in ("Anna", "Cartella", self.anna.name):
			self.assertNotIn(parola, json.dumps(inviato))
		self.assertIn("Write only what the note says", " ".join(inviato["system"].split()))
		frappe.set_user("Administrator")
		evento = frappe.get_doc(modello.EVENTO, fatto["event"])
		self.assertEqual(
			(evento.function, evento.read_capability, evento.reference_name),
			("letter_from_note", "assistente.registro_clinico", self.visita["name"]),
		)

	def test_senza_consenso_da_una_bozza_o_dalla_nota_di_altri_no(self):
		with self.assertRaises(frappe.ValidationError):
			self.bozza()
		self.consenso()
		bozza = self.scrive(DOC1, content="<p>Da firmare</p>")
		with self.assertRaises(frappe.ValidationError):
			self.bozza(record=bozza["name"])
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, cartella.DOSSIER)
		with self.assertRaises(frappe.PermissionError):
			self.bozza(user=DOC2)


class LaNotaTenuta(AssistenteClinicoCase):
	def test_diventa_una_nota_da_firmare_con_il_segno(self):
		self.consenso()
		fatto, _post = self.bozza()
		corretta = LETTERA.replace("[patient's name]", "la signora Cartella").replace(
			"[practitioner's name]", "Dott. Uno"
		)
		tenuta = assistente.keep_draft(fatto["event"], corretta)
		frappe.set_user("Administrator")
		nota = frappe.get_doc(cartella.DOCTYPE, tenuta["note"])
		self.assertEqual(
			(nota.kind, nota.docstatus, nota.practitioner, nota.addendum_to),
			("Note", 0, DOC1, self.visita["name"]),
		)
		self.assertIn("la signora Cartella", nota.content)
		self.assertIn(tenuta["mark"], nota.content)
		self.assertTrue(tenuta["mark"].startswith("AI draft, checked by"))
		evento = frappe.get_doc(modello.EVENTO, fatto["event"])
		self.assertEqual((evento.status, evento.checked_by), (regole.ACCETTATA, DOC1))
		self.assertIn("+Dott. Uno", evento.difference)

	def test_le_istruzioni_anche_sulla_bacheca(self):
		self.consenso()
		fatto, _post = self.bozza("instructions", "Faccia gli esercizi ogni mattina.\nTorni tra un mese.")
		tenuta = assistente.keep_draft(
			fatto["event"], "Faccia gli esercizi ogni mattina.\nTorni tra un mese.", 1
		)
		self.assertTrue(tenuta["posted"])
		frappe.set_user("Administrator")
		[messaggio] = frappe.get_all(
			"Clinic Message", filters={"lead": self.anna.name}, fields=["kind", "body", "author"]
		)
		self.assertEqual((messaggio.kind, messaggio.author), ("Care", DOC1))
		self.assertIn("Faccia gli esercizi", messaggio.body)
		self.assertIn("AI draft, checked by", messaggio.body)

	def test_scartata_non_lascia_note(self):
		self.consenso()
		fatto, _post = self.bozza()
		assistente.discard_draft(fatto["event"])
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(modello.EVENTO, fatto["event"], "status"), regole.SCARTATA)
		self.assertFalse(frappe.db.exists(cartella.DOCTYPE, {"addendum_to": self.visita["name"]}))


class IlRegistroClinico(AssistenteClinicoCase):
	def test_lo_legge_la_direzione_non_il_manager(self):
		self.consenso()
		fatto, _post = self.bozza()
		self.come(MANAGER)
		self.assertNotIn(fatto["event"], [e["name"] for e in modello.get_events()["events"]])
		with self.assertRaises(frappe.PermissionError):
			modello.get_event(fatto["event"])
		self.come(DIRECTOR)
		self.assertIn(fatto["event"], [e["name"] for e in modello.get_events()["events"]])
		self.assertEqual(modello.get_event(fatto["event"])["draft"], LETTERA)


SCHEDA = {
	"sections": [
		{
			"id": "visita",
			"title": "Visita",
			"fields": [
				{"id": "dolore", "type": "scale", "label": "Dolore", "min": 0, "max": 10},
				{
					"id": "sede",
					"type": "choice",
					"label": "Sede",
					"options": [{"label": "Lombare"}, {"label": "Cervicale"}],
				},
				{"id": "farmaci", "type": "text", "label": "Farmaci in corso", "summary": "medications"},
				{"id": "fumo", "type": "yesno", "label": "Fuma"},
			],
		}
	]
}


class LaDettatura(AssistenteClinicoCase):
	def setUp(self):
		super().setUp()
		from crm.clinica.tests.test_schede import SchedeCase

		frappe.set_user("Administrator")
		self.scheda = SchedeCase.pubblica(SCHEDA, "Visita della schiena", use="Clinical sheet")
		self.come(DOC1)
		self.bozza_visita = cartella.start_sheet(self.anna.name, self.scheda)["name"]

	def proponi(self, parole="Dolore sei su dieci in sede lombare, prende ibuprofene 600, non fuma."):
		from crm.clinica import dettatura

		risposte = {
			"dolore": 6,
			"sede": "Lombare",
			"farmaci": "Ibuprofene 600 mg",
			"fumo": False,
			"inventato": "x",
		}
		self.come(DOC1)
		with mock.patch.object(
			requests, "post", return_value=risposta(json.dumps({"answers": risposte}))
		) as post:
			fatto = dettatura.propose_answers(self.bozza_visita, parole)
		return fatto, post

	def test_le_parole_diventano_risposte_da_spuntare(self):
		self.consenso()
		fatto, post = self.proponi()
		proposte = {p["field"]: p for p in fatto["proposals"]}
		self.assertEqual(set(proposte), {"dolore", "sede", "farmaci", "fumo"})
		# medicines, allergies, doses: confirmed one by one
		self.assertTrue(proposte["farmaci"]["one_by_one"])
		self.assertFalse(proposte["dolore"]["one_by_one"])
		inviato = post.call_args.kwargs["json"]
		self.assertIn("sede (choice): Sede - options: Lombare | Cervicale", inviato["system"])
		self.assertNotIn("Anna", json.dumps(inviato))

	def test_si_scrive_solo_quello_spuntato(self):
		from crm.clinica import dettatura

		self.consenso()
		fatto, _post = self.proponi()
		dettatura.apply_answers(fatto["event"], json.dumps({"dolore": 6, "sede": "Lombare"}))
		frappe.set_user("Administrator")
		visita = frappe.get_doc(cartella.DOCTYPE, self.bozza_visita)
		risposte = json.loads(visita.answers)
		self.assertEqual((risposte.get("dolore"), risposte.get("sede")), (6, "Lombare"))
		self.assertNotIn("farmaci", risposte)
		self.assertEqual(visita.docstatus, 0)
		evento = frappe.get_doc(modello.EVENTO, fatto["event"])
		self.assertEqual(evento.status, regole.ACCETTATA)
		self.assertIn("farmaci", evento.difference)

	def test_una_visita_firmata_o_di_altri_no(self):
		from crm.clinica import dettatura

		self.consenso()
		self.come(DOC2)
		with self.assertRaises(frappe.PermissionError):
			dettatura.propose_answers(self.bozza_visita, "Dolore sei su dieci in sede lombare.")
		self.come(DOC1)
		with self.assertRaises(frappe.ValidationError):
			dettatura.propose_answers(self.visita["name"], "Dolore sei su dieci in sede lombare.")


class IlRiassunto(AssistenteClinicoCase):
	def test_dalle_fonti_che_si_leggono_citandole(self):
		from crm.clinica import riassunto, sintesi

		self.consenso()
		self.come(DOC1)
		sintesi.set_value(self.anna.name, "allergies", "Penicillina")
		testo = "Lombalgia acuta con esercizi [1]. Allergica alla penicillina [2]."
		with mock.patch.object(requests, "post", return_value=risposta(testo)) as post:
			fatto = riassunto.summary_before_visit(self.anna.name)
		self.assertEqual(fatto["summary"], testo)
		self.assertEqual([f["n"] for f in fatto["sources"]], list(range(1, len(fatto["sources"]) + 1)))
		self.assertEqual(fatto["sources"][0]["name"], self.visita["name"])
		sistema = " ".join(post.call_args.kwargs["json"]["system"].split())
		self.assertIn("[1]", sistema)
		self.assertIn("Lombalgia acuta", sistema)
		self.assertIn("Penicillina", sistema)
		self.assertIn("no score, no ranking, no alert", sistema)
		self.assertNotIn("Anna", sistema)
		riassunto.read(fatto["event"])
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(modello.EVENTO, fatto["event"], "status"), regole.ACCETTATA)
		# what it read is in the access log, like any reading of the record
		self.assertTrue(
			frappe.db.exists(
				"View Log",
				{
					"reference_doctype": cartella.DOCTYPE,
					"reference_name": self.visita["name"],
					"viewed_by": DOC1,
				},
			)
		)

	def test_senza_consenso_niente_riassunto(self):
		from crm.clinica import riassunto

		self.come(DOC1)
		with self.assertRaises(frappe.ValidationError):
			riassunto.summary_before_visit(self.anna.name)
