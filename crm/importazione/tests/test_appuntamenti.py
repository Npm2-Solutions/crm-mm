# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Appointments brought over from the previous software, on a real site: the sheet
shown before anything is written, the names matched, the person found or made, the
history attended and its clients, nothing announced, nothing brought in twice."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.importazione import appuntamenti, importa
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

MANAGER = "appuntamenti.manager@example.com"
MEDICO = "appuntamenti.medico@example.com"
SERVIZIO = "Visita importata di prova"

FOGLIO = (
	"Paziente;Codice fiscale;E-mail;Data;Ora;Durata;Prestazione;Medico;Stato\n"
	f"ROSSI MARIA;RSSMRA82C52F205N;;02/03/2025;9.30;45 min;{SERVIZIO};Dott. Medico Prova;Eseguito\n"
	f"Rossi Maria;RSSMRA82C52F205N;;03/03/2025;9.30;;{SERVIZIO};Dott. Medico Prova;Disdetto\n"
	"BIANCHI LUCA;;luca.appuntamenti@example.com;15/01/2099;16:00;30;Controllo del nuovo programma;;\n"
	f"VERDI GIUSEPPE;;;04/03/2025;10:00;;{SERVIZIO};;\n"
	f"NERI ANNA;;anna.appuntamenti@example.com;31/02/2025;10:00;;{SERVIZIO};;\n"
)


