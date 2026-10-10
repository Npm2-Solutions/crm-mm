# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre the simulation plays, without a site: who works there, where and
when, what it offers and to whom, the people who will come, and the week.

A poliambulatorio in Milan with a second location in Monza: a medical director
who visits in both, a physiotherapist who also teaches Pilates, a dentist, a
dietitian, the front desk, the manager and marketing. The services are the ones a
week of the simulation needs, each a real setting of the product: a visit with a
deposit paid online, a service paid in full online, an online visit, physiotherapy
sessions a cycle is sold of, the dentist's, a Pilates class with few seats; a
health fund in direct form; a monthly subscription sold in the area and one paid
upfront.

Data, not strings of the interface: they are what a centre writes, so they stay in
Italian. Nobody here is a real person: the addresses are at example.com, which
receives nothing by its own rule, and the numbers are of a range no operator gives.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

#: Every address of the simulation's people: a domain reserved for examples.
DOMINIO = "example.com"
#: The centre's VAT number: of an office (890) that gives none, so nobody's.
PARTITA_IVA = "12345678903"
#: The password of the simulation's staff, unless the site's config names another
#: (``dottorcloud_collaudo_password``).
PASSWORD = "Collaudo-2026!"
NOME_DEL_CENTRO = "Poliambulatorio San Luca"
#: The roles of the team, as the staging guide's JSON names them.
RUOLI = ("responsabile", "segreteria", "medico", "fisioterapista", "dentista", "dietista", "marketing")
GIORNI = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
#: The days the simulation plays, in the order it plays them.
SETTIMANA = ("lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato")


@dataclass(frozen=True)
class Collega:
	ruolo: str
	nome: str
	cognome: str
	#: the levels of `crm.permissions` (never a role by hand)
	livelli: tuple[str, ...]
	#: CRM Professional Qualification, for whoever performs a service
	qualifica: str | None
	titolo: str
	cellulare: str
	#: weekday -> ((start, end, location key), ...), in the centre's clock
	turni: dict[str, tuple[tuple[str, str, str], ...]] = field(default_factory=dict)


def _sempre(*fasce: tuple[str, str], sede: str = "milano") -> tuple[tuple[str, str, str], ...]:
	return tuple((inizio, fine, sede) for inizio, fine in fasce)


SQUADRA = (
	Collega(
		"responsabile",
		"Roberta",
		"Colombo",
		("manager",),
		None,
		"Responsabile del centro",
		"+39 335 000 0101",
	),
	Collega(
		"segreteria",
		"Silvia",
		"Ricci",
		("segreteria",),
		None,
		"Accoglienza e segreteria",
		"+39 338 000 0102",
	),
	Collega(
		"medico",
		"Andrea",
		"Conti",
		("direzione", "operatore"),
		"medico_chirurgo",
		"Direttore sanitario, medico chirurgo",
		"+39 333 000 0103",
		{
			"Monday": _sempre(("09:00", "13:00"), ("14:00", "18:00")),
			"Tuesday": _sempre(("14:00", "19:00"), sede="monza"),
			"Wednesday": _sempre(("09:00", "13:00")),
			"Thursday": _sempre(("14:00", "19:00"), sede="monza"),
			"Friday": _sempre(("09:00", "13:00"), ("14:00", "18:00")),
		},
	),
	Collega(
		"fisioterapista",
		"Marta",
		"Greco",
		("operatore",),
		"fisioterapista",
		"Fisioterapista, riabilitazione e Pilates clinico",
		"+39 347 000 0104",
		{
			**{giorno: _sempre(("08:30", "13:00"), ("14:00", "19:30")) for giorno in GIORNI[:5]},
			"Saturday": _sempre(("09:00", "13:00")),
		},
	),
	Collega(
		"dentista",
		"Stefano",
		"Bruno",
		("operatore",),
		"odontoiatra",
		"Odontoiatra, conservativa e protesi",
		"+39 346 000 0105",
		{
			"Monday": _sempre(("09:00", "13:00"), ("14:00", "19:00")),
			"Wednesday": _sempre(("09:00", "13:00"), ("14:00", "20:00")),
			"Friday": _sempre(("09:00", "13:00"), ("14:00", "18:00")),
		},
	),
	Collega(
		"dietista",
		"Francesca",
		"Gallo",
		("operatore",),
		"dietista",
		"Dietista, educazione alimentare",
		"+39 340 000 0106",
		{
			"Tuesday": _sempre(("09:00", "13:00"), ("14:00", "18:00")),
			"Thursday": _sempre(("09:00", "13:00"), ("14:00", "18:00")),
			"Friday": _sempre(("14:00", "19:00")),
			"Saturday": _sempre(("09:00", "13:00")),
		},
	),
	Collega(
		"marketing",
		"Elisa",
		"Costa",
		("marketing",),
		None,
		"Marketing e comunicazione",
		"+39 349 000 0107",
	),
)

