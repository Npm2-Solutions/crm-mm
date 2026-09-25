# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The Sistema Tessera Sanitaria vocabulary.

Split out of the invoicing tables on purpose. A plumber's invoice needs
`TipoDocumento` and `Natura`; it has no `tipoSpesa`, no `soggetto inviante` and no
opinion about a delega. Keeping the two sets in one file made every one of these
names look like something invoicing had to know about, and it does not.

Nothing here is imported by `crm.invoicing`. That direction is enforced by a test,
because a boundary nobody checks is a boundary that lasts a month.
"""

from __future__ import annotations

from crm.invoicing.engine.codici import StrEnum


class StatoTS(StrEnum):
	NON_APPLICABILE = "non_applicabile"
	DA_INVIARE = "da_inviare"
	PRONTO_EXPORT = "pronto_export"
	INVIATO = "inviato"
	ACCOLTO = "accolto"
	SCARTATO = "scartato"
	ANNULLATO = "annullato"


class ModalitaInvioTS(StrEnum):
	"""Who transmits to the Sistema TS. **Everyone is born in `export`.**"""

	EXPORT = "export"
	CREDENZIALI_STUDIO = "credenziali_studio"
	INTERMEDIARIO = "intermediario"


class StatoDelega(StrEnum):
	"""The truth about the mandate is not asked for, it is probed with 105/106."""

	SCONOSCIUTA = "sconosciuta"
	ASSENTE = "assente"
	PRESENTE = "presente"
	NON_SONDABILE = "non_sondabile"


class OperazioneTS(StrEnum):
	INSERIMENTO = "I"
	VARIAZIONE = "V"
	RIMBORSO = "R"
	CANCELLAZIONE = "C"


# =========================================================== FatturaPA wire


class SoggettoInviante(StrEnum):
	"""The category of whoever issues the document - it decides the expense types."""

	MEDICO_ODONTOIATRA = "medico_odontoiatra"
	PROFESSIONISTA_SANITARIO = "professionista_sanitario"
	STRUTTURA_AUTORIZZATA = "struttura_autorizzata"
	STRUTTURA_ACCREDITATA = "struttura_accreditata"
	VETERINARIO = "veterinario"
	FARMACIA = "farmacia"
	PARAFARMACIA = "parafarmacia"
	OTTICO = "ottico"
	NON_SANITARIO = "non_sanitario"
	"""Anything that does not report to the Sistema TS at all."""


#: Expense types each sender category may use. Applying this matrix **at issue
#: time** is what keeps hundreds of rows from being rejected in January.
TIPI_SPESA_PER_SOGGETTO: dict[str, frozenset[str]] = {
	SoggettoInviante.MEDICO_ODONTOIATRA: frozenset({"SR", "IC", "AA"}),
	SoggettoInviante.PROFESSIONISTA_SANITARIO: frozenset({"SP"}),
	SoggettoInviante.STRUTTURA_AUTORIZZATA: frozenset({"SR", "CT", "PI", "IC", "AA"}),
	SoggettoInviante.STRUTTURA_ACCREDITATA: frozenset({"TK", "SR", "CT", "PI", "IC", "AA"}),
	SoggettoInviante.VETERINARIO: frozenset({"FV", "AA", "SV"}),
	SoggettoInviante.FARMACIA: frozenset({"TK", "FC", "FV", "AD", "AS", "PI", "AA"}),
	SoggettoInviante.PARAFARMACIA: frozenset({"FC", "FV", "AD", "AS", "PI", "AA"}),
	SoggettoInviante.OTTICO: frozenset({"AD", "AA"}),
	SoggettoInviante.NON_SANITARIO: frozenset(),
}

DESCRIZIONE_TIPO_SPESA: dict[str, str] = {
	"TK": "Ticket (quota fissa e/o di partecipazione al costo)",
	"FC": "Farmaco, anche omeopatico, e dispositivo medico CE",
	"FV": "Farmaco per uso veterinario",
	"AD": "Acquisto o affitto di dispositivo medico CE",
	"AS": "Spesa sanitaria relativa ad assistenza domiciliare integrata",
	"SR": "Spesa prestazione sanitaria: intramoenia",
	"CT": "Spesa per certificazione medica",
	"PI": "Spesa prestazione sanitaria: protesica e integrativa",
	"IC": "Spesa per dispositivi, chirurgia estetica e altre prestazioni",
	"AA": "Altre spese - quota NON a carico del contribuente o spesa non sanitaria",
	"SP": "Spesa prestazione sanitaria del professionista sanitario (DM 8/8/2018)",
	"SV": "Spesa veterinaria",
}

#: `flagTipoSpesa` is only admitted with these expense types.
FLAG_TIPO_SPESA_AMMESSO: dict[str, str] = {
	"1": "TK",
	"2": "SR",
}

#: Expense types for which `pagamentoTracciato` is not mandatory. Outside these -
#: and outside public or SSN-accredited facilities - the field has been mandatory
#: since 1/1/2020: without traceability the patient loses the deduction.
TIPI_SPESA_SENZA_TRACCIABILITA: frozenset[str] = frozenset({"TK", "FC", "AD", "FV"})

SOGGETTI_SENZA_TRACCIABILITA: frozenset[str] = frozenset({SoggettoInviante.STRUTTURA_ACCREDITATA})

#: Senders that the tracciato treats as natural persons: `codiceRegione`,
#: `codiceAsl` and `codiceSSA` are omitted and only `cfProprietario` is filled.
SOGGETTI_PERSONA_FISICA: frozenset[str] = frozenset(
	{
		SoggettoInviante.MEDICO_ODONTOIATRA,
		SoggettoInviante.PROFESSIONISTA_SANITARIO,
		SoggettoInviante.VETERINARIO,
	}
)

#: Senders that use the Codice Proprietario `codiceRegione-codiceAsl-codiceSSA`.
SOGGETTI_CON_CODICE_PROPRIETARIO: frozenset[str] = frozenset(
	{
		SoggettoInviante.STRUTTURA_AUTORIZZATA,
		SoggettoInviante.STRUTTURA_ACCREDITATA,
		SoggettoInviante.FARMACIA,
		SoggettoInviante.PARAFARMACIA,
		SoggettoInviante.OTTICO,
	}
)


class TipoDocumentoTS(StrEnum):
	"""`tipoDocumento` - it is *not* "invoice or correction"."""

	FATTURA = "F"
	DOCUMENTO_COMMERCIALE = "D"


class EsitoChiamata(StrEnum):
	ACCOLTO = "0"
	ERRORE_BLOCCANTE = "1"
	ACCOLTO_CON_SEGNALAZIONI = "2"


class TipoMessaggioTS(StrEnum):
	ERRORE = "E"
	WARNING = "W"
	STATISTICA = "S"


#: VAT natures the tracciato accepts. On `tipoDocumento=D` only the two-character
#: forms; on `F` the sub-codes are admitted too.
NATURE_IVA_DOCUMENTO_COMMERCIALE: frozenset[str] = frozenset({"N1", "N2", "N3", "N4", "N5", "N6"})
NATURE_IVA_FATTURA: frozenset[str] = frozenset(
	{
		"N1",
		"N2",
		"N2.1",
		"N2.2",
		"N3",
		"N3.1",
		"N3.2",
		"N3.3",
		"N3.4",
		"N3.5",
		"N3.6",
		"N4",
		"N5",
		"N6",
		"N6.1",
		"N6.2",
		"N6.3",
		"N6.4",
		"N6.5",
		"N6.6",
		"N6.7",
		"N6.8",
		"N6.9",
		"N7",
	}
)

#: The two codes that tell the truth about the Entratel mandate. Nobody has to be
#: asked: the first real document is sent in the practice's own name and the
#: answer says which world we are in.
CODICE_DELEGA_ASSENTE = "105"
"""Sent on behalf of, with no active mandate -> the mandate is NOT there."""

CODICE_DELEGA_PRESENTE = "106"
"""Sent in own name while a mandate is active -> the mandate IS there."""

#: Rejections that send the tenant back to `export` with an alert rather than a
#: retry: the last mile is broken, and invoicing must not stop for it.
CODICI_RETROCESSIONE: frozenset[str] = frozenset({"105", "106", "002", "003", "004", "005", "006"})

#: Transient conditions worth retrying.
CODICI_RITENTABILI: frozenset[str] = frozenset({"999", "500", "503"})

DESCRIZIONE_ESITO_TS: dict[str, str] = {
	"000": "Elaborazione conclusa correttamente",
	"002": "Certificato non valido o scaduto",
	"003": "Utenza non abilitata al servizio",
	"004": "Password scaduta",
	"005": "PINCODE errato o scaduto",
	"006": "Utenza revocata",
	"010": "Struttura del messaggio non conforme",
	"104": "Soggetto non abilitato per la categoria indicata",
	"105": "Invio per conto in assenza di delega attiva",
	"106": "Invio in proprio in presenza di delega attiva",
	"107": "Codice proprietario non congruente con il soggetto",
	"109": "Composizione del proprietario non ammessa per il soggetto",
	"110": "Periodo di riferimento non aperto",
}


def descrivi_esito(codice: str | None) -> str:
	if not codice:
		return ""
	return DESCRIZIONE_ESITO_TS.get(codice, f"Codice {codice}")


def tipi_spesa_ammessi(soggetto: str | None) -> frozenset[str]:
	"""Expense types admitted for a sender category.

	An unknown category returns the empty set on purpose: the caller then says
	"not determinable" instead of guessing a code that gets the row rejected.
	"""
	if not soggetto:
		return frozenset()
	return TIPI_SPESA_PER_SOGGETTO.get(soggetto, frozenset())
