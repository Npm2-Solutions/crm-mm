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
		"Trattamento fisioterapico",
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

# -- the waiting list --------------------------------------------------------------------------

#: Who waits for what: the service key, the practitioner's key (None: anybody), the
#: days and hours that suit (weekday, from, to), urgent, where they joined, the
#: desk's note, how many days ago they joined, what happened (None: still waiting,
#: "offered", "booked", "expired", "removed").
ATTESE = (
	(
		"osteo",
		"luca",
		(("Monday", "09:00", "13:00"), ("Wednesday", "09:00", "13:00")),
		True,
		"Desk",
		"Dolore acuto alla schiena da tre giorni: va bene anche un posto all'ultimo momento.",
		1,
		"offered",
	),
	(
		"osteo",
		"luca",
		(("Tuesday", "17:00", "20:00"), ("Thursday", "17:00", "20:00")),
		False,
		"Online",
		None,
		5,
		None,
	),
	("osteo", None, (), False, "Client area", None, 9, None),
	(
		"nutri",
		"elena",
		(("Tuesday", "14:00", "18:00"), ("Thursday", "14:00", "18:00")),
		False,
		"Desk",
		"Vuole iniziare prima delle vacanze di Natale.",
		4,
		"booked",
	),
	(
		"fisio",
		"giulia",
		(("Saturday", "09:00", "13:00"),),
		False,
		"Online",
		"Lavora tutta la settimana, solo il sabato mattina.",
		3,
		None,
	),
	("massaggio", None, (("Friday", "14:00", "18:00"),), False, "Desk", None, 12, "booked"),
	(
		"osteo",
		"luca",
		(),
		False,
		"Desk",
		"Ha trovato posto in un altro centro, toglierla dalla lista.",
		16,
		"removed",
	),
	("nutri", None, (), False, "Online", None, 34, "expired"),
)

#: How many people wait for a seat in the class that is full.
IN_ATTESA_DELLA_LEZIONE = 2

# -- the conversations ---------------------------------------------------------------------------

