# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Linked people on a real site: the family on the booking page, the invoice to
whoever pays, the consent given by a parent, the person's page.

A mother booking for her son with her own email used to land on her own record, or
to give the boy her email - and the next booking, hers, went to him. Now the
contact finds its owner and the name finds the person: the child gets a record of
his own, linked to her, without her contact.
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import appointments
from crm.api.doc import get_linked_docs_of_document
from crm.clinica import paziente
from crm.moduli import consensi
from crm.patches.v1_0 import guardians_become_linked_people
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.persone import collegate, legami
from crm.scheduling.availability import forget_settings

# the modules, not the classes: a TestCase imported here would run here too
from crm.tests import test_billing_profile as profili
from crm.tests import test_service_booking as prenotazioni
from crm.tests.test_scheduling import SchedulingCase

DESK = "related.desk@example.com"
SALES = "related.sales@example.com"
MAMMA = "maria.famiglia@example.com"


def persona(nome, cognome="Rossi", **valori):
	return frappe.get_doc({"doctype": "CRM Lead", "first_name": nome, "last_name": cognome, **valori}).insert(
		ignore_permissions=True
	)


def legame(figlio, genitore, relazione=legami.GENITORE, **azioni):
	return frappe.get_doc(
		{
			"doctype": "CRM Related Person",
			"person": figlio,
			"related_person": genitore,
			"relation": relazione,
			**azioni,
		}
	).insert(ignore_permissions=True)


class RelatedCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.maria = persona("Maria", email=MAMMA)
		self.luca = persona("Luca")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()


class IlLegame(RelatedCase):
	def test_una_riga_per_coppia_da_qualunque_lato(self):
		legame(self.luca.name, self.maria.name)
		with self.assertRaises(frappe.DuplicateEntryError):
			legame(self.maria.name, self.luca.name, legami.FIGLIO)

	def test_nessuno_e_legato_a_se_stesso(self):
		with self.assertRaises(frappe.ValidationError):
			legame(self.luca.name, self.luca.name)

	def test_scritto_dalla_madre_si_legge_dal_figlio(self):
		collegate.save_related_person(
			self.maria.name,
			relation=legami.FIGLIO,
			acts=legami.IO_PER_LORO,
			other=self.luca.name,
			pays=1,
			books="1",
			represents="0",
		)
		riga = frappe.get_all("CRM Related Person", fields=["*"], filters={"person": self.luca.name})[0]
		self.assertEqual((riga.related_person, riga.relation), (self.maria.name, legami.GENITORE))
		self.assertEqual((riga.pays, riga.books, riga.represents), (1, 1, 0))

		dal_figlio = collegate.get_related_people(self.luca.name)["people"][0]
		self.assertEqual(
			(dal_figlio["other"], dal_figlio["relation"], dal_figlio["acts"]),
			(self.maria.name, legami.GENITORE, legami.LORO_PER_ME),
		)
		dalla_madre = collegate.get_related_people(self.maria.name)["people"][0]
		self.assertEqual(
			(dalla_madre["other"], dalla_madre["relation"], dalla_madre["acts"]),
			(self.luca.name, legami.FIGLIO, legami.IO_PER_LORO),
		)

	def test_senza_nessuno_che_agisce_niente_bandierine(self):
		collegate.save_related_person(
			self.maria.name, relation=legami.PARTNER, other=self.luca.name, pays=1, books=1
		)
		riga = frappe.get_all("CRM Related Person", fields=["pays", "books", "represents"])[0]
		self.assertEqual((riga.pays, riga.books, riga.represents), (0, 0, 0))

	def test_una_persona_nuova_dal_legame(self):
		pagina = collegate.save_related_person(
			self.maria.name,
			relation=legami.FIGLIO,
			acts=legami.IO_PER_LORO,
			first_name="Anna",
			last_name="Rossi",
			books=1,
		)
		anna = pagina["people"][0]
		self.assertEqual(anna["other_name"], "Anna Rossi")
		self.assertFalse(frappe.db.get_value("CRM Lead", anna["other"], "email"))

	def test_chi_paga_chi_decide(self):
		legame(self.luca.name, self.maria.name, pays=1, represents=1)
		self.assertEqual(collegate.pagante_di(self.luca.name), self.maria.name)
		self.assertEqual(collegate.rappresentanti_di(self.luca.name), [self.maria.name])
		# two paying is a choice made invoice by invoice
		paolo = persona("Paolo")
		legame(self.luca.name, paolo.name, pays=1)
		self.assertIsNone(collegate.pagante_di(self.luca.name))

	def test_raggiunto_tramite_chi_prenota(self):
		legame(self.luca.name, self.maria.name, books=1)
		pagina = collegate.get_related_people(self.luca.name)
		self.assertEqual(pagina["reached_through"], ["Maria Rossi"])
		contatto = collegate.get_contact_for(self.luca.name)
		self.assertEqual((contatto["email"], contatto["booked_by"]), (MAMMA, self.maria.name))
		# with a contact of their own they are reached directly
		self.assertEqual(collegate.get_contact_for(self.maria.name)["booked_by"], None)

	def test_se_ne_va_con_la_persona(self):
		legame(self.luca.name, self.maria.name)
		self.assertNotIn(
			"CRM Related Person",
			[d["reference_doctype"] for d in get_linked_docs_of_document("CRM Lead", self.luca.name)],
		)
		frappe.db.delete(
			"CRM Automation Enrollment", {"reference_doctype": "CRM Lead", "reference_name": self.maria.name}
		)
		frappe.delete_doc("CRM Lead", self.maria.name, ignore_permissions=True)
		self.assertFalse(frappe.db.exists("CRM Related Person", {"person": self.luca.name}))

	def test_la_famiglia_arriva_ai_legami_dei_legami(self):
		paolo = persona("Paolo")
		legame(self.luca.name, self.maria.name)
		legame(self.luca.name, paolo.name)
		self.assertEqual(set(collegate.famiglia(self.maria.name)), {self.luca.name, paolo.name})


