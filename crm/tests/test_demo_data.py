# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

"""The demo data (doc 53): made through the product's own rules, nobody written to
while they are in, and taken away without leaving anything behind - every table
counted before and after."""

import frappe
from frappe.tests import IntegrationTestCase

from crm.demo import api, guardie, registro
from crm.demo.registro import Parte

#: What other things write while the demo comes and goes: logs, the search the
#: scheduler syncs, sessions.
VOLATILI = {
	"tabError Log",
	"tabScheduled Job Log",
	"__global_search",
	"tabAccess Log",
	"tabActivity Log",
	"tabSessions",
	"tabRoute History",
}


#: The base's parts, in the order they are registered.
BASE = ("squadra", "agenda", "clienti", "aziende", "lavoro", "abbonamenti", "attese", "conversazioni")
#: The parts the CRM's own modules add, whatever the plan.
DEI_MODULI = ("moduli", "documenti")
#: Where the centre says which pipelines are the new clients' and the quotes'.
IMPOSTAZIONI_DELLE_PIPELINE = ("CRM Client Settings", "CRM Quote Settings")


def _conta() -> dict[str, int]:
	conti = {}
	for tabella in frappe.db.get_tables(cached=False):
		if tabella in VOLATILI:
			continue
		conti[tabella] = frappe.db.sql(f"select count(*) from `{tabella}`")[0][0]
	return conti


def _serie() -> dict[str, int]:
	return {nome: corrente or 0 for nome, corrente in frappe.db.sql("select name, current from `tabSeries`")}


class TestLePartiInOrdine(IntegrationTestCase):
	def test_each_part_after_the_ones_it_needs(self):
		niente = lambda ctx: None  # noqa: E731
		parti = [
			Parte("c", "C", niente, dopo=("b",)),
			Parte("a", "A", niente),
			Parte("b", "B", niente, dopo=("a",)),
			# needs a part that is not there: made anyway, without it
			Parte("d", "D", niente, dopo=("assente",)),
		]
		self.assertEqual([p.chiave for p in registro.in_ordine(parti)], ["a", "b", "c", "d"])

	def test_parts_that_need_each_other_are_refused(self):
		niente = lambda ctx: None  # noqa: E731
		with self.assertRaises(ValueError):
			registro.in_ordine([Parte("a", "A", niente, dopo=("b",)), Parte("b", "B", niente, dopo=("a",))])

	def test_the_base_parts_are_registered(self):
		chiavi = [parte.chiave for parte in registro.tutte_le_parti()]
		for chiave in BASE:
			self.assertIn(chiave, chiavi)
		self.assertLess(chiavi.index("squadra"), chiavi.index("clienti"))
		self.assertLess(chiavi.index("clienti"), chiavi.index("abbonamenti"))
		self.assertLess(chiavi.index("attese"), chiavi.index("conversazioni"))
		for chiave in DEI_MODULI:
			self.assertIn(chiave, chiavi)
		# the forms are signed by people who came
		self.assertIn("clienti", registro.tutte_le_parti()[chiavi.index("moduli")].dopo)


