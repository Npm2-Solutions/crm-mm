# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A campaign on a real site: the list as the reader sees it, who is left out and
why, the enrolment through the engine, the report kept on the campaign."""

import json
from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from crm.automation import campagne
from crm.automation import campagne_regole as R
from crm.moduli import consensi
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

DESK = "campagne.desk@example.com"


def automazione(titolo, passi, **altro):
	return frappe.get_doc(
		{
			"doctype": "CRM Automation",
			"title": titolo,
			"enabled": 1,
			"triggers": [{"trigger_event": "Started by Hand"}],
			"steps": json.dumps(passi),
			**altro,
		}
	).insert(ignore_permissions=True)


def persona(nome, **campi):
	return frappe.get_doc(
		{"doctype": "CRM Lead", "first_name": nome, "last_name": "Campagna", **campi}
	).insert(ignore_permissions=True)


class CampagnaCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		consensi.assicura_tipi()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()


class LAnteprima(CampagnaCase):
	def test_chi_resta_fuori_e_perche(self):
		auto = automazione("Promo SMS", [{"type": "send_sms", "message": "Ciao"}], marketing_consent=1)
		entra = persona("Entra", mobile_no="+393330000001")
		senza = persona("Senza")
		fermo = persona("Fermo", mobile_no="+393330000002", sms_opt_out=1)
		no = persona("No", mobile_no="+393330000003")
		for p in (entra, senza, fermo):
			consensi.registra_risposta(p.name, "marketing")
		nomi = [entra.name, senza.name, fermo.name, no.name]

		vista = campagne.preview_campaign(auto.name, names=nomi)
		self.assertEqual(vista["total"], 4)
		self.assertEqual(vista["enrolled"], 1)
		self.assertEqual(vista["skipped"], {R.SENZA_CONSENSO: 1, R.STOP: 1, R.SENZA_RECAPITO: 1})
		self.assertEqual(vista["channels"], ["sms"])

	def test_le_condizioni_dell_avvio(self):
		auto = automazione("Solo i Mario", [{"type": "add_note", "comment": "x"}])
		auto.triggers[0].trigger_condition = json.dumps(
			[[{"field": "first_name", "operator": "equals", "value": "Mario"}]]
		)
		auto.save()
		mario, luca = persona("Mario"), persona("Luca")
		vista = campagne.preview_campaign(auto.name, names=[mario.name, luca.name])
		self.assertEqual(vista["enrolled"], 1)
		self.assertEqual(vista["skipped"], {R.CONDIZIONI: 1})

	def test_dai_filtri_della_vista(self):
		auto = automazione("Dai filtri", [{"type": "add_note", "comment": "x"}])
		persona("Filtrata", email="filtrata.campagna@example.com")
		vista = campagne.preview_campaign(auto.name, filters={"email": "filtrata.campagna@example.com"})
		self.assertEqual(vista["total"], 1)

	def test_un_automazione_che_non_parte_a_mano(self):
		auto = automazione("Evento", [{"type": "add_note", "comment": "x"}])
		auto.triggers[0].trigger_event = "Lead Created"
		auto.save()
		with self.assertRaises(frappe.ValidationError):
			campagne.preview_campaign(auto.name, names=[persona("X").name])

	def test_una_lista_troppo_grande(self):
		auto = automazione("Grande", [{"type": "add_note", "comment": "x"}])
		nomi = [persona("A").name, persona("B").name]
		with mock.patch.object(R, "MASSIMO", 1), self.assertRaises(frappe.ValidationError):
			campagne.preview_campaign(auto.name, names=nomi)

	def test_solo_chi_gestisce_le_automazioni(self):
		make_user(DESK)
		utenti.sincronizza()
		utenti.assegna_livelli(DESK, ["segreteria"])
		livelli.dimentica_cache()
		auto = automazione("Non per la segreteria", [{"type": "add_note", "comment": "x"}])
		frappe.set_user(DESK)
		with self.assertRaises(frappe.PermissionError):
			campagne.preview_campaign(auto.name, names=[])
		with self.assertRaises(frappe.PermissionError):
			campagne.get_campaigns_to_send()


class LInvio(CampagnaCase):
	def test_iscrive_e_tiene_il_resoconto(self):
		auto = automazione("Benvenuto", [{"type": "add_note", "comment": "Campagna"}], marketing_consent=1)
		si, no = persona("Si"), persona("No")
		consensi.registra_risposta(si.name, "marketing")

		self.assertIn(auto.name, [c["name"] for c in campagne.get_campaigns_to_send()])
		nome = campagne.send_campaign(auto.name, names=[si.name, no.name], source="2 scelte")["name"]
		campagna = frappe.get_doc(campagne.CAMPAGNA, nome)
		self.assertEqual(campagna.status, "Done")
		self.assertEqual((campagna.total, campagna.enrolled), (2, 1))
		self.assertEqual(json.loads(campagna.skipped), {R.SENZA_CONSENSO: 1})
		stati = dict(
			frappe.get_all(
				"CRM Automation Enrollment",
				filters={"automation": auto.name},
				fields=["reference_name", "status"],
				as_list=True,
			)
		)
		self.assertEqual(stati, {si.name: "Completed", no.name: "Skipped"})
		enr = frappe.get_doc(
			"CRM Automation Enrollment", {"automation": auto.name, "reference_name": si.name}
		)
		self.assertEqual(json.loads(enr.state)["payload"], {"campaign": nome})

		# sent again: nobody twice, the skipped one still skipped once
		di_nuovo = campagne.send_campaign(auto.name, names=[si.name, no.name])["name"]
		self.assertEqual(
			json.loads(frappe.db.get_value(campagne.CAMPAGNA, di_nuovo, "skipped")),
			{R.GIA_DENTRO: 1, R.SENZA_CONSENSO: 1},
		)
		self.assertEqual(
			frappe.db.count("CRM Automation Enrollment", {"automation": auto.name, "status": "Skipped"}), 1
		)
		resoconti = campagne.get_campaigns(auto.name)
		self.assertEqual([r["name"] for r in resoconti], [di_nuovo, nome])
		self.assertEqual(resoconti[1]["source"], "2 scelte")

	def test_una_lista_vuota(self):
		auto = automazione("Vuota", [{"type": "add_note", "comment": "x"}])
		with self.assertRaises(frappe.ValidationError):
			campagne.send_campaign(auto.name, filters={"name": "nessuno-qui"})

	def test_l_automazione_tolta_porta_via_le_campagne(self):
		auto = automazione("Via", [{"type": "add_note", "comment": "x"}])
		campagne.send_campaign(auto.name, names=[persona("Uno").name])
		frappe.delete_doc("CRM Automation", auto.name)
		self.assertFalse(frappe.db.exists(campagne.CAMPAGNA, {"automation": auto.name}))