class GliAppuntamentiDalGestionaleDiPrima(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		utenti.sincronizza()
		make_user(MANAGER)
		utenti.assegna_livelli(MANAGER, ["manager"])
		medico = make_user(MEDICO, roles=["Sales User"])
		medico.first_name, medico.last_name = "Medico", "Prova"
		medico.save(ignore_permissions=True)
		livelli.dimentica_cache()
		frappe.cache.delete_value(importa.CHIAVE)
		if not frappe.db.exists("CRM Service", SERVIZIO):
			frappe.get_doc(
				{
					"doctype": "CRM Service",
					"service_name": SERVIZIO,
					"duration": 30,
					"enabled": 1,
					"staff": [{"user": MEDICO}],
				}
			).insert(ignore_permissions=True)
		# somebody already here, by email
		self.luca = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Luca",
				"last_name": "Bianchi",
				"email": "luca.appuntamenti@example.com",
			}
		).insert(ignore_permissions=True)
		# an automation listening to new appointments: it hears none of these
		self.automazione = frappe.get_doc(
			{
				"doctype": "CRM Automation",
				"title": "Ascolta gli appuntamenti importati",
				"enabled": 1,
				"triggers": [{"trigger_event": "Appointment Created"}],
				"steps": json.dumps([{"type": "add_note", "comment": "x"}]),
			}
		).insert(ignore_permissions=True)
		frappe.set_user(MANAGER)
		self.file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "agenda.csv",
				"content": FOGLIO.encode("cp1252"),
				"is_private": 1,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.cache.delete_value(importa.CHIAVE)
		frappe.cache.delete_value(appuntamenti.ESITO)
		frappe.db.rollback()

	def test_prima_si_vede_poi_si_porta_una_volta(self):
		visto = appuntamenti.preview(self.file.file_url)
		self.assertEqual(visto["total"], 5)
		self.assertEqual(visto["to_bring"], 3)
		self.assertEqual(visto["left_out"], 2)
		self.assertEqual(visto["nobody"], 1)
		self.assertEqual(visto["new_people"], 1)
		servizi = {s["name"]: s["choice"] for s in visto["services"]}
		self.assertEqual(servizi[SERVIZIO], SERVIZIO)
		self.assertEqual(servizi["Controllo del nuovo programma"], appuntamenti.ALTRO)
		self.assertEqual(visto["professionals"][0]["choice"], MEDICO)
		self.assertEqual(visto["rows"][4]["outcome"], "left_out")
		self.assertTrue(visto["rows"][4]["problems"])
		# nothing written yet
		self.assertFalse(
			frappe.db.exists("CRM Appointment", {"import_key": ["is", "set"], "service": SERVIZIO})
		)

		scelte = {
			"services": {s["name"]: s["choice"] for s in visto["services"]},
			"professionals": {p["name"]: p["choice"] for p in visto["professionals"]},
		}
		esito = appuntamenti.start(self.file.file_url, json.dumps(scelte))
		self.assertEqual(
			(esito["created"], esito["new_people"], esito["nobody"], esito["left_out"]), (3, 1, 1, 1)
		)
		self.assertEqual(esito["errors"], [])

		maria = frappe.db.get_value("CRM Billing Profile", {"fiscal_code": "RSSMRA82C52F205N"}, "party")
		visite = frappe.get_all(
			"CRM Appointment",
			filters={"import_key": ["is", "set"], "service": SERVIZIO},
			fields=["name", "status", "starts_on", "ends_on"],
			order_by="starts_on asc",
		)
		self.assertEqual([v.status for v in visite], ["Completed", "Cancelled"])
		self.assertEqual(str(visite[0].ends_on), "2025-03-02 10:15:00")
		prima = frappe.get_doc("CRM Appointment", visite[0].name)
		self.assertEqual(prima.participants[0].party, maria)
		self.assertEqual(prima.participants[0].status, "Attended")
		self.assertEqual(prima.staff[0].user, MEDICO)
		# the history makes a client, from then, and her last visit
		persona = frappe.db.get_value(
			"CRM Lead", maria, ["client_since", "relationship", "last_visit"], as_dict=True
		)
		self.assertEqual(str(persona.client_since)[:10], "2025-03-02")
		self.assertEqual(str(persona.last_visit), "2025-03-02")
		self.assertNotEqual(persona.relationship, "Contact")
		# to come, of a service the centre has not: «Other», booked
		futuro = frappe.get_all(
			"CRM Appointment",
			filters={"import_key": ["is", "set"], "starts_on": [">", "2099-01-01"]},
			fields=["service", "status"],
		)
		self.assertEqual(len(futuro), 1)
		self.assertEqual(futuro[0].status, "Scheduled")
		self.assertTrue(frappe.db.get_value("CRM Service", futuro[0].service, "enabled") is not None)
		# nobody heard of it
		self.assertFalse(frappe.db.exists("CRM Automation Enrollment", {"automation": self.automazione.name}))

		# the same sheet again brings nothing twice
		esito = appuntamenti.start(self.file.file_url, json.dumps(scelte))
		self.assertEqual((esito["created"], esito["already"]), (0, 3))
		self.assertEqual(appuntamenti.preview(self.file.file_url)["already"], 3)
		self.assertEqual(frappe.db.count("CRM Billing Profile", {"fiscal_code": "RSSMRA82C52F205N"}), 1)

	def test_una_scelta_che_non_c_e_non_passa(self):
		esito = appuntamenti.start(
			self.file.file_url,
			json.dumps(
				{"services": {SERVIZIO: "Servizio inventato"}, "professionals": {"x": "nessuno@x.it"}}
			),
		)
		self.assertEqual(esito["created"], 3, esito)
		altro = frappe.get_all("CRM Appointment", filters={"import_key": ["is", "set"]}, pluck="service")
		self.assertNotIn(SERVIZIO, altro)

	def test_un_foglio_alla_volta(self):
		frappe.cache.set_value(importa.CHIAVE, {"by": MANAGER})
		with self.assertRaises(frappe.ValidationError):
			appuntamenti.start(self.file.file_url, "{}")

	def test_chi_non_importa_non_vede_il_foglio(self):
		make_user("appuntamenti.nessuno@example.com")
		frappe.set_user("appuntamenti.nessuno@example.com")
		with self.assertRaises(frappe.PermissionError):
			appuntamenti.preview(self.file.file_url)