#: key, name, street, postcode, city, province, phone, opening hours
SEDI = (
	(
		"milano",
		"Sede di Milano",
		"Via Washington 70",
		"20146",
		"Milano",
		"MI",
		"+39 02 0000 0300",
		"Lun-Ven 8:30-20, Sab 9-13",
	),
	(
		"monza",
		"Sede di Monza",
		"Via Italia 12",
		"20900",
		"Monza",
		"MB",
		"+39 039 000 0400",
		"Mar e Gio 14-19",
	),
)

#: key, name, location key, seats, colour, description
STANZE = (
	("studio1", "Studio 1", "milano", 0, "#4F8EDC", "Lettino elettrico, tecar e laser"),
	("studio2", "Studio 2", "milano", 0, "#8B6FD6", "Ambulatorio medico, elettrocardiografo"),
	("studio3", "Studio 3", "milano", 0, "#3FA36B", "Scrivania, bilancia impedenziometrica"),
	("studio4", "Studio 4", "milano", 0, "#D9774B", "Riunito odontoiatrico e radiografico endorale"),
	("palestra", "Palestra", "milano", 4, "#E08A3C", "Quattro reformer, tappetini e piccoli attrezzi"),
	("monza_a", "Monza - Studio A", "monza", 0, "#C25C8B", "Ambulatorio medico"),
)


@dataclass(frozen=True)
class Servizio:
	chiave: str
	nome: str
	categoria: str
	minuti: int
	prezzo: float
	#: the roles of the team who perform it
	chi: tuple[str, ...]
	stanza: str
	#: more than one: a class
	posti: int = 1
	online: bool = True
	#: "", "Deposit", "Full price"
	pagamento: str = ""
	acconto: float = 0
	visita_online: bool = False
	colore: str = "#4F8EDC"
	descrizione: str = ""
	#: a class held only at these hours: weekday -> ((start, end), ...)
	orari: dict[str, tuple[tuple[str, str], ...]] = field(default_factory=dict)


