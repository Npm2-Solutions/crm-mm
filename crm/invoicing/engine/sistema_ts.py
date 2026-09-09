r"""Sistema TS 730: the tracciato, its validation, and the file that carries it.

Healthcare expenses towards a natural person do not travel through the SdI - since
2026 they are forbidden to - so this is the channel that feeds the patient's
pre-filled tax return. It is 95% of the documents of a practice and it costs
nothing to transmit, which is the whole economic point of the design.

Two schemas, not one with a switch. The official XSDs of the kit say so without
ambiguity, and the difference is not cosmetic:

	                     synchronous                       attached file
	namespace            http://documentospesap730...      **none**
	root                 DocumentoSpesaRequest             precompilata
	proprietario         one per document                  **one per file**
	flagOperazione       absent - the SOAP operation says  **mandatory**
	element order        ... cfCittadino, voceSpesa, flag   ... flagOperazione, flag, voceSpesa

`xs:sequence` makes the order binding, so writing them in the same sequence
produces two files the Sistema TS refuses. Hence two distinct writers and not a
parameter.

Encryption: **RSA 1024, PKCS#1 v1.5**, Base64 of 172 characters. Two consequences
that change the data model:

* **the ciphertext is not stable** - it is randomised: never a key, an index or a
  deduplication field;
* **the ciphertext is not storable** - the certificate expires and is reissued.
  **Encrypt at send time, always.** In the database the codice fiscale sits in
  clear, protected by the ordinary access controls of the CRM.

And the trap that looks symmetric and is not:

	                     pincode    cfProprietario    cfCittadino
	SOAP synchronous     encrypted  **encrypted**     encrypted
	SOAP async, request  encrypted  **in clear**      -
	file inside the zip  -          **encrypted**     encrypted
"""

from __future__ import annotations

import base64
import io
import re
import zipfile
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from xml.etree import ElementTree as ET

from . import codice_fiscale as cf
from .codici import (
	FLAG_TIPO_SPESA_AMMESSO,
	NATURE_IVA_DOCUMENTO_COMMERCIALE,
	NATURE_IVA_FATTURA,
	SOGGETTI_CON_CODICE_PROPRIETARIO,
	SOGGETTI_PERSONA_FISICA,
	SOGGETTI_SENZA_TRACCIABILITA,
	TIPI_SPESA_SENZA_TRACCIABILITA,
	EsitoChiamata,
	OperazioneTS,
	SoggettoInviante,
	StrEnum,
	TipoDocumentoTS,
	TipoMessaggioTS,
	tipi_spesa_ammessi,
)

NAMESPACE_SINCRONO = "http://documentospesap730.sanita.finanze.it"

#: The alphabet `numDocumento` admits: no spaces, no `#`, no accents, no `:`.
NUM_DOCUMENTO_PATTERN = re.compile(r"^[A-Za-z0-9_./\-]{1,20}$")

DATA_MINIMA_EMISSIONE = date(2014, 1, 1)
DATA_MINIMA_PAGAMENTO = date(2015, 1, 1)

#: `importo`: at most five integer digits and two decimals, **always positive,
#: refunds included**.
IMPORTO_MASSIMO = Decimal("99999.99")
CENTESIMO = Decimal("0.01")

#: Size limit of the attached zip. Going over it is rejection 108.
LIMITE_ZIP_BYTE = 5 * 1024 * 1024

#: `nomeFileAllegato`: 6-60 basic Latin characters, ending in `.zip`.
NOME_FILE_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]{6,60}$")

#: Bytes that fit in one RSA-1024 PKCS#1 v1.5 block: 128 minus 11 of padding.
MAX_BYTE_IN_CHIARO = 117
LUNGHEZZA_BASE64_ATTESA = 172


def arrotonda(valore) -> Decimal:
	return Decimal(str(valore)).quantize(CENTESIMO, rounding=ROUND_HALF_UP)


class ErroreTS(ValueError):
	"""The tracciato cannot be built or sent as it stands."""

	def __init__(self, problemi: list[str]):
		self.problemi = problemi
		super().__init__("; ".join(problemi))


# ------------------------------------------------------------------- the model


@dataclass
class Proprietario:
	"""The `proprietario` section.

	Its shape changes between a professional and a facility. Not a preference: it
	is the difference between an accepted submission and error 109.
	"""

	cf_proprietario: str
	soggetto: str
	codice_regione: str | None = None
	codice_asl: str | None = None
	codice_ssa: str | None = None

	@property
	def e_persona_fisica(self) -> bool:
		return self.soggetto in SOGGETTI_PERSONA_FISICA

	@property
	def chiave(self) -> tuple[str, str | None, str | None, str | None]:
		"""Who is transmitting, for comparison.

		**One attached file admits one owner.** Two subjects in the same zip make a
		file the schema accepts but that attributes every expense to the first. The
		codice fiscale alone is not enough: the same professional can transmit in
		their own name and for a facility, and those are two distinct inventories.
		"""
		return (self.cf_proprietario, self.codice_regione, self.codice_asl, self.codice_ssa)

	@property
	def codice_proprietario(self) -> str | None:
		"""The code in the `xxx-yyy-zzzzzz` form, where it applies."""
		if self.e_persona_fisica:
			return None
		if not (self.codice_regione and self.codice_asl and self.codice_ssa):
			return None
		return f"{self.codice_regione}-{self.codice_asl}-{self.codice_ssa}"


@dataclass
class IdSpesa:
	"""Identifier of the expense document."""

	p_iva: str
	data_emissione: date
	num_documento: str
	#: Cash-register progressive. **For invoices it is always 1.**
	dispositivo: int = 1

	def chiave(self) -> str:
		return f"{self.p_iva}|{self.data_emissione.isoformat()}|{self.dispositivo}|{self.num_documento}"


