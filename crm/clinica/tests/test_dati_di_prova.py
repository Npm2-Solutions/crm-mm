# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo data with the clinic on (doc 53): the CRM's demo and every one of its
checks - made through the product's rules, nobody written to, taken away leaving
the database as it was - with the clinic's share in it: the visits written in the
record and signed with their reports, the summary, the dentist's chart and care
plans, the diets and the exercises at home."""

import frappe

# the module, not the class: a class imported here would run here a second time
from crm.tests import test_demo_data
from crm.tests.test_demo_data import PIANO, RIGA, piano_cambiato


class TestDatiDiProvaConLaClinica(test_demo_data.TestDatiDiProva):
	# the medical director and the dentist join the team, with the dentist's services
	SQUADRA = test_demo_data.TestDatiDiProva.SQUADRA + 2
	SERVIZI = test_demo_data.TestDatiDiProva.SERVIZI + 6
	# the clinic's words: a client is a patient
	CLIENTE = "paziente"

	@classmethod
	def prima_della_demo(cls):
		super().prima_della_demo()
		# the clinic on as the plan's row says it, without what its switching on
		# brings by itself (its pipelines, its dashboard, the patients looked for
		# again): the demo makes what it needs, and the site stays as it was
		frappe.get_doc(
			{
				"doctype": RIGA,
				"parent": PIANO,
				"parenttype": PIANO,
				"parentfield": "modules",
				"idx": 1,
				"module": "clinica",
				"status": "Active",
			}
		).db_insert()
		piano_cambiato()

	def test_2b_the_clinic_writes_its_record(self):
		r = self.registrati
		for parte in ("clinica", "dentista", "diete"):
			self.assertIn(parte, self.esito["made"])
		squadra = r["User"]
		# the last weeks' visits written in the record by the demo's practitioners and
		# signed, each with its report: a PDF made once, filed among the documents
		visite = frappe.get_all(
			"Clinic Record",
			filters={"name": ["in", sorted(r["Clinic Record"])], "kind": "Visit", "docstatus": 1},
			fields=["name", "practitioner", "pdf_file"],
		)
		self.assertTrue(visite)
		self.assertTrue(all(visita.pdf_file and visita.practitioner in squadra for visita in visite))
		referti = frappe.get_all(
			"CRM Document",
			filters={"name": ["in", sorted(r["CRM Document"])], "document_type": "Report"},
			fields=["record", "file_hash", "clinical"],
		)
		self.assertEqual(sorted(referto.record for referto in referti), sorted(v.name for v in visite))
		self.assertTrue(all(referto.file_hash and referto.clinical for referto in referti))
		# what the sheets said, proposed for the summary and decided by a practitioner
		self.assertTrue(r.get("Clinic Summary Value"))
		# the dentist's first visits: the chart, and the care plan on its teeth
		self.assertTrue(r.get("Clinic Dental Chart"))
		self.assertTrue(
			frappe.db.count(
				"CRM Quote Item", {"parent": ["in", sorted(r["CRM Quote"])], "tooth": ["is", "set"]}
			)
		)
		# a diet or the exercises at home, written by a health professional: health data
		cliniche = frappe.get_all(
			"CRM Personal Plan",
			filters={
				"name": ["in", sorted(r["CRM Personal Plan"])],
				"plan_type": ["in", ["Meal plan", "Exchange diet", "Home exercises"]],
			},
			fields=["status", "clinical"],
		)
		self.assertTrue(cliniche)
		self.assertTrue(all(piano.status == "Published" and piano.clinical for piano in cliniche))
		# a care plan paid in instalments (doc 63): the deposit and the instalments due,
		# invoiced on their days by invoicing's part and paid; never the daily round's
		a_rate = frappe.get_all(
			"CRM Quote",
			filters={"name": ["in", sorted(r["CRM Quote"])], "payment": "Instalments"},
			pluck="name",
		)
		self.assertEqual(len(a_rate), 1)
		righe = frappe.get_all(
			"CRM Quote Instalment",
			filters={"parent": a_rate[0]},
			fields=["kind", "status", "invoice", "due_on"],
			order_by="idx",
		)
		self.assertEqual(len(righe), 11)
		pagate = [riga for riga in righe if riga.status == "Paid"]
		self.assertGreaterEqual(len(pagate), 2)
		self.assertTrue(all(riga.invoice for riga in pagate))
		self.assertEqual({riga.status for riga in righe if riga.due_on > frappe.utils.getdate()}, {"To pay"})
