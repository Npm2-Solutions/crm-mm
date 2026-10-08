# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's words in the demo: its colleagues, its clinical sheets, what the
visits say, the documents, the dentist's services and the plans. Italian, as the
CRM's demo words are (`crm.demo.dati`)."""

from __future__ import annotations

# -- the colleagues the clinic brings ------------------------------------------------------

#: key, first name, last name, levels, qualification, public title, mobile
DIRETTRICE = (
	"direttrice",
	"Laura",
	"Bassi",
	("direzione", "operatore"),
	"medico_chirurgo",
	"Direttrice sanitaria, medico chirurgo",
	"+39 333 555 0107",
)
DENTISTA = (
	"dentista",
	"Marco",
	"Fontana",
	("operatore",),
	"odontoiatra",
	"Odontoiatra, conservativa e implantologia",
	"+39 346 555 0108",
)
TURNI_DENTISTA = {
	"Monday": (("09:00", "13:00"), ("14:00", "19:00")),
	"Wednesday": (("14:00", "20:00"),),
	"Friday": (("09:00", "13:00"), ("14:00", "18:00")),
}
#: key, name, type, seats, colour, description
STUDIO_DENTISTICO = (
	"studio4",
	"Studio 4",
	"Room",
	0,
	"#D9774B",
	"Riunito odontoiatrico e radiografico endorale",
)
#: key, name, minutes, price, colour, description
SERVIZI_DENTISTA = (
	(
		"prima_odonto",
		"Prima visita odontoiatrica",
		30,
		60,
		"#D9774B",
		"Visita, odontogramma e piano di cura.",
	),
	("igiene", "Igiene orale professionale", 45, 80, "#E39A6F", "Ablazione del tartaro e lucidatura."),
	("otturazione", "Otturazione", 45, 100, "#C9673D", "Otturazione in composito di una o più superfici."),
	(
		"devitalizzazione",
		"Devitalizzazione",
		60,
		280,
		"#B8582F",
		"Cura canalare del dente, in una o due sedute.",
	),
	("corona", "Corona in ceramica", 60, 650, "#A84E2A", "Corona in ceramica su dente devitalizzato."),
	("impianto", "Impianto", 90, 1200, "#97441F", "Impianto in titanio con la sua corona."),
)

# -- the answers a person gives about their health ---------------------------------------------

ALLERGIE = (
	("Nessuna nota", 70),
	("Nichel", 8),
	("Penicillina", 8),
	("Pollini e graminacee", 10),
	("Lattosio", 4),
)
FARMACI = (
	("Nessuno", 60),
	("Levotiroxina 50 mcg al mattino", 10),
	("Ramipril 5 mg", 8),
	("Pillola anticoncezionale", 10),
	("Ibuprofene al bisogno", 12),
)
PATOLOGIE = (
	("Nessuna", 65),
	("Ipotiroidismo", 10),
	("Ipertensione arteriosa", 10),
	("Asma lieve", 8),
	("Emicrania", 7),
)


def _campi_anamnesi() -> list[dict]:
	return [
		{"id": "allergie", "type": "text", "label": "Allergie", "summary": "allergies"},
		{"id": "farmaci", "type": "text", "label": "Farmaci", "summary": "medications"},
		{"id": "patologie", "type": "text", "label": "Patologie", "summary": "conditions"},
	]


# -- the physiotherapist's first visit -------------------------------------------------------

