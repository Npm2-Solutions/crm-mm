# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The client area on a site without the clinic: invited by the centre, in with a
code, only one's own people.

A beauty centre or a gym has it as a medical centre does. The desk opens Anna's
area to her address: a user of the site with the area's role, never of the desk.
A code by email lets her in, the same answer goes to an address with no area, five
wrong codes close it; staff never enter this way. In, she sees her appointments
with the booking page's link and her cycles of sessions, her invoices, and nobody
else's; closed, the area refuses her.

Preparing the appointment, she fills the forms the centre asks on the forms page,
with no code (she came in with one); taken up again they keep their answers; a
parent signs for her, who only follows her does not. The desk writes on her board:
the email says only that there is news, and opening the board reads what was new.

Documents and plans show to who has some, and the words are the CRM's own without
the clinic; the base comprises the area, so only a plan without the base closes it.
"""

import datetime
import json
from types import SimpleNamespace
from unittest import mock

import frappe

from crm import verticali
from crm.area import accesso, api, messaggi
from crm.moduli import consensi, richieste, traccia
from crm.moduli.tests.test_compilazioni import PRIVACY, CompilazioniCase
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.persone import collegate, legami
from crm.tests.test_scheduling import SchedulingCase

ANNA = "anna.area@example.com"
CODICE = "246810"
PADRE = "marco.area@example.com"
CARLA = "carla.area@example.com"
DESK = "area.desk@example.com"
OPERATORE = "area.operator@example.com"
MANAGER = "area.manager@example.com"
SALES = "area.sales@example.com"
LIVELLI = ((DESK, "segreteria"), (OPERATORE, "operatore"), (MANAGER, "manager"), (SALES, "commerciale"))


class AreaCase(SchedulingCase):
	#: The plan of these tests: the client area, and no clinic.
	MODULI = ({"module": "area", "status": "Active"},)

	def setUp(self):
		SchedulingCase.setUp(self)
		self.piano(*self.MODULI)
		utenti.sincronizza()
		for user, livello in LIVELLI:
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		consensi.assicura_tipi()
		frappe.local.outgoing_email_account = {}
		posta = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Centro Area",
				"email_id": "centro.area@example.com",
				"enable_outgoing": 1,
				"default_outgoing": 1,
			}
		)
		posta.flags.ignore_mandatory = True
		posta.flags.ignore_validate = True
		posta.insert(ignore_permissions=True)
		stili = mock.patch("frappe.utils.get_assets_json", return_value={})
		stili.start()
		self.addCleanup(stili.stop)
		self.anna = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Anna", "last_name": "Area", "email": ANNA}
		).insert(ignore_permissions=True)
		self.segue(self.anna.name)
		# no request in a test: logging in is setting the user
		entrata = SimpleNamespace(login_as=frappe.set_user)
		patch = mock.patch.object(frappe.local, "login_manager", entrata, create=True)
		patch.start()
		self.addCleanup(patch.stop)
		frappe.cache.delete_value(accesso._chiave_codice(ANNA))
		livelli.dimentica_cache()

	def tearDown(self):
		SchedulingCase.tearDown(self)
		frappe.local.outgoing_email_account = {}
		livelli.dimentica_cache()

	def piano(self, *moduli):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", list(moduli))
		piano.save()
		livelli.dimentica_cache()

	def segue(self, lead):
		# everybody works on the person: the area's own rules are what is tested
		for user, _livello in LIVELLI:
			frappe.get_doc(
				{
					"doctype": "ToDo",
					"reference_type": "CRM Lead",
					"reference_name": lead,
					"allocated_to": user,
					"description": "Area",
				}
			).insert(ignore_permissions=True)

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

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

	def test_un_collega_non_entra_dall_area(self):
		with self.assertRaises(frappe.ValidationError):
			self.invita(email=OPERATORE)

	def test_chi_non_invita_non_apre(self):
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			accesso.invite(self.anna.name)

	def test_la_base_comprende_l_area_anche_se_il_piano_la_spegne(self):
		# every centre has it (05/10/2026): the plan's word on the area alone does
		# not take it away
		self.piano({"module": "area", "status": "Off"})
		self.assertEqual(self.invita()["email"], ANNA)

	def test_senza_la_base_nessuno_la_apre(self):
		self.piano({"module": "base", "status": "Off"}, {"module": "area", "status": "Off"})
		self.come(DESK)
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

	def test_il_cookie_di_una_sessione_finita_non_porta_via_la_nuova(self):
		# the browser kept the cookie of a session the server ended: resuming it as a
		# guest, the framework asks its cookies away, and at the end of the request it
		# deletes after it sets - the right code led back to the door
		from frappe.auth import CookieManager

		self.invita()
		self.manda()
		gestore = CookieManager()
		gestore.delete_cookie(["sid", "user_id", "full_name"])

		def entra(utente):
			frappe.set_user(utente)
			gestore.set_cookie("sid", "la-nuova")
			gestore.set_cookie("user_id", utente)

		with (
			mock.patch.object(frappe.local, "cookie_manager", gestore, create=True),
			mock.patch.object(frappe.local.login_manager, "login_as", entra),
		):
			frappe.set_user("Guest")
			accesso.verify_code(CODICE, ANNA)
		self.assertEqual(gestore.cookies["sid"]["value"], "la-nuova")
		self.assertNotIn("sid", gestore.to_delete)
		self.assertNotIn("user_id", gestore.to_delete)
		# what the new session did not set goes, as the framework asked
		self.assertIn("full_name", gestore.to_delete)

	def test_lo_staff_non_entra_dall_area(self):
		frappe.set_user("Guest")
		prima = frappe.db.count("Email Queue")
		accesso.send_code(OPERATORE)
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
		estetista = self.make_user("area.estetista@example.com")
		self.make_service("Trattamento area", [estetista])
		domani = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
		self.make_appointment(
			"Trattamento area",
			domani,
			[estetista],
			participants=[
				{"party_type": "CRM Lead", "party": self.anna.name, "participant_name": "Anna Area"}
			],
		)
		self.invita()
		self.entra()
		[prossimo] = api.get_appointments(self.anna.name)["upcoming"]
		self.assertEqual(prossimo["service"], "Trattamento area")
		self.assertIn("/prenota?token=", prossimo["manage_url"])

	def test_i_cicli_di_sedute_e_a_che_seduta_e(self):
		frappe.set_user("Administrator")
		estetista = self.make_user("area.laser@example.com")
		servizio = self.make_service("Laser area", [estetista])
		frappe.get_doc(
			{
				"doctype": "CRM Session Cycle",
				"lead": self.anna.name,
				"service": servizio.name,
				"sessions": 3,
				"price": 90,
				"notes": "Per la segreteria",
			}
		).insert()
		domani = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
		self.make_appointment(
			servizio.name,
			domani,
			[estetista],
			participants=[
				{"party_type": "CRM Lead", "party": self.anna.name, "participant_name": "Anna Area"}
			],
		)
		self.invita()
		self.entra()
		fatto = api.get_appointments(self.anna.name)
		[prossimo] = fatto["upcoming"]
		self.assertEqual(prossimo["session"], {"number": 1, "total": 3})
		[ciclo] = fatto["cycles"]
		self.assertEqual(
			(ciclo["service"], ciclo["counts"]["booked"], ciclo["counts"]["left"]),
			("Laser area", 1, 2),
		)
		# what the centre keeps for itself stays there
		self.assertFalse({"price", "notes", "invoice"} & set(ciclo))

	def test_niente_di_altri(self):
		self.invita()
		self.entra()
		frappe.set_user("Administrator")
		altro = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Bruno", "last_name": "Altro"}).insert(
			ignore_permissions=True
		)
		frappe.set_user(ANNA)
		for chiamata in (api.get_appointments, api.get_invoices, api.get_forms):
			with self.assertRaises(frappe.PermissionError, msg=chiamata.__name__):
				chiamata(altro.name)


class PrenotaDiNuovo(AreaCase):
	"""«Book again»: the booking page on the last service, and the page knows who
	comes from the area without anybody typing again."""

	def prepara(self, online=1):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("CRM Scheduling Settings", "online_booking_enabled", 1)
		if hasattr(frappe.local, "crm_scheduling_settings"):
			del frappe.local.crm_scheduling_settings
		estetista = self.make_user("area.ripeti@example.com")
		self.make_service("Pulizia area", [estetista], bookable_online=online, website_slug="pulizia-area")
		ieri = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
		self.make_appointment(
			"Pulizia area",
			ieri,
			[estetista],
			status="Completed",
			participants=[
				{"party_type": "CRM Lead", "party": self.anna.name, "participant_name": "Anna Area"}
			],
		)
		self.invita()
		self.entra()

	def test_il_servizio_dell_ultimo_appuntamento(self):
		self.prepara()
		prenota = api.get_appointments(self.anna.name)["book"]
		self.assertEqual(prenota["service"], "Pulizia area")
		self.assertEqual(prenota["url"], f"/prenota/pulizia-area?persona={self.anna.name}")

	def test_un_servizio_che_non_si_prenota_online_porta_al_catalogo(self):
		self.prepara(online=0)
		prenota = api.get_appointments(self.anna.name)["book"]
		self.assertEqual(prenota, {"url": f"/prenota?persona={self.anna.name}", "service": None})

	def test_senza_prenotazione_online_niente(self):
		self.prepara()
		frappe.db.set_single_value("CRM Scheduling Settings", "online_booking_enabled", 0)
		if hasattr(frappe.local, "crm_scheduling_settings"):
			del frappe.local.crm_scheduling_settings
		frappe.set_user(ANNA)
		self.assertIsNone(api.get_appointments(self.anna.name)["book"])

	def test_la_pagina_sa_chi_prenota_dalla_sessione(self):
		self.prepara()
		frappe.db.set_value("CRM Lead", self.anna.name, "mobile_no", "+393331112233")
		dati = api.per_la_pagina_di_prenotazione(self.anna.name)
		self.assertEqual(dati, {"full_name": "Anna Area", "email": ANNA, "phone": "+393331112233"})
		# somebody else's person, or nobody signed in: the empty form
		frappe.set_user("Administrator")
		altro = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Bruno", "last_name": "Altro"}).insert(
			ignore_permissions=True
		)
		frappe.set_user(ANNA)
		self.assertEqual(api.per_la_pagina_di_prenotazione(altro.name), {})
		frappe.set_user("Guest")
		self.assertEqual(api.per_la_pagina_di_prenotazione(self.anna.name), {})


class SonoArrivato(AreaCase):
	"""«I'm here» from Anna's phone: from half an hour before her appointment until
	it ends, her own, and the desk is told."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.estetista = self.make_user("area.arrivo@example.com")
		self.servizio = self.make_service("Arrivo area", [self.estetista])
		self.invita()

	def appuntamento(self, fra_minuti, persona=None):
		frappe.set_user("Administrator")
		persona = persona or self.anna
		inizio = datetime.datetime.now(datetime.UTC).replace(second=0, microsecond=0) + datetime.timedelta(
			minutes=fra_minuti
		)
		return self.make_appointment(
			self.servizio.name,
			inizio,
			[self.estetista],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": persona.name,
					"participant_name": persona.lead_name,
					"status": "Booked",
				}
			],
		)

	def posto(self, appuntamento):
		return frappe.db.get_value(
			"CRM Appointment Participant",
			{"parent": appuntamento.name},
			["status", "arrived_at"],
			as_dict=True,
		)

	def test_poco_prima_entra_in_sala_d_attesa_e_l_accoglienza_lo_sa(self):
		from crm.notifiche import regole as N

		appuntamento = self.appuntamento(10)
		self.entra()
		[prossimo] = api.get_appointments(self.anna.name)["upcoming"]
		self.assertEqual(prossimo["check_in"]["opens_in"], 0)
		self.assertFalse(prossimo["arrived"])
		self.assertEqual(api.check_in(self.anna.name, appuntamento.name), {"arrived": True})
		posto = self.posto(appuntamento)
		self.assertEqual(posto.status, "Arrived")
		self.assertTrue(posto.arrived_at)
		self.assertTrue(
			frappe.db.exists(
				"CRM Notification",
				{
					"to_user": DESK,
					"sentence": N.ARRIVATO_DALL_AREA,
					"notification_type_doc": appuntamento.name,
				},
			)
		)
		# said again, nothing changes
		self.assertEqual(api.check_in(self.anna.name, appuntamento.name), {"arrived": True})
		[prossimo] = api.get_appointments(self.anna.name)["upcoming"]
		self.assertTrue(prossimo["arrived"])
		self.assertNotIn("check_in", prossimo)

	def test_iniziato_si_puo_ancora_dire(self):
		appuntamento = self.appuntamento(-5)
		self.entra()
		[prossimo] = api.get_appointments(self.anna.name)["upcoming"]
		self.assertEqual(prossimo["name"], appuntamento.name)
		api.check_in(self.anna.name, appuntamento.name)
		self.assertEqual(self.posto(appuntamento).status, "Arrived")

	def test_troppo_presto_no(self):
		appuntamento = self.appuntamento(120)
		self.entra()
		[prossimo] = api.get_appointments(self.anna.name)["upcoming"]
		self.assertGreater(prossimo["check_in"]["opens_in"], 80 * 60)
		with self.assertRaises(frappe.ValidationError):
			api.check_in(self.anna.name, appuntamento.name)
		self.assertEqual(self.posto(appuntamento).status, "Booked")

	def test_l_appuntamento_di_un_altro_no(self):
		bruno = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Bruno", "last_name": "Arrivo"}).insert(
			ignore_permissions=True
		)
		suo = self.appuntamento(10, bruno)
		self.entra()
		with self.assertRaises(frappe.PermissionError):
			api.check_in(self.anna.name, suo.name)
		with self.assertRaises(frappe.PermissionError):
			api.check_in(bruno.name, suo.name)
		self.assertEqual(self.posto(suo).status, "Booked")

	def test_annullato_o_spento_no(self):
		appuntamento = self.appuntamento(10)
		frappe.db.set_single_value("CRM Area Settings", "self_check_in", 0)
		self.entra()
		self.assertNotIn("check_in", api.get_appointments(self.anna.name)["upcoming"][0])
		with self.assertRaises(frappe.ValidationError):
			api.check_in(self.anna.name, appuntamento.name)
		frappe.db.set_single_value("CRM Area Settings", "self_check_in", 1)
		frappe.db.set_value("CRM Appointment", appuntamento.name, "status", "Cancelled")
		with self.assertRaises(frappe.ValidationError):
			api.check_in(self.anna.name, appuntamento.name)


