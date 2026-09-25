# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The healthcare register, which **adds** to invoicing's own.

Thirty-six qualifications that carry two things invoicing has no business knowing:
a VAT exemption under art. 10, and an SdI rule that can be a **ban**. The twenty
ordinary ones - lawyer, engineer, consultant - live in
`crm.invoicing.engine.professioni`, because cassa and ritenuta are ordinary
invoicing and an installation with no patients still has to get them right.

`ProfessioneSanitaria` extends invoicing's `Professione` rather than repeating it.
The direction is the one this whole split allows: this module imports invoicing,
never the reverse.

The two names the seam speaks - `comunicazione_esterna` and
`soggetto_comunicazione` - are exposed alongside this module's own, not instead of
them: `obbligo_ts` is what the code in here should read, because that is what it
means here.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from crm.invoicing.engine.codici import RegolaSdI, TipoCassa, TipoRitenuta
from crm.invoicing.engine.professioni import Professione
from crm.invoicing.engine.professioni import professione as professione_ordinaria

from .codici import SoggettoInviante

#: The category this module adds to invoicing's three.
CATEGORIA_SANITARIA = "sanitaria"

ESENZIONE_PROFESSIONISTA = "art. 10, n. 18, DPR 633/72 (dal 2027: art. 37, c. 1, lett. t, D.Lgs. 10/2026)"
ESENZIONE_STRUTTURA = "art. 10, n. 19, DPR 633/72 (dal 2027: art. 37, c. 1, lett. u, D.Lgs. 10/2026)"


@dataclass(frozen=True)
class ProfessioneSanitaria(Professione):
	"""An ordinary qualification, plus what the Sistema TS needs of it."""

	#: Category for the Sistema TS tracciato: it decides the admitted `tipoSpesa`.
	soggetto_inviante: str = SoggettoInviante.NON_SANITARIO
	#: Bound to report to the Sistema TS, and from which year.
	obbligo_ts: bool = False
	obbligo_ts_dal: int | None = None

	@property
	def comunicazione_esterna(self) -> bool:
		"""The name invoicing knows this duty by."""
		return self.obbligo_ts

	@property
	def soggetto_comunicazione(self) -> str | None:
		"""Likewise: `soggetto_inviante` towards the Sistema TS."""
		return self.soggetto_inviante

	@property
	def sanitaria(self) -> bool:
		return self.categoria == CATEGORIA_SANITARIA

	@property
	def tipo_spesa_suggerito(self) -> str | None:
		if self.soggetto_inviante == SoggettoInviante.PROFESSIONISTA_SANITARIO:
			return "SP"
		if self.soggetto_inviante == SoggettoInviante.MEDICO_ODONTOIATRA:
			return "SR"
		if self.soggetto_inviante == SoggettoInviante.VETERINARIO:
			return "SV"
		return None


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
) -> ProfessioneSanitaria:
	return ProfessioneSanitaria(
		codice=codice,
		etichetta=etichetta,
		categoria=CATEGORIA_SANITARIA,
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


_ELENCO: list[ProfessioneSanitaria] = [
	_sanitaria(
		"medico_chirurgo",
		"Medico chirurgo",
		SoggettoInviante.MEDICO_ODONTOIATRA,
		dal=2015,
		cassa=TipoCassa.ENPAM,
		percentuale=None,
		note="ENPAM provides for no contributo integrativo to charge the patient: nothing goes on the invoice. The 2% and 4% people quote belong to the Fondo della Medicina convenzionata, which the commissioning facilities pay.",
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
		note="Not bound to the Sistema TS for invoices issued to the employer: the recipient is a VAT subject, so the document goes to the SdI.",
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
		note="Its own deadline in mid-March: a separate batch. Veterinary companies (S.r.l., STP) have the option, not the duty.",
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
		note="Arte ausiliaria ex art. 99 R.D. 1265/1934: the service is EXEMPT under art. 10 n. 18, the electronic invoice through the SdI is FORBIDDEN, the Sistema TS report is DUE (Ris. AdE 9/2026).",
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
		note="Ris. AdE 9/2026: TAXABLE at the ordinary rate, electronic invoice through the SdI MANDATORY, no Sistema TS report. The profession is identified by L. 3/2018 and was listed among the technical prevention professions by the DM of 18 July 2024, but the process is not complete: until it is, no exemption and no SdI ban.",
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
		note="Ris. AdE 9/2026: NOT a health profession. Ordinary 22% VAT, SdI mandatory, no Sistema TS report.",
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
		note="Needs the Codice Proprietario codiceRegione-codiceAsl-codiceSSA. An S.r.l. invoicing the patient is a bound subject ONLY if accredited or authorised under art. 8-ter; otherwise it is not one at all.",
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
]


PROFESSIONI: dict[str, ProfessioneSanitaria] = {p.codice: p for p in _ELENCO}

PROFESSIONI_SDI_OBBLIGATORIO: frozenset[str] = frozenset(
	p.codice for p in _ELENCO if p.regola_sdi == RegolaSdI.OBBLIGATORIO
)

PROFESSIONI_TS: frozenset[str] = frozenset(p.codice for p in _ELENCO if p.obbligo_ts)


def professione(codice: str | None):
	"""A healthcare qualification, or invoicing's own answer for an ordinary one.

	Delegating rather than raising keeps one register from the caller's point of
	view: a practice that invoices both a session and a training course asks once
	and gets the right answer either way.
	"""
	if codice and codice in PROFESSIONI:
		return PROFESSIONI[codice]
	return professione_ordinaria(codice)


def elenco() -> list[ProfessioneSanitaria]:
	"""The healthcare register alone. Invoicing's twenty are not in here."""
	return list(_ELENCO)


def professioni_da_verificare() -> list[ProfessioneSanitaria]:
	return [p for p in _ELENCO if p.da_verificare]
