# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The clinic: patients, and in time their record, reports, plans and area.

It hooks onto the CRM the way the Sistema TS hooks onto invoicing: the CRM never
imports it (`tests/test_confine.py` checks), and without the line in
`crm/registrazione.py` the CRM is what it was. The code is on every site; what
it does is switched on per site by the plan's "clinic" module, off by default.

Today: who is a patient, and how they became one (`regole.py`, `paziente.py`).
The clinical record comes next, on the person's page.
"""

from __future__ import annotations

from crm.assistente import Funzione, registra_funzione
from crm.moduli.registro import CONSENSO, TipoConsenso, registra_tipo
from crm.permissions.livelli import (
	A_SCELTA,
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
	descrizione="Patients, the clinical record, forms and consents with signature, the archive, "
	"the patient area, plans",
	ordine=2,
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
	# the archive: the desk scans what the patient brings, for a practitioner
	(
		Capacita(
			"clinica.archivia",
			PIANO,
			clinica=True,
			descrizione="Add documents to the clinical archive: what the patient brings, what arrives in a "
			"conversation",
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
	# giving a report to the patient, by hand or online (Garante, 2009)
	(
		Capacita(
			"clinica.consegna",
			PIANO,
			clinica=True,
			descrizione="Give a report to the patient: by hand, or online for 45 days with their consent",
		),
		{"operatore": SUOI, DIREZIONE: CENTRO},
	),
	# the patient area (design.md, "L'area cliente"): the centre opens it to a person
	(
		Capacita(
			"area.invita",
			PIANO,
			descrizione="Open a person's patient area to them, or to who answers for them, and close it",
		),
		{"segreteria": CENTRO, "operatore": SUOI, "manager": CENTRO, DIREZIONE: CENTRO},
	),
	(
		Capacita(
			"area.messaggi",
			PIANO,
			descrizione="Write on the person's board in their area: the desk about administration, "
			"a practitioner about the care",
		),
		{"segreteria": CENTRO, "operatore": SUOI, DIREZIONE: CENTRO},
	),
	# the plans (design.md, "I piani"): which kinds, the qualification decides
	(
		Capacita(
			"piani.scrivi",
			PIANO,
			clinica=True,
			descrizione="Write and publish plans - a diet, a training, exercises at home, habits - "
			"of the kinds one's qualification allows",
		),
		{"operatore": SUOI},
	),
	# the libraries the plans are written with: the manager, the medical director,
	# and the nutritionist the manager chooses (the tables' licences are the centre's)
	(
		Capacita(
			"piani.librerie",
			PIANO,
			descrizione="Keep the centre's food and exercise libraries: import the food tables and the "
			"exercises, correct names and groups, switch an item off",
		),
		{"manager": CENTRO, DIREZIONE: CENTRO, "operatore": A_SCELTA},
	),
	# the dental care plans (phase 3, "piani di cura (odontoiatria)"): the dentist
	# writes the chart and the plans, the desk handles the quotes
	(
		Capacita(
			"cure.scrivi",
			PIANO,
			clinica=True,
			descrizione="Write the dental chart and the care plans, and propose them as quotes: with a "
			"dentist's qualification",
		),
		{"operatore": SUOI},
	),
	(
		Capacita(
			"cure.preventivi",
			PIANO,
			clinica=True,
			descrizione="Read the care plans proposed as quotes, and record them accepted or declined",
		),
		{"segreteria": CENTRO, "manager": CENTRO},
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
)


def _scheda():
	from crm.moduli.modelli import Uso

	return Uso(
		"Clinical sheet",
		"Clinical sheet",
		"Written by the practitioner during a visit, on the specialty's sheet: it goes to the clinical record",
		clinico=True,
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
# the patients' chat in their area: they use it; in the CRM it goes with the
# area's messages, where what it passes on arrives
CHAT = Funzione(
	"patient_chat",
	"The patients' chat",
	usa="area.messaggi",
	legge="assistente.registro_clinico",
	interruttore="patient_chat",
)
FUNZIONI_ASSISTENTE = (LETTERA, ISTRUZIONI, DETTATURA, RIASSUNTO, RICETTE, CHAT)


def registra() -> None:
	from crm.automation.engine import registra_evento
	from crm.clinica import pipeline
	from crm.clinica.paziente import clinica_accesa

	registra_modulo_piano(MODULO)
	# "Became Patient", offered to the automations where the clinic is on
	registra_evento(pipeline.EVENTO, pipeline.TRIGGER, disponibile=clinica_accesa)
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
	# and a form that records it is read by the care team only
	from crm.moduli import compilazioni, modelli

	modelli.registra_dato_clinico(clinica_accesa)
	compilazioni.registra_lettore_clinico(legge_i_moduli_clinici)
	# the practitioner's sheet: a template written during a visit, into the record
	modelli.registra_uso(_scheda())
	# the lines of the patient's summary a field of a template may answer
	from crm.clinica import sintesi

	sintesi.registra()


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
		sections=(
			section(
				Line.of(
					KPI,
					"new_patients",
					"meta_cost_per_patient",
					"appointments_today",
					"appointments_no_show_rate",
					"recall_due",
				),
				Line.of(KPI, "invoiced_revenue", "appointments_to_invoice", "appointments_to_confirm"),
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
	"""The "clinic" feature, and the widgets that need it (`crm.clinica.widgets`)."""
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
	import crm.clinica.widgets  # registers the widgets
	from crm.dashboard import templates as modelli

	modelli.registra(_cruscotto())
