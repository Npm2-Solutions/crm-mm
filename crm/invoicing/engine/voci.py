# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Every code invoicing asks somebody to choose, said in words.

A fiscal code is a wire format, not a word: RF19, N2.2, TC21 and RT01 mean
something to the SdI and nothing to whoever is setting up a practice. This is the
one place that says what each choice is, when it applies, and whether a healthcare
practice ever meets it.

Two profiles:

* `GENERALE`: everything the specification admits, the common choices first;
* `SANITARIO`: what a healthcare practice can meet. With the clinic on, it is the
  only one offered: a medical centre has no use for the regime of salt and tobacco
  or for the reverse charge on scrap metal, and showing them is how somebody picks
  the wrong one.

A value already stored is always offered, whatever the profile, so a choice made
before never disappears from its own field.

The words are English msgids, translated where they are handed to a screen
(`crm/locale/it.po`). Pure Python, no Frappe: what a code means is checked by a
test, not by somebody reading a screen.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

GENERALE = "generale"
SANITARIO = "sanitario"


@dataclass(frozen=True)
class Voce:
	"""One choice: its stored value, its name and one line on when it applies."""

	valore: str
	etichetta: str
	spiegazione: str = ""
	#: A healthcare practice meets it: offered in the `SANITARIO` profile.
	sanita: bool = False


def _v(valore: str, etichetta: str, spiegazione: str = "", *, sanita: bool = False) -> Voce:
	return Voce(valore, etichetta, spiegazione, sanita)


# ------------------------------------------------------------------ the company

REGIME_FISCALE = (
	_v(
		"RF01",
		"Ordinary regime",
		"VAT is charged, or the exemption is stated, as the law says: the usual regime of a company or a professional.",
		sanita=True,
	),
	_v(
		"RF19",
		"Flat-rate regime (forfettario)",
		"No VAT on the invoice (L. 190/2014), for who has chosen it, with revenue up to EUR 85,000.",
		sanita=True,
	),
	_v(
		"RF02",
		"Minimum taxpayers (minimi)",
		"The old regime of L. 244/2007, only for who still has it.",
		sanita=True,
	),
	_v("RF17", "VAT on a cash basis", "VAT is due when the client pays (art. 32-bis D.L. 83/2012)."),
	_v("RF16", "VAT on a cash basis, public administration", "Art. 6, c. 5, DPR 633/72."),
	_v("RF04", "Agriculture and fishing", "Artt. 34 and 34-bis DPR 633/72."),
	_v("RF05", "Salt and tobacco", "Art. 74, c. 1, DPR 633/72."),
	_v("RF06", "Matches", "Art. 74, c. 1, DPR 633/72."),
	_v("RF07", "Publishing", "Art. 74, c. 1, DPR 633/72."),
	_v("RF08", "Public telephony", "Art. 74, c. 1, DPR 633/72."),
	_v("RF09", "Transport and parking tickets", "Art. 74, c. 1, DPR 633/72."),
	_v("RF10", "Entertainment and games", "The tariff annexed to DPR 640/72."),
	_v("RF11", "Travel agencies", "Art. 74-ter DPR 633/72."),
	_v("RF12", "Farm holidays (agriturismo)", "Art. 5, c. 2, L. 413/91."),
	_v("RF13", "Door-to-door sales", "Art. 25-bis, c. 6, DPR 600/73."),
	_v("RF14", "Second-hand goods, art and antiques", "Art. 36 D.L. 41/95."),
	_v("RF15", "Art auctions", "Art. 40-bis D.L. 41/95."),
	_v("RF18", "Another special regime", "A regime that is not in this list."),
	_v("RF20", "Cross-border VAT franchise", "Directive (EU) 2020/285, for who is enrolled in it."),
)

SOCIO_UNICO = (
	_v("SU", "Single shareholder", "The company has one shareholder.", sanita=True),
	_v("SM", "Several shareholders", "", sanita=True),
)

STATO_LIQUIDAZIONE = (
	_v("LN", "Not in liquidation", "", sanita=True),
	_v("LS", "In liquidation", "", sanita=True),
)

# ------------------------------------------------------------------ VAT

