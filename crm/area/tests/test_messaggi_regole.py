# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the person writes to the centre from their area: the words, one photo or
PDF told by its bytes, and how big."""

import base64
import unittest

from crm.area import messaggi_regole as R

PDF = b"%PDF-1.7\n..."
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 20
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 "
HEIC = b"\x00\x00\x00\x18ftypheic\x00\x00"


class IlFile(unittest.TestCase):
	def test_si_riconosce_dai_primi_byte(self):
		self.assertEqual(
			[R.tipo_del_file(f) for f in (PDF, PNG, JPG, WEBP, HEIC)], ["pdf", "png", "jpg", "webp", "heic"]
		)
		self.assertIsNone(R.tipo_del_file(b"GIF89a"))
		self.assertIsNone(R.tipo_del_file(b"<html>"))
		self.assertIsNone(R.tipo_del_file(None))

	def test_dal_browser(self):
		url = "data:application/pdf;base64," + base64.b64encode(PDF).decode()
		self.assertEqual(R.dal_data_url(url), PDF)
		self.assertIsNone(R.dal_data_url("data:application/pdf;base64,!!non!!"))
		self.assertIsNone(R.dal_data_url("data:text/plain,ciao"))
		self.assertIsNone(R.dal_data_url(None))

	def test_il_nome(self):
		self.assertEqual(R.nome_del_file("C:\\foto\\Ricetta 12.JPG", "jpg"), "Ricetta 12.jpg")
		self.assertEqual(R.nome_del_file("../../etc/passwd", "pdf"), "passwd.pdf")
		self.assertEqual(R.nome_del_file("referto.exe", "pdf"), "referto.pdf")
		self.assertEqual(R.nome_del_file("<script>.png", "png"), "script.png")
		self.assertEqual(R.nome_del_file("", "png"), "file.png")


class IlMessaggio(unittest.TestCase):
	def messaggi(self, *argomenti, **altro):
		return [p.messaggio for p in R.problemi(*argomenti, **altro)]

	def test_parole_o_un_file(self):
		self.assertEqual(self.messaggi("  ", None), ["Write the message or attach a file"])
		self.assertEqual(self.messaggi("Buongiorno", None), [])
		self.assertEqual(self.messaggi("", PDF), [])

	def test_quanto(self):
		self.assertEqual(
			self.messaggi("x" * (R.MAX_TESTO + 1), None), ["A message is at most {0} characters"]
		)
		self.assertEqual(self.messaggi("", PDF + b"0" * R.MAX_ALLEGATO), ["The file is larger than {0} MB"])

	def test_cosa(self):
		self.assertEqual(self.messaggi("Ecco", b"MZ\x90\x00"), ["Only a photo or a PDF can be attached"])
		self.assertEqual(
			self.messaggi("Ecco", None, c_era_un_file=True), ["The file could not be read: attach it again"]
		)
		problema = R.problemi("", PDF + b"0" * R.MAX_ALLEGATO)[0]
		self.assertEqual(problema.testo(), "The file is larger than 5 MB")