SERVIZI = (
	Servizio(
		"visita",
		"Visita medica",
		"Visite",
		30,
		120,
		("medico",),
		"studio2",
		pagamento="Deposit",
		acconto=30,
		colore="#8B6FD6",
		descrizione="Visita medica generale con il direttore sanitario.",
	),
	Servizio(
		"visita_fisio",
		"Visita fisioterapica",
		"Fisioterapia",
		45,
		70,
		("fisioterapista",),
		"studio1",
		colore="#4F8EDC",
		descrizione="Valutazione, test e piano di trattamento.",
	),
	Servizio(
		"fisioterapia",
		"Seduta di fisioterapia",
		"Fisioterapia",
		45,
		50,
		("fisioterapista",),
		"studio1",
		online=False,
		colore="#6FA8E8",
		descrizione="Terapia manuale ed esercizio terapeutico: si vende anche a cicli.",
	),
	Servizio(
		"nutrizione",
		"Visita nutrizionale",
		"Nutrizione",
		45,
		90,
		("dietista",),
		"studio3",
		pagamento="Full price",
		colore="#3FA36B",
		descrizione="Prima visita con le misure, le abitudini e il piano alimentare.",
	),
	Servizio(
		"nutrizione_online",
		"Controllo nutrizionale online",
		"Nutrizione",
		30,
		50,
		("dietista",),
		"studio3",
		pagamento="Full price",
		visita_online=True,
		colore="#7CC49B",
		descrizione="Il controllo in videochiamata, da casa.",
	),
	Servizio(
		"odonto",
		"Prima visita odontoiatrica",
		"Odontoiatria",
		30,
		60,
		("dentista",),
		"studio4",
		colore="#D9774B",
		descrizione="Visita, odontogramma e piano di cura.",
	),
	Servizio(
		"igiene",
		"Igiene orale professionale",
		"Odontoiatria",
		45,
		80,
		("dentista",),
		"studio4",
		online=False,
		colore="#E39A6F",
		descrizione="Ablazione del tartaro e lucidatura.",
	),
	Servizio(
		"otturazione",
		"Otturazione",
		"Odontoiatria",
		45,
		110,
		("dentista",),
		"studio4",
		online=False,
		colore="#C9673D",
		descrizione="Otturazione in composito.",
	),
	Servizio(
		"devitalizzazione",
		"Devitalizzazione",
		"Odontoiatria",
		60,
		280,
		("dentista",),
		"studio4",
		online=False,
		colore="#B25530",
		descrizione="Trattamento canalare di un dente.",
	),
	Servizio(
		"pilates",
		"Pilates di gruppo",
		"Movimento",
		55,
		20,
		("fisioterapista",),
		"palestra",
		posti=4,
		colore="#E08A3C",
		descrizione="Pilates sui reformer, in quattro.",
		orari={"Monday": (("18:00", "19:00"),), "Wednesday": (("18:00", "19:00"),)},
	),
)

#: The health fund: its organisation, the price list's prices by service key, the
#: person's share in percent. Its VAT number, like every one here, is of an office
#: (890) that gives none.
CONVENZIONE = {
	"nome": "Fondo Salute Più",
	"azienda": "Fondo Salute Più S.c.r.l.",
	"partita_iva": "76543218903",
	"listino": "Listino Fondo Salute Più",
	"prezzi": {"visita": 100, "visita_fisio": 60, "fisioterapia": 40},
	"quota": 20,
}

#: key, name, months, payment, price, entries a week (0: unlimited), sold online, description
ABBONAMENTI = (
	(
		"mensile",
		"Pilates mensile",
		3,
		"Monthly",
		# the price of the whole subscription: 70 € a month for three months
		210,
		2,
		True,
		"Due lezioni di Pilates a settimana, pagate ogni mese con la carta.",
	),
	(
		"trimestre",
		"Pilates trimestre",
		3,
		"Upfront",
		240,
		0,
		False,
		"Pilates quante volte vuoi per tre mesi, pagato subito.",
	),
)


#: The form every new patient signs before their first appointment: the privacy
#: notice, the marketing consent, a signature.
INFORMATIVA = {
	"sections": [
		{
			"id": "informativa",
			"title": "Informativa sul trattamento dei dati",
			"fields": [
				{
					"id": "testo",
					"type": "paragraph",
					"text": "Trattiamo i tuoi dati per prenotare e svolgere le prestazioni, per le fatture e "
					"per gli obblighi di legge; i dati sanitari solo per curarti. Puoi chiedere in ogni "
					"momento di vederli, correggerli o cancellarli scrivendo alla segreteria.",
				},
				{
					"id": "letta",
					"type": "consent",
					"label": "Ho letto l'informativa",
					"consent_type": "privacy_notice",
					"must_accept": True,
				},
				{
					"id": "novita",
					"type": "consent",
					"label": "Novità e promemoria",
					"consent_type": "marketing",
					"required": True,
				},
				{
					"id": "dossier",
					"type": "consent",
					"label": "Dossier sanitario",
					"consent_type": "health_dossier",
					"required": True,
				},
				{
					"id": "referti",
					"type": "consent",
					"label": "Referti online",
					"consent_type": "online_reports",
					"required": True,
				},
				{"id": "firma", "type": "signature", "label": "Firma", "required": True},
			],
		}
	]
}


