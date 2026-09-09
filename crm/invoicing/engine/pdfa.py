r"""PDF/A: what the client keeps.

On the healthcare branch this is the only document there is - it does not travel
through the SdI, so nothing else exists to fall back on. It has to still be
readable, and still be provably the one that was handed over, in eight years.

Four properties, and the reason for each:

* **no remote resource.** A PDF that fetches its logo from a URL stops being
  readable the day that host goes away, and tells a third party every time somebody
  opens it. The print format embeds everything;
* **embedded fonts and a colour space that means something.** Without an
  OutputIntent a file is not PDF/A, and declaring it anyway would be a false
  declaration;
* **deterministic.** The dates and the file identifier are derived from the
  document, not from the clock, so regenerating from the same input gives the same
  bytes. That is what lets the stored SHA-256 prove something years later;
* **neutral metadata.** `Author`, `Title`, `Subject`, `Keywords` and `Producer` get
  filled in by whatever rendered the file - often with the template name, and the
  template name says what the practice specialises in.

Honesty about the conformance level: this module builds the **structure** of
PDF/A-3b and then **re-reads what it produced** to see what actually came out.
`verifica` is not a formality - it is why the invoice can record what was achieved
instead of what was hoped. Part 3 rather than 1 because the renderer emits modern
PDF with transparency, which part 1 forbids; and because part 3 is the one that
lets the FatturaPA XML travel inside the document that a human reads.

Formal certification is a validator's job (veraPDF): this says "the structure is
there", which is a weaker and truthful claim.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date

#: Declared producer: constant, neutral, no version that reveals the stack.
PRODUTTORE = "Frappe CRM"

PARTE_PDFA = 3
CONFORMANZA_PDFA = "B"


class Conformita:
	PDFA_3B = "PDF/A-3b (structure verified)"
	PDF_SEMPLICE = "PDF (neutral metadata, not PDF/A)"
	NON_VERIFICATO = "PDF (not verified)"


@dataclass
class RapportoPdf:
	"""What the produced bytes actually contain."""

	cifrato: bool = False
	xmp: bool = False
	pdfaid: bool = False
	output_intent: bool = False
	profilo_icc: bool = False
	font_incorporati: bool = True
	identificativo: bool = False
	allegati: int = 0
	note: list[str] = field(default_factory=list)

	@property
	def conforme(self) -> bool:
		return (
			not self.cifrato
			and self.xmp
			and self.pdfaid
			and self.output_intent
			and self.profilo_icc
			and self.font_incorporati
			and self.identificativo
		)

	@property
	def conformita(self) -> str:
		return Conformita.PDFA_3B if self.conforme else Conformita.PDF_SEMPLICE

	def mancanze(self) -> list[str]:
		"""What is missing, in the words of whoever has to fix it."""
		problemi: list[str] = []
		if self.cifrato:
			problemi.append("the file is encrypted, and PDF/A does not allow encryption")
		if not self.xmp:
			problemi.append("no XMP metadata packet")
		elif not self.pdfaid:
			problemi.append("the XMP packet does not declare pdfaid:part and pdfaid:conformance")
		if not self.output_intent:
			problemi.append("no OutputIntent: without one the file is not PDF/A")
		elif not self.profilo_icc:
			problemi.append("the OutputIntent carries no DestOutputProfile")
		if not self.font_incorporati:
			problemi.append(
				"fonts are referenced but not embedded: install the font on the server, or use one "
				"that is there"
			)
		if not self.identificativo:
			problemi.append("the trailer carries no /ID")
		return problemi + self.note


# --------------------------------------------------------------------- the XMP


def xmp(
	titolo: str, data_documento: date, parte: int = PARTE_PDFA, conformita: str = CONFORMANZA_PDFA
) -> bytes:
	"""A minimal, **neutral** XMP packet.

	No clinical reference, no template name, no tool version. The title is the
	document number and nothing else: a title of "Psychotherapy invoice" is a
	diagnosis written on the outside of the envelope.
	"""
	istante = f"{data_documento.isoformat()}T00:00:00+00:00"
	titolo = _testo_xml(titolo)
	return f"""<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">
   <pdfaid:part>{parte}</pdfaid:part>
   <pdfaid:conformance>{conformita}</pdfaid:conformance>
  </rdf:Description>
  <rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">
   <dc:title><rdf:Alt><rdf:li xml:lang="x-default">{titolo}</rdf:li></rdf:Alt></dc:title>
   <dc:creator><rdf:Seq><rdf:li></rdf:li></rdf:Seq></dc:creator>
   <dc:description><rdf:Alt><rdf:li xml:lang="x-default"></rdf:li></rdf:Alt></dc:description>
  </rdf:Description>
  <rdf:Description rdf:about="" xmlns:pdf="http://ns.adobe.com/pdf/1.3/">
   <pdf:Producer>{PRODUTTORE}</pdf:Producer>
   <pdf:Keywords></pdf:Keywords>
  </rdf:Description>
  <rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/">
   <xmp:CreatorTool>{PRODUTTORE}</xmp:CreatorTool>
   <xmp:CreateDate>{istante}</xmp:CreateDate>
   <xmp:ModifyDate>{istante}</xmp:ModifyDate>
   <xmp:MetadataDate>{istante}</xmp:MetadataDate>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>""".encode()


def _testo_xml(valore: str) -> str:
	return (valore or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def data_pdf(data_documento: date) -> str:
	"""A PDF date fixed to the document's day, with no time of day.

	The generation leaves no timestamp: two runs on the same input have to give the
	same bytes, or the stored hash proves nothing.
	"""
	return f"D:{data_documento.strftime('%Y%m%d')}000000+00'00'"


def identificativo(contenuto: bytes) -> bytes:
	"""The file identifier, derived from the content rather than from the clock."""
	return hashlib.sha256(contenuto).hexdigest()[:32].encode("ascii")


def nome_file_neutro(numero_documento: str) -> str:
	"""`documento_2026-S-128.pdf`.

	The file name is data too: `fattura_psicoterapia_rossi_marzo.pdf` tells the
	diagnosis to anyone who glances at a downloads folder.
	"""
	pulito = "".join(c if c.isalnum() else "-" for c in (numero_documento or ""))
	while "--" in pulito:
		pulito = pulito.replace("--", "-")
	return f"documento_{pulito.strip('-') or 'senza-numero'}.pdf"


# ------------------------------------------------------------------- the check

_MARCATORI = {
	"cifrato": re.compile(rb"/Encrypt[\s/<\[]"),
	"xmp": re.compile(rb"/Subtype\s*/XML|<x:xmpmeta"),
	"pdfaid": re.compile(rb"pdfaid:part"),
	"output_intent": re.compile(rb"/GTS_PDFA"),
	"profilo_icc": re.compile(rb"/DestOutputProfile"),
	"identificativo": re.compile(rb"/ID\s*\["),
	"font": re.compile(rb"/BaseFont"),
	"font_incorporato": re.compile(rb"/FontFile[23]?[\s/]"),
	"allegato": re.compile(rb"/Type\s*/EmbeddedFile"),
}


def verifica_byte(dati: bytes) -> RapportoPdf:
	"""Read the produced bytes back and say what is in them.

	Deliberately a scan and not a parse: it runs on the exact bytes that will be
	stored and hashed, with nothing between. Its one blind spot is a file whose
	objects sit inside object streams - what this module writes does not, and
	`verifica` prefers the object model when the library is there.
	"""
	rapporto = RapportoPdf()
	rapporto.cifrato = bool(_MARCATORI["cifrato"].search(dati))
	rapporto.xmp = bool(_MARCATORI["xmp"].search(dati))
	rapporto.pdfaid = bool(_MARCATORI["pdfaid"].search(dati))
	rapporto.output_intent = bool(_MARCATORI["output_intent"].search(dati))
	rapporto.profilo_icc = bool(_MARCATORI["profilo_icc"].search(dati))
	rapporto.identificativo = bool(_MARCATORI["identificativo"].search(dati))
	rapporto.allegati = len(_MARCATORI["allegato"].findall(dati))
	usa_font = bool(_MARCATORI["font"].search(dati))
	rapporto.font_incorporati = (not usa_font) or bool(_MARCATORI["font_incorporato"].search(dati))
	if not dati.startswith(b"%PDF-"):
		rapporto.note.append("the file does not start with a PDF header")
	return rapporto


def verifica(dati: bytes) -> RapportoPdf:
	"""Structural check, through the object model when it is available."""
	rapporto = verifica_byte(dati)
	try:
		import io

		from pypdf import PdfReader
	except ImportError:
		return rapporto

	try:
		lettore = PdfReader(io.BytesIO(dati))
		radice = lettore.trailer["/Root"]
		rapporto.cifrato = bool(lettore.is_encrypted)
		rapporto.xmp = "/Metadata" in radice
		intenti = radice.get("/OutputIntents") or []
		rapporto.output_intent = bool(intenti)
		rapporto.profilo_icc = any(
			"/DestOutputProfile" in (intento.get_object() or {}) for intento in intenti
		)
		rapporto.identificativo = bool(lettore.trailer.get("/ID"))
	except Exception as errore:
		rapporto.note.append(f"the file could not be re-read: {errore}")
	return rapporto


# ------------------------------------------------------------- the conversion


def profilo_srgb() -> bytes | None:
	"""The sRGB ICC profile for the OutputIntent.

	Generated with littleCMS through Pillow rather than shipped as an opaque binary
	in the repository: it is exactly what is needed and nobody has to trust a blob.
	Returns `None` when Pillow is not there, and the caller then declares a plain
	PDF instead of lying about conformance.
	"""
	try:
		from PIL import ImageCms
	except ImportError:
		return None
	try:
		return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
	except Exception:
		return None


@dataclass
class RisultatoPdf:
	dati: bytes
	sha256: str
	conformita: str
	rapporto: RapportoPdf
	avvisi: list[str] = field(default_factory=list)

	@property
	def byte(self) -> int:
		return len(self.dati)


def converti(
	dati: bytes,
	*,
	titolo: str,
	data_documento: date,
	allegato_xml: tuple[str, bytes] | None = None,
) -> RisultatoPdf:
	"""Turn a rendered PDF into PDF/A structure, and report what came out.

	`allegato_xml` embeds the FatturaPA file inside the document a human reads, so
	the readable rendering and the machine-readable original are one file. That is
	what part 3 is for; on the healthcare branch there is no XML and the parameter
	stays empty.

	It never raises on a conversion problem: an invoice that exists as a plain PDF
	is worth more than an exception at the counter. What it does instead is say so,
	in `conformita`.
	"""
	avvisi: list[str] = []
	try:
		import io

		from pypdf import PdfReader, PdfWriter
		from pypdf.generic import (
			ArrayObject,
			ByteStringObject,
			DecodedStreamObject,
			DictionaryObject,
			NameObject,
			NumberObject,
			TextStringObject,
		)
	except ImportError:
		avvisi.append("pypdf is not available: the file is stored as rendered")
		return RisultatoPdf(
			dati=dati,
			sha256=hashlib.sha256(dati).hexdigest(),
			conformita=Conformita.NON_VERIFICATO,
			rapporto=verifica_byte(dati),
			avvisi=avvisi,
		)

	icc = profilo_srgb()
	if icc is None:
		avvisi.append(
			"no ICC profile available: the file does not declare PDF/A, because without an "
			"OutputIntent it would not be one"
		)

	try:
		lettore = PdfReader(io.BytesIO(dati))
		scrittore = PdfWriter(clone_from=lettore)
		radice = scrittore.root_object

		# The XMP packet stays uncompressed - PDF/A requires it readable as it lies.
		scrittore.xmp_metadata = xmp(titolo, data_documento)
		flusso_xmp = radice["/Metadata"].get_object()
		flusso_xmp[NameObject("/Type")] = NameObject("/Metadata")
		flusso_xmp[NameObject("/Subtype")] = NameObject("/XML")

		if icc:
			profilo = DecodedStreamObject()
			profilo.set_data(icc)
			profilo[NameObject("/N")] = NumberObject(3)
			profilo[NameObject("/Alternate")] = NameObject("/DeviceRGB")
			riferimento = scrittore._add_object(profilo)
			radice[NameObject("/OutputIntents")] = ArrayObject(
				[
					DictionaryObject(
						{
							NameObject("/Type"): NameObject("/OutputIntent"),
							NameObject("/S"): NameObject("/GTS_PDFA1"),
							NameObject("/OutputConditionIdentifier"): TextStringObject("sRGB IEC61966-2.1"),
							NameObject("/OutputCondition"): TextStringObject("sRGB"),
							NameObject("/Info"): TextStringObject("sRGB IEC61966-2.1"),
							NameObject("/RegistryName"): TextStringObject("http://www.color.org"),
							NameObject("/DestOutputProfile"): riferimento,
						}
					)
				]
			)

		marca = data_pdf(data_documento)
		scrittore.add_metadata(
			{
				"/Title": titolo,
				"/Author": "",
				"/Subject": "",
				"/Keywords": "",
				"/Creator": PRODUTTORE,
				"/Producer": PRODUTTORE,
				"/CreationDate": marca,
				"/ModDate": marca,
			}
		)

		if allegato_xml:
			nome, contenuto = allegato_xml
			try:
				allegato = scrittore.add_attachment(nome, contenuto)
				# Part 3 does not just permit the attachment, it wants it declared: the
				# relationship says the file is another rendition of this document, and
				# the catalogue's /AF is where a reader looks for it.
				allegato.pdf_object[NameObject("/AFRelationship")] = NameObject("/Alternative")
				allegato.pdf_object[NameObject("/UF")] = allegato.pdf_object[NameObject("/F")]
				elenco = radice["/Names"]["/EmbeddedFiles"]["/Names"]
				radice[NameObject("/AF")] = ArrayObject([elenco[i] for i in range(1, len(elenco), 2)])
			except Exception as errore:
				avvisi.append(f"the XML could not be embedded: {errore}")

		uscita = io.BytesIO()
		scrittore.write(uscita)
		prodotto = uscita.getvalue()

		# The identifier is derived from the content, so the same input gives the
		# same file. It is written after the body is known, as a second pass.
		impronta = identificativo(prodotto)
		scrittore._ID = ArrayObject([ByteStringObject(impronta), ByteStringObject(impronta)])
		uscita = io.BytesIO()
		scrittore.write(uscita)
		prodotto = uscita.getvalue()
	except Exception as errore:
		avvisi.append(f"the PDF could not be converted ({errore}): it is stored as rendered")
		return RisultatoPdf(
			dati=dati,
			sha256=hashlib.sha256(dati).hexdigest(),
			conformita=Conformita.NON_VERIFICATO,
			rapporto=verifica_byte(dati),
			avvisi=avvisi,
		)

	rapporto = verifica(prodotto)
	avvisi.extend(rapporto.mancanze())
	return RisultatoPdf(
		dati=prodotto,
		sha256=hashlib.sha256(prodotto).hexdigest(),
		conformita=rapporto.conformita,
		rapporto=rapporto,
		avvisi=avvisi,
	)