class SenzaLaClinica(AreaCase):
	def test_niente_della_clinica_e_le_parole_del_crm(self):
		self.invita()
		self.entra()
		[persona] = api.get_me()["people"]
		# nothing given online, no plan: their places answer nothing
		self.assertFalse(persona["sections"].get("documents"))
		self.assertFalse(persona["sections"].get("plans"))
		frappe.set_user("Administrator")
		self.assertIsNone(verticali.attiva())
		self.assertEqual(verticali.parole(), {})
		self.assertEqual(verticali.parola("Client area"), frappe._("Client area"))


class PreparaLAppuntamento(AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.scheda = CompilazioniCase.pubblica(PRIVACY, "Scheda area")
		frappe.db.set_value("CRM Form Template", self.scheda, "ask_on", "First appointment")

	def dovuto(self):
		[voce] = [f for f in api.get_forms(self.anna.name)["forms"] if f["template"] == self.scheda]
		return voce

	def compila(self):
		return api.fill_forms(self.anna.name, json.dumps([self.scheda]))

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
			(self.scheda, "Link", self.anna.name, None, ANNA),
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
		self.invita(relation=accesso.SEGUE, email="figlia.area@example.com")
		self.entra("figlia.area@example.com")
		fatto = api.get_forms(self.anna.name)
		self.assertEqual((fatto["can_fill"], fatto["why_not"]), (False, "follows"))
		with self.assertRaises(frappe.PermissionError):
			self.compila()


class IMessaggi(AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.carla = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Carla", "last_name": "Bacheca", "email": CARLA}
		).insert(ignore_permissions=True)
		self.segue(self.carla.name)
		frappe.cache.delete_value(accesso._chiave_codice(CARLA))
		self.come(DESK)
		accesso.invite(self.carla.name)

	def scrivi(self, chi, testo):
		self.come(chi)
		return messaggi.post_message(self.carla.name, testo)

	def test_la_segreteria_scrive_la_mail_dice_solo_che_c_e_una_novita(self):
		frappe.set_user("Administrator")
		prima = frappe.db.count("Email Queue")
		[messaggio] = self.scrivi(DESK, "Porti il contratto firmato")["messages"]
		self.assertEqual(messaggio["kind"], messaggi.AMMINISTRATIVO)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count("Email Queue"), prima + 1)
		posta = frappe.get_last_doc("Email Queue")
		self.assertEqual([r.recipient for r in posta.recipients], [CARLA])
		self.assertNotIn("contratto", posta.message)

	def test_senza_la_clinica_anche_l_operatore_scrive_all_amministrazione(self):
		[messaggio] = self.scrivi(OPERATORE, "Ci vediamo giovedì")["messages"]
		self.assertEqual(messaggio["kind"], messaggi.AMMINISTRATIVO)
		self.come(DESK)
		[letto] = messaggi.get_messages(self.carla.name)["messages"]
		self.assertEqual(letto["body"], "Ci vediamo giovedì")

	def test_nell_area_si_legge_e_si_segna_letto(self):
		self.scrivi(DESK, "Porti la tessera")
		self.entra(CARLA)
		[persona] = api.get_me()["people"]
		self.assertEqual(persona["unread"], 1)
		[messaggio] = messaggi.area_messages(self.carla.name)["messages"]
		self.assertEqual(messaggio["body"], "Porti la tessera")
		self.assertNotIn("mine", messaggio)
		messaggi.mark_read(self.carla.name)
		self.assertEqual(api.get_me()["people"][0]["unread"], 0)
		self.come(DESK)
		[letto] = messaggi.get_messages(self.carla.name)["messages"]
		self.assertTrue(letto["read_on"])

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