#: The reason -> (functional tests, assessment, plan).
FISIO = {
	"Lombalgia": (
		"Lasègue negativo a destra e a sinistra. Flessione del tronco limitata e dolorosa a fine "
		"corsa, estensione libera. Forza e sensibilità nella norma.",
		"Lombalgia meccanica aspecifica, senza segni neurologici. Contrattura dei paravertebrali "
		"lombari, controllo lombo-pelvico scarso.",
		"Dieci sedute, due a settimana: terapia manuale, esercizio terapeutico per il controllo "
		"lombo-pelvico, educazione alla postura al lavoro. Esercizi a casa tra una seduta e l'altra.",
	),
	"Cervicalgia": (
		"Rotazione del collo ridotta a destra, dolorosa a fine corsa. Spurling negativo. Punti "
		"trigger sul trapezio superiore destro.",
		"Cervicalgia muscolo-tensiva, legata alla postura alla scrivania.",
		"Sei sedute: terapia manuale e massoterapia, esercizi di mobilità e di rinforzo dei "
		"flessori profondi del collo; pause attive durante il lavoro.",
	),
	"Dolore alla spalla": (
		"Abduzione attiva dolorosa tra 70° e 120°. Hawkins e Neer positivi, Jobe debole e doloroso.",
		"Sindrome da conflitto subacromiale con tendinopatia del sovraspinato.",
		"Dieci sedute: controllo della scapola e rinforzo progressivo della cuffia dei rotatori, "
		"tecar nelle prime settimane. Per ora niente sforzi con le braccia sopra la testa.",
	),
	"Distorsione di caviglia": (
		"Gonfiore sotto il malleolo esterno in calo, dolore alla palpazione del legamento "
		"peroneo-astragalico anteriore. Cassetto anteriore negativo. Equilibrio su un piede "
		"instabile.",
		"Esiti di distorsione in inversione della caviglia, di secondo grado, a tre settimane dal trauma.",
		"Otto sedute: recupero della mobilità, rinforzo dei peronieri, propriocezione su superfici "
		"instabili; ritorno graduale alla corsa dalla quinta seduta.",
	),
	"Dolore al ginocchio": (
		"Dolore alla parte anteriore del ginocchio scendendo le scale e dopo la corsa. Test di "
		"Clarke positivo, menischi negativi, legamenti stabili.",
		"Sindrome femoro-rotulea, con debolezza dei glutei e del quadricipite.",
		"Dieci sedute: rinforzo di quadricipite e glutei, controllo del ginocchio nel gesto, "
		"gestione dei carichi della corsa. Tecar nelle prime sedute.",
	),
}
DA_QUANDO = ("Meno di un mese", "Da uno a tre mesi", "Più di tre mesi")

SCHEDA_FISIO = {
	"sections": [
		{
			"id": "motivo",
			"title": "Il motivo della visita",
			"fields": [
				{
					"id": "motivo",
					"type": "choice",
					"label": "Motivo",
					"required": True,
					"options": [{"label": motivo} for motivo in FISIO],
				},
				{
					"id": "da_quando",
					"type": "choice",
					"label": "Da quando",
					"options": [{"label": voce} for voce in DA_QUANDO],
				},
				{
					"id": "dolore",
					"type": "scale",
					"label": "Dolore",
					"min": 0,
					"max": 10,
					"min_label": "Nessuno",
					"max_label": "Il peggiore",
				},
			],
		},
		{"id": "anamnesi", "title": "Anamnesi", "fields": _campi_anamnesi()},
		{
			"id": "valutazione",
			"title": "Valutazione e piano",
			"fields": [
				{"id": "test", "type": "text", "label": "Test funzionali", "multiline": True},
				{
					"id": "valutazione",
					"type": "text",
					"label": "Valutazione funzionale",
					"multiline": True,
					"required": True,
				},
				{
					"id": "piano",
					"type": "text",
					"label": "Piano di trattamento",
					"multiline": True,
					"required": True,
				},
			],
		},
	]
}

#: What the physiotherapist notes after a session, from the third on.
NOTE_DI_SEDUTA = (
	"Dolore in calo (4 su 10). Proseguiamo con il rinforzo, aumentato il carico degli esercizi.",
	"Seduta ben tollerata. Mobilità quasi completa, resta un po' di rigidità a fine giornata.",
	"Peggiorata dopo un fine settimana di giardinaggio: seduta più leggera, solo terapia manuale.",
	"Esercizi a casa fatti con regolarità. Si vede: oggi nessun dolore nei test.",
	"Introdotti gli esercizi in piedi e su una gamba sola. Da ricontrollare la prossima volta.",
)
ADDENDUM = "Telefonata di controllo: dolore quasi sparito, il paziente fa gli esercizi tutti i giorni."

# -- the osteopath's visits, written freely ---------------------------------------------------

