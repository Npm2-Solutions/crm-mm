# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The healthcare rules on a stored qualification.

The register itself belongs to invoicing - every profession has one, and the fund
and the withholding are ordinary invoicing. What is here are the three rules that
only exist where healthcare does, wired in through `doc_events` so the DocType
does not have to know they are coming.

An installation without this module saves the same records and skips these checks,
which is correct: without healthcare there is no art. 10 and no Sistema TS.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.invoicing.engine.codici import RegolaSdI
from crm.tessera_sanitaria.engine.codici import SoggettoInviante, tipi_spesa_ammessi


def valida(doc, metodo=None):
	"""Called on validate of a CRM Professional Qualification."""
	if doc.sender_category and doc.sender_category != SoggettoInviante.NON_SANITARIO:
		doc.is_healthcare = 1

	if doc.vat_exempt and not doc.is_healthcare:
		frappe.throw(
			_(
				"The art. 10 exemption is a joint requirement: objective, the service, and "
				"subjective, a supervised health profession. A qualification that is not one "
				"cannot carry it - see Risoluzione AdE n. 9 del 24 febbraio 2026 on osteopaths, "
				"chiropractors and kinesiologists."
			)
		)

	if doc.ts_required and doc.sdi_rule != RegolaSdI.VIETATO:
		frappe.throw(
			_(
				"A qualification that reports to the Sistema TS is one whose documents towards a "
				"natural person cannot go through the SdI. Set the SdI rule to 'vietato', or turn "
				"the Sistema TS duty off."
			)
		)

	if doc.ts_required and not tipi_spesa_ammessi(doc.sender_category):
		frappe.throw(
			_(
				"Sender category {0} has no admitted tipoSpesa: pick the category the Sistema TS "
				"enrolled this profession under"
			).format(doc.sender_category)
		)
