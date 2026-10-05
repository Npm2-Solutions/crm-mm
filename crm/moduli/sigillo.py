# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's seal and the time stamp on the PDFs it keeps (design.md, "La
firma": "il sigillo del centro e la marca temporale", with pyHanko).

- **The seal** is a PAdES signature made with the centre's certificate, an
  organisation's seal the agency installs (a qualified electronic seal, eIDAS
  art. 35-36, or an advanced one). It goes on the signed form's PDF/A and on the
  visit's report: whoever holds the file can check that nothing changed since.
- **The time stamp** (RFC 3161) comes from the time-stamping authority the centre
  buys stamps from: when the document existed, whatever the server's clock says.
- **Never in the way**: without a certificate the PDF stays as it is, with its
  SHA-256; a stamp that does not come leaves the seal without it, and the
  register says so. A certificate that fails is written in the error log, and
  the document is kept unsealed rather than lost.
- **Sealed before the fingerprint**: the SHA-256 a record keeps is the sealed
  file's, so the fingerprint and the file always agree.
- The seal is invisible: no drawn box that a PDF/A would need fonts for; a PDF
  reader shows it in its signatures panel.
"""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from datetime import UTC, datetime

import frappe
from frappe import _
from frappe.utils import cint

IMPOSTAZIONI = "CRM Signature Settings"
CAMPO_FIRMA = "CentreSeal"


#: What the register writes next to "sealed" when the authority stamped the file.
CON_MARCA = "with a time stamp"


#: How a sealed file's description ends, as `Sigillato.descrizione` writes it in English
CON_MARCA = ", sealed by the centre with a time stamp"
SIGILLATO = ", sealed by the centre"
FIRMATO_DA = re.compile(r"^Signed by (?P<chi>.+) \(PAdES\)$")


def in_parole(conformita: str | None) -> str:
	"""A kept file's conformance as a screen says it, in the reader's language. What is
	stored stays as it was written, being evidence: the engine's words in English
	(«PDF/A-3b (structure verified)»), the seal's and a provider's in the language of
	whoever signed - English where the demo or a job wrote them."""
	if not conformita:
		return ""
	if conformita.endswith(CON_MARCA):
		return _("{0}, sealed by the centre with a time stamp").format(
			in_parole(conformita[: -len(CON_MARCA)])
		)
	if conformita.endswith(SIGILLATO):
		return _("{0}, sealed by the centre").format(in_parole(conformita[: -len(SIGILLATO)]))
	if firmato := FIRMATO_DA.match(conformita):
		return _("Signed by {0} (PAdES)").format(firmato.group("chi"))
	from crm.invoicing.engine import pdfa

	parole = {
		pdfa.Conformita.PDFA_3B: _("PDF/A-3b (structure verified)"),
		pdfa.Conformita.PDF_SEMPLICE: _("PDF (neutral metadata, not PDF/A)"),
		pdfa.Conformita.NON_VERIFICATO: _("PDF (not verified)"),
	}
	return parole.get(conformita, conformita)


@dataclass
class Sigillato:
	dati: bytes
	sigillo: bool = False
	marca: bool = False
	avviso: str | None = None

	@property
	def sha256(self) -> str:
		return hashlib.sha256(self.dati).hexdigest()

	def descrizione(self, conformita: str) -> str:
		"""What the kept file is: its structure, with the seal on it."""
		if not self.sigillo:
			return conformita
		from crm.invoicing.engine import pdfa

		if conformita == pdfa.Conformita.PDFA_3B:
			# the seal is an update added to the file: the structure is checked
			# again, on the bytes that are kept
			conformita = pdfa.verifica(self.dati).conformita
		if self.marca:
			return _("{0}, sealed by the centre with a time stamp").format(conformita)
		return _("{0}, sealed by the centre").format(conformita)

	def traccia(self, doctype: str, nome: str) -> None:
		"""The seal in the document's register: made, or why not."""
		from crm.moduli import traccia

		if self.sigillo:
			traccia.traccia(
				doctype,
				nome,
				"sealed",
				self.avviso or (CON_MARCA if self.marca else None),
				{"sha256": self.sha256, "timestamped": self.marca},
			)
		elif self.avviso:
			traccia.traccia(doctype, nome, "seal_failed", self.avviso)


