# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A signed document carries what was written, and nothing else.

What a person types, and what their browser says it is, goes into the HTML the
PDF is made from. Printed as HTML, an answer like ``<a rel="attachment"
href="file:///...">`` would have WeasyPrint embed a file of the server in the
signed PDF, which the person then downloads; an image address would have the
server fetch it. So the templates escape what they print, and the renderer loads
nothing but what is written inside the page.
"""

import base64
import io
import json
import tempfile
import unittest

import frappe
from pypdf import PdfReader

from crm.moduli import compilazioni, modelli, pdf
from crm.moduli.tests.test_compilazioni import DESK, CompilazioniCase, tratto

TRAPPOLA = '<a rel="attachment" href="file:///etc/hostname">x</a><img src="file:///etc/hostname">'

CON_TESTO = {
	"sections": [
		{
			"id": "storia",
			"title": "Storia",
			"fields": [
				{"id": "note", "type": "text", "label": "Note", "multiline": True},
				{"id": "sign", "type": "signature", "label": "Firma", "required": True},
			],
		}
	]
}


def allegati(contenuto: bytes) -> list[str]:
	"""Every file the PDF carries: attached to the document, or to a page (where
	WeasyPrint puts the target of a ``rel="attachment"`` link)."""
	lettore = PdfReader(io.BytesIO(contenuto))
	trovati = list(lettore.attachments)
	for pagina in lettore.pages:
		for nota in pagina.get("/Annots") or []:
			nota = nota.get_object()
			if nota.get("/Subtype") == "/FileAttachment":
				trovati.append(str(nota["/FS"].get_object().get("/F")))
	return trovati


class IlPdfNonCaricaNiente(CompilazioniCase):
	def test_il_motore_legge_solo_la_pagina(self):
		# a picture on the server's disk, and the same picture written in the page
		immagine = base64.b64decode(tratto().split(",", 1)[1])
		with tempfile.NamedTemporaryFile(suffix=".png") as sul_disco:
			sul_disco.write(immagine)
			sul_disco.flush()
			pagina = (
				f'<p>ciao</p><a rel="attachment" href="file://{sul_disco.name}">x</a>'
				f'<img src="file://{sul_disco.name}"><img src="http://127.0.0.1:9/x.png">'
				f'<img src="{tratto()}">'
			)
			# what the renderer would do on its own: the server's file comes in
			from weasyprint import HTML

			da_solo = HTML(string=pagina).write_pdf()
			self.assertEqual(len(allegati(da_solo)), 1)
			reso = pdf.pdf_da_html(pagina)
		self.assertTrue(reso.startswith(b"%PDF"))
		# nothing of the server's comes in; what is written in the page does
		self.assertEqual(allegati(reso), [])
		self.assertEqual(len(PdfReader(io.BytesIO(reso)).pages[0].images), 1)

	def test_una_risposta_resta_testo(self):
		modello = self.pubblica(CON_TESTO, "Storia")
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, modello)["name"]
		firmato = compilazioni.sign_form(nome, json.dumps({"note": TRAPPOLA}), json.dumps({"sign": tratto()}))
		frappe.set_user("Administrator")
		contenuto = frappe.get_doc("File", {"file_url": firmato["pdf_file"]}).get_content(encodings=[])
		self.assertEqual(allegati(contenuto), [])
		# the answer is kept as it was typed, and printed as text
		self.assertEqual(firmato["answers"]["note"], TRAPPOLA)
		doc = frappe.get_doc(compilazioni.MODULO, nome)
		versione = frappe.get_doc(modelli.VERSIONE, doc.template_version)
		pagina = pdf.html(doc, versione)
		self.assertNotIn('<a rel="attachment"', pagina)
		self.assertIn("&lt;a rel=&#34;attachment&#34;", pagina)

	def test_il_browser_non_scrive_html(self):
		self.come(DESK)
		firmato = self.firma(compilazioni.start_form(self.giulia.name, self.privacy)["name"])
		frappe.set_user("Administrator")
		doc = frappe.get_doc(compilazioni.MODULO, firmato["name"])
		# what the browser sends about itself is the signer's to choose
		doc.signatures[0].user_agent = TRAPPOLA
		versione = frappe.get_doc(modelli.VERSIONE, doc.template_version)
		pagina = pdf.html(doc, versione)
		self.assertNotIn('<img src="file:', pagina)
		self.assertEqual(allegati(pdf.pdf_da_html(pagina)), [])


class UnaScalaDiceFinoDove(unittest.TestCase):
	"""An answer on a scale, on paper and in the record: its ends' numbers and words.
	A 3 between "None" and "Worst" did not say whether the scale went to 5 or to 10.
	The browser says it the same way (`answerInWords`)."""

	def test_gli_estremi_con_i_numeri(self):
		campo = {"type": "scale", "min_label": "None", "max_label": "Worst"}
		self.assertEqual(pdf.risposta_in_parole(campo, 3), "3 (0 None – 10 Worst)")
		self.assertEqual(pdf.risposta_in_parole({"type": "scale", "min": 1, "max": 5}, 4), "4 (1 – 5)")
		self.assertEqual(pdf.risposta_in_parole({"type": "scale", "min": 1.0, "max": 5.0}, 4), "4 (1 – 5)")
		self.assertEqual(pdf.risposta_in_parole(campo, None), "")
