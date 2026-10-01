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
	# the person's journey at the head of their page, and the agenda's first one
	"Comes in": "Visit",
	"First appointment": "First visit",
	# the settings' group of the people the centre serves, and the booking rules';
	# the main menu's group and its list of people, the page and its breadcrumbs
	"Clients": "Patients",
	"People": "Patients",
	"News in the client area": "News in the patient area",
	# the waiting list: where one joins it
	"From the client area": "From the patient area",
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
	# new clients (`crm.clienti`): with the clinic, whoever becomes a patient
	"New clients": "New patients",
	"Client since": "Patient since",
	"Became Client": "Became Patient",
	"The person becomes a client of the centre: the first time they come, or their first invoice.": (
		"The person becomes a patient of the centre: first visit, first healthcare invoice, "
		"first clinical note."
	),
	"People who became clients in the period: the first time they came, or their first invoice": (
		"People who became patients in the period, whatever the rule that made them"
	),
	"Cost per new client": "Cost per new patient",
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
	"Ad spend divided by the people the ads brought who became clients": (
		"Ad spend divided by the people the ads brought who became patients"
	),
	"A booking moves an open deal of the new clients pipeline to the stage after a booking, and the first time the person comes wins it. So the ads report says what a new client costs.": (
		"A booking moves an open deal of the new patients pipeline to the stage after a booking, "
		"and becoming a patient wins it. So the ads report says what a new patient costs."
	),
	"Create the new clients pipeline": "Create the new patients pipeline",
	"The stage after a booking has to be one of the new clients pipeline's stages": (
		"The stage after a booking has to be one of the new patients pipeline's stages"
	),
	"New clients and quotes need two different pipelines": "New patients and quotes need two different pipelines",
}
