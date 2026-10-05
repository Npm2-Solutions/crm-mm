# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's words over the CRM's (`crm.verticali`): with the clinic on, the CRM
is a medical centre's management software and says so everywhere - patients, not
clients; the patient area; the visit to prepare.

Pairs of English strings: the base's, as the CRM writes it, and the clinic's. Each
language translates the clinic's own string; a new place of the base that names
the people or what they come for adds its pair here.
"""

from __future__ import annotations

PAROLE = {
	# DottorCloud
	"Client area": "Patient area",
	# the agenda's first appointment of a person
	"First appointment": "First visit",
	# the settings' group of the people the centre serves, and the booking rules'.
	# The list of people stays "People": it holds everybody the centre has heard
	# from - who asked, a parent, a company's contact - not only its patients
	"Clients": "Patients",
	# Settings > Invoicing: a medical centre's company carries its Sistema TS credentials
	"Who issues the invoices: details, tax regime, numbering.": (
		"Who issues the invoices: details, tax regime, Sistema TS credentials."
	),
	"News in the client area": "News in the patient area",
	# the waiting list: where one joins it
	"From the client area": "From the patient area",
	# the notifications one receives by email too (Settings > Your account)
	"Questions from the client area": "Questions from the patient area",
	"What a person asks the centre from their area.": "What a patient asks the centre from their area.",
	# the area
	"This area is for the centre's clients.": "This area is for the centre's patients.",
	"Prepare your appointment": "Prepare your visit",
	# plans and programmes, written for the person to follow in their area
	"For the person": "For the patient",
	"What to keep in mind, in the words the person reads in their area": (
		"What to keep in mind, in the words the patient reads in their area"
	),
	"What to keep in mind: the person reads it with the session": (
		"What to keep in mind: the patient reads it with the session"
	),
	"A note for the person": "A note for the patient",
	"The next stage opens when the person says the one before is finished, in their area, or when you do.": (
		"The next stage opens when the patient says the one before is finished, in their area, or when you do."
	),
	"What the programme is for, in the words the person reads": (
		"What the programme is for, in the words the patient reads"
	),
	"What the person reads when the stage opens: its goal, what to keep in mind": (
		"What the patient reads when the stage opens: its goal, what to keep in mind"
	),
	# the person's documents: with the clinic, reports and tests first
	"Nothing yet. What the person brings or sends goes here: a contract, a certificate, a consent signed on paper.": (
		"Nothing yet. The tests, reports and images the patient brings go here, and the report "
		"of every signed visit."
	),
	"A contract, a certificate, a signed consent…": "Blood tests, chest X-ray, cardiology report…",
	"The office, the laboratory, the doctor": "The laboratory, the hospital, the doctor",
	"The file is private: only whoever reads the person's documents opens it.": (
		"The file is private: only whoever reads the patient's documents opens it, and every opening of "
		"health data is logged."
	),
	"Give it to the person": "Give it to the patient",
	"The code to open it: give it to the person now": "The code to open it: give it to the patient now",
	"The person, or who took it for them": "The patient, or who took it for them",
	"At most {0}. It opens with a code you give the person here.": (
		"At most {0}. It opens with a code you give the patient here."
	),
	# the quotes: "For the person" above heads them too; signed by the patient
	"Signature of the person, or of who answers for them": (
		"Signature of the patient, or of who answers for them"
	),
	# new clients (`crm.clienti`) stay clients: whoever came or bought, a Pilates
	# class too. A patient is a step above (`paziente`), with its own words - "Patient
	# since", "Became Patient", "New patients" - never the client's renamed. The new
	# clients pipeline is the one to the first visit, named in the clinic's words
	"New clients pipeline": "New patients pipeline",
	# the first steps
	"Your first client": "Your first patient",
	# the person's plans, without the area
	"The person does not enter their area yet: invite them from the Client area tab, so that they see the plans you publish.": (
		"The person does not enter their area yet: invite them from the Patient area tab, so that they see the plans you publish."
	),
	# the marketing module, on the features page
	"Automations, campaigns, Meta leads and spend, social, tracking, cost per new client, the website": (
		"Automations, campaigns, Meta leads and spend, social, tracking, cost per new patient, the website"
	),
	"A booking moves an open deal of the new clients pipeline to the stage after a booking, and the first time the person comes wins it. So the ads report says what a new client costs.": (
		"A booking moves an open deal of the new patients pipeline to the stage after a booking, "
		"and the first time the person comes wins it, whatever they come for. So the ads report "
		"says what bringing in a new client costs."
	),
	"Create the new clients pipeline": "Create the new patients pipeline",
	"The stage after a booking has to be one of the new clients pipeline's stages": (
		"The stage after a booking has to be one of the new patients pipeline's stages"
	),
	"New clients and quotes need two different pipelines": "New patients and quotes need two different pipelines",
	# the agenda: a new appointment, who booked it, two places at once
	"A service for a client, with who delivers it and where.": (
		"A service for a patient, with who delivers it and where."
	),
	"Booked online by the client": "Booked online by the patient",
	"A client in two places at once": "A patient in two places at once",
	# online booking and its rules (Settings > Agenda)
	"Clients can book online": "Patients can book online",
	"Services clients can book": "Services patients can book",
	"People clients can book": "People patients can book",
	"Client picks the professional": "Patient picks the professional",
	"Client can cancel online": "Patient can cancel online",
	"Client can move online": "Patient can move online",
	"Max per client per day (0 = any)": "Max per patient per day (0 = any)",
	"Upcoming bookings per client": "Upcoming bookings per patient",
	"Upcoming per client": "Upcoming per patient",
	"New clients only": "New patients only",
	"Returning clients only": "Returning patients only",
	"Clients book it on the booking page, with the rules below.": (
		"Patients book it on the booking page, with the rules below."
	),
	"A line clients read before choosing them": "A line patients read before choosing them",
	"As a client online": "As a patient online",
	"Question for the client": "Question for the patient",
	"Email the client": "Email the patient",
	"Link clients as leads": "Link patients as leads",
	"Opening the page, and who clients can book for what, is in Online booking.": (
		"Opening the page, and who patients can book for what, is in Online booking."
	),
	"Who clients can book, and for what. Every switch here applies at once.": (
		"Who patients can book, and for what. Every switch here applies at once."
	),
	"Every professional listed below is booked together — two therapists following one client.": (
		"Every professional listed below is booked together — two therapists following one patient."
	),
	"No platform connected yet. Connect the ones where your clients already book.": (
		"No platform connected yet. Connect the ones where your patients already book."
	),
	# a service's rules in short, in the list of services
	"{0} upcoming per client": "{0} upcoming per patient",
	"new clients": "new patients",
	"returning clients": "returning patients",
	# the dashboard's agenda: who booked, who did not come
	"Appointments clients booked themselves on the booking page": (
		"Appointments patients booked themselves on the booking page"
	),
	"Share of the period's new appointments booked by the clients themselves": (
		"Share of the period's new appointments booked by the patients themselves"
	),
	"When clients book online": "When patients book online",
	"Of the appointments that were due, the share where the client did not come": (
		"Of the appointments that were due, the share where the patient did not come"
	),
	"Value of the appointments the client did not turn up to": (
		"Value of the appointments the patient did not turn up to"
	),
	# the person's field, where a centre lays it out
	"When they became a client: the first time they came, or their first invoice. Written once, by the rules; automations and the dashboard count on it.": (
		"When they became a patient: their first visit, first healthcare invoice or first clinical note. "
		"Written once, by the rules; automations and the dashboard count on it."
	),
	# the SMS sender's line, the demo's removal
	"Every SMS the centre sends leaves from here: the waiting list’s offers, the client area’s news, the automations, the ones written by hand.": (
		"Every SMS the centre sends leaves from here: the waiting list’s offers, the patient area’s news, "
		"the automations, the ones written by hand."
	),
	"Everything the demo made goes, and with it what is about its people, what you wrote too: notes, appointments, messages. The services, rooms and price lists you used for your own clients stay.": (
		"Everything the demo made goes, and with it what is about its people, what you wrote too: notes, "
		"appointments, messages. The services, rooms and price lists you used for your own patients stay."
	),
	# the server's: the booking page, a cancellation, why a professional is not bookable
	"This service can be booked online by new clients only.": (
		"This service can be booked online by new patients only."
	),
	"This service can be booked online by existing clients only. Please contact us.": (
		"This service can be booked online by existing patients only. Please contact us."
	),
	"Cancelled online by the client": "Cancelled online by the patient",
	"Pick the services clients can book them for": "Pick the services patients can book them for",
	# the invoice: who it is for
	"Client": "Patient",
	"Choose the client": "Choose the patient",
	"Nobody yet: choose the client.": "Nobody yet: choose the patient.",
}
