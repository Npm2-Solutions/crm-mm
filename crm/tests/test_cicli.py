# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Cycles of sessions (docs/gestionale-medico, phase 3).

The desk sells Mario a cycle of physiotherapy. The appointments of that service join
it by themselves, and so do the ones already booked when it is sold. The cycle counts
what is done, missed, booked and left: used up it is completed, a cancellation opens
it again, a missed session the cycle does not count is one more to book. Each session
costs its share of the price. Paid as a whole it has one invoice, and its sessions
leave the list of appointments to invoice; paid session by session each is invoiced
at its share. The physiotherapist reads the cycles of their appointments; marketing
does not sell them.
"""

import datetime
import json

import frappe
from frappe.utils import add_days, getdate

from crm.api import oggi
from crm.api.activities import appointments_on
from crm.invoicing import api as fatture
from crm.invoicing import emissione
from crm.invoicing.install import semina_qualifiche
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.scheduling import cicli
from crm.scheduling import cicli_regole as C

# modules, not classes: a TestCase imported here would run here too
from crm.tests import test_invoicing as fatturazione
from crm.tests.test_scheduling import SchedulingCase

DESK = "cicli.desk@example.com"
FISIO = "cicli.fisio@example.com"
ALTRO = "cicli.altro@example.com"
MARKETING = "cicli.marketing@example.com"


class CicliCase(SchedulingCase):
	def setUp(self):
		super().setUp()
		utenti.sincronizza()
		for user, livello in (
			(DESK, "segreteria"),
			(FISIO, "operatore"),
			(ALTRO, "operatore"),
			(MARKETING, "marketing"),
		):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		livelli.dimentica_cache()
		self.fisio = self.make_service(
			"Fisioterapia a cicli", [FISIO, ALTRO], default_price=50, currency="EUR"
		)
		self.visita = self.make_service("Visita fuori ciclo", [FISIO], default_price=80, currency="EUR")
		self.mario = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Mario", "last_name": "Cicli"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def giorno(self, quanti, ora=10):
		"""``quanti`` days from today, at ``ora``."""
		return self.tomorrow(ora) + datetime.timedelta(days=quanti - 1)

	def seduta(self, quando, servizio=None, medico=FISIO):
		return self.make_appointment(
			(servizio or self.fisio).name,
			quando,
			[medico],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": self.mario.name,
					"participant_name": self.mario.lead_name,
					"status": "Booked",
				}
			],
		)

	def ciclo(self, sedute=3, name=None, **dati):
		self.come(DESK)
		fatto = cicli.save_cycle(
			self.mario.name, json.dumps({"service": self.fisio.name, "sessions": sedute, **dati}), name=name
		)
		frappe.set_user("Administrator")
		return fatto

	def esito(self, appuntamento, stato):
		doc = frappe.get_doc("CRM Appointment", appuntamento.name)
		doc.participants[0].status = stato
		doc.save()

	def annulla(self, appuntamento):
		doc = frappe.get_doc("CRM Appointment", appuntamento.name)
		doc.status = "Cancelled"
		doc.save()

	def letto(self, ciclo):
		self.come(DESK)
		fatto = cicli.get_cycle(ciclo)
		frappe.set_user("Administrator")
		return fatto

	def prezzo(self, appuntamento):
		return frappe.db.get_value("CRM Appointment", appuntamento.name, ["session_cycle", "total_amount"])


def una_settimana_fa() -> str:
	return str(add_days(getdate(), -7))


class LeSedute(CicliCase):
	def test_un_appuntamento_del_servizio_entra_nel_ciclo_da_solo(self):
		fatto = self.ciclo(3, price=120)
		prima = self.seduta(self.giorno(1))
		self.assertEqual(prima.session_cycle, fatto["name"])
		# each session costs its share: 120 over 3, not the price list's 50
		self.assertEqual((prima.total_amount, prima.participants[0].amount), (40, 40))
		# another service does not join
		self.assertFalse(self.seduta(self.giorno(2, 8), servizio=self.visita).session_cycle)
		self.seduta(self.giorno(2))
		self.seduta(self.giorno(3))
		# three sessions: the fourth is an appointment like any other
		quarta = self.seduta(self.giorno(4))
		self.assertEqual(self.prezzo(quarta), (None, 50))
		letto = self.letto(fatto["name"])
		self.assertEqual(
			letto["counts"], {"done": 0, "missed": 0, "booked": 3, "used": 0, "left": 0, "total": 3}
		)
		self.assertEqual([a["number"] for a in letto["appointments"]], [1, 2, 3])
		self.assertEqual(letto["status"], C.ATTIVO)

	def test_fatte_perse_e_il_ciclo_completato(self):
		fatto = self.ciclo(2, starts_on=una_settimana_fa())
		venuto = self.seduta(self.giorno(-2))
		assente = self.seduta(self.giorno(-1))
		self.esito(venuto, "Attended")
		self.esito(assente, "No Show")
		letto = self.letto(fatto["name"])
		self.assertEqual((letto["counts"]["done"], letto["counts"]["missed"]), (1, 1))
		self.assertEqual(letto["status"], C.COMPLETATO)
		self.assertEqual(frappe.db.get_value(cicli.CICLO, fatto["name"], "status"), C.COMPLETATO)
		# a missed session the cycle does not count is one more to book, and has no number
		self.ciclo(2, name=fatto["name"], starts_on=una_settimana_fa(), missed_count=0)
		letto = self.letto(fatto["name"])
		self.assertEqual((letto["status"], letto["counts"]["left"]), (C.ATTIVO, 1))
		self.assertEqual([a["number"] for a in letto["appointments"]], [1, None])
		self.assertEqual(self.seduta(self.giorno(1)).session_cycle, fatto["name"])

	def test_una_disdetta_libera_la_seduta(self):
		fatto = self.ciclo(1)
		prima = self.seduta(self.giorno(1))
		self.assertFalse(self.seduta(self.giorno(2)).session_cycle)
		self.annulla(prima)
		dopo = self.seduta(self.giorno(3))
		self.assertEqual(dopo.session_cycle, fatto["name"])
		self.assertEqual(
			[(a["name"], a["number"]) for a in self.letto(fatto["name"])["appointments"]],
			[(prima.name, None), (dopo.name, 1)],
		)

	def test_scaduto_non_prende_altre_sedute(self):
		fatto = self.ciclo(3, starts_on=una_settimana_fa(), valid_until=str(add_days(getdate(), -1)))
		self.assertFalse(self.seduta(self.giorno(1)).session_cycle)
		self.assertEqual(self.letto(fatto["name"])["status"], C.SCADUTO)

	def test_un_ciclo_nuovo_prende_gli_appuntamenti_gia_prenotati(self):
		prima, seconda, terza = (self.seduta(self.giorno(n)) for n in (1, 2, 3))
		fatto = self.ciclo(2, price=90)
		self.assertEqual(self.prezzo(prima), (fatto["name"], 45))
		self.assertEqual(self.prezzo(seconda), (fatto["name"], 45))
		self.assertEqual(self.prezzo(terza), (None, 50))
		# a new price: the sessions cost the new share
		self.ciclo(2, name=fatto["name"], price=100)
		self.assertEqual(self.prezzo(prima), (fatto["name"], 50))

	def test_a_mano_dentro_e_fuori(self):
		fatto = self.ciclo(2, price=90)
		seduta = self.seduta(self.giorno(1))
		self.come(DESK)
		cicli.attach(seduta.name, None)
		self.assertEqual(self.prezzo(seduta), (None, 50))
		cicli.attach(seduta.name, fatto["name"])
		self.assertEqual(self.prezzo(seduta), (fatto["name"], 45))
		visita = self.seduta(self.giorno(2, 8), servizio=self.visita)
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			cicli.attach(visita.name, fatto["name"])
		# closed, nothing joins it any more
		cicli.close_cycle(fatto["name"])
		frappe.set_user("Administrator")
		self.assertFalse(self.seduta(self.giorno(3)).session_cycle)

	def test_un_ciclo_sbagliato_si_cancella_finche_nessuna_seduta_e_usata(self):
		fatto = self.ciclo(2, price=90)
		seduta = self.seduta(self.giorno(1))
		self.come(DESK)
		cicli.delete_cycle(fatto["name"])
		self.assertFalse(frappe.db.exists(cicli.CICLO, fatto["name"]))
		self.assertEqual(self.prezzo(seduta), (None, 50))
		usato = self.ciclo(2, starts_on=una_settimana_fa())
		self.esito(self.seduta(self.giorno(-1)), "Attended")
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			cicli.delete_cycle(usato["name"])


class IlPagamento(CicliCase):
	def setUp(self):
		super().setUp()
		semina_qualifiche()
		fatturazione.InvoicingBase.crea_azienda()
		erogatore = fatturazione.InvoicingBase.crea_erogatore("Dott.ssa Bianchi", "psicologo")
		frappe.get_doc(
			{
				"doctype": "CRM Billable Service",
				"service_name": "Fisioterapia a cicli (fattura)",
				"fiscal_description": "Seduta di fisioterapia",
				"crm_service": self.fisio.name,
				"is_healthcare": 0,
				"vat_rate": 22,
				"default_rate": 50,
				"default_provider": erogatore.name,
				"enabled": 1,
			}
		).insert()

	def da_fatturare(self):
		return [riga["name"] for riga in fatture.appointments_to_invoice()]

	def test_pagato_intero_una_fattura_e_le_sedute_escono_dalla_lista(self):
		fatto = self.ciclo(2, price=90, billing=cicli.INTERO, starts_on=una_settimana_fa())
		seduta = self.seduta(self.giorno(-2))
		self.esito(seduta, "Attended")
		self.assertNotIn(seduta.name, self.da_fatturare())
		with self.assertRaises(frappe.ValidationError):
			fatture.issue_from_appointment(seduta.name)
		nome = fatture.issue_from_cycle(fatto["name"])
		fattura = frappe.get_doc("CRM Invoice", nome)
		riga = fattura.items[0]
		self.assertEqual(
			(fattura.session_cycle, fattura.party, len(fattura.items), riga.qty, riga.rate),
			(fatto["name"], self.mario.name, 1, 1, 90),
		)
		self.assertIn("2", riga.description)
		self.assertEqual(getdate(riga.period_from), getdate(una_settimana_fa()))
		# once
		with self.assertRaises(frappe.ValidationError):
			fatture.issue_from_cycle(fatto["name"])
		self.assertEqual(self.letto(fatto["name"])["invoice"], nome)
		# invoiced, it is not deleted
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			cicli.delete_cycle(fatto["name"])

	def test_per_seduta_ogni_seduta_si_fattura_alla_sua_quota(self):
		fatto = self.ciclo(2, price=90, starts_on=una_settimana_fa())
		seduta = self.seduta(self.giorno(-2))
		self.esito(seduta, "Attended")
		self.assertIn(seduta.name, self.da_fatturare())
		nome = fatture.issue_from_appointment(seduta.name)
		self.assertEqual(frappe.get_doc("CRM Invoice", nome).items[0].rate, 45)
		with self.assertRaises(frappe.ValidationError):
			fatture.issue_from_cycle(fatto["name"])

	def test_senza_professionista_la_fattura_si_apre_e_lo_chiede(self):
		# the agenda cannot tell who did it: no professional of the staff's, no
		# default on the card. The desk got an error; now the dialog asks
		frappe.db.set_value(
			"CRM Billable Service", {"crm_service": self.fisio.name}, "default_provider", None
		)
		seduta = self.seduta(self.giorno(-2))
		self.esito(seduta, "Attended")
		with self.assertRaises(frappe.ValidationError):
			fatture.issue_from_appointment(seduta.name)
		proposta = fatture.appointment_invoice_proposal(seduta.name)
		self.assertEqual((proposta["appointment"], proposta["party"]), (seduta.name, self.mario.name))
		self.assertEqual(proposta["items"][0]["service_provider"], "")
		vista = emissione.preview(proposta)
		self.assertEqual(vista["appointment"], seduta.name)
		self.assertTrue(vista["errors"])
		# chosen in the dialog, it is saved with its appointment
		proposta["items"][0]["service_provider"] = frappe.db.get_value("CRM Service Provider", {}, "name")
		salvata = emissione.save(proposta)
		self.assertEqual(frappe.db.get_value("CRM Invoice", salvata["name"], "appointment"), seduta.name)

	def test_pagato_intero_vuole_il_prezzo(self):
		with self.assertRaises(frappe.ValidationError):
			self.ciclo(2, billing=cicli.INTERO)


class ChiLegge(CicliCase):
	def test_la_segreteria_vende_il_fisioterapista_legge_i_suoi(self):
		fatto = self.ciclo(3)
		self.seduta(self.giorno(1))
		self.come(FISIO)
		self.assertEqual([c["name"] for c in cicli.get_cycles(self.mario.name)["cycles"]], [fatto["name"]])
		self.assertEqual(cicli.get_cycle(fatto["name"])["counts"]["booked"], 1)
		# who does not look after Mario reads nothing of him
		self.come(ALTRO)
		with self.assertRaises(frappe.PermissionError):
			cicli.get_cycle(fatto["name"])
		# marketing does not sell cycles
		self.come(MARKETING)
		with self.assertRaises(frappe.PermissionError):
			cicli.save_cycle(self.mario.name, json.dumps({"service": self.fisio.name, "sessions": 5}))

	def test_la_pagina_oggi_e_la_scheda_dicono_la_seduta(self):
		fatto = self.ciclo(3)
		self.seduta(self.giorno(1, 9))
		seconda = self.seduta(self.giorno(2))
		self.come(DESK)
		giorno = oggi.get_day(str(self.giorno(2).date()))
		[riga] = [a for a in giorno["appointments"] if a["name"] == seconda.name]
		self.assertEqual(riga["cycle"], {"cycle": fatto["name"], "number": 2, "total": 3})
		from crm.api import appointments

		scheda = appointments.get_appointment(seconda.name)["cycle"]
		self.assertEqual((scheda["cycle"], scheda["number"], scheda["total"]), (fatto["name"], 2, 3))
		self.assertTrue(scheda["can_manage"])

	def test_la_cronologia_dice_la_seduta(self):
		fatto = self.ciclo(3)
		prima = self.seduta(self.giorno(1, 9))
		seconda = self.seduta(self.giorno(2))
		fuori = self.seduta(self.giorno(3), servizio=self.visita)
		cronologia = {r["name"]: r["data"]["cycle"] for r in appointments_on("CRM Lead", self.mario.name)}
		self.assertEqual(cronologia[prima.name], {"cycle": fatto["name"], "number": 1, "total": 3})
		self.assertEqual(cronologia[seconda.name]["number"], 2)
		# a visit outside the cycle is no session of it
		self.assertIsNone(cronologia[fuori.name])
