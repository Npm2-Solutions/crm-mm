# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A visit on the specialty's clinical sheet, its report, and the patient's summary.

A clinical sheet is the CRM's sheet with the mark of health data: the
practitioner writes it during a visit, in the record, never among the forms. One
without the mark is written at the desk, among the forms. Signing the visit checks the sheet
as a form is checked, freezes it with its hash, and makes the report once. The
answers that fill a line of the summary (allergies, medications, weight...) are
proposed, from the sheet or from a signed clinical form; a practitioner confirms
or discards them, or writes a line by hand. The summary is the care team's.
"""

import hashlib
import json

import frappe

from crm.clinica import cartella, sintesi
from crm.clinica.tests.test_cartella import DESK, DOC1, DOC2, RecordCase
from crm.moduli import compilazioni, modelli
from crm.moduli.tests.test_compilazioni import tratto

VISITA = {
	"sections": [
		{
			"id": "anamnesi",
			"title": "Anamnesi",
			"fields": [
				{
					"id": "allergie",
					"type": "text",
					"label": "Allergie",
					"required": True,
					"summary": "allergies",
				},
				{"id": "peso", "type": "number", "label": "Peso", "unit": "kg", "summary": "weight"},
				{"id": "altezza", "type": "number", "label": "Altezza", "unit": "cm", "summary": "height"},
				{"id": "esame", "type": "text", "label": "Esame obiettivo", "multiline": True},
			],
		}
	]
}

ANAMNESI_MODULO = {
	"sections": [
		{
			"id": "storia",
			"title": "Storia",
			"fields": [
				{"id": "farmaci", "type": "text", "label": "Farmaci", "summary": "medications"},
				{"id": "firma", "type": "signature", "label": "Firma", "required": True},
			],
		}
	]
}


class SchedeCase(RecordCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.scheda = self.pubblica(VISITA, "Visita nutrizionale", use=modelli.SCHEDA, clinical=1)

	@staticmethod
	def pubblica(schema, titolo, **campi):
		modello = modelli.save_template(title=titolo, schema=json.dumps(schema), **campi)
		modelli.publish_template(modello["name"])
		return modello["name"]

	def visita(self, risposte=None, user=DOC1, firma=True):
		self.come(user)
		riga = cartella.start_sheet(self.anna.name, self.scheda)
		return cartella.save_record(
			self.anna.name,
			name=riga["name"],
			content="<p>Da rivedere tra un mese.</p>",
			answers=json.dumps(
				{"allergie": "Nichel", "peso": "64,5", "altezza": "170", "esame": "Nella norma"}
				if risposte is None
				else risposte
			),
			sign=1 if firma else 0,
		)


class LaScheda(SchedeCase):
	def test_una_scheda_clinica_si_scrive_in_cartella_e_non_fra_i_moduli(self):
		frappe.set_user("Administrator")
		modello = frappe.get_doc("CRM Form Template", self.scheda)
		self.assertEqual((modello.use, modello.clinical), (modelli.SCHEDA, 1))
		self.come(DOC1)
		self.assertNotIn(
			self.scheda, [t["name"] for t in compilazioni.get_person_forms(self.anna.name)["templates"]]
		)
		with self.assertRaises(frappe.ValidationError):
			compilazioni.start_form(self.anna.name, self.scheda)
		self.assertIn(self.scheda, [s["name"] for s in cartella.get_record(self.anna.name)["sheets"]])

	def test_una_scheda_senza_il_marchio_e_fra_i_moduli(self):
		frappe.set_user("Administrator")
		trattamento = self.pubblica(
			{
				"sections": [
					{"id": "s", "title": "S", "fields": [{"id": "zona", "type": "text", "label": "Zona"}]}
				]
			},
			"Scheda trattamento",
			use=modelli.SCHEDA,
		)
		self.come(DOC1)
		self.assertIn(
			trattamento, [t["name"] for t in compilazioni.get_person_forms(self.anna.name)["templates"]]
		)
		self.assertNotIn(trattamento, [s["name"] for s in cartella.get_record(self.anna.name)["sheets"]])
		with self.assertRaises(frappe.ValidationError):
			cartella.start_sheet(self.anna.name, trattamento)

	def test_le_schede_cliniche_di_prima_sono_schede_col_marchio(self):
		from crm.patches.v1_0 import sheets_are_the_crms

		frappe.set_user("Administrator")
		versione = frappe.db.get_value("CRM Form Template", self.scheda, "current_version")
		frappe.db.set_value("CRM Form Template", self.scheda, "use", "Clinical sheet")
		frappe.db.set_value("CRM Form Template Version", versione, "use", "Clinical sheet")
		sheets_are_the_crms.execute()
		self.assertEqual(
			frappe.db.get_value("CRM Form Template", self.scheda, ["use", "clinical"]), (modelli.SCHEDA, 1)
		)
		self.assertEqual(frappe.db.get_value("CRM Form Template Version", versione, "use"), modelli.SCHEDA)

	def test_firmata_si_chiude_con_il_referto(self):
		firmata = self.visita()
		self.assertEqual(firmata["docstatus"], 1)
		self.assertEqual(
			firmata["answers"], {"allergie": "Nichel", "peso": 64.5, "altezza": 170, "esame": "Nella norma"}
		)
		versione = frappe.get_doc(
			modelli.VERSIONE, frappe.get_doc("CRM Form Template", self.scheda).current_version
		)
		self.assertEqual(
			firmata["answers_hash"], compilazioni.impronta_risposte(versione.schema_hash, firmata["answers"])
		)
		frappe.set_user("Administrator")
		pdf = frappe.get_doc("File", {"file_url": firmata["pdf_file"]}).get_content(encodings=[])
		self.assertTrue(pdf.startswith(b"%PDF"))
		self.assertEqual(hashlib.sha256(pdf).hexdigest(), firmata["pdf_hash"])
		# the report is the report, not one more attachment of the visit
		self.assertNotIn(firmata["pdf_file"], [a.file_url for a in firmata["attachments"]])

	def test_il_referto_e_sigillato_dal_centro(self):
		from crm.moduli import sigillo
		from crm.moduli.tests.test_sigillo import installa_sigillo

		installa_sigillo()
		self.addCleanup(frappe.clear_document_cache, sigillo.IMPOSTAZIONI, sigillo.IMPOSTAZIONI)
		firmata = self.visita()
		frappe.set_user("Administrator")
		pdf = frappe.get_doc("File", {"file_url": firmata["pdf_file"]}).get_content(encodings=[])
		# the fingerprint the record keeps is the sealed file's
		self.assertEqual(hashlib.sha256(pdf).hexdigest(), firmata["pdf_hash"])
		[firma] = sigillo.verifica(pdf)
		self.assertEqual((firma["intact"], firma["covers_all"]), (True, True))
		self.assertEqual(
			frappe.db.get_value("Clinic Record", firmata["name"], "pdf_conformance"),
			"PDF/A-3b (structure verified), sealed by the centre",
		)

	def test_il_referto_scrive_testo(self):
		from crm.clinica import referto
		from crm.moduli.tests.test_pdf_sicuro import TRAPPOLA, allegati

		self.come(DOC1)
		riga = cartella.start_sheet(self.anna.name, self.scheda)
		firmata = cartella.save_record(
			self.anna.name,
			name=riga["name"],
			content="Controllo tra un mese.\nPortare gli esami.",
			answers=json.dumps({"allergie": "Nichel", "esame": TRAPPOLA}),
			sign=1,
		)
		frappe.set_user("Administrator")
		contenuto = frappe.get_doc("File", {"file_url": firmata["pdf_file"]}).get_content(encodings=[])
		self.assertEqual(allegati(contenuto), [])
		doc = frappe.get_doc("Clinic Record", firmata["name"])
		pagina = referto.html(doc, frappe.get_doc(modelli.VERSIONE, doc.template_version))
		self.assertNotIn('<a rel="attachment"', pagina)
		self.assertIn("&lt;a rel=", pagina)
		# notes written as text keep their lines
		self.assertIn("Controllo tra un mese.\nPortare gli esami.", pagina)

	def test_una_scheda_incompleta_non_si_firma(self):
		with self.assertRaises(frappe.ValidationError):
			self.visita({"peso": "64"})
		self.come(DOC1)
		bozza = cartella.save_record(
			self.anna.name,
			name=cartella.start_sheet(self.anna.name, self.scheda)["name"],
			answers=json.dumps({"peso": "tanto", "allergie": "Nessuna"}),
		)
		# a draft keeps what converts
		self.assertEqual(bozza["answers"], {"allergie": "Nessuna"})
		self.assertEqual(bozza["docstatus"], 0)


class LaSintesi(SchedeCase):
	def test_la_scheda_propone_e_il_medico_conferma(self):
		self.visita()
		self.come(DOC1)
		sintesi_ = sintesi.get_summary(self.anna.name)
		proposte = {p["key"]: p for p in sintesi_["proposals"]}
		self.assertEqual(set(proposte), {"allergies", "weight", "height"})
		self.assertEqual(proposte["weight"]["value"], "64.5 kg")
		# nothing in the summary until somebody confirms it
		self.assertFalse(any(riga.get("value") for riga in sintesi_["lines"]))
		sintesi.confirm_value(proposte["allergies"]["name"])
		sintesi.confirm_value(proposte["weight"]["name"], value="64 kg")
		sintesi.discard_value(proposte["height"]["name"])
		righe = {riga["key"]: riga for riga in sintesi.get_summary(self.anna.name)["lines"]}
		self.assertEqual(righe["allergies"]["value"], "Nichel")
		self.assertEqual(righe["weight"]["value"], "64 kg")
		self.assertIsNone(righe["height"].get("value"))
		self.assertEqual(sintesi.get_summary(self.anna.name)["proposals"], [])
		# decided once
		with self.assertRaises(frappe.ValidationError):
			sintesi.confirm_value(proposte["height"]["name"])

	def test_a_mano_e_l_ultimo_confermato(self):
		self.come(DOC1)
		sintesi.set_value(self.anna.name, "medications", "Nessuno")
		sintesi.set_value(self.anna.name, "medications", "Levotiroxina 50")
		righe = {riga["key"]: riga for riga in sintesi.get_summary(self.anna.name)["lines"]}
		self.assertEqual(righe["medications"]["value"], "Levotiroxina 50")
		with self.assertRaises(frappe.ValidationError):
			sintesi.set_value(self.anna.name, "hobbies", "Tennis")

	def test_anche_un_modulo_clinico_firmato_propone(self):
		frappe.set_user("Administrator")
		modulo = self.pubblica(ANAMNESI_MODULO, "Anamnesi del paziente", clinical=1)
		self.come(DOC1)
		nome = compilazioni.start_form(self.anna.name, modulo)["name"]
		compilazioni.sign_form(nome, json.dumps({"farmaci": "Ramipril"}), json.dumps({"firma": tratto()}))
		[proposta] = sintesi.get_summary(self.anna.name)["proposals"]
		self.assertEqual(
			(proposta["key"], proposta["value"], proposta["source_name"]), ("medications", "Ramipril", nome)
		)

	def test_la_segreteria_non_vede_la_sintesi(self):
		self.visita()
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			sintesi.get_summary(self.anna.name)
		# not even as a list: the desk has no role on the summary at all
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list(sintesi.DOCTYPE, pluck="name")
		with self.assertRaises(frappe.PermissionError):
			sintesi.set_value(self.anna.name, "allergies", "Nichel")
		# another practitioner reads it; deciding is for whoever writes the record
		self.come(DOC2)
		self.assertTrue(sintesi.get_summary(self.anna.name)["proposals"])
