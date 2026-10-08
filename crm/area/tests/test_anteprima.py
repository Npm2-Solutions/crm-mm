# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's preview of a person's area, on a site without the clinic.

The desk opens Anna's preview from her page before her area is open: it sees her
area as she would - her appointments, her plans - and nobody was invited or seen
in it. Sales, who open no area, cannot; a client of the area cannot either; a
colleague does not inherit the desk's preview. From the preview nothing is
changed or sent: a tick, the board read, the forms, the chat, a download, the
waiting list all answer that it is a preview. Only Anna's area is open to it.

What the desk does not read in DottorCloud keeps its place with nothing of it: a
plan with health data, which only its author reads without the clinic. Its
author, previewing, reads it, and the reading goes in the access log.
"""

from unittest import mock

import frappe

from crm.area import accesso, anteprima, api, chat, messaggi
from crm.area.tests.test_area import ANNA, DESK, OPERATORE, SALES
from crm.piani import api as piani
from crm.piani import area as area_piani
from crm.piani.tests.test_piani import PianiCase


class AnteprimaCase(PianiCase):
	def tearDown(self):
		frappe.cache.delete_value(anteprima._chiave())
		super().tearDown()

	def apri(self, user=DESK):
		self.come(user)
		return anteprima.start(self.anna.name)


class LAnteprima(AnteprimaCase):
	def test_la_segreteria_vede_l_area_prima_di_aprirla(self):
		fatto = self.apri()
		self.assertTrue(fatto["url"].endswith("/area"))
		io = api.get_me()
		self.assertEqual([p["name"] for p in io["people"]], [self.anna.name])
		self.assertEqual(io["preview"]["lead"], self.anna.name)
		self.assertIn("upcoming", api.get_appointments(self.anna.name))
		# nobody was invited, nobody was seen in the area
		self.assertFalse(frappe.db.exists(accesso.ACCESSO, {"lead": self.anna.name}))

	def test_chi_non_apre_aree_non_la_vede(self):
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			anteprima.start(self.anna.name)

	def test_un_cliente_dell_area_non_la_apre(self):
		self.invita()
		self.entra()
		with self.assertRaises(frappe.PermissionError):
			anteprima.start(self.anna.name)

	def test_un_collega_non_eredita_l_anteprima(self):
		self.apri()
		self.come(OPERATORE)
		self.assertIsNone(anteprima.in_anteprima())
		with self.assertRaises(frappe.PermissionError):
			api.get_me()

	def test_solo_l_area_della_persona_aperta(self):
		bea = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Bea", "email": "bea.anteprima@example.com"}
		).insert(ignore_permissions=True)
		self.segue(bea.name)
		self.apri()
		with self.assertRaises(frappe.PermissionError):
			api.get_appointments(bea.name)

	def test_chiusa_non_c_e_piu(self):
		self.apri()
		anteprima.stop()
		self.assertIsNone(anteprima.in_anteprima())
		with self.assertRaises(frappe.PermissionError):
			api.get_me()


class DaQuiNonSiCambiaNiente(AnteprimaCase):
	def test_ogni_scrittura_risponde_che_e_un_anteprima(self):
		piano = self.pubblica()["name"]
		self.apri()
		chiamate = {
			"tick": lambda: area_piani.log_item(self.anna.name, piano, "squat", "Done"),
			"board": lambda: messaggi.mark_read(self.anna.name),
			"forms": lambda: api.fill_forms(self.anna.name, "[]"),
			"chat": lambda: chat.ask(self.anna.name, "A che ora aprite?"),
			"invoice": lambda: api.download_invoice(self.anna.name, "nessuna"),
			"waiting": lambda: api.leave_waiting_list(self.anna.name, "nessuna"),
			"arrived": lambda: api.check_in(self.anna.name, "nessuno"),
		}
		for nome, chiamata in chiamate.items():
			with self.subTest(nome), self.assertRaises(frappe.PermissionError):
				chiamata()
		# and the plan says nothing can be ticked
		self.assertFalse(area_piani.area_plan(self.anna.name, piano)["can_log"])

	def test_i_link_per_spostare_non_ci_sono(self):
		self.apri()
		for appuntamento in api.get_appointments(self.anna.name)["upcoming"]:
			self.assertNotIn("manage_url", appuntamento)


class CioCheNonSiLegge(AnteprimaCase):
	def sanitario(self):
		"""A plan of Anna's with health data: without the clinic, its author's only."""
		piano = self.pubblica()["name"]
		frappe.db.set_value(piani.PIANO, piano, "clinical", 1)
		return piano

	def test_resta_al_suo_posto_vuoto(self):
		piano = self.sanitario()
		self.apri()
		[riga] = area_piani.area_plans(self.anna.name)["plans"]
		self.assertEqual(riga, {"name": piano, "hidden": 1})
		with self.assertRaises(frappe.PermissionError):
			area_piani.area_plan(self.anna.name, piano)
		self.assertFalse(frappe.db.exists("View Log", {"reference_name": piano}))

	def test_chi_lo_legge_lo_vede_e_resta_nel_registro(self):
		piano = self.sanitario()
		# the trainer who wrote it opens the areas of the people they follow
		self.apri(OPERATORE)
		[riga] = area_piani.area_plans(self.anna.name)["plans"]
		self.assertEqual(riga["title"], "Forza di ottobre")
		self.assertTrue(frappe.db.exists("View Log", {"reference_name": piano, "viewed_by": OPERATORE}))

	def test_quello_che_legge_senza_dati_sanitari_e_senza_registro(self):
		piano = self.pubblica()["name"]
		self.apri()
		[riga] = area_piani.area_plans(self.anna.name)["plans"]
		self.assertEqual(riga["name"], piano)
		self.assertNotIn("hidden", riga)
		self.assertFalse(frappe.db.exists("View Log", {"reference_name": piano}))


class LAreaDelCliente(AnteprimaCase):
	def test_per_anna_niente_cambia(self):
		# the preview does not touch Anna's own area: she ticks, the board is read
		piano = self.pubblica()["name"]
		self.invita()
		self.entra()
		self.assertIsNone(anteprima.in_anteprima())
		with mock.patch.object(messaggi, "_avvisa"):
			fatto = area_piani.log_item(self.anna.name, piano, "squat", "Done")
		self.assertEqual(fatto["outcome"], "Done")
		self.assertEqual(api.get_me()["preview"], None)
		self.assertEqual(frappe.session.user, ANNA)