@dataclass
class VoceSpesa:
	"""One line. `aliquotaIVA` and `naturaIVA` are **alternatives**."""

	tipo_spesa: str
	importo: Decimal
	#: `1` only with `TK` (emergency room) - `2` only with `SR` (intramoenia).
	flag_tipo_spesa: str | None = None
	aliquota_iva: Decimal | None = None
	natura_iva: str | None = None

	def __post_init__(self) -> None:
		self.importo = arrotonda(self.importo)
		if self.aliquota_iva is not None:
			self.aliquota_iva = arrotonda(self.aliquota_iva)


@dataclass
class DocumentoSpesa:
	"""A complete expense document, ready to validate and to send."""

	proprietario: Proprietario
	id_spesa: IdSpesa
	data_pagamento: date
	tipo_documento: str = TipoDocumentoTS.FATTURA
	voci: list[VoceSpesa] = field(default_factory=list)
	#: Codice fiscale of the **citizen**, in clear. It is encrypted only at send
	#: time, and it must be absent when `flag_opposizione` is set.
	cf_cittadino: str | None = None
	flag_opposizione: bool = False
	#: `1` when the payment precedes the issue - the prepaid package case.
	flag_pagamento_anticipato: bool = False
	#: `SI`/`NO`. `None` when the field is not mandatory for those expense types.
	pagamento_tracciato: bool | None = None
	#: Present **only in the attached file**: in the synchronous channel the
	#: operation is chosen by invoking a different SOAP operation.
	flag_operazione: str | None = None
	#: Identifier of the original document, when reporting a refund.
	id_rimborso: IdSpesa | None = None

	@property
	def anno_competenza(self) -> int:
		"""The year of competence is the one of the **payment date**, not the issue.

		This is the rule that derails prepaid packages and payments on account across
		a year end: a document issued in March 2026 and paid in December 2025 belongs
		to 2025.
		"""
		return self.data_pagamento.year

	@property
	def totale(self) -> Decimal:
		return arrotonda(sum((v.importo for v in self.voci), Decimal("0")))

	@property
	def tipi_spesa(self) -> set[str]:
		return {v.tipo_spesa for v in self.voci}


# -------------------------------------------------------------------- validation


@dataclass
class RisultatoValidazione:
	errori: list[str] = field(default_factory=list)
	avvisi: list[str] = field(default_factory=list)

	@property
	def valido(self) -> bool:
		return not self.errori

	def solleva_se_invalido(self) -> None:
		if self.errori:
			raise ErroreTS(self.errori)

	def unisci(self, altro: RisultatoValidazione) -> None:
		self.errori.extend(altro.errori)
		self.avvisi.extend(altro.avvisi)


def tracciabilita_obbligatoria(soggetto: str, tipo_spesa: str) -> bool:
	"""Is `pagamentoTracciato` mandatory for this pair?

	Mandatory since 1/1/2020 outside the listed expense types and outside public or
	SSN-accredited facilities. Without it the patient loses the 19% deduction, and
	nobody tells them.
	"""
	if soggetto in SOGGETTI_SENZA_TRACCIABILITA:
		return False
	return tipo_spesa not in TIPI_SPESA_SENZA_TRACCIABILITA


def _cf_soggetto_valido(valore: str | None) -> bool:
	"""A natural person's code (16 characters) or a legal person's (11 digits)."""
	valore = (valore or "").strip().upper()
	if len(valore) == 11 and valore.isdigit():
		return True
	return cf.valido(valore)


def valida_proprietario(proprietario: Proprietario) -> RisultatoValidazione:
	esito = RisultatoValidazione()
	soggetto = proprietario.soggetto

	if soggetto == SoggettoInviante.NON_SANITARIO:
		esito.errori.append(
			"the issuer is not a Sistema TS subject: this document does not belong in the tracciato"
		)
		return esito
	if not proprietario.cf_proprietario:
		esito.errori.append("cfProprietario is missing")
	elif not _cf_soggetto_valido(proprietario.cf_proprietario):
		esito.errori.append(f"cfProprietario is not valid: {proprietario.cf_proprietario!r}")

	terna = (proprietario.codice_regione, proprietario.codice_asl, proprietario.codice_ssa)
	if proprietario.e_persona_fisica:
		if any(terna):
			esito.errori.append(
				f"for subject {soggetto!r} codiceRegione, codiceAsl and codiceSSA are omitted: "
				"only cfProprietario is filled"
			)
	elif soggetto in SOGGETTI_CON_CODICE_PROPRIETARIO:
		if not all(terna):
			esito.errori.append(
				f"subject {soggetto!r} needs the full Codice Proprietario "
				"(codiceRegione-codiceAsl-codiceSSA), from the 'Abilitazione al Sistema TS' document"
			)
		else:
			if len(proprietario.codice_regione or "") != 3:
				esito.errori.append("codiceRegione must be three characters")
			if len(proprietario.codice_asl or "") != 3:
				esito.errori.append("codiceAsl must be three characters")
			if not 5 <= len(proprietario.codice_ssa or "") <= 6:
				esito.errori.append("codiceSSA must be five or six characters")
	return esito


