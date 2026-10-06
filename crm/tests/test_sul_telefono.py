# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""The phone's own lists (docs/progetto-ghl/29): a person found by a number
written any way, by name or by email, a page at a time, with when they come
next; the open tasks by when they are due, one's own or everybody's; the deals
of a pipeline by stage; the companies with their deals; the register of calls,
found by a name or a number; the notes, by their title or their words."""

import datetime

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from crm.api import sul_telefono as T
from crm.permissions import livelli, utenti
from crm.scheduling.timeutils import to_system_naive
from crm.tests.test_scheduling import SchedulingCase


def _nomi(risposta) -> set[str]:
	return {riga.name for riga in risposta["rows"]}


class LePersone(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def persona(self, nome: str, **campi):
		return frappe.get_doc({"doctype": "CRM Lead", "first_name": nome, **campi}).insert()

	def test_a_number_is_found_however_it_is_written(self):
		persona = self.persona("Telefonata", mobile_no="+39 340 987 6543")
		for scritto in ("3409876543", "+393409876543", "340 987 65 43", "340-987-6543", "9876543"):
			self.assertIn(persona.name, _nomi(T.get_people(scritto)), scritto)

	def test_two_digits_find_nobody(self):
		self.persona("Due cifre", mobile_no="+39 340 987 6543")
		self.assertEqual(T.get_people("34")["rows"], [])

	def test_a_name_or_an_email(self):
		persona = self.persona("Zefferina", last_name="Quaglia", email="zefferina.q@example.com")
		self.assertIn(persona.name, _nomi(T.get_people("zefferina")))
		self.assertIn(persona.name, _nomi(T.get_people("Quaglia")))
		self.assertIn(persona.name, _nomi(T.get_people("zefferina.q@")))
		self.assertNotIn(persona.name, _nomi(T.get_people("Nessunodicosi")))

	def test_one_step_or_everybody(self):
		lead = self.persona("Passolino")
		cliente = self.persona("Passolino", last_name="Cliente")
		frappe.db.set_value("CRM Lead", cliente.name, "relationship", "Client")
		self.assertEqual(_nomi(T.get_people("Passolino", relationship="Client")), {cliente.name})
		self.assertEqual(_nomi(T.get_people("Passolino", relationship="Contact")), {lead.name})
		self.assertEqual(_nomi(T.get_people("Passolino")), {lead.name, cliente.name})
		# a step the field does not hold narrows nothing
		self.assertEqual(_nomi(T.get_people("Passolino", relationship="Nobody")), {lead.name, cliente.name})

	def test_marketing_finds_people_by_name_only(self):
		# they read email and phone masked: a number typed would tell whose it is
		persona = self.persona("Mascherina", mobile_no="+39 340 555 1212", email="mascherina.m@example.com")
		utente = "telefono.marketing@example.com"
		if not frappe.db.exists("User", utente):
			frappe.get_doc(
				{"doctype": "User", "email": utente, "first_name": "Marketing", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		utenti.assegna_livelli(utente, ["marketing"])
		livelli.dimentica_cache()
		frappe.set_user(utente)
		try:
			self.assertEqual(T.get_people("3405551212")["rows"], [])
			self.assertNotIn(persona.name, _nomi(T.get_people("mascherina.m@")))
			self.assertIn(persona.name, _nomi(T.get_people("Mascherina")))
		finally:
			frappe.set_user("Administrator")
			livelli.dimentica_cache()

	def test_a_page_at_a_time_saying_when_there_are_more(self):
		for i in range(T.PER_PAGINA + 2):
			self.persona(f"Pagina{i}", last_name="Paginatissima")
		prima = T.get_people("Paginatissima")
		self.assertEqual(len(prima["rows"]), T.PER_PAGINA)
		self.assertTrue(prima["more"])
		seconda = T.get_people("Paginatissima", start=T.PER_PAGINA)
		self.assertEqual(len(seconda["rows"]), 2)
		self.assertFalse(seconda["more"])
		self.assertFalse(_nomi(prima) & _nomi(seconda))


class IlProssimoAppuntamento(SchedulingCase):
	def test_the_next_one_that_still_holds(self):
		professionista = self.make_user("telefono.prof@example.com")
		servizio = self.make_service("Visita dal telefono", [professionista], duration=30)
		persona = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Prossimissima"}).insert()
		chi = [{"party_type": "CRM Lead", "party": persona.name, "participant_name": "Prossimissima"}]
		self.make_appointment(
			servizio.name, self.tomorrow(9), [professionista], participants=chi, status="Cancelled"
		)
		self.make_appointment(servizio.name, self.tomorrow(11), [professionista], participants=chi)

		riga = next(r for r in T.get_people("Prossimissima")["rows"] if r.name == persona.name)
		# the agenda keeps the system's time, as the phone shows it
		self.assertEqual(frappe.utils.get_datetime(riga.next_appointment), to_system_naive(self.tomorrow(11)))


class LeCose(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def cosa(self, titolo: str, **campi):
		campi.setdefault("assigned_to", "Administrator")
		campi.setdefault("status", "Todo")
		return frappe.get_doc({"doctype": "CRM Task", "title": titolo, **campi}).insert()

	def test_the_open_ones_by_when_they_are_due(self):
		adesso = now_datetime()
		senza = self.cosa("Senza giorno")
		domani = self.cosa("Domani", due_date=add_days(adesso, 1))
		ieri = self.cosa("Ieri", due_date=add_days(adesso, -1))
		fatta = self.cosa("Fatta", status="Done", due_date=add_days(adesso, -2))
		annullata = self.cosa("Annullata", status="Canceled")

		nostre = {senza.name, domani.name, ieri.name, fatta.name, annullata.name}
		righe = [r.name for r in T.get_tasks(1)["rows"] if r.name in nostre]
		self.assertEqual(righe, [ieri.name, domani.name, senza.name])

	def test_mine_or_everybodys(self):
		altro = "telefono.altro@example.com"
		if not frappe.db.exists("User", altro):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": altro,
					"first_name": "Altro",
					"send_welcome_email": 0,
					"roles": [{"role": "Sales User"}],
				}
			).insert(ignore_permissions=True)
		mia = self.cosa("Mia")
		sua = self.cosa("Sua", assigned_to=altro)

		mie = _nomi(T.get_tasks(1))
		self.assertIn(mia.name, mie)
		self.assertNotIn(sua.name, mie)
		tutte = _nomi(T.get_tasks(0))
		self.assertTrue({mia.name, sua.name} <= tutte)

	def test_what_it_is_about_by_name(self):
		persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Riferita", "last_name": "Bene"}
		).insert()
		cosa = self.cosa("Richiamare", reference_doctype="CRM Lead", reference_docname=persona.name)
		riga = next(r for r in T.get_tasks(1)["rows"] if r.name == cosa.name)
		self.assertEqual(riga.reference_title, persona.lead_name)


class LeTrattative(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def trattativa(self, stato: str):
		organizzazione = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": f"Telefono {frappe.generate_hash(length=6)}"}
		).insert(ignore_permissions=True)
		persona = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Trattata"}).insert()
		return frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"lead": persona.name,
				"organization": organizzazione.name,
				"status": stato,
			}
		).insert()

	def _conteggi(self, pipeline):
		return {r["status"]: r["deals"] for r in T.get_deal_stages(pipeline)}

	def test_each_stage_with_how_many_deals_it_holds(self):
		primo = self.trattativa("Qualification")
		pipeline = primo.pipeline
		prima = self._conteggi(pipeline)
		self.trattativa("Qualification")
		self.trattativa("Negotiation")
		dopo = self._conteggi(pipeline)
		self.assertEqual(dopo.get("Qualification", 0) - prima.get("Qualification", 0), 1)
		self.assertEqual(dopo.get("Negotiation", 0) - prima.get("Negotiation", 0), 1)

	def test_the_deals_of_a_stage_the_latest_moved_first(self):
		vecchia = self.trattativa("Negotiation")
		nuova = self.trattativa("Negotiation")
		frappe.db.set_value(
			"CRM Deal",
			vecchia.name,
			"modified",
			now_datetime() - datetime.timedelta(minutes=1),
			update_modified=False,
		)
		righe = [
			r.name
			for r in T.get_deals("Negotiation", vecchia.pipeline)["rows"]
			if r.name in {vecchia.name, nuova.name}
		]
		self.assertEqual(righe, [nuova.name, vecchia.name])
		self.assertNotIn(vecchia.name, _nomi(T.get_deals("Qualification", vecchia.pipeline)))


class IContatti(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_by_name_company_or_a_number_however_written(self):
		contatto = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Contattissimo",
				"company_name": "Ditta Contattata",
				"phone_nos": [{"phone": "+39 345 222 3344", "is_primary_mobile_no": 1}],
			}
		).insert(ignore_permissions=True)
		for cercato in ("Contattissimo", "Ditta Contattata", "3452223344", "345 222 33 44"):
			self.assertIn(contatto.name, _nomi(T.get_contacts(cercato)), cercato)
		self.assertNotIn(contatto.name, _nomi(T.get_contacts("Nessunodicosi")))
		self.assertEqual(T.get_contacts("34")["rows"], [])


class LeAziende(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_found_by_name_with_their_deals(self):
		nome = f"Aziendina {frappe.generate_hash(length=6)}"
		azienda = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": nome, "website": "https://aziendina.example"}
		).insert(ignore_permissions=True)
		persona = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Aziendale"}).insert()
		for _ in range(2):
			frappe.get_doc(
				{"doctype": "CRM Deal", "lead": persona.name, "organization": azienda.name}
			).insert()

		riga = next(r for r in T.get_organizations(nome)["rows"] if r.name == azienda.name)
		self.assertEqual(riga.deals, 2)
		self.assertIn(azienda.name, _nomi(T.get_organizations("aziendina.example")))
		self.assertNotIn(azienda.name, _nomi(T.get_organizations("Nessunadicosi")))


class LeChiamate(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def chiamata(self, persona=None, **campi):
		campi.setdefault("type", "Incoming")
		campi.setdefault("status", "Completed")
		if persona:
			campi.update(reference_doctype="CRM Lead", reference_docname=persona.name)
		return frappe.get_doc(
			{"doctype": "CRM Call Log", "id": frappe.generate_hash(length=12), **campi}
		).insert(ignore_permissions=True)

	def test_a_number_however_it_is_written_or_a_name(self):
		persona = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Chiamatissima"}).insert()
		entrata = self.chiamata(persona, **{"from": "+39 333 765 4321", "to": "+39 02 1234567"})
		uscita = self.chiamata(type="Outgoing", **{"from": "+39 02 1234567", "to": "+393337654321"})
		for scritto in ("3337654321", "+39 333 765 43 21", "7654321"):
			self.assertTrue({entrata.name, uscita.name} <= _nomi(T.get_calls(scritto)), scritto)
		per_nome = _nomi(T.get_calls("Chiamatissima"))
		self.assertIn(entrata.name, per_nome)
		self.assertNotIn(uscita.name, per_nome)
		self.assertEqual(T.get_calls("33")["rows"], [])

	def test_with_whom_and_whether_nobody_took_it(self):
		persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Persa", "last_name": "Chiamata"}
		).insert()
		persa = self.chiamata(
			persona, status="No Answer", **{"from": "+39 347 000 1111", "to": "+39 02 1234567"}
		)
		uscita = self.chiamata(
			persona,
			type="Outgoing",
			status="No Answer",
			**{"from": "+39 02 1234567", "to": "+39 347 000 1111"},
		)
		righe = {r["name"]: r for r in T.get_calls("Persa Chiamata")["rows"]}
		self.assertTrue(righe[persa.name]["missed"])
		self.assertEqual(righe[persa.name]["number"], "+39 347 000 1111")
		self.assertEqual(righe[persa.name]["person"], persona.lead_name)
		# a call of ours nobody answered is not one we missed
		self.assertFalse(righe[uscita.name]["missed"])
		self.assertEqual(righe[uscita.name]["number"], "+39 347 000 1111")


class LeNote(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def nota(self, titolo: str, contenuto: str = "", **campi):
		return frappe.get_doc(
			{"doctype": "FCRM Note", "title": titolo, "content": contenuto, **campi}
		).insert()

	def test_found_by_title_or_words_the_latest_first(self):
		parola = frappe.generate_hash(length=8)
		prima = self.nota(f"Richiamo {parola}")
		dopo = self.nota("Promemoria", f"<p>Chiedere del <b>{parola}</b></p>")
		frappe.db.set_value(
			"FCRM Note", prima.name, "modified", add_days(now_datetime(), -1), update_modified=False
		)

		righe = [r.name for r in T.get_notes(parola)["rows"]]
		self.assertEqual(righe, [dopo.name, prima.name])
		self.assertNotIn(dopo.name, _nomi(T.get_notes("Nessunadicosi")))

	def test_their_first_words_in_plain_text_and_whom_they_are_about(self):
		persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Annotata", "last_name": "Bene"}
		).insert()
		lunga = "parola " * 60
		nota = self.nota(
			"Visita",
			f"<p>Prima <i>riga</i></p><p>{lunga}</p>",
			reference_doctype="CRM Lead",
			reference_docname=persona.name,
		)
		riga = next(r for r in T.get_notes("Visita")["rows"] if r.name == nota.name)
		self.assertTrue(riga.content.startswith("Prima riga parola"))
		self.assertLessEqual(len(riga.content), T.INIZIO_DELLA_NOTA)
		self.assertNotIn("<", riga.content)
		self.assertEqual(riga.reference_title, persona.lead_name)

	def test_without_reading_notes_nothing(self):
		utente = "telefono.senzanote@example.com"
		if not frappe.db.exists("User", utente):
			frappe.get_doc(
				{"doctype": "User", "email": utente, "first_name": "Senza", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		frappe.set_user(utente)
		with self.assertRaises(frappe.PermissionError):
			T.get_notes()
