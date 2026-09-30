# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""When a form is asked, and whether a signed one still counts.

The rule is pure (`dovuti.dovuto`): by hand never asks; the first appointment
asks whoever never signed; some services ask only for those services; a year
passes; one appointment asks at each appointment; a new version asks again
from its date. Then what the desk sees: the person's forms to sign, the Today
page, and the link that leaves with the booking.
"""

import datetime
import json

import frappe
from frappe.tests import UnitTestCase
from frappe.utils import add_days, getdate

from crm.moduli import compilazioni, dovuti, richieste
from crm.moduli.tests.test_compilazioni import DESK, OTHER, PRIVACY, tratto
from crm.moduli.tests.test_richieste import RichiesteCase
from crm.tests.test_scheduling import SchedulingCase

OGGI = datetime.date(2026, 9, 30)


def firmato(version=1, giorni_fa=10, appointment=None):
	return {"version": version, "signed_on": add_days(OGGI, -giorni_fa), "appointment": appointment}


class IlDovuto(UnitTestCase):
	def modello(self, **campi):
		return {"ask_on": "First appointment", "validity": "Forever", "version": 1, **campi}

	def test_a_mano_non_si_chiede_mai(self):
		self.assertIsNone(dovuti.dovuto(self.modello(ask_on="By hand"), [], {"name": "A"}, OGGI))

	def test_la_prima_volta(self):
		self.assertEqual(dovuti.dovuto(self.modello(), [], None, OGGI), "never_signed")
		self.assertIsNone(dovuti.dovuto(self.modello(), [firmato()], None, OGGI))

	def test_per_un_anno(self):
		modello = self.modello(validity="One year")
		self.assertEqual(dovuti.dovuto(modello, [firmato(giorni_fa=400)], None, OGGI), "expired")
		self.assertIsNone(dovuti.dovuto(modello, [firmato(giorni_fa=400), firmato(giorni_fa=20)], None, OGGI))
		self.assertEqual(dovuti.dovuto(modello, [firmato(giorni_fa=365)], None, OGGI), "expired")

	def test_a_ogni_appuntamento(self):
		modello = self.modello(validity="Every appointment")
		# without an appointment there is nothing to ask yet
		self.assertIsNone(dovuti.dovuto(modello, [], None, OGGI))
		self.assertEqual(
			dovuti.dovuto(modello, [firmato(appointment="B")], {"name": "A"}, OGGI), "every_appointment"
		)
		self.assertIsNone(dovuti.dovuto(modello, [firmato(appointment="A")], {"name": "A"}, OGGI))

	def test_per_alcuni_servizi(self):
		modello = self.modello(ask_on="Services", services=["Visita"])
		self.assertIsNone(dovuti.dovuto(modello, [], {"name": "A", "service": "Massaggio"}, OGGI))
		self.assertIsNone(dovuti.dovuto(modello, [], None, OGGI))
		self.assertEqual(dovuti.dovuto(modello, [], {"name": "A", "service": "Visita"}, OGGI), "never_signed")

	def test_una_versione_nuova_chiede_di_nuovo_dalla_sua_data(self):
		modello = self.modello(version=2, asked_from=add_days(OGGI, -1))
		self.assertEqual(dovuti.dovuto(modello, [firmato(version=1)], None, OGGI), "new_version")
		self.assertIsNone(dovuti.dovuto(modello, [firmato(version=2)], None, OGGI))
		domani = self.modello(version=2, asked_from=add_days(OGGI, 1))
		self.assertIsNone(dovuti.dovuto(domani, [firmato(version=1)], None, OGGI))
		# with no date, a new version does not ask whoever signed before
		self.assertIsNone(dovuti.dovuto(self.modello(version=2), [firmato(version=1)], None, OGGI))


class DovutiCase(RichiesteCase, SchedulingCase):
	def setUp(self):
		SchedulingCase.setUp(self)
		RichiesteCase.setUp(self)
		self.medico = self.make_user("dovuti.doctor@example.com")
		self.visita = self.make_service("Visita dovuti", [self.medico])

	def tearDown(self):
		RichiesteCase.tearDown(self)
		SchedulingCase.tearDown(self)

	def chiedi(self, titolo="Anamnesi", **campi):
		nome = self.pubblica(PRIVACY, titolo)
		frappe.db.set_value("CRM Form Template", nome, {"ask_on": "First appointment", **campi})
		return nome

	def appuntamento(self, quando=None, persona=None):
		"""An appointment for the person; ``quando`` is an aware moment (the agenda
		keeps the system's time)."""
		frappe.set_user("Administrator")
		persona = persona or self.giulia
		quando = quando or datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=2)
		return self.make_appointment(
			self.visita.name,
			quando,
			[self.medico],
			participants=[
				{"party_type": "CRM Lead", "party": persona.name, "participant_name": persona.lead_name}
			],
		)

	def firma(self, nome, risposte=None, firme=None, **altro):
		return compilazioni.sign_form(
			nome,
			json.dumps({"read": True, "marketing": False, "weight": "70"} if risposte is None else risposte),
			json.dumps({"sign": tratto()} if firme is None else firme),
			**altro,
		)