#: The centre's Google Place ID, made up: the review link leads to Google's page
#: for it, which the simulation never opens.
PLACE_ID = "ChIJCollaudoSanLuca0000000"

#: What marketing set up before the week: a campaign sent by hand to a list (only
#: to who agreed to marketing) and the review request after a visit, by email - a
#: centre without its Twilio writes no SMS.
AUTOMAZIONI = (
	{
		"title": "Novità d'autunno",
		"trigger": "Started by Hand",
		"marketing_consent": 1,
		"steps": [
			{
				"type": "send_email",
				"subject": "Le novità d'autunno, {{ first_name }}",
				"message": "Ciao {{ first_name }}, da novembre il Pilates anche il venerdì sera. "
				"Prenota quando vuoi: {{ booking_link }}",
			}
		],
	},
	{
		"title": "Recensione dopo la visita",
		"trigger": "Appointment Completed",
		"marketing_consent": 0,
		"steps": [
			{"type": "wait", "mode": "duration", "days": 0, "hours": 2, "minutes": 0},
			{
				"type": "send_email",
				"subject": "Com'è andata, {{ first_name }}?",
				"message": "Ciao {{ first_name }}, grazie della visita. Se hai un minuto, "
				"racconta agli altri com'è andata: {{ review_link }}",
			},
		],
	},
)


@dataclass(frozen=True)
class Persona:
	"""Somebody who comes to the centre during the week: how they are reached, and
	the device they hold (the suite's names)."""

	chiave: str
	nome: str
	cognome: str
	sesso: str
	nascita: str
	cellulare: str
	dispositivo: str
	#: who books for them (a parent): their key
	genitore: str | None = None

	@property
	def email(self) -> str:
		return indirizzo(self.nome, self.cognome)


PERSONE = (
	Persona("giulia", "Giulia", "Marchetti", "F", "1988-04-12", "+39 351 000 1001", "telefono"),
	Persona("marco", "Marco", "Pellegrini", "M", "1975-09-30", "+39 351 000 1002", "piccolo"),
	Persona("anna", "Anna", "De Luca", "F", "1962-01-21", "+39 351 000 1003", "di_lato"),
	Persona("luca", "Luca", "Ferrara", "M", "1954-06-08", "+39 351 000 1004", "testo_grande"),
	Persona("sara", "Sara", "Lombardi", "F", "1991-11-02", "+39 351 000 1005", "scuro"),
	Persona("elena", "Elena", "Rinaldi", "F", "1984-03-17", "+39 351 000 1006", "telefono"),
	Persona("tommaso", "Tommaso", "Rinaldi", "M", "2018-05-09", "", "telefono", genitore="elena"),
	Persona("paolo", "Paolo", "Fontana", "M", "1980-07-25", "+39 351 000 1007", "telefono"),
	Persona("chiara", "Chiara", "Moretti", "F", "1993-12-14", "+39 351 000 1008", "piccolo"),
	Persona("roberto", "Roberto", "Galli", "M", "1969-02-03", "+39 351 000 1009", "telefono"),
	Persona("davide", "Davide", "Santoro", "M", "1990-08-19", "+39 351 000 1010", "telefono"),
	Persona("federica", "Federica", "Villa", "F", "1986-10-05", "+39 351 000 1011", "telefono"),
)

#: The company whose employee comes, invoiced to it.
AZIENDA_CLIENTE = {
	"nome": "Tecnoservizi S.r.l.",
	"partita_iva": "24681358909",
	"indirizzo": ("Via Torino", "45", "20123", "Milano", "MI"),
	"persona": "federica",
}


#: The month letters of a codice fiscale.
MESI_CF = "ABCDEHLMPRST"


