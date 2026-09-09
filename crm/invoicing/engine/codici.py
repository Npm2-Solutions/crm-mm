"""Code tables: FatturaPA 1.2.2 and Sistema TS 730.

Two standards, one file, because they are consulted together and disagreeing
copies of the same table are how a January full of rejected rows starts.

The rule this module exists to enforce, and the one everybody gets wrong:
**`tipoSpesa` does not follow the service, it follows the register of whoever
issues the document.** The same session is `SR` when the doctor invoices it and
`SP` when the physiotherapist in the same practice does.

Sources: FatturaPA specifiche tecniche v1.9 (tracciato 1.2.2), Sistema TS kit
`kit730P_ver_20240214`, WS Sincrono v1.3 / WS Asincrono v2.5 del 20/12/2020,
DM 19 ottobre 2020, DM 31 luglio 2015.
"""

from __future__ import annotations

try:  # pragma: no cover - Python 3.11+
	from enum import StrEnum
except ImportError:  # pragma: no cover - Python 3.10
	from enum import Enum

	class StrEnum(str, Enum):
		def __str__(self) -> str:
			return str(self.value)


# =============================================================== domain enums


class TipoDestinatario(StrEnum):
	"""Who receives the document. It decides the channel before anything else."""

	PERSONA_FISICA = "persona_fisica"
	SOGGETTO_IVA = "soggetto_iva"
	PUBBLICA_AMMINISTRAZIONE = "pubblica_amministrazione"
	ESTERO = "estero"


class Canale(StrEnum):
	"""Where the document goes once it is issued."""

	SDI = "sdi"
	"""Electronic invoice through the Sistema di Interscambio."""

	PDF_TS = "pdf_ts"
	"""PDF to the patient plus the expense reported to the Sistema TS."""

	PDF_SOLO = "pdf_solo"
	"""PDF only: no SdI, no Sistema TS."""


class RegolaSdI(StrEnum):
	"""How the SdI channel behaves for a service towards a natural person."""

	VIETATO = "vietato"
	"""Structural ban since 2026 (D.Lgs. 12 giugno 2025 n. 81)."""

	OBBLIGATORIO = "obbligatorio"
	"""Not a healthcare service, or expressly ruled in: SdI applies."""

	AMMESSO = "ammesso"


class RegimeFiscale(StrEnum):
	"""FatturaPA `RegimeFiscale`. The value is the wire code."""

	ORDINARIO = "RF01"
	MINIMI = "RF02"
	AGRICOLTURA = "RF04"
	VENDITA_SALI_TABACCHI = "RF05"
	COMMERCIO_FIAMMIFERI = "RF06"
	EDITORIA = "RF07"
	TELEFONIA_PUBBLICA = "RF08"
	DOCUMENTI_TRASPORTO = "RF09"
	INTRATTENIMENTI = "RF10"
	AGENZIE_VIAGGI = "RF11"
	AGRITURISMO = "RF12"
	VENDITE_DOMICILIO = "RF13"
	BENI_USATI = "RF14"
	AGENZIE_ASTE = "RF15"
	IVA_PER_CASSA_PA = "RF16"
	IVA_PER_CASSA = "RF17"
	ALTRO = "RF18"
	FORFETTARIO = "RF19"


DESCRIZIONE_REGIME: dict[str, str] = {
	"RF01": "Regime ordinario",
	"RF02": "Contribuenti minimi (art. 1, c. 96-117, L. 244/2007)",
	"RF04": "Agricoltura e attivita' connesse e pesca (artt. 34 e 34-bis, DPR 633/72)",
	"RF05": "Vendita sali e tabacchi (art. 74, c. 1, DPR 633/72)",
	"RF06": "Commercio dei fiammiferi (art. 74, c. 1, DPR 633/72)",
	"RF07": "Editoria (art. 74, c. 1, DPR 633/72)",
	"RF08": "Gestione di servizi di telefonia pubblica (art. 74, c. 1, DPR 633/72)",
	"RF09": "Rivendita di documenti di trasporto pubblico e di sosta (art. 74, c. 1, DPR 633/72)",
	"RF10": "Intrattenimenti, giochi e altre attivita' (tariffa allegata al DPR 640/72)",
	"RF11": "Agenzie di viaggi e turismo (art. 74-ter, DPR 633/72)",
	"RF12": "Agriturismo (art. 5, c. 2, L. 413/91)",
	"RF13": "Vendite a domicilio (art. 25-bis, c. 6, DPR 600/73)",
	"RF14": "Rivendita di beni usati, oggetti d'arte, d'antiquariato (art. 36, D.L. 41/95)",
	"RF15": "Agenzie di vendite all'asta di oggetti d'arte (art. 40-bis, D.L. 41/95)",
	"RF16": "IVA per cassa P.A. (art. 6, c. 5, DPR 633/72)",
	"RF17": "IVA per cassa (art. 32-bis, D.L. 83/2012)",
	"RF18": "Altro",
	"RF19": "Regime forfettario (art. 1, c. 54-89, L. 190/2014)",
}