#: reason, history, what he found, what he did
OSTEO = (
	(
		"Cefalea muscolo-tensiva",
		"Mal di testa frontale due o tre volte a settimana, peggiore a fine giornata. Lavora al "
		"computer otto ore al giorno.",
		"Tensione dei muscoli suboccipitali e del trapezio, rigidità tra prima e seconda vertebra "
		"cervicale, diaframma poco mobile.",
		"Trattamento fasciale del rachide cervicale, tecniche sul diaframma. Consigliate pause "
		"attive al lavoro. Controllo tra due settimane.",
	),
	(
		"Lombalgia che ritorna",
		"Mal di schiena che si ripete da due anni, peggiore al mattino e dopo molte ore in auto.",
		"Disfunzione della sacro-iliaca destra, ileo-psoas destro accorciato, rigidità del passaggio "
		"tra colonna dorsale e lombare.",
		"Tecniche articolatorie sul bacino e sulla colonna lombare, allungamento dell'ileo-psoas. "
		"Controllo tra tre settimane.",
	),
	(
		"Dolore al collo dopo un colpo di frusta",
		"Tamponamento in auto due mesi fa: dolore al collo e alle spalle, sonno disturbato.",
		"Rigidità tra quinta e sesta vertebra cervicale, tensione degli scaleni e dei trapezi, "
		"nessun segno neurologico.",
		"Tecniche dolci, fasciali e muscolari, nessuna manipolazione. Rivalutazione tra due settimane.",
	),
	(
		"Dolore alla mandibola",
		"Dolore all'articolazione della mandibola a sinistra; di notte digrigna i denti.",
		"Masseteri e temporali tesi, apertura della bocca deviata a sinistra.",
		"Trattamento dei muscoli masticatori e del rachide cervicale alto. Consigliata la visita "
		"del dentista per valutare un bite.",
	),
)
OSCURATA = "Su richiesta del paziente: l'episodio resta a chi l'ha scritto."

# -- the dietitian's first visit ---------------------------------------------------------------

#: The goal -> the advice it ends with.
OBIETTIVI = {
	"Perdere peso": "Riduzione di circa 500 kcal al giorno rispetto al fabbisogno, cinque pasti, "
	"verdura a ogni pasto principale. Controllo tra un mese.",
	"Alimentazione per lo sport": "Carboidrati intorno agli allenamenti, proteine distribuite "
	"nei pasti, attenzione all'idratazione. Controllo prima della gara.",
	"Migliorare la digestione": "Pasti regolari e non abbondanti, cena leggera, meno fritti; un "
	"diario dei sintomi per due settimane.",
	"Mantenere il peso": "Nessuna riduzione: più legumi e pesce durante la settimana, meno "
	"dolci fuori pasto. Controllo tra tre mesi.",
}
PASTI = ("Due", "Tre", "Quattro", "Cinque")
ATTIVITA = ("Sedentaria", "Leggera", "Moderata", "Intensa")

SCHEDA_NUTRIZIONE = {
	"sections": [
		{
			"id": "misure",
			"title": "Le misure",
			"fields": [
				{
					"id": "peso",
					"type": "number",
					"label": "Peso",
					"unit": "kg",
					"decimals": 1,
					"required": True,
					"summary": "weight",
				},
				{
					"id": "altezza",
					"type": "number",
					"label": "Altezza",
					"unit": "cm",
					"required": True,
					"summary": "height",
				},
				{
					"id": "imc",
					"type": "calc",
					"label": "Indice di massa corporea",
					"formula": "peso / (altezza / 100) ^ 2",
					"decimals": 1,
					"unit": "kg/m²",
				},
				{"id": "vita", "type": "number", "label": "Circonferenza vita", "unit": "cm"},
			],
		},
		{
			"id": "abitudini",
			"title": "Le abitudini",
			"fields": [
				{
					"id": "pasti",
					"type": "choice",
					"label": "Pasti al giorno",
					"options": [{"label": voce} for voce in PASTI],
				},
				{
					"id": "attivita",
					"type": "choice",
					"label": "Attività fisica",
					"options": [{"label": voce} for voce in ATTIVITA],
				},
				*_campi_anamnesi(),
			],
		},
		{
			"id": "obiettivo",
			"title": "L'obiettivo",
			"fields": [
				{
					"id": "obiettivo",
					"type": "choice",
					"label": "Obiettivo",
					"required": True,
					"options": [{"label": voce} for voce in OBIETTIVI],
				},
				{
					"id": "indicazioni",
					"type": "text",
					"label": "Indicazioni",
					"multiline": True,
					"required": True,
				},
			],
		},
	]
}

