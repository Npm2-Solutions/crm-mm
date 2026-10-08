# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote answered in the client area, on a site without the clinic.

The therapist proposes Anna's quote; the desk sends it to sign by email, with the
area's link that lands on the quotes. Anna, in with her code, reads it, signs it
with her finger and confirms: the quote is accepted in the area, the deal is won as
at the desk, the stroke and the evidence are kept, the signed copy is made once
with its fingerprint, the register's chain is whole, and the therapist and the desk
are told - without the quote's title. Without a code just verified she does not
sign; whoever only follows her does not answer; the centre's preview changes
nothing; a quote past its day is not answered. Declined with a reason, the deal is
lost with it. A person of the demo data is sent nothing.
"""

import hashlib
import json
from unittest import mock

import frappe
from frappe.utils import add_days, getdate

from crm.area import accesso, anteprima
from crm.area.tests.test_area import ANNA, DESK, OPERATORE
from crm.moduli import traccia
from crm.moduli.tests.test_compilazioni import tratto
from crm.notifiche import regole as N
from crm.preventivi import api as preventivi
from crm.preventivi import area, firma
from crm.preventivi import regole as R
from crm.preventivi.tests.test_preventivi import PreventiviCase


class FirmaCase(PreventiviCase):
	def proposto(self):
		fatto = self.scrive()
		return self.proponi(fatto["name"])

	def avvisi(self, utente):
		return frappe.get_all(
			"CRM Notification",
			filters={"to_user": utente, "notification_type_doctype": "CRM Quote"},
			fields=["sentence", "sentence_args", "reference_name", "notification_type_doc"],
		)


class NellArea(FirmaCase):
	def test_anna_lo_firma_nella_sua_area(self):
		proposto = self.proposto()
		self.invita()
		# the desk sends it to sign: the area's link, by email
		self.come(DESK)
		vie = {v["channel"]: v for v in firma.sign_options(proposto["name"])["channels"]}
		self.assertTrue(vie["Email"]["to"])
		self.assertTrue(vie["SMS"]["reason"])
		mandato = firma.send_to_sign(proposto["name"], "Email")
		self.assertTrue(mandato["sent_to_sign_on"])
		self.assertTrue(mandato["sent_to_sign_to"].startswith("Email · "))
		self.assertTrue(frappe.db.exists("CRM Area Link", {"user": ANNA, "page": "plans", "reason": "quote"}))
		# in with her code, Anna reads it, still to answer
		self.entra()
		[nell_area] = area.area_quotes(self.anna.name)["quotes"]
		self.assertTrue(nell_area["can_answer"])
		self.assertTrue(nell_area["has_pdf"])
		fatto = firma.accept_in_area(self.anna.name, proposto["name"], tratto())
		[nell_area] = fatto["quotes"]
		self.assertEqual(nell_area["status"], R.ACCETTATO)
		self.assertFalse(nell_area["can_answer"])
		self.assertTrue(nell_area["signed_on"])

		frappe.set_user("Administrator")
		doc = frappe.get_doc(preventivi.DOCTYPE, proposto["name"])
		self.assertEqual((doc.answered_in, doc.accepted_by), (R.NELL_AREA, ANNA))
		self.assertEqual(doc.signer_name, "Anna Area")
		self.assertTrue(doc.signature and doc.signed_on)
		# what she signed is the PDF as it was proposed
		pdf = frappe.get_doc("File", {"file_url": doc.quote_pdf}).get_content(encodings=[])
		self.assertEqual(doc.signed_hash, hashlib.sha256(pdf).hexdigest())
		# the signed copy, once, with its fingerprint
		copia = frappe.get_doc("File", {"file_url": doc.signed_pdf})
		self.assertTrue(copia.is_private)
		self.assertEqual(hashlib.sha256(copia.get_content(encodings=[])).hexdigest(), doc.signed_pdf_hash)
		self.assertTrue(doc.signed_pdf_conformance)
		eventi = [e.event for e in traccia.eventi(preventivi.DOCTYPE, doc.name)]
		self.assertEqual(eventi[:3], ["sent", "signed", "pdf_generated"])
		self.assertTrue(traccia.verifica_catena(preventivi.DOCTYPE, doc.name)["integra"])
		# the deal is won, as at the desk
		self.assertEqual(self.tipo_del_deal(doc.deal), "Won")
		# the therapist and the desk hear of it, without the quote's title
		for utente in (OPERATORE, DESK):
			[avviso] = self.avvisi(utente)
			self.assertEqual(avviso.sentence, N.PREVENTIVO_FIRMATO)
			self.assertEqual(json.loads(avviso.sentence_args), ["Anna Area"])
			self.assertNotIn("Trattamenti", avviso.sentence_args)
		# the desk reads how it was answered
		self.come(DESK)
		letto = preventivi.get_quote(doc.name)
		self.assertEqual((letto["answered_in"], letto["signer_name"]), (R.NELL_AREA, "Anna Area"))
		self.assertTrue(letto["signed_pdf"])
		# a second time: no longer waiting for an answer
		frappe.set_user(ANNA)
		with self.assertRaises(frappe.ValidationError):
			firma.accept_in_area(self.anna.name, doc.name, tratto())

	def test_senza_un_codice_appena_letto_non_si_firma(self):
		proposto = self.proposto()
		self.invita()
		self.entra()
		frappe.cache.delete_value(accesso._chiave_verifica(frappe.session.sid))
		self.assertFalse(area.area_quotes(self.anna.name)["verified"])
		with self.assertRaises(frappe.PermissionError):
			firma.accept_in_area(self.anna.name, proposto["name"], tratto())
		# a stroke that is not a picture is no signature
		accesso.segna_verificato()
		with self.assertRaises(frappe.ValidationError):
			firma.accept_in_area(self.anna.name, proposto["name"], "data:image/png;base64,xx")
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(preventivi.DOCTYPE, proposto["name"], "status"), R.PROPOSTO)

	def test_lo_rifiuta_con_il_suo_motivo(self):
		proposto = self.proposto()
		self.invita()
		self.entra()
		fatto = firma.decline_in_area(self.anna.name, proposto["name"], "  Costa troppo  ")
		self.assertEqual(fatto["quotes"], [])
		frappe.set_user("Administrator")
		doc = frappe.get_doc(preventivi.DOCTYPE, proposto["name"])
		self.assertEqual(
			(doc.status, doc.answered_in, doc.decline_reason), (R.RIFIUTATO, R.NELL_AREA, "Costa troppo")
		)
		self.assertEqual(self.tipo_del_deal(doc.deal), "Lost")
		self.assertEqual(frappe.db.get_value("CRM Deal", doc.deal, "lost_notes"), "Costa troppo")
		[avviso] = self.avvisi(OPERATORE)
		self.assertEqual(avviso.sentence, N.PREVENTIVO_RIFIUTATO)

	def test_scaduto_non_si_risponde(self):
		proposto = self.proposto()
		frappe.db.set_value(preventivi.DOCTYPE, proposto["name"], "valid_until", add_days(getdate(), -1))
		self.invita()
		self.entra()
		[nell_area] = area.area_quotes(self.anna.name)["quotes"]
		self.assertTrue(nell_area["expired"])
		self.assertFalse(nell_area["can_answer"])
		with self.assertRaises(frappe.ValidationError):
			firma.decline_in_area(self.anna.name, proposto["name"])

	def test_l_anteprima_non_cambia_niente(self):
		proposto = self.proposto()
		self.come(DESK)
		anteprima.start(self.anna.name)
		self.assertFalse(area.area_quotes(self.anna.name)["can_answer"])
		for chiamata in (
			lambda: firma.accept_in_area(self.anna.name, proposto["name"], tratto()),
			lambda: firma.decline_in_area(self.anna.name, proposto["name"]),
		):
			with self.assertRaises(frappe.PermissionError):
				chiamata()
		anteprima.stop()

	def test_chi_la_segue_soltanto_non_risponde(self):
		proposto = self.proposto()
		self.invita(relation=accesso.SEGUE, email="segue.area@example.com")
		self.entra("segue.area@example.com")
		self.assertFalse(area.area_quotes(self.anna.name)["can_answer"])
		with self.assertRaises(frappe.PermissionError):
			firma.decline_in_area(self.anna.name, proposto["name"])

	def test_un_altra_persona_non_lo_tocca(self):
		proposto = self.proposto()
		self.invita()
		self.entra()
		with self.assertRaises(frappe.PermissionError):
			firma.decline_in_area("CRM-LEAD-NOBODY", proposto["name"])

	def test_alla_demo_non_si_manda_niente(self):
		proposto = self.proposto()
		self.come(DESK)
		with mock.patch.object(firma, "_della_demo", return_value=True):
			with self.assertRaises(frappe.ValidationError):
				firma.send_to_sign(proposto["name"], "Email")
		self.assertFalse(frappe.db.get_value(preventivi.DOCTYPE, proposto["name"], "sent_to_sign_on"))

	def test_senza_posta_in_uscita_non_si_manda_per_email(self):
		from crm.moduli import richieste

		proposto = self.proposto()
		self.come(DESK)
		with mock.patch.object(richieste, "_posta_in_uscita", return_value=False):
			vie = {v["channel"]: v for v in firma.sign_options(proposto["name"])["channels"]}
			self.assertIsNone(vie["Email"]["to"])
			self.assertTrue(vie["Email"]["reason"])
			with self.assertRaises(frappe.ValidationError):
				firma.send_to_sign(proposto["name"], "Email")