class ChiLiVede(RelatedCase):
	def setUp(self):
		super().setUp()
		for user, livello in ((DESK, "segreteria"), (SALES, "commerciale")):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		# the salesperson works on Luca, not on his mother; the desk on both
		self.assegna(self.luca.name, SALES)
		self.assegna(self.luca.name, DESK)
		self.assegna(self.maria.name, DESK)
		legame(self.luca.name, self.maria.name)
		livelli.dimentica_cache()

	@staticmethod
	def assegna(lead, user):
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"reference_type": "CRM Lead",
				"reference_name": lead,
				"allocated_to": user,
				"description": lead,
			}
		).insert(ignore_permissions=True)

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def test_il_legame_si_vede_da_chi_vede_uno_dei_due(self):
		self.come(SALES)
		persone = collegate.get_related_people(self.luca.name)["people"]
		self.assertEqual(persone[0]["other"], self.maria.name)
		self.assertFalse(persone[0]["can_open"])
		with self.assertRaises(frappe.PermissionError):
			collegate.get_related_people(self.maria.name)

	def test_non_si_lega_chi_non_si_vede(self):
		altra = persona("Sofia", "Bianchi")
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			collegate.save_related_person(self.luca.name, relation=legami.FAMILIARE, other=altra.name)

	def test_la_segreteria_lega_e_slega(self):
		anna = persona("Anna")
		self.assegna(anna.name, DESK)
		self.come(DESK)
		pagina = collegate.save_related_person(
			self.maria.name, relation=legami.FIGLIO, acts=legami.IO_PER_LORO, other=anna.name, books=1
		)
		self.assertEqual(len(pagina["people"]), 2)
		riga = next(p for p in pagina["people"] if p["other"] == anna.name)
		self.assertEqual(len(collegate.remove_related_person(self.maria.name, riga["name"])["people"]), 1)


