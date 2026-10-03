# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""The scope follows the level, and what belongs to a person follows the person.

Doc 30, PR 2. The front desk saw only the people it owned; every Sales User read
every appointment, WhatsApp message, SMS and visitor's journey, and wrote services,
price lists and pipeline stages with the API. Now the level says on which records,
and the capability the screen asks for is the one the server asks for.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from crm.api import appointments as agenda
from crm.fcrm.doctype.crm_deal.crm_deal import create_deal
from crm.permissions import documenti, livelli, org_hierarchy, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.tests import con_whatsapp
from crm.tests.test_scheduling import SchedulingCase

DESK = "scope.desk@example.com"
DOC = "scope.doctor@example.com"
DOC2 = "scope.doctor2@example.com"
SALES = "scope.sales@example.com"
MANAGER = "scope.manager@example.com"
DIRECTOR = "scope.director@example.com"

LIVELLI = (
	(DESK, "segreteria"),
	(DOC, "operatore"),
	(DOC2, "operatore"),
	(SALES, "commerciale"),
	(MANAGER, "manager"),
	(DIRECTOR, "direzione"),
)


def persona(nome, **valori):
	return frappe.get_doc(
		{"doctype": "CRM Lead", "first_name": nome, "last_name": "Ambito", **valori}
	).insert(ignore_permissions=True)


def scritto(doctype, **valori):
	"""A row written straight to the table: what is tested is who reads it."""
	doc = frappe.get_doc({"doctype": doctype, **valori})
	doc.name = frappe.generate_hash(length=12)
	doc.db_insert()
	return doc.name


class Livelli:
	def prepara_livelli(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "clinica", "status": "Active"}])
		piano.save()
		livelli.dimentica_cache()
		utenti.sincronizza()
		for user, livello in LIVELLI:
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def vede(self, user, doctype, nome) -> bool:
		"""The list and the record agree: both say yes, or both say no."""
		self.come(user)
		try:
			in_lista = nome in frappe.get_list(doctype, pluck="name", limit_page_length=0)
			nel_record = bool(frappe.has_permission(doctype, "read", doc=nome))
			self.assertEqual(in_lista, nel_record, f"{user} {doctype} {nome}: list and record disagree")
			return in_lista
		finally:
			frappe.set_user("Administrator")
			livelli.dimentica_cache()


class LePersone(Livelli, SchedulingCase):
	def setUp(self):
		super().setUp()
		self.prepara_livelli()
		for user in (DOC, DOC2):
			self.make_user(user)
		self.servizio = self.make_service("Visita ambito", [DOC, DOC2])
		self.sua = persona("Sua", lead_owner=SALES)
		self.di_nessuno = persona("Nessuno")
		self.in_cura = persona("Curata")
		self.make_appointment(
			self.servizio.name,
			self.tomorrow(9),
			[DOC],
			participants=[
				{"party_type": "CRM Lead", "party": self.in_cura.name, "participant_name": "Curata"}
			],
		)

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()

	def test_la_segreteria_e_il_manager_vedono_tutto_il_centro(self):
		for user in (DESK, MANAGER):
			for lead in (self.sua, self.di_nessuno, self.in_cura):
				self.assertTrue(self.vede(user, "CRM Lead", lead.name), (user, lead.first_name))

	def test_l_operatore_vede_chi_ha_in_cura(self):
		self.assertTrue(self.vede(DOC, "CRM Lead", self.in_cura.name))
		self.assertFalse(self.vede(DOC, "CRM Lead", self.di_nessuno.name))
		self.assertFalse(self.vede(DOC, "CRM Lead", self.sua.name))
		self.assertFalse(self.vede(DOC2, "CRM Lead", self.in_cura.name))

	def test_la_cartella_fa_la_cura(self):
		frappe.get_doc(
			{
				"doctype": "Clinic Record",
				"lead": self.di_nessuno.name,
				"practitioner": DOC2,
				"content": "<p>Prima visita</p>",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(self.vede(DOC2, "CRM Lead", self.di_nessuno.name))

	def test_il_commerciale_vede_le_sue(self):
		self.assertTrue(self.vede(SALES, "CRM Lead", self.sua.name))
		self.assertFalse(self.vede(SALES, "CRM Lead", self.di_nessuno.name))

	def test_un_assegnazione_chiusa_da_tempo_non_apre_piu(self):
		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"reference_type": "CRM Lead",
				"reference_name": self.di_nessuno.name,
				"allocated_to": SALES,
				"description": "Richiamare",
				"status": "Closed",
			}
		).insert(ignore_permissions=True)
		# an assignment makes its person the assignee's: owned by somebody else, only
		# the assignment is left to open it
		frappe.db.set_value("CRM Lead", self.di_nessuno.name, "lead_owner", MANAGER)
		self.assertTrue(self.vede(SALES, "CRM Lead", self.di_nessuno.name))
		lontano = add_days(now_datetime(), -(org_hierarchy.GIORNI_ASSEGNAZIONE_CHIUSA + 10))
		frappe.db.set_value("ToDo", todo.name, "modified", lontano, update_modified=False)
		self.assertFalse(self.vede(SALES, "CRM Lead", self.di_nessuno.name))


