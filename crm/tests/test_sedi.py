# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""More than one location in one centre, on a site (docs/crm/62): the engine books
a professional where their shift is, with that location's rooms; the agenda, the
reception desk and the cash closing read one location; an invoice takes its
location's company. With one location nothing changes."""

from __future__ import annotations

import datetime

import frappe
from frappe.utils import nowdate

from crm.api import appointments as A
from crm.api import oggi
from crm.api import sedi as api_sedi
from crm.scheduling import sedi
from crm.scheduling.availability import find_conflicts, get_slots
from crm.scheduling.timeutils import UTC
from crm.tests.test_invoicing import InvoicingBase
from crm.tests.test_scheduling import ALL_DAYS, SchedulingCase


def sede(nome, **altro):
	doc = frappe.get_doc({"doctype": "CRM Location", "location_name": nome, "enabled": 1, **altro}).insert()
	sedi.dimentica()
	return doc.name


def prossimo(nome_del_giorno: str, ora: int = 10) -> datetime.datetime:
	giorno = datetime.datetime.now(UTC).date() + datetime.timedelta(days=1)
	while ALL_DAYS[giorno.weekday()] != nome_del_giorno:
		giorno += datetime.timedelta(days=1)
	return datetime.datetime.combine(giorno, datetime.time(ora), tzinfo=UTC)


class SediCase(SchedulingCase):
	def setUp(self):
		super().setUp()
		# whatever another test or the demo left: this test's locations only
		frappe.db.set_value("CRM Location", {"enabled": 1}, "enabled", 0)
		sedi.dimentica()

	def tearDown(self):
		super().tearDown()
		sedi.dimentica()

	def turni(self, utente, dove: dict):
		"""A week of 08-20, each day at the location `dove` names (else anywhere)."""
		frappe.get_doc(
			{
				"doctype": "CRM Staff Schedule",
				"user": utente,
				"enabled": 1,
				"availability": [
					{
						"workday": giorno,
						"start_time": "08:00:00",
						"end_time": "20:00:00",
						"centre_location": dove.get(giorno),
					}
					for giorno in ALL_DAYS
				],
			}
		).insert()


class UnaSedeSola(SediCase):
	def test_con_una_sede_niente_cambia(self):
		milano = sede("Sede di Milano test")
		self.assertFalse(sedi.piu_sedi())
		self.assertEqual(sedi.per_il_boot(), [])
		anna = self.make_user("anna_sede@example.com")
		stanza = self.make_resource("Studio sede unica")
		servizio = self.make_service(
			"Visita sede unica", [anna], resources=[{"resource": stanza.name, "quantity": 1, "required": 1}]
		)
		slot = get_slots(servizio.name, prossimo("Monday").date(), prossimo("Monday").date())
		self.assertTrue(slot)
		self.assertIsNone(slot[0].location)
		# the only location goes on the appointment, quietly
		appuntamento = self.make_appointment(
			servizio.name,
			prossimo("Monday"),
			[anna],
			resources=[{"resource": stanza.name, "quantity": 1}],
		)
		self.assertEqual(appuntamento.centre_location, milano)
		feed = A.get_calendar(str(prossimo("Monday").date()), str(prossimo("Monday").date()), with_hours=1)
		for giorno in (feed["hours"]["staff"].get(anna) or {}).values():
			self.assertNotIn("sedi", giorno)
		self.assertEqual(A.get_scheduler_meta()["locations"], [])


