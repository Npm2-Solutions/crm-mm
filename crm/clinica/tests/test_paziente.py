# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Becoming a patient, on a real site: the rules, the one door, the recovery.

Nobody has to remember to "convert" anybody. The first sign that the person came,
or the first healthcare invoice, writes the card; with the clinic off in the plan
nothing does; and switched on over old data the clinic finds its patients alone.
"""

import datetime

import frappe

from crm.clinica import paziente, regole
from crm.clinica.eventi import persona_in_cancellazione
from crm.invoicing.install import semina_qualifiche
from crm.moduli import consensi
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

# modules, not classes: a TestCase imported here would run here too
from crm.tests import test_invoicing as fatturazione
from crm.tests.test_scheduling import SchedulingCase

CF = "RSSMRA80A01H501U"
DESK = "clinic.desk@example.com"
SALES = "clinic.sales@example.com"


class ClinicCase(SchedulingCase):
	def setUp(self):
		super().setUp()
		self.doctor = self.make_user("clinic.doctor@example.com")
		self.service = self.make_service("Visita clinica", [self.doctor])
		self.mario = self.persona("Mario", "Paziente")
		self.accendi(True)

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()

	def accendi(self, acceso: bool):
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [])
		if acceso:
			piano.append("modules", {"module": "clinica", "status": "Active"})
		piano.save()
		livelli.dimentica_cache()

	@staticmethod
	def persona(nome, cognome, **valori):
		return frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": nome, "last_name": cognome, **valori}
		).insert(ignore_permissions=True)

	def appuntamento(self, persona, quando, stato="Confirmed", presenza="Booked", servizio=None):
		return self.make_appointment(
			servizio or self.service.name,
			quando,
			[self.doctor],
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

	def scheda(self, persona):
		return frappe.db.get_value(
			"Clinic Patient",
			persona.name,
			["rule", "patient_since", "source_doctype", "source_name", "recorded_by"],
			as_dict=True,
		)


class LeRegole(ClinicCase):
	def test_un_appuntamento_svolto_fa_un_paziente(self):
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		scheda = self.scheda(self.mario)
		self.assertEqual(scheda.rule, regole.APPUNTAMENTO_SVOLTO.valore)
		self.assertEqual(scheda.source_name, incontro.name)
		self.assertEqual(scheda.patient_since, incontro.starts_on)

	def test_basta_il_partecipante_presente(self):
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.participants[0].status = "Attended"
		incontro.save()
		self.assertTrue(paziente.e_paziente(self.mario.name))

	def test_chi_non_e_venuto_resta_un_contatto(self):
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.participants[0].status = "No Show"
		incontro.status = "Completed"
		incontro.save()
		self.assertFalse(paziente.e_paziente(self.mario.name))

	def test_con_la_clinica_spenta_nessuno_diventa_paziente(self):
		self.accendi(False)
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		self.assertFalse(paziente.e_paziente(self.mario.name))

	def test_la_prima_regola_vince_e_le_altre_non_fanno_niente(self):
		paziente.assicura_paziente(self.mario.name, regole.A_MANO, nota="lo conosco")
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		self.assertEqual(self.scheda(self.mario).rule, regole.A_MANO.valore)
		self.assertEqual(frappe.db.count("Clinic Patient", {"lead": self.mario.name}), 1)

	def test_un_servizio_non_sanitario_non_fa_pazienti(self):
		semina_qualifiche()
		corso = self.make_service("Corso di yoga", [self.doctor])
		frappe.get_doc(
			{
				"doctype": "CRM Billable Service",
				"service_name": "Corso di yoga (fattura)",
				"fiscal_description": "Corso di yoga",
				"crm_service": corso.name,
				"is_healthcare": 0,
				"vat_rate": 22,
				"default_rate": 50,
				"enabled": 1,
			}
		).insert()
		incontro = self.appuntamento(self.mario, self.ieri(), servizio=corso.name)
		incontro.status = "Completed"
		incontro.save()
		self.assertFalse(paziente.e_paziente(self.mario.name))

	def professionista(self, utente, sanitaria: bool):
		"""``utente`` with a qualification of the register: a health profession, or not."""
		codice = "prova_sanitaria" if sanitaria else "prova_non_sanitaria"
		if not frappe.db.exists("CRM Professional Qualification", codice):
			frappe.get_doc(
				{
					"doctype": "CRM Professional Qualification",
					"code": codice,
					"qualification_name": codice,
					"category": "sanitaria" if sanitaria else "non_ordinistica",
					"sender_category": "professionista_sanitario" if sanitaria else "non_sanitario",
					"is_healthcare": int(sanitaria),
					"sdi_rule": "vietato" if sanitaria else "obbligatorio",
				}
			).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "CRM Service Provider",
				"provider_name": f"{utente} ({codice})",
				"qualification": codice,
				"user": utente,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

	def test_la_lezione_del_chinesiologo_non_fa_pazienti(self):
		"""Pilates with the kinesiologist alone: no health profession is there
		(Ris. AdE 9/2026), and whoever comes stays a client."""
		chinesiologo = self.make_user("clinic.kinesiologist@example.com")
		self.professionista(chinesiologo, sanitaria=False)
		pilates = self.make_service("Pilates di prova", [chinesiologo])
		incontro = self.make_appointment(
			pilates.name,
			self.ieri(),
			[chinesiologo],
			status="Completed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": self.mario.name,
					"participant_name": self.mario.lead_name,
					"status": "Attended",
				}
			],
		)
		self.assertFalse(paziente.e_paziente(self.mario.name))
		# whoever came is a client, as in any centre
		self.assertIsNotNone(frappe.db.get_value("CRM Lead", self.mario.name, "client_since"))
		self.assertEqual(frappe.db.get_value("CRM Lead", self.mario.name, "relationship"), "Client")
		# the same class with a physiotherapist beside him is the clinic's
		fisioterapista = self.make_user("clinic.physio@example.com")
		self.professionista(fisioterapista, sanitaria=True)
		incontro.append("staff", {"user": fisioterapista})
		incontro.save()
		self.assertTrue(paziente.e_paziente(self.mario.name))
		self.assertEqual(frappe.db.get_value("CRM Lead", self.mario.name, "relationship"), "Patient")

	def test_l_importazione(self):
		frappe.flags.in_import = True
		try:
			frappe.get_doc({"doctype": "Clinic Patient", "lead": self.mario.name}).insert()
		finally:
			frappe.flags.in_import = False
		self.assertEqual(self.scheda(self.mario).rule, regole.IMPORTAZIONE.valore)

	def test_un_paziente_non_si_cancella(self):
		paziente.assicura_paziente(self.mario.name, regole.A_MANO)
		with self.assertRaises(frappe.LinkExistsError):
			persona_in_cancellazione(self.mario)


class LaFattura(ClinicCase):
	def setUp(self):
		super().setUp()
		semina_qualifiche()
		self.azienda = fatturazione.InvoicingBase.crea_azienda()
		self.psicologo = fatturazione.InvoicingBase.crea_erogatore("Dott.ssa Bianchi", "psicologo")
		self.seduta = fatturazione.InvoicingBase.crea_servizio(
			"Seduta di psicoterapia", healthcare=True, exempt=True
		)
		self.corso = fatturazione.InvoicingBase.crea_servizio("Consulenza", healthcare=False, exempt=False)

	def fattura(self, persona, servizio, data=None):
		documento = frappe.get_doc(
			{
				"doctype": "CRM Invoice",
				"company": self.azienda.name,
				"recipient_type": "persona_fisica",
				"party_type": "CRM Lead",
				"party": persona.name,
				"first_name": persona.first_name,
				"last_name": persona.last_name,
				"billing_name": persona.lead_name,
				"fiscal_code": CF,
				"address_line": "Via Verdi 3",
				"postal_code": "00100",
				"city": "Roma",
				"province": "RM",
				"payment_method": "MP08",
				"posting_date": data or frappe.utils.nowdate(),
				"items": [
					{
						"billable_service": servizio.name,
						"service_provider": self.psicologo.name,
						"qty": 1,
						"rate": 100,
					}
				],
			}
		).insert()
		documento.submit()
		return documento

	def test_una_fattura_sanitaria_fa_un_paziente(self):
		documento = self.fattura(self.mario, self.seduta)
		scheda = self.scheda(self.mario)
		self.assertEqual(scheda.rule, regole.FATTURA_SANITARIA.valore)
		self.assertEqual(scheda.source_name, documento.name)

	def test_un_corso_o_un_abbonamento_no(self):
		self.fattura(self.mario, self.corso)
		self.assertFalse(paziente.e_paziente(self.mario.name))
		# a client, who bought something
		self.assertEqual(frappe.db.get_value("CRM Lead", self.mario.name, "relationship"), "Client")

	def test_il_recupero_trova_i_pazienti_di_prima(self):
		"""Switched on over old data: the earliest fact of each person converts, with its date."""
		self.accendi(False)
		lucia = self.persona("Lucia", "Primafattura")
		gianni = self.persona("Gianni", "Mainvenuto")
		# Mario came in person two days ago
		incontro = self.appuntamento(self.mario, self.ieri())
		incontro.status = "Completed"
		incontro.save()
		# Lucia: a healthcare invoice in January, then an appointment
		self.fattura(lucia, self.seduta, data="2026-01-15")
		incontro_lucia = self.appuntamento(lucia, self.ieri(12))
		incontro_lucia.participants[0].status = "Attended"
		incontro_lucia.save()
		# Gianni booked and never came
		mancato = self.appuntamento(gianni, self.ieri(14))
		mancato.participants[0].status = "No Show"
		mancato.save()
		self.assertFalse(paziente.e_paziente(self.mario.name) or paziente.e_paziente(lucia.name))

		self.accendi(True)
		# the site may hold patients of its own: ours are two of them
		self.assertGreaterEqual(paziente.recupera(), 2)
		self.assertEqual(self.scheda(self.mario).rule, regole.APPUNTAMENTO_SVOLTO.valore)
		lucia_scheda = self.scheda(lucia)
		self.assertEqual(lucia_scheda.rule, regole.FATTURA_SANITARIA.valore)
		self.assertEqual(lucia_scheda.patient_since.date(), datetime.date(2026, 1, 15))
		self.assertFalse(lucia_scheda.recorded_by)
		self.assertFalse(paziente.e_paziente(gianni.name))
		# once is once: nothing new the second time
		self.assertEqual(paziente.recupera(), 0)


class ChiLoVede(ClinicCase):
	def setUp(self):
		super().setUp()
		utenti.sincronizza()
		for user in (DESK, SALES):
			make_user(user)
		utenti.assegna_livelli(DESK, ["segreteria"])
		utenti.assegna_livelli(SALES, ["commerciale"])
		frappe.db.set_value("CRM Lead", self.mario.name, "lead_owner", DESK)
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def test_la_segreteria_lo_segna_a_mano(self):
		self.come(DESK)
		stato = paziente.patient_status(self.mario.name)
		self.assertIsNone(stato["patient"])
		self.assertTrue(stato["can_mark"])
		stato = paziente.mark_as_patient(self.mario.name, "Paziente del vecchio studio")
		self.assertEqual(stato["patient"]["rule"], regole.A_MANO.valore)
		self.assertEqual(stato["patient"]["recorded_by"], DESK)
		self.assertFalse(stato["can_mark"])

	def test_il_commerciale_non_sa_chi_e_paziente(self):
		frappe.db.set_value("CRM Lead", self.mario.name, "lead_owner", SALES)
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			paziente.patient_status(self.mario.name)

	def test_a_clinica_spenta_non_c_e_niente_da_vedere(self):
		self.accendi(False)
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			paziente.patient_status(self.mario.name)

	def test_il_commerciale_non_vede_i_consensi_della_clinica(self):
		"""An answer about a health dossier says the person is a patient."""
		consensi.assicura_tipi()
		consensi.registra_risposta(self.mario.name, "health_dossier")
		frappe.db.set_value("CRM Lead", self.mario.name, "lead_owner", SALES)
		self.come(SALES)
		tipi = [t["key"] for t in consensi.get_consents(self.mario.name)["types"]]
		self.assertNotIn("health_dossier", tipi)
		self.assertIn("marketing", tipi)
		self.assertFalse(frappe.get_list("CRM Consent", filters={"lead": self.mario.name}, pluck="name"))
		with self.assertRaises(frappe.PermissionError):
			consensi.record_consent(self.mario.name, "online_reports", "Given", "At the desk")

	def test_i_consensi_della_clinica_solo_con_la_clinica(self):
		consensi.assicura_tipi()
		self.come(DESK)
		tipi = [t["key"] for t in consensi.get_consents(self.mario.name)["types"]]
		self.assertIn("health_dossier", tipi)
		frappe.set_user("Administrator")
		self.accendi(False)
		self.come(DESK)
		tipi = [t["key"] for t in consensi.get_consents(self.mario.name)["types"]]
		self.assertNotIn("health_dossier", tipi)
		self.assertIn("marketing", tipi)


class LaVisitaAllAppuntamento(ClinicCase):
	"""A visit written from the Clinic tab at the person's appointment says they
	came: the tab never named the appointment, and the agenda left them «Booked»
	(the simulation of a week found it)."""

	def setUp(self):
		super().setUp()
		from crm.scheduling.timeutils import UTC

		utenti.sincronizza()
		utenti.assegna_livelli(self.doctor, ["operatore"])
		adesso = datetime.datetime.now(UTC).replace(second=0, microsecond=0)
		self.incontro = self.appuntamento(self.mario, adesso - datetime.timedelta(minutes=10))
		livelli.dimentica_cache()

	def scrive(self, **valori):
		from crm.clinica import cartella

		frappe.set_user(self.doctor)
		livelli.dimentica_cache()
		try:
			return cartella.save_record(self.mario.name, content="<p>Visita.</p>", **valori)
		finally:
			frappe.set_user("Administrator")

	def presenza(self):
		return frappe.db.get_value(
			"CRM Appointment Participant", {"parent": self.incontro.name, "party": self.mario.name}, "status"
		)

	def test_la_visita_all_appuntamento_dice_che_e_venuto(self):
		visita = self.scrive()
		self.assertEqual(
			frappe.db.get_value("Clinic Record", visita["name"], "appointment"), self.incontro.name
		)
		self.assertEqual(self.presenza(), "Attended")

	def test_una_nota_non_dice_niente(self):
		nota = self.scrive(kind="Note")
		self.assertFalse(frappe.db.get_value("Clinic Record", nota["name"], "appointment"))
		self.assertEqual(self.presenza(), "Booked")

	def test_l_appuntamento_di_un_collega_non_e_il_suo(self):
		from crm.clinica import cartella

		collega = self.make_user("clinic.colleague@example.com")
		self.assertIsNone(cartella.appuntamento_in_corso(self.mario.name, collega))
		# nor tomorrow's
		self.incontro.db_set("starts_on", self.incontro.starts_on + datetime.timedelta(days=1))
		self.assertIsNone(cartella.appuntamento_in_corso(self.mario.name, self.doctor))