#: Emails with the centre: the subject, who writes in the centre ("desk", a
#: practitioner's key, or "pratico": whoever the person sees), how it ends ("done":
#: dealt with, "open": waiting for the centre, "later": parked a few days), then the
#: messages: who writes ("lui" the person, "noi" the centre), the hours after the one
#: before, the words. {nome} is the person's first name, {firma} who signs.
EMAIL = (
	(
		"Prima visita fisioterapica",
		"desk",
		"done",
		(
			(
				"lui",
				0,
				"Buongiorno,\n\nvorrei prenotare una prima visita fisioterapica per un dolore alla spalla "
				"destra. Avete posto la prossima settimana, possibilmente di pomeriggio?\n\nGrazie,\n{nome}",
			),
			(
				"noi",
				3,
				"Buongiorno {nome},\n\ncertamente: la dottoressa Ferri ha posto martedì alle 17:15 oppure "
				"giovedì alle 15:00. Ci dica quale preferisce e la confermiamo.\n\nUn saluto,\n{firma}",
			),
			("lui", 2, "Giovedì alle 15:00 va benissimo, grazie!"),
			(
				"noi",
				1,
				"Perfetto, è confermata per giovedì alle 15:00. Il giorno prima le arriverà un "
				"promemoria.\n\nA presto,\n{firma}",
			),
		),
	),
	(
		"Fattura per la dichiarazione dei redditi",
		"desk",
		"done",
		(
			(
				"lui",
				0,
				"Buongiorno,\n\nmi servirebbero le fatture delle sedute di settembre per la detrazione. "
				"Il codice fiscale è quello che vi ho lasciato alla prima visita.\n\nGrazie mille,\n{nome}",
			),
			(
				"noi",
				4,
				"Buongiorno {nome},\n\nle fatture sono pronte: le trova nella sua area personale, nella "
				"sezione Fatture. Se preferisce, gliele stampiamo alla prossima seduta.\n\nUn saluto,\n{firma}",
			),
			("lui", 5, "Trovate, grazie per la rapidità!"),
		),
	),
	(
		"Spostare l'appuntamento di giovedì",
		"desk",
		"open",
		(
			(
				"lui",
				0,
				"Buongiorno,\n\ngiovedì ho una riunione che si è allungata: si può spostare la seduta a "
				"venerdì, anche nel tardo pomeriggio?\n\nScusate il preavviso,\n{nome}",
			),
		),
	),
	(
		"Referto della risonanza",
		"giulia",
		"done",
		(
			(
				"lui",
				0,
				"Buongiorno dottoressa,\n\nho ritirato il referto della risonanza al ginocchio: parla di una "
				"lesione parziale del menisco mediale. Devo portarlo alla prossima seduta?\n\n{nome}",
			),
			(
				"noi",
				6,
				"Buongiorno {nome},\n\nsì, lo porti pure con le immagini: lo guardiamo insieme e adattiamo "
				"gli esercizi. Nel frattempo continui con quelli che le ho dato, senza carichi.\n\n{firma}",
			),
		),
	),
	(
		"Convenzione Salute+",
		"desk",
		"done",
		(
			(
				"lui",
				0,
				"Buonasera,\n\nho l'assicurazione Salute+ tramite l'azienda: siete convenzionati? Mi "
				"interesserebbero dei trattamenti osteopatici.\n\n{nome}",
			),
			(
				"noi",
				14,
				"Buongiorno {nome},\n\nsì, siamo convenzionati: con Salute+ un trattamento osteopatico costa "
				"60 € invece di 70 €. Basta mostrare la tessera alla prima visita.\n\nUn saluto,\n{firma}",
			),
			("lui", 3, "Ottimo, allora vi chiamo per fissare. Grazie!"),
		),
	),
	(
		"Lezione di prova di Pilates",
		"desk",
		"done",
		(
			(
				"lui",
				0,
				"Ciao,\n\nvorrei provare il Pilates di gruppo: si può fare una lezione di prova? Lavoro fino "
				"alle 17, quindi mi andrebbero bene le lezioni serali.\n\n{nome}",
			),
			(
				"noi",
				2,
				"Ciao {nome},\n\ncerto! La prova è gratuita: ci sono le lezioni del lunedì e del mercoledì "
				"alle 18:00. Ti segno per lunedì?\n\n{firma}",
			),
			("lui", 1, "Sì, lunedì alle 18:00. Porto il tappetino?"),
			("noi", 1, "Non serve, li abbiamo noi. Basta un abbigliamento comodo e le calze antiscivolo!"),
		),
	),
	(
		"Disdetta per influenza",
		"desk",
		"later",
		(
			(
				"lui",
				0,
				"Buongiorno,\n\nho la febbre da ieri, purtroppo devo disdire la seduta di domani. Vi "
				"richiamo io appena sto meglio.\n\n{nome}",
			),
			(
				"noi",
				2,
				"Buongiorno {nome},\n\nnessun problema, abbiamo disdetto la seduta. Si riguardi: la "
				"ricontattiamo noi tra qualche giorno per fissare la prossima.\n\nBuona guarigione,\n{firma}",
			),
		),
	),
	(
		"Domanda sul piano alimentare",
		"elena",
		"open",
		(
			(
				"lui",
				0,
				"Buongiorno dottoressa,\n\nnel piano a pranzo c'è il riso integrale: posso sostituirlo con "
				"il farro o con la pasta integrale? E lo spuntino del pomeriggio si può spostare dopo la "
				"palestra?\n\nGrazie,\n{nome}",
			),
		),
	),
	(
		"Grazie di tutto",
		"pratico",
		"done",
		(
			(
				"lui",
				0,
				"Buongiorno,\n\nvolevo solo ringraziarvi: dopo le sedute la schiena va molto meglio e ho "
				"ripreso a correre. Ci vediamo per il controllo!\n\n{nome}",
			),
		),
	),
	(
		"Parcheggio",
		"desk",
		"done",
		(
			(
				"lui",
				0,
				"Buongiorno, c'è un parcheggio vicino al centro? Vengo in auto la prima volta.\n\n{nome}",
			),
			(
				"noi",
				1,
				"Buongiorno {nome},\n\nsì, in via Garibaldi c'è un parcheggio pubblico a due minuti a piedi, "
				"gratuito dopo le 19: è proprio dietro l'angolo.\n\n{firma}",
			),
		),
	),
	(
		"Abbonamento alle lezioni",
		"desk",
		"open",
		(
			(
				"lui",
				0,
				"Ciao,\n\nmi trovo bene con le lezioni di posturale: che abbonamenti avete? Verrei due volte "
				"a settimana.\n\n{nome}",
			),
			(
				"noi",
				3,
				"Ciao {nome},\n\nper due lezioni a settimana c'è l'abbonamento di tre mesi a 130 €, "
				"sospendibile per le vacanze. Se vuoi lo attiviamo dalla prossima lezione.\n\n{firma}",
			),
			("lui", 20, "Perfetto! Si può pagare con il bancomat alla prossima lezione?"),
		),
	),
	(
		"Come va dopo il percorso?",
		"pratico",
		"done",
		(
			(
				"noi",
				0,
				"Buongiorno {nome},\n\nè passato un mese dall'ultima seduta: come va? Se le fa piacere "
				"fissiamo un controllo per vedere come si mantengono i risultati.\n\nUn caro saluto,\n{firma}",
			),
			("lui", 26, "Buongiorno! Va molto bene, grazie. Mi faccio sentire a fine mese per il controllo."),
		),
	),
	(
		"Cosa portare alla prima visita",
		"desk",
		"done",
		(
			(
				"noi",
				0,
				"Buongiorno {nome},\n\nla aspettiamo per la prima visita. Se ha esami o referti recenti li "
				"porti con sé, insieme a un abbigliamento comodo.\n\nA presto,\n{firma}",
			),
		),
	),
	(
		"Certificato di frequenza",
		"desk",
		"open",
		(
			(
				"lui",
				0,
				"Buongiorno,\n\nil mio datore di lavoro mi chiede un'attestazione delle sedute fatte nelle "
				"ultime settimane. Me la potete preparare?\n\n{nome}",
			),
		),
	),
)