class TipoDocumento(StrEnum):
	"""FatturaPA `TipoDocumento`."""

	FATTURA = "TD01"
	ACCONTO_FATTURA = "TD02"
	ACCONTO_PARCELLA = "TD03"
	NOTA_CREDITO = "TD04"
	NOTA_DEBITO = "TD05"
	PARCELLA = "TD06"
	FATTURA_SEMPLIFICATA = "TD07"
	NOTA_CREDITO_SEMPLIFICATA = "TD08"
	NOTA_DEBITO_SEMPLIFICATA = "TD09"
	INTEGRAZIONE_REVERSE_CHARGE_INTERNO = "TD16"
	AUTOFATTURA_SERVIZI_ESTERO = "TD17"
	INTEGRAZIONE_BENI_INTRA = "TD18"
	INTEGRAZIONE_BENI_ART17 = "TD19"
	AUTOFATTURA_REGOLARIZZAZIONE = "TD20"
	AUTOFATTURA_SPLAFONAMENTO = "TD21"
	ESTRAZIONE_DEPOSITO_IVA = "TD22"
	ESTRAZIONE_DEPOSITO_IVA_CON_VERSAMENTO = "TD23"
	FATTURA_DIFFERITA_A = "TD24"
	FATTURA_DIFFERITA_B = "TD25"
	CESSIONE_BENI_AMMORTIZZABILI = "TD26"
	AUTOCONSUMO = "TD27"
	ACQUISTI_SAN_MARINO = "TD28"


DESCRIZIONE_TIPO_DOCUMENTO: dict[str, str] = {
	"TD01": "Fattura",
	"TD02": "Acconto / anticipo su fattura",
	"TD03": "Acconto / anticipo su parcella",
	"TD04": "Nota di credito",
	"TD05": "Nota di debito",
	"TD06": "Parcella",
	"TD07": "Fattura semplificata",
	"TD08": "Nota di credito semplificata",
	"TD09": "Nota di debito semplificata",
	"TD16": "Integrazione fattura reverse charge interno",
	"TD17": "Integrazione / autofattura per acquisto servizi dall'estero",
	"TD18": "Integrazione per acquisto di beni intracomunitari",
	"TD19": "Integrazione / autofattura per acquisto di beni ex art. 17, c. 2, DPR 633/72",
	"TD20": "Autofattura per regolarizzazione e integrazione delle fatture",
	"TD21": "Autofattura per splafonamento",
	"TD22": "Estrazione beni da Deposito IVA",
	"TD23": "Estrazione beni da Deposito IVA con versamento dell'IVA",
	"TD24": "Fattura differita (art. 21, c. 4, lett. a)",
	"TD25": "Fattura differita (art. 21, c. 4, terzo periodo lett. b)",
	"TD26": "Cessione di beni ammortizzabili e passaggi interni",
	"TD27": "Fattura per autoconsumo o cessioni gratuite senza rivalsa",
	"TD28": "Acquisti da San Marino con IVA (fattura cartacea)",
}

#: Documents that reverse the sign of the original: the total is a credit.
TIPI_DOCUMENTO_CREDITO: frozenset[str] = frozenset({"TD04", "TD08"})

#: Documents that must carry `DatiFattureCollegate` — they refer to another one.
TIPI_DOCUMENTO_CON_RIFERIMENTO: frozenset[str] = frozenset({"TD04", "TD05", "TD08", "TD09"})


