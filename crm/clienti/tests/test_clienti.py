# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""New clients on a site without the clinic: a beauty centre.

Giulia fills in a form from an ad, and her deal opens in the new clients pipeline.
She books a facial: the deal says "appointment booked". The desk checks her in:
she is a client from that moment, the deal is won and the automations hear "Became
Client", once. A client is not one again. An invoice makes one too; a credit note
does not. Last year's clients are found and announce nothing. Where a module with
rules of its own is on, the CRM's give way. The manager chooses the pipeline and
the stage after a booking. The dashboard counts the new clients and what one costs.
"""

import datetime
from unittest.mock import patch

import frappe
from frappe.utils import add_days, get_datetime, now_datetime, nowdate

from crm.clienti import cliente, eventi, pipeline, regole
from crm.dashboard import registry
from crm.dashboard.context import Context
from crm.dashboard.widgets.marketing import ad_clients
from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_first_stage
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.preventivi import pipeline as preventivi
from crm.tests.test_scheduling import SchedulingCase

SEGRETERIA = "clienti.desk@example.com"
MANAGER = "clienti.manager@example.com"


class ClientiCase(SchedulingCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.piano()
		self.estetista = self.make_user("clienti.estetista@example.com")
		self.viso = self.make_service("Pulizia viso clienti", [self.estetista])
		self.giulia = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Giulia", "last_name": "Clienti"}
		).insert(ignore_permissions=True)
		# whatever the site had chosen: these tests make their own
		frappe.db.set_single_value(
			pipeline.IMPOSTAZIONI, {"new_clients_pipeline": None, "booked_stage": None}
		)
		pipeline.crea()

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()

	def piano(self, *moduli):
		"""The plan of these tests: the base, and no clinic."""
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", list(moduli))
		piano.save()
		livelli.dimentica_cache()

	def richiesta(self, persona, stadio=None):
		"""A new clients deal, as a form or a lead ad opens it."""
		doc = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"lead": persona.name,
				"status": stadio or get_first_stage(pipeline.quale()),
			}
		)
		doc.flags.ignore_mandatory = True
		doc.flags.from_inquiry = True
		return doc.insert(ignore_permissions=True)

	def appuntamento(self, persona, quando, stato="Confirmed", presenza="Booked"):
		return self.make_appointment(
			self.viso.name,
			quando,
			[self.estetista],
			status=stato,
			participants=[
				{
					"party_type": "CRM Lead",
					"party": persona.name,
					"participant_name": persona.lead_name,
					"status": presenza,
				}
			],
		)

	def ieri(self, ora=10):
		return self.tomorrow(ora) - datetime.timedelta(days=2)

	def stato(self, deal):
		return frappe.db.get_value("CRM Deal", deal.name, "status")

	def tipo(self, deal):
		return frappe.db.get_value("CRM Deal Status", self.stato(deal), "type")

	def da(self, persona):
		return cliente.cliente_da(persona.name)

	@staticmethod
	def annunci(evento):
		return [chiamata for chiamata in evento.call_args_list if chiamata.args[0] == cliente.EVENTO]


class LaPipeline(ClientiCase):
	def test_nasce_una_volta_con_lo_stadio_dopo_la_prenotazione(self):
		conf = pipeline.impostazioni()
		self.assertEqual(
			frappe.db.get_value("CRM Deal Status", conf.booked_stage, ["pipeline", "position"]),
			(conf.new_clients_pipeline, pipeline.PRENOTATO + 1),
		)
		tipi = frappe.get_all(
			"CRM Deal Status", filters={"pipeline": conf.new_clients_pipeline}, pluck="type"
		)
		self.assertIn("Won", tipi)
		self.assertIn("Lost", tipi)
		prima = frappe.db.count("CRM Pipeline")
		self.assertEqual(pipeline.crea(), conf)
		self.assertEqual(frappe.db.count("CRM Pipeline"), prima)

	def test_le_impostazioni_tengono_insieme_pipeline_e_stadio(self):
		preventivi.crea()
		doc = frappe.get_single(pipeline.IMPOSTAZIONI)
		doc.booked_stage = get_first_stage(preventivi.quale())
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		doc = frappe.get_single(pipeline.IMPOSTAZIONI)
		doc.new_clients_pipeline = preventivi.quale()
		doc.booked_stage = None
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_il_manager_la_sceglie(self):
		utenti.sincronizza()
		for user, livello in ((SEGRETERIA, "segreteria"), (MANAGER, "manager")):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		livelli.dimentica_cache()
		frappe.set_user(SEGRETERIA)
		with self.assertRaises(frappe.PermissionError):
			pipeline.get_settings()
		frappe.set_user(MANAGER)
		nome = pipeline.get_settings()["new_clients_pipeline"]
		self.assertEqual(pipeline.save_settings(), {"new_clients_pipeline": None, "booked_stage": None})
		# made again: the one of the same name is taken as it is, and the manager
		# says which of its stages comes after a booking
		self.assertEqual(pipeline.create_pipeline(), {"new_clients_pipeline": nome, "booked_stage": None})


class LaPrenotazione(ClientiCase):
	def test_sposta_la_richiesta_su_appuntamento_fissato(self):
		deal = self.richiesta(self.giulia)
		self.appuntamento(self.giulia, self.tomorrow(10))
		self.assertEqual(self.stato(deal), pipeline.impostazioni().booked_stage)

	def test_una_trattativa_di_un_altra_pipeline_resta_dove_e(self):
		preventivi.crea()
		altra = self.richiesta(self.giulia, get_first_stage(preventivi.quale()))
		self.appuntamento(self.giulia, self.tomorrow(10))
		self.assertEqual(self.stato(altra), get_first_stage(preventivi.quale()))

	def test_senza_pipeline_scelta_niente_si_muove(self):
		deal = self.richiesta(self.giulia)
		primo = self.stato(deal)
		frappe.db.set_single_value(pipeline.IMPOSTAZIONI, "new_clients_pipeline", None)
		self.appuntamento(self.giulia, self.tomorrow(10))
		self.assertEqual(self.stato(deal), primo)


class DiventareCliente(ClientiCase):
	def test_al_banco_diventa_cliente_e_vince_la_richiesta(self):
		from crm.scheduling import esiti

		deal = self.richiesta(self.giulia)
		incontro = self.appuntamento(self.giulia, self.tomorrow(10))
		riga = incontro.participants[0].name
		with patch("crm.automation.engine.process_event") as evento:
			esiti.segna(incontro.name, riga, "Arrived")
		self.assertEqual(
			self.da(self.giulia), frappe.db.get_value("CRM Appointment Participant", riga, "arrived_at")
		)
		self.assertEqual(self.tipo(deal), "Won")
		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "closed_date").isoformat(), nowdate())
		annunci = self.annunci(evento)
		self.assertEqual(len(annunci), 1)
		self.assertEqual(annunci[0].args[1].name, self.giulia.name)
		self.assertEqual(annunci[0].args[2], {"rule": regole.ACCETTAZIONE.valore})

	def test_un_appuntamento_svolto(self):
		incontro = self.appuntamento(self.giulia, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		self.assertEqual(self.da(self.giulia), get_datetime(incontro.starts_on))

	def test_chi_non_e_venuto_resta_un_contatto(self):
		incontro = self.appuntamento(self.giulia, self.ieri())
		incontro.participants[0].status = "No Show"
		incontro.status = "Completed"
		incontro.save()
		self.assertIsNone(self.da(self.giulia))

	def test_una_volta_sola(self):
		incontro = self.appuntamento(self.giulia, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		prima = self.da(self.giulia)
		with patch("crm.automation.engine.process_event") as evento:
			self.assertFalse(cliente.diventa_cliente(self.giulia.name, regole.FATTURA))
			altro = self.appuntamento(self.giulia, self.ieri(15))
			altro.status = "Completed"
			altro.save()
		self.assertEqual(self.da(self.giulia), prima)
		self.assertEqual(self.annunci(evento), [])

	def test_mai_nel_futuro(self):
		cliente.diventa_cliente(self.giulia.name, regole.FATTURA, quando=add_days(nowdate(), 3))
		self.assertLessEqual(self.da(self.giulia), now_datetime())

	def test_un_deal_che_non_si_salva_non_ferma_il_cliente(self):
		self.richiesta(self.giulia)
		with patch("crm.clienti.pipeline.vinci", side_effect=frappe.ValidationError("no")):
			self.assertTrue(cliente.diventa_cliente(self.giulia.name, regole.ACCETTAZIONE))
		self.assertIsNotNone(self.da(self.giulia))

	def test_nessuno_non_diventa_niente(self):
		self.assertFalse(cliente.diventa_cliente(None, regole.FATTURA))
		self.assertFalse(cliente.diventa_cliente("CRM-LEAD-NESSUNO", regole.FATTURA))

	def test_le_automazioni_hanno_il_loro_trigger(self):
		from crm.automation.engine import EVENT_TO_TRIGGER, trigger_offerti

		self.assertEqual(EVENT_TO_TRIGGER[cliente.EVENTO], cliente.TRIGGER)
		self.assertIn(cliente.TRIGGER, trigger_offerti())


class LaFattura(ClientiCase):
	def fattura(self, tipo="TD01"):
		return frappe._dict(
			doctype="CRM Invoice",
			name="FATTURA-DI-PROVA",
			document_type=tipo,
			party_type="CRM Lead",
			party=self.giulia.name,
			posting_date=add_days(nowdate(), -3),
		)

	def test_una_fattura_fa_un_cliente_dal_suo_giorno(self):
		eventi.fattura_confermata(self.fattura())
		self.assertEqual(self.da(self.giulia), get_datetime(add_days(nowdate(), -3)))

	def test_una_nota_di_credito_no(self):
		eventi.fattura_confermata(self.fattura("TD04"))
		self.assertIsNone(self.da(self.giulia))


class IClientiDiPrima(ClientiCase):
	def test_si_trovano_e_non_si_annunciano(self):
		deal = self.richiesta(self.giulia)
		incontro = self.appuntamento(self.giulia, self.ieri())
		# as it went before the CRM knew who its clients were
		with patch.object(cliente, "regole_del_crm", return_value=False):
			incontro.status = "Completed"
			incontro.save()
		self.assertIsNone(self.da(self.giulia))
		with patch("crm.automation.engine.process_event") as evento:
			self.assertGreaterEqual(cliente.recupera(), 1)
		self.assertEqual(self.da(self.giulia), get_datetime(incontro.starts_on))
		self.assertNotEqual(self.tipo(deal), "Won")
		self.assertEqual(self.annunci(evento), [])


class LeRegoleDiUnModulo(ClientiCase):
	def test_dove_un_modulo_decide_quelle_del_crm_si_fanno_da_parte(self):
		acceso = {"si": True}
		with patch.object(cliente, "_regole_proprie", [lambda: acceso["si"]]):
			self.assertFalse(cliente.regole_del_crm())
			incontro = self.appuntamento(self.giulia, self.ieri())
			incontro.status = "Completed"
			incontro.save()
			self.assertIsNone(self.da(self.giulia))
			self.assertEqual(cliente.recupera(), 0)
			# the module calls the door itself, from its own rules
			self.assertTrue(cliente.diventa_cliente(self.giulia.name, regole.ACCETTAZIONE))
			acceso["si"] = False
			self.assertTrue(cliente.regole_del_crm())


class IlCruscotto(ClientiCase):
	def contesto(self):
		return Context.build(add_days(nowdate(), -7), nowdate(), scope="site", config={})

	def test_i_nuovi_clienti(self):
		widget = registry.get("new_clients")
		prima = widget.fn(self.contesto())["value"]
		cliente.diventa_cliente(self.giulia.name, regole.ACCETTAZIONE)
		self.assertEqual(widget.fn(self.contesto())["value"], prima + 1)

	def test_quelli_portati_dalle_pubblicita(self):
		self.assertIsNotNone(registry.get("meta_cost_per_client"))
		prima = ad_clients(self.contesto())
		frappe.db.set_value("CRM Lead", self.giulia.name, "facebook_ad_id", "ad-clienti-1")
		cliente.diventa_cliente(self.giulia.name, regole.ACCETTAZIONE)
		self.assertEqual(ad_clients(self.contesto()), prima + 1)