#: SMS with the centre, where the centre sends them: (who, hours after the one before,
#: words), how it ends. {quando} is the day and time of the person's next appointment.
SMS = (
	(
		(
			(
				"noi",
				0,
				"Promemoria: {quando} ha appuntamento al centro. Per disdire rispondi NO a questo messaggio.",
			),
			("lui", 1, "Ok grazie, ci sarò"),
		),
		"done",
	),
	(
		(
			(
				"noi",
				0,
				"Promemoria: {quando} ha appuntamento al centro. Per disdire rispondi NO a questo messaggio.",
			),
			("lui", 2, "Buongiorno, posso arrivare 10 minuti in ritardo?"),
		),
		"open",
	),
	(
		(("noi", 0, "Il centro resterà chiuso il 1° novembre. Buona festa da tutto il team!"),),
		"done",
	),
)

#: WhatsApp chats with the centre, where the centre has WhatsApp: the same shape.
WHATSAPP = (
	(
		(
			("lui", 0, "Buongiorno! Avete posto per un massaggio decontratturante questa settimana?"),
			("noi", 1, "Buongiorno {nome}! Venerdì alle 16:00 con la dottoressa Ferri, va bene?"),
			("lui", 1, "Perfetto, grazie mille 🙏"),
		),
		"done",
	),
	(
		(
			("noi", 0, "Ciao {nome}, ti ricordiamo la lezione di {quando}. A presto!"),
			("lui", 3, "Grazie! Domani però arrivo con 5 minuti di ritardo"),
		),
		"open",
	),
	(
		(
			("lui", 0, "Buonasera, ho dimenticato la borraccia in palestra ieri 😅"),
			("noi", 12, "Ciao {nome}, l'abbiamo trovata: è all'accoglienza, la puoi ritirare quando vuoi!"),
		),
		"done",
	),
)

# -- marketing -------------------------------------------------------------------------------