class Natura(StrEnum):
	"""FatturaPA `Natura`: why VAT is not charged. Mandatory when the rate is zero."""

	ESCLUSE_ART_15 = "N1"
	NON_SOGGETTE_TERRITORIALITA = "N2.1"
	NON_SOGGETTE_ALTRI = "N2.2"
	NON_IMPONIBILI_ESPORTAZIONI = "N3.1"
	NON_IMPONIBILI_INTRA = "N3.2"
	NON_IMPONIBILI_SAN_MARINO = "N3.3"
	NON_IMPONIBILI_ASSIMILATE = "N3.4"
	NON_IMPONIBILI_INTENTO = "N3.5"
	NON_IMPONIBILI_ALTRE = "N3.6"
	ESENTI = "N4"
	REGIME_MARGINE = "N5"
	REVERSE_CHARGE_ROTTAMI = "N6.1"
	REVERSE_CHARGE_ORO = "N6.2"
	REVERSE_CHARGE_SUBAPPALTO_EDILE = "N6.3"
	REVERSE_CHARGE_FABBRICATI = "N6.4"
	REVERSE_CHARGE_CELLULARI = "N6.5"
	REVERSE_CHARGE_ELETTRONICI = "N6.6"
	REVERSE_CHARGE_EDILE = "N6.7"
	REVERSE_CHARGE_ENERGETICO = "N6.8"
	REVERSE_CHARGE_ALTRI = "N6.9"
	IVA_ASSOLTA_ALTRO_STATO_UE = "N7"


DESCRIZIONE_NATURA: dict[str, str] = {
	"N1": "Escluse ex art. 15 del DPR 633/72",
	"N2.1": "Non soggette ad IVA (artt. da 7 a 7-septies del DPR 633/72)",
	"N2.2": "Non soggette - altri casi",
	"N3.1": "Non imponibili - esportazioni",
	"N3.2": "Non imponibili - cessioni intracomunitarie",
	"N3.3": "Non imponibili - cessioni verso San Marino",
	"N3.4": "Non imponibili - operazioni assimilate alle cessioni all'esportazione",
	"N3.5": "Non imponibili - a seguito di dichiarazioni d'intento",
	"N3.6": "Non imponibili - altre operazioni che non concorrono al plafond",
	"N4": "Esenti",
	"N5": "Regime del margine / IVA non esposta in fattura",
	"N6.1": "Inversione contabile - rottami e altri materiali di recupero",
	"N6.2": "Inversione contabile - oro e argento puro",
	"N6.3": "Inversione contabile - subappalto nel settore edile",
	"N6.4": "Inversione contabile - cessione di fabbricati",
	"N6.5": "Inversione contabile - cessione di telefoni cellulari",
	"N6.6": "Inversione contabile - cessione di prodotti elettronici",
	"N6.7": "Inversione contabile - prestazioni comparto edile e settori connessi",
	"N6.8": "Inversione contabile - operazioni settore energetico",
	"N6.9": "Inversione contabile - altri casi",
	"N7": "IVA assolta in altro stato UE",
}

#: `N2` and `N3` and `N6` without a sub-code were retired with tracciato 1.2.2.
NATURE_RITIRATE: frozenset[str] = frozenset({"N2", "N3", "N6"})

#: Reverse charge: the recipient settles the VAT, the issuer charges none.
NATURE_REVERSE_CHARGE: frozenset[str] = frozenset(
	{"N6.1", "N6.2", "N6.3", "N6.4", "N6.5", "N6.6", "N6.7", "N6.8", "N6.9"}
)

#: Amounts that never enter the taxable base at all (advances in the client's name
#: and on the client's behalf). They do not feed the stamp-duty threshold either.
NATURE_FUORI_BASE: frozenset[str] = frozenset({"N1"})


class ModalitaPagamento(StrEnum):
	"""FatturaPA `ModalitaPagamento`."""

	CONTANTI = "MP01"
	ASSEGNO = "MP02"
	ASSEGNO_CIRCOLARE = "MP03"
	CONTANTI_TESORERIA = "MP04"
	BONIFICO = "MP05"
	VAGLIA_CAMBIARIO = "MP06"
	BOLLETTINO_BANCARIO = "MP07"
	CARTA_PAGAMENTO = "MP08"
	RID = "MP09"
	RID_UTENZE = "MP10"
	RID_VELOCE = "MP11"
	RIBA = "MP12"
	MAV = "MP13"
	QUIETANZA_ERARIO = "MP14"
	GIROCONTO = "MP15"
	DOMICILIAZIONE_BANCARIA = "MP16"
	DOMICILIAZIONE_POSTALE = "MP17"
	BOLLETTINO_POSTALE = "MP18"
	SEPA_DIRECT_DEBIT = "MP19"
	SEPA_CORE = "MP20"
	SEPA_B2B = "MP21"
	TRATTENUTA = "MP22"
	PAGOPA = "MP23"