def codice_fiscale(persona: Persona) -> str:
	"""A codice fiscale coherent with the person's name, birth and sex, born at «Y»
	and a number: a place letter no town nor country has, so it can be nobody's."""
	from crm.invoicing.engine import codice_fiscale as cf

	anno, mese, giorno = (int(x) for x in persona.nascita.split("-"))
	giorno += 40 if persona.sesso == "F" else 0
	luogo = 100 + PERSONE.index(persona)
	primi = (
		f"{cf._tripletta_cognome(persona.cognome)}{cf._tripletta_nome(persona.nome)}"
		f"{anno % 100:02d}{MESI_CF[mese - 1]}{giorno:02d}Y{luogo:03d}"
	)
	return primi + cf.carattere_controllo(primi)


def indirizzo(nome: str, cognome: str) -> str:
	"""An address of the simulation at example.com: ``nome.cognome``, without spaces
	or accents."""
	parti = f"{nome}.{cognome}".lower().replace(" ", "").replace("'", "")
	return f"{parti}@{DOMINIO}"


def della_simulazione(email: str | None) -> bool:
	"""Whether an address is one of the simulation's (or of a domain reserved for
	examples): what the simulation may find on the site before it starts."""
	dominio = (email or "").strip().lower().rpartition("@")[2]
	return dominio == DOMINIO or dominio.endswith("." + DOMINIO)


def utenti(persone: dict | None = None) -> dict[str, dict]:
	"""The team's users by role: the simulation's own at example.com, or the ones the
	staging guide's JSON names (role -> email, first_name, last_name). A role the
	JSON leaves out keeps the simulation's."""
	persone = persone or {}
	sconosciuti = set(persone) - set(RUOLI)
	if sconosciuti:
		raise ValueError(f"Unknown roles: {', '.join(sorted(sconosciuti))}")
	fuori = {}
	for collega in SQUADRA:
		propri = persone.get(collega.ruolo) or {}
		email = (propri.get("email") or "").strip().lower()
		if propri and "@" not in email:
			raise ValueError(f"{collega.ruolo}: an email is needed")
		fuori[collega.ruolo] = {
			"email": email or indirizzo(collega.nome, collega.cognome),
			"first_name": (propri.get("first_name") or collega.nome).strip(),
			"last_name": (propri.get("last_name") or collega.cognome).strip(),
		}
	doppi = {v["email"] for v in fuori.values() if [w["email"] for w in fuori.values()].count(v["email"]) > 1}
	if doppi:
		raise ValueError(f"The same email for two roles: {', '.join(sorted(doppi))}")
	return fuori


def collega(ruolo: str) -> Collega:
	return next(c for c in SQUADRA if c.ruolo == ruolo)


def servizio(chiave: str) -> Servizio:
	return next(s for s in SERVIZI if s.chiave == chiave)


def persona(chiave: str) -> Persona:
	return next(p for p in PERSONE if p.chiave == chiave)


# -- the week ---------------------------------------------------------------------------

#: The national holidays, month-day; Easter Monday moves (`pasquetta`).
FESTIVITA = (
	("01-01", "Capodanno"),
	("01-06", "Epifania"),
	("04-25", "Festa della Liberazione"),
	("05-01", "Festa del lavoro"),
	("06-02", "Festa della Repubblica"),
	("08-15", "Ferragosto"),
	("11-01", "Ognissanti"),
	("12-08", "Immacolata"),
	("12-25", "Natale"),
	("12-26", "Santo Stefano"),
)


def pasquetta(anno: int) -> datetime.date:
	"""Easter Monday of ``anno`` (the Gregorian computus)."""
	a, b, c = anno % 19, anno // 100, anno % 100
	d, e = b // 4, b % 4
	f = (b + 8) // 25
	g = (b - f + 1) // 3
	h = (19 * a + b - d - g + 15) % 30
	i, k = c // 4, c % 4
	l = (32 + 2 * e + 2 * i - h - k) % 7
	m = (a + 11 * h + 22 * l) // 451
	mese = (h + l - 7 * m + 114) // 31
	giorno = (h + l - 7 * m + 114) % 31 + 1
	return datetime.date(anno, mese, giorno) + datetime.timedelta(days=1)


