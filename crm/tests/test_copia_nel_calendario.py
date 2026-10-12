# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An appointment's calendar copy reads to its professionals, never to who comes (doc 56).

Dott.ssa Neri and Dott. Verdi see Anna Bianchi together. Anna was picked from the
address book, and the address of her entry is the user of her client area. The
copy is a private Event of Dott.ssa Neri's, its description the appointment's
notes, and it names Anna by her record. When the Event was saved the framework
wrote her entry's address on her row, and a private Event reads to any user whose
name is the address on one of its rows: Anna's area listed the copy and read the
notes, and the events' reminders by email and Google's invitations would go to her.
Only the professionals' rows keep an address now, whatever saves the copy; an
Event the centre makes itself is the framework's.
"""

from unittest import mock

import frappe
import frappe.client
from frappe.utils import add_to_date, now_datetime

from crm.area import accesso
from crm.patches.v1_0 import the_calendar_copy_keeps_no_address_of_who_comes as patch
from crm.patches.v1_0 import the_calendar_copy_sends_no_digest as patch_del_riepilogo
from crm.scheduling.availability import forget_settings
from crm.tests.test_scheduling import SchedulingCase

SERVIZIO = "Fisioterapia in due"
NOTE = "Dolore lombare, peggiora la sera"


class LaCopiaNelCalendario(SchedulingCase):
	def setUp(self):
		super().setUp()
		self.neri = self.make_user("copia.neri@example.com")
		self.verdi = self.make_user("copia.verdi@example.com")
		self.make_service(SERVIZIO, [self.neri, self.verdi], staff_selection="All required")
		frappe.db.set_single_value("CRM Scheduling Settings", "sync_to_event", 1)
		# the engine kept the settings it read before the switch
		forget_settings()

	# -- fixtures ----------------------------------------------------------

	def utente_dell_area(self, email: str) -> str:
		"""A user of the client area: of the site, never of the desk, named by the
		address, as the area makes it."""
		accesso.assicura_ruolo()
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Anna",
				"last_name": "Bianchi",
				"user_type": "Website User",
				"send_welcome_email": 0,
				"roles": [{"role": accesso.RUOLO}],
			}
		).insert(ignore_permissions=True)
		return email

	def voce_della_rubrica(self, email: str) -> str:
		"""An entry of the address book no person's record owns: picked as itself."""
		return (
			frappe.get_doc(
				{
					"doctype": "Contact",
					"first_name": "Anna",
					"last_name": "Bianchi",
					"email_ids": [{"email_id": email, "is_primary": 1}],
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def copia(self, party_type: str, party: str):
		appuntamento = self.make_appointment(
			SERVIZIO,
			self.tomorrow(10),
			[self.neri, self.verdi],
			participants=[{"party_type": party_type, "party": party, "participant_name": "Anna Bianchi"}],
			notes=NOTE,
		)
		appuntamento.reload()
		self.assertTrue(appuntamento.event, "the appointment has its calendar copy")
		return frappe.get_doc("Event", appuntamento.event)

	def evento_del_centro(self, voce: str):
		"""An Event the centre makes itself, with the entry of the address book on it."""
		inizio = add_to_date(now_datetime(), days=1)
		return frappe.get_doc(
			{
				"doctype": "Event",
				"subject": "Telefonata con Anna",
				"event_type": "Private",
				"starts_on": inizio,
				"ends_on": add_to_date(inizio, minutes=30),
				"event_participants": [{"reference_doctype": "Contact", "reference_docname": voce}],
			}
		).insert(ignore_permissions=True)

	def indirizzi(self, evento: str) -> dict:
		"""Each participant row of an Event as it is saved, and the address on it."""
		return {
			(riga.reference_doctype, riga.reference_docname): riga.email or None
			for riga in frappe.get_all(
				"Event Participants",
				filters={"parenttype": "Event", "parent": evento},
				fields=["reference_doctype", "reference_docname", "email"],
			)
		}

	def dei_professionisti(self) -> dict:
		"""The professionals' rows: each by their user, with their own address."""
		return {("User", self.neri): self.neri, ("User", self.verdi): self.verdi}

	def apre(self, utente: str, evento: str) -> bool:
		"""Whether ``utente`` opens the Event by its name."""
		return frappe.has_permission("Event", "read", doc=frappe.get_doc("Event", evento), user=utente)

	def elenco(self, utente: str) -> list[str]:
		"""The Events ``utente`` finds in their list."""
		frappe.set_user(utente)
		try:
			return frappe.get_list("Event", pluck="name", limit_page_length=0)
		finally:
			frappe.set_user("Administrator")

	def letta_solo_dai_professionisti(self, evento: str, anna: str):
		self.assertFalse(self.apre(anna, evento))
		self.assertNotIn(evento, self.elenco(anna))
		for professionista in (self.neri, self.verdi):
			self.assertTrue(self.apre(professionista, evento))
			self.assertIn(evento, self.elenco(professionista))

	# -- the copy ------------------------------------------------------------

	def test_chi_viene_dalla_rubrica_non_legge_la_copia(self):
		anna = self.utente_dell_area("copia.anna@example.com")
		voce = self.voce_della_rubrica(anna)
		copia = self.copia("Contact", voce)
		# Anna by her entry, with no address; the professionals by their users
		self.assertEqual(self.indirizzi(copia.name), {**self.dei_professionisti(), ("Contact", voce): None})
		self.letta_solo_dai_professionisti(copia.name, anna)

	def test_una_persona_con_la_sua_voce_della_rubrica(self):
		# a person whose entry is linked to her: the framework finds it by the person
		anna = self.utente_dell_area("copia.persona@example.com")
		persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Anna", "last_name": "Bianchi", "email": anna}
		).insert(ignore_permissions=True)
		persona.reload()
		self.assertTrue(persona.contact)
		voce = frappe.get_doc("Contact", persona.contact)
		voce.append("links", {"link_doctype": "CRM Lead", "link_name": persona.name})
		voce.save(ignore_permissions=True)

		copia = self.copia("CRM Lead", persona.name)
		self.assertEqual(
			self.indirizzi(copia.name),
			{**self.dei_professionisti(), ("CRM Lead", persona.name): None},
		)
		self.letta_solo_dai_professionisti(copia.name, anna)

	def test_cambiata_dall_editor_degli_eventi_non_riprende_l_indirizzo(self):
		# the CRM's own event editor (EventModal.vue) writes an Event through
		# frappe.client.set_value, its rows whole and each with the address typed
		anna = self.utente_dell_area("copia.editor@example.com")
		voce = self.voce_della_rubrica(anna)
		copia = self.copia("Contact", voce)
		righe = [
			{"reference_doctype": "User", "reference_docname": utente, "email": utente}
			for utente in (self.neri, self.verdi)
		]
		righe.append({"reference_doctype": "Contact", "reference_docname": voce, "email": anna})

		frappe.set_user(self.neri)
		try:
			frappe.client.set_value("Event", copia.name, {"event_participants": righe})
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(self.indirizzi(copia.name), {**self.dei_professionisti(), ("Contact", voce): None})
		self.letta_solo_dai_professionisti(copia.name, anna)

	def test_salvata_dalla_scrivania_non_riprende_l_indirizzo(self):
		anna = self.utente_dell_area("copia.scrivania@example.com")
		voce = self.voce_della_rubrica(anna)
		copia = self.copia("Contact", voce)

		# saved again in the Desk by Dott.ssa Neri, whose copy it is, as it is: the
		# framework writes the entry's address on the row that has none
		frappe.set_user(self.neri)
		copia.reload()
		copia.save()
		self.assertEqual(self.indirizzi(copia.name), {**self.dei_professionisti(), ("Contact", voce): None})

		# her address typed on her row, her area's user added by hand
		copia.reload()
		for riga in copia.event_participants:
			if riga.reference_doctype == "Contact":
				riga.email = anna
		copia.append(
			"event_participants", {"reference_doctype": "User", "reference_docname": anna, "email": anna}
		)
		copia.save()
		frappe.set_user("Administrator")
		self.assertEqual(
			self.indirizzi(copia.name),
			{**self.dei_professionisti(), ("Contact", voce): None, ("User", anna): None},
		)
		self.letta_solo_dai_professionisti(copia.name, anna)

	def test_un_evento_del_centro_resta_del_framework(self):
		anna = "copia.centro@example.com"
		voce = self.voce_della_rubrica(anna)
		evento = self.evento_del_centro(voce)
		self.assertEqual(self.indirizzi(evento.name), {("Contact", voce): anna})

	# -- the copies saved before ----------------------------------------------

	def test_le_copie_di_prima_perdono_l_indirizzo_di_chi_viene(self):
		anna = self.utente_dell_area("copia.prima@example.com")
		voce = self.voce_della_rubrica(anna)
		copia = self.copia("Contact", voce)
		# as a copy was saved until now: her entry's address on her row, and on Dott.
		# Verdi's too, typed over his own in the Desk
		for tipo, nome in (("Contact", voce), ("User", self.verdi)):
			riga = frappe.db.get_value(
				"Event Participants",
				{"parent": copia.name, "reference_doctype": tipo, "reference_docname": nome},
				"name",
			)
			frappe.db.set_value("Event Participants", riga, "email", anna, update_modified=False)
		self.assertTrue(self.apre(anna, copia.name))
		self.assertIn(copia.name, self.elenco(anna))
		# and an Event the centre made itself, with the same entry on it
		evento = self.evento_del_centro(voce)

		patch.execute()
		self.assertEqual(self.indirizzi(copia.name), {**self.dei_professionisti(), ("Contact", voce): None})
		self.letta_solo_dai_professionisti(copia.name, anna)
		self.assertEqual(self.indirizzi(evento.name), {("Contact", voce): anna})

		# run again, it has nothing left to write
		with mock.patch.object(frappe.db, "set_value") as scrive:
			patch.execute()
		scrive.assert_not_called()

	# -- the framework's nightly digest ------------------------------------------

	def nel_riepilogo(self, evento) -> bool:
		"""Whether the framework's nightly digest of the Event's day lists it for
		its owner (`send_event_digest` reads `get_events(..., for_reminder=True)`)."""
		from frappe.desk.doctype.event.event import get_events

		giorno = evento.starts_on
		return evento.name in [
			e.name for e in get_events(giorno, giorno, user=evento.owner, for_reminder=True)
		]

	def test_la_copia_non_va_nel_riepilogo_della_notte(self):
		voce = self.voce_della_rubrica("copia.riepilogo@example.com")
		copia = self.copia("Contact", voce)
		self.assertEqual(copia.send_reminder, 0)
		self.assertFalse(self.nel_riepilogo(copia))

	def test_le_copie_di_prima_escono_dal_riepilogo(self):
		voce = self.voce_della_rubrica("copia.riepilogo.prima@example.com")
		copia = self.copia("Contact", voce)
		# as a copy was made until now: «Send reminder» on, as the framework starts it
		frappe.db.set_value("Event", copia.name, "send_reminder", 1, update_modified=False)
		evento = self.evento_del_centro(voce)
		self.assertTrue(self.nel_riepilogo(frappe.get_doc("Event", copia.name)))

		patch_del_riepilogo.execute()
		self.assertEqual(frappe.db.get_value("Event", copia.name, "send_reminder"), 0)
		self.assertFalse(self.nel_riepilogo(frappe.get_doc("Event", copia.name)))
		# an Event the centre made itself keeps the framework's digest
		self.assertEqual(frappe.db.get_value("Event", evento.name, "send_reminder"), 1)
