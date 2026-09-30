# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Dental care plans (docs/gestionale-medico, phase 3).

The dentist writes Anna's chart, and a plan of two phases - two fillings, then an
implant with a discount - from the price list; the hygienist writes neither.
Proposed, the plan is frozen, its quote is a PDF and Anna's deal in the quotes
pipeline says "quote delivered"; the desk, which did not read the draft, records
it accepted and the deal is won. The appointment already booked for a filling
takes the first filling, a new one the second, the implant its own at the price
agreed; Anna came, it is done; a cancellation gives it back; every treatment done
or cancelled, the plan is completed. Declined, the deal is lost with the reason,
and a new version starts from it. A colleague reads a proposed plan with the
dossier, and every opening goes in the access log; sales reads nothing of it.
"""

import json

import frappe
from frappe.utils import add_days, getdate

from crm.clinica import cartella, cure, pipeline
from crm.clinica import cure_regole as R
from crm.clinica.tests.test_cartella import DESK, DOC1, DOC2, MANAGER, SALES
from crm.clinica.tests.test_dossier import DossierCase
from crm.tests.test_scheduling import SchedulingCase

DENTISTA, IGIENISTA = DOC1, DOC2


class CureCase(DossierCase, SchedulingCase):
	def setUp(self):
		SchedulingCase.setUp(self)
		DossierCase.setUp(self)
		self.disciplina(DENTISTA, "odontoiatra")
		self.disciplina(IGIENISTA, "igienista_dentale")
		frappe.set_user("Administrator")
		pipeline.crea_pipeline()
		self.otturazione = self.make_service(
			"Otturazione di prova", [DENTISTA], default_price=90, currency="EUR"
		)
		self.impianto = self.make_service("Impianto di prova", [DENTISTA], default_price=1200, currency="EUR")

	def tearDown(self):
		DossierCase.tearDown(self)
		SchedulingCase.tearDown(self)

	def piano(self, **altro):
		self.come(DENTISTA)
		return cure.save_care_plan(
			self.anna.name,
			json.dumps(
				{
					"title": "Piano di cura 2026",
					"items": [
						{
							"service": self.otturazione.name,
							"tooth": "36",
							"surfaces": "om",
							"phase": 1,
							"rate": 90,
						},
						{
							"service": self.otturazione.name,
							"tooth": "46",
							"surfaces": "O",
							"phase": 1,
							"rate": 90,
						},
						{
							"service": self.impianto.name,
							"tooth": "26",
							"phase": 2,
							"rate": 1200,
							"discount": 10,
						},
					],
					**altro,
				}
			),
		)

	def proponi(self, nome):
		self.come(DENTISTA)
		return cure.propose_care_plan(nome)

	def appuntamento(self, servizio, quando):
		frappe.set_user("Administrator")
		return self.make_appointment(
			servizio.name,
			quando,
			[DENTISTA],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": self.anna.name,
					"participant_name": "Anna Cartella",
					"status": "Booked",
				}
			],
		)

	def esito(self, appuntamento, stato):
		frappe.set_user("Administrator")
		doc = frappe.get_doc("CRM Appointment", appuntamento.name)
		doc.participants[0].status = stato
		doc.save()

	def voci(self, nome):
		self.come(DENTISTA)
		return [(v["tooth"], v["status"], v["appointment"]) for v in cure.get_care_plan(nome)["items"]]

	def tipo_del_deal(self, deal):
		return frappe.db.get_value("CRM Deal Status", frappe.db.get_value("CRM Deal", deal, "status"), "type")


class LoStatoDeiDenti(CureCase):
	def test_lo_scrive_il_dentista_lo_legge_il_collega_col_dossier(self):
		self.come(IGIENISTA)
		with self.assertRaises(frappe.PermissionError):
			cure.save_chart(
				self.anna.name, json.dumps([{"tooth": "36", "condition": R.CARIE, "surfaces": "O"}])
			)
		self.come(DENTISTA)
		fatto = cure.save_chart(
			self.anna.name,
			json.dumps(
				[
					{"tooth": "36", "condition": R.CARIE, "surfaces": "om"},
					{"tooth": "18", "condition": R.MANCANTE},
				]
			),
		)
		self.assertEqual(
			[(t["tooth"], t["condition"], t["surfaces"]) for t in fatto["teeth"]],
			[("18", R.MANCANTE, ""), ("36", R.CARIE, "MO")],
		)
		with self.assertRaises(frappe.ValidationError):
			cure.save_chart(
				self.anna.name,
				json.dumps(
					[
						{"tooth": "18", "condition": R.MANCANTE},
						{"tooth": "18", "condition": R.CARIE, "surfaces": "O"},
					]
				),
			)
		# the chart is clinical information: Anna is a patient
		self.assertTrue(frappe.db.exists("Clinic Patient", self.anna.name))
		# the hygienist knows there is one; with the dossier, reads it
		self.come(IGIENISTA)
		self.assertTrue(cure.get_dental(self.anna.name)["chart"]["hidden"])
		self.consenso()
		self.come(IGIENISTA)
		letta = cure.get_dental(self.anna.name)["chart"]
		self.assertEqual(len(letta["teeth"]), 2)
		self.assertFalse(letta["can_write"])


class IlPreventivo(CureCase):
	def test_si_scrive_si_propone_e_la_segreteria_lo_accetta(self):
		fatto = self.piano()
		self.assertEqual(fatto["status"], R.BOZZA)
		self.assertEqual(
			fatto["totals"], {"gross": 1380, "discount": 120, "net": 1260, "done": 0, "left": 1260}
		)
		self.assertEqual([v["surfaces"] for v in fatto["items"]], ["MO", "O", None])
		# the hygienist does not write plans; the desk does not read a draft
		self.come(IGIENISTA)
		with self.assertRaises(frappe.PermissionError):
			cure.save_care_plan(self.anna.name, json.dumps({"title": "Suo", "items": []}))
		self.come(DESK)
		self.assertEqual(cure.get_dental(self.anna.name)["plans"], [])
		with self.assertRaises(frappe.PermissionError):
			cure.get_care_plan(fatto["name"])
		proposto = self.proponi(fatto["name"])
		self.assertEqual(proposto["status"], R.PROPOSTO)
		self.assertTrue(proposto["quote_pdf"])
		self.assertEqual(getdate(proposto["valid_until"]), add_days(getdate(), cure.GIORNI_VALIDITA))
		deal = frappe.get_doc("CRM Deal", proposto["deal"])
		self.assertEqual(deal.pipeline, pipeline.impostazioni().quotes_pipeline)
		self.assertEqual(frappe.db.get_value("CRM Deal Status", deal.status, "position"), pipeline.CONSEGNATO)
		self.assertEqual(deal.expected_deal_value, 1260)
		# proposed, it is not rewritten
		doc = frappe.get_doc(cure.PIANO, fatto["name"])
		doc.title = "Riscritto"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		# the desk reads it now, and records it accepted
		self.come(DESK)
		self.assertEqual([p["name"] for p in cure.get_dental(self.anna.name)["plans"]], [fatto["name"]])
		self.assertTrue(cure.get_care_plan(fatto["name"])["can_decide"])
		accettato = cure.accept_care_plan(fatto["name"], note="Firmato al banco")
		self.assertEqual(
			(accettato["status"], accettato["acceptance_note"]), (R.ACCETTATO, "Firmato al banco")
		)
		self.assertEqual(self.tipo_del_deal(accettato["deal"]), "Won")

	def test_rifiutato_il_deal_e_perso_e_si_riparte_da_una_nuova_versione(self):
		fatto = self.piano()
		self.proponi(fatto["name"])
		self.come(DESK)
		rifiutato = cure.decline_care_plan(fatto["name"], reason="Pricing", note="Ci vuole pensare")
		self.assertEqual(rifiutato["status"], R.RIFIUTATO)
		deal = frappe.get_doc("CRM Deal", rifiutato["deal"])
		self.assertEqual((self.tipo_del_deal(deal.name), deal.lost_reason), ("Lost", "Pricing"))
		self.come(DENTISTA)
		nuova = cure.copy_care_plan(fatto["name"])
		self.assertEqual(
			(nuova["status"], nuova["replaces"], len(nuova["items"])), (R.BOZZA, fatto["name"], 3)
		)
		# proposed and taken back to change it: a draft again, without the old quote
		self.proponi(nuova["name"])
		self.come(DENTISTA)
		ritirata = cure.withdraw_care_plan(nuova["name"])
		self.assertEqual((ritirata["status"], ritirata["quote_pdf"]), (R.BOZZA, None))


class LePrestazioni(CureCase):
	def test_gli_appuntamenti_fanno_il_piano(self):
		fatto = self.piano()
		self.proponi(fatto["name"])
		# booked before the acceptance: it takes the first filling when accepted
		prima = self.appuntamento(self.otturazione, self.tomorrow(9))
		self.assertEqual(frappe.db.get_value("CRM Appointment", prima.name, "total_amount"), 90)
		self.come(DESK)
		cure.accept_care_plan(fatto["name"])
		# a new one takes the next, the implant its own at the price agreed
		seconda = self.appuntamento(self.otturazione, self.tomorrow(11))
		impianto = self.appuntamento(self.impianto, self.tomorrow(14))
		self.assertEqual(impianto.total_amount, 1080)
		self.assertEqual(
			self.voci(fatto["name"]),
			[
				("36", R.PRENOTATA, prima.name),
				("46", R.PRENOTATA, seconda.name),
				("26", R.PRENOTATA, impianto.name),
			],
		)
		# Anna came: done; a cancellation gives the treatment back
		self.esito(prima, "Attended")
		self.esito(seconda, "Cancelled")
		self.assertEqual(self.voci(fatto["name"])[:2], [("36", R.FATTA, prima.name), ("46", R.DA_FARE, None)])
		# the dentist cancels the second filling; the implant done, the plan is completed
		self.come(DENTISTA)
		voce = cure.get_care_plan(fatto["name"])["items"][1]["name"]
		cure.mark_treatment(fatto["name"], voce, R.ANNULLATA)
		self.esito(impianto, "Attended")
		self.come(DENTISTA)
		finito = cure.get_care_plan(fatto["name"])
		self.assertEqual(finito["status"], R.COMPLETATO)
		self.assertEqual(
			finito["totals"], {"gross": 1290, "discount": 120, "net": 1170, "done": 1170, "left": 0}
		)
		# in the person's area: the plan and its treatments
		[nell_area] = cure.della_persona(self.anna.name)
		self.assertEqual(
			[(v["tooth"], v["status"]) for v in nell_area["items"]], [("36", R.FATTA), ("26", R.FATTA)]
		)

	def test_un_appuntamento_eliminato_rende_la_prestazione(self):
		fatto = self.piano()
		self.proponi(fatto["name"])
		self.come(DESK)
		cure.accept_care_plan(fatto["name"])
		appuntamento = self.appuntamento(self.otturazione, self.tomorrow(9))
		frappe.set_user("Administrator")
		frappe.delete_doc("CRM Appointment", appuntamento.name)
		self.assertEqual(self.voci(fatto["name"])[0], ("36", R.DA_FARE, None))


class ChiLegge(CureCase):
	def test_il_collega_col_dossier_e_il_registro_degli_accessi(self):
		fatto = self.piano()
		self.proponi(fatto["name"])
		self.come(IGIENISTA)
		with self.assertRaises(frappe.PermissionError):
			cure.get_care_plan(fatto["name"])
		self.consenso()
		self.come(IGIENISTA)
		letto = cure.get_care_plan(fatto["name"])
		self.assertEqual(letto["title"], "Piano di cura 2026")
		self.assertFalse(letto["can_decide"])
		self.come(MANAGER)
		registro = cartella.access_log(self.anna.name)
		self.assertIn(("care plan", IGIENISTA), [(riga["kind"], riga["viewed_by"]) for riga in registro])
		# sales reads nothing of the teeth
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			cure.get_dental(self.anna.name)
