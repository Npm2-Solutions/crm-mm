"""Legal wording to print on the invoice.

**Every reference is doubled with the Testo Unico that applies from 1 January
2027**, otherwise in January 2027 every invoice cites repealed articles:

	DPR 633/72 art. 21        -> D.Lgs. 10/2026 (TU IVA), art. 72
	DPR 633/72 art. 10 n. 18  -> D.Lgs. 10/2026, art. 37, c. 1, lett. t)
	DPR 633/72 art. 10 n. 19  -> D.Lgs. 10/2026, art. 37, c. 1, lett. u)
	DPR 642/72 art. 15        -> D.Lgs. 123/2025, art. 150
	DPR 600/73                -> D.Lgs. 33/2025 e 141/2026
	TUIR                      -> D.Lgs. 117/2026

`Riferimento.testo` picks the right form from the document date and, in the months
either side, shows both.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

DATA_TESTI_UNICI = date(2027, 1, 1)


@dataclass(frozen=True)
class Riferimento:
	"""A legal reference together with its post-reform version."""

	attuale: str
	nuovo: str
	decorrenza: date = DATA_TESTI_UNICI

	def testo(self, data_documento: date, doppia: bool = True) -> str:
		if data_documento >= self.decorrenza:
			return self.nuovo
		if doppia:
			return f"{self.attuale} (dal {self.decorrenza.strftime('%d/%m/%Y')}: {self.nuovo})"
		return self.attuale


ESENZIONE_PROFESSIONISTA = Riferimento(
	attuale="art. 10, n. 18, del D.P.R. 633/1972",
	nuovo="art. 37, comma 1, lett. t), del D.Lgs. 10/2026",
)
ESENZIONE_STRUTTURA = Riferimento(
	attuale="art. 10, n. 19, del D.P.R. 633/1972",
	nuovo="art. 37, comma 1, lett. u), del D.Lgs. 10/2026",
)
BOLLO_VIRTUALE = Riferimento(
	attuale="art. 15 del D.P.R. 642/1972",
	nuovo="art. 150 del D.Lgs. 123/2025",
)
RITENUTA_ACCONTO = Riferimento(
	attuale="art. 25 del D.P.R. 600/1973",
	nuovo="art. 61 del D.Lgs. 141/2026",
)
FUORI_CAMPO_TERRITORIALE = Riferimento(
	attuale="art. 7-ter del D.P.R. 633/1972",
	nuovo="art. 12 del D.Lgs. 10/2026",
)
SPLIT_PAYMENT = Riferimento(
	attuale="art. 17-ter del D.P.R. 633/1972",
	nuovo="art. 30 del D.Lgs. 10/2026",
)
ANTICIPAZIONI = Riferimento(
	attuale="art. 15, comma 1, n. 3, del D.P.R. 633/1972",
	nuovo="art. 26, comma 1, lett. c), del D.Lgs. 10/2026",
)


def esenzione(data_documento: date, struttura: bool = False) -> str:
	"""The "exempt operation" annotation with the article behind it.

	It is mandatory (art. 21, c. 6, lett. c). On a PDF **this** is what counts, not
	the `N4`/`N2.2` codes, which are XML fields with no legal weight on paper.
	"""
	norma = ESENZIONE_STRUTTURA if struttura else ESENZIONE_PROFESSIONISTA
	return f"Operazione esente da IVA ai sensi dell'{norma.testo(data_documento)}."


def forfettario(includi_ritenuta: bool = True) -> list[str]:
	"""The customary wording of the flat-rate regime.

	Not imposed by any statute, but universally used. `RF19` and `N2.2` stay XML
	fields: irrelevant on the PDF, relevant to the Sistema TS.
	"""
	righe = [
		"Operazione senza applicazione dell'IVA ai sensi dell'art. 1, commi da 54 a 89, "
		"della L. 190/2014 - regime forfettario."
	]
	if includi_ritenuta:
		righe.append(
			"Operazione non soggetta a ritenuta d'acconto ai sensi dell'art. 1, comma 67, della L. 190/2014."
		)
	return righe


def bollo_virtuale(
	data_documento: date,
	numero_autorizzazione: str | None,
	data_autorizzazione: date | None,
	ufficio: str | None,
	importo: Decimal = Decimal("2.00"),
) -> str:
	"""Wording for a stamp duty settled virtually.

	The law imposes no formula, **but the authorisation number and date are
	mandatory**: the documents "must bear a clearly legible statement indicating the
	means of payment of the duty and the details of the relevant authorisation".
	Wording without those details does not satisfy the rule.
	"""
	if not numero_autorizzazione or not data_autorizzazione:
		raise ValueError(
			"virtual stamp duty without the authorisation details: number and date are mandatory "
			"in the wording (art. 15 DPR 642/72). Until the authorisation has been issued, the "
			"document goes out with a physical stamp on the original"
		)
	sede = f", Direzione Provinciale di {ufficio}" if ufficio else ""
	return (
		f"Imposta di bollo di EUR {importo:.2f} assolta in modo virtuale ai sensi dell'"
		f"{BOLLO_VIRTUALE.testo(data_documento)} - Autorizzazione dell'Agenzia delle Entrate"
		f"{sede}, n. {numero_autorizzazione} del {data_autorizzazione.strftime('%d/%m/%Y')}."
	)


def bollo_su_originale(
	identificativo: str | None,
	data_contrassegno: date | None,
	data_documento: date,
	importo: Decimal = Decimal("2.00"),
) -> str:
	"""Wording for the physical stamp applied to the paper original.

	Settled practice, **not codified in any Agenzia document**: it is treated as
	such. The stamp's date has to be the same as or earlier than the invoice date.
	"""
	if identificativo and data_contrassegno:
		if data_contrassegno > data_documento:
			raise ValueError(
				f"the stamp is dated {data_contrassegno.strftime('%d/%m/%Y')}, later than the "
				f"invoice of {data_documento.strftime('%d/%m/%Y')}: it must be of the same date "
				"or earlier"
			)
		return (
			f"Imposta di bollo di EUR {importo:.2f} assolta sull'originale - contrassegno "
			f"n. {identificativo} del {data_contrassegno.strftime('%d/%m/%Y')}."
		)
	return (
		f"Imposta di bollo di EUR {importo:.2f} assolta sull'originale cartaceo, conservato presso lo studio."
	)


def riaddebito_bollo() -> str:
	"""The re-charge is **an integral part of the compensation** (Risposta AdE 428/2022).

	It is not an art. 15 advance and it is not "outside VAT": it follows the regime
	of the service, so on a healthcare invoice it is exempt under art. 10 n. 18.
	"""
	return "Recupero imposta di bollo"


def contributo_integrativo(sigla: str, percentuale: Decimal) -> str:
	"""The levy line. The contributo integrativo **has to be shown on the invoice**
	(art. 8, c. 3, D.Lgs. 103/1996) and it enters the VAT base."""
	return f"Contributo integrativo {sigla.upper()} {percentuale:.0f}%"


def rivalsa_inps(percentuale: Decimal = Decimal("4")) -> str:
	"""The INPS rivalsa is **optional** and, unlike the contributo integrativo, it
	counts towards the professional's income and is subject to the withholding."""
	return f"Rivalsa contributo previdenziale INPS {percentuale:.0f}%"