NATURA = (
	_v(
		"N4",
		"Exempt (art. 10)",
		"Healthcare services of diagnosis, care and rehabilitation, and the other operations of art. 10 DPR 633/72.",
		sanita=True,
	),
	_v(
		"N2.2",
		"Not subject: flat-rate or minimum regime",
		"Who invoices is in the flat-rate (forfettario) or minimum regime, or in another case outside VAT.",
		sanita=True,
	),
	_v(
		"N1",
		"Excluded: advances re-charged (art. 15)",
		"Amounts paid in the client's name and on their behalf, re-charged exactly as paid.",
		sanita=True,
	),
	_v(
		"N2.1",
		"Not subject: taxed abroad",
		"A service whose VAT is due in another country (artt. 7-7-septies).",
	),
	_v("N3.1", "Not taxable: exports", "Goods sent outside the European Union."),
	_v("N3.2", "Not taxable: supplies within the EU", "Goods sold to a VAT subject of another member state."),
	_v("N3.3", "Not taxable: supplies to San Marino", ""),
	_v(
		"N3.4",
		"Not taxable: operations treated as exports",
		"International transport and the services tied to it.",
	),
	_v(
		"N3.5",
		"Not taxable: declaration of intent",
		"A habitual exporter has sent its declaration of intent.",
	),
	_v(
		"N3.6",
		"Not taxable: other cases",
		"Other non-taxable operations that do not count towards the ceiling.",
	),
	_v("N5", "Margin regime", "Second-hand goods, art and travel agencies: VAT is not shown on the invoice."),
	_v("N6.1", "Reverse charge: scrap and recovered materials", "The client pays the VAT, not who invoices."),
	_v(
		"N6.2",
		"Reverse charge: gold and silver, used jewellery",
		"Gold and silver under L. 7/2000 and used jewellery sold to dealers: the client pays the VAT, not who invoices.",
	),
	_v("N6.3", "Reverse charge: building subcontracting", "The client pays the VAT, not who invoices."),
	_v("N6.4", "Reverse charge: sale of buildings", "The client pays the VAT, not who invoices."),
	_v("N6.5", "Reverse charge: mobile phones", "The client pays the VAT, not who invoices."),
	_v("N6.6", "Reverse charge: electronic products", "The client pays the VAT, not who invoices."),
	_v("N6.7", "Reverse charge: building and related services", "The client pays the VAT, not who invoices."),
	_v("N6.8", "Reverse charge: energy sector", "The client pays the VAT, not who invoices."),
	_v("N6.9", "Reverse charge: other cases", "The client pays the VAT, not who invoices."),
	_v("N7", "VAT paid in another EU state", "Distance sales and digital services declared through the OSS."),
)

# ------------------------------------------------------------------ the document

TIPO_DOCUMENTO = (
	_v("TD01", "Invoice", "The usual document.", sanita=True),
	_v(
		"TD04",
		"Credit note",
		"Cancels or reduces an invoice already issued, which it refers to.",
		sanita=True,
	),
	_v("TD05", "Debit note", "Adds to an invoice already issued, which it refers to.", sanita=True),
	_v(
		"TD02",
		"Advance on an invoice",
		"A payment on account before the service is complete, for instance before a dental treatment.",
		sanita=True,
	),
	_v(
		"TD06",
		"Professional fee note (parcella)",
		"What a professional issues for their fee: it counts as an invoice.",
		sanita=True,
	),
	_v("TD03", "Advance on a professional fee note", "", sanita=True),
	_v("TD24", "Deferred invoice", "Groups the deliveries or services of a month, with their documents."),
	_v("TD25", "Deferred invoice, triangular sale", "Art. 21, c. 4, third period, lett. b)."),
	_v("TD16", "Reverse charge supplement", "Not issued to a client: it completes a purchase invoice."),
	_v("TD17", "Self-invoice: services bought abroad", "Not issued to a client: it completes a purchase."),
	_v("TD18", "Supplement: goods bought within the EU", "Not issued to a client: it completes a purchase."),
	_v("TD19", "Self-invoice: goods under art. 17, c. 2", "Not issued to a client: it completes a purchase."),
	_v(
		"TD20",
		"Self-invoice to regularise a purchase",
		"Art. 6, c. 9-bis, D.Lgs. 471/97 or art. 46, c. 5, D.L. 331/93. A supplier's missing invoice is TD29.",
	),
	_v("TD21", "Self-invoice for exceeding the ceiling", ""),
	_v("TD22", "Goods taken out of a VAT warehouse", ""),
	_v("TD23", "Goods taken out of a VAT warehouse, VAT paid", ""),
	_v("TD26", "Sale of depreciable assets", ""),
	_v("TD27", "Self-consumption or free supplies", ""),
	_v("TD28", "Purchases from San Marino with VAT", ""),
	_v(
		"TD29",
		"Report of a missing or irregular invoice",
		"Art. 6, c. 8, D.Lgs. 471/97: what the client tells the Agenzia when the supplier did not invoice.",
	),
)

