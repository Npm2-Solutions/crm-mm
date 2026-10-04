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


def _conta() -> dict[str, int]:
	conti = {}
	for tabella in frappe.db.get_tables(cached=False):
		if tabella in VOLATILI:
			continue
		conti[tabella] = frappe.db.sql(f"select count(*) from `{tabella}`")[0][0]
	return conti


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
		for chiave in ("squadra", "agenda", "clienti", "aziende", "lavoro"):
			self.assertIn(chiave, chiavi)
		self.assertLess(chiavi.index("squadra"), chiavi.index("clienti"))


class TestDatiDiProva(IntegrationTestCase):
	"""One demo, small, made and taken away: what it holds, what it never sends,
	and the database as it was."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if registro.caricati() or frappe.db.count(registro.REGISTRO):
			from crm.demo.togli import togli

			togli()
		frappe.db.commit()
		cls.prima = _conta()
		cls.esito = api.crea(utente="Administrator", scala=0.08)
		cls.registrati = registro.registrati()

	@classmethod
	def tearDownClass(cls):
		if registro.caricati() or frappe.db.count(registro.REGISTRO):
			from crm.demo.togli import togli

			togli()
		frappe.db.commit()
		super().tearDownClass()

	def test_1_every_part_is_made(self):
		self.assertEqual(self.esito["failed"], [])
		self.assertTrue(registro.caricati())
		self.assertEqual(set(self.esito["made"]), {"squadra", "agenda", "clienti", "aziende", "lavoro"})

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
		# whoever loads the demo has things to do and somebody mentions them
		self.assertTrue(
			frappe.db.count(
				"CRM Task", {"name": ["in", sorted(r["CRM Task"])], "assigned_to": "Administrator"}
			)
		)
		# every record written down is there
		for doctype, nomi in r.items():
			# the framework writes a user's defaults again, under new names
			if doctype in ("DefaultValue",):
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
