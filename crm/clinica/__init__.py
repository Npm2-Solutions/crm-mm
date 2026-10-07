# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic: the vertical that makes the CRM a medical centre's management software.

Switched on, it turns the CRM into the centre's software, all of it
(docs/verticali/clinica/design.md, "Tre strati"): its words - patients, visits, the
patient area (`parole.py`, through `crm.verticali`); what exists only for health
data or medical practice - who is a patient (`regole.py`, `paziente.py`), the
record and its reports, the dossier, the summary, the dental chart, diets; and its
rules on the CRM's own pieces, which it registers rather than copies - the client
area's places and the board's messages about the care, the forms with health data.

It hooks onto the CRM the way the Sistema TS hooks onto invoicing: the CRM never
imports it (`tests/test_confine.py` checks), and without the line in
`crm/registrazione.py` the CRM is what it was. The code is on every site; what
it does is switched on per site by the plan's "clinic" module, off by default.
"""

from __future__ import annotations

from crm.assistente import Funzione, registra_funzione
from crm.moduli.registro import CONSENSO, TipoConsenso, registra_tipo
from crm.permissions.livelli import (
	CENTRO,
	SUOI,
	Capacita,
	Livello,
	ModuloPiano,
	concedi,
	registra_capacita,
	registra_livello,
	registra_modulo_piano,
	registra_ruolo,
)

#: The plan's module: off until the agency switches it on for a medical centre.
PIANO = "clinica"
DIREZIONE = "direzione"

MODULO = ModuloPiano(
	PIANO,
	"Clinic",
	predefinito=False,
	descrizione="The medical centre's management software: patients, the clinical record and "
	"reports, health data in plans and documents, and the patient area",
	ordine=2,
	# a medical centre gives its patients their area: it comes with the clinic
	comprende=("area",),
	# the clinical sheets are forms of the builder; the clinic's consents
	impostazioni=("Forms", "Consents"),
)

LIVELLO_DIREZIONE = Livello(
	DIREZIONE,
	"CRM Medical Director",
	"Medical Director",
	"Answers for the clinical side: sees every patient's record, decides who may open it, "
	"builds the clinical templates.",
	base=False,
	piano=PIANO,
	ordine=5,
)

#: Who is a patient is itself health data: the practitioner, the front desk, the
#: manager and the medical director know it; marketing and sales do not.
CAPACITA = (
	(
		Capacita(
			"pazienti.vedi",
			PIANO,
			scrive=False,
			clinica=True,
			descrizione="Who is a patient, since when and why",
		),
		{"segreteria": CENTRO, "operatore": SUOI, "manager": CENTRO, DIREZIONE: CENTRO},
	),
	(
		Capacita("pazienti.segna", PIANO, clinica=True, descrizione="Mark somebody as a patient by hand"),
		{"segreteria": CENTRO, "operatore": SUOI, "manager": CENTRO, DIREZIONE: CENTRO},
	),
	(
		Capacita(
			"pazienti.recupera",
			PIANO,
			descrizione="Find the patients in the appointments and invoices already there",
		),
		{"manager": CENTRO, DIREZIONE: CENTRO},
	),
	# the record (doc 30, "Vedere la cartella"): the practitioner their patients -
	# everybody's with the dossier consent - the medical director all of it
	(
		Capacita("clinica.vedi", PIANO, scrive=False, clinica=True, descrizione="Read the clinical record"),
		{"operatore": SUOI, DIREZIONE: CENTRO},
	),
	(
		Capacita("clinica.scrivi", PIANO, clinica=True, descrizione="Write and sign visits and notes"),
		{"operatore": SUOI},
	),
	# health data among a person's documents (`crm.documenti`): the desk scans what
	# the patient brings, for a practitioner
	(
		Capacita(
			"clinica.archivia",
			PIANO,
			clinica=True,
			descrizione="Add health data to a person's documents: the tests, reports, images and "
			"prescriptions the patient brings or sends",
		),
		{"segreteria": CENTRO, "operatore": SUOI, DIREZIONE: CENTRO},
	),
	# the dossier (doc 30): obscuring an episode is the medical director's, at the
	# patient's request; a practitioner opens a record out of their care writing why
	(
		Capacita(
			"clinica.oscura",
			PIANO,
			clinica=True,
			descrizione="Obscure an episode of the record at the patient's request, and reveal it again",
		),
		{DIREZIONE: CENTRO},
	),
	(
		Capacita(
			"clinica.fuori_equipe",
			PIANO,
			clinica=True,
			descrizione="Open the record of somebody not in your care, writing why: for a day, in the access log",
		),
		{"operatore": SUOI},
	),
	# the teeth (phase 3, "piani di cura (odontoiatria)"): the dentist writes the
	# chart, and a care plan is a quote of the CRM's with a tooth on its rows
	(
		Capacita(
			"cure.scrivi",
			PIANO,
			clinica=True,
			descrizione="Write the dental chart, and the tooth and its surfaces on a quote: with a "
			"dentist's qualification",
		),
		{"operatore": SUOI},
	),
	# the assistant on one's patients (design.md, "L'assistente"): the plan's
	# assistant module, the clinic's data
	(
		Capacita(
			"assistente.bozze",
			"assistente",
			clinica=True,
			descrizione="The assistant on one's patients: drafts from one's signed notes, a visit from "
			"dictation, a summary before the visit - checked and signed by the practitioner",
		),
		{"operatore": SUOI},
	),
	(
		Capacita(
			"assistente.registro_clinico",
			"assistente",
			scrive=False,
			clinica=True,
			descrizione="Read the assistant's clinical events, and re-read the monthly sample",
		),
		{DIREZIONE: CENTRO},
	),
	(
		Capacita(
			"clinica.traccia",
			PIANO,
			scrive=False,
			clinica=True,
			descrizione="Know that a visit happened, not what was said",
		),
		{"segreteria": CENTRO},
	),
	(
		Capacita(
			"clinica.accessi",
			PIANO,
			scrive=False,
			clinica=True,
			descrizione="Who opened a patient's record, and when: not what they read",
		),
		{"manager": CENTRO, DIREZIONE: CENTRO},
	),
)

#: The CRM's capabilities the medical director has: people and consents, the
#: agenda to read, their own calendar, dashboards and operational numbers.
CRM_DELLA_DIREZIONE = (
	"persone.vedi",
	"consensi.vedi",
	"consensi.raccogli",
	"agenda.vedi",
	"google_calendar.proprio",
	"dashboard.personali",
	"numeri.operativi",
	"profilo.proprio",
	# the informed consents and the clinical sheets are the director's to write
	"moduli.configura",
	"moduli.vedi",
	"moduli.compila",
	# the patient area: opening it, the board, and the register of its chat
	"area.invita",
	"area.messaggi",
	"assistente.registro",
	# the plans: to read them, and the libraries - the tables' licences are the centre's
	"piani.vedi",
	"piani.librerie",
	# a person's documents: health data read with the dossier's rules, and what goes
	# after its day is the medical director's to take away
	"documenti.vedi",
	"documenti.aggiungi",
	"documenti.consegna",
	"documenti.togli",
	# the quotes: the care plans, and closing one stopped half-way
	"preventivi.vedi",
	"preventivi.gestisci",
)


DOSSIER = TipoConsenso(
	chiave="health_dossier",
	etichetta="Health dossier",
	natura=CONSENSO,
	piano=PIANO,
	capacita="pazienti.vedi",
	descrizione="Every practitioner of the centre may read the whole record, not only their own "
	"visits (Garante, 4/6/2015).",
	testi={
		"it": (
			"Acconsento alla costituzione del dossier sanitario: i professionisti del centro che mi "
			"hanno in cura possono consultare tutte le informazioni cliniche raccolte su di me, non "
			"solo le proprie. Posso revocare il consenso e oscurare singoli episodi."
		),
		"en": (
			"I agree to a health dossier: the centre's practitioners who treat me may read all the "
			"clinical information collected about me, not only their own. I can withdraw this "
			"consent and hide single episodes."
		),
	},
)

REFERTI_ONLINE = TipoConsenso(
	chiave="online_reports",
	etichetta="Online reports",
	natura=CONSENSO,
	piano=PIANO,
	capacita="pazienti.vedi",
	descrizione="Reports delivered online, in the patient area (Garante, 2009).",
	testi={
		"it": (
			"Chiedo di ricevere i miei referti online, nell'area riservata, e posso escludere "
			"singoli esami. Posso revocare il consenso in qualsiasi momento."
		),
		"en": (
			"I ask to receive my reports online, in my private area, and I can leave single tests "
			"out. I can withdraw this consent at any time."
		),
	},
)


ASSISTENTE = TipoConsenso(
	chiave="ai_assistant",
	etichetta="Assistant",
	natura=CONSENSO,
	piano=PIANO,
	capacita="pazienti.vedi",
	descrizione="An AI assistant drafts documents from what the practitioner wrote; the practitioner "
	"checks and signs them (L. 132/2025, art. 7).",
	testi={
		"it": (
			"Acconsento che il centro usi un assistente di intelligenza artificiale per preparare bozze "
			"di documenti (lettere, istruzioni dopo la visita, riassunti) da quello che i professionisti "
			"hanno scritto. I professionisti le rivedono e le firmano; l'assistente non fa diagnosi. "
			"Posso revocare il consenso in qualsiasi momento."
		),
		"en": (
			"I agree that the centre uses an artificial intelligence assistant to draft documents "
			"(letters, instructions after the visit, summaries) from what the practitioners wrote. "
			"They check and sign them; the assistant makes no diagnosis. I can withdraw this "
			"consent at any time."
		),
	},
)


# what the assistant does on the patients' record (design.md, "L'assistente"):
# the practitioner's own, and their events the medical director's to read
LETTERA = Funzione(
	"letter_from_note",
	"A letter from the note",
	usa="assistente.bozze",
	legge="assistente.registro_clinico",
	interruttore="note_drafts",
)
ISTRUZIONI = Funzione(
	"instructions_from_note",
	"Instructions from the note",
	usa="assistente.bozze",
	legge="assistente.registro_clinico",
	interruttore="note_drafts",
)
DETTATURA = Funzione(
	"visit_from_dictation",
	"A visit from dictation",
	usa="assistente.bozze",
	legge="assistente.registro_clinico",
	interruttore="dictation",
)
RIASSUNTO = Funzione(
	"summary_before_visit",
	"A summary before the visit",
	usa="assistente.bozze",
	legge="assistente.registro_clinico",
	interruttore="summaries",
)
RICETTE = Funzione(
	"menu_recipes",
	"Recipes for a meal plan",
	usa="assistente.bozze",
	legge="assistente.registro_clinico",
	interruttore="menus",
)
FUNZIONI_ASSISTENTE = (LETTERA, ISTRUZIONI, DETTATURA, RIASSUNTO, RICETTE)


def registra() -> None:
	from crm.automation import engine
	from crm.clienti import pipeline as clienti
	from crm.clinica import paziente, pipeline
	from crm.clinica.paziente import clinica_accesa

	registra_modulo_piano(MODULO)
	# the CRM's rules say who is a client, the clinic's who is a patient besides: the
	# new clients pipeline, in its words, is the one to the first visit
	clienti.registra_nomi(PIANO, pipeline.NUOVI_PAZIENTI)
	engine.registra_evento(paziente.EVENTO, paziente.TRIGGER, disponibile=clinica_accesa)
	# somebody brought over from the previous software was the clinic's patient
	# there: the import rule (regola 5)
	from crm.importazione import importa

	importa.registra_dopo(paziente.dall_importazione)
	_registra_dashboard(clinica_accesa)
	registra_ruolo(
		"Medical Director",
		"Answers for the clinical side of the centre.",
		livelli=(DIREZIONE,),
	)
	registra_livello(LIVELLO_DIREZIONE, ("Sales User", "Practitioner", "Medical Director"))
	for capacita, concessioni in CAPACITA:
		registra_capacita(capacita, concessioni)
	# what the medical director does of the CRM's own (doc 30, the Dir column)
	for nome in CRM_DELLA_DIREZIONE:
		concedi(nome, {DIREZIONE: CENTRO})
	registra_tipo(DOSSIER)
	registra_tipo(REFERTI_ONLINE)
	registra_tipo(ASSISTENTE)
	# what the assistant does on the patients' record, each read by the medical director
	for funzione in FUNZIONI_ASSISTENTE:
		registra_funzione(funzione)
	# "health data" on a form template means something where the clinic is on,
	# and a form that records it is read by the care team only; a sheet with the
	# mark is the practitioner's clinical sheet, written in the record (`cartella`)
	from crm.moduli import compilazioni, modelli

	modelli.registra_dato_clinico(clinica_accesa)
	compilazioni.registra_lettore_clinico(legge_i_moduli_clinici)
	# the lines of the patient's summary a field of a template may answer
	from crm.clinica import sintesi

	sintesi.registra()
	# who reads what carries health data in the CRM - plans, programmes, documents -
	# and what carries it by who wrote it: the dossier's rules
	from crm.clinica import dossier
	from crm.permissions import sanitari

	sanitari.registra_lettore(dossier.lettore())
	# its plans on the CRM's engine: diets and exercises at home, the foods
	from crm.clinica import piani

	piani.registra()
	# its documents among the person's: reports, tests, images, prescriptions
	from crm.clinica import documenti

	documenti.registra()
	# the tooth and its surfaces on the CRM's quotes: a care plan
	from crm.clinica import cure

	cure.registra()
	# with the clinic on, the CRM is a medical centre's software and says so
	from crm.clinica.parole import PAROLE
	from crm.marchio import DOTTORCLOUD
	from crm.verticali import Verticale, registra_verticale

	# and wears its brand: DottorCloud's name, marks and colours, everywhere; and
	# invoices as a healthcare practice, with only the choices it meets
	registra_verticale(
		Verticale(PIANO, PIANO, parole=PAROLE, marchio=DOTTORCLOUD.chiave, fatturazione="sanitario")
	)
	_registra_area()
	# its share of the demo: the record, the dentist, the diets
	from crm.clinica import demo

	demo.registra()


def _registra_area() -> None:
	"""The clinic's kind of message on the board of the patient area."""
	from crm.area import messaggi
	from crm.permissions import livelli

	# about the care: written by a practitioner, read like one of their visits
	messaggi.registra_tipo(
		messaggi.TipoMessaggio(
			"Care",
			scrive=lambda user: livelli.puo("clinica.scrivi", user),
			legge=_legge_la_cura,
			campi=lambda user: {"practitioner": user, "visibility": "Care team"},
			priorita=10,
		)
	)