class DueSedi(SediCase):
	def setUp(self):
		super().setUp()
		self.milano = sede("Sede di Milano test", address_line="Via Roma 1", city="Milano", pincode="20100")
		self.monza = sede(
			"Sede di Monza test", address_line="Via Italia 12", city="Monza", pincode="20900", province="MB"
		)
		self.luca = self.make_user("luca_sede@example.com")
		# Luca works in Monza on Tuesdays, in Milan the other days
		self.turni(self.luca, {g: (self.monza if g == "Tuesday" else self.milano) for g in ALL_DAYS})
		self.studio = self.make_resource("Studio 2 test", centre_location=self.milano)
		self.monza_a = self.make_resource("Monza A test", centre_location=self.monza)
		self.servizio = self.make_service(
			"Osteopatia sedi",
			[self.luca],
			resources=[{"resource": self.studio.name, "quantity": 1, "required": 1}],
		)

	def test_piu_sedi(self):
		self.assertTrue(sedi.piu_sedi())
		self.assertEqual({s["name"] for s in sedi.per_il_boot()}, {self.milano, self.monza})

	def test_il_martedi_a_monza_con_la_stanza_di_monza(self):
		martedi = prossimo("Tuesday").date()
		slots = get_slots(self.servizio.name, martedi, martedi)
		self.assertTrue(slots)
		self.assertEqual({s.location for s in slots}, {self.monza})
		self.assertEqual({r["resource"] for s in slots for r in s.resources}, {self.monza_a.name})
		self.assertEqual(get_slots(self.servizio.name, martedi, martedi, location=self.milano), [])

	def test_il_lunedi_a_milano(self):
		lunedi = prossimo("Monday").date()
		slots = get_slots(self.servizio.name, lunedi, lunedi)
		self.assertEqual({s.location for s in slots}, {self.milano})
		self.assertEqual({r["resource"] for s in slots for r in s.resources}, {self.studio.name})
		self.assertEqual(get_slots(self.servizio.name, lunedi, lunedi, location=self.monza), [])

	def test_mai_in_due_posti(self):
		doc = frappe.get_doc(
			{
				"doctype": "CRM Appointment",
				"service": self.servizio.name,
				"starts_on": prossimo("Tuesday").replace(tzinfo=None),
				"staff": [{"user": self.luca}],
				"resources": [{"resource": self.studio.name, "quantity": 1}],
			}
		)
		doc.apply_service_defaults()
		self.assertTrue(any("Sede di Monza test" in c for c in find_conflicts(doc)))

	def test_la_sede_dell_appuntamento_e_l_agenda(self):
		a_monza = self.make_appointment(
			self.servizio.name,
			prossimo("Tuesday"),
			[self.luca],
			resources=[{"resource": self.monza_a.name, "quantity": 1}],
		)
		self.assertEqual(a_monza.centre_location, self.monza)
		# no room: the shift says where
		senza_stanza = self.make_appointment(self.servizio.name, prossimo("Tuesday", 15), [self.luca])
		self.assertEqual(senza_stanza.centre_location, self.monza)
		giorno = str(prossimo("Tuesday").date())
		nomi = lambda feed: {a["name"] for a in feed["appointments"]}  # noqa: E731
		self.assertIn(a_monza.name, nomi(A.get_calendar(giorno, giorno, location=self.monza)))
		self.assertNotIn(a_monza.name, nomi(A.get_calendar(giorno, giorno, location=self.milano)))
		self.assertIn(a_monza.name, nomi(A.get_calendar(giorno, giorno)))
		# the grid knows where each works that day
		ore = A.get_calendar(giorno, giorno, with_hours=1)["hours"]["staff"][self.luca][giorno]
		self.assertEqual(ore["sedi"], [self.monza])
		meta = A.get_scheduler_meta()
		self.assertEqual(len(meta["locations"]), 2)
		self.assertIn(
			self.monza,
			next(r for r in meta["resources"] if r["name"] == self.monza_a.name)["centre_location"],
		)
		# the reception desk of one location
		self.assertIn(
			a_monza.name, {a["name"] for a in oggi.get_day(giorno, location=self.monza)["appointments"]}
		)
		self.assertNotIn(
			a_monza.name, {a["name"] for a in oggi.get_day(giorno, location=self.milano)["appointments"]}
		)

	def test_l_indirizzo_che_la_persona_legge(self):
		a_monza = self.make_appointment(
			self.servizio.name,
			prossimo("Tuesday"),
			[self.luca],
			resources=[{"resource": self.monza_a.name, "quantity": 1}],
		)
		self.assertEqual(sedi.indirizzo_di(a_monza), "Sede di Monza test, Via Italia 12, 20900 Monza (MB)")

	def test_la_sede_abituale(self):
		self.assertIsNone(sedi.sede_abituale())
		api_sedi.set_my_location(self.monza)
		self.assertEqual(sedi.sede_abituale(), self.monza)
		api_sedi.set_my_location(None)
		self.assertIsNone(sedi.sede_abituale())

	def test_la_storia_va_nella_sede_della_sua_stanza(self):
		anna = self.make_user("anna_storia@example.com")
		vecchia = self.make_resource("Studio vecchio test")
		servizio = self.make_service("Visita storia", [anna])
		prima = self.make_appointment(
			servizio.name, prossimo("Monday"), [anna], resources=[{"resource": vecchia.name, "quantity": 1}]
		)
		self.assertFalse(prima.centre_location)
		vecchia.centre_location = self.monza
		vecchia.save()
		self.assertEqual(frappe.db.get_value("CRM Appointment", prima.name, "centre_location"), self.monza)

	def test_i_turni_portano_nella_loro_sede_gli_appuntamenti_avanti(self):
		anna = self.make_user("anna_turni@example.com")
		servizio = self.make_service("Visita turni", [anna])
		avanti = self.make_appointment(servizio.name, prossimo("Tuesday"), [anna])
		self.assertFalse(avanti.centre_location)
		self.turni(anna, {"Tuesday": self.monza})
		self.assertEqual(frappe.db.get_value("CRM Appointment", avanti.name, "centre_location"), self.monza)

	def test_una_sede_con_stanze_non_si_elimina(self):
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, "CRM Location", self.monza)


