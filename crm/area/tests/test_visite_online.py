# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Online visits, on a site without the clinic.

A service held by video gives each appointment the link of its room: on the
agency's video server a room of its own, its name random and nothing of Anna's,
made once when it is saved; without a server the professional's own room; a link
the desk pastes stays, an http one is refused. It needs no room of the centre. The
staff who read the appointment read its link; Anna enters it from her area only,
from a quarter of an hour before it starts, and never somebody else's; the list
never carries the link. The demo's appointments get no room on a real server. The
reminder says it is an online visit and sends Anna to her area, never to the room.
"""

import datetime
from unittest import mock

import frappe

from crm.api import appointments as api_appuntamenti
from crm.area import accesso, api
from crm.area.tests.test_area import DESK, AreaCase
from crm.scheduling import promemoria, visite_online
from crm.scheduling import visite_online_regole as R

SERVER = "https://video.example.eu"


class VisiteOnlineCase(AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		frappe.db.set_single_value("CRM Scheduling Settings", "video_server", SERVER)
		self.medico = self.make_user("video.medico@example.com")
		self.stanza = self.make_resource("Studio video")
		self.servizio = self.make_service(
			"Visita video",
			[self.medico],
			online_visit=1,
			resources=[{"resource_type": "Room", "resource": self.stanza.name, "quantity": 1, "required": 1}],
		)

	def tearDown(self):
		frappe.db.set_single_value("CRM Scheduling Settings", "video_server", None)
		super().tearDown()

	def appuntamento(self, fra_minuti=10, persona=None, **altro):
		frappe.set_user("Administrator")
		persona = persona or self.anna
		inizio = datetime.datetime.now(datetime.UTC).replace(second=0, microsecond=0) + datetime.timedelta(
			minutes=fra_minuti
		)
		return self.make_appointment(
			self.servizio.name,
			inizio,
			[self.medico],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": persona.name,
					"participant_name": persona.lead_name,
					"status": "Booked",
				}
			],
			**altro,
		)


class LaStanza(VisiteOnlineCase):
	def test_una_stanza_casuale_fatta_una_volta(self):
		appuntamento = self.appuntamento()
		link = appuntamento.video_link
		self.assertRegex(link, rf"^{SERVER}/[a-z2-7]{{24}}$")
		nome = link.rsplit("/", 1)[1]
		self.assertNotIn(appuntamento.name.lower(), nome)
		self.assertNotIn("anna", nome)
		appuntamento.notes = "Di nuovo"
		appuntamento.save()
		self.assertEqual(appuntamento.video_link, link)
		# another appointment, another room
		self.assertNotEqual(self.appuntamento(200).video_link, link)

	def test_il_server_dalla_configurazione(self):
		frappe.db.set_single_value("CRM Scheduling Settings", "video_server", None)
		with mock.patch.dict(frappe.conf, {"dottorcloud_video": {"url": "https://meet.example.eu/"}}):
			self.assertEqual(visite_online.server(), "https://meet.example.eu")
			self.assertTrue(self.appuntamento().video_link.startswith("https://meet.example.eu/"))

	def test_senza_server_la_stanza_del_professionista(self):
		frappe.db.set_single_value("CRM Scheduling Settings", "video_server", None)
		self.assertIsNone(self.appuntamento().video_link)
		api_appuntamenti.save_schedule(
			{"user": self.medico, "enabled": 0, "video_link": "https://meet.google.com/abc-defg-hij"}
		)
		self.assertEqual(self.appuntamento(200).video_link, "https://meet.google.com/abc-defg-hij")
		with self.assertRaises(frappe.ValidationError):
			api_appuntamenti.save_schedule({"user": self.medico, "enabled": 0, "video_link": "http://x.eu"})

	def test_un_link_incollato_resta_se_e_https(self):
		appuntamento = self.appuntamento(video_link="https://zoom.us/j/123")
		self.assertEqual(appuntamento.video_link, "https://zoom.us/j/123")
		with self.assertRaises(frappe.ValidationError):
			self.appuntamento(200, video_link="javascript:alert(1)")

	def test_un_servizio_in_studio_non_ne_ha(self):
		altro = self.make_service("In studio", [self.medico])
		inizio = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=2)
		self.assertIsNone(self.make_appointment(altro.name, inizio, [self.medico]).video_link)

	def test_nessun_ambulatorio_del_centro(self):
		[stanza] = self.servizio.resources
		self.assertFalse(visite_online.serve_la_stanza(self.servizio, stanza))
		attrezzo = frappe._dict(resource=None, resource_type="Equipment")
		self.assertTrue(visite_online.serve_la_stanza(self.servizio, attrezzo))
		self.servizio.online_visit = 0
		self.assertTrue(visite_online.serve_la_stanza(self.servizio, stanza))

	def test_mai_per_la_demo(self):
		with mock.patch("crm.demo.registro.raccolta", return_value=mock.MagicMock()):
			self.assertIsNone(self.appuntamento().video_link)

	def test_lo_staff_lo_legge_dal_pannello(self):
		appuntamento = self.appuntamento()
		self.come(DESK)
		letto = api_appuntamenti.get_appointment(appuntamento.name)
		self.assertTrue(letto["online_visit"])
		self.assertEqual(letto["video_link"], appuntamento.video_link)


class DallArea(VisiteOnlineCase):
	def setUp(self):
		super().setUp()
		self.invita()

	def test_si_entra_un_quarto_d_ora_prima(self):
		appuntamento = self.appuntamento(10)
		self.entra()
		[prossimo] = api.get_appointments(self.anna.name)["upcoming"]
		self.assertTrue(prossimo["online"])
		self.assertEqual(prossimo["online_visit"]["opens_in"], 0)
		# the list never carries the room, nor the check-in of a visit at the centre
		self.assertNotIn(appuntamento.video_link, frappe.as_json(prossimo))
		self.assertNotIn("check_in", prossimo)
		self.assertIsNone(prossimo["location"])
		self.assertEqual(
			api.enter_online_visit(self.anna.name, appuntamento.name), {"url": appuntamento.video_link}
		)

	def test_troppo_presto_no(self):
		appuntamento = self.appuntamento(120)
		self.entra()
		[prossimo] = api.get_appointments(self.anna.name)["upcoming"]
		self.assertGreater(prossimo["online_visit"]["opens_in"], 100 * 60)
		with self.assertRaises(frappe.ValidationError):
			api.enter_online_visit(self.anna.name, appuntamento.name)

	def test_annullato_no(self):
		appuntamento = self.appuntamento(5)
		frappe.db.set_value("CRM Appointment", appuntamento.name, "status", "Cancelled")
		self.entra()
		with self.assertRaises(frappe.ValidationError):
			api.enter_online_visit(self.anna.name, appuntamento.name)

	def test_l_appuntamento_di_un_altro_no(self):
		bruno = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Bruno", "last_name": "Video"}).insert(
			ignore_permissions=True
		)
		suo = self.appuntamento(5, bruno)
		self.entra()
		with self.assertRaises(frappe.PermissionError):
			api.enter_online_visit(self.anna.name, suo.name)
		with self.assertRaises(frappe.PermissionError):
			api.enter_online_visit(bruno.name, suo.name)
		with self.assertRaises(frappe.PermissionError):
			api.enter_online_visit(self.anna.name, "nessuno")

	def test_lo_staff_non_entra_da_qui(self):
		appuntamento = self.appuntamento(5)
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			api.enter_online_visit(self.anna.name, appuntamento.name)


class IlPromemoria(VisiteOnlineCase):
	def test_dice_che_e_online_e_manda_all_area(self):
		appuntamento = self.appuntamento(24 * 60)
		[riga] = appuntamento.participants
		testo = promemoria._testo(appuntamento, riga, self.anna.name)
		self.assertIn(frappe._("{0}, online visit").format("Visita video"), testo["cosa"])
		self.assertIn("/area/appointments", testo["online"])
		testo["link"] = "https://centro.example.com/prenota?token=x"
		sms = promemoria.testo_sms(testo, None)
		self.assertIn("/area/appointments", sms)
		self.assertNotIn(appuntamento.video_link, sms + testo["online"])
		# her area was opened for her, and nothing was sent to say so
		self.assertTrue(accesso.accessi_aperti(self.anna.name))

	def test_un_area_chiusa_non_si_riapre(self):
		self.invita()
		frappe.set_user("Administrator")
		frappe.db.set_value(accesso.ACCESSO, {"lead": self.anna.name}, "enabled", 0)
		self.assertIsNone(visite_online.area_per(self.anna.name))
		self.assertEqual(
			visite_online.frase(None),
			frappe._("It is an online visit: the centre tells you how to enter it."),
		)

	def test_la_finestra_e_quella_delle_regole(self):
		self.assertEqual(visite_online.MINUTI, int(R.ANTICIPO.total_seconds() // 60))
