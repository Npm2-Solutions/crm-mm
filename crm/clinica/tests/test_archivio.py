# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Health data among a person's documents (`crm.documenti`), read by the record's rules.

A practitioner files a test, the front desk scans what the patient brings for a
practitioner, a signed visit files its own report, a file received on WhatsApp
goes among the documents and stops being public. Whom a document is for and
whoever added it read it, the medical director reads it, the colleagues with the
dossier; "only me" stays its practitioner's. A mistake goes the same day, later
only by the director, with its reason in the audit log. Every listing and every
download is in the access log.
"""

import hashlib

import frappe
from frappe.utils import add_days, now_datetime

from crm.clinica import cartella
from crm.clinica.tests.test_cartella import DESK, DIRECTOR, DOC1, DOC2, MANAGER, SALES, RecordCase
from crm.documenti import api as archivio
from crm.moduli import consensi, traccia


class ArchivioCase(RecordCase):
	def carica(self, user=DOC1, contenuto="Emoglobina 13,5", nome="esami.txt", privato=1):
		"""A file the user uploads, attached to nothing yet: what the dialog does first."""
		self.come(user)
		return frappe.get_doc(
			{"doctype": "File", "file_name": nome, "is_private": privato, "content": contenuto}
		).insert()

	def archivia(self, user=DOC1, **campi):
		allegato = self.carica(user, contenuto=campi.pop("contenuto", f"Esame di {user}"))
		campi.setdefault("title", "Esami del sangue")
		campi.setdefault("document_type", "Test result")
		return archivio.add_document(self.anna.name, allegato.name, **campi)

	def vede(self, user, nome):
		self.come(user)
		return nome in [d["name"] for d in archivio.get_documents(self.anna.name)["documents"]]


class LAggiunta(ArchivioCase):
	def test_il_medico_archivia_un_esame(self):
		allegato = self.carica(contenuto="Emoglobina 13,5")
		riga = archivio.add_document(
			self.anna.name,
			allegato.name,
			title="Esami del sangue",
			document_type="Test result",
			document_date="2026-09-20",
			source="Laboratorio Rossi",
		)
		self.assertEqual((riga["practitioner"], riga["document_type"]), (DOC1, "Test result"))
		self.assertEqual(riga["file_hash"], hashlib.sha256(b"Emoglobina 13,5").hexdigest())
		self.assertTrue(riga["file"].startswith("/private/"))
		frappe.set_user("Administrator")
		self.assertEqual(
			frappe.db.get_value("File", allegato.name, ["attached_to_doctype", "attached_to_name"]),
			(archivio.DOCTYPE, riga["name"]),
		)
		# a clinical document makes a patient, like the record
		self.assertEqual(frappe.db.get_value("Clinic Patient", self.anna.name, "source_name"), riga["name"])

	def test_la_segreteria_archivia_per_un_medico(self):
		with self.assertRaises(frappe.ValidationError):
			self.archivia(DESK)
		self.come(DESK)
		scelte = [p["value"] for p in archivio.get_choices()["practitioners"]]
		self.assertIn(DOC1, scelte)
		self.assertNotIn(DESK, scelte)
		riga = self.archivia(DESK, practitioner=DOC1, visibility="Only me")
		# only a practitioner keeps their own document to themselves
		self.assertEqual((riga["practitioner"], riga["visibility"]), (DOC1, "Care team"))
		self.assertTrue(self.vede(DESK, riga["name"]))
		self.assertTrue(self.vede(DOC1, riga["name"]))
		self.assertTrue(self.vede(DIRECTOR, riga["name"]))
		self.assertFalse(self.vede(DOC2, riga["name"]))
		# the desk sees what it added, not the rest of the archive
		altro = self.archivia(DOC1)
		self.assertFalse(self.vede(DESK, altro["name"]))
		# nor the record: the Clinic tab is not the desk's, the care plans are quotes
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			cartella.get_record(self.anna.name)

	def test_si_archivia_solo_un_file_appena_caricato_da_se(self):
		di_altri = self.carica(DOC2, contenuto="altro")
		self.come(DOC1)
		with self.assertRaises(frappe.ValidationError):
			archivio.add_document(self.anna.name, di_altri.name, "Esami", "Test result")
		pubblico = self.carica(DOC1, contenuto="pubblico", nome="pubblico.txt", privato=0)
		with self.assertRaises(frappe.ValidationError):
			archivio.add_document(self.anna.name, pubblico.name, "Esami", "Test result")
		riga = self.archivia(DOC1)
		gia_attaccato = frappe.db.get_value("File", {"attached_to_name": riga["name"]}, "name")
		with self.assertRaises(frappe.ValidationError):
			archivio.add_document(self.anna.name, gia_attaccato, "Esami", "Test result")
		# a report of the centre comes from a signed visit, not from an upload
		with self.assertRaises(frappe.ValidationError):
			self.archivia(DOC1, document_type="Report")

	def test_chi_non_cura_non_archivia(self):
		for user in (SALES, MANAGER):
			allegato = self.carica(user)
			with self.assertRaises(frappe.PermissionError, msg=user):
				archivio.add_document(self.anna.name, allegato.name, "Esami", "Test result")
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			archivio.get_documents(self.anna.name)
		# the manager reads the person's documents, never health data
		self.archivia(DOC1)
		self.assertFalse(self.vede(MANAGER, frappe.db.get_value(archivio.DOCTYPE, {"lead": self.anna.name})))
		self.come(MANAGER)
		self.assertNotIn("Test result", [t["value"] for t in archivio.get_choices()["types"]])


class ChiLoLegge(ArchivioCase):
	def test_col_dossier_lo_leggono_i_colleghi(self):
		riga = self.archivia(DOC1)
		self.assertFalse(self.vede(DOC2, riga["name"]))
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, cartella.DOSSIER)
		self.assertTrue(self.vede(DOC2, riga["name"]))
		# the file follows the document: Frappe serves it to whoever reads it
		self.come(DOC2)
		self.assertTrue(frappe.get_doc("File", {"attached_to_name": riga["name"]}).is_downloadable())
		frappe.set_user("Administrator")
		consensi.revoca(self.anna.name, cartella.DOSSIER)
		self.assertFalse(self.vede(DOC2, riga["name"]))
		self.come(DOC2)
		self.assertFalse(frappe.get_doc("File", {"attached_to_name": riga["name"]}).is_downloadable())

	def test_solo_io_resta_suo(self):
		riga = self.archivia(DOC1, visibility="Only me")
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, cartella.DOSSIER)
		self.assertFalse(self.vede(DIRECTOR, riga["name"]))
		self.assertFalse(self.vede(DOC2, riga["name"]))
		self.assertTrue(self.vede(DOC1, riga["name"]))


class IlReferto(ArchivioCase):
	def test_la_visita_firmata_va_in_archivio(self):
		firmata = self.scrive(sign=1)
		self.assertTrue(firmata["pdf_file"])
		self.come(DIRECTOR)
		[referto] = [d for d in archivio.get_documents(self.anna.name)["documents"] if d["record"]]
		self.assertEqual(
			(referto["record"], referto["document_type"], referto["practitioner"], referto["file"]),
			(firmata["name"], "Report", DOC1, firmata["pdf_file"]),
		)
		# the visit's own report: not put right, not taken away
		self.assertFalse(referto["can_edit"] or referto["can_remove"])
		self.come(DOC1)
		with self.assertRaises(frappe.PermissionError):
			archivio.remove_document(referto["name"], "per sbaglio")

	def test_una_nota_non_fa_referto(self):
		self.scrive(sign=1, kind="Note")
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists(archivio.DOCTYPE, {"lead": self.anna.name}))


class LaRimozione(ArchivioCase):
	def test_lo_stesso_giorno_chi_l_ha_aggiunto_con_un_motivo(self):
		riga = self.archivia(DOC1)
		with self.assertRaises(frappe.ValidationError):
			archivio.remove_document(riga["name"], " ")
		self.come(DOC2)
		with self.assertRaises(frappe.PermissionError):
			archivio.remove_document(riga["name"], "non è suo")
		self.come(DOC1)
		archivio.remove_document(riga["name"], "Persona sbagliata")
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists(archivio.DOCTYPE, riga["name"]))
		[evento] = traccia.eventi(archivio.DOCTYPE, riga["name"])
		self.assertEqual((evento.event, evento.detail, evento.user), ("removed", "Persona sbagliata", DOC1))

	def test_poi_solo_la_direzione(self):
		riga = self.archivia(DOC1)
		frappe.db.set_value(archivio.DOCTYPE, riga["name"], "added_on", add_days(now_datetime(), -1))
		self.come(DOC1)
		with self.assertRaises(frappe.PermissionError):
			archivio.remove_document(riga["name"], "Persona sbagliata")
		self.come(DIRECTOR)
		archivio.remove_document(riga["name"], "Persona sbagliata")
		self.assertFalse(frappe.db.exists(archivio.DOCTYPE, riga["name"]))


class IlRegistro(ArchivioCase):
	def test_elenco_e_scaricamenti_nel_registro(self):
		from frappe.core.doctype.access_log.access_log import make_access_log

		riga = self.archivia(DOC1)
		self.vede(DIRECTOR, riga["name"])
		allegato = frappe.db.get_value("File", {"attached_to_name": riga["name"]}, "name")
		# what Frappe writes when the private file is downloaded
		make_access_log(doctype="File", document=allegato, file_type="txt")
		self.come(MANAGER)
		registro = cartella.access_log(self.anna.name)
		del_direttore = {r.kind for r in registro if r.viewed_by == DIRECTOR}
		self.assertEqual(del_direttore, {"documents", "file"})

	def test_si_tengono_due_anni_anche_gli_scaricamenti(self):
		frappe.set_user("Administrator")
		impostazioni = frappe.get_single("Log Settings")
		impostazioni.set(
			"logs_to_clear", [r for r in impostazioni.logs_to_clear if r.ref_doctype != "Access Log"]
		)
		impostazioni.append("logs_to_clear", {"ref_doctype": "Access Log", "days": 30})
		impostazioni.save()
		riga = next(
			r for r in frappe.get_single("Log Settings").logs_to_clear if r.ref_doctype == "Access Log"
		)
		self.assertEqual(riga.days, cartella.GIORNI_REGISTRO)


class DallaConversazione(ArchivioCase):
	def ricevuto(self, contenuto=b"ricetta", persona=None):
		frappe.set_user("Administrator")
		persona = persona or self.anna.name
		messaggio = frappe.get_doc(
			{
				"doctype": archivio.MESSAGGIO,
				"type": "Incoming",
				"message_type": "Manual",
				"content_type": "document",
				"message": "",
				"message_id": frappe.generate_hash(length=20),
				"from": "393400000077",
				"reference_doctype": "CRM Lead",
				"reference_name": persona,
			}
		)
		messaggio.db_insert()
		# as frappe_whatsapp keeps what arrives: public, attached to the message
		file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"{frappe.generate_hash(length=10)}.txt",
				"attached_to_doctype": archivio.MESSAGGIO,
				"attached_to_name": messaggio.name,
				"attached_to_field": "attach",
				"content": contenuto,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(archivio.MESSAGGIO, messaggio.name, "attach", file.file_url)
		return messaggio.name, file.name

	def test_un_file_ricevuto_va_in_archivio_e_non_e_piu_pubblico(self):
		messaggio, originale = self.ricevuto(b"ricetta")
		self.come(DESK)
		riga = archivio.archive_from_message(
			messaggio, title="Ricetta", document_type="Prescription", practitioner=DOC1
		)
		self.assertEqual(riga["file_hash"], hashlib.sha256(b"ricetta").hexdigest())
		self.assertTrue(riga["file"].startswith("/private/"))
		frappe.set_user("Administrator")
		# the conversation keeps it, private, and points at where it is now
		file_url = frappe.db.get_value("File", originale, "file_url")
		self.assertTrue(file_url.startswith("/private/"))
		self.assertEqual(frappe.db.get_value(archivio.MESSAGGIO, messaggio, "attach"), file_url)

	def test_chi_non_legge_la_conversazione_non_archivia(self):
		# somebody the practitioner does not care for: their conversation is not theirs
		bruno = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Bruno", "last_name": "Altrove"}).insert(
			ignore_permissions=True
		)
		messaggio, _originale = self.ricevuto(persona=bruno.name)
		self.come(DOC1)
		with self.assertRaises(frappe.PermissionError):
			archivio.archive_from_message(messaggio, title="Ricetta", document_type="Prescription")
