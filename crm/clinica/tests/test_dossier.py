# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The dossier: who reads what the others wrote.

With the patient's consent the practitioners who have them in care read the whole
record - not the ones who do not. The medical director obscures an episode at the
patient's request, and then nobody else can tell it exists: not in the record, not
in the archive, not as a padlock, not in the summary. An entry can be for one's
own discipline. A practitioner opens the record of somebody not in their care
only writing why, for a day, and the access log shows it.
"""

import frappe
from frappe.utils import add_to_date, now_datetime

from crm.clinica import cartella, dossier, sintesi
from crm.clinica.tests.test_cartella import DESK, DIRECTOR, DOC1, DOC2, MANAGER, RecordCase
from crm.documenti import api as archivio
from crm.moduli import consensi, traccia
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

#: A practitioner of the centre who does not care for Anna.
DOC3 = "record.doctor3@example.com"


class DossierCase(RecordCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		make_user(DOC3)
		utenti.assegna_livelli(DOC3, ["operatore"])
		livelli.dimentica_cache()

	def consenso(self):
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, cartella.DOSSIER)

	def disciplina(self, user, qualifica):
		frappe.set_user("Administrator")
		frappe.get_doc(
			{
				"doctype": "CRM Service Provider",
				"provider_name": f"Provider {user}",
				"qualification": qualifica,
				"user": user,
			}
		).insert(ignore_permissions=True)

	def legge_voce(self, user, nome):
		self.come(user)
		return frappe.has_permission("Clinic Record", "read", doc=nome) and nome in frappe.get_list(
			"Clinic Record", pluck="name"
		)


class IlDossierVuoleLaCura(RecordCase):
	def test_col_consenso_solo_chi_ha_in_cura(self):
		frappe.set_user("Administrator")
		make_user(DOC3)
		utenti.assegna_livelli(DOC3, ["operatore"])
		firmata = self.scrive(sign=1)
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, cartella.DOSSIER)
		self.come(DOC2)
		self.assertIn(firmata["name"], frappe.get_list("Clinic Record", pluck="name"))
		# a practitioner who does not care for Anna reads nothing of hers, list or record
		self.come(DOC3)
		self.assertNotIn(firmata["name"], frappe.get_list("Clinic Record", pluck="name"))
		self.assertFalse(frappe.has_permission("Clinic Record", "read", doc=firmata["name"]))


class LOscuramento(DossierCase):
	def test_l_episodio_sparisce_per_gli_altri(self):
		visita = self.scrive(sign=1)
		aggiunta = self.scrive(addendum_to=visita["name"], content="<p>Meglio.</p>", sign=1)
		self.consenso()
		self.assertTrue(self.legge_voce(DOC2, visita["name"]))
		self.come(DIRECTOR)
		esito = dossier.obscure("Clinic Record", aggiunta["name"], "Richiesta del 30/09, su carta")
		# the whole episode: the visit, its addendum, their two reports in the archive
		self.assertEqual(esito["entries"], 4)
		for nome in (visita["name"], aggiunta["name"]):
			self.assertFalse(self.legge_voce(DOC2, nome))
			self.assertTrue(self.legge_voce(DOC1, nome))
			self.assertTrue(self.legge_voce(DIRECTOR, nome))
		self.come(DOC2)
		self.assertEqual(archivio.get_documents(self.anna.name)["documents"], [])
		self.assertEqual(cartella.get_record(self.anna.name)["records"], [])
		# not even as a padlock, for the desk or a colleague
		for user in (DESK, DOC2):
			self.come(user)
			self.assertEqual(cartella.visite_su("CRM Lead", self.anna.name), [], user)
		self.come(DOC1)
		self.assertEqual(len(cartella.visite_su("CRM Lead", self.anna.name)), 2)
		self.come(DIRECTOR)
		self.assertTrue(all(r["obscured"] for r in cartella.get_record(self.anna.name)["records"]))
		# and back, when the patient changes their mind
		dossier.reveal("Clinic Record", visita["name"])
		self.assertTrue(self.legge_voce(DOC2, visita["name"]))
		frappe.set_user("Administrator")
		self.assertEqual(
			[e.event for e in traccia.eventi("Clinic Record", visita["name"])], ["obscured", "revealed"]
		)

	def test_solo_la_direzione_e_solo_un_episodio_firmato(self):
		firmata = self.scrive(sign=1)
		bozza = self.scrive()
		self.come(DOC1)
		with self.assertRaises(frappe.PermissionError):
			dossier.obscure("Clinic Record", firmata["name"])
		# a draft is its author's alone: the director does not even see it
		self.come(DIRECTOR)
		with self.assertRaises(frappe.PermissionError):
			dossier.obscure("Clinic Record", bozza["name"])
		[referto] = archivio.get_documents(self.anna.name)["documents"]
		with self.assertRaises(frappe.ValidationError):
			dossier.obscure("CRM Document", referto["name"])

	def test_un_documento_si_oscura_da_solo(self):
		self.come(DOC1)
		allegato = frappe.get_doc(
			{"doctype": "File", "file_name": "hiv.txt", "is_private": 1, "content": "negativo"}
		).insert()
		documento = archivio.add_document(self.anna.name, allegato.name, "Esame", "Test result")
		self.consenso()
		self.come(DOC2)
		self.assertEqual(len(archivio.get_documents(self.anna.name)["documents"]), 1)
		self.come(DIRECTOR)
		dossier.obscure("CRM Document", documento["name"])
		self.come(DOC2)
		self.assertEqual(archivio.get_documents(self.anna.name)["documents"], [])
		self.come(DOC1)
		self.assertEqual(len(archivio.get_documents(self.anna.name)["documents"]), 1)

	def test_la_sintesi_non_tradisce_l_episodio(self):
		visita = self.scrive(sign=1)
		self.consenso()
		frappe.set_user("Administrator")
		frappe.get_doc(
			{
				"doctype": sintesi.DOCTYPE,
				"lead": self.anna.name,
				"key": "medications",
				"value": "Terapia riservata",
				"status": sintesi.CONFERMATO,
				"source_doctype": "Clinic Record",
				"source_name": visita["name"],
				"source_title": "Visita",
				"proposed_on": now_datetime(),
				"decided_by": DOC1,
				"decided_on": now_datetime(),
			}
		).insert(ignore_permissions=True)
		self.come(DIRECTOR)
		dossier.obscure("Clinic Record", visita["name"])

		def farmaci(user):
			self.come(user)
			[riga] = [r for r in sintesi.get_summary(self.anna.name)["lines"] if r["key"] == "medications"]
			return riga.get("value")

		self.assertIsNone(farmaci(DOC2))
		self.assertEqual(farmaci(DOC1), "Terapia riservata")
		self.assertEqual(farmaci(DIRECTOR), "Terapia riservata")


class LaDisciplina(DossierCase):
	def test_la_legge_chi_ha_la_stessa_disciplina(self):
		for user, qualifica in ((DOC1, "osteopata"), (DOC2, "osteopata"), (DOC3, "chiropratico")):
			self.disciplina(user, qualifica)
		frappe.set_user("Administrator")
		# DOC3 cares for Anna too, but is not an osteopath
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"reference_type": "CRM Lead",
				"reference_name": self.anna.name,
				"allocated_to": DOC3,
				"description": "Anna",
			}
		).insert(ignore_permissions=True)
		visita = self.scrive(sign=1, visibility="My discipline")
		self.assertEqual(visita["discipline"], "osteopata")
		self.consenso()
		self.assertTrue(self.legge_voce(DOC2, visita["name"]))
		self.assertFalse(self.legge_voce(DOC3, visita["name"]))
		self.assertTrue(self.legge_voce(DIRECTOR, visita["name"]))

	def test_senza_disciplina_non_si_sceglie(self):
		with self.assertRaises(frappe.ValidationError):
			self.scrive(visibility="My discipline")


class FuoriEquipe(DossierCase):
	def test_si_apre_scrivendo_il_motivo_per_un_giorno(self):
		firmata = self.scrive(sign=1)
		self.consenso()
		self.come(DOC3)
		self.assertFalse(frappe.has_permission("CRM Lead", "read", doc=self.anna.name))
		[trovata] = dossier.find_out_of_care("Anna Cartella")
		self.assertEqual((trovata["name"], trovata["in_care"]), (self.anna.name, False))
		self.assertEqual(dossier.find_out_of_care("Anna"), [])
		with self.assertRaises(frappe.ValidationError):
			dossier.open_out_of_care(self.anna.name, "urgente")
		dossier.open_out_of_care(self.anna.name, "Dolore toracico, la collega è assente")
		self.assertTrue(frappe.has_permission("CRM Lead", "read", doc=self.anna.name))
		self.assertTrue(self.legge_voce(DOC3, firmata["name"]))
		self.come(DOC3)
		self.assertEqual(
			cartella.get_record(self.anna.name)["out_of_care"]["reason"],
			"Dolore toracico, la collega è assente",
		)
		# the manager sees who opened it, and why
		self.come(MANAGER)
		[apertura] = [r for r in cartella.access_log(self.anna.name) if r.kind == "out_of_care"]
		self.assertEqual(
			(apertura.viewed_by, apertura.reason), (DOC3, "Dolore toracico, la collega è assente")
		)
		# a day later it is closed again
		frappe.set_user("Administrator")
		frappe.db.set_value(
			dossier.CONCESSIONE,
			{"user": DOC3, "lead": self.anna.name},
			"expires_on",
			add_to_date(now_datetime(), hours=-1),
		)
		self.come(DOC3)
		self.assertFalse(frappe.has_permission("CRM Lead", "read", doc=self.anna.name))

	def test_la_segreteria_non_apre_fuori_equipe(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			dossier.find_out_of_care("Anna Cartella")
		with self.assertRaises(frappe.PermissionError):
			dossier.open_out_of_care(self.anna.name, "Voglio vedere la cartella di Anna")
