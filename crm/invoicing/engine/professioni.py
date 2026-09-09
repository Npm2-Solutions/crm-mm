"""Register of qualifications: VAT exemption, Sistema TS duty, SdI routing, fund.

This table is the reason a practice picks a vertical module over a generic
accounting package: **it is exactly the casuistry practices get wrong on their
own.** It covers healthcare and everything else in one list, because a CRM
invoices a physiotherapist and a marketing agency out of the same screen and the
answer has to come from the same place.

The counter-intuitive part, from **Risoluzione AdE n. 9 del 24 febbraio 2026**:

	Osteopata        imponibile, ordinary rate    SdI mandatory   no Sistema TS
	Chiropratico     imponibile                   SdI mandatory   no Sistema TS
	Chinesiologo     imponibile 22%               SdI mandatory   no Sistema TS
	Massoterapista   esente art. 10 n. 18         SdI forbidden   Sistema TS yes

So a multi-specialty practice with an osteopath and a physiotherapist runs **two
opposite regimes on the same legal person**. A guard that blocks the SdI for
everything that "looks medical" blocks a document the law says *must* go through
it - the violation in reverse, and the expensive one, because nobody notices.

WARNING: this is a documented starting point, not a tax opinion. The exemption
test is **joint** - objective (diagnosis, care, rehabilitation) and subjective (a
supervised health profession) - so the service catalogue carries an explicit
exemption flag, verified by the accountant profession by profession, never
inferred. The `da_verificare` entries mark where that verification is mandatory
before going live.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .codici import (
	CausalePagamento,
	RegolaSdI,
	SoggettoInviante,
	TipoCassa,
	TipoRitenuta,
)

#: Withholding on self-employment income: 20% of the taxable compensation
#: (art. 25, DPR 600/73; from 2027: D.Lgs. 33/2025 and 141/2026).
ALIQUOTA_RITENUTA_ORDINARIA = Decimal("20.00")

ESENZIONE_PROFESSIONISTA = "art. 10, n. 18, DPR 633/72 (dal 2027: art. 37, c. 1, lett. t, D.Lgs. 10/2026)"
ESENZIONE_STRUTTURA = "art. 10, n. 19, DPR 633/72 (dal 2027: art. 37, c. 1, lett. u, D.Lgs. 10/2026)"


class Categoria:
	"""What kind of issuer this is. It drives defaults, never the tax answer."""

	SANITARIA = "sanitaria"
	ORDINISTICA = "ordinistica"
	NON_ORDINISTICA = "non_ordinistica"
	IMPRESA = "impresa"


@dataclass(frozen=True)
class Professione:
	codice: str
	etichetta: str
	categoria: str
	#: Category for the Sistema TS tracciato: it decides the admitted `tipoSpesa`.
	soggetto_inviante: str
	#: VAT exemption under art. 10 n. 18 (professional) or n. 19 (care facility).
	esente_iva: bool
	riferimento_esenzione: str | None
	#: Bound to report to the Sistema TS, and from which year.
	obbligo_ts: bool
	obbligo_ts_dal: int | None
	regola_sdi: str
	cassa: str | None
	cassa_percentuale: Decimal | None
	#: Is the levy a mandatory `contributo integrativo` or an optional rivalsa?
	cassa_obbligatoria: bool
	#: The `contributo integrativo` is **not** subject to withholding; the optional
	#: INPS 4% rivalsa **is**, because it is part of the compensation.
	cassa_soggetta_a_ritenuta: bool = False
	#: Withholding applies by default when the client is a withholding agent. It
	#: never applies towards a natural person, who is not one.
	ritenuta_applicabile: bool = False
	ritenuta_aliquota: Decimal = ALIQUOTA_RITENUTA_ORDINARIA
	tipo_ritenuta: str = TipoRitenuta.PERSONE_FISICHE
	causale_pagamento: str = CausalePagamento.AUTONOMO_ABITUALE
	aliquota_iva_default: Decimal = Decimal("22.00")
	#: Points the accountant has to close before going live.
	da_verificare: tuple[str, ...] = field(default_factory=tuple)
	note: str = ""

	@property
	def sanitaria(self) -> bool:
		return self.categoria == Categoria.SANITARIA

	@property
	def tipo_spesa_suggerito(self) -> str | None:
		if self.soggetto_inviante == SoggettoInviante.PROFESSIONISTA_SANITARIO:
			return "SP"
		if self.soggetto_inviante == SoggettoInviante.MEDICO_ODONTOIATRA:
			return "SR"
		if self.soggetto_inviante == SoggettoInviante.VETERINARIO:
			return "SV"
		return None

	@property
	def natura_iva_suggerita(self) -> str | None:
		"""`N4` under the ordinary regime. The flat-rate regime uses `N2.2`.

		The code is computed and stored **even when it is not printed**: it has no
		legal weight on a PDF, but the Sistema TS tracciato has a `naturaIVA` field.
		"""
		return "N4" if self.esente_iva else None


def _sanitaria(
	codice: str,
	etichetta: str,
	soggetto: str,
	*,
	esente: bool = True,
	riferimento: str | None = ESENZIONE_PROFESSIONISTA,
	obbligo_ts: bool = True,
	dal: int | None = None,
	sdi: str = RegolaSdI.VIETATO,
	cassa: str | None = TipoCassa.INPS,
	percentuale: str | None = "4.00",
	cassa_obbligatoria: bool = False,
	cassa_soggetta_a_ritenuta: bool | None = None,
	verificare: tuple[str, ...] = (),
	note: str = "",
) -> Professione:
	return Professione(
		codice=codice,
		etichetta=etichetta,
		categoria=Categoria.SANITARIA,
		soggetto_inviante=soggetto,
		esente_iva=esente,
		riferimento_esenzione=riferimento if esente else None,
		obbligo_ts=obbligo_ts,
		obbligo_ts_dal=dal,
		regola_sdi=sdi,
		cassa=cassa,
		cassa_percentuale=Decimal(percentuale) if percentuale else None,
		cassa_obbligatoria=cassa_obbligatoria,
		cassa_soggetta_a_ritenuta=(
			not cassa_obbligatoria if cassa_soggetta_a_ritenuta is None else cassa_soggetta_a_ritenuta
		),
		# A healthcare invoice to a patient never carries a withholding: a natural
		# person is not a withholding agent (art. 23, c. 1, DPR 600/73). Towards a
		# company - a medico competente billing an employer - it does.
		ritenuta_applicabile=True,
		da_verificare=verificare,
		note=note,
	)


def _professionale(
	codice: str,
	etichetta: str,
	*,
	categoria: str = Categoria.ORDINISTICA,
	cassa: str | None = TipoCassa.INPS,
	percentuale: str | None = "4.00",
	cassa_obbligatoria: bool = False,
	cassa_soggetta_a_ritenuta: bool | None = None,
	ritenuta: bool = True,
	aliquota_ritenuta: str = "20.00",
	tipo_ritenuta: str = TipoRitenuta.PERSONE_FISICHE,
	causale: str = CausalePagamento.AUTONOMO_ABITUALE,
	aliquota_iva: str = "22.00",
	verificare: tuple[str, ...] = (),
	note: str = "",
) -> Professione:
	return Professione(
		codice=codice,
		etichetta=etichetta,
		categoria=categoria,
		soggetto_inviante=SoggettoInviante.NON_SANITARIO,
		esente_iva=False,
		riferimento_esenzione=None,
		obbligo_ts=False,
		obbligo_ts_dal=None,
		regola_sdi=RegolaSdI.OBBLIGATORIO,
		cassa=cassa,
		cassa_percentuale=Decimal(percentuale) if percentuale else None,
		cassa_obbligatoria=cassa_obbligatoria,
		cassa_soggetta_a_ritenuta=(
			not cassa_obbligatoria if cassa_soggetta_a_ritenuta is None else cassa_soggetta_a_ritenuta
		),
		ritenuta_applicabile=ritenuta,
		ritenuta_aliquota=Decimal(aliquota_ritenuta),
		tipo_ritenuta=tipo_ritenuta,
		causale_pagamento=causale,
		aliquota_iva_default=Decimal(aliquota_iva),
		da_verificare=verificare,
		note=note,
	)


_ELENCO: list[Professione] = [
	# ================================================== healthcare, since 2015
	_sanitaria(
		"medico_chirurgo",
		"Medico chirurgo",
		SoggettoInviante.MEDICO_ODONTOIATRA,
		dal=2015,
		cassa=TipoCassa.ENPAM,
		percentuale=None,
		note="ENPAM provides for no contributo integrativo to charge the patient: nothing "
		"goes on the invoice. The 2% and 4% people quote belong to the Fondo della Medicina "
		"convenzionata, which the commissioning facilities pay.",
	),
	_sanitaria(
		"odontoiatra",
		"Odontoiatra",
		SoggettoInviante.MEDICO_ODONTOIATRA,
		dal=2015,
		cassa=TipoCassa.ENPAM,
		percentuale=None,
		note="Like the medico chirurgo: no rivalsa on the invoice.",
	),
	_sanitaria(
		"medico_competente",
		"Medico competente (invoices to the employer)",
		SoggettoInviante.MEDICO_ODONTOIATRA,
		obbligo_ts=False,
		dal=2015,
		sdi=RegolaSdI.AMMESSO,
		cassa=TipoCassa.ENPAM,
		percentuale=None,
		note="Not bound to the Sistema TS for invoices issued to the employer: the recipient "
		"is a VAT subject, so the document goes to the SdI.",
	),
	# ================================================== healthcare, since 2016
	_sanitaria(
		"psicologo",
		"Psicologo / psicoterapeuta",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2016,
		cassa=TipoCassa.ENPAP,
		percentuale="2.00",
		cassa_obbligatoria=True,
		note="ENPAP contributo integrativo 2% on the gross fee, mandatory and shown on the invoice.",
	),
	_sanitaria(
		"infermiere",
		"Infermiere",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2016,
		cassa=TipoCassa.ENPAPI,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_sanitaria(
		"ostetrica",
		"Ostetrica / ostetrico",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2016,
		cassa=None,
		percentuale=None,
		verificare=("pension fund and the rivalsa that goes with it",),
		note="The reference fund has to be confirmed: nothing is assumed here.",
	),
	_sanitaria(
		"tsrm",
		"Tecnico sanitario di radiologia medica",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2016,
	),
	_sanitaria(
		"veterinario",
		"Medico veterinario",
		SoggettoInviante.VETERINARIO,
		dal=2016,
		cassa=TipoCassa.ENPAV,
		percentuale="2.00",
		cassa_obbligatoria=True,
		note="Its own deadline in mid-March: a separate batch. Veterinary companies (S.r.l., "
		"STP) have the option, not the duty.",
	),
	_sanitaria(
		"ottico",
		"Ottico",
		SoggettoInviante.OTTICO,
		dal=2016,
		cassa=None,
		percentuale=None,
		verificare=("VAT regime of each individual supply",),
		note="Admitted expense types: AD and AA only.",
	),
	# ================================================== healthcare, since 2019
	_sanitaria(
		"biologo",
		"Biologo",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
		cassa=TipoCassa.ENPAB,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_sanitaria("fisioterapista", "Fisioterapista", SoggettoInviante.PROFESSIONISTA_SANITARIO, dal=2019),
	_sanitaria("logopedista", "Logopedista", SoggettoInviante.PROFESSIONISTA_SANITARIO, dal=2019),
	_sanitaria("dietista", "Dietista", SoggettoInviante.PROFESSIONISTA_SANITARIO, dal=2019),
	_sanitaria("igienista_dentale", "Igienista dentale", SoggettoInviante.PROFESSIONISTA_SANITARIO, dal=2019),
	_sanitaria("podologo", "Podologo", SoggettoInviante.PROFESSIONISTA_SANITARIO, dal=2019),
	_sanitaria(
		"tecnico_ortopedico", "Tecnico ortopedico", SoggettoInviante.PROFESSIONISTA_SANITARIO, dal=2019
	),
	_sanitaria(
		"ortottista",
		"Ortottista / assistente di oftalmologia",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
	),
	_sanitaria(
		"educatore_professionale",
		"Educatore professionale",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
	),
	_sanitaria(
		"assistente_sanitario",
		"Assistente sanitario",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
		cassa=TipoCassa.ENPAPI,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_sanitaria(
		"tecnico_laboratorio",
		"Tecnico di laboratorio biomedico",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
	),
	_sanitaria("audiometrista", "Tecnico audiometrista", SoggettoInviante.PROFESSIONISTA_SANITARIO, dal=2019),
	_sanitaria(
		"audioprotesista", "Tecnico audioprotesista", SoggettoInviante.PROFESSIONISTA_SANITARIO, dal=2019
	),
	_sanitaria(
		"tecnico_neurofisiopatologia",
		"Tecnico di neurofisiopatologia",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
	),
	_sanitaria(
		"tecnico_fisiopatologia_cardiocircolatoria",
		"Tecnico di fisiopatologia cardiocircolatoria e perfusione cardiovascolare",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
	),
	_sanitaria(
		"terapista_neuro_psicomotricita",
		"Terapista della neuro e psicomotricita' dell'eta' evolutiva",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
	),
	_sanitaria(
		"tecnico_riabilitazione_psichiatrica",
		"Tecnico della riabilitazione psichiatrica",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
	),
	_sanitaria(
		"terapista_occupazionale",
		"Terapista occupazionale",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
	),
	_sanitaria(
		"tecnico_prevenzione",
		"Tecnico della prevenzione nell'ambiente e nei luoghi di lavoro",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2019,
	),
	# ============================ Risoluzione AdE n. 9 del 24 febbraio 2026
	_sanitaria(
		"massoterapista",
		"Massoterapista (massaggiatore capo bagnino)",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		dal=2016,
		verificare=("the Sistema TS category it is enrolled under, and the tipoSpesa to use",),
		note="Arte ausiliaria ex art. 99 R.D. 1265/1934: the service is EXEMPT under art. 10 "
		"n. 18, the electronic invoice through the SdI is FORBIDDEN, the Sistema TS report is "
		"DUE (Ris. AdE 9/2026).",
	),
	_sanitaria(
		"osteopata",
		"Osteopata",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		esente=False,
		riferimento=None,
		obbligo_ts=False,
		dal=None,
		sdi=RegolaSdI.OBBLIGATORIO,
		note="Ris. AdE 9/2026: TAXABLE at the ordinary rate, electronic invoice through the SdI "
		"MANDATORY, no Sistema TS report. The profession is identified by L. 3/2018 and was "
		"listed among the technical prevention professions by the DM of 18 July 2024, but the "
		"process is not complete: until it is, no exemption and no SdI ban.",
	),
	_sanitaria(
		"chiropratico",
		"Chiropratico",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		esente=False,
		riferimento=None,
		obbligo_ts=False,
		dal=None,
		sdi=RegolaSdI.OBBLIGATORIO,
		note="Ris. AdE 9/2026: taxable, SdI mandatory, no Sistema TS report.",
	),
	_sanitaria(
		"chinesiologo",
		"Chinesiologo (art. 41 D.Lgs. 36/2021)",
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		esente=False,
		riferimento=None,
		obbligo_ts=False,
		dal=None,
		sdi=RegolaSdI.OBBLIGATORIO,
		cassa=None,
		percentuale=None,
		note="Ris. AdE 9/2026: NOT a health profession. Ordinary 22% VAT, SdI mandatory, no "
		"Sistema TS report.",
	),
	# ==================================================== healthcare facilities
	_sanitaria(
		"struttura_autorizzata",
		"Struttura autorizzata ex art. 8-ter D.Lgs. 502/1992",
		SoggettoInviante.STRUTTURA_AUTORIZZATA,
		dal=2016,
		riferimento=ESENZIONE_STRUTTURA,
		cassa=None,
		percentuale=None,
		note="Needs the Codice Proprietario codiceRegione-codiceAsl-codiceSSA. An S.r.l. "
		"invoicing the patient is a bound subject ONLY if accredited or authorised under "
		"art. 8-ter; otherwise it is not one at all.",
	),
	_sanitaria(
		"struttura_accreditata",
		"Struttura accreditata al SSN",
		SoggettoInviante.STRUTTURA_ACCREDITATA,
		dal=2015,
		riferimento=ESENZIONE_STRUTTURA,
		cassa=None,
		percentuale=None,
		note="For public or accredited private facilities, payment traceability may not be required.",
	),
	_sanitaria(
		"farmacia",
		"Farmacia",
		SoggettoInviante.FARMACIA,
		dal=2015,
		cassa=None,
		percentuale=None,
		verificare=("VAT regime per product type",),
	),
	_sanitaria(
		"parafarmacia",
		"Parafarmacia",
		SoggettoInviante.PARAFARMACIA,
		dal=2016,
		cassa=None,
		percentuale=None,
		verificare=("VAT regime per product type",),
	),
	# ================================================ regulated non-healthcare
	_professionale(
		"avvocato",
		"Avvocato",
		cassa=TipoCassa.AVVOCATI,
		percentuale="4.00",
		cassa_obbligatoria=True,
		note="Cassa Forense contributo integrativo 4%: mandatory, part of the VAT base, not "
		"subject to withholding.",
	),
	_professionale(
		"commercialista",
		"Dottore commercialista",
		cassa=TipoCassa.COMMERCIALISTI,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_professionale(
		"ragioniere",
		"Ragioniere / perito commerciale",
		cassa=TipoCassa.RAGIONIERI,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_professionale(
		"consulente_lavoro",
		"Consulente del lavoro",
		cassa=TipoCassa.ENPACL,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_professionale(
		"ingegnere",
		"Ingegnere",
		cassa=TipoCassa.INGEGNERI_ARCHITETTI,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_professionale(
		"architetto",
		"Architetto",
		cassa=TipoCassa.INGEGNERI_ARCHITETTI,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_professionale(
		"geometra",
		"Geometra",
		cassa=TipoCassa.GEOMETRI,
		percentuale="5.00",
		cassa_obbligatoria=True,
		verificare=("the current Cassa Geometri contributo integrativo rate",),
	),
	_professionale(
		"perito_industriale",
		"Perito industriale",
		cassa=TipoCassa.EPPI,
		percentuale="5.00",
		cassa_obbligatoria=True,
	),
	_professionale(
		"notaio",
		"Notaio",
		cassa=TipoCassa.NOTARIATO,
		percentuale=None,
		verificare=("the Cassa Nazionale del Notariato levy, which is not a rivalsa on the client",),
	),
	_professionale(
		"giornalista",
		"Giornalista",
		cassa=TipoCassa.INPGI,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_professionale(
		"agrotecnico",
		"Agrotecnico / perito agrario",
		cassa=TipoCassa.ENPAIA,
		percentuale="4.00",
		cassa_obbligatoria=True,
	),
	_professionale(
		"agente_commercio",
		"Agente e rappresentante di commercio",
		cassa=TipoCassa.ENASARCO,
		percentuale=None,
		ritenuta=True,
		aliquota_ritenuta="23.00",
		causale=CausalePagamento.PROVVIGIONI_MONOMANDATARIO,
		verificare=(
			"the ENASARCO rate and the split between principal and agent",
			"the withholding base: 50% or 20% of the commission depending on the arrangement",
		),
		note="Commissions do not follow the professional pattern: the withholding is 23% of a "
		"reduced base, and ENASARCO is a contribution split with the principal, not a rivalsa "
		"charged to the client. Configure it explicitly.",
	),
	_professionale(
		"psicologo_del_lavoro",
		"Psicologo del lavoro (non-clinical services)",
		cassa=TipoCassa.ENPAP,
		percentuale="2.00",
		cassa_obbligatoria=True,
		note="Organisational assessment, training and selection are not diagnosis or care: they "
		"are taxable and go through the SdI. The clinical work of the same professional does not "
		"- that is the `psicologo` entry.",
	),
	# ============================================ non-regulated professionals
	_professionale(
		"consulente",
		"Consulente (non-regulated profession)",
		categoria=Categoria.NON_ORDINISTICA,
		note="Marketing, management, IT, training: taxable at 22%, SdI, optional INPS 4% rivalsa, "
		"20% withholding towards a withholding agent.",
	),
	_professionale(
		"formatore",
		"Formatore / docente",
		categoria=Categoria.NON_ORDINISTICA,
		verificare=("exemption under art. 10 n. 20 for school-recognised training",),
		note="Training is taxable as a rule. The art. 10 n. 20 exemption is narrow - recognised "
		"bodies and school or vocational education - and it is decided in the service card, "
		"never inferred from the word 'course'.",
	),
	_professionale(
		"sviluppatore",
		"Sviluppatore software",
		categoria=Categoria.NON_ORDINISTICA,
	),
	_professionale(
		"designer",
		"Designer / creativo",
		categoria=Categoria.NON_ORDINISTICA,
		note="Assignment of copyright in a work of the mind follows a different pattern "
		"(causale B, reduced base): it goes on its own line with its own service card.",
	),
	# ============================================================== companies
	_professionale(
		"societa_servizi",
		"Societa' o impresa di servizi",
		categoria=Categoria.IMPRESA,
		cassa=None,
		percentuale=None,
		ritenuta=False,
		note="A company is not subject to the withholding on self-employment income and has no "
		"professional fund to charge. The plain case, and the most common one in a CRM.",
	),
	_professionale(
		"associazione_professionale",
		"Associazione professionale / STP",
		categoria=Categoria.IMPRESA,
		cassa=TipoCassa.INPS,
		percentuale="4.00",
		ritenuta=True,
		tipo_ritenuta=TipoRitenuta.PERSONE_GIURIDICHE,
		verificare=("the fund of the associated professionals and the rate to charge",),
		note="An association keeps the withholding but as a legal person (RT02). The fund "
		"depends on the professionals it groups.",
	),
	_professionale(
		"ente_non_commerciale",
		"Ente non commerciale",
		categoria=Categoria.IMPRESA,
		cassa=None,
		percentuale=None,
		ritenuta=False,
		verificare=("whether the activity is commercial and therefore in scope of VAT",),
	),
]

PROFESSIONI: dict[str, Professione] = {p.codice: p for p in _ELENCO}

#: Qualifications for which the SdI is **mandatory** even towards a natural
#: person. Blocking them "because they look medical" is the violation in reverse.
PROFESSIONI_SDI_OBBLIGATORIO: frozenset[str] = frozenset(
	p.codice for p in _ELENCO if p.regola_sdi == RegolaSdI.OBBLIGATORIO and p.sanitaria
)

#: Qualifications bound to report to the Sistema TS.
PROFESSIONI_TS: frozenset[str] = frozenset(p.codice for p in _ELENCO if p.obbligo_ts)


def professione(codice: str | None) -> Professione:
	"""Look up a qualification. The catalogue never infers - it raises."""
	try:
		return PROFESSIONI[codice]
	except KeyError:
		raise KeyError(
			f"qualification {codice!r} is not in the register. The catalogue never infers: add it "
			"in crm/invoicing/engine/professioni.py, or as a CRM Professional Qualification "
			f"record, after the accountant has verified it. Known: {', '.join(sorted(PROFESSIONI))}"
		) from None


def professioni_da_verificare() -> list[Professione]:
	"""What the accountant has to close before go-live."""
	return [p for p in _ELENCO if p.da_verificare]


def elenco() -> list[Professione]:
	"""The register, in declaration order - healthcare first, then the rest."""
	return list(_ELENCO)