# ------------------------------------------------------------------ payment

#: Traceable, or not: on a healthcare service the patient's 19% deduction depends on
#: it (art. 1, c. 679, L. 160/2019), so the line says it.
MODALITA_PAGAMENTO = (
	_v(
		"MP08",
		"Card or app",
		"Debit, credit or prepaid card at the POS, or a payment app: traceable.",
		sanita=True,
	),
	_v(
		"MP01",
		"Cash",
		"Not traceable: on a healthcare service the patient loses the 19% tax deduction.",
		sanita=True,
	),
	_v("MP05", "Bank transfer", "Traceable.", sanita=True),
	_v("MP02", "Cheque", "Traceable.", sanita=True),
	_v("MP03", "Banker's draft", "Traceable.", sanita=True),
	_v("MP19", "SEPA direct debit", "Traceable.", sanita=True),
	_v("MP20", "SEPA direct debit, CORE", "Traceable.", sanita=True),
	_v("MP21", "SEPA direct debit, B2B", "Between businesses."),
	_v("MP23", "PagoPA", "Payment to a public administration."),
	_v("MP12", "RIBA", "Bank receipt."),
	_v("MP13", "MAV", "Payment notice."),
	_v("MP07", "Bank slip", ""),
	_v("MP18", "Postal slip", ""),
	_v("MP09", "RID", "Interbank direct debit."),
	_v("MP10", "RID for utilities", ""),
	_v("MP11", "Fast RID", ""),
	_v("MP16", "Bank domiciliation", ""),
	_v("MP17", "Postal domiciliation", ""),
	_v("MP06", "Promissory note", ""),
	_v("MP04", "Cash at the Treasury", "Payments to a public administration."),
	_v("MP14", "Treasury receipt", ""),
	_v("MP15", "Transfer between special accounts", ""),
	_v("MP22", "Deduction from sums already collected", ""),
)

CONDIZIONI_PAGAMENTO = (
	_v("TP02", "In one payment", "", sanita=True),
	_v("TP01", "In instalments", "", sanita=True),
	_v("TP03", "In advance", "Paid before the service, on account.", sanita=True),
)

# ------------------------------------------------------------------ fund and withholding

CASSA = (
	_v(
		"TC09",
		"ENPAM: doctors and dentists",
		"Nothing is charged to the patient: ENPAM puts no contribution on the invoice.",
		sanita=True,
	),
	_v("TC21", "ENPAP: psychologists", "A 2% contribution on the fee, shown on the invoice.", sanita=True),
	_v(
		"TC20",
		"ENPAPI: nurses and health assistants",
		"A 4% contribution on the fee, shown on the invoice.",
		sanita=True,
	),
	_v(
		"TC19",
		"ENPAB: biologists and nutritionists",
		"A 4% contribution on the fee, shown on the invoice.",
		sanita=True,
	),
	_v("TC11", "ENPAV: vets", "A 2% contribution on the fee, shown on the invoice.", sanita=True),
	_v("TC10", "ENPAF: pharmacists", "", sanita=True),
	_v(
		"TC22",
		"INPS, separate management",
		"The optional 4% re-charge of a professional without a fund of their own, such as a physiotherapist or a speech therapist.",
		sanita=True,
	),
	_v("TC01", "Cassa Forense: lawyers", "A 4% contribution, shown on the invoice."),
	_v("TC02", "Accountants' fund", "A 4% contribution, shown on the invoice."),
	_v("TC03", "Surveyors' fund", ""),
	_v("TC04", "Inarcassa: engineers and architects", "A 4% contribution, shown on the invoice."),
	_v("TC05", "Notaries' fund", ""),
	_v("TC06", "Bookkeepers' fund", ""),
	_v("TC07", "ENASARCO: sales agents", ""),
	_v("TC08", "ENPACL: labour consultants", ""),
	_v(
		"TC12",
		"ENPAIA: agriculture employees",
		"Agrotecnici and periti agrari have their own funds inside it.",
	),
	_v("TC13", "Fund of forwarding and maritime agencies' employees", ""),
	_v("TC14", "INPGI: journalists", ""),
	_v("TC15", "ONAOSI: orphans of healthcare workers", ""),
	_v("TC16", "CASAGIT: journalists' health fund", ""),
	_v("TC17", "EPPI: industrial experts", ""),
	_v("TC18", "EPAP: agronomists, geologists, chemists, actuaries", ""),
)