class LaSchedaEOggi(DovutiCase):
	def test_la_scheda_dice_cosa_firmare_per_il_prossimo_appuntamento(self):
		anamnesi = self.chiedi()
		appuntamento = self.appuntamento()
		self.come(DESK)
		dovuto = compilazioni.get_person_forms(self.giulia.name)["due"]
		self.assertEqual(dovuto["appointment"]["name"], appuntamento.name)
		[voce] = [f for f in dovuto["forms"] if f["template"] == anamnesi]
		self.assertEqual(
			(voce["reason"], voce["pending"], voce["appointment"]), ("never_signed", None, appuntamento.name)
		)
		# started, it is under way; signed, it is owed no more
		nome = compilazioni.start_form(self.giulia.name, anamnesi, appointment=appuntamento.name)["name"]
		self.assertEqual(
			[
				f["pending"]
				for f in compilazioni.get_person_forms(self.giulia.name)["due"]["forms"]
				if f["template"] == anamnesi
			],
			["draft"],
		)
		self.firma(nome)
		self.assertNotIn(
			anamnesi, [f["template"] for f in compilazioni.get_person_forms(self.giulia.name)["due"]["forms"]]
		)

	def test_oggi_segna_chi_deve_firmare(self):
		anamnesi = self.chiedi()
		from crm.scheduling.timeutils import scheduling_tz

		# today at noon where the agenda is: the same day whatever the server's zone
		oggi = datetime.datetime.combine(getdate(), datetime.time(12, 0), tzinfo=scheduling_tz())
		appuntamento = self.appuntamento(oggi)
		self.come(DESK)
		from crm.api import oggi as pagina

		giorno = pagina.get_day(str(getdate()))
		[riga] = [a for a in giorno["appointments"] if a["name"] == appuntamento.name]
		[persona] = riga["participants"]
		# the site may ask other forms of its own: this one is among them
		self.assertIn(anamnesi, [f["template"] for f in persona["due_forms"]])

	def test_chi_non_vede_i_moduli_non_li_vede_nemmeno_qui(self):
		self.chiedi()
		self.appuntamento()
		self.come(OTHER)
		with self.assertRaises(frappe.PermissionError):
			compilazioni.get_person_forms(self.giulia.name)


class ConLaPrenotazione(DovutiCase):
	def test_il_link_parte_con_la_prenotazione(self):
		anamnesi = self.chiedi(send_before=1)
		self.chiedi("Questionario")  # asked, but not sent by itself
		appuntamento = self.appuntamento()
		frappe.set_user("Administrator")
		[richiesta] = frappe.get_all(
			richieste.RICHIESTA,
			filters={"lead": self.giulia.name},
			fields=["name", "template", "channel", "appointment", "expires_on", "status"],
		)
		self.assertEqual(
			(richiesta.template, richiesta.channel, richiesta.appointment, richiesta.status),
			(anamnesi, "Link", appuntamento.name, "Sent"),
		)
		# the link lasts until the appointment
		self.assertEqual(richiesta.expires_on, appuntamento.starts_on)
		posta = frappe.get_last_doc("Email Queue", filters={"reference_name": richiesta.name})
		self.assertNotIn("Anamnesi", posta.message)
		# a second booking does not send it again while the first link is open
		self.appuntamento(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=5))
		self.assertEqual(frappe.db.count(richieste.RICHIESTA, {"lead": self.giulia.name}), 1)

	def test_senza_email_o_troppo_vicino_non_parte(self):
		self.chiedi(send_before=1)
		frappe.db.set_value("CRM Lead", self.giulia.name, "email", None)
		self.appuntamento()
		self.assertEqual(frappe.db.count(richieste.RICHIESTA, {"lead": self.giulia.name}), 0)
		frappe.db.set_value("CRM Lead", self.giulia.name, "email", "giulia.modulo@example.com")
		# in half an hour there is no time to fill it at home
		self.appuntamento(datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=30))
		self.assertEqual(frappe.db.count(richieste.RICHIESTA, {"lead": self.giulia.name}), 0)