#: The demo's Meta page: its lead forms, by key - the name and the questions (key,
#: label, Meta's type). The ids the demo gives them are made up, never a real one.
META_MODULI = {
	"prima": (
		"Prenota la prima visita",
		(
			("full_name", "Nome e cognome", "FULL_NAME"),
			("email", "Email", "EMAIL"),
			("phone_number", "Cellulare", "PHONE"),
			("motivo", "Che cosa ti porta da noi?", "CUSTOM"),
		),
	),
	"info": (
		"Chiedi informazioni",
		(
			("full_name", "Nome e cognome", "FULL_NAME"),
			("email", "Email", "EMAIL"),
			("phone_number", "Cellulare", "PHONE"),
			("quando", "Quando preferisci essere richiamato?", "CUSTOM"),
		),
	),
}
#: Its campaigns: key, name, the ad set, the paths of the people they bring, the days
#: they ran (from, to: days ago, 0 still running), and their ads - key, name, title,
#: words, the form they open.
META_CAMPAGNE = (
	(
		"schiena",
		"Autunno in movimento",
		"Mal di schiena, 30-65 anni, 10 km",
		("fisio", "tecar", "osteo", "massaggio"),
		(100, 0),
		(
			(
				"schiena_dolore",
				"Mal di schiena? Prima visita",
				"Il mal di schiena non è normale",
				"Una valutazione con la fisioterapista e un piano per stare meglio, senza liste d'attesa.",
				"prima",
			),
			(
				"schiena_corsa",
				"Torna a correre senza dolore",
				"Torna a correre",
				"Fisioterapia sportiva e un programma per riprendere a correre, passo dopo passo.",
				"prima",
			),
		),
	),
	(
		"nutrizione",
		"Nutrizione: la prima visita",
		"Benessere e alimentazione, 25-55 anni",
		("nutri",),
		(75, 12),
		(
			(
				"nutri_piano",
				"Il tuo piano alimentare",
				"Mangiare bene, senza rinunce",
				"Una prima visita con la dietista e un piano su misura, con la lista della spesa nell'app.",
				"info",
			),
		),
	),
	(
		"pilates",
		"Pilates in piccoli gruppi",
		"Pilates e postura, 30-60 anni",
		("lezioni",),
		(45, 0),
		(
			(
				"pilates_gruppi",
				"Pilates: al massimo sei persone",
				"Pilates in piccoli gruppi",
				"Lezioni con il chinesiologo, al massimo sei persone: la prima è di prova.",
				"info",
			),
		),
	),
)
#: What an ad spends a day at the demo's full size, in euros; how many see it for
#: each euro, and the share of them who click.
META_SPESA = (4.0, 9.0)
META_IMPRESSIONI = (90, 160)
META_CLIC = (0.008, 0.02)
#: What people write in the forms' own questions, by the path they come for.
META_MOTIVI = {
	"fisio": (
		"Mal di schiena da qualche mese",
		"Dolore al collo, lavoro tutto il giorno al computer",
		"Mi fa male il ginocchio quando corro",
	),
	"tecar": ("Tendinite alla spalla", "Una distorsione che non passa"),
	"osteo": ("Mal di schiena", "La cervicale, soprattutto la mattina"),
	"massaggio": ("Contratture alla schiena", "Un massaggio dopo le gare"),
}
META_QUANDO = ("La mattina", "In pausa pranzo", "Dopo le 18")