TIPO_RITENUTA = (
	_v(
		"RT01",
		"Withholding tax, natural person",
		"The 20% withholding on a professional's fee, when the client is a company or another professional.",
		sanita=True,
	),
	_v(
		"RT02",
		"Withholding tax, legal person",
		"For an association of professionals or a professional company (STP).",
		sanita=True,
	),
	_v("RT03", "INPS contribution", "Withheld as a social security contribution."),
	_v("RT04", "ENASARCO contribution", ""),
	_v("RT05", "ENPAM contribution", ""),
	_v("RT06", "Another social security contribution", ""),
)

#: The Modello 770 reason of a withholding. A closed list: the wrong letter misfiles
#: the certification the client sends.
CAUSALE_PAGAMENTO = (
	_v(
		"A",
		"Professional work",
		"Fees for work done in the habitual exercise of a profession: the usual case.",
		sanita=True,
	),
	_v("M", "Occasional self-employment", "Work that is not habitual.", sanita=True),
	_v(
		"M2",
		"Occasional work, ENPAPI",
		"Occasional work for which enrolment in the ENPAPI separate management is due.",
		sanita=True,
	),
	_v("O", "Occasional work, no separate management", "Occasional work with no enrolment due."),
	_v(
		"B", "Works of the mind, by their author", "Copyright and patents used by the author or the inventor."
	),
	_v("L", "Works of the mind, by others", "Copyright used by somebody other than the author."),
	_v("L1", "Works of the mind, bought", "Copyright acquired for a consideration."),
	_v(
		"C",
		"Participation agreements",
		"Profits of a participation agreement where only work is contributed.",
	),
	_v("D", "Founding members' profits", "Profits of the promoting and founding members of a company."),
	_v("E", "Protest of bills", "By municipal secretaries."),
	_v("G", "End of a professional sporting career", ""),
	_v("H", "End of an agency relationship", ""),
	_v("I", "End of notarial functions", ""),
	_v("M1", "Obligations to do, not to do or allow", ""),
	_v("N", "Amateur sport allowances", "Travel allowances, refunds and prizes in amateur sport."),
	_v("O1", "Obligations to do, no separate management", ""),
	_v("P", "Equipment hired from non-residents", ""),
	_v("Q", "Commissions, single-firm agent", ""),
	_v("R", "Commissions, multi-firm agent", ""),
	_v("S", "Commissions to a commission agent", ""),
	_v("T", "Commissions to a broker", ""),
	_v("U", "Commissions to a business finder", ""),
	_v("V", "Door-to-door sales commissions", ""),
	_v("V1", "Occasional commercial activity", ""),
	_v("W", "Contract work for a condominium", "Art. 25-ter DPR 600/73: the 4% withholding."),
	_v("ZO", "Another reason", "A reason that is not in this list."),
)

# ------------------------------------------------------------------ stamp duty and keeping

MODALITA_BOLLO = (
	_v(
		"su_originale",
		"Stamp on the paper original",
		"A EUR 2 stamp (marca da bollo) on the copy you hand over, for exempt invoices over EUR 77.47.",
		sanita=True,
	),
	_v(
		"virtuale",
		"Virtual stamp duty, authorised",
		"Paid to the Agenzia under an authorisation (art. 15 DPR 642/72): its number and date go on every invoice.",
		sanita=True,
	),
	_v("non_dovuto", "Never due", "No exempt invoice of yours ever goes over EUR 77.47.", sanita=True),
)