class TestDatiDiProva(IntegrationTestCase):
	"""One demo, small, made and taken away: what it holds, what it never sends,
	and the database as it was."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if registro.caricati() or frappe.db.count(registro.REGISTRO):
			from crm.demo.togli import togli

			togli()
		# the product's own setup the demo makes where the centre has none stays when it
		# goes: the pipelines of new clients and of quotes, made first so they count as
		# the site's - and given back as they were when the tests are done
		from crm.clienti import pipeline as nuovi_clienti
		from crm.preventivi import pipeline as preventivi

		cls.pipeline_di_prima = set(frappe.get_all("CRM Pipeline", pluck="name"))
		cls.impostazioni_di_prima = {
			doctype: frappe.db.sql("select field, value from `tabSingles` where doctype = %s", doctype)
			for doctype in IMPOSTAZIONI_DELLE_PIPELINE
		}
		nuovi_clienti.crea()
		preventivi.crea()
		frappe.db.commit()
		cls.prima = _conta()
		cls.serie_di_prima = _serie()
		cls.esito = api.crea(utente="Administrator", scala=0.08)
		cls.registrati = registro.registrati()

	@classmethod
	def tearDownClass(cls):
		if registro.caricati() or frappe.db.count(registro.REGISTRO):
			from crm.demo.togli import togli

			togli()
		# the pipelines these tests made, gone; the settings as they were
		for pipeline in set(frappe.get_all("CRM Pipeline", pluck="name")) - cls.pipeline_di_prima:
			frappe.db.delete("CRM Deal Status", {"pipeline": pipeline})
			frappe.db.delete("CRM Pipeline", {"name": pipeline})
		for doctype, righe in cls.impostazioni_di_prima.items():
			frappe.db.delete("Singles", {"doctype": doctype})
			for campo, valore in righe:
				frappe.db.sql(
					"insert into `tabSingles` (doctype, field, value) values (%s, %s, %s)",
					(doctype, campo, valore),
				)
			frappe.clear_document_cache(doctype, doctype)
		frappe.db.commit()
		super().tearDownClass()

	def test_1_every_part_is_made(self):
		self.assertEqual(self.esito["failed"], [])
		self.assertTrue(registro.caricati())
		# every part of the modules that are on, the base's and the CRM's own first
		accese = {parte.chiave for parte in registro.tutte_le_parti() if registro.accesa(parte)}
		self.assertEqual(set(self.esito["made"]), accese)
		self.assertLessEqual(set(BASE) | set(DEI_MODULI), accese)

	def test_2_a_centre_full_of_life(self):
		r = self.registrati
		self.assertEqual(len(r.get("User", ())), 6)
		self.assertEqual(len(r.get("CRM Service", ())), 10)
		self.assertGreater(len(r.get("CRM Lead", ())), 10)
		self.assertGreater(len(r.get("CRM Appointment", ())), 20)
		self.assertGreater(len(r.get("CRM Deal", ())), 5)
		self.assertTrue(r.get("CRM Task"))
		self.assertTrue(r.get("FCRM Note"))
		self.assertTrue(r.get("CRM Call Log"))
		# the CRM's own rules ran: people came, became clients, their deals were won
		persone = sorted(r["CRM Lead"])
		self.assertTrue(frappe.db.count("CRM Lead", {"name": ["in", persone], "client_since": ["is", "set"]}))
		self.assertTrue(frappe.db.count("CRM Lead", {"name": ["in", persone], "last_visit": ["is", "set"]}))
		# the course agreed at the first visit, the subscriptions on sale, who waits,
		# what was written
		self.assertTrue(r.get("CRM Session Cycle") or r.get("CRM Quote"))
		self.assertEqual(len(r.get("CRM Subscription Type", ())), 3)
		self.assertTrue(r.get("CRM Waiting List Entry"))
		self.assertTrue(r.get("Communication"))
		if r.get("CRM Quote"):
			# a quote handed over has its PDF, and moved its deal
			proposti = frappe.get_all(
				"CRM Quote",
				filters={"name": ["in", sorted(r["CRM Quote"])], "status": ["!=", "Draft"]},
				fields=["quote_pdf", "deal"],
			)
			self.assertTrue(all(riga.quote_pdf for riga in proposti))
		# the forms published, signed with their PDF and the consents they gave, sent
		# to who comes in the next days, the sheets written in today's sessions
		self.assertGreaterEqual(len(r.get("CRM Form Template", ())), 3)
		firmati = frappe.get_all(
			"CRM Form",
			filters={"name": ["in", sorted(r.get("CRM Form", ()))], "docstatus": 1},
			fields=["name", "lead", "pdf_file"],
		)
		if firmati:
			self.assertTrue(all(riga.pdf_file for riga in firmati))
			self.assertTrue(
				frappe.db.count("CRM Consent", {"lead": ["in", sorted({riga.lead for riga in firmati})]})
			)
			# every signature has its evidence, chained
			from crm.moduli import traccia

			for riga in firmati[:3]:
				self.assertTrue(traccia.verifica_catena("CRM Form", riga.name)["integra"])
		# every subscription's contract filed and handed over; a few online
		documenti = frappe.get_all(
			"CRM Document",
			filters={"name": ["in", sorted(r.get("CRM Document", ()))]},
			fields=["name", "document_type", "file", "file_hash"],
		)
		self.assertTrue(documenti)
		self.assertTrue(all(riga.file and riga.file_hash for riga in documenti))
		if r.get("CRM Subscription"):
			self.assertIn("Contract", {riga.document_type for riga in documenti})
			self.assertTrue(
				frappe.db.count(
					"CRM Document Delivery", {"document": ["in", [riga.name for riga in documenti]]}
				)
			)
		# whoever loads the demo has things to do and somebody mentions them
		self.assertTrue(
			frappe.db.count(
				"CRM Task", {"name": ["in", sorted(r["CRM Task"])], "assigned_to": "Administrator"}
			)
		)
		# every record written down is there
		for doctype, nomi in r.items():
			# the framework writes a user's defaults again, under new names; a person's
			# messages add up in one notification, which takes the place of the one before
			if doctype in ("DefaultValue", "CRM Notification"):
				continue
			trovati = frappe.db.count(doctype, {"name": ["in", sorted(nomi)]})
			self.assertEqual(trovati, len(nomi), doctype)

	def test_3_the_team_has_its_levels_and_no_password(self):
		for utente in self.registrati["User"]:
			self.assertTrue(frappe.get_all("Has Role", filters={"parent": utente}, pluck="role"))
			self.assertFalse(
				frappe.db.sql("select 1 from `__Auth` where doctype='User' and name=%s", utente),
				"a demo colleague cannot sign in",
			)

	def test_4_nobody_receives_anything(self):
		persona = sorted(self.registrati["CRM Lead"])[0]
		email, cellulare = frappe.db.get_value("CRM Lead", persona, ["email", "mobile_no"])
		# a number of the demo's is known, one of somebody else's is not
		self.assertTrue(guardie.numero_di_prova(cellulare))
		self.assertFalse(guardie.numero_di_prova("+39 02 1234 5678"))
		# a call does not leave
		from crm.telephony.uscita import perche_no

		self.assertTrue(perche_no(cellulare))
		# an email leaves the queue unsent
		if email:
			frappe.sendmail(recipients=[email], subject="Promemoria", message="Ciao", now=False)
			coda = frappe.get_all(
				"Email Queue",
				filters={"status": "Error"},
				fields=["name", "error"],
				order_by="creation desc",
				limit=1,
			)
			self.assertTrue(coda and "demo" in (coda[0].error or ""))
		# a notification about a demo person stays in the panel
		from crm.notifiche import regole as R
		from crm.notifiche.avvisi import avvisa

		nome = avvisa(
			"Administrator",
			"Mention",
			R.MENZIONE,
			["Paolo", "Mario"],
			da=None,
			riguarda=("CRM Lead", persona),
		)
		if nome:
			self.assertFalse(frappe.db.get_value("CRM Notification", nome, "email_due"))

	def test_4b_a_real_message_from_a_demo_number_is_not_the_demos(self):
		from crm.integrations.api import find_contact_by_phone_number, get_contact_lead_or_deal_from_number

		persona = sorted(self.registrati["CRM Lead"])[0]
		cellulare = frappe.db.get_value("CRM Lead", persona, "mobile_no")
		if not cellulare:
			return
		# the screens still name it...
		self.assertTrue(guardie.contatto_della_demo(find_contact_by_phone_number(cellulare)))
		# ...but a message that comes in from it is not filed on the demo's person
		self.assertEqual(get_contact_lead_or_deal_from_number(cellulare), (None, None))
		self.assertIsNone(guardie.persona_vera(cellulare))

	def test_4c_the_demos_forms_are_asked_of_the_demos_people_only(self):
		from crm.moduli import dovuti

		modelli = self.registrati.get("CRM Form Template", set())
		if not modelli:
			return
		# somebody real, booked while the demo is in: not one of the demo's forms
		vera = "una-persona-vera-del-centro"
		chiesti = dovuti.dovuti([vera], {vera: None}, clinici=True)[vera]
		self.assertFalse({voce["template"] for voce in chiesti} & modelli)
		# the demo's people still owe them, until they sign
		persone = sorted(self.registrati["CRM Lead"])
		chiesti = dovuti.dovuti(persone, dict.fromkeys(persone), clinici=True)
		self.assertTrue({voce["template"] for voci in chiesti.values() for voce in voci} & modelli)

	def test_4d_what_the_demo_made_takes_no_first_step(self):
		from crm import primi_passi

		# the demo's services, people and colleagues are not the centre's: its first
		# steps still show what the centre itself has to set up
		for doctype in ("CRM Service", "CRM Lead", "CRM Appointment"):
			nomi = sorted(self.registrati[doctype])
			self.assertFalse(primi_passi.c_e(doctype, {"name": ["in", nomi]}), doctype)

	def test_5_visitors_of_the_booking_page_do_not_see_the_demo(self):
		from crm.api import service_booking

		servizi = self.registrati["CRM Service"]
		frappe.set_user("Guest")
		try:
			try:
				catalogo = service_booking.get_catalog()
			except frappe.PermissionError:
				return  # online booking switched off on this site
			nomi = {card.get("name") for card in catalogo.get("services", [])}
			self.assertFalse(nomi & servizi)
		finally:
			frappe.set_user("Administrator")

	def test_6_taking_them_away_leaves_the_database_as_it_was(self):
		from crm.demo.togli import togli

		indirizzi = frappe.get_all(
			"CRM Lead", filters={"name": ["in", sorted(self.registrati["CRM Lead"])]}, pluck="email"
		)
		esito = togli()
		self.assertTrue(esito["removed"])
		self.assertFalse(registro.caricati())
		self.assertEqual(frappe.db.count(registro.REGISTRO), 0)

		dopo = _conta()
		diversi = {
			tabella: (self.prima.get(tabella), dopo.get(tabella))
			for tabella in set(self.prima) | set(dopo)
			if self.prima.get(tabella) != dopo.get(tabella)
		}
		self.assertEqual(diversi, {})
		# the numbers go on from where they were: the series with no name too, which every
		# "format:APPT-{#####}" doctype shares
		self.assertEqual(_serie(), self.serie_di_prima)

		# nothing of theirs left to read, anywhere a name or an address could stay
		for indirizzo in [indirizzo for indirizzo in indirizzi if indirizzo]:
			self.assertFalse(frappe.db.exists("Contact Email", {"email_id": indirizzo}))
			self.assertFalse(frappe.db.exists("Email Queue Recipient", {"recipient": indirizzo}))
		for utente in self.registrati["User"]:
			self.assertFalse(frappe.db.exists("User", utente))
			self.assertFalse(frappe.db.sql("select 1 from tabDefaultValue where parent=%s", utente))
		self.assertFalse(
			frappe.db.sql(
				"select 1 from `tabDeleted Document` where deleted_doctype in ('CRM Lead', 'CRM Appointment', 'CRM Deal') and deleted_name in %(nomi)s",
				{"nomi": sorted(self.registrati["CRM Lead"] | self.registrati["CRM Appointment"])},
			)
		)
