# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The second seam, from the centre to marketing: the recall (docs/gestionale-medico).

People are picked by administrative data - when they last came, what they booked -
never by the clinical record, and only with their yes to marketing. An automation
for marketing skips whoever did not agree, says so in its runs, and does not send
if the consent was withdrawn meanwhile. The centre's dashboard counts who is due.
"""

import datetime
import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, nowdate

from crm.automation import engine
from crm.dashboard import registry, store, templates
from crm.dashboard.context import Context
from crm.moduli import consensi
from crm.permissions import livelli
from crm.tests.test_automation import make_automation
from crm.tests.test_scheduling import SchedulingCase

EMAIL = [{"type": "send_email", "subject": "Ci rivediamo?", "message": "È passato un anno."}]


class RichiamiCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		consensi.assicura_tipi()
		self.anna = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Anna",
				"last_name": "Richiamo",
				"email": "anna.richiamo@example.com",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def automazione(self, **valori):
		return make_automation(
			f"Richiamo {frappe.generate_hash(length=6)}", EMAIL, marketing_consent=1, **valori
		)


class IlConsenso(RichiamiCase):
	def test_senza_il_si_si_salta_e_si_dice(self):
		automazione = self.automazione()
		self.assertIsNone(engine.enroll(automazione.name, "CRM Lead", self.anna.name))
		saltate = frappe.get_all(
			"CRM Automation Enrollment",
			filters={"automation": automazione.name, "reference_name": self.anna.name},
			fields=["name", "status"],
		)
		self.assertEqual([s.status for s in saltate], ["Skipped"])
		log = frappe.get_all("CRM Automation Step Log", filters={"parent": saltate[0].name}, pluck="detail")
		self.assertIn("No marketing consent", log)
		# once per person, however many times the trigger fires
		engine.enroll(automazione.name, "CRM Lead", self.anna.name)
		self.assertEqual(frappe.db.count("CRM Automation Enrollment", {"automation": automazione.name}), 1)

	def test_chi_dice_si_dopo_entra(self):
		automazione = self.automazione()
		engine.enroll(automazione.name, "CRM Lead", self.anna.name)
		consensi.registra_risposta(self.anna.name, "marketing")
		self.assertIsNotNone(engine.enroll(automazione.name, "CRM Lead", self.anna.name))

	def test_revocato_nel_frattempo_non_si_manda(self):
		automazione = self.automazione()
		consensi.registra_risposta(self.anna.name, "marketing")
		nome = engine.enroll(automazione.name, "CRM Lead", self.anna.name)
		consensi.revoca(self.anna.name, "marketing")
		frappe.db.set_value("CRM Automation Enrollment", nome, {"status": "Active", "current_step": 0})
		engine.advance_enrollment(nome)
		# the second time round, after the withdrawal
		self.assertTrue(
			frappe.db.exists(
				"CRM Automation Step Log",
				{
					"parent": nome,
					"action": "send_email",
					"status": "Skipped",
					"detail": ["like", "No marketing consent%"],
				},
			)
		)

	def test_senza_l_opzione_tutto_come_prima(self):
		automazione = make_automation(f"Senza {frappe.generate_hash(length=6)}", EMAIL)
		self.assertIsNotNone(engine.enroll(automazione.name, "CRM Lead", self.anna.name))


class LUltimaVisita(SchedulingCase):
	def setUp(self):
		super().setUp()
		self.medico = self.make_user("richiami.medico@example.com")
		self.servizio = self.make_service("Controllo annuale", [self.medico])
		self.bruno = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Bruno", "last_name": "Visita"}
		).insert(ignore_permissions=True)

	def appuntamento(self, giorni_fa, stato="Completed", presenza="Booked"):
		quando = self.tomorrow(10) - datetime.timedelta(days=giorni_fa + 1)
		doc = self.make_appointment(
			self.servizio.name,
			quando,
			[self.medico],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": self.bruno.name,
					"participant_name": self.bruno.lead_name,
					"status": presenza,
				}
			],
		)
		doc.status = stato
		doc.save()
		return doc

	def test_l_agenda_la_tiene(self):
		recente = self.appuntamento(10)
		self.appuntamento(40)
		visita, servizio = frappe.db.get_value("CRM Lead", self.bruno.name, ["last_visit", "last_service"])
		# the older one, closed later, does not take its place
		self.assertEqual(getdate(visita), getdate(recente.starts_on))
		self.assertEqual(servizio, self.servizio.name)

	def test_chi_non_e_venuto_no(self):
		self.appuntamento(10, stato="Confirmed", presenza="No Show")
		self.assertIsNone(frappe.db.get_value("CRM Lead", self.bruno.name, "last_visit"))

	def test_la_patch_la_trova_nel_passato(self):
		from crm.patches.v1_0 import last_visit_from_appointments

		incontro = self.appuntamento(20)
		frappe.db.set_value("CRM Lead", self.bruno.name, {"last_visit": None, "last_service": None})
		last_visit_from_appointments.execute()
		self.assertEqual(
			getdate(frappe.db.get_value("CRM Lead", self.bruno.name, "last_visit")),
			getdate(incontro.starts_on),
		)

	def test_il_promemoria_la_legge(self):
		"""The recall is a Date Reminder on the last visit: a year after it."""
		automazione = make_automation(
			f"Dopo un anno {frappe.generate_hash(length=6)}",
			EMAIL,
			trigger_event="Date Reminder",
			trigger_config=json.dumps(
				{"doctype": "CRM Lead", "date_field": "last_visit", "direction": "after", "offset_days": 365}
			),
		)
		frappe.db.set_value("CRM Lead", self.bruno.name, "last_visit", add_days(nowdate(), -365))
		frappe.cache.delete_value(f"crm_date_reminders_ran|{frappe.utils.today()}")
		engine.process_date_reminders_tick()
		self.assertTrue(
			frappe.db.exists(
				"CRM Automation Enrollment",
				{"automation": automazione.name, "reference_name": self.bruno.name},
			)
		)


class IlCruscottoDelCentro(RichiamiCase):
	def test_da_richiamare(self):
		frappe.db.set_value(
			"CRM Lead",
			self.anna.name,
			{"last_visit": add_days(nowdate(), -400), "marketing_consent": "Given"},
		)
		widget = registry.get("recall_due")
		ctx = Context.build(nowdate(), nowdate(), scope=widget.scope, config={})
		prima = widget.fn(ctx)["value"]
		frappe.db.set_value("CRM Lead", self.anna.name, "marketing_consent", "Withdrawn")
		self.assertEqual(widget.fn(ctx)["value"], prima - 1)

	def test_il_modello_c_e_con_la_clinica(self):
		self.assertIn("medical_centre", {t.id for t in templates.tutti()})
		self.assertEqual(templates.get("medical_centre").requires, ("clinic",))

	def test_nasce_quando_si_accende_la_clinica(self):
		frappe.db.delete("CRM Dashboard", {"template": "medical_centre"})
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [])
		piano.save()
		livelli.dimentica_cache()
		store.create_template_dashboards(only=("medical_centre",))
		self.assertFalse(frappe.db.exists("CRM Dashboard", {"template": "medical_centre"}))
		piano.set("modules", [{"module": "clinica", "status": "Active"}])
		piano.save()
		self.assertTrue(frappe.db.exists("CRM Dashboard", {"template": "medical_centre"}))