class LeFamiglieSuPrenota(SchedulingCase):
	"""Who the appointment is for, on the email a family shares."""

	online_service = prenotazioni.TestServiceBooking.online_service
	book = prenotazioni.TestServiceBooking.book

	def setUp(self):
		super().setUp()
		self.with_settings(
			online_booking_enabled=1,
			require_privacy_consent=0,
			ask_marketing_consent=0,
			max_active_per_customer=0,
			default_min_notice_hours=0,
			default_max_horizon_days=30,
			default_require_phone=0,
			default_online_confirmation="Automatic",
		)
		self.anna = self.make_user("anna.family@example.com")
		self.bruno = self.make_user("bruno.family@example.com")
		self.servizio = self.online_service()
		self._mail = patch("frappe.sendmail")
		self.mail = self._mail.start()

	def tearDown(self):
		self._mail.stop()
		super().tearDown()

	def with_settings(self, **values):
		settings = frappe.get_doc("CRM Scheduling Settings")
		settings.update(values)
		settings.save()
		forget_settings()

	def riga(self, risultato):
		return frappe.get_doc("CRM Appointment Participant", {"access_token": risultato["token"]})

	def prenota(self, ora, **kw):
		kw.setdefault("full_name", "Maria Rossi")
		return self.book(self.servizio, self.tomorrow(ora), email=MAMMA, **kw)

	def test_la_madre_prenota_per_il_figlio(self):
		riga = self.riga(self.prenota(9, for_name="Luca Rossi", for_relation=legami.GENITORE))
		maria = frappe.db.get_value("CRM Lead", {"email": MAMMA}, "name")
		self.assertNotEqual(riga.party, maria)
		self.assertEqual(frappe.db.get_value("CRM Lead", riga.party, "lead_name"), "Luca Rossi")
		# the contact stays hers: on the booking, not on his record
		self.assertFalse(frappe.db.get_value("CRM Lead", riga.party, "email"))
		self.assertEqual((riga.email, riga.booked_by, riga.participant_name), (MAMMA, maria, "Luca Rossi"))
		legame_ = frappe.get_all(
			"CRM Related Person",
			filters={"person": riga.party},
			fields=["related_person", "relation", "books"],
		)[0]
		self.assertEqual((legame_.related_person, legame_.relation, legame_.books), (maria, "Parent", 1))

	def test_poi_la_madre_prenota_per_se_e_resta_lei(self):
		luca = self.riga(self.prenota(9, for_name="Luca Rossi", for_relation=legami.GENITORE)).party
		lei = self.riga(self.prenota(10)).party
		self.assertNotEqual(lei, luca)
		self.assertEqual(frappe.db.get_value("CRM Lead", lei, "email"), MAMMA)

	def test_col_nome_del_figlio_e_il_figlio_anche_senza_sceglierlo(self):
		luca = self.riga(self.prenota(9, for_name="Luca Rossi", for_relation=legami.GENITORE)).party
		self.assertEqual(self.riga(self.prenota(10, full_name="Luca Rossi")).party, luca)
		# a name nobody has is somebody new, never his mother's record
		nuova = self.riga(self.prenota(11, full_name="Sofia Rossi")).party
		self.assertNotIn(nuova, (luca, frappe.db.get_value("CRM Lead", {"email": MAMMA}, "name")))

	def test_il_padre_con_l_email_della_madre_trova_il_figlio(self):
		luca = self.riga(self.prenota(9, for_name="Luca Rossi", for_relation=legami.GENITORE)).party
		riga = self.riga(
			self.prenota(10, full_name="Paolo Rossi", for_name="Luca Rossi", for_relation=legami.GENITORE)
		)
		self.assertEqual(riga.party, luca)
		self.assertEqual(frappe.db.get_value("CRM Lead", riga.booked_by, "lead_name"), "Paolo Rossi")
		self.assertIn(riga.booked_by, collegate.chi_fa(luca, legami.PRENOTA))

	def test_i_limiti_contano_chi_viene(self):
		self.with_settings(max_active_per_customer=1)
		self.prenota(9, for_name="Luca Rossi", for_relation=legami.GENITORE)
		self.prenota(10, for_name="Anna Rossi", for_relation=legami.GENITORE)
		self.prenota(11)
		with self.assertRaises(frappe.ValidationError):
			self.prenota(12, for_name="Luca Rossi", for_relation=legami.GENITORE)

	def test_la_privacy_la_legge_chi_prenota_per_tutti_e_due(self):
		consensi.assicura_tipi()
		self.with_settings(require_privacy_consent=1)
		riga = self.riga(
			self.prenota(
				9, for_name="Luca Rossi", for_relation=legami.GENITORE, consent=1, consent_text="Letto"
			)
		)
		sua = frappe.get_all(
			"CRM Consent",
			filters={"lead": riga.booked_by, "consent_type": "privacy_notice"},
			pluck="given_by",
		)
		del_figlio = frappe.get_all(
			"CRM Consent", filters={"lead": riga.party, "consent_type": "privacy_notice"}, pluck="given_by"
		)
		self.assertEqual(sua, [None])
		self.assertEqual(del_figlio, [riga.booked_by])

	def test_l_email_saluta_chi_ha_prenotato(self):
		self.with_settings(send_client_confirmation=1)
		self.prenota(9, for_name="Luca Rossi", for_relation=legami.GENITORE)
		# the staff are told too: the client's email is the one to her
		alla_madre = [c.kwargs for c in self.mail.call_args_list if c.kwargs.get("recipients") == [MAMMA]]
		self.assertEqual(len(alla_madre), 1)
		self.assertIn("Maria Rossi", alla_madre[0]["message"])
		self.assertIn("Luca Rossi", alla_madre[0]["message"])

	def test_un_titolare_senza_nome_e_lui(self):
		senza_nome = persona(MAMMA, "", email=MAMMA)
		self.assertEqual(self.riga(self.prenota(9, full_name="Giulia Verdi")).party, senza_nome.name)

	def test_la_segreteria_che_modifica_non_perde_chi_ha_prenotato(self):
		riga = self.riga(self.prenota(9, for_name="Luca Rossi", for_relation=legami.GENITORE))
		dati = appointments.get_appointment(riga.parent)
		dati["participants"] = [
			{k: v for k, v in p.items() if k not in ("booked_by", "booked_by_name")}
			for p in dati["participants"]
		]
		appointments.save_appointment(dati, name=riga.parent)
		# the rows are written anew: the one for Luca still says who booked him
		self.assertEqual(
			frappe.db.get_value("CRM Appointment Participant", {"parent": riga.parent}, "booked_by"),
			riga.booked_by,
		)