class GliAppuntamenti(Livelli, SchedulingCase):
	def setUp(self):
		super().setUp()
		self.prepara_livelli()
		for user in (DOC, DOC2):
			self.make_user(user)
		self.servizio = self.make_service("Visita agenda", [DOC, DOC2])
		self.sua = persona("Sua", lead_owner=SALES)
		self.altra = persona("Altra")

		def appuntamento(ora, medico, lead):
			return self.make_appointment(
				self.servizio.name,
				self.tomorrow(ora),
				[medico],
				participants=[
					{"party_type": "CRM Lead", "party": lead.name, "participant_name": lead.first_name}
				],
			).name

		self.del_primo = appuntamento(9, DOC, self.altra)
		self.del_secondo = appuntamento(11, DOC2, self.altra)
		self.della_sua = appuntamento(13, DOC2, self.sua)

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()

	def test_la_segreteria_vede_l_agenda_di_tutti(self):
		for nome in (self.del_primo, self.del_secondo, self.della_sua):
			self.assertTrue(self.vede(DESK, "CRM Appointment", nome))

	def test_l_operatore_la_sua(self):
		self.assertTrue(self.vede(DOC, "CRM Appointment", self.del_primo))
		self.assertFalse(self.vede(DOC, "CRM Appointment", self.del_secondo))

	def test_il_commerciale_le_sue_persone_e_il_resto_occupato(self):
		self.assertTrue(self.vede(SALES, "CRM Appointment", self.della_sua))
		self.assertFalse(self.vede(SALES, "CRM Appointment", self.del_primo))
		self.come(SALES)
		giorno = self.tomorrow(0).date().isoformat()
		calendario = agenda.get_calendar(giorno, giorno, include_events=False)
		self.assertIn(self.della_sua, [a["name"] for a in calendario["appointments"]])
		self.assertNotIn(self.del_primo, [a["name"] for a in calendario["appointments"]])
		# the other two appointments of our practitioners, among whatever else the day holds
		dei_medici = [b for b in calendario["busy"] if {s["user"] for s in b["staff"]} & {DOC, DOC2}]
		self.assertEqual(len(dei_medici), 2)
		for occupato in calendario["busy"]:
			# when, and who works it: never who comes or why
			self.assertEqual(
				set(occupato), {"starts_on", "ends_on", "start_utc", "end_utc", "staff", "resources"}
			)
		# who sees the whole agenda has no busy time to be shown
		self.come(DESK)
		self.assertEqual(agenda.get_calendar(giorno, giorno, include_events=False)["busy"], [])

	def test_l_operatore_prenota_solo_nella_sua_agenda(self):
		def nuovo(medico):
			return frappe.get_doc(
				{"doctype": "CRM Appointment", "service": self.servizio.name, "staff": [{"user": medico}]}
			)

		self.assertTrue(frappe.has_permission("CRM Appointment", "create", doc=nuovo(DOC), user=DOC))
		livelli.dimentica_cache()
		self.assertFalse(frappe.has_permission("CRM Appointment", "create", doc=nuovo(DOC2), user=DOC))

	def test_elimina_solo_il_manager(self):
		self.assertFalse(frappe.has_permission("CRM Appointment", "delete", doc=self.del_primo, user=DESK))
		livelli.dimentica_cache()
		self.assertTrue(frappe.has_permission("CRM Appointment", "delete", doc=self.del_primo, user=MANAGER))