# -- the dentist's first visit ---------------------------------------------------------------

MOTIVI_DENTISTA = ("Controllo", "Dolore a un dente", "Gengive che sanguinano", "Dente mancante")
IGIENE = ("Buona", "Discreta", "Scarsa")
GENGIVE = ("Sane", "Gengivite", "Parodontite iniziale")

SCHEDA_DENTISTA = {
	"sections": [
		{"id": "anamnesi", "title": "Anamnesi", "fields": _campi_anamnesi()},
		{
			"id": "esame",
			"title": "Esame",
			"fields": [
				{
					"id": "motivo",
					"type": "choice",
					"label": "Motivo",
					"required": True,
					"options": [{"label": voce} for voce in MOTIVI_DENTISTA],
				},
				{
					"id": "igiene",
					"type": "choice",
					"label": "Igiene orale",
					"options": [{"label": voce} for voce in IGIENE],
				},
				{
					"id": "gengive",
					"type": "choice",
					"label": "Gengive",
					"options": [{"label": voce} for voce in GENGIVE],
				},
				{"id": "esame", "type": "text", "label": "Esame obiettivo", "multiline": True},
				{
					"id": "piano",
					"type": "text",
					"label": "Piano di cura",
					"multiline": True,
					"required": True,
				},
			],
		},
	]
}
#: The teeth a cavity is found in, and the surfaces it takes.
DENTI_POSTERIORI = (
	"14",
	"15",
	"16",
	"17",
	"24",
	"25",
	"26",
	"27",
	"34",
	"35",
	"36",
	"37",
	"44",
	"45",
	"46",
	"47",
)
SUPERFICI = ("O", "OD", "MO", "D", "M", "OV")
NOTE_PIANO = (
	"Le cure in due fasi: prima l'igiene e le otturazioni, poi il resto. I prezzi valgono tre mesi.",
	"Si comincia dall'igiene; le otturazioni nelle sedute dopo, una arcata alla volta.",
)

# -- the documents the clinic files -----------------------------------------------------------

#: The reason of a first visit -> (title, the report the person brought).
IMMAGINI = {
	"Dolore al ginocchio": (
		"Risonanza magnetica del ginocchio",
		"Condropatia femoro-rotulea di primo grado. Menischi e legamenti crociati integri. Minimo "
		"versamento articolare.",
	),
	"Dolore alla spalla": (
		"Ecografia della spalla",
		"Tendinopatia del sovraspinato senza lesioni a tutto spessore. Borsa subacromiale "
		"lievemente distesa.",
	),
	"Distorsione di caviglia": (
		"Radiografia della caviglia",
		"Nessuna frattura. Tumefazione dei tessuti molli in sede perimalleolare esterna.",
	),
	"Lombalgia": (
		"Radiografia della colonna lombare",
		"Lieve riduzione dello spazio tra quarta e quinta vertebra lombare. Nessun cedimento dei "
		"corpi vertebrali.",
	),
}
CENTRO_IMMAGINI = "Centro di diagnostica per immagini"
LABORATORIO = "Laboratorio analisi"
#: name, unit, low, high, the normal range as the report prints it
ESAMI = (
	("Glicemia", "mg/dL", 78, 99, "70 - 100"),
	("Colesterolo totale", "mg/dL", 165, 228, "< 200"),
	("Colesterolo HDL", "mg/dL", 42, 72, "> 40"),
	("Trigliceridi", "mg/dL", 60, 160, "< 150"),
	("Ferritina", "ng/mL", 22, 140, "15 - 150"),
	("TSH", "mUI/L", 0.9, 3.6, "0,4 - 4,0"),
	("Vitamina D", "ng/mL", 14, 38, "30 - 100"),
)
PRESCRIZIONE = (
	"Prescrizione di fisioterapia",
	"Si prescrive un ciclo di dieci sedute di esercizio terapeutico e terapia manuale per {motivo}, "
	"due a settimana. Rivalutazione al termine del ciclo.",
)

# -- what a practitioner writes on the person's board -----------------------------------------------

