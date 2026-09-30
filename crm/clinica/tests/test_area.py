# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The patient area: invited by the centre, in with a code, only one's own people.

The desk opens Anna's area to her address: a user of the site with the patient
role, never of the desk. A code by email lets her in, the same answer goes to an
address with no area, five wrong codes close it; staff never enter this way. In,
she sees her appointments with the booking page's link, the documents given
online (downloaded after a code verified in the last minutes) and her invoices,
and nobody else's; closed, the area refuses her.

Preparing the visit, she fills the forms the centre asks on the forms page, with
no code (she came in with one), and taken up again they keep their answers; a
parent signs for her, who only follows her does not. The centre writes on her
board: the email says only that there is news, a message about the care is read
like a visit, and opening the board reads what was new.
"""

import datetime
import json
from types import SimpleNamespace
from unittest import mock

import frappe

from crm.clinica import consegna, paziente
from crm.clinica.area import accesso, api, messaggi
from crm.clinica.tests.test_cartella import DESK, DOC1, SALES
from crm.clinica.tests.test_consegna import ConsegnaCase
from crm.moduli import consensi, richieste, traccia
from crm.moduli.tests.test_compilazioni import PRIVACY, CompilazioniCase
from crm.persone import collegate, legami
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


class PreparaLaVisita(AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		consensi.assicura_tipi()
		self.anamnesi = CompilazioniCase.pubblica(PRIVACY, "Anamnesi area")
		frappe.db.set_value("CRM Form Template", self.anamnesi, "ask_on", "First appointment")

	def dovuto(self):
		[voce] = [f for f in api.get_forms(self.anna.name)["forms"] if f["template"] == self.anamnesi]
		return voce

	def compila(self):
		return api.fill_forms(self.anna.name, json.dumps([self.anamnesi]))

	def test_si_compila_dall_area_senza_un_altro_codice(self):
		self.invita()
		self.entra()
		self.assertEqual((self.dovuto()["pending"], self.dovuto()["fill"]), (None, True))
		aperto = self.compila()
		self.assertEqual(aperto["url"], f"/modulo/{aperto['token']}")
		# the page opens with the session the area gave: no code asked
		frappe.set_user("Guest")
		richieste.open_request(aperto["token"])
		[voce] = richieste.get_request_forms(aperto["token"], session=aperto["session"])["forms"]
		frappe.set_user("Administrator")
		richiesta = frappe.get_doc(richieste.RICHIESTA, voce["id"])
		self.assertEqual(
			(
				richiesta.template,
				richiesta.channel,
				richiesta.recipient,
				richiesta.given_by,
				richiesta.sent_by,
			),
			(self.anamnesi, "Link", self.anna.name, None, ANNA),
		)
		self.assertTrue(richiesta.sent_to.startswith("a") and richiesta.sent_to.endswith("@example.com"))
		self.assertIn(
			api.DALL_AREA,
			frappe.get_all(
				traccia.REGISTRO,
				filters={"reference_name": richiesta.name, "event": "sent"},
				pluck="detail",
			),
		)

	def test_ripreso_resta_lo_stesso_e_il_vecchio_link_non_vale(self):
		self.invita()
		self.entra()
		primo = self.compila()
		self.assertEqual(self.dovuto()["pending"], "sent")
		secondo = self.compila()
		self.assertNotEqual(primo["token"], secondo["token"])
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count(richieste.RICHIESTA, {"lead": self.anna.name}), 1)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			richieste.open_request(primo["token"])
		richieste.open_request(secondo["token"])

	def test_solo_quello_che_il_centro_chiede(self):
		self.invita()
		self.entra()
		with self.assertRaises(frappe.ValidationError):
			api.fill_forms(self.anna.name, json.dumps(["nessun-modello"]))

	def test_il_genitore_firma_per_lei_chi_la_segue_no(self):
		frappe.set_user("Administrator")
		padre = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Marco", "last_name": "Genitore", "email": PADRE}
		).insert(ignore_permissions=True)
		collegate.assicura_legame(self.anna.name, padre.name, legami.GENITORE, represents=1)
		self.invita(relation=accesso.TUTORE)
		self.invita(relation=accesso.SE_STESSO)
		# Anna has a parent who answers for her: she sees her forms, and does not sign them
		self.entra()
		fatto = api.get_forms(self.anna.name)
		self.assertEqual(
			(fatto["can_fill"], fatto["why_not"], self.dovuto()["fill"]), (False, "parent", False)
		)
		with self.assertRaises(frappe.PermissionError):
			self.compila()
		# her father does
		frappe.set_user("Administrator")
		frappe.cache.delete_value(accesso._chiave_codice(PADRE))
		self.entra(PADRE)
		self.assertTrue(api.get_forms(self.anna.name)["can_fill"])
		aperto = self.compila()
		frappe.set_user("Administrator")
		richiesta = frappe.get_doc(richieste.RICHIESTA, {"token_hash": richieste._impronta(aperto["token"])})
		self.assertEqual((richiesta.given_by, richiesta.recipient), (padre.name, padre.name))

	def test_chi_la_segue_vede_e_non_firma(self):
		self.invita(relation=accesso.SEGUE, email="figlia.segue@example.com")
		self.entra("figlia.segue@example.com")
		fatto = api.get_forms(self.anna.name)
		self.assertEqual((fatto["can_fill"], fatto["why_not"]), (False, "follows"))
		with self.assertRaises(frappe.PermissionError):
			self.compila()


class IMessaggi(AreaCase):
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

	def test_la_segreteria_scrive_la_mail_dice_solo_che_c_e_una_novita(self):
		frappe.set_user("Administrator")
		prima = frappe.db.count("Email Queue")
		[messaggio] = self.scrivi(DESK, "Porti le analisi del sangue")["messages"]
		self.assertEqual(messaggio["kind"], messaggi.AMMINISTRATIVO)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count("Email Queue"), prima + 1)
		posta = frappe.get_last_doc("Email Queue")
		self.assertEqual([r.recipient for r in posta.recipients], [CARLA])
		self.assertNotIn("analisi", posta.message)
		# the desk's message is not health data: nobody becomes a patient for it
		self.assertFalse(paziente.e_paziente(self.carla.name))

	def test_nell_area_si_legge_e_si_segna_letto(self):
		self.scrivi(DESK, "Porti la tessera sanitaria")
		self.entra(CARLA)
		[persona] = api.get_me()["people"]
		self.assertEqual(persona["unread"], 1)
		[messaggio] = messaggi.area_messages(self.carla.name)["messages"]
		self.assertEqual(messaggio["body"], "Porti la tessera sanitaria")
		self.assertNotIn("mine", messaggio)
		messaggi.mark_read(self.carla.name)
		self.assertEqual(api.get_me()["people"][0]["unread"], 0)
		self.come(DESK)
		[letto] = messaggi.get_messages(self.carla.name)["messages"]
		self.assertTrue(letto["read_on"])

	def test_della_cura_scrive_il_medico_e_si_legge_come_una_visita(self):
		[messaggio] = self.scrivi(DOC1, "Riduca il caffè")["messages"]
		self.assertEqual(messaggio["kind"], messaggi.CURA)
		# health data: Carla is a patient now, and the desk does not read it
		frappe.set_user("Administrator")
		self.assertTrue(paziente.e_paziente(self.carla.name))
		self.come(DESK)
		self.assertEqual(messaggi.get_messages(self.carla.name)["messages"], [])
		self.entra(CARLA)
		[letto] = messaggi.area_messages(self.carla.name)["messages"]
		self.assertEqual(letto["body"], "Riduca il caffè")

	def test_non_si_riscrive_e_non_scrive_chi_non_puo(self):
		[messaggio] = self.scrivi(DESK, "Domani alle 9")["messages"]
		frappe.set_user("Administrator")
		doc = frappe.get_doc(messaggi.MESSAGGIO, messaggio["name"])
		doc.body = "Domani alle 10"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.PermissionError):
			self.scrivi(SALES, "Offerta")

	def test_niente_bacheche_di_altri(self):
		self.entra(CARLA)
		for chiamata in (messaggi.area_messages, messaggi.mark_read):
			with self.assertRaises(frappe.PermissionError, msg=chiamata.__name__):
				chiamata(self.anna.name)