DESCRIZIONE_PAGAMENTO: dict[str, str] = {
	"MP01": "Contanti",
	"MP02": "Assegno",
	"MP03": "Assegno circolare",
	"MP04": "Contanti presso Tesoreria",
	"MP05": "Bonifico",
	"MP06": "Vaglia cambiario",
	"MP07": "Bollettino bancario",
	"MP08": "Carta di pagamento",
	"MP09": "RID",
	"MP10": "RID utenze",
	"MP11": "RID veloce",
	"MP12": "RIBA",
	"MP13": "MAV",
	"MP14": "Quietanza erario",
	"MP15": "Giroconto su conti di contabilita' speciale",
	"MP16": "Domiciliazione bancaria",
	"MP17": "Domiciliazione postale",
	"MP18": "Bollettino di c/c postale",
	"MP19": "SEPA Direct Debit",
	"MP20": "SEPA Direct Debit CORE",
	"MP21": "SEPA Direct Debit B2B",
	"MP22": "Trattenuta su somme gia' riscosse",
	"MP23": "PagoPA",
}

#: Payment methods that satisfy the traceability the 19% deduction needs
#: (art. 1, c. 679, L. 160/2019). Everything else costs the payer the deduction.
PAGAMENTI_TRACCIATI: frozenset[str] = frozenset(
	{
		"MP02",
		"MP03",
		"MP05",
		"MP06",
		"MP07",
		"MP08",
		"MP09",
		"MP10",
		"MP11",
		"MP12",
		"MP13",
		"MP15",
		"MP16",
		"MP17",
		"MP18",
		"MP19",
		"MP20",
		"MP21",
		"MP22",
		"MP23",
	}
)

#: Cash, in every shape it takes.
PAGAMENTI_CONTANTI: frozenset[str] = frozenset({"MP01", "MP04"})


class CondizioniPagamento(StrEnum):
	RATE = "TP01"
	COMPLETO = "TP02"
	ANTICIPO = "TP03"


class EsigibilitaIVA(StrEnum):
	IMMEDIATA = "I"
	DIFFERITA = "D"
	SCISSIONE_PAGAMENTI = "S"


class TipoScontoMaggiorazione(StrEnum):
	SCONTO = "SC"
	MAGGIORAZIONE = "MG"


class TipoRitenuta(StrEnum):
	"""FatturaPA `TipoRitenuta`."""

	PERSONE_FISICHE = "RT01"
	PERSONE_GIURIDICHE = "RT02"
	INPS = "RT03"
	ENASARCO = "RT04"
	ENPAM = "RT05"
	ALTRO_PREVIDENZIALE = "RT06"


class CausalePagamento(StrEnum):
	"""`CausalePagamento` of the withholding: the Modello 770 code.

	`A` is self-employment work in the exercise of arts and professions - the one a
	professional invoice carries. The others exist because the field is a closed
	list and picking the wrong letter misfiles the certification.
	"""

	AUTONOMO_ABITUALE = "A"
	UTILIZZAZIONE_OPERE_INGEGNO = "B"
	CONTRATTI_ASSOCIAZIONE = "C"
	AMMINISTRATORI = "D"
	LEVATA_PROTESTI = "E"
	INDENNITA_CESSAZIONE = "G"
	INDENNITA_AGENTI = "H"
	PROVVIGIONI = "L"
	AUTONOMO_OCCASIONALE = "M"
	OBBLIGHI_FARE_NON_FARE = "M1"
	INDENNITA_TRASFERTA = "N"
	AUTONOMO_OCCASIONALE_SENZA_INPS = "O"
	PRESTAZIONI_SPORTIVE = "N1"
	REDDITI_DIVERSI = "P"
	PROVVIGIONI_MONOMANDATARIO = "Q"
	PROVVIGIONI_PLURIMANDATARIO = "R"
	ALTRO = "Z"


