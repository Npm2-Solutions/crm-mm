# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The patient area: invited by the centre, in with a code, only one's own people.

The desk opens Anna's area to her address: a user of the site with the patient
role, never of the desk. A code by email lets her in, the same answer goes to an
address with no area, five wrong codes close it; staff never enter this way. In,
she sees her appointments with the booking page's link, the documents given
online (downloaded after a code verified in the last minutes) and her invoices,
and nobody else's; closed, the area refuses her.
"""

import datetime
from types import SimpleNamespace
from unittest import mock

import frappe

from crm.clinica import consegna
from crm.clinica.area import accesso, api
from crm.clinica.tests.test_cartella import DESK, DOC1, SALES
from crm.clinica.tests.test_consegna import ConsegnaCase
from crm.tests.test_scheduling import SchedulingCase

ANNA = "anna.referto@example.com"
CODICE = "246810"


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

	def entra(self):
		self.manda()
		frappe.set_user("Guest")
		accesso.verify_code(CODICE, ANNA)
		self.assertEqual(frappe.session.user, ANNA)


class LInvito(AreaCase):
	def test_la_segreteria_apre_l_area_a_un_utente_del_sito(self):
		fatto = self.invita()
		self.assertEqual(fatto["email"], ANNA)
		frappe.set_user("Administrator")
		utente = frappe.get_doc("User", ANNA)
		self.assertEqual(utente.user_type, "Website User")
		self.assertIn(accesso.RUOLO, [r.role for r in utente.roles])
		[riga] = fatto["accesses"]
		self.assertEqual((riga.user, riga.relation, riga.enabled), (ANNA, "Self", 1))

	def test_un_collega_non_diventa_paziente(self):
		with self.assertRaises(frappe.ValidationError):
			self.invita(email=DOC1)

	def test_chi_non_invita_non_apre(self):
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			accesso.invite(self.anna.name)


class LaPorta(AreaCase):
	def test_col_codice_si_entra(self):
		self.invita()
		self.entra()
		io = api.get_me()
		self.assertEqual([p["name"] for p in io["people"]], [self.anna.name])

	def test_la_stessa_risposta_per_chi_non_ha_l_area(self):
		frappe.set_user("Guest")
		prima = frappe.db.count("Email Queue")
		self.assertEqual(accesso.send_code("nessuno@example.com"), {"sent": True, "minutes": 10})
		self.assertEqual(frappe.db.count("Email Queue"), prima)

	def test_il_codice_va_per_email_e_cinque_sbagliati_chiudono(self):
		self.invita()
		self.manda()
		frappe.set_user("Administrator")
		[posta] = frappe.get_all("Email Queue", fields=["name", "message"], order_by="creation desc", limit=1)
		self.assertIn(CODICE, posta.message)
		self.assertEqual([r.recipient for r in frappe.get_doc("Email Queue", posta.name).recipients], [ANNA])
		for _volta in range(accesso.TENTATIVI):
			frappe.set_user("Guest")
			with self.assertRaises(frappe.ValidationError):
				accesso.verify_code("000000", ANNA)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.ValidationError):
			accesso.verify_code(CODICE, ANNA)
		self.assertEqual(frappe.session.user, "Guest")

	def test_lo_staff_non_entra_dall_area(self):
		frappe.set_user("Guest")
		prima = frappe.db.count("Email Queue")
		accesso.send_code(DOC1)
		self.assertEqual(frappe.db.count("Email Queue"), prima)

	def test_chiusa_non_si_entra_piu(self):
		self.invita()
		self.come(DESK)
		accesso.revoke(self.anna.name, ANNA)
		frappe.set_user(ANNA)
		with self.assertRaises(frappe.PermissionError):
			api.get_me()


class Dentro(AreaCase):
	def test_gli_appuntamenti_con_il_link_della_prenotazione(self):
		frappe.set_user("Administrator")
		medico = self.make_user("area.doctor@example.com")
		self.make_service("Visita area", [medico])
		domani = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
		self.make_appointment(
			"Visita area",
			domani,
			[medico],
			participants=[
				{"party_type": "CRM Lead", "party": self.anna.name, "participant_name": "Anna Cartella"}
			],
		)
		self.invita()
		self.entra()
		[prossimo] = api.get_appointments(self.anna.name)["upcoming"]
		self.assertEqual(prossimo["service"], "Visita area")
		self.assertIn("/prenota?token=", prossimo["manage_url"])

	def test_i_documenti_online_dopo_un_codice(self):
		self.consenso()
		self.online(send_email=0)
		self.invita()
		self.entra()
		[documento] = api.get_documents(self.anna.name)["documents"]
		self.assertEqual(documento["title"], "Esami")
		# the code verified at the door counts for the next minutes
		api.download_document(self.anna.name, documento["name"])
		self.assertEqual(frappe.local.response.filecontent, b"Esame di record.doctor1@example.com")
		# later, a code again
		frappe.cache.delete_value(accesso._chiave_verifica(frappe.session.sid))
		with self.assertRaises(frappe.PermissionError):
			api.download_document(self.anna.name, documento["name"])
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
		for chiamata in (api.get_appointments, api.get_documents, api.get_invoices):
			with self.assertRaises(frappe.PermissionError, msg=chiamata.__name__):
				chiamata(altro.name)