def ritenuta_acconto(
	data_documento: date, aliquota: Decimal = Decimal("20"), importo: Decimal | None = None
) -> str:
	"""Wording for the withholding on self-employment income."""
	quota = f" - EUR {importo:.2f}" if importo is not None else ""
	return (
		f"Ritenuta d'acconto {aliquota:.0f}% ai sensi dell'{RITENUTA_ACCONTO.testo(data_documento)}{quota}."
	)


def niente_ritenuta() -> str:
	"""Towards a natural person there is **never** a withholding: they are not a
	withholding agent (art. 23, c. 1, DPR 600/73). No wording is required - this
	exists only for templates that ask for it explicitly."""
	return (
		"Operazione non soggetta a ritenuta d'acconto: il committente non riveste la "
		"qualifica di sostituto d'imposta."
	)


def inversione_contabile(natura: str | None = None) -> str:
	"""Reverse charge: the client settles the tax, the invoice carries no VAT."""
	from .codici import DESCRIZIONE_NATURA

	dettaglio = DESCRIZIONE_NATURA.get(natura or "", "")
	coda = f" ({dettaglio})" if dettaglio else ""
	return f"Inversione contabile - operazione soggetta a reverse charge{coda}."


def scissione_pagamenti(data_documento: date) -> str:
	"""Split payment: the VAT is shown but paid to the Treasury by the client."""
	return (
		"Scissione dei pagamenti ai sensi dell'"
		f"{SPLIT_PAYMENT.testo(data_documento)}: IVA versata dal committente."
	)


def fuori_campo_territoriale(data_documento: date) -> str:
	"""Cross-border B2B service: outside the scope of Italian VAT."""
	return (
		f"Operazione non soggetta ad IVA ai sensi dell'{FUORI_CAMPO_TERRITORIALE.testo(data_documento)} "
		"- inversione contabile a carico del committente."
	)


def anticipazione(data_documento: date) -> str:
	"""Advances in the client's name and on the client's behalf: outside the base."""
	return (
		"Somme escluse dalla base imponibile ai sensi dell'"
		f"{ANTICIPAZIONI.testo(data_documento)} - anticipazioni in nome e per conto del cliente."
	)


def opposizione() -> str:
	"""The opposition annotation on the fiscal document.

	**Not optional**: art. 3, c. 2, DM 31/7/2015 has the citizen ask orally for "the
	opposition to be annotated on the fiscal document", and the information "must be
	kept by the doctor too". How to word it is a choice, and it is kept **neutral**:
	a reference to exercising the opposition for pre-filled-return purposes, nothing
	else. Anything more descriptive turns the invoice into a disclosure.
	"""
	return (
		"Il soggetto ha manifestato opposizione all'utilizzo dei dati della presente spesa ai "
		"fini della dichiarazione dei redditi precompilata."
	)


def pagamento(codice: str | None, tracciato: bool | None) -> str:
	from .codici import DESCRIZIONE_PAGAMENTO

	etichetta = DESCRIZIONE_PAGAMENTO.get(codice or "", codice or "")
	testo = f"Modalita' di pagamento: {etichetta}."
	if tracciato is False:
		testo += " Pagamento non tracciabile: la spesa non da' diritto alla detrazione del 19%."
	return testo


def duplice_esemplare(copia: int, totale: int = 2) -> str:
	"""A paper invoice is drawn up **in duplicate**, one copy of which is handed or
	sent to the client (art. 21, c. 4)."""
	return "Originale" if copia == 1 else f"Copia per il cliente ({copia} di {totale})"


def conservazione_elettronica() -> str:
	"""The wording of the electronic-invoice-outside-the-SdI configuration.

	Circolare 18/E 2014: a document issued in electronic form has to be kept in
	electronic form, and that duty starts on day one - not when somebody remembers.
	"""
	return "Documento informatico emesso e conservato ai sensi del D.M. 17 giugno 2014 e del D.Lgs. 82/2005."