#: The demo's automations, switched off - so that they never write to the centre's
#: own people: the centre switches on the ones it keeps. Key, title, what it does,
#: the trigger and its settings, whether it asks for the marketing consent, its steps.
#: «{cliente}» and «{area}» are the vertical's words, a clinic's patient and area.
AUTOMAZIONI = (
	(
		"benvenuto",
		"Benvenuto a chi diventa {cliente}",
		"Dopo la prima visita un'email di benvenuto, con dove trovare appuntamenti, moduli e "
		"documenti, e il segno «Nuovo {cliente}».",
		"Became Client",
		None,
		False,
		(
			{
				"type": "send_email",
				"subject": "Benvenuto, {{ first_name }}!",
				"message": "Ciao {{ first_name }}, grazie per averci scelto. Nell'{area} trovi i tuoi "
				"appuntamenti, i moduli da compilare e i tuoi documenti. A presto!",
			},
			{"type": "add_tag", "tag": "Nuovo {cliente}"},
		),
	),
	(
		"richiamo",
		"Richiamo dopo due mesi",
		"A chi non torna da due mesi e ha detto sì al marketing: un'email per sapere come sta, e "
		"una cosa da fare per la segreteria.",
		"Date Reminder",
		{"doctype": "CRM Lead", "date_field": "last_visit", "direction": "after", "offset_days": 60},
		True,
		(
			{
				"type": "send_email",
				"subject": "Come stai, {{ first_name }}?",
				"message": "Ciao {{ first_name }}, è passato un po' dalla tua ultima visita. Se vuoi "
				"prenotare un controllo, rispondi a questa email o chiamaci.",
			},
			{"type": "create_task", "title": "Richiamare {{ lead_name }} per un controllo", "due_in_days": 2},
		),
	),
	(
		"richiesta",
		"Nuova richiesta da un modulo",
		"Chi lascia i suoi dati in un modulo del sito o di Meta: una cosa da fare per richiamarlo in "
		"giornata.",
		"Lead Form Submitted",
		None,
		False,
		(
			{
				"type": "create_task",
				"title": "Richiamare {{ lead_name }}: ha chiesto informazioni",
				"due_in_days": 0,
			},
		),
	),
	(
		"assenza",
		"Assenza all'appuntamento",
		"Chi non si presenta riceve un'email per riprenotare, e la segreteria lo richiama il giorno dopo.",
		"Appointment No Show",
		None,
		False,
		(
			{
				"type": "send_email",
				"subject": "Oggi non ti abbiamo visto, {{ first_name }}",
				"message": "Ciao {{ first_name }}, oggi non sei riuscito a venire: vuoi spostare "
				"l'appuntamento? Rispondi a questa email o chiamaci.",
			},
			{"type": "create_task", "title": "Riprenotare {{ lead_name }}", "due_in_days": 1},
		),
	),
)

#: The centre's social profiles in the demo, on its page.
PROFILI_SOCIAL = ("Instagram", "Facebook")
#: Its posts: the day (from today: before, published; after, scheduled), the hour, the
#: words, the profiles.
POST_SOCIAL = (
	(
		-38,
		"18:30",
		"Riprendono le lezioni di Pilates in piccoli gruppi: al massimo sei persone, con il "
		"chinesiologo. La prima è di prova 💪",
		("Instagram", "Facebook"),
	),
	(
		-26,
		"12:30",
		"Mal di schiena da scrivania? Tre esercizi da fare in pausa pranzo, spiegati dalla nostra "
		"fisioterapista 👇",
		("Instagram",),
	),
	(
		-15,
		"09:00",
		"Una settimana al mese per la prevenzione: con la prima visita fisioterapica c'è anche il "
		"controllo della postura.",
		("Facebook",),
	),
	(
		-6,
		"19:00",
		"La ricetta della settimana dalla nostra dietista: zuppa di zucca e lenticchie, 380 kcal a "
		"porzione 🎃",
		("Instagram", "Facebook"),
	),
	(
		3,
		"18:00",
		"Novità: la fisioterapia sportiva anche il sabato mattina. Prenota dall'app o in accoglienza.",
		("Instagram",),
	),
	(
		7,
		"12:00",
		"Cinque domande al nostro osteopata: quando serve davvero un trattamento?",
		("Facebook",),
	),
	(
		12,
		"18:30",
		"Che cosa mangiare prima e dopo l'allenamento: i consigli della dietista per chi corre.",
		("Instagram", "Facebook"),
	),
)
#: A post somebody is still writing.
POST_BOZZA = "Le novità del mese: gli orari, i corsi nuovi, la settimana della prevenzione…"

#: The links whose clicks the centre counts: the address, where it goes, what it is
#: for, how many clicked it at the demo's full size.
LINK_TRACCIATI = (
	("prenota-instagram", "/prenota", "Il link nella bio di Instagram", 64),
	("volantino-pilates", "/prenota", "Il QR code del volantino delle lezioni di Pilates", 23),
)