def _legge_la_cura(doc, user: str) -> bool:
	from crm.clinica import dossier

	return dossier.legge_le_altre(doc, user)


def legge_i_moduli_clinici(user: str | None = None) -> bool:
	"""Who reads a form with health data: whoever reads or writes the record."""
	from crm.permissions.livelli import puo

	return puo("clinica.vedi", user) or puo("clinica.scrivi", user)


def _cruscotto():
	from frappe import _lt

	from crm.dashboard.templates import CHART, KPI, LIST, Line, Template, section

	return Template(
		"medical_centre",
		_lt("Medical centre"),
		_lt("New patients and what one costs, the day's agenda, no-shows, recalls and invoices"),
		"stethoscope",
		sequence=5,
		requires=("clinic",),
		# the day's agenda and the no-shows: for whoever reads the operational numbers
		reader="numeri.operativi",
		sections=(
			section(
				Line.of(
					KPI,
					# the clinic's own (`cruscotto`): new patients, what one costs
					"new_patients",
					"meta_cost_per_patient",
					"appointments_today",
					"appointments_no_show_rate",
					"recall_due",
				),
				Line.of(
					KPI,
					# whoever came or bought: the Pilates class too
					"new_clients",
					"invoiced_revenue",
					"appointments_to_invoice",
					"appointments_to_confirm",
				),
				Line.of(CHART, "appointments_trend", "appointments_by_service"),
				Line.of(
					LIST,
					"appointments_upcoming",
					"appointments_to_invoice_list",
					"appointments_to_confirm_list",
				),
			),
		),
	)


def _registra_dashboard(clinica_accesa) -> None:
	"""The "clinic" feature, and the medical centre's dashboard that needs it."""
	from frappe import _lt

	from crm.dashboard.features import FEATURES, Feature

	FEATURES.setdefault(
		"clinic",
		Feature(
			"clinic",
			_lt("Clinic"),
			_lt("The clinic is a module of the plan: the agency switches it on"),
			None,
			clinica_accesa,
		),
	)
	# the clinic's widgets register when their module is imported
	from crm.clinica import cruscotto
	from crm.dashboard import templates as modelli

	modelli.registra(_cruscotto())
