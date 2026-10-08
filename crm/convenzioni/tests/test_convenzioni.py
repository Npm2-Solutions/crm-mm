# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Conventions on a site (doc 61): Anna is covered by Salute+ in direct form. Her
osteopathy costs the convention's 60, she pays a fifth and the fund the rest; the
visit waits for Salute+'s authorisation until its number is written. Her invoice is
her share only, and one with nothing for her is never proposed. At the end of the
month the fund gets one invoice, to the company, a line a pratica, through the SdI
and never to the Sistema TS; thrown away, its pratiche are to bill again. A company's
convention is a discount in indirect form. The covers follow the person."""

import datetime
import json

import frappe
from frappe.utils import add_days, getdate

from crm.api import oggi
from crm.api import service_booking as SB
from crm.convenzioni import api, convenzioni
from crm.convenzioni import regole as R
from crm.invoicing import anagrafica
from crm.invoicing import api as fatture
from crm.invoicing.install import semina_qualifiche
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

# modules, not classes: a TestCase imported here would run here too
from crm.tests import test_invoicing as fatturazione
from crm.tests import test_service_booking as prenota
from crm.tests.test_scheduling import SchedulingCase

DESK = "conv.desk@example.com"
MANAGER = "conv.manager@example.com"
OSTEO = "conv.osteo@example.com"


class ConvenzioniCase(SchedulingCase):
	def setUp(self):
		super().setUp()
		utenti.sincronizza()
		for user, livello in ((DESK, "segreteria"), (MANAGER, "manager"), (OSTEO, "operatore")):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		livelli.dimentica_cache()
		self.osteo = self.make_service("Osteopatia conv", [OSTEO], default_price=70, currency="EUR")
		listino = frappe.get_doc(
			{"doctype": "CRM Price List", "price_list_name": "Salute+ test", "enabled": 1, "currency": "EUR"}
		).insert()
		frappe.get_doc(
			{
				"doctype": "CRM Service Price",
				"price_list": listino.name,
				"service": self.osteo.name,
				"price": 60,
				"currency": "EUR",
				"enabled": 1,
			}
		).insert()
		self.fondo_azienda = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Salute+ Assicurazioni test"}
		).insert(ignore_permissions=True)
		anagrafica.save_billing_profile(
			"CRM Organization",
			self.fondo_azienda.name,
			{
				"billing_name": "Salute+ Assicurazioni S.p.A.",
				"tax_id": "01234567897",
				"recipient_code": "SPLUS01",
				"address_line": "Corso Italia",
				"civic_number": "40",
				"postal_code": "20122",
				"city": "Milano",
				"province": "MI",
				"country": "IT",
			},
		)
		self.come(MANAGER)
		self.fondo = api.save_convention(
			{
				"convention_name": "Salute+ test",
				"kind": R.ASSICURAZIONE,
				"enabled": 1,
				"organization": self.fondo_azienda.name,
				"direct": 1,
				"indirect": 1,
				"requires_authorisation": 1,
				"price_mode": R.LISTINO,
				"price_list": listino.name,
				"share_mode": R.PERCENTUALE,
				"share_percent": 20,
			}
		)["name"]
		frappe.set_user("Administrator")
		self.anna = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Anna", "last_name": "Fondo"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def giorno(self, quanti, ora=10):
		return self.tomorrow(ora) + datetime.timedelta(days=quanti - 1)

	def visita(self, quando, **campi):
		return self.make_appointment(
			self.osteo.name,
			quando,
			[OSTEO],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": self.anna.name,
					"participant_name": self.anna.lead_name,
					"status": "Booked",
				}
			],
			**campi,
		)

	def venuta(self, appuntamento):
		doc = frappe.get_doc("CRM Appointment", appuntamento.name)
		doc.participants[0].status = "Attended"
		doc.save()
		return doc


class IlPrezzoELeQuote(ConvenzioniCase):
	def test_forma_diretta_il_listino_e_le_due_quote(self):
		self.come(DESK)
		api.save_cover(self.anna.name, {"convention": self.fondo, "card_number": "SP123"})
		frappe.set_user("Administrator")
		doc = self.visita(self.giorno(2), convention=self.fondo, convention_form=R.DIRETTA)
		self.assertEqual((doc.total_amount, doc.patient_share, doc.fund_share), (60, 12, 48))
		self.assertEqual(doc.price_source, "Salute+ test")
		self.assertTrue(doc.convention_cover)
		info = convenzioni.del_appuntamento(doc)
		self.assertTrue(info["missing_authorisation"])
		self.assertEqual((info["state"], info["card_number"]), (R.DA_AUTORIZZARE, "SP123"))
		doc.authorisation = "SP-2026-1"
		doc.save()
		self.assertEqual(convenzioni.del_appuntamento(doc)["state"], R.AUTORIZZATA)
		# without the convention it is the centre's price again, on the centre's list
		doc.convention = None
		doc.save()
		self.assertEqual((doc.total_amount, doc.patient_share, doc.price_list), (70, 0, None))

	def test_la_scrivania_lo_vede(self):
		doc = self.visita(self.giorno(1), convention=self.fondo, convention_form=R.DIRETTA)
		self.come(DESK)
		giorno = oggi.get_day(str(getdate(doc.starts_on)))
		(riga,) = [r for r in giorno["appointments"] if r.get("convention")]
		self.assertTrue(riga["convention"]["missing_authorisation"])

	def test_una_convenzione_aziendale_e_uno_sconto(self):
		self.come(MANAGER)
		azienda = api.save_convention(
			{
				"convention_name": "Dipendenti test",
				"kind": R.AZIENDA,
				"enabled": 1,
				"indirect": 1,
				"price_mode": R.SCONTO,
				"discount_percent": 15,
			}
		)["name"]
		frappe.set_user("Administrator")
		doc = self.visita(self.giorno(2), convention=azienda)
		self.assertEqual(doc.convention_form, R.INDIRETTA)
		# 70 less 15% is 59.50: all the person's
		self.assertEqual((doc.total_amount, doc.patient_share, doc.fund_share), (59.5, 59.5, 0))
		with self.assertRaises(frappe.ValidationError):
			self.visita(self.giorno(3), convention=azienda, convention_form=R.DIRETTA)

	def test_solo_chi_gestisce_le_convenzioni(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			api.list_conventions()
		with self.assertRaises(frappe.ValidationError):
			self.come(MANAGER)
			api.save_convention({"convention_name": "Senza forme", "kind": R.FONDO})


class LaFattura(ConvenzioniCase):
	def setUp(self):
		super().setUp()
		semina_qualifiche()
		fatturazione.InvoicingBase.crea_azienda()
		erogatore = fatturazione.InvoicingBase.crea_erogatore("Dott. Verdi conv", "osteopata")
		frappe.get_doc(
			{
				"doctype": "CRM Billable Service",
				"service_name": "Osteopatia conv (fattura)",
				"fiscal_description": "Trattamento osteopatico",
				"crm_service": self.osteo.name,
				"is_healthcare": 1,
				"vat_exempt": 1,
				"exemption_reference": "art. 10, n. 18, DPR 633/72",
				"vat_rate": 0,
				"ts_expense_type": "SP",
				"default_rate": 70,
				"default_provider": erogatore.name,
				"enabled": 1,
			}
		).insert()

	def test_la_persona_paga_la_sua_quota_e_il_fondo_il_resto_a_fine_mese(self):
		prima = self.venuta(
			self.visita(self.giorno(-3), convention=self.fondo, convention_form=R.DIRETTA, authorisation="A1")
		)
		seconda = self.venuta(
			self.visita(self.giorno(-2), convention=self.fondo, convention_form=R.DIRETTA, authorisation="A2")
		)
		self.come(DESK)
		proposta = fatture.appointment_invoice_proposal(prima.name)
		self.assertEqual(proposta["items"][0]["rate"], 12)

		mese = str(prima.starts_on)[:7]
		if str(seconda.starts_on)[:7] != mese:
			return
		letto = api.get_claims(self.fondo, mese)
		self.assertEqual(letto["totals"]["to_bill"], 96)
		self.assertTrue(letto["can_bill"])
		nome = api.bill_fund(self.fondo, mese)
		fattura = frappe.get_doc("CRM Invoice", nome)
		self.assertEqual((fattura.party_type, fattura.party), ("CRM Organization", self.fondo_azienda.name))
		self.assertEqual(fattura.recipient_type, "soggetto_iva")
		self.assertEqual([r.rate for r in fattura.items], [48, 48])
		self.assertIn("Aut. A1", fattura.items[0].description)
		# to the SdI, never to the Sistema TS: it knows only natural persons
		self.assertEqual(fattura.ts_status, "non_applicabile")
		self.assertEqual(fattura.channel, "sdi")
		stati = {p["appointment"]: p["state"] for p in api.get_claims(self.fondo, mese)["claims"]}
		self.assertEqual(stati[prima.name], R.IN_BOZZA)
		# twice: nothing left to bill
		with self.assertRaises(frappe.ValidationError):
			api.bill_fund(self.fondo, mese)
		# a billed pratica keeps its convention
		frappe.set_user("Administrator")
		doc = frappe.get_doc("CRM Appointment", prima.name)
		doc.convention_form = R.INDIRETTA
		with self.assertRaises(frappe.ValidationError):
			doc.save()
		# the draft thrown away: the pratiche are to bill again
		frappe.delete_doc("CRM Invoice", nome)
		stati = {p["appointment"]: p["state"] for p in api.get_claims(self.fondo, mese)["claims"]}
		self.assertEqual(stati[prima.name], R.ESEGUITA)
		self.assertIn("Quota fondo", api.export_month(self.fondo, mese)["content"])

	def test_tutto_al_fondo_nulla_alla_persona(self):
		self.come(MANAGER)
		api.save_convention(
			{**api._riga(frappe.get_doc(api.CONVENZIONE, self.fondo)), "share_mode": R.NIENTE},
			name=self.fondo,
		)
		frappe.set_user("Administrator")
		visita = self.venuta(
			self.visita(self.giorno(-2), convention=self.fondo, convention_form=R.DIRETTA, authorisation="A3")
		)
		self.assertEqual((visita.patient_share, visita.fund_share), (0, 60))
		self.come(DESK)
		self.assertNotIn(visita.name, [r["name"] for r in fatture.appointments_to_invoice()])
		with self.assertRaises(frappe.ValidationError):
			fatture.appointment_invoice_proposal(visita.name)


class LaCopertura(ConvenzioniCase):
	def test_segue_la_persona_e_se_ne_va_con_lei(self):
		self.come(DESK)
		letto = api.save_cover(
			self.anna.name,
			{
				"convention": self.fondo,
				"card_number": "SP9",
				"valid_upto": str(add_days(getdate(), 30)),
			},
		)
		(copertura,) = letto["covers"]
		self.assertTrue(copertura["valid"])
		riepilogo = api.nel_riepilogo(self.anna.name)
		self.assertEqual(riepilogo["covers"][0]["card_number"], "SP9")
		with self.assertRaises(frappe.ValidationError):
			api.save_cover(self.anna.name, {"convention": ""})
		frappe.set_user("Administrator")
		frappe.delete_doc("CRM Lead", self.anna.name, force=True)
		self.assertFalse(frappe.db.exists(api.COPERTURA, copertura["name"]))

	def test_le_opzioni_del_pannello_mettono_prima_le_sue(self):
		self.come(DESK)
		api.save_cover(self.anna.name, {"convention": self.fondo, "card_number": "SP1"})
		opzioni = api.options_for(self.anna.name, str(getdate()))["conventions"]
		self.assertEqual(opzioni[0]["name"], self.fondo)
		self.assertTrue(opzioni[0]["covered"])
		self.assertEqual(
			api.quote(self.fondo, R.DIRETTA, 60, self.osteo.name),
			{"total": 60.0, "patient_share": 12.0, "fund_share": 48.0, "requires_authorisation": True},
		)
		json.dumps(opzioni)


class SullaPaginaDiPrenotazione(prenota.TestServiceBooking):
	"""Only the cases of this file: the parent class's run in their own module."""

	def setUp(self):
		super().setUp()
		organizzazione = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Fondo online test"}
		).insert(ignore_permissions=True)
		self.fondo = frappe.get_doc(
			{
				"doctype": "CRM Convention",
				"convention_name": "Fondo online test",
				"kind": R.FONDO,
				"enabled": 1,
				"direct": 1,
				"organization": organizzazione.name,
				"show_online": 1,
			}
		).insert()
		self.nascosto = frappe.get_doc(
			{"doctype": "CRM Convention", "convention_name": "Non online", "kind": R.AZIENDA, "indirect": 1}
		).insert()

	def test_la_prenotazione_aspetta_il_si_del_centro(self):
		servizio = self.online_service("Fisio conv online")
		offerte = [c["id"] for c in SB.get_catalog()["conventions"]]
		self.assertIn(self.fondo.name, offerte)
		self.assertNotIn(self.nascosto.name, offerte)
		fatta = self.book(servizio, self.tomorrow(11), convention=self.fondo.name, card_number="FX 12")
		self.assertTrue(fatta["pending_approval"])
		nome = frappe.db.get_value("CRM Appointment Participant", {"access_token": fatta["token"]}, "parent")
		appuntamento = frappe.get_doc("CRM Appointment", nome)
		self.assertEqual(
			(appuntamento.convention, appuntamento.convention_form), (self.fondo.name, R.DIRETTA)
		)
		self.assertEqual(
			frappe.db.get_value(api.COPERTURA, appuntamento.convention_cover, "card_number"), "FX 12"
		)
		with self.assertRaises(frappe.ValidationError):
			self.book(servizio, self.tomorrow(14), email="altro@example.com", convention=self.nascosto.name)


# the parent's own cases run in their module, not again here
for _nome in [n for n in dir(prenota.TestServiceBooking) if n.startswith("test_")]:
	setattr(SullaPaginaDiPrenotazione, _nome, None)
