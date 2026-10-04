# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The words of the demo: an Italian centre of physiotherapy, osteopathy, nutrition
and movement, its team, the people who come to it and what is written about them.

Data, not strings of the interface: they are what a centre writes, so they stay in
Italian, as a centre's own records do. Nothing here is a real person: names are
put together from common ones, the addresses are at example.com - a domain that
receives no email by its own rule - and the numbers are never called, written to or
messaged (`crm.demo.guardie`).
"""

from __future__ import annotations

#: The domain every demo address is at: reserved for examples, it receives nothing.
DOMINIO = "example.com"

# -- the team -----------------------------------------------------------------------------

#: key, first name, last name, levels, qualification (CRM Professional Qualification),
#: public title, mobile
SQUADRA = (
	("manager", "Paolo", "Rinaldi", ("manager",), None, "Direttore del centro", "+39 335 555 0101"),
	("desk", "Chiara", "Romano", ("segreteria",), None, "Accoglienza e segreteria", "+39 338 555 0102"),
	(
		"giulia",
		"Giulia",
		"Ferri",
		("operatore",),
		"fisioterapista",
		"Fisioterapista, riabilitazione ortopedica e sportiva",
		"+39 347 555 0103",
	),
	(
		"luca",
		"Luca",
		"Moretti",
		("operatore",),
		"osteopata",
		"Osteopata D.O., dolore cervicale e lombare",
		"+39 349 555 0104",
	),
	(
		"elena",
		"Elena",
		"Galli",
		("operatore",),
		"dietista",
		"Dietista, educazione alimentare e sport",
		"+39 340 555 0105",
	),
	(
		"davide",
		"Davide",
		"Marino",
		("operatore",),
		"chinesiologo",
		"Chinesiologo, pilates e ginnastica posturale",
		"+39 348 555 0106",
	),
)

#: Who works when: weekday -> (start, end) shifts, in the centre's clock.
TURNI = {
	"giulia": {
		"Monday": (("08:30", "13:00"), ("14:00", "19:00")),
		"Tuesday": (("08:30", "13:00"), ("14:00", "19:00")),
		"Wednesday": (("08:30", "13:00"), ("14:00", "19:00")),
		"Thursday": (("08:30", "13:00"), ("14:00", "19:00")),
		"Friday": (("08:30", "13:00"), ("14:00", "18:00")),
		"Saturday": (("09:00", "13:00"),),
	},
	"luca": {
		"Monday": (("09:00", "13:00"), ("14:00", "18:00")),
		"Tuesday": (("14:00", "20:00"),),
		"Wednesday": (("09:00", "13:00"), ("14:00", "18:00")),
		"Thursday": (("14:00", "20:00"),),
		"Friday": (("09:00", "13:00"), ("14:00", "18:00")),
	},
	"elena": {
		"Tuesday": (("09:00", "13:00"), ("14:00", "18:00")),
		"Thursday": (("09:00", "13:00"), ("14:00", "18:00")),
		"Friday": (("14:00", "19:00"),),
		"Saturday": (("09:00", "13:00"),),
	},
	"davide": {
		"Monday": (("17:30", "21:00"),),
		"Tuesday": (("07:30", "09:30"), ("18:00", "21:00")),
		"Wednesday": (("17:30", "21:00"),),
		"Thursday": (("07:30", "09:30"), ("18:00", "21:00")),
		"Friday": (("17:30", "20:30"),),
		"Sunday": (("09:30", "12:00"),),
	},
}

# -- rooms and services ---------------------------------------------------------------------

#: Where each colleague works: their appointments take their room.
STUDIO = {"giulia": "studio1", "luca": "studio2", "elena": "studio3", "davide": "palestra"}

#: key, name, type, seats, colour, description
STANZE = (
	("studio1", "Studio 1", "Room", 0, "#4F8EDC", "Lettino elettrico, tecar e laser"),
	("studio2", "Studio 2", "Room", 0, "#8B6FD6", "Lettino per osteopatia"),
	("studio3", "Studio 3", "Room", 0, "#3FA36B", "Scrivania, bilancia impedenziometrica"),
	("palestra", "Palestra", "Room", 8, "#E08A3C", "Otto reformer, tappetini e piccoli attrezzi"),
)

#: key, name, category, minutes, price, staff keys, room key, max participants,
#: per participant, bookable online, colour, description
SERVIZI = (
	(
		"prima_fisio",
		"Prima visita fisioterapica",
		"Fisioterapia",
		45,
		60,
		("giulia",),
		"studio1",
		1,
		False,
		True,
		"#4F8EDC",
		"Valutazione, test funzionali e programma di trattamento.",
	),
	(
		"fisio",
		"Seduta di fisioterapia",
		"Fisioterapia",
		45,
		50,
		("giulia",),
		"studio1",
		1,
		False,
		False,
		"#5B9BE6",
		"Terapia manuale ed esercizio terapeutico.",
	),
	(
		"tecar",
		"Tecar terapia",
		"Fisioterapia",
		30,
		40,
		("giulia",),
		"studio1",
		1,
		False,
		False,
		"#7FB2EE",
		"Diatermia per tendiniti, contratture e recupero dopo un trauma.",
	),
	(
		"massaggio",
		"Massaggio decontratturante",
		"Fisioterapia",
		50,
		55,
		("giulia", "luca"),
		"studio1",
		1,
		False,
		True,
		"#2E7BCF",
		"Per collo, schiena e gambe affaticate.",
	),
	(
		"prima_osteo",
		"Prima visita osteopatica",
		"Osteopatia",
		60,
		80,
		("luca",),
		"studio2",
		1,
		False,
		True,
		"#8B6FD6",
		"Anamnesi, valutazione e primo trattamento.",
	),
	(
		"osteo",
		"Trattamento osteopatico",
		"Osteopatia",
		50,
		70,
		("luca",),
		"studio2",
		1,
		False,
		True,
		"#9D85E0",
		"Trattamento di controllo.",
	),
	(
		"nutri",
		"Consulenza nutrizionale",
		"Nutrizione",
		60,
		80,
		("elena",),
		"studio3",
		1,
		False,
		True,
		"#3FA36B",
		"Anamnesi alimentare, misure e piano personalizzato.",
	),
	(
		"controllo_nutri",
		"Controllo nutrizionale",
		"Nutrizione",
		30,
		45,
		("elena",),
		"studio3",
		1,
		False,
		True,
		"#5DB884",
		"Misure, andamento e aggiustamenti del piano.",
	),
	(
		"pilates",
		"Pilates di gruppo",
		"Movimento",
		55,
		15,
		("davide",),
		"palestra",
		8,
		True,
		True,
		"#E08A3C",
		"Lezione su reformer, al massimo otto persone.",
	),
	(
		"posturale",
		"Ginnastica posturale",
		"Movimento",
		45,
		12,
		("davide",),
		"palestra",
		6,
		True,
		True,
		"#E8A35E",
		"Esercizi per schiena e postura, in piccolo gruppo.",
	),
)

#: The weekly classes: weekday, start, service key.
LEZIONI = (
	("Monday", "18:00", "pilates"),
	("Monday", "19:15", "posturale"),
	("Tuesday", "07:45", "pilates"),
	("Tuesday", "18:30", "pilates"),
	("Wednesday", "18:00", "pilates"),
	("Wednesday", "19:15", "pilates"),
	("Thursday", "07:45", "posturale"),
	("Thursday", "18:30", "pilates"),
	("Friday", "18:00", "posturale"),
	("Sunday", "10:00", "pilates"),
)

#: An agreement's prices, for a health insurance's members: service key -> price.
CONVENZIONE = ("Convenzione Salute+", {"fisio": 42, "osteo": 60, "nutri": 65})

#: The days the centre is closed, as month-day, with their names.
FESTIVITA = (
	("01-01", "Capodanno"),
	("01-06", "Epifania"),
	("04-25", "Festa della Liberazione"),
	("05-01", "Festa del lavoro"),
	("06-02", "Festa della Repubblica"),
	("08-15", "Ferragosto"),
	("11-01", "Ognissanti"),
	("12-08", "Immacolata Concezione"),
	("12-25", "Natale"),
	("12-26", "Santo Stefano"),
)

# -- the people ------------------------------------------------------------------------------

NOMI_DONNA = (
	"Giulia",
	"Francesca",
	"Sara",
	"Martina",
	"Valentina",
	"Alessandra",
	"Federica",
	"Silvia",
	"Laura",
	"Paola",
	"Roberta",
	"Simona",
	"Anna",
	"Maria",
	"Elisa",
	"Ilaria",
	"Beatrice",
	"Camilla",
	"Alice",
	"Giorgia",
	"Marta",
	"Sofia",
	"Noemi",
	"Arianna",
	"Claudia",
	"Monica",
	"Daniela",
	"Barbara",
	"Cristina",
	"Lucia",
	"Veronica",
	"Serena",
	"Michela",
	"Stefania",
	"Teresa",
	"Rita",
	"Carla",
	"Irene",
	"Nicoletta",
	"Emma",
)

NOMI_UOMO = (
	"Marco",
	"Andrea",
	"Matteo",
	"Alessandro",
	"Francesco",
	"Lorenzo",
	"Simone",
	"Stefano",
	"Riccardo",
	"Giovanni",
	"Roberto",
	"Fabio",
	"Daniele",
	"Gabriele",
	"Federico",
	"Emanuele",
	"Tommaso",
	"Nicola",
	"Antonio",
	"Giuseppe",
	"Massimo",
	"Claudio",
	"Alberto",
	"Enrico",
	"Filippo",
	"Pietro",
	"Edoardo",
	"Mattia",
	"Leonardo",
	"Michele",
	"Vincenzo",
	"Carlo",
	"Sergio",
	"Diego",
	"Giorgio",
	"Raffaele",
	"Ivan",
	"Bruno",
)

COGNOMI = (
	"Russo",
	"Ferrari",
	"Esposito",
	"Bianchi",
	"Colombo",
	"Ricci",
	"Greco",
	"Bruno",
	"Gallo",
	"Conti",
	"De Luca",
	"Mancini",
	"Costa",
	"Giordano",
	"Rizzo",
	"Lombardi",
	"Barbieri",
	"Fontana",
	"Santoro",
	"Mariani",
	"Caruso",
	"Ferrara",
	"Martini",
	"Leone",
	"Longo",
	"Gentile",
	"Martinelli",
	"Vitale",
	"Lombardo",
	"Serra",
	"Coppola",
	"De Santis",
	"D'Angelo",
	"Marchetti",
	"Parisi",
	"Villa",
	"Conte",
	"Ferraro",
	"Fabbri",
	"Bianco",
	"Marini",
	"Grasso",
	"Valentini",
	"Messina",
	"Sala",
	"De Angelis",
	"Gatti",
	"Pellegrini",
	"Palumbo",
	"Sanna",
	"Farina",
	"Rizzi",
	"Monti",
	"Cattaneo",
	"Morelli",
	"Amato",
	"Silvestri",
	"Mazza",
	"Testa",
	"Carbone",
	"Giuliani",
	"Benedetti",
	"Barone",
	"Rossetti",
	"Caputo",
	"Montanari",
	"Guerra",
	"Palmieri",
	"Bernardi",
	"Fiore",
	"De Rosa",
	"Ferretti",
	"Bellini",
	"Basile",
	"Riva",
	"Donati",
	"Piras",
	"Sartori",
	"Neri",
	"Milani",
	"Pagano",
	"Ruggiero",
	"Sorrentino",
	"Orlando",
	"Negri",
)

#: The mobile prefixes the demo's numbers start with, after +39.
PREFISSI = (
	"320",
	"328",
	"329",
	"333",
	"334",
	"338",
	"339",
	"340",
	"345",
	"347",
	"348",
	"349",
	"366",
	"380",
	"389",
	"392",
	"393",
)

#: Where people came from (CRM Lead Source), with how often.
FONTI = (
	("Website", 26),
	("Reference", 24),
	("Instagram", 14),
	("Facebook", 8),
	("Advertisement", 10),
	("Walk In", 10),
	("Online booking", 8),
)

#: Companies the centre works with: key, name, industry, employees, the person who
#: deals with the centre (first, last, job title, gender).
AZIENDE = (
	(
		"tecnoprogetti",
		"Tecnoprogetti Srl",
		"Technology",
		"51-200",
		("Valeria", "Ricciardi", "Responsabile risorse umane", "Female"),
	),
	(
		"studio_bianchi",
		"Studio Legale Bianchi & Associati",
		"Legal",
		"11-50",
		("Ernesto", "Bianchi", "Socio fondatore", "Male"),
	),
	(
		"olimpia",
		"Palestra Olimpia",
		"Sports",
		"11-50",
		("Marco", "Tedeschi", "Direttore tecnico", "Male"),
	),
	(
		"farmacia",
		"Farmacia San Marco",
		"Pharmaceuticals",
		"1-10",
		("Lucia", "Vianello", "Titolare", "Female"),
	),
	(
		"adriatica",
		"Logistica Adriatica SpA",
		"Transportation",
		"201-500",
		("Gianluca", "Ferrante", "Responsabile sicurezza e salute", "Male"),
	),
)

#: The agreements with the companies: company key, title, stage (by type and step in
#: the default pipeline), value, days since it opened, days to the expected close,
#: lost reason.
ACCORDI = (
	("tecnoprogetti", "Welfare aziendale: fisioterapia per i dipendenti", ("Ongoing", 2), 6000, 34, 20, None),
	("studio_bianchi", "Prevenzione posturale per lo studio", ("Won", 0), 2400, 52, -18, None),
	("olimpia", "Rieducazione sportiva per gli iscritti", ("Ongoing", 3), 3500, 21, 30, None),
	(
		"farmacia",
		"Giornate di screening posturale in farmacia",
		("Lost", 0),
		1200,
		45,
		-9,
		"Budget Constraints",
	),
	("adriatica", "Programma schiena sana per i magazzinieri", ("Open", 0), 9000, 6, 60, None),
)

#: A family: the parent books for the child, and pays.
FAMIGLIA = (
	("Francesca", "Lodi", "Female", "+39 347 555 0711"),
	("Tommaso", "Lodi", "Male", None),
)

# -- what people need, and how they come back ----------------------------------------------------

#: A path: the first service, the one after it, how many times after (min, max), the
#: days between them (min, max).
PERCORSI = {
	"fisio": ("prima_fisio", "fisio", (4, 9), (3, 7)),
	"tecar": ("prima_fisio", "tecar", (3, 5), (3, 5)),
	"osteo": ("prima_osteo", "osteo", (2, 4), (10, 21)),
	"nutri": ("nutri", "controllo_nutri", (2, 4), (14, 28)),
	"massaggio": ("massaggio", "massaggio", (1, 3), (10, 21)),
}

#: What a person's appointments are for, with how often.
BISOGNI = (
	("fisio", 30),
	("tecar", 8),
	("osteo", 20),
	("nutri", 17),
	("massaggio", 8),
	("lezioni", 17),
)

#: Why an appointment was cancelled.
DISDETTE = (
	"Influenza, chiede di spostare",
	"Impegno di lavoro improvviso",
	"Ha disdetto per telefono",
	"Bambino malato",
	"Spostato su sua richiesta",
	"Sciopero dei mezzi",
)

# -- deals of the new clients pipeline ------------------------------------------------------------

#: Why a request went nowhere (CRM Lost Reason), with the note the desk wrote.
PERSI = (
	("Unresponsive Prospect", "Richiamata tre volte, non risponde."),
	("Pricing", "Cercava un prezzo più basso, ha scelto un centro convenzionato."),
	("Long Sales Cycle", "Ci pensa dopo l'estate."),
	("Other", "Si è trasferita in un'altra città."),
)

# -- tasks, notes, calls --------------------------------------------------------------------------

#: title, description, who does it (team key, or "io" for whoever loads the demo),
#: priority, status, due in days (negative: overdue), about a person (True) or not.
COSE_DA_FARE = (
	(
		"Richiamare per fissare il controllo",
		"Ha finito il ciclo, proporre il controllo a un mese.",
		"desk",
		"High",
		"Todo",
		0,
		True,
	),
	(
		"Confermare gli appuntamenti di domani",
		"Telefonata o messaggio a chi non ha confermato.",
		"desk",
		"High",
		"Todo",
		0,
		False,
	),
	(
		"Inviare il riepilogo delle sedute",
		"Lo chiede per il rimborso dell'assicurazione.",
		"desk",
		"Medium",
		"Todo",
		1,
		True,
	),
	(
		"Preparare la proposta per Tecnoprogetti",
		"Pacchetto da dieci sedute per dipendente, prezzi della convenzione.",
		"manager",
		"High",
		"In Progress",
		2,
		False,
	),
	(
		"Ordinare gli elastici per la palestra",
		"Fasce di tre resistenze, almeno venti.",
		"davide",
		"Low",
		"Todo",
		5,
		False,
	),
	(
		"Richiamare: ha chiesto informazioni sul pilates",
		"Preferisce le lezioni del mattino.",
		"desk",
		"Medium",
		"Todo",
		-1,
		True,
	),
	(
		"Aggiornare il programma di esercizi",
		"Aggiungere il lavoro propriocettivo dalla prossima seduta.",
		"giulia",
		"Medium",
		"Todo",
		2,
		True,
	),
	(
		"Rivedere il piano alimentare",
		"Ha perso due chili, ridurre gli spuntini serali.",
		"elena",
		"Medium",
		"In Progress",
		3,
		True,
	),
	(
		"Chiedere il referto della risonanza",
		"Serve prima del prossimo trattamento.",
		"luca",
		"High",
		"Todo",
		-2,
		True,
	),
	(
		"Organizzare la serata sulla postura",
		"Incontro aperto agli iscritti della Palestra Olimpia.",
		"io",
		"Medium",
		"Backlog",
		14,
		False,
	),
	(
		"Controllare le disponibilità di agosto",
		"Ferie del team e chiusura del centro.",
		"io",
		"Low",
		"Todo",
		10,
		False,
	),
	(
		"Telefonare per la disdetta di ieri",
		"Capire se vuole recuperare la seduta.",
		"desk",
		"Medium",
		"Todo",
		-1,
		True,
	),
	(
		"Mandare le istruzioni per la prima visita",
		"Portare scarpe comode e gli esami recenti.",
		"desk",
		"Low",
		"Done",
		-3,
		True,
	),
	(
		"Fattura per la convenzione dello Studio Bianchi",
		"Prima rata del pacchetto annuale.",
		"manager",
		"Medium",
		"Done",
		-6,
		False,
	),
	("Proposta del ciclo di tecar", "Cinque sedute, due a settimana.", "giulia", "Medium", "Done", -4, True),
	(
		"Verificare il recupero dopo la distorsione",
		"Test di equilibrio alla prossima seduta.",
		"giulia",
		"Low",
		"Todo",
		6,
		True,
	),
	(
		"Prenotare il controllo a tre settimane",
		"Ha lasciato detto di chiamarla dopo le 18.",
		"desk",
		"Medium",
		"Todo",
		2,
		True,
	),
	(
		"Rispondere alla richiesta dal sito",
		"Chiede se trattiamo la cefalea muscolo-tensiva.",
		"io",
		"High",
		"Todo",
		0,
		True,
	),
	(
		"Preparare la lista d'attesa del pilates",
		"Chi aspetta un posto al giovedì sera.",
		"davide",
		"Medium",
		"Todo",
		1,
		False,
	),
	(
		"Chiudere la convenzione con la Palestra Olimpia",
		"Ultimo incontro fissato per la prossima settimana.",
		"manager",
		"High",
		"Todo",
		7,
		False,
	),
	(
		"Inviare il questionario sulle abitudini alimentari",
		"Da compilare prima della consulenza.",
		"elena",
		"Low",
		"Done",
		-2,
		True,
	),
	(
		"Riprogrammare le sedute dopo le ferie",
		"Rientra lunedì, tre sedute da recuperare.",
		"desk",
		"Medium",
		"Canceled",
		-5,
		True,
	),
)

#: title, words, who wrote it, about a person (True) or a company agreement (False).
NOTE = (
	(
		"Preferenze per gli appuntamenti",
		"<p>Preferisce gli appuntamenti dopo le 17, lavora su turni fino alle 16.</p>",
		"desk",
		True,
	),
	(
		"Dolore lombare",
		"<p>Dolore lombare da tre settimane, lavora molte ore al computer. Nessun trauma, peggiora la sera.</p>",
		"giulia",
		True,
	),
	(
		"Obiettivo",
		"<p>Vuole tornare a correre la mezza maratona di primavera. Programma graduale, controllo dopo quattro settimane.</p>",
		"giulia",
		True,
	),
	(
		"Dopo il primo trattamento",
		"<p>Riferisce meno rigidità al collo al risveglio. Ricontrollo tra tre settimane.</p>",
		"luca",
		True,
	),
	(
		"Abitudini alimentari",
		"<p>Salta spesso la colazione, pranzo veloce in ufficio. Proposto un piano con spuntini semplici da portare al lavoro.</p>",
		"elena",
		True,
	),
	(
		"Andamento",
		"<p>Meno due chili in un mese, energia migliore nel pomeriggio. Proseguiamo con lo stesso piano.</p>",
		"elena",
		True,
	),
	(
		"Lezioni di gruppo",
		"<p>Viene con la sorella, chiedono di stare nella stessa lezione del mercoledì.</p>",
		"davide",
		True,
	),
	(
		"Telefonata",
		"<p>Ha chiamato per sapere se la seduta si può pagare con il bancomat: sì, anche con il telefono.</p>",
		"desk",
		True,
	),
	(
		"Esami",
		"<p>Ha portato la risonanza del ginocchio: lesione parziale del menisco mediale, nessuna indicazione chirurgica.</p>",
		"giulia",
		True,
	),
	(
		"Rimborso",
		"<p>Ha un'assicurazione sanitaria aziendale: servono le fatture con la descrizione delle sedute.</p>",
		"desk",
		True,
	),
	(
		"Prossimi passi",
		"<p>Dopo il ciclo di fisioterapia consigliato il pilates due volte a settimana per mantenere il risultato.</p>",
		"giulia",
		True,
	),
	(
		"Primo contatto",
		"<p>Ha trovato il centro su Instagram, chiede un trattamento per la cervicale prima delle vacanze.</p>",
		"desk",
		True,
	),
	(
		"Postura",
		"<p>Spalle chiuse e testa in avanti, lavora in negozio in piedi. Esercizi da fare a casa due volte al giorno.</p>",
		"davide",
		True,
	),
	(
		"Incontro con l'azienda",
		"<p>Interessati a un pacchetto per circa quaranta dipendenti. Vogliono una giornata di valutazione in sede.</p>",
		"manager",
		False,
	),
	(
		"Condizioni proposte",
		"<p>Dieci per cento di sconto sulle sedute e una valutazione posturale gratuita per ogni dipendente.</p>",
		"manager",
		False,
	),
	(
		"Budget",
		"<p>Il budget per quest'anno è già stato impegnato. Riprendere i contatti a gennaio.</p>",
		"manager",
		False,
	),
)

#: The calls of the last weeks: incoming or outgoing, the outcome, minutes, the
#: callback, whether a message was left, who took it, what it was about.
CHIAMATE = (
	("Incoming", "Completed", 3, None, False, "desk"),
	("Incoming", "Completed", 5, None, False, "desk"),
	("Outgoing", "Completed", 2, None, False, "desk"),
	("Incoming", "No Answer", 0, "Pending", True, "desk"),
	("Outgoing", "No Answer", 0, None, False, "desk"),
	("Incoming", "Completed", 7, None, False, "giulia"),
	("Outgoing", "Completed", 4, None, False, "elena"),
	("Incoming", "Busy", 0, "Done", False, "desk"),
	("Outgoing", "Completed", 1, None, False, "desk"),
	("Incoming", "Completed", 2, None, False, "desk"),
	("Incoming", "No Answer", 0, "Pending", False, "desk"),
	("Outgoing", "Completed", 6, None, False, "luca"),
	("Incoming", "Completed", 4, None, False, "desk"),
	("Outgoing", "Completed", 3, None, False, "manager"),
	("Incoming", "No Answer", 0, "Done", True, "desk"),
	("Outgoing", "Completed", 2, None, False, "desk"),
)

# -- cycles and quotes, agreed at the first visit ----------------------------------------------

#: A cycle of sessions sold at the first visit: the sessions' service key -> the packs
#: on sale, sessions -> price of the whole cycle.
CICLI = {
	"fisio": {5: 230, 10: 440},
	"tecar": {5: 180},
}

#: What a cycle is for, as the desk writes it on the cycle.
NOTE_CICLI = {
	"fisio": (
		"Lombalgia: terapia manuale ed esercizio terapeutico.",
		"Riabilitazione dopo una distorsione di caviglia.",
		"Cervicalgia, rieducazione posturale.",
		"Spalla dolorosa, rinforzo della cuffia dei rotatori.",
		"Ginocchio dopo la ricostruzione del crociato.",
	),
	"tecar": (
		"Tendinopatia rotulea.",
		"Contrattura al polpaccio.",
		"Epicondilite al gomito destro.",
	),
}

#: The quote a practitioner proposes after the first visit, by path: its title, the
#: words for the person, the discount on each session (%).
PREVENTIVI = {
	"fisio": (
		"Percorso di fisioterapia",
		"Sedute settimanali di terapia manuale ed esercizio terapeutico, poi un controllo a un mese.",
		10,
	),
	"osteo": (
		"Ciclo di trattamenti osteopatici",
		"Trattamenti a distanza di due o tre settimane, secondo come risponde al primo.",
		0,
	),
	"nutri": (
		"Percorso nutrizionale",
		"Piano alimentare personalizzato, con un controllo ogni tre o quattro settimane.",
		5,
	),
}

#: How the person said yes to a quote.
SI_AL_PREVENTIVO = (
	"Firmato in studio dopo la visita.",
	"Confermato per email.",
	"Accettato al telefono con la segreteria.",
)

#: Why a quote was declined (CRM Lost Reason), with what the person said.
NO_AL_PREVENTIVO = (
	("Pricing", "Preferisce pagare seduta per seduta."),
	("Other", "Ha scelto un centro più vicino a casa."),
	("Long Sales Cycle", "Ci pensa e si fa sentire dopo le vacanze."),
)

# -- subscriptions to the classes -------------------------------------------------------------

#: key, name, months, payment, price, how the entries count, entries in that week or
#: month, the services it comprises, the most days of suspension (0: none), the days
#: of the reminder before the end, renewed by itself, description.
ABBONAMENTI = (
	(
		"pilates8",
		"Pilates · 8 ingressi al mese",
		1,
		"Upfront",
		110,
		"Per month",
		8,
		("pilates",),
		0,
		5,
		True,
		"Fino a otto lezioni di Pilates al mese. Si rinnova da solo ogni mese.",
	),
	(
		"posturale",
		"Ginnastica posturale · 3 mesi",
		3,
		"Upfront",
		130,
		"Per week",
		2,
		("posturale",),
		21,
		10,
		False,
		"Due lezioni a settimana per tre mesi, sospendibile per le vacanze.",
	),
	(
		"open",
		"Movimento open · 6 mesi",
		6,
		"Monthly",
		390,
		"Unlimited",
		0,
		("pilates", "posturale"),
		30,
		14,
		False,
		"Tutte le lezioni di gruppo per sei mesi, con il pagamento in rate mensili.",
	),
)
