# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A centre made ready on a test bench, its clock, and what its people read.

The test site is not empty and is not a test bench: the flag is given for the
test, the site forced, and nothing is committed - the class rolls back what the
centre wrote, so the next tests find the site as it was.
"""

from __future__ import annotations

import datetime
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime, now_datetime

from crm.collaudo import api, prepara, tempo
from crm.collaudo import regole as R
from crm.permissions import livelli


class CentroDiProva(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._banco = patch.dict(frappe.local.conf, {"dottorcloud_collaudo": 1})
		self._banco.start()
		# what the centre writes stays in this test's transaction
		self._commit = patch.object(frappe.db, "commit")
		self._commit.start()

	def tearDown(self):
		self._commit.stop()
		self._banco.stop()
		tempo._applica(None)
		frappe.set_user("Administrator")
		frappe.db.rollback()
		frappe.clear_cache()
		livelli.dimentica_cache()

	def test_solo_su_un_banco_di_prova(self):
		with patch.dict(frappe.local.conf, {"dottorcloud_collaudo": 0}):
			self.assertRaises(frappe.PermissionError, prepara.centro, servizi_finti=0, forza=1)
			self.assertRaises(frappe.PermissionError, tempo.adesso)
			self.assertRaises(frappe.PermissionError, api.posta, "x@example.com")

	def test_solo_per_l_agenzia(self):
		frappe.set_user("Guest")
		self.assertRaises(frappe.PermissionError, prepara.centro, servizi_finti=0, forza=1)

	def test_un_sito_con_le_sue_persone_e_rifiutato(self):
		frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Vera", "last_name": "Persona", "email": "vera@centro.it"}
		).insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, prepara.centro, servizi_finti=0)

	def test_il_centro_e_intero_e_si_rifa(self):
		fatto = prepara.centro(servizi_finti=0, forza=1)
		self.assertEqual(fatto["problems"], [])
		squadra = prepara.squadra()
		self.assertEqual(set(squadra), set(R.RUOLI))
		self.assertEqual(livelli.livelli_di(squadra["medico"]), ["operatore", "direzione"])
		self.assertEqual(livelli.livelli_di(squadra["segreteria"]), ["segreteria"])
		self.assertEqual(fatto["team"]["medico"]["password"], R.PASSWORD)
		# its company issues in test, as a medical centre
		azienda = frappe.get_doc("CRM Invoicing Company", fatto["company"])
		self.assertEqual(azienda.provider_environment, "sandbox")
		self.assertEqual(azienda.sender_category, "struttura_autorizzata")
		# the shipped clinical sheets, published by the medical director
		self.assertTrue(
			frappe.db.count(
				"CRM Form Template", {"use": "Sheet", "clinical": 1, "current_version": ["is", "set"]}
			)
		)
		# nothing outside on staging
		self.assertFalse(frappe.db.get_single_value("CRM Stripe Settings", "enabled"))
		self.assertFalse(frappe.db.get_single_value("CRM Scheduling Settings", "video_server"))

		# marketing's campaign by hand and the review request, on
		for definizione in R.AUTOMAZIONI:
			self.assertTrue(frappe.db.get_value("CRM Automation", {"title": definizione["title"]}, "enabled"))

		prima = {
			d: frappe.db.count(d)
			for d in ("CRM Service", "CRM Location", "CRM Resource", "User", "CRM Automation")
		}
		di_nuovo = prepara.centro(servizi_finti=0, forza=1)
		self.assertEqual(di_nuovo["problems"], [])
		self.assertEqual(prima, {d: frappe.db.count(d) for d in prima})

	def test_le_persone_vere_dello_staging(self):
		fatto = prepara.centro(
			persone={
				"dietista": {
					"email": "dietista.vera@centro.example.com",
					"first_name": "Vera",
					"last_name": "Dieta",
				}
			},
			servizi_finti=0,
			forza=1,
		)
		self.assertEqual(fatto["team"]["dietista"]["email"], "dietista.vera@centro.example.com")
		self.assertTrue(
			frappe.db.get_value("CRM Staff Schedule", {"user": "dietista.vera@centro.example.com"})
		)


class OrologioDelBanco(IntegrationTestCase):
	def setUp(self):
		try:
			import freezegun
		except ImportError:
			self.skipTest("freezegun is a development requirement")
		frappe.set_user("Administrator")
		self._banco = patch.dict(frappe.local.conf, {"dottorcloud_collaudo": 1})
		self._banco.start()
		self._commit = patch.object(frappe.db, "commit")
		self._commit.start()

	def tearDown(self):
		tempo._applica(None)
		self._commit.stop()
		self._banco.stop()
		frappe.db.rollback()
		frappe.clear_cache()

	def test_l_orologio_va_avanti_e_torna(self):
		tra_un_anno = (now_datetime() + datetime.timedelta(days=400)).replace(microsecond=0)
		stato = tempo.imposta(str(tra_un_anno))
		self.assertTrue(stato["moved"])
		self.assertLess(abs((now_datetime() - tra_un_anno).total_seconds()), 60)
		# never backwards
		self.assertRaises(
			frappe.ValidationError, tempo.imposta, str(tra_un_anno - datetime.timedelta(days=30))
		)
		tempo.azzera()
		self.assertLess(abs((now_datetime() - get_datetime(frappe.utils.now())).total_seconds()), 5)
		self.assertLess(now_datetime(), tra_un_anno - datetime.timedelta(days=300))

	def test_su_un_altro_sito_l_orologio_resta_vero(self):
		from freezegun.api import real_datetime

		tempo._applica(86400 * 30)
		self.assertGreater(now_datetime(), real_datetime.now() + datetime.timedelta(days=29))
		with patch.dict(frappe.local.conf, {"dottorcloud_collaudo": 0}):
			tempo.allinea()
		self.assertLess(abs((now_datetime() - real_datetime.now()).total_seconds()), 86400)

	def test_esegue_solo_i_lavori_programmati(self):
		self.assertRaises(frappe.ValidationError, tempo.esegui, "frappe.client.delete")
		self.assertIn("crm.scheduling.promemoria.ogni_quarto_d_ora", tempo.lavori_programmati())


class PostaDelBanco(IntegrationTestCase):
	def test_la_posta_di_una_persona(self):
		with patch.dict(frappe.local.conf, {"dottorcloud_collaudo": 1}):
			frappe.sendmail(
				recipients=["lettrice.collaudo@example.com"],
				subject="Il tuo codice",
				message='<p>Il codice è <b>123456</b>.</p><p><a href="http://sito.example.com/area?x=1&amp;y=2">Entra</a></p>',
				now=False,
			)
			lette = api.posta("lettrice.collaudo@example.com")
		self.assertTrue(lette)
		ultima = lette[-1]
		self.assertEqual(ultima["subject"], "Il tuo codice")
		self.assertIn("123456", ultima["text"])
		self.assertIn("http://sito.example.com/area?x=1&y=2", ultima["links"])
		frappe.db.rollback()