DI_CURA = {
	"giulia": "Buongiorno {nome}, ricordi gli esercizi della sera: tre serie, senza forzare. Se il "
	"dolore sale sopra il 5, ne parliamo alla prossima seduta.",
	"elena": "Buongiorno {nome}, nel piano trova il menù della settimana e la lista della spesa. Mi "
	"scriva pure se qualcosa non le torna.",
	"dentista": "Buongiorno {nome}, le prossime sedute del piano di cura sono già in agenda. Se "
	"dopo la pulizia sente i denti sensibili, è normale per qualche giorno.",
}
FUORI_EQUIPE = "La fisioterapista mi chiede un parere sull'alimentazione prima che riprenda a correre."

# -- the dietitian's menus and the physiotherapist's exercises at home ------------------------------

#: moment key, label, time, foods (CIQUAL code, grams, alternatives)
MENU = (
	(
		"colazione",
		"Colazione",
		"07:30",
		(("19016", 200, "uno yogurt bianco"), ("32140", 40, None), ("13005", 100, "una mela")),
	),
	("spuntino", "Spuntino", "10:30", (("15005", 15, "15 g di mandorle"),)),
	(
		"pranzo",
		"Pranzo",
		"13:00",
		(
			("9811", 80, "riso o farro"),
			("20385", 150, "o altra verdura di stagione"),
			("12120", 10, None),
			("17270", 10, None),
		),
	),
	("merenda", "Merenda", "16:30", (("13039", 150, "o altra frutta di stagione"),)),
	(
		"cena",
		"Cena",
		"20:00",
		(
			("26072", 150, "120 g di pollo o due uova"),
			("4003", 150, "50 g di pane"),
			("20031", 80, None),
			("17270", 10, None),
		),
	),
)
ABITUDINI_DEL_MENU = (("Due litri d'acqua nella giornata", None), ("Legumi al posto del secondo", 2))
#: moment key, label, time, food groups (group, portions, alternatives)
SCAMBI = (
	(
		"colazione",
		"Colazione",
		"07:30",
		(
			("Milk and dairy", 1, "latte o yogurt bianco"),
			("Cereals and tubers", 1, "pane, fette biscottate o fiocchi d'avena"),
			("Fruit", 1, None),
		),
	),
	(
		"pranzo",
		"Pranzo",
		"13:00",
		(
			("Cereals and tubers", 2, "pasta, riso, farro o pane"),
			("Vegetables", 2, None),
			("Oils and fats", 1, "olio extravergine"),
		),
	),
	(
		"cena",
		"Cena",
		"20:00",
		(
			("Fish", 1, "carne bianca, uova o legumi"),
			("Vegetables", 2, None),
			("Cereals and tubers", 1, "pane o patate"),
			("Oils and fats", 1, None),
		),
	),
)
#: The reason of a first visit -> the exercises at home: (as the library names it, sets,
#: reps, duration, rest).
ESERCIZI_A_CASA = {
	"Lombalgia": (
		("Pelvic tilt", 2, "12", None, "30 sec"),
		("Dead bug", 3, "8 per lato", None, "30 sec"),
		("Pelvic tilt into bridge", 3, "10", None, "40 sec"),
		("Seated lower back stretch", 1, None, "30 sec", None),
	),
	"Cervicalgia": (
		("Neck side stretch", 2, None, "20 sec per lato", None),
		("Side push neck stretch", 2, "10", None, "20 sec"),
		("Chest and front of shoulder stretch", 2, None, "30 sec", None),
	),
	"Dolore alla spalla": (
		("Rear deltoid stretch", 2, None, "30 sec", None),
		("Chest and front of shoulder stretch", 2, None, "30 sec", None),
		("Overhead triceps stretch", 2, None, "20 sec per lato", None),
	),
	"Distorsione di caviglia": (
		("Bodyweight standing calf raise", 3, "12", None, "30 sec"),
		("One leg floor calf raise", 2, "10 per gamba", None, "30 sec"),
		("Calf stretch with hands against wall", 2, None, "30 sec per lato", None),
	),
	"Dolore al ginocchio": (
		("Low glute bridge on floor", 3, "12", None, "40 sec"),
		("Split squats", 3, "8 per gamba", None, "45 sec"),
		("Lying (side) quads stretch", 1, None, "30 sec per lato", None),
		("Hamstring stretch", 1, None, "30 sec per lato", None),
	),
}
