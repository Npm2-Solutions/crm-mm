# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Forms with health data, where the clinic is on.

A template marked "health data" is filled by the care team: the practitioner
signs it with the person and reads it; the front desk and sales never see it.
Signed, it makes the person a patient (rule 1), with the form as the source.
"""

import json

import frappe

from crm.clinica import regole
from crm.clinica.tests.test_paziente import ClinicCase
from crm.moduli import compilazioni, consensi, modelli
from crm.moduli.tests.test_compilazioni import tratto
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

DOC = "clinicforms.doctor@example.com"
DESK = "clinicforms.desk@example.com"

ANAMNESI = {
	"sections": [
		{
			"id": "storia",
			"title": "Storia",
			"fields": [
				{"id": "allergie", "type": "text", "label": "Allergie", "required": True},
				{"id": "firma", "type": "signature", "label": "Firma", "required": True},
			],
		}
	]
}


class ModuliClinici(ClinicCase):
	def setUp(self):
		super().setUp()
		consensi.assicura_tipi()
		utenti.sincronizza()
		for user, livello in ((DOC, "operatore"), (DESK, "segreteria")):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		# the practitioner cares for Mario: his record and forms are hers to see
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"reference_type": "CRM Lead",
				"reference_name": self.mario.name,
				"allocated_to": DOC,
				"description": "Mario",
			}
		).insert(ignore_permissions=True)
		modello = modelli.save_template(title="Anamnesi", schema=json.dumps(ANAMNESI), clinical=1)
		modelli.publish_template(modello["name"])
		self.anamnesi = modello["name"]
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def firma_dal_medico(self):
		self.come(DOC)
		nome = compilazioni.start_form(self.mario.name, self.anamnesi)["name"]
		return compilazioni.sign_form(
			nome, json.dumps({"allergie": "Nessuna"}), json.dumps({"firma": tratto()})
		)

	def test_firmato_fa_un_paziente(self):
		self.assertIsNone(self.scheda(self.mario))
		firmato = self.firma_dal_medico()
		self.assertTrue(firmato["clinical"])
		frappe.set_user("Administrator")
		scheda = self.scheda(self.mario)
		self.assertEqual(scheda.rule, regole.INFORMAZIONE_MEDICA.valore)
		self.assertEqual((scheda.source_doctype, scheda.source_name), (compilazioni.MODULO, firmato["name"]))

	def test_la_segreteria_non_lo_vede_e_non_lo_compila(self):
		nome = self.firma_dal_medico()["name"]
		self.come(DESK)
		persona = compilazioni.get_person_forms(self.mario.name)
		self.assertNotIn(nome, [f["name"] for f in persona["forms"]])
		self.assertNotIn(self.anamnesi, [t["name"] for t in persona["templates"]])
		with self.assertRaises(frappe.PermissionError):
			compilazioni.get_form(nome)
		with self.assertRaises(frappe.PermissionError):
			compilazioni.start_form(self.mario.name, self.anamnesi)

	def test_il_medico_lo_legge(self):
		nome = self.firma_dal_medico()["name"]
		self.come(DOC)
		self.assertEqual(compilazioni.get_form(nome)["answers"], {"allergie": "Nessuna"})
		self.assertIn(nome, frappe.get_list(compilazioni.MODULO, pluck="name"))
