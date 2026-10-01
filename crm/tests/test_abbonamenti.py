# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Subscriptions (design.md, "Cosa si aggiunge al CRM": "gli abbonamenti"), in a gym
without the clinic.

The gym sells two types: "Open", a month of the weights room and pilates as often as
one likes, paid at once; "Twice a week", three months of pilates twice a week, paid
by the month, that can be suspended and renews by itself. Giulia buys one: her
pilates appointments use its entries by themselves and cost nothing, two a week,
the third is priced by the price list; a cancellation gives the entry back, a missed
one is used, personal training is not comprised, a cycle comes first. A new
subscription takes what she had booked; a suspension moves the end and lets go of
the appointments in it. On each instalment's day an invoice of the subscription
opens by itself, and the entries leave the appointments to invoice. Before the end
she is reminded; one that renews by itself starts again the day after. The trainer
reads the subscriptions of their appointments, marketing does not sell them, and
the area shows Giulia what is left this week.
"""

import datetime
import json

import frappe
from frappe.utils import add_days, getdate

from crm.area import api as area_api
from crm.area.tests import test_area as area
from crm.invoicing import api as fatture
from crm.invoicing.install import semina_qualifiche
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.scheduling import abbonamenti as A
from crm.scheduling import abbonamenti_regole as R
from crm.scheduling import cicli

# modules, not classes: a TestCase imported here would run here too
from crm.tests import test_invoicing as fatturazione
from crm.tests.test_scheduling import SchedulingCase

DESK = "abbonamenti.desk@example.com"
COACH = "abbonamenti.coach@example.com"
ALTRO = "abbonamenti.altro@example.com"
MARKETING = "abbonamenti.marketing@example.com"
UTC = datetime.timezone.utc


class AbbonamentiCase(SchedulingCase):
	def setUp(self):
		super().setUp()
		utenti.sincronizza()
		for user, livello in (
			(DESK, "segreteria"),
			(COACH, "operatore"),
			(ALTRO, "operatore"),
			(MARKETING, "marketing"),
		):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		livelli.dimentica_cache()
		self.pilates = self.make_service(
			"Pilates in abbonamento", [COACH, ALTRO], default_price=20, currency="EUR"
		)
		self.pesi = self.make_service("Sala pesi in abbonamento", [COACH], default_price=10, currency="EUR")
		self.personal = self.make_service("Personal training", [COACH], default_price=50, currency="EUR")
		self.giulia = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Giulia",
				"last_name": "Abbonata",
				"email": "giulia.abbonata@example.com",
			}
		).insert(ignore_permissions=True)
		self.open = A.save_type(
			json.dumps(
				{
					"type_name": "Open in prova",
					"months": 1,
					"price": 60,
					"currency": "EUR",
					"payment": R.SUBITO,
					"services": [self.pilates.name, self.pesi.name],
					"entries": R.ILLIMITATI,
				}
			)
		)["name"]
		self.due = A.save_type(
			json.dumps(
				{
					"type_name": "Due a settimana in prova",
					"months": 3,
					"price": 270,
					"currency": "EUR",
					"payment": R.MENSILE,
					"services": [self.pilates.name],
					"entries": R.A_SETTIMANA,
					"entries_count": 2,
					"can_suspend": 1,
					"max_suspension_days": 14,
					"remind_days": 7,
					"auto_renew": 1,
				}
			)
		)["name"]

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def lunedi(self, settimane=1, giorni=0, ora=10):
		"""Monday ``settimane`` weeks on (1: the next one), ``giorni`` after it, at
		``ora``."""
		oggi = datetime.datetime.now(UTC).date()
		lunedi = oggi + datetime.timedelta(days=7 - oggi.weekday() + 7 * (settimane - 1) + giorni)
		return datetime.datetime.combine(lunedi, datetime.time(ora), tzinfo=UTC)

	def vendi(self, tipo=None, **dati):
		self.come(DESK)
		try:
			return A.sell_subscription(
				self.giulia.name, json.dumps({"subscription_type": tipo or self.due, **dati})
			)
		finally:
			frappe.set_user("Administrator")

	def lezione(self, quando, servizio=None, staff=COACH):
		return self.make_appointment(
			(servizio or self.pilates).name,
			quando,
			[staff],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": self.giulia.name,
					"participant_name": self.giulia.lead_name,
					"status": "Booked",
				}
			],
		)

	def esito(self, appuntamento, stato):
		doc = frappe.get_doc("CRM Appointment", appuntamento.name)
		doc.participants[0].status = stato
		doc.save()

	def annulla(self, appuntamento):
		doc = frappe.get_doc("CRM Appointment", appuntamento.name)
		doc.status = "Cancelled"
		doc.save()

	def prezzo(self, appuntamento):
		return frappe.db.get_value("CRM Appointment", appuntamento.name, ["subscription", "total_amount"])

	def letto(self, nome):
		self.come(DESK)
		try:
			return A.get_subscription(nome)
		finally:
			frappe.set_user("Administrator")


class GliIngressi(AbbonamentiCase):
	def test_due_a_settimana_e_la_terza_si_paga(self):
		fatto = self.vendi()
		prima = self.lezione(self.lunedi())
		seconda = self.lezione(self.lunedi(giorni=1))
		self.assertEqual(self.prezzo(prima), (fatto["name"], 0))
		self.assertEqual(self.prezzo(seconda), (fatto["name"], 0))
		self.assertIn(
			"Due a settimana in prova", frappe.db.get_value("CRM Appointment", prima.name, "price_source")
		)
		# the week's two are used: the third is priced by the price list
		self.assertEqual(self.prezzo(self.lezione(self.lunedi(giorni=2))), (None, 20))
		# the next week has its own two
		self.assertEqual(self.prezzo(self.lezione(self.lunedi(2))), (fatto["name"], 0))
		# another service is not comprised
		self.assertEqual(self.prezzo(self.lezione(self.lunedi(giorni=3), servizio=self.personal)), (None, 50))

	def test_una_disdetta_rende_l_ingresso_e_una_assenza_lo_usa(self):
		fatto = self.vendi()
		prima = self.lezione(self.lunedi())
		self.lezione(self.lunedi(giorni=1))
		self.annulla(prima)
		self.assertEqual(self.prezzo(self.lezione(self.lunedi(giorni=2))), (fatto["name"], 0))
		# a missed entry is used: the week is full again
		self.esito(frappe.get_doc("CRM Appointment", self.lezione(self.lunedi(2)).name), "No Show")
		self.lezione(self.lunedi(2, giorni=1))
		self.assertEqual(self.prezzo(self.lezione(self.lunedi(2, giorni=2))), (None, 20))
		letto = self.letto(fatto["name"])
		self.assertEqual(
			[a["state"] for a in letto["appointments"]], ["cancelled", "booked", "booked", "missed", "booked"]
		)

	def test_open_quante_volte_si_vuole(self):
		fatto = self.vendi(self.open)
		for giorni in range(4):
			self.assertEqual(self.prezzo(self.lezione(self.lunedi(giorni=giorni))), (fatto["name"], 0))
		self.assertEqual(
			self.prezzo(self.lezione(self.lunedi(giorni=4), servizio=self.pesi)), (fatto["name"], 0)
		)
		self.assertIsNone(self.letto(fatto["name"])["used"])

	def test_un_ciclo_viene_prima(self):
		self.vendi()
		self.come(DESK)
		ciclo = cicli.save_cycle(
			self.giulia.name, json.dumps({"service": self.pilates.name, "sessions": 5, "price": 100})
		)
		frappe.set_user("Administrator")
		lezione = self.lezione(self.lunedi())
		self.assertEqual(
			frappe.db.get_value(
				"CRM Appointment", lezione.name, ["session_cycle", "subscription", "total_amount"]
			),
			(ciclo["name"], None, 20),
		)

	def test_finito_non_prende_altro(self):
		fatto = self.vendi(self.open, starts_on=str(add_days(getdate(), -40)))
		self.assertEqual(fatto["status"], R.SCADUTO)
		self.assertEqual(self.prezzo(self.lezione(self.lunedi())), (None, 20))

	def test_un_abbonamento_nuovo_prende_quello_che_era_prenotato(self):
		prima, seconda, terza = (self.lezione(self.lunedi(giorni=g)) for g in (0, 1, 2))
		fatto = self.vendi()
		self.assertEqual(self.prezzo(prima), (fatto["name"], 0))
		self.assertEqual(self.prezzo(seconda), (fatto["name"], 0))
		# two a week: the third stays as it was
		self.assertEqual(self.prezzo(terza), (None, 20))

	def test_a_mano_dentro_e_fuori_e_chiuso(self):
		fatto = self.vendi()
		lezione = self.lezione(self.lunedi())
		self.come(DESK)
		A.attach(lezione.name, None)
		self.assertEqual(self.prezzo(lezione), (None, 20))
		pannello = A.attach(lezione.name, fatto["name"])
		self.assertEqual(self.prezzo(lezione), (fatto["name"], 0))
		self.assertEqual(pannello["subscription"], fatto["name"])
		personal = self.lezione(self.lunedi(giorni=1), servizio=self.personal)
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			A.attach(personal.name, fatto["name"])
		# closed, nothing new uses it; open again, it does
		A.close_subscription(fatto["name"])
		frappe.set_user("Administrator")
		self.assertEqual(self.prezzo(self.lezione(self.lunedi(2))), (None, 20))
		self.come(DESK)
		A.reopen_subscription(fatto["name"])
		frappe.set_user("Administrator")
		self.assertEqual(self.prezzo(self.lezione(self.lunedi(2, giorni=1))), (fatto["name"], 0))

	def test_sbagliato_si_cancella_finche_niente_e_usato(self):
		fatto = self.vendi()
		lezione = self.lezione(self.lunedi())
		self.come(DESK)
		A.delete_subscription(fatto["name"])
		self.assertFalse(frappe.db.exists(A.ABBONAMENTO, fatto["name"]))
		self.assertEqual(self.prezzo(lezione), (None, 20))
		usato = self.vendi(self.open, starts_on=str(add_days(getdate(), -3)))
		venuta = self.lezione(
			datetime.datetime.combine(add_days(getdate(), -1), datetime.time(10), tzinfo=UTC)
		)
		self.esito(venuta, "Attended")
		self.assertEqual(self.prezzo(venuta)[0], usato["name"])
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			A.delete_subscription(usato["name"])


class IGiorni(AbbonamentiCase):
	def test_la_fine_e_le_rate(self):
		oggi = getdate()
		fatto = self.vendi(starts_on=str(oggi))
		self.assertEqual(getdate(fatto["ends_on"]), R.fine(oggi, 3))
		self.assertEqual(
			[(getdate(r["due_on"]), r["amount"]) for r in fatto["instalments"]],
			[(R.piu_mesi(oggi, i), 90.0) for i in range(3)],
		)
		# another price at the sale: the instalments follow
		altro = self.vendi(starts_on=str(oggi), price=240)
		self.assertEqual([r["amount"] for r in altro["instalments"]], [80.0, 80.0, 80.0])
		# paid at once: one
		subito = self.vendi(starts_on=str(oggi), payment=R.SUBITO)
		self.assertEqual([r["amount"] for r in subito["instalments"]], [270.0])

	def test_la_sospensione_sposta_la_fine_e_lascia_gli_appuntamenti(self):
		fatto = self.vendi()
		lezione = self.lezione(self.lunedi(2))
		self.assertEqual(self.prezzo(lezione)[0], fatto["name"])
		da, a = self.lunedi(2).date(), self.lunedi(2, giorni=6).date()
		self.come(DESK)
		sospeso = A.suspend_subscription(fatto["name"], str(da), str(a), "Una distorsione")
		frappe.set_user("Administrator")
		self.assertEqual(getdate(sospeso["ends_on"]), getdate(fatto["ends_on"]) + datetime.timedelta(days=7))
		# what was booked in those days lets go of it, and nothing new joins
		self.assertEqual(self.prezzo(lezione), (None, 20))
		self.assertEqual(self.prezzo(self.lezione(self.lunedi(2, giorni=2))), (None, 20))
		self.assertEqual(self.prezzo(self.lezione(self.lunedi(3)))[0], fatto["name"])
		# more than the type allows
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			A.suspend_subscription(fatto["name"], str(self.lunedi(4).date()), str(self.lunedi(5).date()))
		# taken away, the end comes back
		tolto = A.remove_suspension(fatto["name"], sospeso["suspensions"][0]["name"])
		self.assertEqual(tolto["ends_on"], fatto["ends_on"])

	def test_sospeso_oggi_e_un_tipo_che_non_si_sospende(self):
		fatto = self.vendi(starts_on=str(add_days(getdate(), -5)))
		self.come(DESK)
		sospeso = A.suspend_subscription(
			fatto["name"], str(add_days(getdate(), -1)), str(add_days(getdate(), 3))
		)
		self.assertEqual(
			(sospeso["status"], sospeso["suspended_until"]), (R.SOSPESO, str(add_days(getdate(), 3)))
		)
		self.assertEqual(frappe.db.get_value(A.ABBONAMENTO, fatto["name"], "status"), R.SOSPESO)
		aperto = self.vendi(self.open)
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			A.suspend_subscription(aperto["name"], str(getdate()), str(add_days(getdate(), 2)))


class LeRate(AbbonamentiCase):
	def setUp(self):
		super().setUp()
		semina_qualifiche()
		fatturazione.InvoicingBase.crea_azienda()
		erogatore = fatturazione.InvoicingBase.crea_erogatore("Istruttore Rossi", "psicologo")
		self.scheda = frappe.get_doc(
			{
				"doctype": "CRM Billable Service",
				"service_name": "Abbonamento palestra (fattura)",
				"fiscal_description": "Abbonamento ai corsi",
				"is_healthcare": 0,
				"vat_rate": 22,
				"default_rate": 90,
				"default_provider": erogatore.name,
				"enabled": 1,
			}
		).insert()
		tipo = frappe.get_doc(A.TIPO, self.due)
		tipo.billable_service = self.scheda.name
		tipo.save()

	def test_la_rata_del_giorno_si_fattura_da_sola(self):
		fatto = self.vendi(starts_on=str(getdate()))
		A.ogni_giorno()
		letto = self.letto(fatto["name"])
		prima, seconda, _terza = letto["instalments"]
		self.assertTrue(prima["invoice"])
		# the ones still to come wait for their day
		self.assertFalse(seconda["invoice"])
		fattura = frappe.get_doc("CRM Invoice", prima["invoice"])
		riga = fattura.items[0]
		self.assertEqual(
			(fattura.subscription, fattura.party, fattura.docstatus, riga.rate, riga.billable_service),
			(fatto["name"], self.giulia.name, 0, 90, self.scheda.name),
		)
		self.assertEqual(getdate(riga.period_from), getdate())
		self.assertEqual(getdate(riga.period_to), getdate(seconda["due_on"]) - datetime.timedelta(days=1))
		# once
		A.ogni_giorno()
		self.assertEqual(frappe.db.count("CRM Invoice", {"subscription": fatto["name"]}), 1)
		with self.assertRaises(frappe.ValidationError):
			fatture.issue_from_subscription(fatto["name"], prima["name"])

	def test_gli_ingressi_non_si_fatturano_uno_per_uno(self):
		fatto = self.vendi(starts_on=str(add_days(getdate(), -3)))
		venuta = self.lezione(
			datetime.datetime.combine(add_days(getdate(), -1), datetime.time(10), tzinfo=UTC)
		)
		self.esito(venuta, "Attended")
		self.assertEqual(self.prezzo(venuta)[0], fatto["name"])
		self.assertNotIn(venuta.name, [r["name"] for r in fatture.appointments_to_invoice()])
		with self.assertRaises(frappe.ValidationError):
			fatture.issue_from_appointment(venuta.name)

	def test_a_mano_e_un_prezzo_nuovo(self):
		fatto = self.vendi(starts_on=str(add_days(getdate(), 10)))
		self.come(DESK)
		fatta = A.invoice_instalment(fatto["name"], fatto["instalments"][0]["name"])
		self.assertTrue(fatta["invoice"])
		# a new price: what is invoiced stays, the rest is shared again
		cambiato = A.save_subscription(fatto["name"], json.dumps({"price": 300}))
		self.assertEqual([r["amount"] for r in cambiato["instalments"]], [90.0, 105.0, 105.0])
		frappe.set_user("Administrator")

	def test_emessa_da_sola_quando_il_tipo_lo_dice(self):
		tipo = frappe.get_doc(A.TIPO, self.due)
		tipo.issue_invoices = 1
		tipo.save()
		fatto = self.vendi(starts_on=str(getdate()))
		A.ogni_giorno()
		prima = self.letto(fatto["name"])["instalments"][0]
		# issued, or a draft that says why not: never nothing
		self.assertTrue(prima["invoice"])
		self.assertTrue(prima["issued"] or prima["problem"])

	def test_senza_scheda_niente_fatture(self):
		fatto = self.vendi(self.open, starts_on=str(getdate()))
		A.ogni_giorno()
		self.assertFalse(frappe.db.exists("CRM Invoice", {"subscription": fatto["name"]}))
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			A.invoice_instalment(fatto["name"], fatto["instalments"][0]["name"])


class LaFine(AbbonamentiCase):
	def test_il_promemoria_una_volta(self):
		# three months that end in five days
		inizio = R.piu_mesi(getdate(), -3) + datetime.timedelta(days=5)
		fatto = self.vendi(starts_on=str(inizio))
		self.assertTrue(R.da_ricordare(getdate(), getdate(fatto["ends_on"]), 7))
		A.ogni_giorno()
		A.ogni_giorno()
		posta = frappe.get_all(
			"Email Queue", filters={"reference_doctype": A.ABBONAMENTO, "reference_name": fatto["name"]}
		)
		self.assertEqual(len(posta), 1)
		self.assertEqual(frappe.db.get_value(A.ABBONAMENTO, fatto["name"], "reminded_on"), getdate())

	def test_si_rinnova_da_solo_il_giorno_dopo(self):
		inizio = R.piu_mesi(getdate(), -3) - datetime.timedelta(days=2)
		fatto = self.vendi(starts_on=str(inizio))
		self.assertEqual(fatto["status"], R.SCADUTO)
		A.ogni_giorno()
		dopo = frappe.db.get_value(A.ABBONAMENTO, fatto["name"], "renewed_by")
		self.assertTrue(dopo)
		nuovo = frappe.get_doc(A.ABBONAMENTO, dopo)
		self.assertEqual(
			(nuovo.lead, nuovo.subscription_type, getdate(nuovo.starts_on), nuovo.renewal_of),
			(
				self.giulia.name,
				self.due,
				getdate(fatto["ends_on"]) + datetime.timedelta(days=1),
				fatto["name"],
			),
		)
		# once
		A.ogni_giorno()
		self.assertEqual(frappe.db.count(A.ABBONAMENTO, {"renewal_of": fatto["name"]}), 1)

	def test_rinnovato_a_mano_e_open_non_si_rinnova(self):
		fatto = self.vendi(self.open, starts_on=str(add_days(getdate(), -40)))
		A.ogni_giorno()
		self.assertFalse(frappe.db.get_value(A.ABBONAMENTO, fatto["name"], "renewed_by"))
		self.come(DESK)
		nuovo = A.renew_subscription(fatto["name"])
		self.assertEqual(getdate(nuovo["starts_on"]), getdate(fatto["ends_on"]) + datetime.timedelta(days=1))
		with self.assertRaises(frappe.ValidationError):
			A.renew_subscription(fatto["name"])


class ChiLegge(AbbonamentiCase):
	def test_la_segreteria_vende_l_istruttore_legge_i_suoi(self):
		fatto = self.vendi()
		self.lezione(self.lunedi())
		self.come(COACH)
		self.assertEqual(
			[s["name"] for s in A.get_subscriptions(self.giulia.name)["subscriptions"]], [fatto["name"]]
		)
		# this week's entries: the lesson is next week's
		self.assertEqual(A.get_subscription(fatto["name"])["used"], 0)
		# who does not train Giulia reads nothing of her
		self.come(ALTRO)
		with self.assertRaises(frappe.PermissionError):
			A.get_subscription(fatto["name"])
		# marketing does not sell subscriptions
		self.come(MARKETING)
		with self.assertRaises(frappe.PermissionError):
			A.sell_subscription(self.giulia.name, json.dumps({"subscription_type": self.open}))
		# the types are the manager's and the desk's settings
		with self.assertRaises(frappe.PermissionError):
			A.save_type(json.dumps({"type_name": "Di nascosto", "services": [self.pilates.name]}))

	def test_la_scheda_dell_appuntamento(self):
		fatto = self.vendi()
		lezione = self.lezione(self.lunedi())
		from crm.api import appointments

		self.come(DESK)
		scheda = appointments.get_appointment(lezione.name)["subscription"]
		self.assertEqual((scheda["subscription"], scheda["can_manage"]), (fatto["name"], True))
		[opzione] = scheda["options"]
		self.assertEqual((opzione["type"], opzione["used"]), (self.due, 1))


class ITipi(AbbonamentiCase):
	def test_un_tipo_vuole_nome_e_servizi_e_venduto_non_si_cancella(self):
		with self.assertRaises(frappe.ValidationError):
			A.save_type(json.dumps({"type_name": "Senza servizi", "services": []}))
		with self.assertRaises(frappe.ValidationError):
			A.save_type(json.dumps({"type_name": "", "services": [self.pilates.name]}))
		self.vendi(self.open)
		with self.assertRaises(frappe.ValidationError):
			A.delete_type(self.open)
		# switched off, it is not sold any more
		tipo = A.save_type(json.dumps({**A.get_types()[0], "enabled": 0}), name=A.get_types()[0]["name"])
		self.assertFalse(tipo["enabled"])
		with self.assertRaises(frappe.ValidationError):
			self.vendi(tipo["name"])
		nuovo = A.save_type(json.dumps({"type_name": "Mai venduto", "services": [self.pilates.name]}))
		A.delete_type(nuovo["name"])
		self.assertFalse(frappe.db.exists(A.TIPO, nuovo["name"]))


class NellArea(area.AreaCase):
	def test_quello_che_resta_questa_settimana(self):
		frappe.set_user("Administrator")
		pilates = self.make_service("Pilates dell'area", [area.OPERATORE], default_price=20, currency="EUR")
		tipo = A.save_type(
			json.dumps(
				{
					"type_name": "Due a settimana dell'area",
					"description": "Pilates due volte a settimana",
					"months": 1,
					"price": 90,
					"services": [pilates.name],
					"entries": R.A_SETTIMANA,
					"entries_count": 2,
				}
			)
		)["name"]
		fatto = A.nuovo(self.anna.name, tipo, getdate())
		domani = datetime.datetime.now(UTC) + datetime.timedelta(days=1)
		self.make_appointment(
			pilates.name,
			domani,
			[area.OPERATORE],
			participants=[
				{"party_type": "CRM Lead", "party": self.anna.name, "participant_name": "Anna Area"}
			],
		)
		self.invita()
		self.entra()
		[mio] = area_api.get_appointments(self.anna.name)["subscriptions"]
		self.assertEqual(
			(mio["name"], mio["type"], mio["description"], mio["entries_count"]),
			(fatto.name, tipo, "Pilates due volte a settimana", 2),
		)
		# what the centre keeps for itself stays there
		self.assertFalse({"price", "notes", "instalments"} & set(mio))
