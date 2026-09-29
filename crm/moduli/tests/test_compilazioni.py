# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Filling and signing a form: the draft, the signature, the PDF, the register.

What a signed form keeps is what the person signed: the answers checked by the
server's own rules, the picture of each stroke with who, when and on which
answers, a PDF/A made once, the consents in the register on the words they read,
and the events of the form in a chain that shows any change.
"""

import base64
import hashlib
import io
import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.moduli import compilazioni, consensi, modelli, traccia
from crm.moduli import schema as S
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

DESK = "forms.desk@example.com"
SALES = "forms.sales@example.com"
OTHER = "forms.other@example.com"

PRIVACY = {
	"sections": [
		{
			"id": "privacy",
			"title": "Privacy",
			"fields": [
				{"id": "notice", "type": "paragraph", "text": "Come usiamo i tuoi dati."},
				{
					"id": "read",
					"type": "consent",
					"label": "Ho letto",
					"consent_type": "privacy_notice",
					"must_accept": True,
				},
				{
					"id": "marketing",
					"type": "consent",
					"label": "Novità",
					"consent_type": "marketing",
					"required": True,
				},
				{"id": "weight", "type": "number", "label": "Peso", "unit": "kg"},
				{"id": "sign", "type": "signature", "label": "Firma", "required": True},
			],
		}
	]
}


def tratto(larghezza=300, altezza=100) -> str:
	from PIL import Image, ImageDraw

	immagine = Image.new("RGBA", (larghezza, altezza), (255, 255, 255, 0))
	ImageDraw.Draw(immagine).line((10, 80, 150, 20, 290, 70), fill=(20, 20, 20, 255), width=3)
	buffer = io.BytesIO()
	immagine.save(buffer, format="PNG")
	return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


class CompilazioniCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		consensi.assicura_tipi()
		utenti.sincronizza()
		for user, livello in ((DESK, "segreteria"), (SALES, "commerciale"), (OTHER, "commerciale")):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		self.giulia = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Giulia", "last_name": "Modulo"}
		).insert(ignore_permissions=True)
		# the salesperson works on Giulia; the other one does not
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"reference_type": "CRM Lead",
				"reference_name": self.giulia.name,
				"allocated_to": SALES,
				"description": "Giulia",
			}
		).insert(ignore_permissions=True)
		self.privacy = self.pubblica(PRIVACY, "Privacy")
		livelli.dimentica_cache()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	@staticmethod
	def pubblica(schema, titolo, **campi):
		modello = modelli.save_template(title=titolo, schema=json.dumps(schema), **campi)
		modelli.publish_template(modello["name"])
		return modello["name"]

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def firma(self, nome, risposte=None, firme=None, **altro):
		risposte = {"read": True, "marketing": False, "weight": "70,5"} if risposte is None else risposte
		return compilazioni.sign_form(
			nome, json.dumps(risposte), json.dumps({"sign": tratto()} if firme is None else firme), **altro
		)


class LaFirma(CompilazioniCase):
	def test_firmato_resta_com_era(self):
		self.come(DESK)
		modulo = compilazioni.start_form(self.giulia.name, self.privacy)
		self.assertEqual((modulo["docstatus"], modulo["version"]), (0, 1))
		firmato = self.firma(modulo["name"])
		self.assertEqual(firmato["docstatus"], 1)
		self.assertEqual(firmato["answers"], {"read": True, "marketing": False, "weight": 70.5})
		self.assertEqual(
			firmato["answers_hash"],
			compilazioni.impronta_risposte(firmato["schema_hash"], firmato["answers"]),
		)
		[firma] = firmato["signatures"]
		self.assertEqual(
			(firma["field"], firma["signer"], firma["level"], firma["method"]),
			("sign", "patient", "simple", "Drawn"),
		)
		self.assertEqual(firma["signer_name"], self.giulia.lead_name)
		self.assertTrue(firma["image"].startswith("/private/files/"))
		# signed, it is not changed nor thrown away
		with self.assertRaises(frappe.ValidationError):
			compilazioni.save_answers(modulo["name"], json.dumps({"weight": 80}))
		with self.assertRaises(frappe.ValidationError):
			compilazioni.discard_form(modulo["name"])

	def test_il_pdf_e_fatto_una_volta_e_si_prova(self):
		self.come(DESK)
		firmato = self.firma(compilazioni.start_form(self.giulia.name, self.privacy)["name"])
		self.assertTrue(firmato["pdf_file"].startswith("/private/files/"))
		self.assertIn("PDF/A-3b", firmato["pdf_conformance"])
		frappe.set_user("Administrator")
		contenuto = frappe.get_doc("File", {"file_url": firmato["pdf_file"]}).get_content(encodings=[])
		self.assertTrue(contenuto.startswith(b"%PDF"))
		self.assertEqual(hashlib.sha256(contenuto).hexdigest(), firmato["pdf_hash"])
		from crm.moduli import pdf

		doc = frappe.get_doc(compilazioni.MODULO, firmato["name"])
		self.assertTrue(pdf.genera_e_allega(doc)["skipped"])

	def test_manca_qualcosa_non_si_firma(self):
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		with self.assertRaises(frappe.ValidationError):
			self.firma(nome, {"read": True})
		with self.assertRaises(frappe.ValidationError):
			self.firma(nome, firme={})
		# a notice that has to be accepted is not answered by a no
		with self.assertRaises(frappe.ValidationError):
			self.firma(nome, {"read": False, "marketing": True})
		self.assertEqual(frappe.db.get_value(compilazioni.MODULO, nome, "docstatus"), 0)

	def test_la_firma_e_un_disegno(self):
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		for sbagliata in (
			"data:image/jpeg;base64,AAAA",
			"data:image/png;base64,non-base64!!",
			"data:image/png;base64," + base64.b64encode(b"GIF89a....").decode(),
		):
			with self.assertRaises(frappe.ValidationError):
				self.firma(nome, firme={"sign": sbagliata})

	def test_una_firma_avanzata_non_si_disegna(self):
		schema = json.loads(json.dumps(PRIVACY))
		schema["sections"][0]["fields"][-1]["level"] = "advanced"
		modello = self.pubblica(schema, "Consenso informato")
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, modello)["name"]
		with self.assertRaises(frappe.ValidationError):
			self.firma(nome)

	def test_una_bozza_si_salva_a_meta_e_si_butta(self):
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		salvate = compilazioni.save_answers(
			nome, json.dumps({"weight": "tanto", "read": True, "sign": tratto()})
		)
		# what converts is kept, what does not is said; a signature is not an answer
		self.assertEqual(salvate["answers"], {"read": True})
		self.assertEqual([p["code"] for p in salvate["problems"]], ["not_a_number"])
		compilazioni.discard_form(nome)
		self.assertFalse(frappe.db.exists(compilazioni.MODULO, nome))
		self.assertFalse(frappe.db.exists(traccia.REGISTRO, {"reference_name": nome}))


class IlRegistroDeiConsensi(CompilazioniCase):
	def test_i_consensi_vanno_nel_registro_con_le_parole_firmate(self):
		genitore = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Paola", "last_name": "Modulo"}
		).insert(ignore_permissions=True)
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		self.firma(nome, given_by=genitore.name)
		frappe.set_user("Administrator")
		versione = frappe.get_doc(
			modelli.VERSIONE, frappe.db.get_value(compilazioni.MODULO, nome, "template_version")
		)
		testi = {c["id"]: c for c in S.campi(json.loads(versione.schema))}
		righe = {
			r.consent_type: r
			for r in frappe.get_all(
				"CRM Consent",
				filters={"lead": self.giulia.name},
				fields=[
					"consent_type",
					"status",
					"text",
					"text_version",
					"source_doctype",
					"source_name",
					"channel",
					"given_by",
				],
			)
		}
		self.assertEqual(righe["privacy_notice"].status, "Given")
		self.assertEqual(righe["marketing"].status, "Refused")
		self.assertEqual(righe["marketing"].text, testi["marketing"]["text"])
		self.assertEqual(righe["marketing"].text_version, testi["marketing"]["text_version"])
		self.assertEqual(
			(righe["marketing"].source_doctype, righe["marketing"].source_name), (compilazioni.MODULO, nome)
		)
		self.assertEqual(righe["marketing"].channel, "At the desk")
		self.assertEqual(righe["marketing"].given_by, genitore.name)
		self.assertEqual(frappe.db.get_value("CRM Lead", self.giulia.name, "marketing_consent"), "Refused")


class LaTraccia(CompilazioniCase):
	def test_gli_eventi_in_catena(self):
		self.come(DESK)
		nome = self.firma(compilazioni.start_form(self.giulia.name, self.privacy)["name"])["name"]
		frappe.set_user("Administrator")
		eventi = [e.event for e in traccia.eventi(compilazioni.MODULO, nome)]
		self.assertEqual(eventi[:3], ["created", "signed", "pdf_generated"])
		self.assertEqual(eventi.count("consent_recorded"), 2)
		self.assertTrue(traccia.verifica_catena(compilazioni.MODULO, nome)["integra"])
		# changed behind its back, the chain says where
		secondo = traccia.eventi(compilazioni.MODULO, nome)[1]
		frappe.db.set_value(traccia.REGISTRO, secondo.name, "detail", "altered")
		esito = traccia.verifica_catena(compilazioni.MODULO, nome)
		self.assertEqual((esito["integra"], esito["rotto_a"]), (False, 1))

	def test_un_evento_non_si_tocca(self):
		self.come(DESK)
		nome = self.firma(compilazioni.start_form(self.giulia.name, self.privacy)["name"])["name"]
		frappe.set_user("Administrator")
		evento = frappe.get_doc(traccia.REGISTRO, traccia.eventi(compilazioni.MODULO, nome)[0].name)
		evento.detail = "rewritten"
		with self.assertRaises(frappe.ValidationError):
			evento.save(ignore_permissions=True)
		with self.assertRaises(frappe.LinkExistsError):
			frappe.delete_doc(traccia.REGISTRO, evento.name, ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": traccia.REGISTRO,
					"reference_doctype": compilazioni.MODULO,
					"reference_name": nome,
					"event": "signed",
				}
			).insert(ignore_permissions=True)


class ChiLiVede(CompilazioniCase):
	def test_seguono_la_persona(self):
		self.come(DESK)
		nome = self.firma(compilazioni.start_form(self.giulia.name, self.privacy)["name"])["name"]
		self.come(SALES)
		self.assertIn(nome, [f["name"] for f in compilazioni.get_person_forms(self.giulia.name)["forms"]])
		self.assertEqual(compilazioni.get_form(nome)["name"], nome)
		self.come(OTHER)
		with self.assertRaises(frappe.PermissionError):
			compilazioni.get_form(nome)
		self.assertNotIn(nome, frappe.get_list(compilazioni.MODULO, pluck="name"))

	def test_la_segreteria_non_legge_i_dati_sanitari(self):
		self.assertFalse(compilazioni.legge_dati_clinici(DESK))
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, self.privacy)["name"]
		frappe.db.set_value(compilazioni.MODULO, nome, "clinical", 1)
		with self.assertRaises(frappe.PermissionError):
			compilazioni.get_form(nome)
		self.assertNotIn(nome, frappe.get_list(compilazioni.MODULO, pluck="name"))