def valida_documento(documento: DocumentoSpesa) -> RisultatoValidazione:
	"""Validate against the whole tracciato. It does not raise: it returns.

	Every rule here is a row that would otherwise be rejected in January, when
	fixing it costs a variation and a phone call. Validating **at issue time** means
	the error comes back while the patient is still at the desk.
	"""
	esito = valida_proprietario(documento.proprietario)
	soggetto = documento.proprietario.soggetto
	ammessi = tipi_spesa_ammessi(soggetto)
	id_spesa = documento.id_spesa

	# ------------------------------------------------------------- identifier
	if not cf.identificativo_ts_valido(id_spesa.p_iva):
		esito.errori.append(
			"pIva must be exactly eleven digits (professionals without a VAT number use the "
			"eleven-digit code issued by the Sistema TS)"
		)
	if id_spesa.data_emissione < DATA_MINIMA_EMISSIONE:
		esito.errori.append(f"dataEmissione cannot precede {DATA_MINIMA_EMISSIONE.isoformat()}")
	if not 1 <= id_spesa.dispositivo <= 999:
		esito.errori.append("dispositivo must be between 1 and 999")
	if documento.tipo_documento == TipoDocumentoTS.FATTURA and id_spesa.dispositivo != 1:
		esito.errori.append(
			"for invoices dispositivo is always 1: the cash-register progressive belongs to receipts"
		)
	if not NUM_DOCUMENTO_PATTERN.match(id_spesa.num_documento or ""):
		esito.errori.append(
			f"numDocumento {id_spesa.num_documento!r} is not admitted: at most 20 characters of the "
			r"alphabet [A-Za-z0-9_./\-] - no spaces, accents, '#' or ':'"
		)

	# ------------------------------------------------------------------ dates
	if documento.data_pagamento < DATA_MINIMA_PAGAMENTO:
		esito.errori.append(f"dataPagamento cannot precede {DATA_MINIMA_PAGAMENTO.isoformat()}")
	if documento.data_pagamento < id_spesa.data_emissione and not documento.flag_pagamento_anticipato:
		esito.errori.append(
			"dataPagamento precedes dataEmissione: flagPagamentoAnticipato=1 is required (the "
			"prepaid package case)"
		)
	if documento.flag_pagamento_anticipato and documento.data_pagamento > id_spesa.data_emissione:
		esito.avvisi.append(
			"flagPagamentoAnticipato is set but the payment follows the issue: check it, the flag "
			"is for the opposite case"
		)
	if documento.flag_operazione == OperazioneTS.RIMBORSO:
		if documento.data_pagamento != id_spesa.data_emissione:
			esito.errori.append("with flagOperazione=R the dataPagamento must equal the dataEmissione")
		if documento.id_rimborso is None:
			esito.errori.append(
				"with flagOperazione=R an idRimborso is required: the identifier of the original document"
			)

	# ------------------------------------------------------------- opposition
	# The document is transmitted either way, but without cfCittadino. Sending the
	# code with the flag set gets the row rejected.
	if documento.flag_opposizione:
		if documento.cf_cittadino:
			esito.errori.append(
				"with flagOpposizione=1 the cfCittadino field must be absent: the document is "
				"transmitted anyway, anonymously"
			)
	elif not documento.cf_cittadino:
		esito.errori.append(
			"cfCittadino is missing and no opposition was declared: the opposition is an explicit "
			"choice, not an empty field"
		)
	elif not cf.valido(documento.cf_cittadino):
		esito.errori.append(
			f"cfCittadino is not valid: {documento.cf_cittadino!r} (an omocodia code is valid, it "
			"is not an error)"
		)

	# ------------------------------------------------------------------ items
	if not documento.voci:
		esito.errori.append("the document has no expense item")

	natura_ammessa = (
		NATURE_IVA_FATTURA
		if documento.tipo_documento == TipoDocumentoTS.FATTURA
		else NATURE_IVA_DOCUMENTO_COMMERCIALE
	)
	natura_max_len = 4 if documento.tipo_documento == TipoDocumentoTS.FATTURA else 2

	serve_tracciabilita = False
	for indice, voce in enumerate(documento.voci, start=1):
		prefisso = f"item {indice}"
		if voce.tipo_spesa not in ammessi:
			esito.errori.append(
				f"{prefisso}: tipoSpesa {voce.tipo_spesa!r} is not admitted for subject {soggetto!r}. "
				f"Admitted: {', '.join(sorted(ammessi)) or 'none'}. The expense type follows the "
				"register of whoever issues, not the service"
			)
		if voce.flag_tipo_spesa is not None:
			atteso = FLAG_TIPO_SPESA_AMMESSO.get(voce.flag_tipo_spesa)
			if atteso is None:
				esito.errori.append(
					f"{prefisso}: flagTipoSpesa {voce.flag_tipo_spesa!r} is not foreseen (1 and 2 only)"
				)
			elif voce.tipo_spesa != atteso:
				esito.errori.append(
					f"{prefisso}: flagTipoSpesa={voce.flag_tipo_spesa} is only admitted with "
					f"tipoSpesa={atteso}, not with {voce.tipo_spesa!r}"
				)
		if voce.importo <= Decimal("0"):
			esito.errori.append(f"{prefisso}: importo must be positive, refunds included")
		elif voce.importo > IMPORTO_MASSIMO:
			esito.errori.append(f"{prefisso}: importo above the tracciato maximum ({IMPORTO_MASSIMO})")

		ha_aliquota = voce.aliquota_iva is not None
		ha_natura = bool(voce.natura_iva)
		if ha_aliquota and ha_natura:
			esito.errori.append(f"{prefisso}: aliquotaIVA and naturaIVA are alternatives, never together")
		elif not ha_aliquota and not ha_natura:
			esito.errori.append(f"{prefisso}: either aliquotaIVA or naturaIVA is required")
		elif ha_natura:
			natura = voce.natura_iva or ""
			if len(natura) > natura_max_len:
				esito.errori.append(
					f"{prefisso}: naturaIVA {natura!r} is too long for tipoDocumento="
					f"{documento.tipo_documento} (max {natura_max_len} characters)"
				)
			elif natura not in natura_ammessa:
				esito.errori.append(
					f"{prefisso}: naturaIVA {natura!r} is not admitted for tipoDocumento="
					f"{documento.tipo_documento}"
				)

		if tracciabilita_obbligatoria(soggetto, voce.tipo_spesa):
			serve_tracciabilita = True

	# -------------------------------------------------------- traced payment
	if serve_tracciabilita:
		if documento.pagamento_tracciato is None:
			esito.errori.append("pagamentoTracciato is mandatory for these expense types (since 1/1/2020)")
		elif documento.pagamento_tracciato is False:
			esito.avvisi.append(
				"payment not traced: the patient loses the 19% deduction. Watch mixed payments - if "
				"any part is in cash the document is reported as not traced"
			)
	elif documento.pagamento_tracciato is not None:
		esito.avvisi.append("pagamentoTracciato is filled but not required for these expense types")

	return esito