def festivita(anno: int) -> list[tuple[datetime.date, str]]:
	"""The holidays of ``anno``: the fixed ones and Easter Monday."""
	giorni = [(datetime.date.fromisoformat(f"{anno}-{giorno}"), nome) for giorno, nome in FESTIVITA]
	giorni.append((pasquetta(anno), "Lunedì dell'Angelo"))
	return sorted(giorni)


def lunedi_dopo(giorno: datetime.date) -> datetime.date:
	"""The first Monday after ``giorno`` (never ``giorno`` itself) whose week, Monday
	to Saturday, has no holiday: the week the simulation plays starts after
	everything already on the site, on days the centre is open."""
	lunedi = giorno + datetime.timedelta(days=7 - giorno.weekday())
	while True:
		feste = {g for anno in (lunedi.year, lunedi.year + 1) for g, _nome in festivita(anno)}
		if not any(lunedi + datetime.timedelta(days=i) in feste for i in range(6)):
			return lunedi
		lunedi += datetime.timedelta(days=7)


def settimana(lunedi: datetime.date) -> dict[str, datetime.date]:
	"""The days the simulation plays, by their Italian names."""
	if lunedi.weekday() != 0:
		raise ValueError(f"{lunedi} is not a Monday")
	return {nome: lunedi + datetime.timedelta(days=indice) for indice, nome in enumerate(SETTIMANA)}


def turni_del_giorno(giorno: datetime.date) -> dict[str, tuple[tuple[str, str, str], ...]]:
	"""Who works on ``giorno``: role -> their shifts that day."""
	nome = GIORNI[giorno.weekday()]
	return {c.ruolo: c.turni[nome] for c in SQUADRA if c.turni.get(nome)}


# -- a centre that holds together --------------------------------------------------------------


def problemi(foto: dict, finti: bool = True) -> list[str]:
	"""What does not hold together in a centre made by `prepara.centro`, from its
	photograph (`prepara.fotografia`): every role a user with its levels, every
	service somebody who works and a room of a location, the company that issues in
	test, the settings the week counts on - Stripe only on the fakes (``finti``):
	staging connects its own sandbox from the screens. Empty when the centre is
	whole."""
	fuori = []
	livelli = foto.get("livelli") or {}
	for collega_ in SQUADRA:
		propri = set(livelli.get(collega_.ruolo) or ())
		if not propri:
			fuori.append(f"{collega_.ruolo}: no user with a level")
		elif not set(collega_.livelli) <= propri:
			fuori.append(f"{collega_.ruolo}: levels {sorted(propri)} instead of {sorted(collega_.livelli)}")
		if collega_.turni and not (foto.get("turni") or {}).get(collega_.ruolo):
			fuori.append(f"{collega_.ruolo}: no shifts")
	servizi = foto.get("servizi") or {}
	for servizio_ in SERVIZI:
		trovato = servizi.get(servizio_.nome)
		if not trovato:
			fuori.append(f"{servizio_.nome}: missing")
			continue
		if not trovato.get("staff"):
			fuori.append(f"{servizio_.nome}: nobody performs it")
		if not trovato.get("stanze"):
			fuori.append(f"{servizio_.nome}: no room")
		if servizio_.online and not trovato.get("online"):
			fuori.append(f"{servizio_.nome}: not bookable online")
		if not trovato.get("scheda"):
			fuori.append(f"{servizio_.nome}: no card to invoice it")
		if servizio_.pagamento and trovato.get("pagamento") != servizio_.pagamento:
			fuori.append(f"{servizio_.nome}: paid online {trovato.get('pagamento')!r}")
	azienda = foto.get("azienda") or {}
	if not azienda:
		fuori.append("no issuing company")
	elif azienda.get("ambiente") != "sandbox":
		fuori.append("the issuing company is not in test")
	accesi = ("clinica", "promemoria", "solleciti", "attese", "prenotazione_online") + (
		("stripe",) if finti else ()
	)
	for chiave in accesi:
		if not (foto.get("accesi") or {}).get(chiave):
			fuori.append(f"{chiave}: off")
	if len(foto.get("sedi") or ()) != len(SEDI):
		fuori.append("the locations are not two")
	return fuori
