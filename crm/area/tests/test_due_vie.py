# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The board both ways, on a site without the clinic.

Anna writes to the centre from the Messages of her area, maybe with a photo or a
PDF: the message is on her board, the file private with it. The desk and her
operator hear of it by her name only - never the words - and a second one before
they read adds to the same notification, never in place of other news of the
area. Opening the board reads it; the desk answers there and Anna reads the answer
in her area. Nothing written, a file too big or not a photo nor a PDF, the centre's
preview, somebody else's area: refused. Who does not read the board does not open
the file.
"""

import base64
import json

import frappe

from crm.area import anteprima, messaggi
from crm.area import messaggi_regole as R
from crm.area.tests.test_area import ANNA, DESK, OPERATORE, SALES, AreaCase
from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa


def un_pdf() -> bytes:
	import io

	from pypdf import PdfWriter

	scrittore = PdfWriter()
	scrittore.add_blank_page(width=200, height=200)
	uscita = io.BytesIO()
	scrittore.write(uscita)
	return uscita.getvalue()


PDF = un_pdf()


def come_url(contenuto: bytes, tipo: str = "application/pdf") -> str:
	return f"data:{tipo};base64," + base64.b64encode(contenuto).decode()


class DueVie(AreaCase):
	def scrive(self, **altro):
		return messaggi.send_message(self.anna.name, **altro)

	def avvisi(self, utente):
		return frappe.get_all(
			"CRM Notification",
			filters={"to_user": utente, "type": "Area", "reference_name": self.anna.name},
			fields=["sentence", "sentence_args", "count", "message", "notification_type_doc"],
		)

	def test_anna_scrive_e_la_segreteria_risponde(self):
		self.invita()
		self.entra()
		fatto = self.scrive(
			body="Posso portare la ricetta?", attachment=come_url(PDF), attachment_name="ricetta.pdf"
		)
		[mio] = fatto["messages"]
		self.assertTrue(mio["from_person"])
		self.assertEqual((mio["kind"], mio["attachment_name"]), (messaggi.DALLA_PERSONA, "ricetta.pdf"))
		self.assertFalse(mio["read_on"])
		# what she wrote is not news for her
		self.assertEqual(messaggi.da_leggere(self.anna.name), 0)

		frappe.set_user("Administrator")
		doc = frappe.get_doc(messaggi.MESSAGGIO, mio["name"])
		file = frappe.get_doc("File", {"file_url": doc.attachment})
		self.assertTrue(file.is_private)
		self.assertEqual(file.get_content(encodings=[]), PDF)

		# the desk and her operator hear of it by her name, never the words
		for utente in (DESK, OPERATORE):
			[avviso] = self.avvisi(utente)
			self.assertEqual(avviso.sentence, N.MESSAGGIO_AREA)
			self.assertEqual(json.loads(avviso.sentence_args), ["Anna Area"])
			self.assertFalse(avviso.message)
		# who does not read the board hears nothing, and does not open the file
		self.assertEqual(self.avvisi(SALES), [])
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			messaggi.attachment(doc.name)

		# a second one before they read adds to the same notification
		frappe.set_user(ANNA)
		self.scrive(body="E anche il referto")
		[avviso] = self.avvisi(DESK)
		self.assertEqual((avviso.sentence, avviso.count), (N.MESSAGGIO_AREA_MOLTI, 2))

		# the desk opens the board: read, and the file opens
		self.come(DESK)
		bacheca = messaggi.get_messages(self.anna.name)
		self.assertTrue(all(m["read_on"] for m in bacheca["messages"] if m["from_person"]))
		messaggi.attachment(doc.name)
		self.assertEqual(frappe.local.response.filecontent, PDF)
		self.assertEqual(frappe.local.response.filename, "ricetta.pdf")
		# and answers there: Anna reads it in her area
		messaggi.post_message(self.anna.name, "Sì, la porti pure.")
		frappe.set_user(ANNA)
		self.assertEqual(messaggi.da_leggere(self.anna.name), 1)
		righe = messaggi.area_messages(self.anna.name)["messages"]
		self.assertEqual(righe[0]["body"], "Sì, la porti pure.")
		self.assertFalse(righe[0]["from_person"])
		self.assertTrue(righe[1]["read_on"])

	def test_altre_novita_dell_area_restano(self):
		self.invita()
		self.entra()
		frappe.set_user("Administrator")
		avvisa(DESK, "Area", N.PREVENTIVO_FIRMATO, ["Anna Area"], riguarda=("CRM Lead", self.anna.name))
		frappe.set_user(ANNA)
		self.scrive(body="Grazie")
		frasi = sorted(a.sentence for a in self.avvisi(DESK))
		self.assertEqual(frasi, sorted([N.PREVENTIVO_FIRMATO, N.MESSAGGIO_AREA]))

	def test_cosa_si_rifiuta(self):
		self.invita()
		self.entra()
		for altro in (
			{"body": "   "},
			{"body": "x" * (R.MAX_TESTO + 1)},
			{"body": "Ecco", "attachment": come_url(b"MZ\x90\x00", "application/octet-stream")},
			{"body": "Ecco", "attachment": come_url(PDF + b"0" * R.MAX_ALLEGATO)},
			{"body": "Ecco", "attachment": "data:application/pdf;base64,!!"},
			{"body": "Ecco", "attachment": come_url(b"%PDF-1.4 rotto")},
		):
			with self.assertRaises(frappe.ValidationError, msg=str(altro)[:60]):
				self.scrive(**altro)
		with self.assertRaises(frappe.PermissionError):
			messaggi.send_message("CRM-LEAD-NOBODY", body="Ciao")
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count(messaggi.MESSAGGIO, {"lead": self.anna.name}), 0)

	def test_l_anteprima_non_scrive(self):
		self.come(DESK)
		anteprima.start(self.anna.name)
		with self.assertRaises(frappe.PermissionError):
			self.scrive(body="Ciao")
		anteprima.stop()

	def test_una_foto_senza_parole(self):
		import io

		from PIL import Image

		buffer = io.BytesIO()
		Image.new("RGB", (40, 30), (200, 30, 30)).save(buffer, format="PNG")
		self.invita()
		self.entra()
		[mio] = self.scrive(
			attachment=come_url(buffer.getvalue(), "image/png"), attachment_name="IMG_0042.png"
		)["messages"]
		self.assertEqual((mio["body"], mio["attachment_name"]), ("", "IMG_0042.png"))
