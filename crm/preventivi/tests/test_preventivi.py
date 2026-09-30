# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Quotes on a site without the clinic: a beauty centre's treatments.

The therapist writes Anna's quote - a facial, then a laser treatment with a
discount - from the price list; the desk does not read the draft, and sales never
reads it. Proposed, it is frozen, its PDF is made and Anna's deal in the quotes
pipeline says "quote delivered"; it is no health data, so nothing goes in the
access log. The desk records it accepted, the deal is won; an appointment of the
facial takes its row at the price agreed, Anna came, it is done; every row done
or cancelled, the quote is completed. Anna reads it in her area. Declined, the deal
is lost with the reason, and a new version starts from it. The manager chooses the
pipeline and how long a quote holds.
"""

import json

import frappe
from frappe.utils import add_days, getdate

from crm.area.tests.test_area import DESK, MANAGER, OPERATORE, SALES, AreaCase
from crm.permissions import utenti
from crm.preventivi import api as preventivi
from crm.preventivi import area, documento, pipeline
from crm.preventivi import regole as R


class PreventiviCase(AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		pipeline.crea()
		self.viso = self.make_service("Pulizia viso di prova", [OPERATORE], default_price=60, currency="EUR")
		self.laser = self.make_service("Laser di prova", [OPERATORE], default_price=200, currency="EUR")

	def scrive(self, user=OPERATORE, **altro):
		self.come(user)
		return preventivi.save_quote(
			self.anna.name,
			json.dumps(
				{
					"title": "Trattamenti di ottobre",
					"items": [
						{"service": self.viso.name, "phase": 1, "rate": 60},
						{"service": self.laser.name, "phase": 2, "rate": 200, "discount": 10},
					],
					**altro,
				}
			),
		)

	def proponi(self, nome):
		self.come(OPERATORE)
		return preventivi.propose_quote(nome)

	def tipo_del_deal(self, deal):
		return frappe.db.get_value("CRM Deal Status", frappe.db.get_value("CRM Deal", deal, "status"), "type")


class IlPreventivo(PreventiviCase):
	def test_si_scrive_si_propone_e_la_segreteria_lo_accetta(self):
		fatto = self.scrive()
		self.assertEqual((fatto["status"], fatto["clinical"]), (R.BOZZA, 0))
		self.assertEqual(fatto["totals"], {"gross": 260, "discount": 20, "net": 240, "done": 0, "left": 240})
		self.assertEqual(fatto["items"][0]["description"], "Pulizia viso di prova")
		# without the clinic no tooth is offered, nor taken
		self.assertFalse(fatto["offers"].get("teeth"))
		# a draft is its author's
		for user in (DESK, SALES):
			self.come(user)
			self.assertEqual(preventivi.get_quotes(self.anna.name)["quotes"], [], user)
			with self.assertRaises(frappe.PermissionError):
				preventivi.get_quote(fatto["name"])
		proposto = self.proponi(fatto["name"])
		self.assertEqual(proposto["status"], R.PROPOSTO)
		self.assertTrue(proposto["quote_pdf"])
		self.assertEqual(getdate(proposto["valid_until"]), add_days(getdate(), R.GIORNI_VALIDITA))
		self.assertIn("Laser di prova", documento.html(frappe.get_doc(preventivi.DOCTYPE, fatto["name"])))
		deal = frappe.get_doc("CRM Deal", proposto["deal"])
		self.assertEqual(deal.pipeline, pipeline.quale())
		self.assertEqual(frappe.db.get_value("CRM Deal Status", deal.status, "position"), pipeline.CONSEGNATO)
		self.assertEqual(deal.expected_deal_value, 240)
		# proposed, it is not rewritten, nor thrown away
		doc = frappe.get_doc(preventivi.DOCTYPE, fatto["name"])
		doc.title = "Riscritto"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		# sales reads it and does not decide; the desk records it accepted
		self.come(SALES)
		self.assertFalse(preventivi.get_quote(fatto["name"])["can_decide"])
		with self.assertRaises(frappe.PermissionError):
			preventivi.accept_quote(fatto["name"])
		self.come(DESK)
		self.assertEqual(
			[q["name"] for q in preventivi.get_quotes(self.anna.name)["quotes"]], [fatto["name"]]
		)
		accettato = preventivi.accept_quote(fatto["name"], note="Firmato al banco")
		self.assertEqual(
			(accettato["status"], accettato["acceptance_note"]), (R.ACCETTATO, "Firmato al banco")
		)
		self.assertEqual(self.tipo_del_deal(accettato["deal"]), "Won")
		# no health data: nothing in the access log
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("View Log", {"reference_name": fatto["name"]}))
		# the lists follow the same rule
		self.come(SALES)
		self.assertEqual(frappe.get_list(preventivi.DOCTYPE, pluck="name"), [fatto["name"]])

	def test_rifiutato_il_deal_e_perso_e_si_riparte_da_una_nuova_versione(self):
		fatto = self.scrive()
		self.proponi(fatto["name"])
		self.come(DESK)
		rifiutato = preventivi.decline_quote(fatto["name"], reason="Pricing", note="Ci pensa")
		self.assertEqual(
			(rifiutato["status"], rifiutato["decline_reason"]), (R.RIFIUTATO, "Pricing, Ci pensa")
		)
		deal = frappe.get_doc("CRM Deal", rifiutato["deal"])
		self.assertEqual((self.tipo_del_deal(deal.name), deal.lost_reason), ("Lost", "Pricing"))
		self.come(OPERATORE)
		nuova = preventivi.copy_quote(fatto["name"])
		self.assertEqual(
			(nuova["status"], nuova["replaces"], len(nuova["items"])), (R.BOZZA, fatto["name"], 2)
		)
		# proposed and taken back to change it: a draft again, without the old PDF
		self.proponi(nuova["name"])
		self.come(OPERATORE)
		ritirata = preventivi.withdraw_quote(nuova["name"])
		self.assertEqual((ritirata["status"], ritirata["quote_pdf"]), (R.BOZZA, None))
		preventivi.delete_quote_draft(nuova["name"])
		self.assertFalse(frappe.db.exists(preventivi.DOCTYPE, nuova["name"]))

	def test_senza_un_dente_senza_la_clinica(self):
		self.come(OPERATORE)
		with self.assertRaises(frappe.ValidationError):
			preventivi.save_quote(
				self.anna.name,
				json.dumps({"title": "Col dente", "items": [{"service": self.viso.name, "tooth": "36"}]}),
			)

	def test_chi_non_scrive_preventivi_non_ne_scrive(self):
		self.come(SALES)
		self.assertTrue(preventivi.get_quotes(self.anna.name)["can_write"])
		frappe.set_user("Administrator")
		utenti.assegna_livelli(SALES, ["marketing"])
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			preventivi.save_quote(self.anna.name, json.dumps({"title": "Suo", "items": []}))


class LeSedute(PreventiviCase):
	def appuntamento(self, servizio, quando):
		frappe.set_user("Administrator")
		return self.make_appointment(
			servizio.name,
			quando,
			[OPERATORE],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": self.anna.name,
					"participant_name": "Anna Area",
					"status": "Booked",
				}
			],
		)

	def esito(self, appuntamento, stato):
		frappe.set_user("Administrator")
		doc = frappe.get_doc("CRM Appointment", appuntamento.name)
		doc.participants[0].status = stato
		doc.save()

	def test_gli_appuntamenti_fanno_il_preventivo(self):
		fatto = self.scrive()
		self.proponi(fatto["name"])
		self.come(DESK)
		preventivi.accept_quote(fatto["name"])
		# the laser at the price agreed, less the discount
		laser = self.appuntamento(self.laser, self.tomorrow(11))
		self.assertEqual(laser.total_amount, 180)
		viso = self.appuntamento(self.viso, self.tomorrow(9))
		self.come(OPERATORE)
		self.assertEqual(
			[(v["status"], v["appointment"]) for v in preventivi.get_quote(fatto["name"])["items"]],
			[(R.PRENOTATA, viso.name), (R.PRENOTATA, laser.name)],
		)
		# in her area Anna reads it, the rows booked
		self.invita()
		self.entra()
		[nell_area] = area.area_quotes(self.anna.name)["quotes"]
		self.assertEqual(nell_area["title"], "Trattamenti di ottobre")
		self.assertTrue(all(v["when"] for v in nell_area["items"]))
		# Anna came to both: the quote is completed
		self.esito(viso, "Attended")
		self.esito(laser, "Attended")
		self.come(OPERATORE)
		finito = preventivi.get_quote(fatto["name"])
		self.assertEqual(finito["status"], R.COMPLETATO)
		self.assertEqual(finito["totals"]["done"], 240)


class LeImpostazioni(PreventiviCase):
	def test_il_manager_sceglie_la_pipeline_e_la_validita(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			pipeline.get_settings()
		self.come(MANAGER)
		self.assertEqual(pipeline.get_settings()["quotes_pipeline"], pipeline.quale())
		pipeline.save_settings(quotes_pipeline=pipeline.quale(), valid_days=30)
		fatto = self.scrive()
		proposto = self.proponi(fatto["name"])
		self.assertEqual(getdate(proposto["valid_until"]), add_days(getdate(), 30))
		# without a pipeline, a quote moves no deal
		self.come(MANAGER)
		pipeline.save_settings(quotes_pipeline=None, valid_days=None)
		altro = self.scrive(title="Senza pipeline")
		self.assertIsNone(self.proponi(altro["name"])["deal"])
