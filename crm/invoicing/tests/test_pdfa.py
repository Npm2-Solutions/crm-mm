# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The document the client keeps, and the check that says what it really is.

The point of these tests is not that a conversion runs: it is that the module
**never declares more than it produced**. Take the OutputIntent away and it has to
say so; take pypdf away and it has to hand back the file as rendered rather than
claim a conformance it did not reach.
"""

from __future__ import annotations

import io
import re
import unittest
from datetime import date

from crm.invoicing.engine import pdfa
from crm.invoicing.tests.base import UnitTestCase

try:
	import pypdf
	from PIL import Image

	LIBRERIE = True
except ImportError:  # pragma: no cover - a bench always has both
	LIBRERIE = False


def pdf_reso() -> bytes:
	"""A real rendered PDF to work on, without needing the print pipeline."""
	immagine = Image.new("RGB", (595, 842), "white")
	buffer = io.BytesIO()
	immagine.save(buffer, format="PDF")
	return buffer.getvalue()


class XmpTest(UnitTestCase):
	def test_dichiara_parte_e_conformanza(self):
		pacchetto = pdfa.xmp("2026/S/128", date(2026, 3, 10)).decode()
		self.assertIn("<pdfaid:part>3</pdfaid:part>", pacchetto)
		self.assertIn("<pdfaid:conformance>B</pdfaid:conformance>", pacchetto)

	def test_le_date_vengono_dal_documento_non_dall_orologio(self):
		pacchetto = pdfa.xmp("x", date(2026, 3, 10)).decode()
		self.assertIn("2026-03-10T00:00:00+00:00", pacchetto)
		self.assertEqual(pacchetto.count("2026-03-10T00:00:00+00:00"), 3)

	def test_i_metadati_restano_neutri(self):
		pacchetto = pdfa.xmp("2026/S/128", date(2026, 3, 10)).decode()
		self.assertIn("<pdf:Keywords></pdf:Keywords>", pacchetto)
		self.assertIn("<rdf:li></rdf:li>", pacchetto)
		# The producer never carries a version that would describe the stack.
		self.assertNotIn("wkhtmltopdf", pacchetto)

	def test_il_titolo_si_scappa(self):
		pacchetto = pdfa.xmp("A & B <x>", date(2026, 3, 10)).decode()
		self.assertIn("A &amp; B &lt;x&gt;", pacchetto)

	def test_la_data_pdf_non_porta_l_ora(self):
		self.assertEqual(pdfa.data_pdf(date(2026, 3, 10)), "D:20260310000000+00'00'")


class NomeFileTest(UnitTestCase):
	def test_il_nome_non_e_parlante(self):
		self.assertEqual(pdfa.nome_file_neutro("2026/S/128"), "documento_2026-S-128.pdf")

	def test_i_separatori_non_si_accumulano(self):
		self.assertEqual(pdfa.nome_file_neutro("2026 // S // 1"), "documento_2026-S-1.pdf")

	def test_un_numero_mancante_non_produce_un_nome_vuoto(self):
		self.assertEqual(pdfa.nome_file_neutro(""), "documento_senza-numero.pdf")


class VerificaTest(UnitTestCase):
	"""The scan runs on the exact bytes that get stored and hashed."""

	def test_un_file_senza_nulla_non_e_conforme(self):
		rapporto = pdfa.verifica_byte(b"%PDF-1.7\n%%EOF")
		self.assertFalse(rapporto.conforme)
		self.assertIn("no XMP metadata packet", rapporto.mancanze())
		self.assertIn("no OutputIntent: without one the file is not PDF/A", rapporto.mancanze())

	def test_la_cifratura_esclude_pdfa(self):
		rapporto = pdfa.verifica_byte(b"%PDF-1.7 /Encrypt 12 0 R")
		self.assertTrue(rapporto.cifrato)
		self.assertIn("the file is encrypted, and PDF/A does not allow encryption", rapporto.mancanze())

	def test_i_font_non_incorporati_si_notano(self):
		rapporto = pdfa.verifica_byte(b"%PDF-1.7 /BaseFont /Helvetica")
		self.assertFalse(rapporto.font_incorporati)
		self.assertTrue(any("not embedded" in m for m in rapporto.mancanze()))

	def test_un_file_senza_testo_non_ha_font_da_incorporare(self):
		rapporto = pdfa.verifica_byte(b"%PDF-1.7 no fonts here")
		self.assertTrue(rapporto.font_incorporati)

	def test_i_font_incorporati_passano(self):
		rapporto = pdfa.verifica_byte(b"%PDF-1.7 /BaseFont /ABCDEF+Inter /FontFile2 9 0 R")
		self.assertTrue(rapporto.font_incorporati)

	def test_un_file_che_non_e_un_pdf_lo_dice(self):
		rapporto = pdfa.verifica_byte(b"questo non e' un pdf")
		self.assertIn("the file does not start with a PDF header", rapporto.mancanze())

	def test_tutto_presente_significa_conforme(self):
		finto = b"%PDF-1.7 /Subtype /XML pdfaid:part /GTS_PDFA1 /DestOutputProfile /ID [<aa><aa>]"
		self.assertTrue(pdfa.verifica_byte(finto).conforme)


@unittest.skipUnless(LIBRERIE, "pypdf and Pillow are needed for the conversion")
class ConversioneTest(UnitTestCase):
	def test_un_pdf_reso_diventa_pdfa(self):
		risultato = pdfa.converti(pdf_reso(), titolo="2026/S/128", data_documento=date(2026, 3, 10))
		self.assertEqual(risultato.conformita, pdfa.Conformita.PDFA_3B)
		self.assertEqual(risultato.avvisi, [])
		self.assertTrue(risultato.rapporto.conforme)

	def test_la_conversione_e_deterministica(self):
		sorgente = pdf_reso()
		primo = pdfa.converti(sorgente, titolo="x", data_documento=date(2026, 3, 10))
		secondo = pdfa.converti(sorgente, titolo="x", data_documento=date(2026, 3, 10))
		self.assertEqual(primo.sha256, secondo.sha256)

	def test_un_titolo_diverso_da_un_file_diverso(self):
		sorgente = pdf_reso()
		primo = pdfa.converti(sorgente, titolo="2026/S/1", data_documento=date(2026, 3, 10))
		secondo = pdfa.converti(sorgente, titolo="2026/S/2", data_documento=date(2026, 3, 10))
		self.assertNotEqual(primo.sha256, secondo.sha256)

	def test_l_identificativo_viene_dal_contenuto(self):
		risultato = pdfa.converti(pdf_reso(), titolo="x", data_documento=date(2026, 3, 10))
		self.assertTrue(risultato.rapporto.identificativo)
		self.assertIn(b"/ID", risultato.dati)

	def test_l_xmp_resta_leggibile_in_chiaro(self):
		# PDF/A wants the metadata packet uncompressed: a reader has to find it
		# without running a decompressor.
		risultato = pdfa.converti(pdf_reso(), titolo="2026/S/128", data_documento=date(2026, 3, 10))
		self.assertIn(b"pdfaid:part", risultato.dati)
		self.assertIn(b"2026/S/128", risultato.dati)

	def test_le_date_non_portano_l_ora_di_generazione(self):
		# The bytes carry the date escaped as a PDF string, so it is read back through
		# the parser rather than matched against the raw file.
		from pypdf import PdfReader

		risultato = pdfa.converti(pdf_reso(), titolo="x", data_documento=date(2026, 3, 10))
		metadati = PdfReader(io.BytesIO(risultato.dati)).metadata
		self.assertEqual(metadati["/CreationDate"], pdfa.data_pdf(date(2026, 3, 10)))
		self.assertEqual(metadati["/ModDate"], metadati["/CreationDate"])

	def test_l_xml_viaggia_dentro_il_documento(self):
		risultato = pdfa.converti(
			pdf_reso(),
			titolo="2026/E/45",
			data_documento=date(2026, 3, 10),
			allegato_xml=("IT00743110157_00001.xml", b"<FatturaElettronica/>"),
		)
		self.assertEqual(risultato.rapporto.allegati, 1)
		self.assertIn(b"/AFRelationship", risultato.dati)
		from pypdf import PdfReader

		lettore = PdfReader(io.BytesIO(risultato.dati))
		self.assertEqual(list(lettore.attachments), ["IT00743110157_00001.xml"])

	def test_senza_profilo_icc_non_dichiara_pdfa(self):
		originale = pdfa.profilo_srgb
		pdfa.profilo_srgb = lambda: None
		try:
			risultato = pdfa.converti(pdf_reso(), titolo="x", data_documento=date(2026, 3, 10))
		finally:
			pdfa.profilo_srgb = originale
		self.assertEqual(risultato.conformita, pdfa.Conformita.PDF_SEMPLICE)
		self.assertTrue(any("ICC" in a for a in risultato.avvisi))

	def test_un_ingresso_illeggibile_non_solleva(self):
		risultato = pdfa.converti(b"non e' un pdf", titolo="x", data_documento=date(2026, 3, 10))
		self.assertEqual(risultato.conformita, pdfa.Conformita.NON_VERIFICATO)
		self.assertEqual(risultato.dati, b"non e' un pdf")
		self.assertTrue(risultato.avvisi)

	def test_il_profilo_srgb_e_un_icc_valido(self):
		profilo = pdfa.profilo_srgb()
		self.assertIsNotNone(profilo)
		# An ICC profile declares its own length in the first four bytes.
		self.assertEqual(int.from_bytes(profilo[:4], "big"), len(profilo))
		self.assertEqual(profilo[36:40], b"acsp")

	def test_il_pdf_prodotto_si_rilegge(self):
		risultato = pdfa.converti(pdf_reso(), titolo="x", data_documento=date(2026, 3, 10))
		from pypdf import PdfReader

		lettore = PdfReader(io.BytesIO(risultato.dati))
		self.assertEqual(lettore.metadata["/Producer"], pdfa.PRODUTTORE)
		self.assertEqual(lettore.metadata["/Author"], "")
		self.assertEqual(len(re.findall(rb"/Type\s*/Metadata", risultato.dati)), 1)
