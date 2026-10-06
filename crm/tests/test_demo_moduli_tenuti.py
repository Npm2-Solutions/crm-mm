# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Taking the demo away keeps what the centre took over, whole: a real person's
form filled on one of the demo's forms keeps the version it was filled on and its
template; a price list the centre uses keeps its prices for the services that stay.
What is about the demo's people goes, even when nobody wrote it down as the demo's.
What the centre threw in the bin stays there."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.demo import registro
from crm.demo.modo import in_prova
from crm.demo.togli import togli
from crm.moduli import compilazioni, modelli
from crm.preventivi import api as preventivi
from crm.tests.test_demo_data import _conta

SCHEMA = {
	"sections": [
		{
			"id": "benvenuto",
			"title": "Benvenuto",
			"fields": [{"id": "come", "type": "text", "label": "Come ci hai conosciuto?"}],
		}
	]
}
PARTE = "tenuti"


class CioCheIlCentroHaTenuto(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if registro.caricati() or frappe.db.count(registro.REGISTRO):
			self.skipTest("the demo data are in: these tests take the demo away")
		self.prima = _conta()
		self.avvio = frappe.utils.now_datetime()
		self.fatti = []
		# the counters before the test's first record, kept as the demo's job keeps
		# them (crm.demo.api.crea): taking the demo away puts them back, and drops a
		# series it started - on a new site, the first form's and the first quote's
		self.serie = frappe.as_json(dict(frappe.db.sql("select name, current from `tabSeries`")))
		frappe.db.set_default(registro.SERIE, self.serie)

	def tearDown(self):
		self._via()
		frappe.db.set_default(registro.SERIE, None)

	def _via(self):
		"""What a test made and the removal kept goes the way the demo does, with what
		it left behind: a published version is never deleted otherwise."""
		frappe.set_user("Administrator")
		rimasti = [
			(doctype, nome) for doctype, nome in self.fatti if nome and frappe.db.exists(doctype, nome)
		]
		if not rimasti:
			return
		with in_prova(PARTE):
			for doctype, nome in rimasti:
				registro.annota_a_mano(doctype, nome)
		# written down now, they count as the demo's from the test's start: what they
		# left behind since then is theirs, and so are the counters it moved
		frappe.db.set_default(registro.INIZIO, str(self.avvio))
		frappe.db.set_default(registro.SERIE, self.serie)
		togli()

	def _com_era(self):
		"""Everything gone, the database as it was before the test."""
		self._via()
		dopo = _conta()
		diversi = {
			tabella: (self.prima.get(tabella), dopo.get(tabella))
			for tabella in set(self.prima) | set(dopo)
			if self.prima.get(tabella) != dopo.get(tabella)
		}
		self.assertEqual(diversi, {})

	def _persona(self, nome: str) -> str:
		persona = frappe.get_doc({"doctype": "CRM Lead", "first_name": nome, "last_name": "Prova"}).insert()
		self.fatti += [("CRM Lead", persona.name), ("Contact", persona.reload().contact)]
		return persona.name

	def _modulo(self) -> tuple[str, str]:
		"""One of the demo's forms, published."""
		modello = modelli.save_template(title="Benvenuto della prova", schema=json.dumps(SCHEMA), enabled=1)
		modelli.publish_template(modello["name"])
		versione = frappe.db.get_value(modelli.MODELLO, modello["name"], "current_version")
		self.fatti += [(modelli.MODELLO, modello["name"]), (modelli.VERSIONE, versione)]
		return modello["name"], versione

	def test_il_modulo_di_una_persona_vera_resta(self):
		with in_prova(PARTE):
			modello, versione = self._modulo()
			della_demo = self._persona("Demo")
			compilazioni.start_form(della_demo, modello)

		# the centre used the demo's form for somebody of its own before it took the
		# demo away
		suo = compilazioni.start_form(self._persona("Vera"), modello)["name"]
		self.fatti.append((compilazioni.MODULO, suo))
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — the demo's removal reads and commits on its own

		esito = togli()

		# the person's form stays, with what it was filled on
		self.assertTrue(frappe.db.exists(compilazioni.MODULO, suo))
		self.assertTrue(frappe.db.exists(modelli.VERSIONE, versione))
		self.assertEqual(frappe.db.get_value(modelli.MODELLO, modello, "current_version"), versione)
		self.assertIn(versione, esito["kept"].get(modelli.VERSIONE, []))
		# the demo's own person goes, and the form filled for them
		self.assertFalse(frappe.db.exists("CRM Lead", della_demo))
		self.assertFalse(frappe.db.exists(compilazioni.MODULO, {"lead": della_demo}))
		self._com_era()

	def test_quel_che_si_fa_poi_per_la_demo_non_tiene_niente(self):
		with in_prova(PARTE):
			modello, versione = self._modulo()
			della_demo = self._persona("Demo")

		# the next morning one of the demo's people is asked for the form - by the
		# desk, by a job - and nobody writes it down as the demo's
		suo = compilazioni.start_form(della_demo, modello)["name"]
		self.fatti.append((compilazioni.MODULO, suo))
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — the demo's removal reads and commits on its own

		esito = togli()

		# it is about the demo: it goes, and keeps nothing of the demo's
		self.assertFalse(frappe.db.exists(compilazioni.MODULO, suo))
		self.assertFalse(frappe.db.exists(modelli.VERSIONE, versione))
		self.assertFalse(frappe.db.exists(modelli.MODELLO, modello))
		self.assertEqual(esito["kept"], {})
		self._com_era()

	def test_un_listino_tenuto_tiene_i_prezzi_di_cio_che_resta(self):
		with in_prova(PARTE):
			visita, seduta = (
				frappe.get_doc(
					{
						"doctype": "CRM Service",
						"service_name": nome,
						"duration": 30,
						"staff_selection": "Any one",
						"staff": [{"user": frappe.session.user}],
						"enabled": 1,
					}
				)
				.insert()
				.name
				for nome in ("Visita della prova", "Seduta della prova")
			)
			listino = (
				frappe.get_doc(
					{"doctype": "CRM Price List", "price_list_name": "Convenzione della prova", "enabled": 1}
				)
				.insert()
				.name
			)
			prezzi = {
				servizio: frappe.get_doc(
					{
						"doctype": "CRM Service Price",
						"price_list": listino,
						"service": servizio,
						"price": prezzo,
						"enabled": 1,
					}
				)
				.insert()
				.name
				for servizio, prezzo in ((visita, 40), (seduta, 30))
			}
		self.fatti += [("CRM Service", visita), ("CRM Service", seduta), ("CRM Price List", listino)]
		self.fatti += [("CRM Service Price", prezzo) for prezzo in prezzi.values()]

		# the centre proposes one of its own the demo's visit at the demo's agreement
		preventivo = preventivi.save_quote(
			self._persona("Vera"),
			{
				"title": "Visita in convenzione",
				"price_list": listino,
				"items": [{"service": visita, "rate": 40}],
			},
		)["name"]
		self.fatti.append(("CRM Quote", preventivo))
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — the demo's removal reads and commits on its own

		esito = togli()

		# the list and the visit stay, and so does what the list asks for the visit
		self.assertTrue(frappe.db.exists("CRM Price List", listino))
		self.assertTrue(frappe.db.exists("CRM Service", visita))
		self.assertTrue(frappe.db.exists("CRM Service Price", prezzi[visita]))
		self.assertIn(prezzi[visita], esito["kept"].get("CRM Service Price", []))
		# the session nobody of the centre's used goes, and its price with it
		self.assertFalse(frappe.db.exists("CRM Service", seduta))
		self.assertFalse(frappe.db.exists("CRM Service Price", prezzi[seduta]))
		self._com_era()

	def test_il_cestino_del_centro_resta(self):
		# the centre throws its latest person in the bin: the framework gives the
		# number back, and the demo's first person takes it
		cestinata = self._persona("Cestinata")
		frappe.delete_doc("CRM Lead", cestinata)
		cestino = frappe.db.get_value(
			"Deleted Document", {"deleted_doctype": "CRM Lead", "deleted_name": cestinata}
		)
		with in_prova(PARTE):
			della_demo = self._persona("Demo")
		self.assertEqual(della_demo, cestinata)
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — the demo's removal reads and commits on its own

		arrivo = registro.cominciata()
		try:
			togli()
			# the demo's person goes, the centre's row in the bin stays
			self.assertFalse(frappe.db.exists("CRM Lead", della_demo))
			self.assertTrue(frappe.db.exists("Deleted Document", cestino))
		finally:
			# what the centre's deletion left before the demo came, given back
			for doctype in ("Deleted Document", "Comment"):
				frappe.db.delete(doctype, {"creation": ["between", (self.avvio, arrivo)]})
			frappe.db.commit()  # nosemgrep: frappe-manual-commit — the bin as it was
		self.assertFalse(frappe.db.exists("Deleted Document", cestino))
		self._com_era()