class CassaPerSede(InvoicingBase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_value("CRM Location", {"enabled": 1}, "enabled", 0)
		sedi.dimentica()
		self.milano = sede("Cassa Milano test")
		self.monza = sede("Cassa Monza test")

	def tearDown(self):
		super().tearDown()
		sedi.dimentica()

	def incassata(self, dove):
		documento = self.fattura(
			self.consulenza.name, self.consulente.name, payment_method="MP01", centre_location=dove
		)
		documento.submit()
		frappe.db.set_value("CRM Invoice", documento.name, {"collected_on": nowdate(), "test_document": 0})
		return documento

	def test_ogni_sede_chiude_la_sua(self):
		prima = oggi.get_cash_summary(nowdate(), location=self.monza)["collected"]
		a_monza = self.incassata(self.monza)
		self.assertEqual(frappe.db.get_value("CRM Invoice", a_monza.name, "centre_location"), self.monza)
		self.incassata(self.milano)
		monza = oggi.get_cash_summary(nowdate(), location=self.monza)
		self.assertAlmostEqual(
			monza["collected"] - prima, float(a_monza.net_payable or a_monza.grand_total), places=2
		)
		self.assertEqual(monza["location"], self.monza)
		# one closing for each location, one for the whole centre, the same day
		oggi.close_cash_day(nowdate(), monza["expected_cash"], location=self.monza)
		oggi.close_cash_day(nowdate(), 0, location=self.milano)
		oggi.close_cash_day(nowdate(), 0)
		oggi.close_cash_day(nowdate(), 1, location=self.monza)
		self.assertEqual(frappe.db.count("CRM Cash Closing", {"date": nowdate()}), 3)
		self.assertEqual(oggi.get_cash_summary(nowdate(), location=self.monza)["closing"]["counted_cash"], 1)

	def test_la_sede_con_la_sua_societa(self):
		frappe.db.set_value("CRM Location", self.monza, "company", self.azienda.name)
		sedi.dimentica()
		# nobody is the default: only the location says who invoices
		frappe.db.set_value("CRM Invoicing Company", self.azienda.name, "is_default", 0)
		frappe.db.set_single_value("CRM Invoicing Settings", "default_company", None)
		documento = self.fattura(
			self.consulenza.name, self.consulente.name, company=None, centre_location=self.monza
		)
		self.assertEqual(documento.company, self.azienda.name)
		with self.assertRaises(frappe.ValidationError):
			self.fattura(
				self.consulenza.name, self.consulente.name, company=None, centre_location=self.milano
			)
