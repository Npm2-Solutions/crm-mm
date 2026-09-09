"""Classification engine and **SdI guard**.

Never by inference, never by keyword, never with a model: the classification is a
**configured** property. A service without a card is not billable, and there is no
silent default anywhere in this file.

The guard is not built on `is_sanitaria`. It is built on a **triple**:

	(service, qualification of whoever performs it, kind of recipient)
	   -> {exempt | taxable} x {SdI forbidden | SdI mandatory} x {Sistema TS yes | no}

Two symmetrical mistakes, both serious, are what this module exists to prevent:

* sending a healthcare invoice for a natural person to the SdI - that is a privacy
  breach, not a tax error, and it has to be blocked **server-side with a 403**;
* **not** sending an osteopath's invoice to the SdI - the violation in reverse,
  which is born precisely from a guard written too wide.

Running in Europe adds a third case the original design could ignore: a client in
another member state. Since 2022 those invoices go through the SdI too, with
`codice destinatario XXXXXXX`, and the VAT treatment is a territorial question
(art. 7-ter) that this module surfaces but never answers on its own.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal

from .codici import (
	NATURE_FUORI_BASE,
	NATURE_REVERSE_CHARGE,
	Canale,
	RegimeFiscale,
	RegolaSdI,
	TipoDestinatario,
	tipi_spesa_ammessi,
)
from .professioni import Professione, professione

#: How a qualification code is turned into a `Professione`. The shipped register is
#: the default; the CRM overrides it with the editable table, because the choices
#: that decide fiscal correctness belong to the practice owner and not to a file
#: only a developer can change.
Risolutore = Callable[[str], Professione]


class GuardiaSdI(PermissionError):
	"""An attempt to route a document that cannot travel through the SdI.

	It is a `PermissionError` on purpose: the API turns it into **403**, not 400.
	It is not malformed input, it is a forbidden operation.
	"""

	def __init__(self, motivo: str, righe: list[str] | None = None):
		self.motivo = motivo
		self.righe = righe or []
		super().__init__(motivo)


@dataclass
class RigaDaClassificare:
	"""Engine input: service plus performer, with no dependency on the ORM."""

	servizio_id: str | None
	descrizione_fiscale: str
	is_sanitaria: bool
	#: Exemption declared in the catalogue, **verified by the accountant**.
	esente_iva: bool
	erogatore_id: str | None
	erogatore_qualifica: str | None
	imponibile: Decimal
	tipo_spesa_catalogo: str | None = None
	natura_iva_catalogo: str | None = None
	aliquota_catalogo: Decimal | None = None
	flag_tipo_spesa: str | None = None
	#: Share covered by a voucher or a bonus: reported under `AA`, because it did
	#: not stay at the taxpayer's expense.
	quota_non_a_carico: Decimal | None = None
	e_riga_bollo: bool = False
	#: Advance in the client's name and on the client's behalf (art. 15): outside
	#: the taxable base entirely, and outside the stamp-duty threshold.
	e_anticipazione: bool = False


@dataclass
class EsitoRiga:
	riga: RigaDaClassificare
	esente_iva: bool
	natura_iva: str | None
	aliquota: Decimal | None
	regola_sdi: str
	va_al_ts: bool
	tipo_spesa: str | None
	flag_tipo_spesa: str | None
	soggetto_inviante: str | None
	#: Is the electronic-invoice duty **explicit for the qualification** (Ris. 9/2026:
	#: osteopath, chiropractor, kinesiologist), or merely *derived* from the service
	#: not being healthcare or the recipient being a VAT subject? The difference
	#: decides how a mixed document resolves, and it is the distinction between the
	#: two symmetrical mistakes.
	obbligo_sdi_esplicito: bool = False
	#: The line carries no VAT and no exemption either: it is out of the base.
	fuori_base_iva: bool = False
	reverse_charge: bool = False
	errori: list[str] = field(default_factory=list)
	avvisi: list[str] = field(default_factory=list)


@dataclass
class EsitoClassificazione:
	righe: list[EsitoRiga]
	canale: str
	sdi_consentito: bool
	sdi_obbligatorio: bool
	ts_richiesto: bool
	errori: list[str] = field(default_factory=list)
	avvisi: list[str] = field(default_factory=list)

	@property
	def valido(self) -> bool:
		return not self.errori and not any(r.errori for r in self.righe)

	@property
	def tutti_errori(self) -> list[str]:
		elenco = list(self.errori)
		for indice, riga in enumerate(self.righe, start=1):
			elenco.extend(f"line {indice}: {e}" for e in riga.errori)
		return elenco

	@property
	def tutti_avvisi(self) -> list[str]:
		elenco = list(self.avvisi)
		for indice, riga in enumerate(self.righe, start=1):
			elenco.extend(f"line {indice}: {a}" for a in riga.avvisi)
		return elenco

	@property
	def righe_ts(self) -> list[EsitoRiga]:
		return [r for r in self.righe if r.va_al_ts]


def _natura(esente: bool, regime: str, catalogo: str | None) -> str | None:
	"""`N4` under the ordinary regime, `N2.2` under the flat rate.

	On a PDF the code carries no legal weight - the textual annotation does. **It
	is still needed**, because the Sistema TS tracciato has a `naturaIVA` field. It
	is computed and stored even when it is never printed.
	"""
	if not esente:
		return None
	if regime == RegimeFiscale.FORFETTARIO:
		return "N2.2"
	return catalogo or "N4"


def natura_territoriale(
	destinatario: str,
	paese: str | None,
	controparte_soggetto_iva: bool,
) -> tuple[str | None, str]:
	"""What the territorial rule *suggests* for a cross-border service.

	It suggests. It never decides: the answer depends on the kind of service
	(arts. 7-quater and 7-quinquies carve out real estate, transport, catering,
	events, and services to a private individual abroad), and that is a property of
	the service card. Returning a code here and calling it settled is how an invoice
	goes out with no VAT that owed 22%.
	"""
	stato = (paese or "IT").upper()
	if stato in ("IT", ""):
		return None, ""
	if destinatario == TipoDestinatario.ESTERO or stato != "IT":
		if controparte_soggetto_iva:
			return (
				"N2.1",
				"Cross-border B2B service: art. 7-ter puts the general rule outside the scope of "
				"Italian VAT, with the reverse charge on the client. Services connected to real "
				"estate, transport, catering and admission to events follow arts. 7-quater and "
				"7-quinquies instead - confirm it on the service card.",
			)
		return (
			None,
			"Cross-border service to a private individual: as a general rule Italian VAT still "
			"applies, and the OSS regime may come into play. Confirm the treatment before issuing.",
		)
	return None, ""


def _risolvi_tipo_spesa(
	riga: RigaDaClassificare, emittente: str, erogatore: str
) -> tuple[str | None, list[str]]:
	"""(service, performer's qualification, **issuer's category**) -> `tipoSpesa`.

	Two different subjects, which coincide in a solo practice and diverge in a
	facility:

	* **whoever performs** decides whether the service is exempt and whether it goes
	  to the Sistema TS - the same session is `SR` from the doctor and `SP` from the
	  physiotherapist;
	* **whoever issues the fiscal document** decides which codes are *usable*,
	  because it is their category that ends up in `proprietario.soggetto`, and the
	  tracciato validates the field against it.

	When a facility does the invoicing the codes are its own - `SR CT PI IC AA` for
	an authorised one - and **`SP` is not among them**, however much a health
	professional performed the session. Picking from the profession would produce a
	document that is rejected at send time: with the invoice already issued and
	already handed to the patient.
	"""
	ammessi = tipi_spesa_ammessi(emittente)
	problemi: list[str] = []

	if riga.quota_non_a_carico and riga.quota_non_a_carico > 0 and "AA" in ammessi:
		return "AA", problemi

	candidato = riga.tipo_spesa_catalogo
	if candidato and candidato in ammessi:
		return candidato, problemi
	if candidato:
		problemi.append(
			f"the catalogue proposes tipoSpesa {candidato!r}, which is not admitted to whoever "
			f"issues the document (category {emittente!r}; admitted: {', '.join(sorted(ammessi))}). "
			"The expense type follows the issuer of the fiscal document, not the service"
		)
		return None, problemi

	if len(ammessi) == 1:
		# The health professional invoicing in their own name: `SP` and nothing else.
		return next(iter(ammessi)), problemi

	naturali = tipi_spesa_ammessi(erogatore)
	if erogatore != emittente and not (naturali & ammessi):
		problemi.append(
			f"tipoSpesa not determinable: the service is performed by a subject of category "
			f"{erogatore!r} (which would use {', '.join(sorted(naturali))}), but the document is "
			f"issued by {emittente!r}, which cannot use those codes "
			f"(admitted: {', '.join(sorted(ammessi))}). Pick it on the service card"
		)
	else:
		problemi.append(
			f"tipoSpesa not determinable for {emittente!r}: the catalogue does not say, and the "
			f"issuer's category admits more than one ({', '.join(sorted(ammessi))}). Pick it on "
			"the service card"
		)
	return None, problemi


def classifica_riga(
	riga: RigaDaClassificare,
	destinatario: str,
	regime: str = RegimeFiscale.ORDINARIO,
	soggetto_emittente: str | None = None,
	risolvi: Risolutore | None = None,
) -> EsitoRiga:
	"""`soggetto_emittente` is the category of **whoever issues the document**.

	`None` is not a fallback: it says the performer is also the issuer - the
	professional invoicing in their own name, which is the majority. When a facility
	invoices, the two diverge and the tenant's category has to be passed: it is the
	one that decides which expense types are usable.
	"""
	errori: list[str] = []
	avvisi: list[str] = []

	def _riga_semplice(**kwargs) -> EsitoRiga:
		base = {
			"riga": riga,
			"esente_iva": False,
			"natura_iva": None,
			"aliquota": None,
			"regola_sdi": RegolaSdI.AMMESSO,
			"va_al_ts": False,
			"tipo_spesa": None,
			"flag_tipo_spesa": None,
			"soggetto_inviante": None,
			"errori": errori,
			"avvisi": avvisi,
		}
		base.update(kwargs)
		return EsitoRiga(**base)

	if riga.e_anticipazione:
		# Art. 15: outside the taxable base altogether. It is not exempt, it is not
		# there - and it does not feed the stamp-duty threshold either.
		return _riga_semplice(natura_iva="N1", fuori_base_iva=True)

	if riga.e_riga_bollo:
		# The re-charged stamp duty is **part of the compensation** and follows the
		# VAT regime of the service: it is not a line to classify, it inherits.
		return _riga_semplice(
			esente_iva=riga.esente_iva,
			natura_iva=_natura(riga.esente_iva, regime, riga.natura_iva_catalogo),
			aliquota=None if riga.esente_iva else riga.aliquota_catalogo,
		)

	if not riga.servizio_id:
		errori.append("service not in the catalogue: a service without a card is not billable")
	if not riga.erogatore_qualifica:
		errori.append(
			"no performer on the line: without a qualification neither the expense type nor the "
			"VAT regime can be determined"
		)
		return _riga_semplice()

	try:
		prof = (risolvi or professione)(riga.erogatore_qualifica)
	except KeyError as exc:
		errori.append(str(exc))
		return _riga_semplice()

	# ------------------------------------------------------------ VAT exemption
	# The requirement is **joint**: objective (the service) and subjective (the
	# profession). The catalogue can only narrow it, never widen it.
	if riga.esente_iva and not prof.esente_iva:
		errori.append(
			f"the catalogue declares the service exempt, but {prof.etichetta!r} is not a health "
			"profession for exemption purposes: the service is TAXABLE at the ordinary rate and "
			"the electronic invoice through the SdI is MANDATORY (Risoluzione AdE n. 9 del 24 "
			"febbraio 2026). Correct the service card"
		)
	esente = riga.esente_iva and prof.esente_iva
	if not riga.esente_iva and prof.esente_iva and riga.is_sanitaria:
		avvisi.append(
			f"service declared taxable although performed by {prof.etichetta!r}: possible (cosmetic "
			"surgery, for instance), but it has to be confirmed in the catalogue"
		)

	# ------------------------------------------------------------------ routing
	obbligo_esplicito = False
	if destinatario in (
		TipoDestinatario.SOGGETTO_IVA,
		TipoDestinatario.PUBBLICA_AMMINISTRAZIONE,
		TipoDestinatario.ESTERO,
	):
		# Towards VAT subjects, the PA and abroad the channel is always the SdI, and
		# there is no Sistema TS report: the Sistema TS only knows natural persons.
		regola = RegolaSdI.OBBLIGATORIO
		va_al_ts = False
	elif not riga.is_sanitaria:
		# Not healthcare, towards a natural person: electronic invoice, no Sistema TS.
		regola = RegolaSdI.OBBLIGATORIO
		va_al_ts = False
	else:
		regola = prof.regola_sdi
		va_al_ts = prof.obbligo_ts and regola == RegolaSdI.VIETATO
		obbligo_esplicito = regola == RegolaSdI.OBBLIGATORIO

	if (
		destinatario == TipoDestinatario.PERSONA_FISICA
		and regola == RegolaSdI.OBBLIGATORIO
		and riga.is_sanitaria
	):
		avvisi.append(
			f"{prof.etichetta!r}: the service is NOT exempt and the electronic invoice through the "
			"SdI is mandatory towards the patient too. No Sistema TS report"
		)

	# ------------------------------------------------------------- expense type
	tipo_spesa: str | None = None
	if va_al_ts:
		tipo_spesa, problemi = _risolvi_tipo_spesa(
			riga, soggetto_emittente or prof.soggetto_inviante, prof.soggetto_inviante
		)
		errori.extend(problemi)

	flag = riga.flag_tipo_spesa
	if flag and tipo_spesa:
		atteso = {"1": "TK", "2": "SR"}.get(flag)
		if atteso != tipo_spesa:
			errori.append(
				f"flagTipoSpesa={flag} is only admitted with tipoSpesa={atteso}, not with {tipo_spesa!r}"
			)

	# ------------------------------------------------------------- VAT on the line
	natura = _natura(esente, regime, riga.natura_iva_catalogo)
	reverse_charge = False
	fuori_base = False
	if not esente and riga.natura_iva_catalogo:
		# A non-exempt line can still carry no VAT: reverse charge, out of scope,
		# non-taxable export. The catalogue says which, and it is never guessed.
		natura = riga.natura_iva_catalogo
		reverse_charge = natura in NATURE_REVERSE_CHARGE
		fuori_base = natura in NATURE_FUORI_BASE
	if regime == RegimeFiscale.FORFETTARIO and not natura:
		natura = "N2.2"

	aliquota: Decimal | None
	if natura:
		aliquota = Decimal("0.00")
	elif esente:
		aliquota = Decimal("0.00")
	else:
		aliquota = riga.aliquota_catalogo if riga.aliquota_catalogo is not None else prof.aliquota_iva_default

	return EsitoRiga(
		riga=riga,
		esente_iva=esente,
		natura_iva=natura,
		aliquota=aliquota,
		regola_sdi=regola,
		va_al_ts=va_al_ts,
		tipo_spesa=tipo_spesa,
		flag_tipo_spesa=flag,
		soggetto_inviante=prof.soggetto_inviante,
		obbligo_sdi_esplicito=obbligo_esplicito,
		fuori_base_iva=fuori_base,
		reverse_charge=reverse_charge,
		errori=errori,
		avvisi=avvisi,
	)


def classifica(
	righe: list[RigaDaClassificare],
	destinatario: str,
	regime: str = RegimeFiscale.ORDINARIO,
	soggetto_emittente: str | None = None,
	risolvi: Risolutore | None = None,
) -> EsitoClassificazione:
	"""Classify the whole document. **Model it per line, never per document.**

	`soggetto_emittente` is the category of whoever issues the fiscal document. It
	is worth passing always: in a facility the performer and the issuer diverge, and
	it is the issuer's category that decides which expense types the tracciato takes.
	"""
	if not righe:
		return EsitoClassificazione(
			righe=[],
			canale=Canale.PDF_SOLO,
			sdi_consentito=False,
			sdi_obbligatorio=False,
			ts_richiesto=False,
			errori=["the document has no lines"],
		)

	esiti = [classifica_riga(r, destinatario, regime, soggetto_emittente, risolvi) for r in righe]
	da_valutare = [e for e in esiti if not e.riga.e_riga_bollo and not e.riga.e_anticipazione]

	vietato = any(e.regola_sdi == RegolaSdI.VIETATO for e in da_valutare)
	obbligatorio = any(e.regola_sdi == RegolaSdI.OBBLIGATORIO for e in da_valutare)
	obbligo_esplicito = any(e.obbligo_sdi_esplicito for e in da_valutare)
	ts_richiesto = any(e.va_al_ts for e in esiti)

	errori: list[str] = []
	avvisi: list[str] = []

	if vietato and obbligo_esplicito:
		# A real conflict: one line **cannot** go through the SdI, another **must**
		# by express provision. "Take the stricter rule" does not resolve it - the
		# only way out is to split the document.
		errori.append(
			"mixed document cannot be issued: it holds lines for which the electronic invoice "
			"through the SdI is FORBIDDEN (exempt healthcare service towards a natural person) "
			"and lines for which it is MANDATORY by express provision (Ris. AdE n. 9 del 24 "
			"febbraio 2026: osteopath, chiropractor, kinesiologist). Issue two separate documents"
		)

	if vietato and not obbligo_esplicito:
		# **A single healthcare line towards a natural person takes the whole document
		# out of the SdI channel.** The stricter rule wins, and only the healthcare
		# share goes to the Sistema TS.
		canale = Canale.PDF_TS if ts_richiesto else Canale.PDF_SOLO
		sdi_consentito = False
		if len(da_valutare) > 1 and obbligatorio:
			avvisi.append(
				"a single healthcare line towards a natural person takes the whole document out of "
				"the SdI channel: only the healthcare share goes to the Sistema TS. To keep the "
				"non-healthcare line in an electronic invoice, issue it on a separate document"
			)
	elif obbligatorio:
		canale = Canale.SDI
		sdi_consentito = True
	else:
		canale = Canale.PDF_SOLO
		sdi_consentito = False

	return EsitoClassificazione(
		righe=esiti,
		canale=canale,
		sdi_consentito=sdi_consentito and not vietato,
		sdi_obbligatorio=obbligatorio and not vietato,
		ts_richiesto=ts_richiesto,
		errori=errori,
		avvisi=avvisi,
	)


def guardia_sdi(esito: EsitoClassificazione) -> None:
	"""Server-side barrier: raises when the document cannot go to the SdI.

	**It is not a UI flag.** It holds for every user and every override, and in the
	interface the "send to SdI" button does not exist at all: a greyed-out button
	invites somebody to go looking for how to turn it on.
	"""
	if esito.sdi_consentito:
		return
	motivi = [
		f"line {i}: {e.riga.descrizione_fiscale} - performed by {e.riga.erogatore_qualifica!r}, "
		"exempt healthcare service towards a natural person"
		for i, e in enumerate(esito.righe, start=1)
		if e.regola_sdi == RegolaSdI.VIETATO
	]
	raise GuardiaSdI(
		"Sending to the SdI is not allowed: since 2026 the electronic invoice through the Sistema "
		"di Interscambio for healthcare services towards natural persons is structurally forbidden "
		"(D.Lgs. 12 giugno 2025 n. 81, art. 10-bis D.L. 119/2018). The patient receives the invoice "
		"as a PDF and the expense is reported to the Sistema TS.",
		motivi,
	)
