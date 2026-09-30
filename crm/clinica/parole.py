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
	"News in the client area": "News in the patient area",
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
}
