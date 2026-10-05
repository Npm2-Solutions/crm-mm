r"""What the Sistema di Interscambio says back.

Six kinds of notice, and only one of them is good news. They matter because a
rejection means the invoice **counts as not issued**: the five days to correct and
resend run from the notice, not from when somebody opens the mailbox.

	RC  Ricevuta di consegna                  delivered to the client
	NS  Notifica di scarto                    rejected - the invoice does not exist
	MC  Mancata consegna                      the SdI has it, the client has not
	AT  Attestazione di trasmissione          delivery impossible, filed instead
	NE  Notifica esito committente            the PA accepted or refused it
	DT  Decorrenza termini                    the PA said nothing for fifteen days

`MC` is the one that gets misread. It is not a failure: the invoice is fiscally
issued and sits in the client's reserved area. What is owed is telling the client,
because the SdI will not.

The parsing is namespace-agnostic on purpose - local names only. The notice
namespaces are versioned and differ between the test and production environments;
a parser that insists on them breaks at the first change, and breaks silently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from xml.etree import ElementTree as ET

from .codici import StatoSdI, StrEnum


class TipoRicevuta(StrEnum):
	CONSEGNA = "RC"
	SCARTO = "NS"
	MANCATA_CONSEGNA = "MC"
	ATTESTAZIONE = "AT"
	ESITO_COMMITTENTE = "NE"
	DECORRENZA_TERMINI = "DT"
	#: what the client (a public administration) sends: the issuer never gets it
	ESITO_CESSIONARIO = "EC"
	#: the SdI refusing the client's outcome: the client's, not the issuer's
	SCARTO_ESITO = "SE"
	METADATI = "MT"


DESCRIZIONE_RICEVUTA: dict[str, str] = {
	"RC": "Ricevuta di consegna: la fattura è stata recapitata al destinatario",
	"NS": "Notifica di scarto: la fattura si considera non emessa",
	"MC": "Mancata consegna: verso un privato o un'azienda la fattura è emessa e messa a disposizione nell'area riservata del cliente; verso una PA il SdI ritenta per dieci giorni, poi manda l'attestazione",
	"AT": "Attestazione di avvenuta trasmissione con impossibilità di recapito",
	"NE": "Notifica di esito: la PA ha accettato o rifiutato il documento",
	"DT": "Decorrenza termini: la PA non si è espressa entro quindici giorni",
	"EC": "Esito del committente: lo manda la PA che ha ricevuto la fattura",
	"SE": "Scarto dell'esito del committente: l'esito della PA non era valido",
	"MT": "Metadati del file fattura, per chi la riceve",
}

#: `ITxxxxxxxxxxx_00001_RC_001.xml` - the notice carries the name of the file it
#: answers, which is the only reliable way back to the document. The attestation
#: arrives as `..._AT_001.zip`, holding the invoice and itself (Allegato B-1 1.8.4).
NOME_RICEVUTA = re.compile(
	r"^(?P<trasmittente>[A-Z]{2}[A-Za-z0-9]{2,28})_(?P<progressivo>[A-Za-z0-9]{1,5})"
	r"_(?P<tipo>RC|NS|MC|AT|NE|DT|EC|SE|MT)_(?P<contatore>[A-Za-z0-9]{1,3})\.(xml|zip)$",
	re.IGNORECASE,
)

#: The outcome a public administration returns.
ESITO_ACCETTAZIONE = "EC01"
ESITO_RIFIUTO = "EC02"

#: Which invoice state each notice leaves behind.
STATO_PER_TIPO: dict[str, str] = {
	TipoRicevuta.CONSEGNA: StatoSdI.CONSEGNATA,
	TipoRicevuta.SCARTO: StatoSdI.SCARTATA,
	TipoRicevuta.MANCATA_CONSEGNA: StatoSdI.MANCATA_CONSEGNA,
	TipoRicevuta.ATTESTAZIONE: StatoSdI.MANCATA_CONSEGNA,
	TipoRicevuta.ESITO_COMMITTENTE: StatoSdI.ESITO_PA,
	TipoRicevuta.DECORRENZA_TERMINI: StatoSdI.DECORRENZA_TERMINI,
}

#: Messages that are the client's or the file's, not an outcome of the invoice
#: sent: they leave the document's state as it was.
SENZA_STATO: frozenset[str] = frozenset(
	{TipoRicevuta.ESITO_CESSIONARIO, TipoRicevuta.SCARTO_ESITO, TipoRicevuta.METADATI}
)

#: Notices after which the document is fiscally settled and needs nothing more.
TIPI_TERMINALI: frozenset[str] = frozenset(
	{
		TipoRicevuta.CONSEGNA,
		TipoRicevuta.MANCATA_CONSEGNA,
		TipoRicevuta.ATTESTAZIONE,
		TipoRicevuta.DECORRENZA_TERMINI,
	}
)

#: What each rejection code means, as the SdI's "Elenco dei controlli" v2.0
#: (31/01/2025) and the "Rappresentazione tabellare" v1.4 state it (read on
#: 05/10/2026), in words a desk reads. The SdI's own text comes with it.
DESCRIZIONE_SCARTO: dict[str, str] = {
	"00001": "Nome file non valido",
	"00002": "Nome file duplicato",
	"00003": "Le dimensioni del file superano quelle ammesse",
	"00100": "Certificato di firma scaduto",
	"00101": "Certificato di firma revocato",
	"00102": "La firma elettronica del file non è valida",
	"00103": "Alla firma elettronica manca il riferimento temporale",
	"00104": "La CA che ha emesso il certificato di firma non è tra quelle affidabili",
	"00105": "Il riferimento temporale della firma è successivo alla ricezione del file",
	"00106": "File o archivio vuoto o corrotto",
	"00107": "Il certificato di firma non è valido",
	"00200": "File non conforme al formato",
	"00201": "Più di 50 errori di formato: i controlli si sono fermati",
	"00300": "Identificativo fiscale del trasmittente non valido",
	"00301": "Partita IVA di chi emette non valida",
	"00302": "Codice fiscale di chi emette non valido",
	"00303": "Partita IVA del rappresentante fiscale o del terzo emittente non valida",
	"00304": "Codice fiscale del rappresentante fiscale non valido",
	"00305": "Partita IVA del cliente non valida",
	"00306": "Codice fiscale del cliente non valido",
	"00311": "Codice destinatario non valido",
	"00312": "Codice destinatario non attivo",
	"00313": "Il codice destinatario XXXXXXX vale solo per un cliente estero con identificativo IVA",
	"00320": "Partita IVA e codice fiscale di chi emette non coerenti",
	"00321": "Codice fiscale di chi emette non partecipante al gruppo IVA",
	"00322": "Manca il codice fiscale di chi emette, con una partita IVA di gruppo IVA",
	"00323": "Partita IVA di chi emette cessata da oltre 5 anni",
	"00324": "Partita IVA e codice fiscale del cliente non coerenti",
	"00325": "Codice fiscale del cliente non partecipante al gruppo IVA",
	"00326": "Manca il codice fiscale del cliente, con una partita IVA di gruppo IVA",
	"00327": "Codice fiscale di gruppo IVA del cliente non riferito a un partecipante",
	"00398": "Codice ufficio non univoco nell'IPA",
	"00399": "Cliente presente nell'IPA: la fattura va in formato PA",
	"00400": "Riga con aliquota IVA zero senza Natura",
	"00401": "Riga con Natura e aliquota IVA diversa da zero",
	"00403": "Data della fattura successiva alla ricezione",
	"00404": "Fattura duplicata",
	"00409": "Fattura duplicata nello stesso lotto",
	"00411": "Mancano i dati della ritenuta, con una riga soggetta a ritenuta",
	"00413": "Cassa previdenziale con aliquota IVA zero senza Natura",
	"00414": "Cassa previdenziale con Natura e aliquota IVA diversa da zero",
	"00415": "Mancano i dati della ritenuta, con la cassa soggetta a ritenuta",
	"00417": "Manca sia la partita IVA sia il codice fiscale del cliente",
	"00418": "Data della fattura precedente a quella del documento collegato",
	"00419": "Manca il riepilogo per un'aliquota IVA presente nelle righe o nella cassa",
	"00420": "Inversione contabile (N6) con scissione dei pagamenti",
	"00421": "Imposta del riepilogo non calcolata secondo le regole",
	"00422": "Imponibile del riepilogo non calcolato secondo le regole",
	"00423": "Prezzo totale della riga non calcolato secondo le regole",
	"00424": "Aliquota IVA non espressa in percentuale",
	"00425": "Numero della fattura senza cifre",
	"00427": "Codice destinatario di lunghezza non ammessa per il formato",
	"00428": "Formato di trasmissione non coerente con la versione",
	"00429": "Riepilogo con aliquota IVA zero senza Natura",
	"00430": "Riepilogo con Natura e aliquota IVA diversa da zero",
	"00437": "Sconto o maggiorazione del documento senza percentuale né importo",
	"00438": "Sconto o maggiorazione di riga senza percentuale né importo",
	"00443": "Un'aliquota IVA delle righe o della cassa non ha il suo riepilogo",
	"00444": "Una Natura delle righe o della cassa non ha il suo riepilogo",
	"00445": "Natura generica N2, N3 o N6 non più ammessa dal 2021",
	"00471": "Per questo tipo di documento chi emette non può essere il cliente",
	"00472": "Per questo tipo di documento chi emette deve essere il cliente",
	"00473": "Per questo tipo di documento il paese di chi emette non è ammesso",
	"00474": "Per questo tipo di documento non sono ammesse righe con aliquota IVA zero",
	"00475": "Per questo tipo di documento serve la partita IVA del cliente",
	"00476": "Chi emette e il cliente non possono essere entrambi esteri",
	"00477": "Non imponibile per dichiarazione d'intento, con dichiarazione invalidata",
}


@dataclass(frozen=True)
class ErroreSdI:
	codice: str
	descrizione: str
	suggerimento: str = ""

	def testo(self) -> str:
		nota = DESCRIZIONE_SCARTO.get(self.codice)
		parti = [f"{self.codice}: {self.descrizione or nota or ''}".strip(": ")]
		if nota and nota.lower() not in (self.descrizione or "").lower():
			parti.append(f"({nota})")
		return " ".join(parti)


@dataclass
class Ricevuta:
	"""One notice, read."""

	tipo: str
	identificativo_sdi: str | None = None
	nome_file: str | None = None
	message_id: str | None = None
	data: datetime | None = None
	esito: str | None = None
	descrizione: str | None = None
	errori: list[ErroreSdI] = field(default_factory=list)
	riferimento_fattura: str | None = None

	@property
	def stato(self) -> str:
		return STATO_PER_TIPO.get(self.tipo, StatoSdI.INVIATO)

	@property
	def scartata(self) -> bool:
		return self.tipo == TipoRicevuta.SCARTO or self.esito == ESITO_RIFIUTO

	@property
	def terminale(self) -> bool:
		"""Is there nothing further to wait for?"""
		if self.tipo in TIPI_TERMINALI:
			return True
		return self.tipo == TipoRicevuta.ESITO_COMMITTENTE and self.esito == ESITO_ACCETTAZIONE

	def riassunto(self) -> str:
		"""A sentence for whoever has to act on it."""
		base = DESCRIZIONE_RICEVUTA.get(self.tipo, f"Ricevuta {self.tipo}")
		if self.tipo == TipoRicevuta.SCARTO and self.errori:
			return base + ". " + " · ".join(e.testo() for e in self.errori)
		if self.tipo == TipoRicevuta.ESITO_COMMITTENTE:
			esito = "accettata" if self.esito == ESITO_ACCETTAZIONE else "rifiutata"
			coda = f" - {self.descrizione}" if self.descrizione else ""
			return f"{base}: {esito}{coda}"
		if self.descrizione:
			return f"{base}. {self.descrizione}"
		return base


def tipo_da_nome(nome: str | None) -> str | None:
	"""The notice type, read out of the file name.

	The name is not decoration: it carries the transmitter, the progressive of the
	file being answered and the notice type, and it is the only reliable way back to
	the document when the body does not name it.
	"""
	corrispondenza = NOME_RICEVUTA.match((nome or "").strip())
	if not corrispondenza:
		return None
	return corrispondenza.group("tipo").upper()


def riferimento_da_nome(nome: str | None) -> str | None:
	"""The name of the invoice file this notice answers."""
	corrispondenza = NOME_RICEVUTA.match((nome or "").strip())
	if not corrispondenza:
		return None
	return f"{corrispondenza.group('trasmittente')}_{corrispondenza.group('progressivo')}.xml"


def e_ricevuta(nome: str | None) -> bool:
	return tipo_da_nome(nome) is not None


def _tutti(radice, nome: str) -> list:
	return radice.findall(f".//{{*}}{nome}")


def _testo(radice, *nomi: str) -> str | None:
	for nome in nomi:
		for nodo in _tutti(radice, nome):
			valore = (nodo.text or "").strip()
			if valore:
				return valore
	return None


def _data(valore: str | None) -> datetime | None:
	if not valore:
		return None
	for formato in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
		try:
			return datetime.strptime(valore.split("+")[0].rstrip("Z"), formato)
		except ValueError:
			continue
	return None


_RADICI: dict[str, str] = {
	"RicevutaConsegna": TipoRicevuta.CONSEGNA,
	"RicevutaScarto": TipoRicevuta.SCARTO,
	"RicevutaImpossibilitaRecapito": TipoRicevuta.MANCATA_CONSEGNA,
	"RicevutaImpossibultaRecapito": TipoRicevuta.MANCATA_CONSEGNA,
	"AttestazioneTrasmissioneFattura": TipoRicevuta.ATTESTAZIONE,
	"NotificaEsito": TipoRicevuta.ESITO_COMMITTENTE,
	"NotificaDecorrenzaTermini": TipoRicevuta.DECORRENZA_TERMINI,
	# the names of MessaggiTypes v1.1, which the SdI still sends on some channels
	"NotificaScarto": TipoRicevuta.SCARTO,
	"NotificaMancataConsegna": TipoRicevuta.MANCATA_CONSEGNA,
	"NotificaEsitoCommittente": TipoRicevuta.ESITO_CESSIONARIO,
	"ScartoEsitoCommittente": TipoRicevuta.SCARTO_ESITO,
	"MetadatiInvioFile": TipoRicevuta.METADATI,
}


def analizza(contenuto: bytes, nome_file: str | None = None) -> Ricevuta | None:
	"""Read a notice. Returns `None` when the file is not one.

	The type comes from the root element when it is recognisable and from the file
	name otherwise - the SdI has shipped both spellings of the undelivered notice
	over the years, and a parser that knows only one of them loses the notice.
	"""
	try:
		radice = ET.fromstring(contenuto)
	except ET.ParseError:
		return None

	locale = radice.tag.split("}")[-1]
	tipo = _RADICI.get(locale) or tipo_da_nome(nome_file)
	if not tipo:
		return None

	ricevuta = Ricevuta(
		tipo=tipo,
		identificativo_sdi=_testo(radice, "IdentificativoSdI"),
		nome_file=_testo(radice, "NomeFile") or nome_file,
		message_id=_testo(radice, "MessageId", "MessageIdCommittente"),
		data=_data(
			_testo(radice, "DataOraConsegna", "DataOraRicezione", "DataOraMessaAdisposizione", "Data")
		),
		esito=_testo(radice, "Esito"),
		descrizione=_testo(radice, "Descrizione", "MessaggioIstruzione"),
		riferimento_fattura=riferimento_da_nome(nome_file),
	)

	for nodo in _tutti(radice, "Errore"):
		codice = _testo(nodo, "Codice") or ""
		descrizione = _testo(nodo, "Descrizione") or ""
		suggerimento = _testo(nodo, "Suggerimento") or ""
		if codice or descrizione:
			ricevuta.errori.append(ErroreSdI(codice, descrizione, suggerimento))

	if ricevuta.tipo == TipoRicevuta.SCARTO and not ricevuta.errori and ricevuta.descrizione:
		ricevuta.errori.append(ErroreSdI("", ricevuta.descrizione))
	return ricevuta