valida = valida_documento


# -------------------------------------------------------------------- encryption


class Cifratore:
	"""Encrypts tracciato fields with the public key of the current certificate.

	Built once per submission, not once per process: if the kit is updated while
	the service runs, the encryptor has to be rebuilt.

	`cryptography` is imported lazily so the rest of this module - the model, the
	validation, the XML - stays usable with nothing installed. Validation is what
	runs at issue time; encryption only runs at send time.
	"""

	__slots__ = ("_chiave", "scadenza")

	def __init__(self, chiave_pubblica, scadenza: date | None = None):
		self._chiave = chiave_pubblica
		self.scadenza = scadenza

	@classmethod
	def da_certificato(cls, pem_o_der: bytes) -> Cifratore:
		"""Load `SanitelCF.cer` - the certificate shipped with the official kit."""
		from cryptography import x509
		from cryptography.hazmat.primitives.serialization import Encoding

		try:
			certificato = x509.load_der_x509_certificate(pem_o_der)
		except ValueError:
			certificato = x509.load_pem_x509_certificate(pem_o_der)
		scadenza = certificato.not_valid_after_utc.date()
		if scadenza < date.today():
			# Every submission fails with code 002 once the certificate has expired,
			# and the failure is silent until somebody reads the response.
			raise ErroreTS(
				[
					f"the Sistema TS certificate expired on {scadenza.isoformat()}: download the "
					"current kit before submitting, every submission would fail with code 002"
				]
			)
		del Encoding
		return cls(certificato.public_key(), scadenza)

	def cifra(self, valore: str) -> str:
		from cryptography.hazmat.primitives.asymmetric import padding

		grezzo = (valore or "").strip().upper().encode("ascii")
		if not grezzo:
			raise ErroreTS(["nothing to encrypt: the field is empty"])
		if len(grezzo) > MAX_BYTE_IN_CHIARO:
			raise ErroreTS([f"the value exceeds {MAX_BYTE_IN_CHIARO} bytes: RSA 1024 cannot carry it"])
		cifrato = self._chiave.encrypt(grezzo, padding.PKCS1v15())
		return base64.b64encode(cifrato).decode("ascii")

	def cifra_opzionale(self, valore: str | None) -> str | None:
		return self.cifra(valore) if valore else None


class CifratoreFittizio(Cifratore):
	"""A stand-in for tests and for `export` mode dry runs.

	It produces a string of the right shape and **says so**: `NONCIFRATO` at the
	front, so a file built with it can never be mistaken for one that is ready to
	send.
	"""

	def __init__(self):
		super().__init__(None, None)

	def cifra(self, valore: str) -> str:
		grezzo = f"NONCIFRATO:{(valore or '').strip().upper()}".encode()
		return base64.b64encode(grezzo).decode("ascii")


# --------------------------------------------------------------------------- XML


def _el(genitore, nome: str, testo: str | None = None, ns: str | None = None):
	figlio = ET.SubElement(genitore, f"{{{ns}}}{nome}" if ns else nome)
	if testo is not None:
		figlio.text = testo
	return figlio


def formatta_importo(valore: Decimal) -> str:
	"""At most five integer digits and two decimals, **always positive**."""
	return f"{abs(Decimal(valore)):.2f}"


def scrivi_proprietario(
	genitore,
	proprietario: Proprietario,
	cf_proprietario_serializzato: str,
	ns: str | None = None,
	nome_elemento: str = "Proprietario",
):
	"""Write the owner section.

	`cf_proprietario_serializzato` arrives already encrypted **or** in clear
	depending on the channel: that is the asymmetric trap, and the decision does
	**not** live here.
	"""
	nodo = _el(genitore, nome_elemento, ns=ns)
	if not proprietario.e_persona_fisica:
		_el(nodo, "codiceRegione", proprietario.codice_regione, ns)
		_el(nodo, "codiceAsl", proprietario.codice_asl, ns)
		_el(nodo, "codiceSSA", proprietario.codice_ssa, ns)
	_el(nodo, "cfProprietario", cf_proprietario_serializzato, ns)
	return nodo


def scrivi_id_spesa(genitore, id_spesa: IdSpesa, nome_elemento: str = "idSpesa", ns: str | None = None):
	nodo = _el(genitore, nome_elemento, ns=ns)
	_el(nodo, "pIva", id_spesa.p_iva, ns)
	_el(nodo, "dataEmissione", id_spesa.data_emissione.isoformat(), ns)
	# `dispositivo` and `numDocumento` live **inside** `numDocumentoFiscale`: they
	# are the document number, not two fields sitting next to the VAT number.
	numero = _el(nodo, "numDocumentoFiscale", ns=ns)
	_el(numero, "dispositivo", str(id_spesa.dispositivo), ns)
	_el(numero, "numDocumento", id_spesa.num_documento, ns)
	return nodo