MODALITA_DOCUMENTO = (
	_v(
		"analogico_con_copia",
		"On paper, with a copy",
		"The invoices that do not go through the SdI are printed, and the paper original is kept, in two copies: nobody to pay for preservation.",
		sanita=True,
	),
	_v(
		"elettronica_extra_sdi",
		"Electronic, outside the SdI",
		"The PDF is the original: a paid preservation service has to keep it for ten years.",
		sanita=True,
	),
)

# ------------------------------------------------------------------ numbering

#: How an invoice's number reads: the year, the series and the counter, in the
#: order chosen. Every one fits the Sistema TS's twenty characters with a six-digit
#: counter and the test series (`numerazione.valida_formato`): a picker, so that a
#: centre cannot write one that the Sistema TS refuses in January.
FORMATO_NUMERO = (
	_v("{anno}/{serie}/{numero}", "2026/S/15", "Year, series, number: the most common.", sanita=True),
	_v("{serie}/{numero}/{anno}", "S/15/2026", "Series, number, year.", sanita=True),
	_v("{numero}/{serie}/{anno}", "15/S/2026", "Number, series, year.", sanita=True),
	_v("{anno}-{serie}-{numero}", "2026-S-15", "Year, series and number, with dashes.", sanita=True),
)

CONSERVAZIONE_SDI = (
	_v(
		"agenzia_entrate",
		"Agenzia delle Entrate, free",
		"Join once in Fatture e Corrispettivi: it keeps the invoices that pass through the SdI for fifteen years.",
		sanita=True,
	),
	_v("provider", "The provider", "The accredited provider that transmits keeps them too.", sanita=True),
	_v("altro", "Another service", "Name it in the reference.", sanita=True),
)

CONSERVAZIONE_LOCALE = (
	_v("provider", "The provider", "", sanita=True),
	_v("altro", "Another service", "Name it in the reference.", sanita=True),
)

# ------------------------------------------------------------------ transmission

CANALE_SDI = (
	_v(
		"provider",
		"Itala, automatic",
		"The accredited intermediary the invoices go through: it sends them and reads the notices that come back.",
		sanita=True,
	),
	_v("pec", "Your PEC mailbox", "Free, but somebody has to read the notices that come back.", sanita=True),
	_v(
		"export",
		"Download and upload it yourself",
		"The file is prepared here: you upload it in Fatture e Corrispettivi.",
		sanita=True,
	),
)

FLUSSO_SDI = (
	_v("uscita", "Outgoing only", "The invoices you issue.", sanita=True),
	_v("entrambi", "Outgoing and incoming", "The purchase invoices too, read here.", sanita=True),
)

AMBIENTE = (
	_v("sandbox", "In test", "The invoices are numbered PROVA and reach nobody.", sanita=True),
	_v("production", "Live", "Every invoice is real.", sanita=True),
)

# ------------------------------------------------------------------ qualifications and clients

REGOLA_SDI = (
	_v(
		"vietato",
		"Never through the SdI",
		"A healthcare service to a patient: a PDF to the patient, the expense to the Sistema TS.",
		sanita=True,
	),
	_v(
		"obbligatorio", "Always through the SdI", "An electronic invoice, whoever the client is.", sanita=True
	),
	_v(
		"ammesso",
		"Through the SdI when the client is a business",
		"Towards a company or a professional, as a doctor billing an employer.",
		sanita=True,
	),
)

CATEGORIA_QUALIFICA = (
	_v("sanitaria", "Health profession", "", sanita=True),
	_v("ordinistica", "Profession with a register", "Lawyer, accountant, engineer, architect..."),
	_v("non_ordinistica", "Profession without a register", "Consultant, trainer, developer..."),
	_v("impresa", "Company", ""),
)

#: Decided by the classification, never chosen: shown, so in words too.
CANALE_DOCUMENTO = (
	_v("sdi", "Electronic invoice", "Sent through the SdI.", sanita=True),
	_v(
		"pdf_ts",
		"PDF + Sistema TS",
		"A PDF to the patient, the expense to the Sistema TS: never through the SdI.",
		sanita=True,
	),
	_v("pdf_solo", "PDF only", "A PDF, and nothing transmitted.", sanita=True),
)

