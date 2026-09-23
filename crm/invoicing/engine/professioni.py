# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The qualifications invoicing needs on its own.

Twenty of them, and none is healthcare: lawyer, accountant, engineer, architect,
notary, consultant, developer. They are here because **cassa and ritenuta are
ordinary invoicing**, not a Sistema TS concern - Cassa Forense at 4%, Inarcassa at
4%, withholding at 20%. An installation that never sees a patient still has to get
those right, and getting them wrong is a wrong invoice rather than a missing
feature.

The healthcare register lives in `crm.tessera_sanitaria` and **adds** to this one:
thirty-six more qualifications, with a VAT exemption and an SdI rule this module
neither knows nor needs. Resolution walks the chain in
`crm.invoicing.estensioni`, so a code unknown here is still found there when that
module is installed.

Pure Python, no Frappe: the rules that decide whether somebody gets fined are
provable with a checkout and an interpreter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .codici import (
	CausalePagamento,
	RegolaSdI,
	TipoCassa,
	TipoRitenuta,
)

#: Withholding on self-employment income: 20% of the taxable compensation
#: (art. 25, DPR 600/73; from 2027: D.Lgs. 33/2025 and 141/2026).
ALIQUOTA_RITENUTA_ORDINARIA = Decimal("20.00")


class Categoria:
	"""What kind of issuer this is. It drives defaults, never the tax answer."""

	ORDINISTICA = "ordinistica"
	NON_ORDINISTICA = "non_ordinistica"
	IMPRESA = "impresa"


@dataclass(frozen=True)
class Professione:
	codice: str
	etichetta: str
	categoria: str
	#: VAT exemption under art. 10 n. 18 (professional) or n. 19 (care facility).
	esente_iva: bool
	riferimento_esenzione: str | None
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
	def comunicazione_esterna(self) -> bool:
		"""No duty towards any system other than the SdI.

		The name belongs to the seam in `crm.invoicing.estensioni`, not to this file:
		invoicing understands that a line may owe a report somewhere else, and a module
		that knows about such a system overrides this.
		"""
		return False

	@property
	def soggetto_comunicazione(self) -> str | None:
		return None

	@property
	def natura_iva_suggerita(self) -> str | None:
		"""`N4` under the ordinary regime. The flat-rate regime uses `N2.2`.

		The code is computed and stored **even when it is not printed**: it has no
		legal weight on a PDF, but the Sistema TS tracciato has a `naturaIVA` field.
		"""
		return "N4" if self.esente_iva else None


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
		esente_iva=False,
		riferimento_esenzione=None,
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


def professione(codice: str | None) -> Professione:
	"""Resolve a code, or refuse. **A qualification is never guessed.**

	Raising rather than defaulting is the whole point: a line whose qualification
	nobody configured has no VAT regime, no fund and no withholding, and inventing
	any of the three produces a document that is wrong in a way nobody notices.
	"""
	if not codice:
		raise KeyError("No qualification on the line: the fiscal treatment cannot be determined")
	try:
		return PROFESSIONI[codice]
	except KeyError:
		raise KeyError(
			f"qualification {codice!r} is not in the register. The catalogue never infers: add it "
			"as a CRM Professional Qualification record, after the accountant has verified it. "
			"A healthcare qualification needs the Sistema TS module, which adds thirty-six more. "
			f"Known here: {', '.join(sorted(PROFESSIONI))}"
		) from None


def elenco() -> list[Professione]:
	"""The shipped register, in order."""
	return list(_ELENCO)


def professioni_da_verificare() -> list[Professione]:
	"""The ones an accountant still has to sign off before go-live."""
	return [p for p in _ELENCO if p.da_verificare]