def _impostazioni():
	return frappe.get_cached_doc(IMPOSTAZIONI)


def attivo(cfg=None) -> bool:
	cfg = cfg or _impostazioni()
	return bool(cint(cfg.get("seal_enabled")) and cfg.get("seal_certificate"))


def _certificato(cfg) -> bytes:
	nome = frappe.db.get_value("File", {"file_url": cfg.seal_certificate}, "name")
	if not nome:
		raise ValueError("The seal's certificate file is missing")
	return frappe.get_doc("File", nome).get_content(encodings=[])


def firmatario(cfg=None):
	"""The centre's signer, from its PKCS#12 certificate, read in memory: the key is
	never written anywhere but the private file the agency uploaded."""
	from pyhanko.sign import signers

	cfg = cfg or _impostazioni()
	contenuto = _certificato(cfg)
	parola = cfg.get_password("seal_password", raise_exception=False)
	try:
		return signers.SimpleSigner.load_pkcs12_data(
			contenuto if isinstance(contenuto, bytes) else contenuto.encode("latin-1"),
			other_certs=(),
			passphrase=parola.encode("utf-8") if parola else None,
		)
	except ValueError as errore:
		raise ValueError("The seal's certificate cannot be read: check the file and its password") from errore


def nome_breve(nome) -> str:
	"""A certificate's name as a person says it: who, and of which organisation."""
	valori = nome.native
	chi = valori.get("common_name") or valori.get("organization_name") or nome.human_friendly
	ente = valori.get("organization_name")
	return f"{chi} · {ente}" if ente and ente != chi else chi


def validita(firmatario) -> tuple[datetime, datetime]:
	periodo = firmatario.signing_cert["tbs_certificate"]["validity"]
	return periodo["not_before"].native, periodo["not_after"].native


def valido_ora(firmatario) -> bool:
	dal, al = validita(firmatario)
	return dal <= datetime.now(UTC) <= al


def marcatore(cfg=None):
	"""The time-stamping authority, if the centre has one. Never while the demo data
	are made: a form of the demo spends none of the stamps the centre buys."""
	from pyhanko.sign import timestamps

	from crm.demo import registro

	cfg = cfg or _impostazioni()
	if not cfg.get("tsa_url") or registro.raccolta() is not None:
		return None
	utente = cfg.get("tsa_username")
	parola = cfg.get_password("tsa_password", raise_exception=False) if utente else None
	return timestamps.HTTPTimeStamper(cfg.tsa_url, auth=(utente, parola) if utente else None, timeout=10)


def _firma(pdf: bytes, firmatario, marcatore_, motivo: str | None, luogo: str | None) -> bytes:
	from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
	from pyhanko.sign import fields, signers

	scrittore = IncrementalPdfFileWriter(io.BytesIO(pdf))
	metadati = signers.PdfSignatureMetadata(
		field_name=CAMPO_FIRMA,
		reason=motivo,
		location=luogo,
		md_algorithm="sha256",
		subfilter=fields.SigSeedSubFilter.PADES,
	)
	uscita = signers.sign_pdf(scrittore, metadati, signer=firmatario, timestamper=marcatore_)
	return uscita.getvalue()