class LaFatturaAChiPaga(profili.ProfileBase):
	def setUp(self):
		super().setUp()
		self.giulia = self.persona("Giulia", "Rossi")
		self.profilo(self.mario.name, fiscal_code=profili.CF_PAZIENTE, **profili.INDIRIZZO)
		self.profilo(self.giulia.name, fiscal_code=profili.CF_GIULIA)
		legame(self.giulia.name, self.mario.name, pays=1)

	def test_la_visita_della_figlia_va_al_padre(self):
		fattura = self.fattura_a(
			self.giulia, billing_name=None, first_name=None, last_name=None, fiscal_code=None
		)
		self.assertEqual(fattura.fiscal_code, profili.CF_PAZIENTE)
		self.assertEqual((fattura.first_name, fattura.last_name), ("Mario", "Rossi"))
		self.assertEqual(fattura.city, "Roma")
		self.assertIn("Giulia Rossi", fattura.causale)
		self.assertIn(profili.CF_GIULIA, fattura.causale)

	def test_confermata_completa_il_padre_non_la_figlia(self):
		self.fattura_a(
			self.giulia,
			billing_name=None,
			first_name=None,
			last_name=None,
			fiscal_code=None,
			pec="mario@pec.it",
		).submit()
		self.assertEqual(self.del_titolare(self.mario.name).pec, "mario@pec.it")
		self.assertFalse(self.del_titolare(self.giulia.name).pec)

	def test_se_la_cassa_la_intesta_a_lei_completa_lei(self):
		self.fattura_a(
			self.giulia,
			billing_name="Giulia Rossi",
			first_name="Giulia",
			last_name="Rossi",
			fiscal_code=profili.CF_GIULIA,
			pec="giulia@pec.it",
			**profili.INDIRIZZO,
		).submit()
		# the address was written at the desk, not taken from her father's
		self.assertEqual(self.del_titolare(self.giulia.name).city, "Roma")
		self.assertEqual(self.del_titolare(self.giulia.name).pec, "giulia@pec.it")


class IlPazienteMinorenne(profili.ProfileBase):
	def test_minorenne_senza_chi_decide_lo_si_dice(self):
		giulia = self.persona("Giulia", "Rossi")
		self.profilo(giulia.name, fiscal_code=profili.CF_GIULIA)
		stato = paziente._stato(giulia.name)
		self.assertTrue(stato["minor"])
		self.assertEqual(stato["representatives"], [])
		legame(giulia.name, self.mario.name, represents=1)
		self.assertEqual(
			[r["name"] for r in paziente._stato(giulia.name)["representatives"]], [self.mario.name]
		)

	def test_senza_codice_fiscale_non_si_sa(self):
		self.assertIsNone(paziente._stato(self.mario.name)["minor"])


class IlConsensoDatoDaUnGenitore(RelatedCase):
	def setUp(self):
		super().setUp()
		consensi.assicura_tipi()

	def test_solo_chi_e_legato_risponde_per_lui(self):
		estraneo = persona("Sofia", "Bianchi")
		with self.assertRaises(frappe.ValidationError):
			consensi.record_consent(self.luca.name, "privacy_notice", given_by=estraneo.name)
		legame(self.luca.name, self.maria.name, represents=1)
		pagina = consensi.record_consent(self.luca.name, "privacy_notice", given_by=self.maria.name)
		self.assertEqual(pagina["answered_by"][0]["name"], self.maria.name)
		attuale = next(t for t in pagina["types"] if t["key"] == "privacy_notice")["current"]
		self.assertEqual(attuale["given_by_name"], "Maria Rossi")


class LaPatch(RelatedCase):
	def test_il_tutore_della_scheda_diventa_un_legame(self):
		if not frappe.db.has_column("Clinic Patient", "guardian"):
			self.skipTest("the old column was trimmed")
		frappe.get_doc({"doctype": "Clinic Patient", "lead": self.luca.name, "rule": "By hand"}).insert(
			ignore_permissions=True
		)
		frappe.db.sql(
			"update `tabClinic Patient` set guardian=%s, guardian_relation='Legal guardian' where lead=%s",
			(self.maria.name, self.luca.name),
		)
		guardians_become_linked_people.execute()
		riga = frappe.get_all(
			"CRM Related Person",
			filters={"person": self.luca.name},
			fields=["related_person", "relation", "represents"],
		)[0]
		self.assertEqual(
			(riga.related_person, riga.relation, riga.represents), (self.maria.name, "Legal guardian", 1)
		)
