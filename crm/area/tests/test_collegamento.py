# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The link by email that enters the area.

The desk writes on Anna's board: the email carries a link of hers that enters
without a code, once, within seven days, and counts as a code just read. Spent,
old or made up, it enters nobody and says the same. An invoice issued to Anna is
told the same way where the centre switched it on: off, nothing leaves; on, her
area is opened if she had none, and for a minor it is the parent's. A test
invoice, never.
"""

import email
import re
from unittest import mock

import frappe
from frappe.utils import add_days, now_datetime

from crm.area import accesso, collegamento, messaggi
from crm.area.tests.test_area import ANNA, DESK, PADRE, AreaCase
from crm.persone import collegate, legami


def _testo_della_posta() -> str:
	"""The last email as its reader sees it: the queue keeps it as MIME."""
	posta = email.message_from_string(frappe.get_last_doc("Email Queue").message)
	return "".join(
		parte.get_payload(decode=True).decode()
		for parte in posta.walk()
		if parte.get_content_type() == "text/html"
	)


def _link_della_posta() -> str:
	[indirizzo] = set(re.findall(r"/area/login\?link=([A-Za-z0-9_\-]+)", _testo_della_posta()))
	return indirizzo


class IlLink(AreaCase):
	def scrivi(self):
		self.invita()
		self.come(DESK)
		messaggi.post_message(self.anna.name, "Porti la tessera")
		frappe.set_user("Administrator")
		return _link_della_posta()

	def test_la_bacheca_manda_un_link_che_entra_una_volta(self):
		link = self.scrivi()
		frappe.set_user("Guest")
		self.assertEqual(collegamento.enter(link), {"page": "messages"})
		self.assertEqual(frappe.session.user, ANNA)
		# a code just read: a document may be downloaded at once
		self.assertTrue(accesso.verificato_da_poco())
		frappe.set_user("Guest")
		with self.assertRaises(frappe.ValidationError):
			collegamento.enter(link)
		self.assertEqual(frappe.session.user, "Guest")

	def test_si_tiene_solo_l_impronta(self):
		link = self.scrivi()
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists(collegamento.LINK, {"token_hash": link}))
		self.assertTrue(frappe.db.exists(collegamento.LINK, {"token_hash": collegamento._impronta(link)}))

	def test_vecchio_o_inventato_non_entra(self):
		link = self.scrivi()
		frappe.set_user("Administrator")
		frappe.db.set_value(
			collegamento.LINK,
			{"token_hash": collegamento._impronta(link)},
			"expires_on",
			add_days(now_datetime(), -1),
		)
		for prova in (link, "inventato", ""):
			frappe.set_user("Guest")
			with self.assertRaises(frappe.ValidationError):
				collegamento.enter(prova)
		self.assertEqual(frappe.session.user, "Guest")

	def test_area_chiusa_il_link_non_apre(self):
		link = self.scrivi()
		self.come(DESK)
		accesso.revoke(self.anna.name, ANNA)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			collegamento.enter(link)


class IlDocumentoNuovo(AreaCase):
	def accendi(self, si=True):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("CRM Area Settings", "email_new_documents", int(si))

	def fattura(self, lead, prova=0):
		return frappe._dict(party_type="CRM Lead", party=lead, test_document=prova)

	def test_spento_non_parte_niente(self):
		self.accendi(False)
		prima = frappe.db.count("Email Queue")
		collegamento.fattura_emessa(self.fattura(self.anna.name))
		self.assertEqual(frappe.db.count("Email Queue"), prima)
		self.assertFalse(accesso.accessi_aperti(self.anna.name))

	def test_acceso_apre_l_area_e_manda_il_link(self):
		self.accendi()
		prima = frappe.db.count("Email Queue")
		collegamento.fattura_emessa(self.fattura(self.anna.name))
		# one email, the link's: never the invitation besides it
		self.assertEqual(frappe.db.count("Email Queue"), prima + 1)
		[aperto] = accesso.accessi_aperti(self.anna.name)
		self.assertEqual(aperto.user, ANNA)
		posta = frappe.get_last_doc("Email Queue")
		self.assertEqual([r.recipient for r in posta.recipients], [ANNA])
		# what it is stays in the area
		self.assertNotIn(".pdf", _testo_della_posta())
		link = _link_della_posta()
		frappe.set_user("Guest")
		self.assertEqual(collegamento.enter(link), {"page": "documents"})

	def test_due_documenti_di_fila_una_email(self):
		# the balance of a visit and the next visit's deposit, a few seconds apart:
		# the first email's link is still there to use
		self.accendi()
		prima = frappe.db.count("Email Queue")
		collegamento.fattura_emessa(self.fattura(self.anna.name))
		link = _link_della_posta()
		collegamento.fattura_emessa(self.fattura(self.anna.name))
		self.assertEqual(frappe.db.count("Email Queue"), prima + 1)
		# once she entered by it, the next document is news again
		frappe.set_user("Guest")
		collegamento.enter(link)
		frappe.set_user("Administrator")
		collegamento.fattura_emessa(self.fattura(self.anna.name))
		self.assertEqual(frappe.db.count("Email Queue"), prima + 2)

	def test_una_fattura_di_prova_mai(self):
		self.accendi()
		prima = frappe.db.count("Email Queue")
		collegamento.fattura_emessa(self.fattura(self.anna.name, prova=1))
		self.assertEqual(frappe.db.count("Email Queue"), prima)

	def test_per_un_minore_va_al_genitore(self):
		self.accendi()
		frappe.set_user("Administrator")
		padre = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Marco", "last_name": "Area", "email": PADRE}
		).insert(ignore_permissions=True)
		figlio = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Leo", "last_name": "Area"}).insert(
			ignore_permissions=True
		)
		collegate.assicura_legame(figlio.name, padre.name, legami.GENITORE, represents=1)
		collegamento.fattura_emessa(self.fattura(figlio.name))
		[aperto] = accesso.accessi_aperti(figlio.name)
		self.assertEqual((aperto.user, aperto.relation), (PADRE, accesso.TUTORE))

	def test_la_demo_non_scrive(self):
		self.accendi()
		prima = frappe.db.count("Email Queue")
		with mock.patch.object(collegamento, "_della_demo", return_value=True):
			collegamento.fattura_emessa(self.fattura(self.anna.name))
		self.assertEqual(frappe.db.count("Email Queue"), prima)
