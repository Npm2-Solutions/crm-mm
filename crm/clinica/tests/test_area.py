# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The client area with the clinic on: the patient area (`crm.area` is the CRM's;
its own tests are in `crm/area/tests`).

The clinic comprises the area: with the clinic alone in the plan the desk opens
Anna's area. Inside, the documents given online are hers, downloaded after a code
verified in the last minutes, and nobody else's. A practitioner writes about the
care on her board: read like a visit, and it makes her a patient; the desk's
message does not. DottorCloud and the area say patients, not clients.
"""

from types import SimpleNamespace
from unittest import mock

import frappe

from crm import verticali
from crm.api import plan
from crm.area import accesso, api, messaggi
from crm.clinica import paziente
from crm.clinica.tests.test_cartella import DESK, DOC1, MANAGER
from crm.clinica.tests.test_consegna import ConsegnaCase
from crm.documenti import area as documenti
from crm.documenti import consegna
from crm.permissions import livelli
from crm.tests.test_scheduling import SchedulingCase

ANNA = "anna.referto@example.com"
CODICE = "246810"
PADRE = "marco.genitore@example.com"
CARLA = "carla.bacheca@example.com"


class AreaCase(ConsegnaCase, SchedulingCase):
	def setUp(self):
		SchedulingCase.setUp(self)
		ConsegnaCase.setUp(self)
		# no request in a test: logging in is setting the user
		entrata = SimpleNamespace(login_as=frappe.set_user)
		patch = mock.patch.object(frappe.local, "login_manager", entrata, create=True)
		patch.start()
		self.addCleanup(patch.stop)
		frappe.cache.delete_value(accesso._chiave_codice(ANNA))

	def tearDown(self):
		ConsegnaCase.tearDown(self)
		SchedulingCase.tearDown(self)

	def invita(self, **altro):
		self.come(DESK)
		return accesso.invite(self.anna.name, **altro)

	def manda(self, email=ANNA, codice=CODICE):
		frappe.set_user("Guest")
		with mock.patch.object(accesso, "_codice", return_value=codice):
			return accesso.send_code(email)

	def entra(self, email=ANNA):
		self.manda(email)
		frappe.set_user("Guest")
		accesso.verify_code(CODICE, email)
		self.assertEqual(frappe.session.user, email)


class LaClinicaComprendeLArea(AreaCase):
	def test_con_la_sola_clinica_nel_piano_l_area_c_e(self):
		fatto = self.invita()
		self.assertEqual(fatto["email"], ANNA)
		# the manager reads the plan: the area is there, as part of the clinic
		self.come(MANAGER)
		[area] = [m for m in plan.get_plan()["modules"] if m["key"] == "area"]
		self.assertEqual((area["state"], area["comprised_by"]), ("active", ["Clinic"]))


class IDocumenti(AreaCase):
	def test_i_documenti_online_dopo_un_codice(self):
		self.consenso()
		self.online(send_email=0)
		self.invita()
		self.entra()
		[persona] = api.get_me()["people"]
		self.assertTrue(persona["sections"]["documents"])
		[documento] = documenti.get_documents(self.anna.name)["documents"]
		self.assertEqual(documento["title"], "Esami")
		# the code verified at the door counts for the next minutes
		documenti.download_document(self.anna.name, documento["name"])
		self.assertEqual(frappe.local.response.filecontent, b"Esame di record.doctor1@example.com")
		# later, a code again
		frappe.cache.delete_value(accesso._chiave_verifica(frappe.session.sid))
		with self.assertRaises(frappe.PermissionError):
			documenti.download_document(self.anna.name, documento["name"])
		frappe.set_user("Administrator")
		self.assertEqual(
			frappe.db.get_value(consegna.CONSEGNA, documento["name"], "status"), consegna.SCARICATO
		)

	def test_niente_di_altri(self):
		self.invita()
		self.entra()
		frappe.set_user("Administrator")
		altro = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Bruno", "last_name": "Altro"}).insert(
			ignore_permissions=True
		)
		frappe.set_user(ANNA)
		with self.assertRaises(frappe.PermissionError):
			documenti.get_documents(altro.name)


class IMessaggiDellaCura(AreaCase):
	def setUp(self):
		super().setUp()
		# somebody who is not a patient yet, followed by the desk and a doctor
		frappe.set_user("Administrator")
		self.carla = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Carla", "last_name": "Bacheca", "email": CARLA}
		).insert(ignore_permissions=True)
		for user in (DESK, DOC1):
			frappe.get_doc(
				{
					"doctype": "ToDo",
					"reference_type": "CRM Lead",
					"reference_name": self.carla.name,
					"allocated_to": user,
					"description": "Carla",
				}
			).insert(ignore_permissions=True)
		frappe.cache.delete_value(accesso._chiave_codice(CARLA))
		self.come(DESK)
		accesso.invite(self.carla.name)

	def scrivi(self, chi, testo):
		self.come(chi)
		return messaggi.post_message(self.carla.name, testo)

	def test_il_messaggio_della_segreteria_non_fa_paziente(self):
		[messaggio] = self.scrivi(DESK, "Porti le analisi del sangue")["messages"]
		self.assertEqual(messaggio["kind"], messaggi.AMMINISTRATIVO)
		frappe.set_user("Administrator")
		self.assertFalse(paziente.e_paziente(self.carla.name))

	def test_della_cura_scrive_il_medico_e_si_legge_come_una_visita(self):
		[messaggio] = self.scrivi(DOC1, "Riduca il caffè")["messages"]
		self.assertEqual(messaggio["kind"], "Care")
		# health data: Carla is a patient now, and the desk does not read it
		frappe.set_user("Administrator")
		self.assertTrue(paziente.e_paziente(self.carla.name))
		self.assertEqual(frappe.db.get_value(messaggi.MESSAGGIO, messaggio["name"], "practitioner"), DOC1)
		self.come(DESK)
		self.assertEqual(messaggi.get_messages(self.carla.name)["messages"], [])
		self.entra(CARLA)
		[letto] = messaggi.area_messages(self.carla.name)["messages"]
		self.assertEqual(letto["body"], "Riduca il caffè")


class LeParoleDellaClinica(AreaCase):
	def test_dottorcloud_e_l_area_dicono_pazienti(self):
		frappe.set_user("Administrator")
		livelli.dimentica_cache()
		self.assertEqual(verticali.attiva().chiave, "clinica")
		self.assertEqual(verticali.parole()["Client area"], "Patient area")
		# the page of DottorCloud reads "Client area" as the clinic says it
		from crm.www import crm as pagina

		self.assertEqual(pagina.get_translated_messages()["Client area"], frappe._("Patient area"))
		self.assertEqual(pagina.get_vertical()["key"], "clinica")
		# the area's own dictionary gets the pairs
		from crm.www import area as pagina_area

		self.assertEqual(
			pagina_area._parole()["This area is for the centre's clients."],
			"This area is for the centre's patients.",
		)

	def test_la_clinica_indossa_dottorcloud(self):
		from crm import marchio

		frappe.set_user("Administrator")
		livelli.dimentica_cache()
		self.assertEqual(verticali.attiva().marchio, marchio.DOTTORCLOUD.chiave)
		self.assertEqual(marchio.attivo(), marchio.DOTTORCLOUD)
		self.assertEqual(marchio.per_le_pagine()["name"], "DottorCloud")
