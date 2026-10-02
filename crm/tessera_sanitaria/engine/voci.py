# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The Sistema TS choices, said in words.

Registered into invoicing's vocabulary (`crm.invoicing.engine.voci`) when this
module loads: invoicing hands them to the screens without knowing what an expense
type is.

The expense types follow the Sistema TS web service specification (730 - Spese
Sanitarie, WS sincrono v1.3, 20/12/2020, Tabella 4): the names are short, the line
under each is the specification's own description. Which of them an issuer may use
is not decided here but by its category (`codici.TIPI_SPESA_PER_SOGGETTO`).
"""

from __future__ import annotations

from crm.invoicing.engine.messaggi import Nome
from crm.invoicing.engine.voci import Voce


def _v(valore: str, etichetta: str, spiegazione: str = "", *, sanita: bool = True) -> Voce:
	return Voce(valore, etichetta, spiegazione, sanita)


#: In the order a medical centre meets them.
TIPO_SPESA = (
	_v(
		"SR",
		"Visits and specialist services",
		"General and specialist visits, diagnostic and instrumental tests, surgery other than aesthetic, medical certificates, hospital stays net of comfort.",
	),
	_v(
		"SP",
		"Health professional's services",
		"Services of a health profession (physiotherapist, psychologist, nurse, dietitian...) invoiced in their own name.",
	),
	_v(
		"IC",
		"Aesthetic surgery and medicine",
		"Aesthetic surgery and aesthetic medicine, outpatient or in hospital: not a deductible healthcare expense.",
	),
	_v(
		"AA",
		"Other expenses",
		"What is not a deductible healthcare expense, or a share the patient did not bear.",
	),
	_v(
		"TK",
		"Ticket",
		"Co-payment for public healthcare: fixed share or difference from the reference price, emergency room, direct access.",
	),
	_v(
		"AS",
		"ECG, spirometry, Holter and similar tests",
		"ECG, spirometry, blood pressure and heart Holter, glycaemia, cholesterol and triglyceride tests, blood pressure, pharmacy services and similar.",
	),
	_v("PI", "Prosthetic and supplementary care", ""),
	_v("CT", "Thermal cures", ""),
	_v("AD", "Purchase or rental of a CE medical device", ""),
	_v("FC", "Medicines and CE medical devices", "Medicines, homeopathic too, and CE medical devices."),
	_v("FV", "Veterinary medicines", ""),
	_v("SV", "Veterinary expenses", ""),
)

FLAG_TIPO_SPESA = (
	_v("1", "Emergency room ticket", "Only with the Ticket expense type."),
	_v("2", "Intramoenia visit", "Only with Visits and specialist services."),
)

SOGGETTO_INVIANTE = (
	_v(
		"professionista_sanitario",
		"Health professional, in their own name",
		"Physiotherapist, psychologist, nurse, dietitian, speech therapist...: every service goes to the Sistema TS as a health professional's service.",
	),
	_v(
		"medico_odontoiatra",
		"Doctor or dentist, in their own name",
		"Visits and specialist services, aesthetic medicine, other expenses.",
	),
	_v(
		"struttura_autorizzata",
		"Healthcare facility authorised by the Region",
		"A clinic or practice authorised under art. 8-ter D.Lgs. 502/1992: it needs the Region, ASL and facility codes.",
	),
	_v(
		"struttura_accreditata",
		"Facility accredited with the national health service",
		"Public or private, accredited with the SSN.",
	),
	_v("veterinario", "Vet", ""),
	_v("farmacia", "Pharmacy", ""),
	_v("parafarmacia", "Para-pharmacy", ""),
	_v("ottico", "Optician", ""),
	_v("non_sanitario", "Not healthcare", "Reports nothing to the Sistema TS.", sanita=False),
)

MODALITA_INVIO = (
	_v(
		"credenziali_studio",
		"With the centre's Sistema TS credentials",
		"Every invoice is reported the same day, at no cost per document: the recommended way.",
	),
	_v(
		"intermediario",
		"Through the accountant (Entratel)",
		"When the accountant holds a mandate to send on the centre's behalf.",
	),
	_v("provider", "Through the provider", "Under the accredited provider's own accreditation."),
	_v(
		"export",
		"Download the file and upload it",
		"You upload it yourself on the Sistema TS portal, by 31 January.",
	),
)

STATO_DELEGA = (
	_v("sconosciuta", "Not known yet", "The first report finds it out."),
	_v("assente", "No mandate", "The centre reports in its own name."),
	_v(
		"presente",
		"Mandate active",
		"The accountant holds a mandate: reports in the centre's own name are refused.",
	),
	_v("non_sondabile", "Cannot be checked", ""),
)

OPERAZIONE = (
	_v("I", "New expense", ""),
	_v("V", "Correction", "Corrects an expense already reported."),
	_v("R", "Refund", "Money given back to the patient."),
	_v("C", "Cancellation", "Removes an expense reported by mistake."),
)

FAMIGLIE = {
	"tipo_spesa": TIPO_SPESA,
	"flag_tipo_spesa": FLAG_TIPO_SPESA,
	"soggetto_inviante": SOGGETTO_INVIANTE,
	"modalita_invio_ts": MODALITA_INVIO,
	"stato_delega": STATO_DELEGA,
	"operazione_ts": OPERAZIONE,
}


def nome(famiglia: tuple[Voce, ...], valore: str | None) -> Nome:
	"""A code of a family by its name, for a sentence (`Messaggio`): translated where
	the sentence is read; a code nobody named stays itself."""
	voce = next((voce for voce in famiglia if voce.valore == valore), None)
	return Nome(voce.etichetta if voce else (valore or ""))


def nomi(famiglia: tuple[Voce, ...], valori) -> tuple[Nome, ...]:
	"""Several codes of a family by their names, in the order the family offers them."""
	scelti = set(valori)
	noti = [voce.valore for voce in famiglia]
	ordinati = [valore for valore in noti if valore in scelti] + sorted(scelti - set(noti))
	return tuple(nome(famiglia, valore) for valore in ordinati)


def registra() -> None:
	from crm.invoicing.engine import voci

	for nome, voci_ in FAMIGLIE.items():
		voci.registra(nome, voci_)