class IlDaPagare(AreaCase):
	"""What is left to pay of each invoice, the total and how the centre is paid:
	never a test invoice, nothing for one collected."""

	def fattura(self, **valori):
		from crm.invoicing.install import semina_qualifiche
		from crm.tests.test_invoicing import CF_PAZIENTE, InvoicingBase

		frappe.set_user("Administrator")
		semina_qualifiche()
		azienda = InvoicingBase.crea_azienda()
		erogatore = InvoicingBase.crea_erogatore("Studio Neri", "societa_servizi")
		servizio = InvoicingBase.crea_servizio("Consulenza", healthcare=False, exempt=False)
		documento = frappe.get_doc(
			{
				"doctype": "CRM Invoice",
				"company": azienda.name,
				"recipient_type": "persona_fisica",
				"party_type": "CRM Lead",
				"party": self.anna.name,
				"billing_name": "Anna Area",
				"first_name": "Anna",
				"last_name": "Area",
				"fiscal_code": CF_PAZIENTE,
				"address_line": "Via Verdi 3",
				"postal_code": "00100",
				"city": "Roma",
				"province": "RM",
				"payment_method": "MP05",
				"items": [
					{
						"billable_service": servizio.name,
						"service_provider": erogatore.name,
						"qty": 1,
						"rate": 65,
					}
				],
			}
		).insert()
		documento.submit()
		frappe.db.set_value(
			"CRM Invoice", documento.name, {"collected_on": None, "test_document": 0, **valori}
		)
		return documento.name

	def test_quanto_resta_e_come_si_paga(self):
		da_pagare = self.fattura()
		pagata = self.fattura(collected_on=frappe.utils.today())
		di_prova = self.fattura(test_document=1)
		frappe.db.set_single_value(
			"CRM Payment Reminder Settings", "how_to_pay", "IBAN IT60X0542811101000000123456"
		)
		self.invita()
		self.entra()
		fatto = api.get_invoices(self.anna.name)
		righe = {riga["name"]: riga for riga in fatto["invoices"]}
		self.assertNotIn(di_prova, righe)
		self.assertEqual(righe[pagata]["to_pay"], 0)
		self.assertGreater(righe[da_pagare]["to_pay"], 0)
		self.assertEqual(fatto["to_pay"], righe[da_pagare]["to_pay"])
		self.assertIn("IT60X0542811101000000123456", fatto["how_to_pay"])

		# in the centre's preview, an invoice the previewer does not read does not count
		from crm.area import anteprima

		with mock.patch.object(
			api.anteprima,
			"filtra",
			side_effect=lambda doctype, righe: [
				anteprima.coperta(riga) if riga["name"] == da_pagare else riga for riga in righe
			],
		):
			nascosta = api.get_invoices(self.anna.name)
		self.assertEqual(nascosta["to_pay"], 0)
		self.assertEqual(nascosta["how_to_pay"], "")

		# all paid: nothing to say on how to pay
		frappe.set_user("Administrator")
		frappe.db.set_value("CRM Invoice", da_pagare, "collected_on", frappe.utils.today())
		frappe.set_user(ANNA)
		self.assertEqual(api.get_invoices(self.anna.name)["to_pay"], 0)