#: Derived from the payment method: the patient's deduction depends on it.
PAGAMENTO_TRACCIATO = (
	_v("yes", "Traced", "Card, bank transfer, cheque: a traceable method.", sanita=True),
	_v("no", "Not traced", "Cash, even only in part.", sanita=True),
	_v("not_applicable", "Not applicable", "", sanita=True),
)

TIPO_DESTINATARIO = (
	_v("persona_fisica", "Private person", "A patient or a private client, with no VAT number.", sanita=True),
	_v("soggetto_iva", "Company or professional", "Has a VAT number.", sanita=True),
	_v("pubblica_amministrazione", "Public administration", "", sanita=True),
	_v("estero", "Abroad", "A client outside Italy.", sanita=True),
)

_FAMIGLIE: dict[str, tuple[Voce, ...]] = {
	"regime_fiscale": REGIME_FISCALE,
	"socio_unico": SOCIO_UNICO,
	"stato_liquidazione": STATO_LIQUIDAZIONE,
	"natura": NATURA,
	"tipo_documento": TIPO_DOCUMENTO,
	"modalita_pagamento": MODALITA_PAGAMENTO,
	"condizioni_pagamento": CONDIZIONI_PAGAMENTO,
	"cassa": CASSA,
	"tipo_ritenuta": TIPO_RITENUTA,
	"causale_pagamento": CAUSALE_PAGAMENTO,
	"modalita_bollo": MODALITA_BOLLO,
	"modalita_documento": MODALITA_DOCUMENTO,
	"formato_numero": FORMATO_NUMERO,
	"conservazione_sdi": CONSERVAZIONE_SDI,
	"conservazione_locale": CONSERVAZIONE_LOCALE,
	"canale_sdi": CANALE_SDI,
	"flusso_sdi": FLUSSO_SDI,
	"ambiente": AMBIENTE,
	"regola_sdi": REGOLA_SDI,
	"categoria_qualifica": CATEGORIA_QUALIFICA,
	"tipo_destinatario": TIPO_DESTINATARIO,
	"canale_documento": CANALE_DOCUMENTO,
	"pagamento_tracciato": PAGAMENTO_TRACCIATO,
}


def registra(famiglia: str, voci_: tuple[Voce, ...]) -> None:
	"""A module that adds a vocabulary of its own (the Sistema TS) registers it here:
	invoicing hands it to the screens without knowing what it says."""
	_FAMIGLIE[famiglia] = tuple(voci_)


def famiglie() -> list[str]:
	return list(_FAMIGLIE)


def tutte(famiglia: str) -> tuple[Voce, ...]:
	"""Every choice of a family, in the order they are offered. Unknown: none."""
	return _FAMIGLIE.get(famiglia, ())


def voci(
	famiglia: str,
	profilo: str = GENERALE,
	attuale: str | Iterable[str] | None = None,
	ammessi: frozenset[str] | set[str] | None = None,
) -> list[Voce]:
	"""The choices of a family for a profile, in order.

	`ammessi` narrows them further where a rule decides (the expense types an issuer
	may use). The value already stored is always among them, even when the profile
	or the rule would leave it out: a choice made before never vanishes from its own
	field, it just stops being suggested. A table's column passes the values of all
	its rows.
	"""
	scelte = [
		voce
		for voce in tutte(famiglia)
		if (profilo != SANITARIO or voce.sanita) and (ammessi is None or voce.valore in ammessi)
	]
	for valore in [attuale] if isinstance(attuale, str) else attuale or ():
		if valore and all(voce.valore != valore for voce in scelte):
			trovata = next((voce for voce in tutte(famiglia) if voce.valore == valore), None)
			scelte.append(trovata or Voce(valore, valore))
	return scelte


def etichetta(famiglia: str, valore: str | None) -> str:
	"""The name of a stored value, or the value itself when nobody named it."""
	if not valore:
		return ""
	return next((voce.etichetta for voce in tutte(famiglia) if voce.valore == valore), valore)
