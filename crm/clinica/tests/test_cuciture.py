# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The first seam, from marketing to the centre: becoming a patient closes the deal.

The pipelines are the CRM's (`crm.clienti`, `crm.preventivi`): switching the clinic
on makes them, the new clients one in the clinic's words. A booking moves an open
new-patients deal to "appointment booked"; becoming a patient makes a client of
the centre from the same moment, wins it, and the automations hear "Became
Client" - "Became Patient" in the clinic's words. The patients found in last
year's data close nothing and start nothing.
"""

from unittest.mock import patch

import frappe
from frappe.utils import add_days, nowdate

from crm.clienti import cliente
from crm.clienti import pipeline as clienti
from crm.clinica import paziente, pipeline, regole
from crm.clinica.tests.test_paziente import ClinicCase
from crm.dashboard import registry
from crm.dashboard.context import Context
from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_first_stage
from crm.preventivi import pipeline as preventivi


class CucitureCase(ClinicCase):
	def richiesta(self, persona, stadio=None):
		"""A new-patients deal, as a form or a lead ad opens it."""
		doc = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"lead": persona.name,
				"status": stadio or get_first_stage(clienti.quale()),
			}
		)
		doc.flags.ignore_mandatory = True
		doc.flags.from_inquiry = True
		return doc.insert(ignore_permissions=True)

	def stato(self, deal):
		return frappe.db.get_value("CRM Deal", deal.name, "status")

	def tipo(self, deal):
		return frappe.db.get_value("CRM Deal Status", self.stato(deal), "type")

	@staticmethod
	def annunci(evento):
		return [chiamata for chiamata in evento.call_args_list if chiamata.args[0] == cliente.EVENTO]


class LePipeline(CucitureCase):
	def test_accesa_la_clinica_nascono_le_due(self):
		conf = clienti.impostazioni()
		self.assertTrue(frappe.db.exists("CRM Pipeline", conf.new_clients_pipeline))
		self.assertTrue(frappe.db.exists("CRM Pipeline", preventivi.quale()))
		tipi = frappe.get_all(
			"CRM Deal Status", filters={"pipeline": conf.new_clients_pipeline}, pluck="type"
		)
		self.assertIn("Won", tipi)
		self.assertIn("Lost", tipi)

	def test_una_volta_sola(self):
		prima = frappe.db.count("CRM Pipeline")
		conf = clienti.impostazioni()
		self.assertEqual(pipeline.crea_pipeline(), conf)
		self.accendi(True)
		self.assertEqual(frappe.db.count("CRM Pipeline"), prima)

	def test_nelle_parole_della_clinica(self):
		"""The CRM's new clients pipeline, made where the clinic is on, is named as
		the new patients' one; without the clinic, as the CRM's."""
		self.assertIn(clienti._definizione()[0], {nomi[0] for nomi in pipeline.NUOVI_PAZIENTI.values()})
		self.accendi(False)
		self.assertIn(clienti._definizione()[0], {nomi[0] for nomi in clienti.NUOVI_CLIENTI.values()})


class LaPrenotazione(CucitureCase):
	def test_sposta_la_richiesta_su_appuntamento_fissato(self):
		deal = self.richiesta(self.mario)
		self.appuntamento(self.mario, self.tomorrow(10))
		self.assertEqual(self.stato(deal), clienti.impostazioni().booked_stage)

	def test_una_trattativa_di_un_altra_pipeline_resta_dove_e(self):
		preventivo = self.richiesta(self.mario, get_first_stage(preventivi.quale()))
		self.appuntamento(self.mario, self.tomorrow(10))
		self.assertEqual(self.stato(preventivo), get_first_stage(preventivi.quale()))

	def test_la_sposta_il_crm_anche_a_clinica_spenta(self):
		deal = self.richiesta(self.mario)
		self.accendi(False)
		self.appuntamento(self.mario, self.tomorrow(10))
		self.assertEqual(self.stato(deal), clienti.impostazioni().booked_stage)


class DiventarePaziente(CucitureCase):
	def test_vince_la_richiesta(self):
		deal = self.richiesta(self.mario)
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		self.assertTrue(paziente.e_paziente(self.mario.name))
		self.assertEqual(self.tipo(deal), "Won")
		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "closed_date").isoformat(), nowdate())
		# a patient is a client from the same moment
		self.assertEqual(cliente.cliente_da(self.mario.name), self.scheda(self.mario).patient_since)

	def test_le_automazioni_lo_sentono(self):
		with patch("crm.automation.engine.process_event") as evento:
			paziente.assicura_paziente(self.mario.name, regole.A_MANO)
		annunci = self.annunci(evento)
		self.assertEqual(len(annunci), 1)
		self.assertEqual(annunci[0].args[1].name, self.mario.name)
		self.assertEqual(annunci[0].args[2], {"rule": regole.A_MANO.valore})

	def test_il_trigger_e_del_crm_nelle_parole_della_clinica(self):
		from crm import verticali
		from crm.automation.engine import trigger_offerti

		self.assertIn(cliente.TRIGGER, trigger_offerti())
		self.assertNotIn("Became Patient", trigger_offerti())
		self.assertEqual(verticali.parole()[cliente.TRIGGER], "Became Patient")

	def test_le_regole_del_crm_si_fanno_da_parte(self):
		"""With the clinic on, a course makes nobody a patient, nor a client."""
		self.assertFalse(cliente.regole_del_crm())
		corso = self.make_service("Corso di yoga cuciture", [self.doctor])
		frappe.get_doc(
			{
				"doctype": "CRM Billable Service",
				"service_name": "Corso di yoga cuciture",
				"fiscal_description": "Corso di yoga",
				"crm_service": corso.name,
				"is_healthcare": 0,
				"vat_rate": 22,
				"default_rate": 50,
				"enabled": 1,
			}
		).insert()
		incontro = self.appuntamento(self.mario, self.ieri(), servizio=corso.name)
		incontro.status = "Completed"
		incontro.save()
		self.assertFalse(paziente.e_paziente(self.mario.name))
		self.assertIsNone(cliente.cliente_da(self.mario.name))

	def test_i_pazienti_di_prima_non_chiudono_niente(self):
		self.accendi(False)
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		deal = self.richiesta(self.mario)
		with patch("crm.automation.engine.process_event") as evento:
			# switching it on looks for the patients already there
			self.accendi(True)
			paziente.recupera()
		self.assertTrue(paziente.e_paziente(self.mario.name))
		self.assertNotEqual(self.tipo(deal), "Won")
		self.assertEqual(self.annunci(evento), [])

	def test_un_deal_che_non_si_salva_non_ferma_il_paziente(self):
		self.richiesta(self.mario)
		with patch("crm.clienti.pipeline.vinci", side_effect=frappe.ValidationError("no")):
			paziente.assicura_paziente(self.mario.name, regole.A_MANO)
		self.assertTrue(paziente.e_paziente(self.mario.name))


class IlCruscotto(CucitureCase):
	def contesto(self):
		return Context.build(add_days(nowdate(), -7), nowdate(), scope="site", config={})

	def test_i_nuovi_pazienti(self):
		widget = registry.get("new_clients")
		prima = widget.fn(self.contesto())["value"]
		paziente.assicura_paziente(self.mario.name, regole.A_MANO)
		self.assertEqual(widget.fn(self.contesto())["value"], prima + 1)

	def test_il_costo_di_un_nuovo_paziente(self):
		from crm.dashboard.widgets.marketing import ad_clients

		prima = ad_clients(self.contesto())
		frappe.db.set_value("CRM Lead", self.mario.name, "facebook_ad_id", "ad-1")
		paziente.assicura_paziente(self.mario.name, regole.A_MANO)
		self.assertEqual(ad_clients(self.contesto()), prima + 1)

	def test_nelle_parole_della_clinica(self):
		from crm.api.dashboard import get_widget_catalog

		titoli = {widget["id"]: widget["title"] for widget in get_widget_catalog()["widgets"]}
		self.assertEqual(titoli["new_clients"], frappe._("New patients"))
		self.assertEqual(titoli["meta_cost_per_client"], frappe._("Cost per new patient"))
		self.accendi(False)
		titoli = {widget["id"]: widget["title"] for widget in get_widget_catalog()["widgets"]}
		self.assertEqual(titoli["new_clients"], frappe._("New clients"))


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


class LAccensione(CucitureCase):
	def test_il_piano_appena_salvato(self):
		"""on_update runs before Frappe drops the cached plan: switching the clinic on
		reads the plan just saved, so the patients already there are looked for."""
		self.accendi(False)
		frappe.get_cached_doc("CRM Plan")  # in the cache, as on a live site
		frappe.db.set_default(paziente.RECUPERO_FATTO, "")
		with patch("frappe.enqueue") as coda:
			piano = frappe.get_single("CRM Plan")
			piano.append("modules", {"module": "clinica", "status": "Active"})
			piano.save()
		self.assertIn("crm.clinica.paziente.recupera", [c.args[0] for c in coda.call_args_list])
