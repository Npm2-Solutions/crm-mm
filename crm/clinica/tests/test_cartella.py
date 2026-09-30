# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinical record on a real site: who reads it, and the trace of who did.

Its author reads it always; the medical director once it is signed; the other
practitioners only with the patient's consent to the health dossier. The front
desk knows a visit happened; manager, sales and marketing know nothing. Every read
from the CRM is in the access log, and the log is kept two years.
"""

import frappe
from frappe.tests import IntegrationTestCase

from crm.clinica import cartella, paziente, regole
from crm.moduli import consensi
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

DOC1 = "record.doctor1@example.com"
DOC2 = "record.doctor2@example.com"
DESK = "record.desk@example.com"
MANAGER = "record.manager@example.com"
DIRECTOR = "record.director@example.com"
SALES = "record.sales@example.com"
TUTTI = (DOC1, DOC2, DESK, MANAGER, DIRECTOR, SALES)


class RecordCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "clinica", "status": "Active"}])
		piano.save()
		livelli.dimentica_cache()
		utenti.sincronizza()
		for user in TUTTI:
			make_user(user)
		for user, livello in (
			(DOC1, "operatore"),
			(DOC2, "operatore"),
			(DESK, "segreteria"),
			(MANAGER, "manager"),
			(DIRECTOR, "direzione"),
			(SALES, "commerciale"),
		):
			utenti.assegna_livelli(user, [livello])
		consensi.assicura_tipi()
		self.anna = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Anna", "last_name": "Cartella"}
		).insert(ignore_permissions=True)
		# everybody works on Anna: the record's own rules are what is tested here
		for user in TUTTI:
			frappe.get_doc(
				{
					"doctype": "ToDo",
					"reference_type": "CRM Lead",
					"reference_name": self.anna.name,
					"allocated_to": user,
					"description": "Anna",
				}
			).insert(ignore_permissions=True)
		livelli.dimentica_cache()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def scrive(self, user=DOC1, **valori):
		self.come(user)
		valori.setdefault("content", "<p>Lombalgia, esercizi per due settimane.</p>")
		return cartella.save_record(self.anna.name, **valori)

	def legge(self, user, nome):
		self.come(user)
		return nome in [r["name"] for r in cartella.get_record(self.anna.name)["records"]]


class LaVisita(RecordCase):
	def test_la_prima_visita_fa_un_paziente(self):
		visita = self.scrive()
		scheda = frappe.db.get_value(
			"Clinic Patient", self.anna.name, ["rule", "recorded_by", "source_name"], as_dict=True
		)
		self.assertEqual(scheda.rule, regole.INFORMAZIONE_MEDICA.valore)
		self.assertEqual(scheda.recorded_by, DOC1)
		self.assertEqual(scheda.source_name, visita["name"])

	def test_la_prima_bozza_buttata_lascia_il_paziente(self):
		visita = self.scrive()
		cartella.delete_draft(visita["name"])
		# the card keeps the rule and the moment, and no longer points to the draft
		scheda = frappe.db.get_value(
			"Clinic Patient", self.anna.name, ["rule", "source_doctype", "source_name"], as_dict=True
		)
		self.assertEqual(
			(scheda.rule, scheda.source_doctype, scheda.source_name),
			(regole.INFORMAZIONE_MEDICA.valore, None, None),
		)

	def test_una_bozza_e_del_suo_autore(self):
		bozza = self.scrive()
		self.assertTrue(self.legge(DOC1, bozza["name"]))
		self.assertFalse(self.legge(DIRECTOR, bozza["name"]))
		self.assertFalse(self.legge(DOC2, bozza["name"]))

	def test_firmata_la_legge_la_direzione_e_i_colleghi_solo_col_dossier(self):
		firmata = self.scrive(sign=1)
		self.assertTrue(self.legge(DIRECTOR, firmata["name"]))
		self.assertFalse(self.legge(DOC2, firmata["name"]))
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, cartella.DOSSIER)
		self.assertTrue(self.legge(DOC2, firmata["name"]))
		frappe.set_user("Administrator")
		consensi.revoca(self.anna.name, cartella.DOSSIER)
		self.assertFalse(self.legge(DOC2, firmata["name"]))

	def test_solo_io_non_la_legge_nessun_altro(self):
		nota = self.scrive(sign=1, visibility="Only me", kind="Note")
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, cartella.DOSSIER)
		self.assertFalse(self.legge(DIRECTOR, nota["name"]))
		self.assertFalse(self.legge(DOC2, nota["name"]))
		self.assertTrue(self.legge(DOC1, nota["name"]))

	def test_firmata_non_si_riscrive_si_aggiunge(self):
		firmata = self.scrive(sign=1)
		with self.assertRaises(frappe.PermissionError):
			self.scrive(name=firmata["name"], content="<p>Riscritta</p>")
		aggiunta = self.scrive(addendum_to=firmata["name"], content="<p>Dolore ridotto.</p>", sign=1)
		self.assertEqual(aggiunta["addendum_to"], firmata["name"])
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc("Clinic Record", firmata["name"]).cancel()

	def test_gli_allegati_restano_privati(self):
		bozza = self.scrive()

		def allega(privato):
			return frappe.get_doc(
				{
					"doctype": "File",
					"file_name": "referto.txt",
					"content": "esame",
					"attached_to_doctype": "Clinic Record",
					"attached_to_name": bozza["name"],
					"is_private": privato,
				}
			).insert()

		with self.assertRaises(frappe.ValidationError):
			allega(0)
		self.assertTrue(allega(1).file_url.startswith("/private/"))

	def test_non_si_firma_una_visita_vuota(self):
		with self.assertRaises(frappe.ValidationError):
			self.scrive(content="<p> </p>", sign=1)

	def test_chi_non_cura_non_legge(self):
		self.scrive(sign=1)
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			cartella.get_record(self.anna.name)
		# the desk comes to add to the archive: no record, and no reading logged
		self.come(DESK)
		visto = cartella.get_record(self.anna.name)
		self.assertEqual((visto["records"], visto["can_read"], visto["can_archive"]), ([], False, True))
		# the manager comes for the access log: no record, and no reading logged
		self.come(MANAGER)
		visto = cartella.get_record(self.anna.name)
		self.assertEqual(visto["records"], [])
		self.assertFalse(visto["can_read"])
		self.assertTrue(visto["can_see_log"])
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			cartella.save_record(self.anna.name, content="<p>x</p>")


class IlRegistroDegliAccessi(RecordCase):
	def test_ogni_lettura_lascia_una_traccia(self):
		firmata = self.scrive(sign=1)
		prima = frappe.db.count(
			"View Log", {"reference_doctype": "Clinic Record", "reference_name": firmata["name"]}
		)
		self.legge(DIRECTOR, firmata["name"])
		dopo = frappe.db.count(
			"View Log", {"reference_doctype": "Clinic Record", "reference_name": firmata["name"]}
		)
		self.assertEqual(dopo, prima + 1)
		self.come(MANAGER)
		registro = cartella.access_log(self.anna.name)
		self.assertIn(DIRECTOR, [riga.viewed_by for riga in registro])
		self.come(DOC2)
		with self.assertRaises(frappe.PermissionError):
			cartella.access_log(self.anna.name)

	def test_si_tiene_due_anni(self):
		frappe.set_user("Administrator")
		impostazioni = frappe.get_single("Log Settings")
		impostazioni.set(
			"logs_to_clear", [r for r in impostazioni.logs_to_clear if r.ref_doctype != "View Log"]
		)
		impostazioni.append("logs_to_clear", {"ref_doctype": "View Log", "days": 180})
		impostazioni.save()
		riga = next(r for r in frappe.get_single("Log Settings").logs_to_clear if r.ref_doctype == "View Log")
		self.assertEqual(riga.days, cartella.GIORNI_REGISTRO)


class LaCronologia(RecordCase):
	def nodi(self, user):
		self.come(user)
		return cartella.visite_su("CRM Lead", self.anna.name)

	def test_chi_vede_cosa_nella_cronologia(self):
		firmata = self.scrive(sign=1)
		self.scrive(content="<p>bozza</p>")
		self.scrive(sign=1, visibility="Only me", content="<p>per me</p>")

		segreteria = self.nodi(DESK)
		self.assertEqual([n["name"] for n in segreteria], [firmata["name"]])
		self.assertTrue(segreteria[0]["data"]["locked"])
		self.assertTrue(self.nodi(DOC2)[0]["data"]["locked"])
		self.assertFalse(self.nodi(DIRECTOR)[0]["data"]["locked"])
		self.assertEqual(len(self.nodi(DOC1)), 3)
		self.assertEqual(self.nodi(SALES), [])
		self.assertEqual(self.nodi(MANAGER), [])

	def test_con_la_clinica_spenta_niente(self):
		self.scrive(sign=1)
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [])
		piano.save()
		livelli.dimentica_cache()
		self.assertEqual(self.nodi(DESK), [])
		self.assertFalse(paziente.clinica_accesa())
