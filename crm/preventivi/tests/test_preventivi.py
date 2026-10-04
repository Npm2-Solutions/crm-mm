# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Quotes on a site without the clinic: a beauty centre's treatments.

The therapist writes Anna's quote - a facial, then a laser treatment with a
discount - from the price list; the desk does not read the draft, and sales never
reads it. Proposed, it is frozen, its PDF is made and Anna's deal in the quotes
pipeline says "quote delivered"; it is no health data, so nothing goes in the
access log. The desk records it accepted, the deal is won; an appointment of the
facial takes its row at the price agreed, Anna came, it is done; every row done
or cancelled, the quote is completed. Anna reads it in her area. Declined, the deal
is lost with the reason, and a new version starts from it. The manager chooses the
pipeline and how long a quote holds.
"""

import json
import unittest

import frappe
from frappe.utils import add_days, getdate

from crm.area.tests.test_area import DESK, MANAGER, OPERATORE, SALES, AreaCase
from crm.permissions import utenti
from crm.preventivi import api as preventivi
from crm.preventivi import area, documento, pipeline
from crm.preventivi import regole as R


class PreventiviCase(AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		pipeline.crea()
		self.viso = self.make_service("Pulizia viso di prova", [OPERATORE], default_price=60, currency="EUR")
		self.laser = self.make_service("Laser di prova", [OPERATORE], default_price=200, currency="EUR")

	def scrive(self, user=OPERATORE, **altro):
		self.come(user)
		return preventivi.save_quote(
			self.anna.name,
			json.dumps(
				{
					"title": "Trattamenti di ottobre",
					"items": [
						{"service": self.viso.name, "phase": 1, "rate": 60},
						{"service": self.laser.name, "phase": 2, "rate": 200, "discount": 10},
					],
					**altro,
				}
			),
		)

	def proponi(self, nome):
		self.come(OPERATORE)
		return preventivi.propose_quote(nome)

	def tipo_del_deal(self, deal):
		return frappe.db.get_value("CRM Deal Status", frappe.db.get_value("CRM Deal", deal, "status"), "type")


class IlPreventivo(PreventiviCase):
	def test_si_scrive_si_propone_e_la_segreteria_lo_accetta(self):
		fatto = self.scrive()
		self.assertEqual((fatto["status"], fatto["clinical"]), (R.BOZZA, 0))
		self.assertEqual(fatto["totals"], {"gross": 260, "discount": 20, "net": 240, "done": 0, "left": 240})
		self.assertEqual(fatto["items"][0]["description"], "Pulizia viso di prova")
		# without the clinic no tooth is offered, nor taken
		self.assertFalse(fatto["offers"].get("teeth"))
		# a draft is its author's
		for user in (DESK, SALES):
			self.come(user)
			self.assertEqual(preventivi.get_quotes(self.anna.name)["quotes"], [], user)
			with self.assertRaises(frappe.PermissionError):
				preventivi.get_quote(fatto["name"])
		proposto = self.proponi(fatto["name"])
		self.assertEqual(proposto["status"], R.PROPOSTO)
		self.assertTrue(proposto["quote_pdf"])
		self.assertEqual(getdate(proposto["valid_until"]), add_days(getdate(), R.GIORNI_VALIDITA))
		self.assertIn("Laser di prova", documento.html(frappe.get_doc(preventivi.DOCTYPE, fatto["name"])))
		deal = frappe.get_doc("CRM Deal", proposto["deal"])
		self.assertEqual(deal.pipeline, pipeline.quale())
		self.assertEqual(frappe.db.get_value("CRM Deal Status", deal.status, "position"), pipeline.CONSEGNATO)
		self.assertEqual(deal.expected_deal_value, 240)
		# proposed, it is not rewritten, nor thrown away
		doc = frappe.get_doc(preventivi.DOCTYPE, fatto["name"])
		doc.title = "Riscritto"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		# sales reads it and does not decide; the desk records it accepted
		self.come(SALES)
		self.assertFalse(preventivi.get_quote(fatto["name"])["can_decide"])
		with self.assertRaises(frappe.PermissionError):
			preventivi.accept_quote(fatto["name"])
		self.come(DESK)
		self.assertEqual(
			[q["name"] for q in preventivi.get_quotes(self.anna.name)["quotes"]], [fatto["name"]]
		)
		accettato = preventivi.accept_quote(fatto["name"], note="Firmato al banco")
		self.assertEqual(
			(accettato["status"], accettato["acceptance_note"]), (R.ACCETTATO, "Firmato al banco")
		)
		self.assertEqual(self.tipo_del_deal(accettato["deal"]), "Won")
		# no health data: nothing in the access log
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("View Log", {"reference_name": fatto["name"]}))
		# the lists follow the same rule
		self.come(SALES)
		self.assertEqual(frappe.get_list(preventivi.DOCTYPE, pluck="name"), [fatto["name"]])

	def test_rifiutato_il_deal_e_perso_e_si_riparte_da_una_nuova_versione(self):
		fatto = self.scrive()
		self.proponi(fatto["name"])
		self.come(DESK)
		rifiutato = preventivi.decline_quote(fatto["name"], reason="Pricing", note="Ci pensa")
		self.assertEqual(
			(rifiutato["status"], rifiutato["decline_reason"]), (R.RIFIUTATO, "Pricing, Ci pensa")
		)
		deal = frappe.get_doc("CRM Deal", rifiutato["deal"])
		self.assertEqual((self.tipo_del_deal(deal.name), deal.lost_reason), ("Lost", "Pricing"))
		self.come(OPERATORE)
		nuova = preventivi.copy_quote(fatto["name"])
		self.assertEqual(
			(nuova["status"], nuova["replaces"], len(nuova["items"])), (R.BOZZA, fatto["name"], 2)
		)
		# proposed and taken back to change it: a draft again, without the old PDF
		self.proponi(nuova["name"])
		self.come(OPERATORE)
		ritirata = preventivi.withdraw_quote(nuova["name"])
		self.assertEqual((ritirata["status"], ritirata["quote_pdf"]), (R.BOZZA, None))
		preventivi.delete_quote_draft(nuova["name"])
		self.assertFalse(frappe.db.exists(preventivi.DOCTYPE, nuova["name"]))

	def test_senza_un_dente_senza_la_clinica(self):
		self.come(OPERATORE)
		with self.assertRaises(frappe.ValidationError):
			preventivi.save_quote(
				self.anna.name,
				json.dumps({"title": "Col dente", "items": [{"service": self.viso.name, "tooth": "36"}]}),
			)

	def test_una_riga_lasciata_vuota_non_ferma_la_bozza(self):
		# the editor adds rows one at a time: one left behind with nothing in it
		self.come(OPERATORE)
		vuota = {"service": None, "description": "", "qty": 1, "phase": 1, "rate": 0, "discount": 0}
		bozza = preventivi.save_quote(
			self.anna.name,
			json.dumps(
				{"title": "Una riga in più", "items": [{"service": self.viso.name, "rate": 60}, vuota]}
			),
		)
		self.assertEqual([voce["service"] for voce in bozza["items"]], [self.viso.name])

	def test_chi_non_scrive_preventivi_non_ne_scrive(self):
		self.come(SALES)
		self.assertTrue(preventivi.get_quotes(self.anna.name)["can_write"])
		frappe.set_user("Administrator")
		utenti.assegna_livelli(SALES, ["marketing"])
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			preventivi.save_quote(self.anna.name, json.dumps({"title": "Suo", "items": []}))


class LeSedute(PreventiviCase):
	def appuntamento(self, servizio, quando):
		frappe.set_user("Administrator")
		return self.make_appointment(
			servizio.name,
			quando,
			[OPERATORE],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": self.anna.name,
					"participant_name": "Anna Area",
					"status": "Booked",
				}
			],
		)

	def esito(self, appuntamento, stato):
		frappe.set_user("Administrator")
		doc = frappe.get_doc("CRM Appointment", appuntamento.name)
		doc.participants[0].status = stato
		doc.save()

	def test_gli_appuntamenti_fanno_il_preventivo(self):
		fatto = self.scrive()
		self.proponi(fatto["name"])
		self.come(DESK)
		preventivi.accept_quote(fatto["name"])
		# the laser at the price agreed, less the discount
		laser = self.appuntamento(self.laser, self.tomorrow(11))
		self.assertEqual(laser.total_amount, 180)
		viso = self.appuntamento(self.viso, self.tomorrow(9))
		self.come(OPERATORE)
		self.assertEqual(
			[(v["status"], v["appointment"]) for v in preventivi.get_quote(fatto["name"])["items"]],
			[(R.PRENOTATA, viso.name), (R.PRENOTATA, laser.name)],
		)
		# in her area Anna reads it, the rows booked
		self.invita()
		self.entra()
		[nell_area] = area.area_quotes(self.anna.name)["quotes"]
		self.assertEqual(nell_area["title"], "Trattamenti di ottobre")
		self.assertTrue(all(v["when"] for v in nell_area["items"]))
		# Anna came to both: the quote is completed
		self.esito(viso, "Attended")
		self.esito(laser, "Attended")
		self.come(OPERATORE)
		finito = preventivi.get_quote(fatto["name"])
		self.assertEqual(finito["status"], R.COMPLETATO)
		self.assertEqual(finito["totals"]["done"], 240)


class LeImpostazioni(PreventiviCase):
	def test_il_manager_sceglie_la_pipeline_e_la_validita(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			pipeline.get_settings()
		self.come(MANAGER)
		self.assertEqual(pipeline.get_settings()["quotes_pipeline"], pipeline.quale())
		pipeline.save_settings(quotes_pipeline=pipeline.quale(), valid_days=30)
		fatto = self.scrive()
		proposto = self.proponi(fatto["name"])
		self.assertEqual(getdate(proposto["valid_until"]), add_days(getdate(), 30))
		# without a pipeline, a quote moves no deal
		self.come(MANAGER)
		pipeline.save_settings(quotes_pipeline=None, valid_days=None)
		altro = self.scrive(title="Senza pipeline")
		self.assertIsNone(self.proponi(altro["name"])["deal"])


class LaTrattativa(PreventiviCase):
	"""The deal is the sale, the quote what the person is asked to accept: a deal of
	the quotes pipeline lists its quotes and makes new ones its own; accepted, it is
	won and worth what was agreed. A quote never moves a deal of another pipeline, nor
	opens a closed one again."""

	def trattativa(self, nome_pipeline, lead=None):
		frappe.set_user("Administrator")
		doc = frappe.new_doc("CRM Deal")
		doc.lead = lead or self.anna.name
		doc.status = frappe.db.get_value(
			"CRM Deal Status", {"pipeline": nome_pipeline}, "name", order_by="position asc"
		)
		doc.flags.from_inquiry = True
		doc.insert(ignore_permissions=True)
		return doc.name

	def scrive_nella(self, deal, user=OPERATORE):
		self.come(user)
		return preventivi.save_quote(
			self.anna.name,
			json.dumps({"title": "Dalla trattativa", "items": [{"service": self.viso.name, "rate": 60}]}),
			deal=deal,
		)

	def test_accettato_la_trattativa_vinta_vale_il_preventivo(self):
		fatto = self.scrive()
		self.proponi(fatto["name"])
		self.come(DESK)
		accettato = preventivi.accept_quote(fatto["name"])
		deal = frappe.get_doc("CRM Deal", accettato["deal"])
		self.assertEqual(self.tipo_del_deal(deal.name), "Won")
		# the number the dashboards add up for what was won
		self.assertEqual((deal.deal_value, deal.expected_deal_value), (240, 240))

	def test_il_totale_dei_prodotti_non_scrive_sopra_il_preventivo(self):
		"""A deal kept from before the products grid went still has a products
		total: with the expected value kept up to date from the products, every
		save wrote it over the value of the quote proposed on the deal (doc 50)."""
		prima = frappe.db.get_single_value("FCRM Settings", "auto_update_expected_deal_value")
		self.addCleanup(frappe.db.set_single_value, "FCRM Settings", "auto_update_expected_deal_value", prima)
		frappe.db.set_single_value("FCRM Settings", "auto_update_expected_deal_value", 1)
		deal = self.trattativa(pipeline.quale())
		frappe.db.set_value("CRM Deal", deal, {"total": 500, "net_total": 500, "expected_deal_value": 500})
		self.proponi(self.scrive_nella(deal)["name"])
		self.assertEqual(frappe.db.get_value("CRM Deal", deal, "expected_deal_value"), 60)
		# saved again afterwards, it keeps the quote's value
		frappe.set_user("Administrator")
		doc = frappe.get_doc("CRM Deal", deal)
		doc.flags.from_inquiry = True
		doc.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("CRM Deal", deal, "expected_deal_value"), 60)

	def test_dalla_trattativa_i_suoi_preventivi(self):
		primo = self.scrive()
		deal = self.proponi(primo["name"])["deal"]
		altro = self.scrive(title="Di Anna, senza trattativa")
		# a new quote made from the deal's page is the deal's
		nuovo = self.scrive_nella(deal)
		self.assertEqual(frappe.db.get_value(preventivi.DOCTYPE, nuovo["name"], "deal"), deal)
		della_trattativa = preventivi.get_quotes(self.anna.name, deal=deal)
		self.assertEqual(della_trattativa["deal"], deal)
		self.assertEqual({q["name"] for q in della_trattativa["quotes"]}, {primo["name"], nuovo["name"]})
		# the person's page lists them all
		self.assertEqual(
			{q["name"] for q in preventivi.get_quotes(self.anna.name)["quotes"]},
			{primo["name"], nuovo["name"], altro["name"]},
		)
		# the quote says which deal it is, in the stage's words
		self.assertTrue(preventivi.get_quote(nuovo["name"])["deal_label"])
		# proposed, it moves its own deal: no second deal for one sale
		self.assertEqual(self.proponi(nuovo["name"])["deal"], deal)

	def test_una_trattativa_di_un_altra_pipeline_resta_dov_e(self):
		from crm.clienti import pipeline as nuovi_clienti

		frappe.set_user("Administrator")
		nuovi_clienti.crea()
		primo_contatto = self.trattativa(nuovi_clienti.quale())
		stadio = frappe.db.get_value("CRM Deal", primo_contatto, "status")
		gia = self.scrive(title="Già scritto")
		# its page shows the person's quotes, and a quote made there is no quote of its
		self.come(OPERATORE)
		qui = preventivi.get_quotes(self.anna.name, deal=primo_contatto)
		self.assertIsNone(qui["deal"])
		self.assertEqual([q["name"] for q in qui["quotes"]], [gia["name"]])
		fatto = self.scrive_nella(primo_contatto)
		self.assertFalse(frappe.db.get_value(preventivi.DOCTYPE, fatto["name"], "deal"))
		# proposed, it goes to the quotes pipeline; the first visit's deal stays where it is
		proposto = self.proponi(fatto["name"])
		self.assertNotEqual(proposto["deal"], primo_contatto)
		self.assertEqual(frappe.db.get_value("CRM Deal", proposto["deal"], "pipeline"), pipeline.quale())
		self.assertEqual(frappe.db.get_value("CRM Deal", primo_contatto, "status"), stadio)

	def test_la_trattativa_di_un_altra_persona(self):
		frappe.set_user("Administrator")
		bruno = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Bruno", "last_name": "Altro"}).insert(
			ignore_permissions=True
		)
		sua = self.trattativa(pipeline.quale(), lead=bruno.name)
		self.come(OPERATORE)
		with self.assertRaises(frappe.PermissionError):
			preventivi.get_quotes(self.anna.name, deal=sua)
		with self.assertRaises(frappe.PermissionError):
			self.scrive_nella(sua)

	def test_una_trattativa_chiusa_non_si_riapre(self):
		fatto = self.scrive()
		perso = self.proponi(fatto["name"])["deal"]
		self.come(DESK)
		preventivi.decline_quote(fatto["name"], reason="Pricing")
		# a new version after a "no" is a new sale: the lost deal stays lost
		self.come(OPERATORE)
		nuova = preventivi.copy_quote(fatto["name"])
		self.assertFalse(frappe.db.get_value(preventivi.DOCTYPE, nuova["name"], "deal"))
		riproposta = self.proponi(nuova["name"])
		self.assertNotEqual(riproposta["deal"], perso)
		self.assertEqual(self.tipo_del_deal(perso), "Lost")
		# while the deal is open, a new version stays on it
		self.come(OPERATORE)
		ancora = preventivi.copy_quote(nuova["name"])
		self.assertEqual(frappe.db.get_value(preventivi.DOCTYPE, ancora["name"], "deal"), riproposta["deal"])


class INumeri(PreventiviCase):
	"""The dashboard: quotes proposed, the share accepted, the ones to call back."""

	def risposta(self, widget_id, viewer, scope=None):
		from crm.dashboard import registry
		from crm.dashboard.context import Context

		frappe.set_user(viewer)
		widget = registry.get(widget_id)
		oggi = getdate()
		ctx = Context.build(
			add_days(oggi, -1),
			add_days(oggi, 1),
			viewer=viewer,
			scope=scope or widget.scope,
			config=widget.clean_config({}),
		)
		return widget.fn(ctx)

	def test_proposti_accettati_e_da_richiamare(self):
		accettato, rifiutato, in_attesa, ripensato = (
			self.scrive(title=titolo)["name"] for titolo in ("Sì", "No", "Aspetta", "Ci ripensa")
		)
		for nome in (accettato, rifiutato, in_attesa, ripensato):
			self.proponi(nome)
		self.come(DESK)
		preventivi.accept_quote(accettato)
		preventivi.decline_quote(rifiutato, reason="Pricing")
		preventivi.decline_quote(ripensato, reason="Pricing")
		# put right after the "no": the same conversation, not a second "no"
		self.come(OPERATORE)
		preventivi.copy_quote(ripensato)

		# whose work is counted is the author's: the operator's numbers are these quotes'
		self.assertEqual(self.risposta("quotes_proposed", OPERATORE)["value"], 4)
		self.assertEqual(self.risposta("quotes_acceptance_rate", OPERATORE)["value"], 50)
		self.assertEqual(self.risposta("quotes_waiting_value", OPERATORE)["value"], 240)
		lista = self.risposta("quotes_waiting", OPERATORE)
		self.assertEqual(lista["total"], 1)
		[voce] = lista["items"]
		self.assertEqual((voce["title"], voce["subtitle"], voce["value"]), ("Anna Area", "Aspetta", 240))
		self.assertEqual(voce["route"]["params"]["leadId"], self.anna.name)
		self.assertNotIn("badge", voce)
		# three days without an answer: to call back
		frappe.set_user("Administrator")
		frappe.db.set_value(
			preventivi.DOCTYPE, in_attesa, "proposed_on", add_days(getdate(), -4), update_modified=False
		)
		self.assertEqual(self.risposta("quotes_waiting", OPERATORE)["items"][0]["badge"]["color"], "orange")

	def test_chi_non_legge_i_preventivi_non_li_conta(self):
		self.proponi(self.scrive()["name"])
		# the whole centre's work, so that only the rule of reading decides
		prima = self.risposta("quotes_waiting", SALES, scope="site")
		self.assertIn(self.anna.name, [v["route"]["params"]["leadId"] for v in prima["items"]])
		frappe.set_user("Administrator")
		utenti.assegna_livelli(SALES, ["marketing"])
		livelli_cache()
		self.assertEqual(self.risposta("quotes_waiting", SALES, scope="site")["total"], 0)
		self.assertEqual(self.risposta("quotes_waiting_value", SALES, scope="site")["value"], 0)


def livelli_cache():
	from crm.permissions import livelli

	livelli.dimentica_cache()


class IlLayoutDellaTrattativa(unittest.TestCase):
	"""The patch that takes the products grid off the deal's page."""

	def test_via_la_griglia_e_i_suoi_totali(self):
		from crm.patches.v1_0.deals_take_their_value_from_quotes import senza_prodotti

		dettagli = {"label": "Details", "columns": [{"name": "a", "fields": ["organization", "total"]}]}
		prodotti = {"label": "Products", "columns": [{"name": "b", "fields": ["products"]}]}
		totali = {"columns": [{"name": "c", "fields": ["total"]}, {"name": "d", "fields": ["net_total"]}]}
		vuota = {"label": "Empty", "columns": [{"name": "e", "fields": []}]}
		con_schede = json.dumps([{"name": "first_tab", "sections": [dettagli, prodotti, totali, vuota]}])
		self.assertEqual(
			json.loads(senza_prodotti(con_schede)),
			[
				{
					"name": "first_tab",
					"sections": [
						{"label": "Details", "columns": [{"name": "a", "fields": ["organization"]}]},
						# what was empty before is not ours to take away
						vuota,
					],
				}
			],
		)
		# an old layout without tabs keeps its shape
		self.assertEqual(json.loads(senza_prodotti(json.dumps([prodotti, vuota]))), [vuota])
		# nothing to take away, nothing touched; what does not read stays as it is
		gia = json.dumps([vuota])
		self.assertIs(senza_prodotti(gia), gia)
		self.assertEqual(senza_prodotti("{rotto"), "{rotto")
		self.assertIsNone(senza_prodotti(None))
