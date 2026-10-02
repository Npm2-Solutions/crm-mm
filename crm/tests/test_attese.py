# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Waiting lists, in a beauty centre without the clinic (design.md, "Cosa si
aggiunge al CRM").

Chiara massages tomorrow from ten to eleven, and Anna has the place. Giulia would
like it: the desk puts her on the waiting list, and Marco after her. Anna cancels,
and the place goes to Giulia by email with a link, while Marco waits; she says yes
and the appointment is hers. Had the desk booked the hour meanwhile, the place
would have gone and Giulia would be back in the line; had she said no, or nothing
for two hours, it would go to Marco, and never to her again. With three at a time,
the first who confirms takes it. Who is in a hurry goes first; who is busy at that
hour, or cannot answer before it starts, is not offered it.

A full Pilates class: Sara waits for a seat, one frees up, and she joins that very
class; /prenota shows the class as full and takes her on the list for it, as it
takes whoever finds no time that suits, with the privacy tick in the register, and
somebody booking for their child. The desk finds the free places of an entry,
offers one or books it; the practitioner sees who waits for them, marketing does
not see the list. In her area Anna joins a list and answers an offer. An offer
goes by SMS or WhatsApp where the centre set them up, and the desk calls whoever
has no email nor mobile. A deleted person takes their entries with them.
"""

import datetime
import json
import re
from unittest import mock

import frappe
from frappe.utils import add_days, get_datetime, getdate, now_datetime

from crm.api import service_booking as SB
from crm.area import api as area_api

# modules, not classes: a TestCase imported here would run here too
from crm.area.tests import test_area as area
from crm.moduli import consensi
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.scheduling import attese as A
from crm.scheduling import attese_pubblico as P
from crm.scheduling import attese_regole as R
from crm.scheduling.availability import forget_settings
from crm.scheduling.timeutils import to_system_naive
from crm.telephony.tests.test_sms import mittente_di_prova
from crm.tests import test_scheduling as agenda

DESK = "attese.desk@example.com"
CHIARA = "attese.chiara@example.com"
LUCA = "attese.luca@example.com"
VENDITE = "attese.vendite@example.com"
MARKETING = "attese.marketing@example.com"
LIVELLI = (
	(DESK, "segreteria"),
	(CHIARA, "operatore"),
	(LUCA, "operatore"),
	(VENDITE, "commerciale"),
	(MARKETING, "marketing"),
)
LINK = re.compile(r"/lista-attesa/([A-Za-z0-9_-]+)")
MODELLO = "posto-libero-prova"


class Aiuti:
	"""The beauty centre of these tests: Chiara's one massage place tomorrow, and
	the people who want it."""

	def prepara(self):
		utenti.sincronizza()
		for user, livello in LIVELLI:
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		livelli.dimentica_cache()
		consensi.assicura_tipi()
		self.impostazioni(
			enabled=1,
			offers_at_once=1,
			hours_to_answer=2,
			min_notice_hours=0,
			days_ahead=2,
			online_join=1,
			area_join=1,
			whatsapp_template=None,
		)
		self.domani = self.tomorrow(10)
		giorno = agenda.ALL_DAYS[self.domani.weekday()]
		# one place a day: tomorrow from ten to eleven
		self.massaggio = self.make_service(
			"Massaggio in attesa",
			[CHIARA],
			bookable_online=1,
			website_slug="massaggio-in-attesa",
			availability=[{"workday": giorno, "start_time": "10:00:00", "end_time": "11:00:00"}],
		)
		self.giulia = self.persona("Giulia", "giulia.attese@example.com", "+393331110001")
		self.marco = self.persona("Marco", "marco.attese@example.com", "+393331110002")
		self.sara = self.persona("Sara", "sara.attese@example.com", "+393331110003")
		self.cliente = self.persona("Anna", "anna.attese@example.com", "+393331110009")
		self.occupato = self.appuntamento(self.cliente, self.domani)
		posta = mock.patch("frappe.sendmail")
		self.sendmail = posta.start()
		self.addCleanup(posta.stop)

	def impostazioni(self, **campi):
		doc = frappe.get_doc(A.IMPOSTAZIONI)
		doc.update(campi)
		doc.save(ignore_permissions=True)

	def online(self, **campi):
		"""The booking page open, permissive: each test says what it checks."""
		config = frappe.get_doc("CRM Scheduling Settings")
		config.update(
			{
				"online_booking_enabled": 1,
				"require_privacy_consent": 0,
				"max_active_per_customer": 0,
				"default_min_notice_hours": 0,
				"default_max_horizon_days": 30,
				"default_require_phone": 0,
				**campi,
			}
		)
		config.save()
		forget_settings()

	def persona(self, nome, email=None, cellulare=None):
		return frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": nome,
				"last_name": "Attese",
				"email": email or "",
				"mobile_no": cellulare or "",
			}
		).insert(ignore_permissions=True)

	def appuntamento(self, persona, quando, servizio=None, staff=CHIARA):
		return self.make_appointment(
			(servizio or self.massaggio).name,
			quando,
			[staff],
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

	def in_lista(self, persona, **dati):
		self.come(DESK)
		try:
			return A.save_entry(persona.name, json.dumps({"service": self.massaggio.name, **dati}))
		finally:
			frappe.set_user("Administrator")

	def annulla(self, appuntamento):
		frappe.set_user("Administrator")
		doc = frappe.get_doc("CRM Appointment", appuntamento.name)
		doc.status = "Cancelled"
		doc.save()

	def voce(self, fatto):
		return frappe.get_doc(A.VOCE, fatto["name"])

	def link(self, email):
		"""The link of the last email to ``email``."""
		for chiamata in reversed(self.sendmail.call_args_list):
			if chiamata.kwargs.get("recipients") == [email]:
				trovato = LINK.search(chiamata.kwargs.get("message") or "")
				if trovato:
					return trovato.group(1)
		self.fail(f"no link to {email}")

	def oggetti(self):
		return [chiamata.kwargs.get("subject") or "" for chiamata in self.sendmail.call_args_list]

	def da_ospite(self, funzione, *args, **kwargs):
		frappe.set_user("Guest")
		try:
			return funzione(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()


class AtteseCase(Aiuti, agenda.SchedulingCase):
	def setUp(self):
		super().setUp()
		self.prepara()

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()


class LaFila(AtteseCase):
	def test_il_posto_liberato_va_al_primo_della_fila(self):
		giulia = self.in_lista(self.giulia)
		marco = self.in_lista(self.marco)
		# nothing is free: they wait
		self.assertEqual((giulia["status"], giulia["offer"]), (R.IN_ATTESA, None))
		self.annulla(self.occupato)
		voce = self.voce(giulia)
		self.assertEqual(voce.status, R.PROPOSTA)
		[offerta] = voce.offers
		self.assertEqual((offerta.status, offerta.channel, offerta.staff), (R.INVIATA, R.EMAIL, CHIARA))
		self.assertEqual(get_datetime(offerta.starts_on), to_system_naive(self.domani))
		# two hours to answer, and never past an hour before it starts
		self.assertLessEqual(
			get_datetime(offerta.expires_on), to_system_naive(self.domani) - datetime.timedelta(hours=1)
		)
		self.assertLessEqual(
			get_datetime(offerta.expires_on), now_datetime() + datetime.timedelta(hours=2, minutes=1)
		)
		# the link is kept as its fingerprint only
		token = self.link("giulia.attese@example.com")
		self.assertEqual(offerta.token_hash, A.impronta(token))
		self.assertTrue(any("A place has freed up" in oggetto for oggetto in self.oggetti()))
		# Marco waits
		self.assertEqual((self.voce(marco).status, self.voce(marco).offers), (R.IN_ATTESA, []))

	def test_tre_alla_volta_il_primo_che_conferma(self):
		self.impostazioni(offers_at_once=3)
		voci = [self.in_lista(persona) for persona in (self.giulia, self.marco, self.sara)]
		self.annulla(self.occupato)
		self.assertEqual({self.voce(v).status for v in voci}, {R.PROPOSTA})
		# Marco is the quickest
		esito = self.da_ospite(P.confirm_offer, self.link("marco.attese@example.com"))
		self.assertEqual(esito["result"], "booked")
		for fatto in (voci[0], voci[2]):
			voce = self.voce(fatto)
			self.assertEqual((voce.status, voce.offers[0].status), (R.IN_ATTESA, R.PRESA))
		# Giulia's link now says the place has gone, and she is still on the list
		vista = self.da_ospite(P.open_offer, self.link("giulia.attese@example.com"))
		self.assertEqual((vista["offer"]["status"], vista["can_leave"]), (R.PRESA, True))

	def test_chi_ha_fretta_passa_avanti(self):
		giulia = self.in_lista(self.giulia)
		marco = self.in_lista(self.marco, urgent=1)
		self.annulla(self.occupato)
		self.assertEqual((self.voce(marco).status, self.voce(giulia).status), (R.PROPOSTA, R.IN_ATTESA))

	def test_non_a_chi_a_quell_ora_e_occupato(self):
		pulizia = self.make_service("Pulizia viso in attesa", [LUCA])
		self.appuntamento(self.giulia, self.domani, servizio=pulizia, staff=LUCA)
		giulia = self.in_lista(self.giulia)
		marco = self.in_lista(self.marco)
		self.annulla(self.occupato)
		self.assertEqual((self.voce(giulia).status, self.voce(marco).status), (R.IN_ATTESA, R.PROPOSTA))

	def test_troppo_vicino_non_si_propone(self):
		self.impostazioni(min_notice_hours=48)
		giulia = self.in_lista(self.giulia)
		self.annulla(self.occupato)
		self.assertEqual(self.voce(giulia).status, R.IN_ATTESA)

	def test_solo_nei_giorni_che_puo(self):
		# Giulia can only in the evenings: the place at ten is not for her
		giulia = self.in_lista(self.giulia, parts=["evening"])
		marco = self.in_lista(self.marco, parts=["morning"])
		self.annulla(self.occupato)
		self.assertEqual((self.voce(giulia).status, self.voce(marco).status), (R.IN_ATTESA, R.PROPOSTA))
		self.assertEqual(self.voce(giulia).days[0].start_time, datetime.timedelta(hours=18))

	def test_spostato_o_eliminato_libera_l_ora(self):
		giulia = self.in_lista(self.giulia)
		doc = frappe.get_doc("CRM Appointment", self.occupato.name)
		doc.starts_on = to_system_naive(self.domani + datetime.timedelta(days=1))
		doc.ends_on = None
		doc.save()
		self.assertEqual(self.voce(giulia).status, R.PROPOSTA)

	def test_eliminato(self):
		giulia = self.in_lista(self.giulia)
		frappe.delete_doc("CRM Appointment", self.occupato.name, ignore_permissions=True)
		self.assertEqual(self.voce(giulia).status, R.PROPOSTA)


class LaRisposta(AtteseCase):
	def test_si_e_l_appuntamento_e_suo(self):
		giulia = self.in_lista(self.giulia)
		self.annulla(self.occupato)
		esito = self.da_ospite(P.confirm_offer, self.link("giulia.attese@example.com"))
		self.assertEqual(esito["result"], "booked")
		voce = self.voce(giulia)
		self.assertEqual(voce.status, R.PRENOTATA)
		appuntamento = frappe.get_doc("CRM Appointment", voce.booked_appointment)
		self.assertEqual(
			(appuntamento.status, appuntamento.source, appuntamento.service),
			("Confirmed", "Online", self.massaggio.name),
		)
		self.assertEqual([r.user for r in appuntamento.staff], [CHIARA])
		[riga] = appuntamento.participants
		self.assertEqual(
			(riga.party, riga.booked_online, riga.email), (self.giulia.name, 1, "giulia.attese@example.com")
		)
		self.assertEqual(
			(voce.offers[0].status, voce.offers[0].appointment), (R.ACCETTATA, appuntamento.name)
		)
		# the page shows the booking; the email says it is booked
		self.assertEqual(esito["booked"]["start"], self.domani.isoformat())
		self.assertTrue(any("Your appointment is booked" in oggetto for oggetto in self.oggetti()))
		# a second yes books nothing more
		di_nuovo = self.da_ospite(P.confirm_offer, self.link("giulia.attese@example.com"))
		self.assertEqual(
			frappe.db.count("CRM Appointment", {"service": self.massaggio.name, "status": "Confirmed"}), 1
		)
		self.assertTrue(di_nuovo["booked"])

	def test_se_qualcuno_e_stato_piu_veloce(self):
		giulia = self.in_lista(self.giulia)
		self.annulla(self.occupato)
		token = self.link("giulia.attese@example.com")
		# the desk books the same hour on the calendar meanwhile
		self.appuntamento(self.sara, self.domani)
		esito = self.da_ospite(P.confirm_offer, token)
		self.assertEqual(esito["result"], "taken")
		voce = self.voce(giulia)
		self.assertEqual(
			(voce.status, voce.offers[0].status, voce.booked_appointment), (R.IN_ATTESA, R.PRESA, None)
		)

	def test_aprendo_il_link_si_vede_che_il_posto_e_andato(self):
		giulia = self.in_lista(self.giulia)
		self.annulla(self.occupato)
		self.appuntamento(self.sara, self.domani)
		vista = self.da_ospite(P.open_offer, self.link("giulia.attese@example.com"))
		self.assertEqual(vista["offer"]["status"], R.PRESA)
		self.assertFalse(vista["offer"]["can_answer"])
		self.assertEqual(self.voce(giulia).status, R.IN_ATTESA)

	def test_no_grazie_e_il_posto_va_al_prossimo(self):
		giulia = self.in_lista(self.giulia)
		marco = self.in_lista(self.marco)
		self.annulla(self.occupato)
		self.da_ospite(P.decline_offer, self.link("giulia.attese@example.com"))
		voce = self.voce(giulia)
		self.assertEqual((voce.status, voce.offers[0].status), (R.IN_ATTESA, R.RIFIUTATA))
		self.assertEqual(self.voce(marco).status, R.PROPOSTA)
		# and the same place is never offered to her again
		self.da_ospite(P.decline_offer, self.link("marco.attese@example.com"))
		A.cerca()
		self.assertEqual(len(self.voce(giulia).offers), 1)

	def test_senza_risposta_passa_al_prossimo(self):
		giulia = self.in_lista(self.giulia)
		marco = self.in_lista(self.marco)
		self.annulla(self.occupato)
		[offerta] = self.voce(giulia).offers
		frappe.db.set_value(A.OFFERTA, offerta.name, "expires_on", add_days(now_datetime(), -1))
		frappe.cache.delete_value(A.CHIAVE_GIRO)
		A.ogni_dieci_minuti()
		voce = self.voce(giulia)
		self.assertEqual((voce.status, voce.offers[0].status), (R.IN_ATTESA, R.SENZA_RISPOSTA))
		self.assertEqual(self.voce(marco).status, R.PROPOSTA)

	def test_esce_dalla_lista(self):
		giulia = self.in_lista(self.giulia)
		marco = self.in_lista(self.marco)
		self.annulla(self.occupato)
		vista = self.da_ospite(P.leave_list, self.link("giulia.attese@example.com"))
		self.assertEqual((vista["status"], vista["can_leave"]), (R.TOLTA, False))
		self.assertEqual(self.voce(giulia).offers[0].status, R.RIFIUTATA)
		self.assertEqual(self.voce(marco).status, R.PROPOSTA)

	def test_un_link_che_non_c_e(self):
		for token in ("", "corto", "x" * 40, "y" * 200):
			with self.assertRaises(frappe.PermissionError):
				self.da_ospite(P.open_offer, token)

	def test_l_ultimo_giorno_passato(self):
		# the centre's day, not the server's: they differ for hours around midnight
		oggi = A._oggi()
		giulia = self.in_lista(self.giulia, until=str(oggi + datetime.timedelta(days=3)))
		frappe.db.set_value(A.VOCE, giulia["name"], "until", oggi - datetime.timedelta(days=1))
		A.chiudi_scadute()
		self.assertEqual(self.voce(giulia).status, R.SCADUTA)


class LaLezione(AtteseCase):
	def setUp(self):
		super().setUp()
		self.pilates = self.make_service(
			"Pilates in attesa",
			[CHIARA],
			max_participants=2,
			bookable_online=1,
			website_slug="pilates-in-attesa",
		)
		self.lezione = self.make_appointment(
			self.pilates.name,
			self.tomorrow(18),
			[CHIARA],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": p.name,
					"participant_name": p.lead_name,
					"status": "Booked",
				}
				for p in (self.cliente, self.marco)
			],
		)

	def test_un_posto_nella_lezione_piena(self):
		sara = self.in_lista(self.sara, service=self.pilates.name, class_session=self.lezione.name)
		self.assertEqual(sara["status"], R.IN_ATTESA)
		# Marco cannot come: his seat frees up
		doc = frappe.get_doc("CRM Appointment", self.lezione.name)
		doc.participants[1].status = "Cancelled"
		doc.save()
		voce = self.voce(sara)
		self.assertEqual((voce.status, voce.offers[0].class_session), (R.PROPOSTA, self.lezione.name))
		esito = self.da_ospite(P.confirm_offer, self.link("sara.attese@example.com"))
		self.assertEqual(esito["result"], "booked")
		# the same class, not a new one
		self.assertEqual(self.voce(sara).booked_appointment, self.lezione.name)
		persone = [
			r.party
			for r in frappe.get_doc("CRM Appointment", self.lezione.name).participants
			if r.status != "Cancelled"
		]
		self.assertEqual(persone, [self.cliente.name, self.sara.name])

	def test_da_prenota_si_vede_piena_e_si_entra_in_lista(self):
		self.online(require_privacy_consent=1)
		giorno = str(getdate(self.tomorrow(18)))
		fatto = self.da_ospite(SB.get_slots_public, "pilates-in-attesa", giorno, giorno)
		[piena] = fatto["full"][giorno]
		self.assertEqual(piena["session"], A.id_pubblico(self.lezione.name))
		self.assertNotIn(self.lezione.name, json.dumps(fatto))
		entrato = self.da_ospite(
			P.join_waiting_list,
			service="pilates-in-attesa",
			full_name="Sara Attese",
			email="sara.attese@example.com",
			session=piena["session"],
			consent=1,
			consent_text="Ho letto l'informativa",
		)
		self.assertTrue(LINK.search(entrato["link"]))
		voce = frappe.get_doc(A.VOCE, {"lead": self.sara.name})
		self.assertEqual((voce.class_session, voce.source, voce.days), (self.lezione.name, R.ONLINE, []))
		# a seat in a class is waited for until the class
		self.assertEqual(getdate(voce.until), self.tomorrow(18).date())
		# the tick is in the register, with the entry it came with
		self.assertTrue(
			frappe.db.exists(
				"CRM Consent",
				{
					"lead": self.sara.name,
					"consent_type": "privacy_notice",
					"source_doctype": A.VOCE,
					"source_name": voce.name,
				},
			)
		)


class DaPrenota(AtteseCase):
	def setUp(self):
		super().setUp()
		self.online()

	def entra(self, **dati):
		dati = {
			"service": "massaggio-in-attesa",
			"full_name": "Paola Nuova",
			"email": "paola.attese@example.com",
			"days": json.dumps(["Monday", "Wednesday"]),
			"parts": json.dumps(["morning"]),
			**dati,
		}
		return self.da_ospite(P.join_waiting_list, **dati)

	def test_chi_non_trova_un_orario_entra_in_lista(self):
		self.assertEqual(self.da_ospite(SB.get_catalog)["waiting_list"]["channels"], [R.EMAIL])
		entrato = self.entra()
		lead = frappe.db.get_value("CRM Lead", {"email": "paola.attese@example.com"}, "name")
		voce = frappe.get_doc(A.VOCE, {"lead": lead})
		self.assertEqual((voce.source, voce.channel, voce.contact), (R.ONLINE, R.EMAIL, None))
		self.assertEqual(R.scelte_da(voce.days), {"days": ["Monday", "Wednesday"], "parts": ["morning"]})
		self.assertEqual(getdate(voce.until), A._oggi() + datetime.timedelta(days=30))
		self.assertEqual(voce.token_hash, A.impronta(LINK.search(entrato["link"]).group(1)))
		self.assertTrue(any("You are on the waiting list" in oggetto for oggetto in self.oggetti()))
		# the page of the link shows what she waits for
		vista = self.da_ospite(P.open_offer, LINK.search(entrato["link"]).group(1))
		self.assertEqual(
			(vista["status"], vista["choice"]["parts"], vista["offer"]), (R.IN_ATTESA, ["morning"], None)
		)

	def test_col_telefono_di_un_familiare(self):
		# the phone is Giulia's and the name is new: a record of Nina's own, linked
		# to Giulia and without contacts, as a booking makes it; the entry keeps
		# what Nina typed, and the offers go there
		self.entra(
			full_name="Nina Attese",
			email="nina.attese@example.com",
			phone="+39 333 111 0001",
			days="[]",
			parts="[]",
		)
		voce = frappe.get_doc(A.VOCE, {"email": "nina.attese@example.com"})
		self.assertNotEqual(voce.lead, self.giulia.name)
		self.assertEqual(A._destinatario(voce)[1:], ("nina.attese@example.com", "+393331110001"))
		self.annulla(self.occupato)
		self.assertEqual(frappe.db.get_value(A.VOCE, voce.name, "status"), R.PROPOSTA)
		self.assertTrue(self.link("nina.attese@example.com"))

	def test_una_voce_sola_per_servizio(self):
		self.entra()
		self.entra(parts=json.dumps(["evening"]))
		lead = frappe.db.get_value("CRM Lead", {"email": "paola.attese@example.com"}, "name")
		[voce] = frappe.get_all(A.VOCE, filters={"lead": lead}, pluck="name")
		self.assertEqual(R.scelte_da(frappe.get_doc(A.VOCE, voce).days)["parts"], ["evening"])

	def test_per_un_figlio(self):
		self.entra(for_name="Leo Nuovo", for_relation="Parent")
		madre = frappe.db.get_value("CRM Lead", {"email": "paola.attese@example.com"}, "name")
		voce = frappe.get_doc(A.VOCE, {"contact": madre})
		self.assertEqual(frappe.db.get_value("CRM Lead", voce.lead, "lead_name"), "Leo Nuovo")
		self.assertNotEqual(voce.lead, madre)

	def test_se_il_centro_non_la_offre(self):
		self.impostazioni(online_join=0)
		self.assertIsNone(self.da_ospite(SB.get_catalog)["waiting_list"])
		with self.assertRaises(frappe.PermissionError):
			self.entra()

	def test_un_ultimo_giorno_che_non_si_puo(self):
		with self.assertRaises(frappe.ValidationError):
			self.entra(until=str(A._oggi() - datetime.timedelta(days=1)))


class IlBanco(AtteseCase):
	def test_la_segreteria_trova_il_posto_e_lo_fissa(self):
		self.impostazioni(enabled=0)
		giulia = self.in_lista(self.giulia, notes="Preferisce Chiara")
		self.annulla(self.occupato)
		# nothing leaves by itself: the desk looks
		self.assertEqual(self.voce(giulia).status, R.IN_ATTESA)
		self.come(DESK)
		[posto] = A.find_places(giulia["name"])["places"]
		self.assertEqual((posto["staff"], posto["offered"]), ([CHIARA], 0))
		fatto = A.book_place(giulia["name"], posto["start"])
		self.assertEqual(fatto["status"], R.PRENOTATA)
		appuntamento = frappe.get_doc("CRM Appointment", fatto["appointment"])
		self.assertEqual((appuntamento.source, appuntamento.participants[0].booked_online), ("Internal", 0))
		self.assertEqual(appuntamento.owner, DESK)

	def test_la_segreteria_propone_a_mano(self):
		self.impostazioni(enabled=0)
		giulia = self.in_lista(self.giulia)
		self.annulla(self.occupato)
		self.come(DESK)
		[posto] = A.find_places(giulia["name"])["places"]
		fatto = A.offer_place(giulia["name"], posto["start"])
		self.assertEqual(fatto["status"], R.PROPOSTA)
		self.assertEqual((fatto["offer"]["channel"], fatto["offer"]["offered_by"]), (R.EMAIL, "attese.desk"))
		# one offer at a time
		with self.assertRaises(frappe.ValidationError):
			A.offer_place(giulia["name"], posto["start"])

	def test_toglie_dalla_lista(self):
		giulia = self.in_lista(self.giulia)
		self.come(DESK)
		self.assertEqual(A.remove_entry(giulia["name"])["status"], R.TOLTA)
		self.assertEqual(A.get_entries(self.giulia.name)["entries"][0]["status"], R.TOLTA)

	def test_chi_non_fa_il_servizio(self):
		with self.assertRaises(frappe.ValidationError):
			self.in_lista(self.giulia, staff=LUCA)


class ChiLaVede(AtteseCase):
	def setUp(self):
		super().setUp()
		self.pulizia = self.make_service("Pulizia viso in attesa", [LUCA])
		self.di_giulia = self.in_lista(self.giulia)["name"]
		self.di_marco = self.in_lista(self.marco, service=self.pulizia.name)["name"]

	def nomi(self, user):
		"""The entries of these tests ``user`` reads: a site may hold others."""
		self.come(user)
		try:
			return {v["name"] for v in A.get_waiting_list()["entries"]} & {self.di_giulia, self.di_marco}
		finally:
			frappe.set_user("Administrator")

	def test_la_segreteria_tutti_l_operatore_i_suoi(self):
		self.assertEqual(self.nomi(DESK), {self.di_giulia, self.di_marco})
		self.assertEqual(self.nomi(CHIARA), {self.di_giulia})
		self.assertEqual(self.nomi(LUCA), {self.di_marco})

	def test_il_commerciale_le_sue_persone(self):
		self.assertEqual(self.nomi(VENDITE), set())
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"reference_type": "CRM Lead",
				"reference_name": self.giulia.name,
				"allocated_to": VENDITE,
				"description": "Attese",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(self.nomi(VENDITE), {self.di_giulia})

	def test_il_marketing_no(self):
		self.come(MARKETING)
		with self.assertRaises(frappe.PermissionError):
			A.get_waiting_list()
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(A.VOCE, self.di_giulia).check_permission("read")

	def test_le_impostazioni_del_manager(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			A.save_settings(json.dumps({"offers_at_once": 5}))


class ICanali(AtteseCase):
	def test_sms_col_link(self):
		# the offers leave from the centre's one sender (doc 52)
		mittente_di_prova(numero="+390212345678")
		giulia = self.in_lista(self.giulia, channel="SMS")
		with mock.patch("crm.api.sms.deliver_via_twilio") as consegna:
			self.annulla(self.occupato)
		[sms] = consegna.call_args.args
		self.assertEqual((sms.get("from"), sms.to), ("+390212345678", "+393331110001"))
		self.assertIn("/lista-attesa/", sms.message)
		self.assertEqual(self.voce(giulia).offers[0].channel, R.SMS)

	def test_chi_ha_scritto_stop_la_riceve_per_email(self):
		# a STOP to the centre's SMS is heard by the waiting list too (doc 52)
		mittente_di_prova(numero="+390212345678")
		frappe.db.set_value("CRM Lead", self.giulia.name, "sms_opt_out", 1)
		giulia = self.in_lista(self.giulia, channel="SMS")
		with mock.patch("crm.api.sms.deliver_via_twilio") as consegna:
			self.annulla(self.occupato)
		consegna.assert_not_called()
		self.assertEqual(self.voce(giulia).offers[0].channel, R.EMAIL)

	def test_whatsapp_col_link_nelle_variabili(self):
		if not frappe.db.exists("DocType", "WhatsApp Templates"):
			self.skipTest("frappe_whatsapp is not installed")
		if not frappe.db.exists("WhatsApp Templates", MODELLO):
			modello = frappe.get_doc(
				{
					"doctype": "WhatsApp Templates",
					"name": MODELLO,
					"template_name": MODELLO,
					"template": "Ciao {{1}}, si è liberato un posto per {{2}}, {{3}}: {{4}}",
					"language": frappe.db.get_value("Language", {}, "name") or "it",
					"category": "UTILITY",
					"status": "APPROVED",
				}
			)
			# as it is after Meta approved it: nothing is asked of Meta here
			modello.db_insert()
		self.impostazioni(whatsapp_template=MODELLO)
		giulia = self.in_lista(self.giulia, channel="WhatsApp")
		with mock.patch("crm.api.whatsapp.insert_and_send") as spedisce:
			self.annulla(self.occupato)
		[doc] = spedisce.call_args.args
		variabili = list(json.loads(doc.body_param).values())
		self.assertEqual(variabili[:2], ["Giulia", "Massaggio in attesa"])
		self.assertIn("/lista-attesa/", variabili[3])
		self.assertEqual(json.loads(doc.template_parameters), variabili)
		self.assertEqual((doc.to, doc.reference_name), ("+393331110001", self.giulia.name))
		self.assertEqual(self.voce(giulia).offers[0].channel, R.WHATSAPP)

	def test_senza_recapiti_chiama_la_segreteria(self):
		nessuno = self.persona("Nessuno")
		voce = self.in_lista(nessuno)
		self.annulla(self.occupato)
		[offerta] = self.voce(voce).offers
		self.assertEqual((offerta.status, offerta.channel), (R.INVIATA, ""))
		self.assertIn("call them", offerta.delivery)


class LaPersonaCancellata(AtteseCase):
	def test_se_ne_va_con_le_sue_voci(self):
		# the automations of the test site keep a person from going: the hook is
		# asked directly, as the deletion does before anything else
		giulia = self.in_lista(self.giulia)
		leo = self.persona("Leo")
		per_leo = self.in_lista(leo, contact=self.giulia.name)
		self.assertIn(
			"crm.scheduling.attese.cancella_con_la_persona",
			frappe.get_hooks("doc_events")["CRM Lead"]["on_trash"],
		)
		A.cancella_con_la_persona(frappe.get_doc("CRM Lead", self.giulia.name))
		self.assertFalse(frappe.db.exists(A.VOCE, giulia["name"]))
		self.assertIsNone(frappe.db.get_value(A.VOCE, per_leo["name"], "contact"))

	def test_un_appuntamento_eliminato_lascia_le_liste(self):
		giulia = self.in_lista(self.giulia)
		self.annulla(self.occupato)
		esito = self.da_ospite(P.confirm_offer, self.link("giulia.attese@example.com"))
		self.assertTrue(esito["booked"])
		# without letting go, the entry's links would keep the appointment from going
		frappe.delete_doc("CRM Appointment", self.voce(giulia).booked_appointment, ignore_permissions=True)
		voce = self.voce(giulia)
		self.assertEqual(
			(voce.status, voce.booked_appointment, voce.offers[0].appointment), (R.PRENOTATA, None, None)
		)


class DallArea(Aiuti, area.AreaCase):
	def setUp(self):
		super().setUp()
		self.prepara()
		self.invita()
		self.entra()

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()

	def test_entra_in_lista_e_risponde(self):
		opzioni = area_api.get_waiting_options(self.anna.name)
		self.assertIn(self.massaggio.name, [s["name"] for s in opzioni["services"]])
		[voce] = area_api.join_waiting_list(
			self.anna.name, self.massaggio.name, parts=json.dumps(["morning"])
		)["waiting"]
		self.assertEqual((voce["status"], voce["offer"]), (R.IN_ATTESA, None))
		self.annulla(self.occupato)
		self.come(area.ANNA)
		[voce] = area_api.get_appointments(self.anna.name)["waiting"]
		self.assertTrue(voce["offer"]["can_answer"])
		esito = area_api.answer_waiting_offer(self.anna.name, voce["name"], "yes")
		self.assertEqual((esito["result"], esito["waiting"]), ("booked", []))
		[prossimo] = area_api.get_appointments(self.anna.name)["upcoming"]
		self.assertEqual(prossimo["service"], "Massaggio in attesa")

	def test_la_lista_degli_altri_no(self):
		di_giulia = self.in_lista(self.giulia)["name"]
		self.come(area.ANNA)
		with self.assertRaises(frappe.PermissionError):
			area_api.leave_waiting_list(self.anna.name, di_giulia)
		with self.assertRaises(frappe.PermissionError):
			area_api.join_waiting_list(self.giulia.name, self.massaggio.name)