def sigilla(pdf: bytes, motivo: str | None = None) -> Sigillato:
	"""The PDF with the centre's seal and, if the centre has an authority, its time
	stamp. Without a seal configured, the PDF as it came."""
	cfg = _impostazioni()
	if not attivo(cfg):
		return Sigillato(pdf)
	luogo = cfg.get("seal_location") or None
	try:
		chi = firmatario(cfg)
	except Exception:
		frappe.log_error(title="The centre's seal could not be read")
		return Sigillato(pdf, avviso="The seal's certificate cannot be read")
	if not valido_ora(chi):
		# a seal of an expired certificate reads as a broken one: none, and said so
		frappe.log_error(title="The centre's seal certificate is not valid today")
		return Sigillato(pdf, avviso="The seal's certificate is not valid today")
	try:
		tempo = marcatore(cfg)
	except Exception:
		tempo = None
	try:
		return Sigillato(_firma(pdf, chi, tempo, motivo, luogo), sigillo=True, marca=tempo is not None)
	except Exception:
		if tempo is None:
			frappe.log_error(title="The centre's seal failed")
			return Sigillato(pdf, avviso="The seal failed")
		frappe.log_error(title="The time stamp did not come")
	# the authority did not answer: sealed without the stamp, and said so
	try:
		return Sigillato(
			_firma(pdf, chi, None, motivo, luogo),
			sigillo=True,
			avviso="The time stamp did not come: sealed without it",
		)
	except Exception:
		frappe.log_error(title="The centre's seal failed")
		return Sigillato(pdf, avviso="The seal failed")


def verifica(pdf: bytes) -> list[dict]:
	"""The signatures in a PDF, and whether each still covers the document: for the
	evidence and for a test."""
	from pyhanko.pdf_utils.reader import PdfFileReader
	from pyhanko.sign.validation import validate_pdf_signature
	from pyhanko_certvalidator import ValidationContext

	lettore = PdfFileReader(io.BytesIO(pdf))
	esiti = []
	for firma in lettore.embedded_signatures:
		stato = validate_pdf_signature(firma, ValidationContext(allow_fetching=False))
		esiti.append(
			{
				"field": firma.field_name,
				"intact": bool(stato.intact),
				"covers_all": stato.coverage.name == "ENTIRE_FILE",
				"signer": stato.signing_cert.subject.human_friendly if stato.signing_cert else None,
				"timestamped": stato.timestamp_validity is not None,
			}
		)
	return esiti


@frappe.whitelist()
def get_seal_status() -> dict:
	"""The seal as the agency set it up: whose certificate, until when, and whether
	a time-stamping authority is set."""
	from crm.permissions import livelli

	livelli.verifica("tecnico.integrazioni")
	cfg = _impostazioni()
	stato = {"enabled": attivo(cfg), "tsa": bool(cfg.get("tsa_url"))}
	if cfg.get("seal_certificate"):
		try:
			chi = firmatario(cfg)
			certificato = chi.signing_cert
			dal, al = validita(chi)
			stato.update(
				{
					"subject": nome_breve(certificato.subject),
					"issuer": nome_breve(certificato.issuer),
					# self-signed: good for a test, not recognised by a PDF reader
					"self_signed": certificato.subject == certificato.issuer,
					"valid_from": dal.date().isoformat(),
					"valid_until": al.date().isoformat(),
					"days_left": (al - datetime.now(UTC)).days,
					"valid_now": valido_ora(chi),
				}
			)
		except Exception as errore:
			stato["error"] = (
				_(str(errore)) if isinstance(errore, ValueError) else _("The certificate cannot be read")
			)
	return stato


@frappe.whitelist(methods=["POST"])
def try_seal() -> dict:
	"""Seal a test page now: whether the certificate and the authority work."""
	from crm.moduli.pdf import pdf_da_html
	from crm.permissions import livelli

	livelli.verifica("tecnico.integrazioni")
	prova = pdf_da_html("<p>Test of the centre's seal</p>")
	esito = sigilla(prova, motivo="Test")
	return {
		"sealed": esito.sigillo,
		"timestamped": esito.marca,
		"notice": _(esito.avviso) if esito.avviso else None,
		"signatures": verifica(esito.dati) if esito.sigillo else [],
	}
