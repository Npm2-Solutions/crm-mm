# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinical sheets DottorCloud ships: drafts of the centre's where the clinic
is on, in the centre's language, never published by themselves, never written
again once the centre touched them; to start from in the builder; and a score
on a clinical sheet followed over time beside the forms'."""

import json

import frappe
from frappe.utils import add_days, now_datetime

from crm import lingue
from crm.clinica import cartella, schede_pronte
from crm.clinica.tests.test_cartella import DESK, DIRECTOR, DOC1, RecordCase
from crm.moduli import andamenti, modelli

CHIAVI = (
	"physio_assessment",
	"physio_followup",
	"nutrition_first",
	"nutrition_followup",
	"dental_first",
	"general_history",
)


class LeSchedePronte(RecordCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		frappe.db.set_default(schede_pronte.CARICATE, None)
		frappe.db.set_default(schede_pronte.TENUTE, None)
		frappe.db.set_default(lingue.SCELTA, "it")

	def modello(self, chiave):
		tenute = json.loads(frappe.db.get_default(schede_pronte.TENUTE) or "{}")
		return frappe.get_doc(modelli.MODELLO, tenute[chiave]["name"])

	def test_bozze_del_centro_nella_sua_lingua(self):
		fatto = schede_pronte.carica_schede()
		self.assertEqual(fatto["created"] + fatto["kept"], len(CHIAVI))
		fisio = self.modello("physio_assessment")
		self.assertEqual(
			(fisio.title, fisio.use, fisio.clinical, fisio.specialty),
			("Valutazione fisioterapica", modelli.SCHEDA, 1, "Fisioterapia"),
		)
		# a draft: nobody fills it before the centre publishes it
		self.assertFalse(fisio.current_version)
		self.assertIn("body_chart", fisio.schema)
		# the same file and language: nothing to do
		self.assertIsNone(schede_pronte.carica_schede())

	def test_segue_la_lingua_finche_nessuno_la_tocca(self):
		schede_pronte.carica_schede()
		cambiata = self.modello("nutrition_first")
		schema = json.loads(cambiata.schema)
		schema["sections"][0]["title"] = "Il nostro motivo"
		cambiata.schema = json.dumps(schema)
		cambiata.save()
		pubblicata = self.modello("dental_first")
		modelli.publish_template(pubblicata.name)
		cancellata = self.modello("general_history")
		cancellata.delete()

		frappe.db.set_default(lingue.SCELTA, "en")
		fatto = schede_pronte.carica_schede()
		self.assertEqual(self.modello("physio_assessment").title, "Physiotherapy assessment")
		self.assertEqual((fatto["updated"], fatto["kept"]), (3, 2))
		# changed, published, deleted: the centre's
		self.assertEqual(self.modello("nutrition_first").title, "Prima visita nutrizionale")
		self.assertEqual(self.modello("dental_first").title, "Prima visita odontoiatrica")
		self.assertFalse(frappe.db.exists(modelli.MODELLO, cancellata.name))

	def test_un_modello_del_centro_con_lo_stesso_nome_resta_solo(self):
		modelli.save_template(title="Anamnesi generale", schema=json.dumps({"sections": []}))
		schede_pronte.carica_schede()
		self.assertEqual(frappe.db.count(modelli.MODELLO, {"title": "Anamnesi generale"}), 1)

	def test_senza_clinica_niente(self):
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [])
		piano.save()
		self.assertIsNone(schede_pronte.carica_schede(forza=True))
		self.assertEqual(schede_pronte.partenze(), [])

	def test_si_parte_da_una_scheda(self):
		self.come(DIRECTOR)
		partenze = {p["key"]: p for p in modelli.get_starters()}
		fisio = partenze["clinic.physio_assessment"]
		self.assertEqual(
			(fisio["use"], fisio["clinical"], fisio["title"]), ("Sheet", 1, "Valutazione fisioterapica")
		)
		# who does not build templates is offered none
		self.come(DESK)
		self.assertEqual(modelli.get_starters(), [])


class IPunteggiDelleVisite(RecordCase):
	def test_una_scheda_con_un_punteggio_nel_tempo(self):
		frappe.set_user("Administrator")
		scheda = next(s for s in schede_pronte.nella_lingua_del_centro() if s["key"] == "physio_followup")
		modello = modelli.save_template(
			title=scheda["title"],
			schema=json.dumps(scheda["schema"]),
			use=modelli.SCHEDA,
			clinical=1,
		)
		modelli.publish_template(modello["name"])
		chiavi = ("f_walk", "f_sit", "f_stand", "f_sleep", "f_lift", "f_dress", "f_work", "f_leisure")
		for valore, giorni in ((5, 30), (2, 2)):
			self.come(DOC1)
			riga = cartella.start_sheet(self.anna.name, modello["name"])
			cartella.save_record(
				self.anna.name,
				name=riga["name"],
				answers=json.dumps({**dict.fromkeys(chiavi, valore), "done": "Esercizi"}),
				record_date=str(add_days(now_datetime(), -giorni)),
				sign=1,
			)
		self.come(DOC1)
		[serie] = andamenti.get_trends(self.anna.name)
		self.assertEqual([p["value"] for p in serie["points"]], [40, 16])
		self.assertEqual({p["kind"] for p in serie["points"]}, {"visit"})
		# the front desk knows a visit happened, never what it said
		self.come(DESK)
		self.assertEqual(andamenti.get_trends(self.anna.name), [])
