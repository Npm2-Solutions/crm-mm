"""Document arithmetic: fee -> fund -> VAT -> stamp duty -> withholding.

**The order is fixed and tested**, because the boundary cases are exactly where it
goes wrong: EUR 76 of fee with the 2% ENPAP levy makes 77.52 and the stamp duty is
due; EUR 75 makes 76.50 and it is not. At exactly 77.47 it is **not** due: the
threshold is passed, not reached (art. 13, c. 1, Tariffa Parte I, DPR 642/72,
nota 2 lett. a).

Four corrections against what almost everyone takes for granted:

* **ENPAM provides for no contributo integrativo to charge the patient.** The 2%
  and 4% people quote belong to the Fondo della Medicina convenzionata, paid by
  the commissioning facilities, not by the patient.
* **Re-charging the stamp duty is not an "art. 15 exclusion"**: Risposta AdE n. 428
  del 12 agosto 2022 says it "forms an integral part of the compensation". So it
  follows the VAT regime of the service - on a healthcare invoice it is exempt
  under art. 10 n. 18 - and it counts towards revenue, in the flat-rate regime too.
* **The contributo integrativo enters the VAT base** (art. 16 D.L. 41/1995, today
  art. 27, c. 7, TU IVA): it follows the exemption of the service, it enters the
  total, and therefore the stamp-duty threshold and the amount reported to the
  Sistema TS.
* **The contributo integrativo is not subject to the withholding; the optional INPS
  4% rivalsa is.** The first is a levy for the fund, the second is compensation.
  Getting this backwards is a certification that does not reconcile.

The invariant this module guarantees, and the one that matters: **the total on the
PDF and the sum of the items reported to the Sistema TS coincide**, with the single
exception of a stamp duty paid in cash.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from .classificazione import EsitoClassificazione, EsitoRiga
from .codici import (
	NATURE_REVERSE_CHARGE,
	EsigibilitaIVA,
	ModalitaBollo,
	TipoCassa,
	TipoRitenuta,
)

CENTESIMO = Decimal("0.01")
ZERO = Decimal("0.00")
CENTO = Decimal("100")

#: The stamp duty is due **above** this threshold, not from it.
SOGLIA_BOLLO = Decimal("77.47")
IMPORTO_BOLLO = Decimal("2.00")

#: Default rivalsa rates. `None` means the fund has nothing to show on an invoice.
PERCENTUALE_CASSA: dict[str, Decimal | None] = {
	TipoCassa.ENPAM: None,  # no contributo integrativo charged to the patient
	TipoCassa.NOTARIATO: None,
	TipoCassa.ENPAP: Decimal("2.00"),
	TipoCassa.ENPAV: Decimal("2.00"),
	TipoCassa.ENPAPI: Decimal("4.00"),
	TipoCassa.ENPAB: Decimal("4.00"),
	TipoCassa.AVVOCATI: Decimal("4.00"),
	TipoCassa.COMMERCIALISTI: Decimal("4.00"),
	TipoCassa.RAGIONIERI: Decimal("4.00"),
	TipoCassa.ENPACL: Decimal("4.00"),
	TipoCassa.INGEGNERI_ARCHITETTI: Decimal("4.00"),
	TipoCassa.GEOMETRI: Decimal("5.00"),
	TipoCassa.EPPI: Decimal("5.00"),
	TipoCassa.EPAP: Decimal("2.00"),
	TipoCassa.INPGI: Decimal("4.00"),
	TipoCassa.ENPAIA: Decimal("4.00"),
	TipoCassa.INPS: Decimal("4.00"),  # optional
}

#: Funds whose contributo integrativo is **mandatory** to show on the invoice
#: (art. 8, c. 3, D.Lgs. 103/1996). The INPS 4% rivalsa is optional instead.
CASSE_OBBLIGATORIE: frozenset[str] = frozenset(
	{
		TipoCassa.ENPAP,
		TipoCassa.ENPAPI,
		TipoCassa.ENPAB,
		TipoCassa.ENPAV,
		TipoCassa.AVVOCATI,
		TipoCassa.COMMERCIALISTI,
		TipoCassa.RAGIONIERI,
		TipoCassa.ENPACL,
		TipoCassa.INGEGNERI_ARCHITETTI,
		TipoCassa.GEOMETRI,
		TipoCassa.EPPI,
		TipoCassa.EPAP,
		TipoCassa.INPGI,
		TipoCassa.ENPAIA,
	}
)


def arrotonda(valore) -> Decimal:
	return Decimal(str(valore)).quantize(CENTESIMO, rounding=ROUND_HALF_UP)


@dataclass
class RigaCalcolata:
	esito: EsitoRiga
	imponibile: Decimal
	#: Share of the fund levy attributed to this line.
	cassa: Decimal
	aliquota: Decimal
	natura: str | None
	iva: Decimal
	#: Share of the re-charged stamp duty attributed to this line.
	bollo_riaddebitato: Decimal
	#: Amount to report to the Sistema TS for this line (0 when it does not go).
	importo_ts: Decimal
	tipo_spesa: str | None
	fuori_base_iva: bool = False

	@property
	def totale(self) -> Decimal:
		return arrotonda(self.imponibile + self.cassa + self.iva + self.bollo_riaddebitato)


@dataclass
class RiepilogoIva:
	"""One `DatiRiepilogo` block: a (rate, nature) pair with its own tax."""

	aliquota: Decimal
	natura: str | None
	imponibile: Decimal
	imposta: Decimal
	esigibilita: str = EsigibilitaIVA.IMMEDIATA
	riferimento_normativo: str | None = None


@dataclass
class Calcolo:
	righe: list[RigaCalcolata]
	riepiloghi: list[RiepilogoIva]
	imponibile: Decimal
	cassa: Decimal
	iva: Decimal
	#: Amounts outside the taxable base altogether (art. 15 advances).
	anticipazioni: Decimal
	#: The base the threshold is measured on: the amounts not charged with VAT.
	base_bollo: Decimal
	bollo_dovuto: bool
	bollo: Decimal
	bollo_riaddebitato: Decimal
	base_ritenuta: Decimal
	ritenuta: Decimal
	aliquota_ritenuta: Decimal
	tipo_ritenuta: str | None
	causale_pagamento: str | None
	totale: Decimal
	#: What the client actually transfers: the total less the withholding, and less
	#: the VAT when the split-payment regime applies.
	netto_a_pagare: Decimal
	totale_ts: Decimal
	percentuale_cassa: Decimal | None
	cassa_obbligatoria: bool
	cassa_soggetta_a_ritenuta: bool
	tipo_cassa: str | None
	split_payment: bool
	avvisi: list[str] = field(default_factory=list)

	@property
	def quadra(self) -> bool:
		"""Does the document total match what is reported to the Sistema TS?

		They diverge legitimately only when the stamp duty was paid in cash and only
		the service is reported.
		"""
		return self.totale == self.totale_ts

	@property
	def imposta_totale(self) -> Decimal:
		return self.iva

	def voci_ts(self) -> list[tuple[str, Decimal]]:
		"""Expense items for the tracciato, aggregated by type."""
		aggregato: dict[str, Decimal] = {}
		for riga in self.righe:
			if riga.importo_ts <= ZERO or not riga.tipo_spesa:
				continue
			aggregato[riga.tipo_spesa] = aggregato.get(riga.tipo_spesa, ZERO) + riga.importo_ts
		return [(tipo, arrotonda(importo)) for tipo, importo in sorted(aggregato.items())]


def _ripartisci(totale: Decimal, pesi: list[Decimal]) -> list[Decimal]:
	"""Split `totale` across the lines in proportion to the weights, to the cent.

	The rounding remainder lands on the heaviest line, so the sum of the shares is
	**exactly** the total and the reconciliation with the Sistema TS comes out to
	the cent instead of "nearly".
	"""
	somma_pesi = sum(pesi, ZERO)
	if totale == ZERO or somma_pesi == ZERO:
		return [ZERO for _ in pesi]
	quote = [arrotonda(totale * peso / somma_pesi) for peso in pesi]
	residuo = arrotonda(totale - sum(quote, ZERO))
	if residuo != ZERO:
		indice = max(range(len(pesi)), key=lambda i: pesi[i])
		quote[indice] = arrotonda(quote[indice] + residuo)
	return quote


def calcola(
	classificazione: EsitoClassificazione,
	*,
	tipo_cassa: str | None = None,
	percentuale_cassa: Decimal | None = None,
	cassa_obbligatoria: bool | None = None,
	cassa_soggetta_a_ritenuta: bool = False,
	applica_rivalsa_facoltativa: bool = False,
	modalita_bollo: str = ModalitaBollo.SU_ORIGINALE,
	bollo_riaddebitato: bool = False,
	soggetto_a_bollo: bool = True,
	bollo_pagato_in_contanti: bool = False,
	anticipazioni_nella_base_bollo: bool = True,
	applica_ritenuta: bool = False,
	aliquota_ritenuta: Decimal = Decimal("20.00"),
	tipo_ritenuta: str = TipoRitenuta.PERSONE_FISICHE,
	causale_pagamento: str | None = "A",
	ritenuta_su_riaddebito_bollo: bool = False,
	split_payment: bool = False,
	riferimenti_normativi: dict[str, str] | None = None,
) -> Calcolo:
	"""Compute the document in the right order.

	`applica_rivalsa_facoltativa` concerns only the INPS 4% rivalsa, which is **not**
	mandatory: the default is off and the operator turns it on knowingly.
	"""
	avvisi: list[str] = []
	righe_utili = [r for r in classificazione.righe if not r.riga.e_riga_bollo]
	fuori_base = [r for r in righe_utili if r.fuori_base_iva]

	# 1 - the fee
	imponibili = [arrotonda(r.riga.imponibile) for r in righe_utili]
	imponibili_servizi = [arrotonda(r.riga.imponibile) if not r.fuori_base_iva else ZERO for r in righe_utili]
	imponibile = arrotonda(sum(imponibili_servizi, ZERO))
	anticipazioni = arrotonda(sum((arrotonda(r.riga.imponibile) for r in fuori_base), ZERO))

	# 2 - the fund levy: on the gross fee, before anything else
	percentuale = percentuale_cassa
	if percentuale is None and tipo_cassa:
		percentuale = PERCENTUALE_CASSA.get(tipo_cassa)
	obbligatoria = cassa_obbligatoria if cassa_obbligatoria is not None else tipo_cassa in CASSE_OBBLIGATORIE
	if percentuale and not obbligatoria and not applica_rivalsa_facoltativa:
		# The INPS 4% rivalsa is optional: it is not applied by default.
		percentuale = None
	if tipo_cassa == TipoCassa.ENPAM and (percentuale or ZERO) > ZERO:
		avvisi.append(
			"a rivalsa has been configured for ENPAM: ENPAM provides for no contributo integrativo "
			"to charge the patient. Check with the accountant before showing it on the invoice"
		)
	importo_cassa = arrotonda(imponibile * percentuale / CENTO) if percentuale else ZERO
	quote_cassa = _ripartisci(importo_cassa, imponibili_servizi)

	# 3 - VAT on the taxable lines only; the levy follows the regime of the service
	iva_totale = ZERO
	quote_iva: list[Decimal] = []
	for indice, riga in enumerate(righe_utili):
		aliquota = riga.aliquota or ZERO
		if riga.fuori_base_iva or riga.natura_iva or aliquota <= ZERO:
			quote_iva.append(ZERO)
			continue
		base = imponibili_servizi[indice] + quote_cassa[indice]
		quota = arrotonda(base * aliquota / CENTO)
		quote_iva.append(quota)
		iva_totale += quota
	iva_totale = arrotonda(iva_totale)

	# 4 - the stamp-duty threshold, measured on the amounts NOT charged with VAT and
	#     **after** the fund levy. On a pure healthcare invoice it equals the total.
	base_bollo = arrotonda(
		sum(
			(
				imponibili_servizi[i] + quote_cassa[i]
				for i, r in enumerate(righe_utili)
				if not r.fuori_base_iva and (r.natura_iva or r.esente_iva or not (r.aliquota or ZERO) > ZERO)
			),
			ZERO,
		)
	)
	if anticipazioni > ZERO and anticipazioni_nella_base_bollo:
		# Advances under art. 15 are not charged with VAT either, so the prevailing
		# reading puts them in the threshold. It is a reading, not a settled point:
		# it is a switch, and it says so out loud when it is what tips the balance.
		nuova_base = arrotonda(base_bollo + anticipazioni)
		if base_bollo <= SOGLIA_BOLLO < nuova_base:
			avvisi.append(
				"the stamp duty becomes due only because the art. 15 advances are counted in the "
				"threshold. That is the prevailing reading of nota 2 lett. a) and it is not settled "
				"- confirm it with the accountant"
			)
		base_bollo = nuova_base

	bollo_dovuto = bool(soggetto_a_bollo and base_bollo > SOGLIA_BOLLO)
	bollo = IMPORTO_BOLLO if bollo_dovuto else ZERO

	# 5 - the re-charge: part of the compensation, not an advance. It stays out of
	#     the threshold base: the stamp duty does not feed itself.
	riaddebito = bollo if (bollo_dovuto and bollo_riaddebitato) else ZERO
	pesi_esenti = [
		imponibili_servizi[i] if (r.natura_iva or r.esente_iva) else ZERO for i, r in enumerate(righe_utili)
	]
	if sum(pesi_esenti, ZERO) == ZERO:
		pesi_esenti = imponibili_servizi
	quote_riaddebito = _ripartisci(riaddebito, pesi_esenti)

	if bollo_dovuto and modalita_bollo == ModalitaBollo.SU_ORIGINALE:
		avvisi.append(
			"stamp duty settled with a physical stamp on the paper original: the PDF has to carry "
			"the 14-digit identifier and the date of the stamp, which must be the same as or "
			"earlier than the invoice date"
		)

	# 6 - the withholding: on the compensation, plus the levy only when the levy is
	#     compensation itself. Never on the VAT.
	base_ritenuta = ZERO
	ritenuta = ZERO
	if applica_ritenuta and aliquota_ritenuta > ZERO:
		base_ritenuta = imponibile
		if cassa_soggetta_a_ritenuta:
			base_ritenuta += importo_cassa
		if ritenuta_su_riaddebito_bollo:
			base_ritenuta += riaddebito
		base_ritenuta = arrotonda(base_ritenuta)
		ritenuta = arrotonda(base_ritenuta * aliquota_ritenuta / CENTO)

	totale = arrotonda(imponibile + importo_cassa + iva_totale + riaddebito + anticipazioni)

	# 7 - amounts for the Sistema TS: only the lines that go, each with its share of
	#     the levy and of the re-charge. This is where the totals are made to coincide.
	righe_calcolate: list[RigaCalcolata] = []
	for indice, riga in enumerate(righe_utili):
		importo_ts = ZERO
		if riga.va_al_ts:
			importo_ts = arrotonda(
				imponibili_servizi[indice]
				+ quote_cassa[indice]
				+ quote_iva[indice]
				+ (ZERO if bollo_pagato_in_contanti else quote_riaddebito[indice])
			)
		righe_calcolate.append(
			RigaCalcolata(
				esito=riga,
				imponibile=imponibili[indice],
				cassa=quote_cassa[indice],
				aliquota=riga.aliquota or ZERO,
				natura=riga.natura_iva,
				iva=quote_iva[indice],
				bollo_riaddebitato=quote_riaddebito[indice],
				importo_ts=importo_ts,
				tipo_spesa=riga.tipo_spesa,
				fuori_base_iva=riga.fuori_base_iva,
			)
		)

	totale_ts = arrotonda(sum((r.importo_ts for r in righe_calcolate), ZERO))

	if bollo_pagato_in_contanti and riaddebito > ZERO:
		avvisi.append(
			"only the stamp duty was paid in cash: the Sistema TS is told the amount of the service "
			"alone and the report stays 'traced'"
		)

	esigibilita = EsigibilitaIVA.SCISSIONE_PAGAMENTI if split_payment else EsigibilitaIVA.IMMEDIATA
	riepiloghi = _riepiloghi(righe_calcolate, quote_riaddebito, esigibilita, riferimenti_normativi or {})

	netto_a_pagare = arrotonda(totale - ritenuta - (iva_totale if split_payment else ZERO))
	if split_payment and iva_totale > ZERO:
		avvisi.append(
			"split payment (art. 17-ter): the VAT is shown but not collected. The invoice has to "
			"carry the annotation 'scissione dei pagamenti' and the client pays the net amount"
		)
	if any(r.esito.reverse_charge for r in righe_calcolate):
		avvisi.append(
			"reverse charge: the invoice carries no VAT and has to say 'inversione contabile'. "
			"The client settles the tax"
		)

	calcolo = Calcolo(
		righe=righe_calcolate,
		riepiloghi=riepiloghi,
		imponibile=imponibile,
		cassa=importo_cassa,
		iva=iva_totale,
		anticipazioni=anticipazioni,
		base_bollo=base_bollo,
		bollo_dovuto=bollo_dovuto,
		bollo=bollo,
		bollo_riaddebitato=riaddebito,
		base_ritenuta=base_ritenuta,
		ritenuta=ritenuta,
		aliquota_ritenuta=aliquota_ritenuta if applica_ritenuta else ZERO,
		tipo_ritenuta=tipo_ritenuta if applica_ritenuta and ritenuta > ZERO else None,
		causale_pagamento=causale_pagamento if applica_ritenuta and ritenuta > ZERO else None,
		totale=totale,
		netto_a_pagare=netto_a_pagare,
		totale_ts=totale_ts,
		percentuale_cassa=percentuale,
		cassa_obbligatoria=obbligatoria,
		cassa_soggetta_a_ritenuta=cassa_soggetta_a_ritenuta,
		tipo_cassa=tipo_cassa if percentuale else None,
		split_payment=split_payment,
		avvisi=avvisi,
	)

	if classificazione.ts_richiesto and not calcolo.quadra and not bollo_pagato_in_contanti:
		differenza = arrotonda(calcolo.totale - calcolo.totale_ts)
		if differenza != ZERO and all(r.va_al_ts for r in righe_utili):
			avvisi.append(
				f"the document total ({calcolo.totale}) does not match the amount reported to the "
				f"Sistema TS ({calcolo.totale_ts}): difference {differenza}. The patient would see a "
				"different number in the pre-filled return than the one they are holding"
			)
	return calcolo


def _riepiloghi(
	righe: list[RigaCalcolata],
	quote_riaddebito: list[Decimal],
	esigibilita: str,
	riferimenti: dict[str, str],
) -> list[RiepilogoIva]:
	"""Group into `DatiRiepilogo` blocks, one per (rate, nature) pair.

	The re-charged stamp duty is folded into the block of the line it follows: it is
	part of the compensation, so it cannot become a summary block of its own.
	"""
	aggregato: dict[tuple[str, str], list[Decimal]] = {}
	for indice, riga in enumerate(righe):
		chiave = (f"{riga.aliquota:.2f}", riga.natura or "")
		imponibile = riga.imponibile + riga.cassa + quote_riaddebito[indice]
		imposta = riga.iva
		if chiave not in aggregato:
			aggregato[chiave] = [ZERO, ZERO]
		aggregato[chiave][0] += imponibile
		aggregato[chiave][1] += imposta

	riepiloghi: list[RiepilogoIva] = []
	for (aliquota, natura), (imponibile, imposta) in sorted(aggregato.items()):
		riepiloghi.append(
			RiepilogoIva(
				aliquota=Decimal(aliquota),
				natura=natura or None,
				imponibile=arrotonda(imponibile),
				imposta=arrotonda(imposta),
				esigibilita=esigibilita,
				riferimento_normativo=riferimenti.get(natura) if natura else None,
			)
		)
	return riepiloghi


def tracciabile(codice_pagamento: str | None) -> bool | None:
	"""Is the payment traced for deduction purposes?

	The rule almost nobody knows: **a mixed payment - part cash, part traced - is
	reported as NOT traced.** The single exception is a stamp duty paid in cash,
	which does not contaminate the service; that case is handled in `calcola` by
	leaving the re-charge out of the reported amount.
	"""
	from .codici import PAGAMENTI_CONTANTI, PAGAMENTI_TRACCIATI

	if not codice_pagamento:
		return None
	if codice_pagamento in PAGAMENTI_CONTANTI:
		return False
	if codice_pagamento in PAGAMENTI_TRACCIATI:
		return True
	return None


def natura_richiede_riferimento(natura: str | None) -> bool:
	"""Does this nature need a `RiferimentoNormativo` on the summary block?

	Not a formal requirement of the schema, but exemptions and reverse charges are
	read by a human on the other side, and "N4" on its own tells them nothing.
	"""
	if not natura:
		return False
	return natura == "N4" or natura in NATURE_REVERSE_CHARGE or natura.startswith("N3")
