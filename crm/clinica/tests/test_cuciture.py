# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The first seam, from marketing to the centre: becoming a patient closes the deal.

Switching the clinic on makes the two pipelines of a medical centre. A booking moves
an open new-patients deal to "appointment booked"; becoming a patient wins it, and
the automations hear "Became Patient". The patients found in last year's data close
nothing and start nothing.
"""

from unittest.mock import patch

import frappe
from frappe.utils import add_days, nowdate

from crm.clinica import paziente, pipeline, regole
from crm.clinica.tests.test_paziente import ClinicCase
from crm.dashboard import registry
from crm.dashboard.context import Context
from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_first_stage


class CucitureCase(ClinicCase):
	def richiesta(self, persona, stadio=None):
		"""A new-patients deal, as a form or a lead ad opens it."""
		conf = pipeline.impostazioni()
		doc = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"lead": persona.name,
				"status": stadio or get_first_stage(conf.new_patients_pipeline),
			}
		)
		doc.flags.ignore_mandatory = True
		doc.flags.from_inquiry = True
		return doc.insert(ignore_permissions=True)

	def stato(self, deal):
		return frappe.db.get_value("CRM Deal", deal.name, "status")

	def tipo(self, deal):
		return frappe.db.get_value("CRM Deal Status", self.stato(deal), "type")


class LePipeline(CucitureCase):
	def test_accesa_la_clinica_nascono_le_due(self):
		conf = pipeline.impostazioni()
		self.assertTrue(frappe.db.exists("CRM Pipeline", conf.new_patients_pipeline))
		self.assertTrue(frappe.db.exists("CRM Pipeline", conf.quotes_pipeline))
		self.assertEqual(
			frappe.db.get_value("CRM Deal Status", conf.booked_stage, "pipeline"), conf.new_patients_pipeline
		)
		tipi = frappe.get_all(
			"CRM Deal Status", filters={"pipeline": conf.new_patients_pipeline}, pluck="type"
		)
		self.assertIn("Won", tipi)
		self.assertIn("Lost", tipi)

	def test_una_volta_sola(self):
		prima = frappe.db.count("CRM Pipeline")
		conf = pipeline.impostazioni()
		self.assertEqual(pipeline.crea_pipeline(), conf)
		self.accendi(True)
		self.assertEqual(frappe.db.count("CRM Pipeline"), prima)

	def test_le_impostazioni_tengono_insieme_pipeline_e_stadio(self):
		conf = pipeline.impostazioni()
		doc = frappe.get_single(pipeline.IMPOSTAZIONI)
		doc.booked_stage = get_first_stage(conf.quotes_pipeline)
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)


class LaPrenotazione(CucitureCase):
	def test_sposta_la_richiesta_su_appuntamento_fissato(self):
		deal = self.richiesta(self.mario)
		self.appuntamento(self.mario, self.tomorrow(10))
		self.assertEqual(self.stato(deal), pipeline.impostazioni().booked_stage)

	def test_una_trattativa_di_un_altra_pipeline_resta_dove_e(self):
		conf = pipeline.impostazioni()
		preventivo = self.richiesta(self.mario, get_first_stage(conf.quotes_pipeline))
		self.appuntamento(self.mario, self.tomorrow(10))
		self.assertEqual(self.stato(preventivo), get_first_stage(conf.quotes_pipeline))

	def test_con_la_clinica_spenta_non_sposta(self):
		deal = self.richiesta(self.mario)
		primo = self.stato(deal)
		self.accendi(False)
		self.appuntamento(self.mario, self.tomorrow(10))
		self.assertEqual(self.stato(deal), primo)


class DiventarePaziente(CucitureCase):
	def test_vince_la_richiesta(self):
		deal = self.richiesta(self.mario)
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		self.assertTrue(paziente.e_paziente(self.mario.name))
		self.assertEqual(self.tipo(deal), "Won")
		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "closed_date").isoformat(), nowdate())

	def test_le_automazioni_lo_sentono(self):
		with patch("crm.automation.engine.process_event") as evento:
			paziente.assicura_paziente(self.mario.name, regole.A_MANO)
		chiamata = evento.call_args
		self.assertEqual(chiamata.args[0], pipeline.EVENTO)
		self.assertEqual(chiamata.args[1].name, self.mario.name)
		self.assertEqual(chiamata.args[2], {"rule": regole.A_MANO.valore})

	def test_il_trigger_c_e_dove_la_clinica_e_accesa(self):
		from crm.automation.engine import trigger_offerti

		self.assertIn(pipeline.TRIGGER, trigger_offerti())
		self.accendi(False)
		self.assertNotIn(pipeline.TRIGGER, trigger_offerti())

	def test_i_pazienti_di_prima_non_chiudono_niente(self):
		self.accendi(False)
		deal = self.richiesta(self.mario)
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		with patch("crm.automation.engine.process_event") as evento:
			# switching it on looks for the patients already there
			self.accendi(True)
			paziente.recupera()
		self.assertTrue(paziente.e_paziente(self.mario.name))
		self.assertNotEqual(self.tipo(deal), "Won")
		evento.assert_not_called()

	def test_un_deal_che_non_si_salva_non_ferma_il_paziente(self):
		self.richiesta(self.mario)
		with patch("crm.clinica.pipeline.vinci", side_effect=frappe.ValidationError("no")):
			paziente.assicura_paziente(self.mario.name, regole.A_MANO)
		self.assertTrue(paziente.e_paziente(self.mario.name))


class IlCruscotto(CucitureCase):
	def risposta(self, widget_id):
		widget = registry.get(widget_id)
		self.assertIsNotNone(widget, widget_id)
		ctx = Context.build(
			add_days(nowdate(), -7),
			nowdate(),
			scope=widget.scope,
			config=widget.clean_config({}),
		)
		return widget.fn(ctx)

	def test_i_nuovi_pazienti(self):
		paziente.assicura_paziente(self.mario.name, regole.A_MANO)
		self.assertGreaterEqual(self.risposta("new_patients")["value"], 1)

	def test_il_costo_di_un_nuovo_paziente(self):
		frappe.db.set_value("CRM Lead", self.mario.name, "facebook_ad_id", "ad-1")
		paziente.assicura_paziente(self.mario.name, regole.A_MANO)
		frappe.get_doc(
			{
				"doctype": "Facebook Ad Insight",
				"ad_id": "ad-1",
				"date": nowdate(),
				"spend": 120,
				"currency": "EUR",
			}
		).insert(ignore_permissions=True, ignore_mandatory=True, ignore_links=True)
		from crm.clinica.widgets import patients_from_ads

		self.assertEqual(
			patients_from_ads(Context.build(add_days(nowdate(), -7), nowdate(), scope="site", config={})),
			1,
		)


class LAccettazione(CucitureCase):
	"""Rule 2: the desk checks somebody in, and they are a patient from that moment."""

	def test_chi_arriva_al_banco_e_un_paziente(self):
		from crm.scheduling import esiti

		incontro = self.appuntamento(self.mario, self.tomorrow(10))
		riga = incontro.participants[0].name
		esiti.segna(incontro.name, riga, "Arrived")
		scheda = self.scheda(self.mario)
		self.assertEqual(scheda.rule, regole.ACCETTAZIONE.valore)
		self.assertEqual(
			scheda.patient_since,
			frappe.db.get_value("CRM Appointment Participant", riga, "arrived_at"),
		)

	def test_la_visita_chiude_l_appuntamento(self):
		incontro = self.appuntamento(self.mario, self.ieri())
		frappe.get_doc(
			{
				"doctype": "Clinic Record",
				"lead": self.mario.name,
				"kind": "Visit",
				"content": "<p>Controllo.</p>",
				"appointment": incontro.name,
				"practitioner": self.doctor,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("CRM Appointment", incontro.name, "status"), "Completed")
		self.assertEqual(
			frappe.db.get_value("CRM Appointment Participant", incontro.participants[0].name, "status"),
			"Attended",
		)
		self.assertEqual(self.scheda(self.mario).rule, regole.INFORMAZIONE_MEDICA.valore)
