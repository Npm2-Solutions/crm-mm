# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The signatures the CRM does not give itself.

On paper: the answers typed are checked, the scan is kept inside the PDF/A with
its hash, and the operator attests it is a true copy; without the attestation,
or with something that is not a scan of this form, nothing is signed.

With a provider, through its adapter: the form goes with its answers frozen and
waits; the provider's webhook signs it with the provider's PDF, as it came; a
refusal leaves it a draft; a call that is not the provider's changes nothing.
"""

import hashlib
import io
import json
from typing import ClassVar
from unittest import mock

import frappe

from crm.invoicing.engine import pdfa
from crm.moduli import compilazioni, firme, registro, traccia
from crm.moduli.tests.test_compilazioni import DESK, PRIVACY, CompilazioniCase
from crm.permissions import livelli


@firme.registra_fornitore
class FornitoreDiProva(firme.FornitoreFirma):
	"""A provider that signs when told to: what a real one does, minus the network."""

	nome = "Prova"
	livelli = ("advanced",)
	buste: ClassVar[dict] = {}
	prossimo: ClassVar[dict | None] = None

	def crea(self, doc, pdf, firmatari):
		riferimento = f"BUSTA-{doc.name}-{len(self.buste)}"
		self.buste[riferimento] = {"pdf": pdf, "firmatari": firmatari}
		return {
			"reference": riferimento,
			"signers": [
				{"field": f["field"], "url": self.pagina(riferimento, f["field"])} for f in firmatari
			],
		}

	def pagina(self, riferimento, campo):
		return f"https://firma.example.com/{riferimento}/{campo}"

	def evento(self, richiesta):
		if not FornitoreDiProva.prossimo or FornitoreDiProva.prossimo.get("secret") != "segreto":
			raise frappe.PermissionError("not the provider")
		return FornitoreDiProva.prossimo

	def firmato(self, riferimento):
		# what comes back is another file: the one the provider signed
		busta = self.buste[riferimento]
		busta.setdefault("firmato", con_la_firma(busta["pdf"]))
		return busta["firmato"]

	def prove(self, riferimento):
		return scansione_pdf(1)


def scansione_png(linea=(50, 700, 300, 650, 550, 720)) -> bytes:
	from PIL import Image, ImageDraw

	immagine = Image.new("RGB", (600, 800), (255, 255, 255))
	ImageDraw.Draw(immagine).line(linea, fill=(10, 10, 10), width=4)
	buffer = io.BytesIO()
	immagine.save(buffer, format="PNG")
	return buffer.getvalue()


def scansione_pdf(pagine=2) -> bytes:
	from pypdf import PdfWriter

	scrittore = PdfWriter()
	for _pagina in range(pagine):
		scrittore.add_blank_page(width=595, height=842)
	buffer = io.BytesIO()
	scrittore.write(buffer)
	return buffer.getvalue()


def con_la_firma(pdf: bytes) -> bytes:
	from pypdf import PdfReader, PdfWriter

	scrittore = PdfWriter(clone_from=PdfReader(io.BytesIO(pdf)))
	scrittore.add_metadata({"/Signer": "Prova"})
	buffer = io.BytesIO()
	scrittore.write(buffer)
	return buffer.getvalue()


def pagine(contenuto: bytes) -> int:
	from pypdf import PdfReader

	return len(PdfReader(io.BytesIO(contenuto)).pages)


AVANZATA = json.loads(json.dumps(PRIVACY))
AVANZATA["sections"][0]["fields"][-1]["level"] = "advanced"


class FirmeCase(CompilazioniCase):
	def carica(self, nome, contenuto, file_name="scansione.png", **altro):
		return frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"attached_to_doctype": compilazioni.MODULO,
				"attached_to_name": nome,
				"is_private": 1,
				"content": contenuto,
				**altro,
			}
		).insert(ignore_permissions=True)

	def risposte(self):
		return json.dumps({"read": True, "marketing": True, "weight": "70"})


class SuCarta(FirmeCase):
	def test_si_firma_su_carta_e_si_attesta(self):
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		contenuto = scansione_png()
		file = self.carica(nome, contenuto)
		firmato = compilazioni.sign_on_paper(nome, self.risposte(), file.file_url, attest=1)
		self.assertEqual((firmato["docstatus"], firmato["channel"]), (1, "On paper"))
		[firma] = firmato["signatures"]
		self.assertEqual((firma["level"], firma["method"], firma["image"]), ("handwritten", "On paper", None))
		self.assertEqual(firmato["paper"]["sha256"], hashlib.sha256(contenuto).hexdigest())
		self.assertIn("On paper", firmato["recognised"])

		frappe.set_user("Administrator")
		pdf = frappe.get_doc("File", {"file_url": firmato["pdf_file"]}).get_content(encodings=[])
		# the scan is inside the PDF/A, as its source
		self.assertEqual(pdfa.verifica_byte(pdf).allegati, 1)
		self.assertIn(b"/Source", pdf)
		eventi = [e.event for e in traccia.eventi(compilazioni.MODULO, nome)]
		self.assertLess(eventi.index("attested"), eventi.index("signed"))
		self.assertTrue(traccia.verifica_catena(compilazioni.MODULO, nome)["integra"])
		self.assertEqual(
			frappe.db.get_value(
				"CRM Consent", {"lead": self.giulia.name, "consent_type": "marketing"}, "channel"
			),
			"On paper",
		)

	def test_una_scansione_in_pdf_porta_le_sue_pagine(self):
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		file = self.carica(nome, scansione_pdf(2), file_name="scansione.pdf")
		firmato = compilazioni.sign_on_paper(nome, self.risposte(), file.file_url, attest=1)
		frappe.set_user("Administrator")
		pdf = frappe.get_doc("File", {"file_url": firmato["pdf_file"]}).get_content(encodings=[])
		self.assertGreaterEqual(pagine(pdf), 1 + 2)

	def test_senza_attestazione_o_scansione_vera_non_si_firma(self):
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		buona = self.carica(nome, scansione_png())
		with self.assertRaises(frappe.ValidationError):
			compilazioni.sign_on_paper(nome, self.risposte(), buona.file_url, attest=0)
		finta = self.carica(nome, b"not a picture at all", file_name="finta.png")
		with self.assertRaises(frappe.ValidationError):
			compilazioni.sign_on_paper(nome, self.risposte(), finta.file_url, attest=1)
		pubblica = self.carica(nome, scansione_png(), file_name="pubblica.png", is_private=0)
		with self.assertRaises(frappe.ValidationError):
			compilazioni.sign_on_paper(nome, self.risposte(), pubblica.file_url, attest=1)
		# the scan of another form is not this form's
		altro = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		di_un_altro = self.carica(altro, scansione_png(linea=(80, 600, 500, 640)))
		with self.assertRaises(frappe.ValidationError):
			compilazioni.sign_on_paper(nome, self.risposte(), di_un_altro.file_url, attest=1)
		# the answers are checked all the same
		with self.assertRaises(frappe.ValidationError):
			compilazioni.sign_on_paper(nome, json.dumps({}), buona.file_url, attest=1)
		self.assertEqual(frappe.db.get_value(compilazioni.MODULO, nome, "docstatus"), 0)

	def test_la_copia_da_firmare_si_stampa(self):
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		compilazioni.save_answers(nome, self.risposte())
		compilazioni.printable_form(nome)
		self.assertTrue(frappe.local.response.filecontent.startswith(b"%PDF"))
		frappe.local.flags.commit = False
		frappe.set_user("Administrator")
		self.assertIn("printed", [e.event for e in traccia.eventi(compilazioni.MODULO, nome)])

	def test_un_modulo_con_firma_avanzata_si_firma_su_carta(self):
		modello = self.pubblica(AVANZATA, "Consenso informato")
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, modello)["name"]
		file = self.carica(nome, scansione_png())
		firmato = compilazioni.sign_on_paper(nome, self.risposte(), file.file_url, attest=1)
		self.assertEqual(firmato["docstatus"], 1)


class ConIlFornitore(FirmeCase):
	def setUp(self):
		super().setUp()
		FornitoreDiProva.buste = {}
		FornitoreDiProva.prossimo = None
		attivo = mock.patch.object(firme, "attivo", return_value=FornitoreDiProva())
		attivo.start()
		self.addCleanup(attivo.stop)
		self.consenso = self.pubblica(AVANZATA, "Consenso informato")

	def manda(self):
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.consenso)["name"]
		mandato = compilazioni.send_to_provider(nome, self.risposte())
		return nome, mandato

	def chiama(self, **esito):
		FornitoreDiProva.prossimo = {"secret": "segreto", **esito}
		frappe.set_user("Guest")
		try:
			return firme.webhook(provider="Prova")
		finally:
			frappe.set_user("Administrator")

	def test_il_fornitore_firma_e_il_pdf_e_il_suo(self):
		nome, mandato = self.manda()
		self.assertEqual((mandato["provider_status"], mandato["provider_name"]), ("Sent", "Prova"))
		[firmatario] = mandato["signers"]
		self.assertTrue(firmatario["url"].startswith("https://firma.example.com/"))
		busta = next(iter(FornitoreDiProva.buste.values()))
		self.assertTrue(busta["pdf"].startswith(b"%PDF"))
		self.assertEqual(busta["firmatari"][0]["email"], None)
		# while it is at the provider, the answers do not change
		with self.assertRaises(frappe.ValidationError):
			compilazioni.save_answers(nome, json.dumps({"weight": 80}))

		riferimento = frappe.db.get_value(compilazioni.MODULO, nome, "provider_reference")
		esito = self.chiama(
			reference=riferimento, event="signed", signers=[{"field": "sign", "ip_address": "10.1.2.3"}]
		)
		self.assertTrue(esito["known"])
		doc = frappe.get_doc(compilazioni.MODULO, nome)
		self.assertEqual((doc.docstatus, doc.provider_status), (1, "Signed"))
		[firma] = doc.signatures
		self.assertEqual(
			(firma.level, firma.method, firma.provider, firma.provider_reference, firma.ip_address),
			("advanced", "Provider", "Prova", riferimento, "10.1.2.3"),
		)
		# the document is the provider's, as it came: not converted
		pdf = frappe.get_doc("File", {"file_url": doc.pdf_file}).get_content(encodings=[])
		self.assertEqual(pdf, FornitoreDiProva.buste[riferimento]["firmato"])
		self.assertEqual(doc.pdf_hash, hashlib.sha256(pdf).hexdigest())
		self.assertIn("Prova", doc.pdf_conformance)
		self.assertTrue(doc.provider_evidence)
		eventi = [e.event for e in traccia.eventi(compilazioni.MODULO, nome)]
		self.assertEqual(eventi[:4], ["created", "provider_sent", "signed", "pdf_received"])
		# said twice, it is still signed once
		self.chiama(reference=riferimento, event="signed")
		self.assertEqual([e.event for e in traccia.eventi(compilazioni.MODULO, nome)].count("signed"), 1)
		self.assertEqual(
			frappe.db.get_value(
				"CRM Consent", {"lead": self.giulia.name, "consent_type": "marketing"}, "status"
			),
			registro.DATO,
		)

	def test_rifiutato_torna_una_bozza(self):
		nome, _mandato = self.manda()
		riferimento = frappe.db.get_value(compilazioni.MODULO, nome, "provider_reference")
		self.chiama(reference=riferimento, event="declined")
		doc = frappe.get_doc(compilazioni.MODULO, nome)
		self.assertEqual((doc.docstatus, doc.provider_status), (0, "Declined"))
		self.come(DESK)
		# a draft again: it can be changed and sent again
		compilazioni.save_answers(nome, json.dumps({"weight": 80}))
		self.assertEqual(compilazioni.send_to_provider(nome, self.risposte())["provider_status"], "Sent")

	def test_una_chiamata_non_sua_non_cambia_niente(self):
		nome, _mandato = self.manda()
		riferimento = frappe.db.get_value(compilazioni.MODULO, nome, "provider_reference")
		FornitoreDiProva.prossimo = {"secret": "sbagliato", "reference": riferimento, "event": "signed"}
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			firme.webhook(provider="Prova")
		with self.assertRaises(frappe.PermissionError):
			firme.webhook(provider="UnAltro")
		frappe.set_user("Administrator")
		self.assertEqual(self.chiama(reference="BUSTA-sconosciuta", event="signed")["known"], False)
		self.assertEqual(frappe.db.get_value(compilazioni.MODULO, nome, "docstatus"), 0)

	def test_si_riprende_dal_fornitore(self):
		nome, _mandato = self.manda()
		riferimento = frappe.db.get_value(compilazioni.MODULO, nome, "provider_reference")
		self.come(DESK)
		ripreso = compilazioni.take_back_from_provider(nome)
		self.assertIsNone(ripreso["provider_status"])
		compilazioni.save_answers(nome, json.dumps({"weight": 80}))
		# what the provider still has does not sign it any more
		self.assertEqual(self.chiama(reference=riferimento, event="signed")["known"], False)
		self.assertEqual(frappe.db.get_value(compilazioni.MODULO, nome, "docstatus"), 0)

	def test_un_livello_che_il_fornitore_non_da(self):
		schema = json.loads(json.dumps(PRIVACY))
		schema["sections"][0]["fields"][-1]["level"] = "qualified"
		modello = self.pubblica(schema, "Referto")
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, modello)["name"]
		with self.assertRaises(frappe.ValidationError):
			compilazioni.send_to_provider(nome, self.risposte())


class SenzaFornitore(FirmeCase):
	def tearDown(self):
		super().tearDown()
		# the settings were saved in a transaction rolled back: not in the cache either
		frappe.clear_document_cache(firme.IMPOSTAZIONI, firme.IMPOSTAZIONI)

	def test_senza_fornitore_non_si_manda(self):
		self.assertIsNone(firme.attivo())
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		with self.assertRaises(frappe.ValidationError):
			compilazioni.send_to_provider(nome, self.risposte())
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			firme.webhook()

	def piano(self, *moduli):
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": modulo, "status": "Active"} for modulo in moduli])
		piano.save()
		livelli.dimentica_cache()

	def fornitore_impostato(self):
		impostazioni = frappe.get_single(firme.IMPOSTAZIONI)
		impostazioni.enabled = 1
		impostazioni.provider = "Prova"
		impostazioni.save()
		frappe.clear_document_cache(firme.IMPOSTAZIONI, firme.IMPOSTAZIONI)

	def test_la_firma_avanzata_e_un_extra_del_piano(self):
		"""The provider set up, the plan decides: off, nothing new goes to it; what
		was sent still comes back."""
		self.fornitore_impostato()
		self.piano()
		self.assertIsNone(firme.attivo())
		self.assertEqual(firme.attivo(nuove=False).nome, "Prova")
		self.assertEqual(firme.get_provider()["name"], None)
		self.piano(firme.PIANO)
		self.assertEqual(firme.attivo().nome, "Prova")

	def test_le_impostazioni_conoscono_i_fornitori(self):
		self.piano(firme.PIANO)
		impostazioni = frappe.get_single(firme.IMPOSTAZIONI)
		impostazioni.enabled = 1
		impostazioni.provider = "Sconosciuto"
		with self.assertRaises(frappe.ValidationError):
			impostazioni.save()
		self.fornitore_impostato()
		self.assertEqual(firme.attivo().nome, "Prova")
		self.assertIn("Prova", firme.get_provider()["available"])
		# the operator's page knows it can send there
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		self.assertEqual(compilazioni.get_form(nome)["provider"]["name"], "Prova")
