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
}