def scrivi_voce(genitore, voce: VoceSpesa, ns: str | None = None):
	nodo = _el(genitore, "voceSpesa", ns=ns)
	_el(nodo, "tipoSpesa", voce.tipo_spesa, ns)
	if voce.flag_tipo_spesa:
		_el(nodo, "flagTipoSpesa", voce.flag_tipo_spesa, ns)
	_el(nodo, "importo", formatta_importo(voce.importo), ns)
	# Alternatives, never together: the validation already guarantees it.
	if voce.aliquota_iva is not None:
		_el(nodo, "aliquotaIVA", f"{voce.aliquota_iva:.2f}", ns)
	elif voce.natura_iva:
		_el(nodo, "naturaIVA", voce.natura_iva, ns)
	return nodo


def scrivi_documento_sincrono(
	genitore,
	documento: DocumentoSpesa,
	cf_cittadino_cifrato: str | None,
	nome_elemento: str,
	ns: str | None = NAMESPACE_SINCRONO,
):
	"""The document as `DocumentoSpesa730pSchema.xsd` wants it.

	Order imposed by the schema's `xs:sequence`:

		idSpesa, dataPagamento, flagPagamentoAnticipato?, cfCittadino?,
		voceSpesa+, pagamentoTracciato?, tipoDocumento?, flagOpposizione?

	Here `voceSpesa` comes **before** the three closing flags, which is the
	opposite of the attached file. There is no `flagOperazione`: the operation is
	chosen by the SOAP operation being invoked.
	"""
	nodo = _el(genitore, nome_elemento, ns=ns)
	scrivi_id_spesa(nodo, documento.id_spesa, "idSpesa", ns)
	_el(nodo, "dataPagamento", documento.data_pagamento.isoformat(), ns)
	if documento.flag_pagamento_anticipato:
		_el(nodo, "flagPagamentoAnticipato", "1", ns)
	# With flagOpposizione=1 the code is **not** written: sending it rejects the row.
	if not documento.flag_opposizione and cf_cittadino_cifrato:
		_el(nodo, "cfCittadino", cf_cittadino_cifrato, ns)
	for voce in documento.voci:
		scrivi_voce(nodo, voce, ns)
	if documento.pagamento_tracciato is not None:
		_el(nodo, "pagamentoTracciato", "SI" if documento.pagamento_tracciato else "NO", ns)
	_el(nodo, "tipoDocumento", str(documento.tipo_documento), ns)
	_el(nodo, "flagOpposizione", "1" if documento.flag_opposizione else "0", ns)
	return nodo


def scrivi_documento_allegato(genitore, documento: DocumentoSpesa, cf_cittadino_cifrato: str | None):
	"""The document as `730_precompilata.xsd` wants it.

	Order imposed by the schema's `xs:sequence`, **different from the synchronous
	one**:

		idSpesa, idRimborso?, dataPagamento, flagPagamentoAnticipato?,
		flagOperazione, cfCittadino?, pagamentoTracciato?, tipoDocumento?,
		flagOpposizione?, voceSpesa+

	`flagOperazione` is mandatory and appears **only here**: in the attached file
	there is no SOAP operation to say whether this is an insert or a variation. And
	no namespace: the schema declares none.
	"""
	nodo = _el(genitore, "documentoSpesa")
	scrivi_id_spesa(nodo, documento.id_spesa, "idSpesa", None)
	if documento.id_rimborso is not None:
		scrivi_id_spesa(nodo, documento.id_rimborso, "idRimborso", None)
	_el(nodo, "dataPagamento", documento.data_pagamento.isoformat())
	if documento.flag_pagamento_anticipato:
		_el(nodo, "flagPagamentoAnticipato", "1")
	_el(nodo, "flagOperazione", str(documento.flag_operazione or OperazioneTS.INSERIMENTO))
	if not documento.flag_opposizione and cf_cittadino_cifrato:
		_el(nodo, "cfCittadino", cf_cittadino_cifrato)
	if documento.pagamento_tracciato is not None:
		_el(nodo, "pagamentoTracciato", "SI" if documento.pagamento_tracciato else "NO")
	_el(nodo, "tipoDocumento", str(documento.tipo_documento))
	_el(nodo, "flagOpposizione", "1" if documento.flag_opposizione else "0")
	for voce in documento.voci:
		scrivi_voce(nodo, voce, None)
	return nodo


def costruisci_file_allegato(documenti: list[DocumentoSpesa], cifratore: Cifratore) -> bytes:
	"""Build the summary XML (schema `730_precompilata.xsd`).

	Three things the schema imposes that nobody guesses:

	* **no namespace.** The schema declares no `targetNamespace`: the `precompilata`
	  root and every child are written bare;
	* **one `proprietario` per file**, not one per document. A batch is one subject's
	  submission, and the schema takes that for granted;
	* `flagOperazione` **mandatory** on every document.

	Inside the file **both** codici fiscali are encrypted.
	"""
	if not documenti:
		raise ErroreTS(["nothing to send: an empty zip is rejection 103"])

	proprietari = {d.proprietario.chiave for d in documenti}
	if len(proprietari) > 1:
		raise ErroreTS(
			[
				"the attached file admits one owner, and these documents carry "
				f"{len(proprietari)}: they have to be split into separate zips"
			]
		)

	radice = ET.Element("precompilata")
	scrivi_proprietario(
		radice,
		documenti[0].proprietario,
		cifratore.cifra(documenti[0].proprietario.cf_proprietario),
		None,
		nome_elemento="proprietario",
	)
	for documento in documenti:
		cf_cittadino = (
			None if documento.flag_opposizione else cifratore.cifra_opzionale(documento.cf_cittadino)
		)
		scrivi_documento_allegato(radice, documento, cf_cittadino)
	corpo = ET.tostring(radice, encoding="unicode")
	return f'<?xml version="1.0" encoding="UTF-8"?>{corpo}'.encode()