class IMessaggiEIlTracciamento(Livelli, IntegrationTestCase):
	def setUp(self):
		self.prepara_livelli()
		self.sua = persona("Sua", lead_owner=SALES)
		self.altra = persona("Altra")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def messaggio(self, doctype, lead=None):
		valori = {"reference_doctype": "CRM Lead", "reference_name": lead.name} if lead else {}
		return scritto(doctype, **valori)

	def test_whatsapp_e_sms_seguono_la_persona(self):
		# WhatsApp's messages where the bench has frappe_whatsapp
		messaggi = ["CRM SMS Message", *(["WhatsApp Message"] if con_whatsapp() else [])]
		for doctype in messaggi:
			sulla_sua = self.messaggio(doctype, self.sua)
			sull_altra = self.messaggio(doctype, self.altra)
			di_nessuno = self.messaggio(doctype)
			self.assertTrue(self.vede(SALES, doctype, sulla_sua), doctype)
			self.assertFalse(self.vede(SALES, doctype, sull_altra), doctype)
			self.assertTrue(self.vede(SALES, doctype, di_nessuno), doctype)
			self.assertTrue(self.vede(DESK, doctype, sull_altra), doctype)
			# the medical director does not converse: no messages at all
			self.assertFalse(self.vede(DIRECTOR, doctype, di_nessuno), doctype)

	def test_il_tracciamento_segue_la_persona(self):
		della_sua = scritto("CRM Visitor", lead=self.sua.name)
		dell_altra = scritto("CRM Visitor", lead=self.altra.name)
		anonimo = scritto("CRM Visitor")
		self.assertTrue(self.vede(SALES, "CRM Visitor", della_sua))
		self.assertFalse(self.vede(SALES, "CRM Visitor", dell_altra))
		# the traffic that is nobody yet is for whoever handles tracking
		self.assertFalse(self.vede(SALES, "CRM Visitor", anonimo))
		self.assertFalse(self.vede(DESK, "CRM Visitor", anonimo))
		self.assertTrue(self.vede(DESK, "CRM Visitor", dell_altra))
		self.assertTrue(self.vede(MANAGER, "CRM Visitor", anonimo))


class IDocumentiDelManager(Livelli, IntegrationTestCase):
	def setUp(self):
		self.prepara_livelli()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def puo(self, chi, doctype, ptype="create", **valori) -> bool:
		livelli.dimentica_cache()
		doc = frappe.get_doc({"doctype": doctype, **valori})
		return bool(frappe.has_permission(doctype, ptype, doc=doc, user=chi))

	def test_servizi_listini_fasi_e_modelli_al_manager(self):
		doctypes = ["CRM Service", "CRM Price List", "CRM Lead Status"]
		# WhatsApp's templates where the bench has frappe_whatsapp
		doctypes += ["WhatsApp Templates"] if con_whatsapp() else []
		for doctype in doctypes:
			self.assertFalse(self.puo(DESK, doctype), doctype)
			self.assertFalse(self.puo(SALES, doctype), doctype)
			self.assertTrue(self.puo(MANAGER, doctype), doctype)

	def test_turni_e_sale(self):
		self.assertTrue(self.puo(DESK, "CRM Staff Schedule", user=DOC))
		self.assertTrue(self.puo(DOC, "CRM Staff Schedule", user=DOC))
		self.assertFalse(self.puo(DOC2, "CRM Staff Schedule", user=DOC))
		self.assertTrue(self.puo(DESK, "CRM Resource"))
		self.assertFalse(self.puo(DOC, "CRM Resource"))

	def test_le_proprie_viste_e_il_proprio_telefono(self):
		self.assertTrue(self.puo(SALES, "CRM View Settings", user=SALES, public=0))
		self.assertFalse(self.puo(SALES, "CRM View Settings", public=1))
		self.assertTrue(self.puo(MANAGER, "CRM View Settings", public=1))
		self.assertTrue(self.puo(SALES, "CRM Telephony Agent", user=SALES))
		self.assertFalse(self.puo(SALES, "CRM Telephony Agent", user=DESK))
		self.assertTrue(self.puo(MANAGER, "CRM Telephony Agent", user=DESK))

	def test_leggere_non_cambia(self):
		self.assertTrue(self.puo(DESK, "CRM Service", ptype="read"))

	def test_ogni_documento_ha_il_suo_hook(self):
		"""The list and hooks.py cannot drift apart: a document in the list without its
		hook would be written by anyone again."""
		registrati = frappe.get_hooks("has_permission")
		for doctype in documenti.SCRITTURA:
			self.assertIn("crm.permissions.documenti.has_permission", registrati.get(doctype, []), doctype)


class LaTrattativa(Livelli, IntegrationTestCase):
	def setUp(self):
		self.prepara_livelli()
		self.altra = persona("Altra")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def test_non_si_apre_su_chi_non_si_vede(self):
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			create_deal({"lead": self.altra.name})