class TipoCassa(StrEnum):
	"""FatturaPA `TipoCassa`: which fund the `contributo` belongs to."""

	AVVOCATI = "TC01"
	COMMERCIALISTI = "TC02"
	GEOMETRI = "TC03"
	INGEGNERI_ARCHITETTI = "TC04"
	NOTARIATO = "TC05"
	RAGIONIERI = "TC06"
	ENASARCO = "TC07"
	ENPACL = "TC08"
	ENPAM = "TC09"
	ENPAF = "TC10"
	ENPAV = "TC11"
	ENPAIA = "TC12"
	AGENZIE_MARITTIME = "TC13"
	INPGI = "TC14"
	ONAOSI = "TC15"
	CASAGIT = "TC16"
	EPPI = "TC17"
	EPAP = "TC18"
	ENPAB = "TC19"
	ENPAPI = "TC20"
	ENPAP = "TC21"
	INPS = "TC22"


DESCRIZIONE_CASSA: dict[str, str] = {
	"TC01": "Cassa Nazionale Previdenza e Assistenza Avvocati e Procuratori legali",
	"TC02": "Cassa Previdenza Dottori Commercialisti",
	"TC03": "Cassa Previdenza e Assistenza Geometri",
	"TC04": "Cassa Nazionale Previdenza e Assistenza Ingegneri e Architetti",
	"TC05": "Cassa Nazionale del Notariato",
	"TC06": "Cassa Nazionale Previdenza e Assistenza Ragionieri e Periti commerciali",
	"TC07": "ENASARCO - Ente Nazionale Assistenza Agenti e Rappresentanti di Commercio",
	"TC08": "ENPACL - Consulenti del Lavoro",
	"TC09": "ENPAM - Medici",
	"TC10": "ENPAF - Farmacisti",
	"TC11": "ENPAV - Veterinari",
	"TC12": "ENPAIA - Agrotecnici",
	"TC13": "Fondo Previdenza Impiegati Agenzie Marittime Raccomandatarie",
	"TC14": "INPGI - Giornalisti",
	"TC15": "ONAOSI - Orfani Sanitari Italiani",
	"TC16": "CASAGIT - Giornalisti Italiani",
	"TC17": "EPPI - Periti Industriali",
	"TC18": "EPAP - Pluricategoriale",
	"TC19": "ENPAB - Biologi",
	"TC20": "ENPAPI - Infermieri",
	"TC21": "ENPAP - Psicologi",
	"TC22": "INPS - Gestione separata",
}


class ModalitaBollo(StrEnum):
	VIRTUALE = "virtuale"
	"""Art. 15 DPR 642/72, with the authorisation number and date on the document."""

	SU_ORIGINALE = "su_originale"
	"""Physical stamp on the paper original."""

	NON_DOVUTO = "non_dovuto"


class ModalitaDocumento(StrEnum):
	"""The two product configurations of Circolare 18/E 2014.

	Not a detail: they carry different retention obligations and a different
	coherent answer on the stamp duty.
	"""

	ANALOGICO_CON_COPIA = "analogico_con_copia"
	ELETTRONICA_EXTRA_SDI = "elettronica_extra_sdi"


class StatoSdI(StrEnum):
	NON_APPLICABILE = "non_applicabile"
	DA_INVIARE = "da_inviare"
	INVIATO = "inviato"
	CONSEGNATA = "consegnata"
	SCARTATA = "scartata"
	MANCATA_CONSEGNA = "mancata_consegna"
	ESITO_PA = "esito_pa"
	DECORRENZA_TERMINI = "decorrenza_termini"
	ERRORE = "errore"


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


FORMATO_PRIVATI = "FPR12"
FORMATO_PA = "FPA12"

#: The recipient has no interchange code: the invoice reaches the SdI and stops
#: there unless a PEC address travels with it.
CODICE_DESTINATARIO_ASSENTE = "0000000"
#: Non-resident recipient.
CODICE_DESTINATARIO_ESTERO = "XXXXXXX"

#: `CodiceDestinatario` is 6 characters for the PA and 7 for everybody else.
LUNGHEZZA_CODICE_PA = 6
LUNGHEZZA_CODICE_PRIVATI = 7


# =========================================================== Sistema TS 730


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