# ------------------------------------------------------------------ zip and split


def nome_file_valido(nome: str) -> bool:
	return bool(nome) and nome.endswith(".zip") and bool(NOME_FILE_PATTERN.match(nome))


def nome_file(riferimento: str, anno: int, parte: int = 1, parti: int = 1) -> str:
	"""Build an always-conformant attachment name.

	The name must not be descriptive: it carries a technical identifier, not the
	name of the practice and certainly not of a patient.
	"""
	base = re.sub(r"[^A-Za-z0-9]", "", riferimento or "")[:20] or "EMITTENTE"
	candidato = f"TS730_{base}_{anno}_{parte:02d}di{parti:02d}.zip"
	if len(candidato) > 60:
		candidato = f"TS730_{anno}_{parte:02d}di{parti:02d}.zip"
	return candidato


def crea_zip(nome_interno: str, contenuto: bytes) -> bytes:
	"""Compress the XML. Maximum deflate: every byte saved is one more document."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archivio:
		# Fixed timestamp: the zip has to be reproducible, or two exports of the same
		# batch hash differently and the reconciliation does not line up.
		info = zipfile.ZipInfo(nome_interno, date_time=(1980, 1, 1, 0, 0, 0))
		info.compress_type = zipfile.ZIP_DEFLATED
		info.external_attr = 0o644 << 16
		archivio.writestr(info, contenuto)
	return buffer.getvalue()


@dataclass
class ParteBatch:
	"""One part of the batch: a single zip, under the limit."""

	parte: int
	parti_totali: int
	documenti: list[DocumentoSpesa]
	xml: bytes
	zip_bytes: bytes
	nome_file: str

	@property
	def dimensione(self) -> int:
		return len(self.zip_bytes)


def _dividi(
	documenti: list[DocumentoSpesa], cifratore: Cifratore, limite: int, nome_interno: str
) -> list[tuple[list[DocumentoSpesa], bytes, bytes]]:
	xml = costruisci_file_allegato(documenti, cifratore)
	archivio = crea_zip(nome_interno, xml)
	if len(archivio) <= limite or len(documenti) == 1:
		if len(archivio) > limite:
			raise ErroreTS(
				["a single document produces a zip above 5 MB: that is anomalous data, not a batch problem"]
			)
		return [(documenti, xml, archivio)]
	meta = len(documenti) // 2
	return _dividi(documenti[:meta], cifratore, limite, nome_interno) + _dividi(
		documenti[meta:], cifratore, limite, nome_interno
	)


def prepara_batch(
	documenti: list[DocumentoSpesa],
	cifratore: Cifratore,
	riferimento: str,
	anno: int | None = None,
	limite: int = LIMITE_ZIP_BYTE,
) -> list[ParteBatch]:
	"""Prepare one or more zips, each under the 5 MB limit.

	Compression is not linear in the number of documents, so it is not estimated:
	it is compressed and measured. The split is by bisection, which keeps the number
	of parts minimal without ever going over.
	"""
	if not documenti:
		return []
	anno = anno or documenti[0].anno_competenza
	nome_interno = f"TS730_{anno}.xml"
	pezzi = _dividi(list(documenti), cifratore, limite, nome_interno)
	totale = len(pezzi)
	parti: list[ParteBatch] = []
	for indice, (gruppo, xml, archivio) in enumerate(pezzi, start=1):
		parti.append(
			ParteBatch(
				parte=indice,
				parti_totali=totale,
				documenti=gruppo,
				xml=xml,
				zip_bytes=archivio,
				nome_file=nome_file(riferimento, anno, indice, totale),
			)
		)
	return parti


# ------------------------------------------------------------------- deadlines


def scadenza_invio(anno: int, veterinario: bool = False) -> date:
	"""When the year's expenses have to be with the Sistema TS.

	31 January of the following year for everybody, **mid-March for vets**, who have
	their own deadline and therefore their own batch. Merging the two is how a vet
	practice discovers in February that it is late.
	"""
	return date(anno + 1, 3, 16) if veterinario else date(anno + 1, 1, 31)


def giorni_alla_scadenza(anno: int, oggi: date | None = None, veterinario: bool = False) -> int:
	return (scadenza_invio(anno, veterinario) - (oggi or date.today())).days


# ------------------------------------------------------------------- channels

HOST_TEST = "invioSS730pTest.sanita.finanze.it"
HOST_PRODUZIONE = "invioSS730p.sanita.finanze.it"

SERVIZIO_SINCRONO = "DocumentoSpesa730pWeb/DocumentoSpesa730pPort"
SERVIZIO_ASINCRONO = "InvioTelematicoSS730pMtomWeb/InvioTelematicoSS730pMtomPort"


class Canale(StrEnum):
	"""The three ways in.

	Picking the wrong family of endpoints **does not give a readable error**: it
	gives 401, or "user not recognised". So the channel is configuration, not a
	parameter somebody passes by hand.

		sistema_ts   /DocumentoSpesa730pWeb/...   professionals and facilities   pincode encrypted
		enti         /enti/...                    regions and public bodies      pincode encrypted
		entratel     /entrate/...                 tax intermediaries             pincode in clear

	The endpoints do not publish their WSDL and are not callable from a browser.
	"""

	SISTEMA_TS = "sistema_ts"
	ENTI = "enti"
	ENTRATEL = "entratel"


class Ambiente(StrEnum):
	TEST = "test"
	PRODUZIONE = "produzione"


PREFISSO_CANALE: dict[str, str] = {
	Canale.SISTEMA_TS: "",
	Canale.ENTI: "enti/",
	Canale.ENTRATEL: "entrate/",
}

#: On the Entratel channel the pincode travels **in clear** - it is the
#: intermediary's, not the practice's. Everywhere else it is encrypted.
PINCODE_IN_CHIARO: frozenset[str] = frozenset({Canale.ENTRATEL})


@dataclass(frozen=True)
class Destinazione:
	canale: str
	ambiente: str

	@property
	def host(self) -> str:
		return HOST_TEST if self.ambiente == Ambiente.TEST else HOST_PRODUZIONE

	@property
	def pincode_cifrato(self) -> bool:
		return self.canale not in PINCODE_IN_CHIARO

	def _url(self, servizio: str) -> str:
		return f"https://{self.host}/{PREFISSO_CANALE[self.canale]}{servizio}"

	@property
	def url_sincrono(self) -> str:
		return self._url(SERVIZIO_SINCRONO)

	@property
	def url_asincrono(self) -> str:
		return self._url(SERVIZIO_ASINCRONO)


def destinazione(canale: str, ambiente: str = Ambiente.TEST) -> Destinazione:
	return Destinazione(Canale(canale), Ambiente(ambiente))


def canale_per_modalita(modalita: str) -> str:
	"""The base channel for the practice's own credentials, `/entrate/` for an
	intermediary. The two are not interchangeable, and getting it wrong gives 401."""
	return Canale.ENTRATEL if modalita == "intermediario" else Canale.SISTEMA_TS


# ------------------------------------------------------------ synchronous SOAP

NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"


class Operazione(StrEnum):
	"""The four operations of the synchronous service.

	The operation is **not** expressed with `flagOperazione` here: it is chosen by
	invoking a different SOAP operation.
	"""

	INSERIMENTO = "Inserimento"
	VARIAZIONE = "Variazione"
	RIMBORSO = "Rimborso"
	CANCELLAZIONE = "Cancellazione"


OPERAZIONE_DA_FLAG: dict[str, str] = {
	OperazioneTS.INSERIMENTO: Operazione.INSERIMENTO,
	OperazioneTS.VARIAZIONE: Operazione.VARIAZIONE,
	OperazioneTS.RIMBORSO: Operazione.RIMBORSO,
	OperazioneTS.CANCELLAZIONE: Operazione.CANCELLAZIONE,
}

#: Operations that carry only the identifier, not the document body.
OPERAZIONI_SOLO_IDENTIFICATIVO: frozenset[str] = frozenset({Operazione.CANCELLAZIONE})

#: The document wrapper changes name with the operation. Not an oddity to
#: normalise: it is what `DocumentoSpesa730pSchema.xsd` declares, and a different
#: name is not recognised.
WRAPPER_DOCUMENTO: dict[str, str] = {
	Operazione.INSERIMENTO: "idInserimentoDocumentoFiscale",
	Operazione.VARIAZIONE: "idVariazioneDocumentoFiscale",
	Operazione.RIMBORSO: "DocumentoSpesa",
	Operazione.CANCELLAZIONE: "idCancellazioneDocumentoFiscale",
}

#: In a refund and a cancellation the bare identifier gets an element of its own,
#: beside the document (refund) or instead of it (cancellation).
WRAPPER_IDENTIFICATIVO: dict[str, str] = {
	Operazione.RIMBORSO: "idRimborsoDocumentoFiscale",
	Operazione.CANCELLAZIONE: "idCancellazioneDocumentoFiscale",
}


@dataclass
class Credenziali:
	"""Access credentials.

	They are **the practice's**, not ours. In `intermediario` mode they are the
	accountant's Entratel credentials instead, and the pincode travels in clear.
	"""

	utente: str
	password: str
	pincode: str
	#: On the Entratel channel: `codicefiscale-sedetelematica`, e.g. `07874631000-000`.
	opzionale1: str | None = None
	opzionale2: str | None = None
	opzionale3: str | None = None


def costruisci_busta(
	documento: DocumentoSpesa,
	credenziali: Credenziali,
	destinazione: Destinazione,
	cifratore: Cifratore,
	operazione: str = Operazione.INSERIMENTO,
) -> bytes:
	"""Build the SOAP 1.1 document/literal envelope for one operation.

	All three encryption rules apply here, and they are not symmetric:

	* `pincode` - encrypted, **except** on the `/entrate/` channel;
	* `cfProprietario` - encrypted;
	* `cfCittadino` - encrypted, and absent when there is an opposition.
	"""
	operazione = Operazione(operazione)
	ET.register_namespace("soapenv", NS_SOAP)
	ET.register_namespace("ts", NAMESPACE_SINCRONO)

	busta = ET.Element(f"{{{NS_SOAP}}}Envelope")
	ET.SubElement(busta, f"{{{NS_SOAP}}}Header")
	corpo = ET.SubElement(busta, f"{{{NS_SOAP}}}Body")
	# `inserimentoDocumentoSpesaRequest`, lowercase initial: it is the name the
	# schema declares, and with a capital the service does not recognise the root.
	radice = f"{operazione.value[0].lower()}{operazione.value[1:]}DocumentoSpesaRequest"
	richiesta = ET.SubElement(corpo, f"{{{NAMESPACE_SINCRONO}}}{radice}")

	def campo(nome: str, valore: str | None) -> None:
		if valore in (None, ""):
			return
		_el(richiesta, nome, valore, NAMESPACE_SINCRONO)

	# The order is the schema's `xs:sequence`: the three optionals **before** the
	# pincode.
	campo("opzionale1", credenziali.opzionale1)
	campo("opzionale2", credenziali.opzionale2)
	campo("opzionale3", credenziali.opzionale3)
	campo(
		"pincode",
		cifratore.cifra(credenziali.pincode) if destinazione.pincode_cifrato else credenziali.pincode,
	)

	scrivi_proprietario(
		richiesta,
		documento.proprietario,
		cifratore.cifra(documento.proprietario.cf_proprietario),
		NAMESPACE_SINCRONO,
	)

	if operazione in WRAPPER_IDENTIFICATIVO:
		identificativo = documento.id_rimborso or documento.id_spesa
		scrivi_id_spesa(richiesta, identificativo, WRAPPER_IDENTIFICATIVO[operazione], NAMESPACE_SINCRONO)

	if operazione not in OPERAZIONI_SOLO_IDENTIFICATIVO:
		cf_cittadino = (
			None if documento.flag_opposizione else cifratore.cifra_opzionale(documento.cf_cittadino)
		)
		scrivi_documento_sincrono(
			richiesta,
			documento,
			cf_cittadino,
			WRAPPER_DOCUMENTO[operazione],
			NAMESPACE_SINCRONO,
		)

	corpo_xml = ET.tostring(busta, encoding="unicode")
	return f'<?xml version="1.0" encoding="UTF-8"?>{corpo_xml}'.encode()


def soap_action(operazione: str) -> str:
	"""The operation's SOAPAction, in the form the kit's WSDL declares.

	It is not a URL: it is `inserimento.documentospesap730.sanita.finanze.it` - the
	operation name in lowercase, a dot, the service domain.
	"""
	dominio = NAMESPACE_SINCRONO.rstrip("/").removeprefix("http://")
	return f"{Operazione(operazione).value.lower()}.{dominio}"


# ---------------------------------------------------------------- the response

#: The protocol is a string of **seventeen digits**.
PROTOCOLLO_PATTERN = re.compile(r"^\d{17}$")


@dataclass(frozen=True)
class Messaggio:
	tipo: str
	codice: str
	descrizione: str

	@property
	def scartante(self) -> bool:
		return self.tipo == TipoMessaggioTS.ERRORE


@dataclass
class Esito:
	"""The outcome of one call."""

	esito_chiamata: str | None = None
	protocollo: str | None = None
	messaggi: list[Messaggio] = field(default_factory=list)
	fault: str | None = None

	@property
	def accolto(self) -> bool:
		"""Accepted, with or without remarks, and with a protocol."""
		if self.fault:
			return False
		if self.esito_chiamata not in (
			EsitoChiamata.ACCOLTO,
			EsitoChiamata.ACCOLTO_CON_SEGNALAZIONI,
		):
			return False
		return bool(self.protocollo)

	@property
	def errori(self) -> list[Messaggio]:
		return [m for m in self.messaggi if m.scartante]

	@property
	def codici_errore(self) -> list[str]:
		return [m.codice for m in self.errori]

	@property
	def protocollo_valido(self) -> bool:
		return bool(self.protocollo and PROTOCOLLO_PATTERN.match(self.protocollo))

	def riassunto(self) -> str:
		"""A sentence for whoever is at the desk, not for a developer."""
		if self.fault:
			return f"The Sistema TS answered with a SOAP fault: {self.fault}"
		if self.accolto:
			testo = f"Accepted, protocol {self.protocollo}"
			avvisi = [m for m in self.messaggi if m.tipo == TipoMessaggioTS.WARNING]
			if avvisi:
				testo += f" (with {len(avvisi)} remark(s))"
			return testo
		if self.errori:
			from .codici import descrivi_esito

			return " - ".join(descrivi_esito(m.codice) for m in self.errori)
		return "Not accepted by the Sistema TS, with no diagnostic message"


def _tutti(radice, nome: str) -> list:
	"""Every element with this local name, whatever namespace it carries.

	The parsing is deliberately namespace-agnostic. The service's namespaces are not
	published with the specification and differ between test and production; a
	parser that insists on them breaks at the first deploy, and breaks silently.
	"""
	return radice.findall(f".//{{*}}{nome}")


def _primo_testo(radice, *nomi: str) -> str | None:
	for nome in nomi:
		for nodo in _tutti(radice, nome):
			valore = (nodo.text or "").strip()
			if valore:
				return valore
	return None


def analizza_risposta(corpo: bytes) -> Esito:
	"""Read the SOAP response of a submission."""
	esito = Esito()
	try:
		radice = ET.fromstring(corpo)
	except ET.ParseError as exc:
		esito.fault = f"the response is not parseable as XML: {exc}"
		return esito

	fault = _tutti(radice, "Fault")
	if fault:
		stringa = _primo_testo(fault[0], "faultstring", "Reason", "Text")
		codice = _primo_testo(fault[0], "faultcode", "Value")
		esito.fault = " ".join(x for x in (codice, stringa) if x) or "SOAP Fault"
		return esito

	esito.esito_chiamata = _primo_testo(radice, "esitoChiamata", "esito")
	esito.protocollo = _primo_testo(radice, "protocollo", "protocolloTelematico")

	for nodo in _tutti(radice, "messaggio") + _tutti(radice, "listaMessaggi"):
		tipo = _primo_testo(nodo, "tipoMessaggio", "tipo") or ""
		codice = _primo_testo(nodo, "codiceEsito", "codice", "codiceMessaggio") or ""
		descrizione = _primo_testo(nodo, "descrizione", "descrizioneMessaggio", "testo") or ""
		if not (tipo or codice or descrizione):
			continue
		esito.messaggi.append(Messaggio(tipo=tipo, codice=codice, descrizione=descrizione))

	# Some responses carry the rejection code outside the message list.
	if not esito.messaggi:
		codice = _primo_testo(radice, "codiceEsito", "codiceErrore")
		if codice:
			esito.messaggi.append(
				Messaggio(
					tipo=TipoMessaggioTS.ERRORE,
					codice=codice,
					descrizione=_primo_testo(radice, "descrizione", "descrizioneErrore") or "",
				)
			)
	return esito
