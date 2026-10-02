# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The healthcare rules on invoicing's own records.

Three DocTypes here belong to invoicing and serve every sector: the qualification
register, the service card, the issuing company. Each carries a handful of rules
that only exist where healthcare does - the art. 10 exemption, the tipoSpesa, the
Codice Proprietario - and those rules are wired in through `doc_events` rather
than written into controllers that also serve lawyers and plumbers.

Keeping them here is not tidiness. A controller that imports this module stops
loading the day the module is not installed, and an invoicing system that will not
load is worse than one without healthcare.

An installation without this saves the same records and skips these checks, which
is correct: without healthcare there is no art. 10 and no Sistema TS.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.invoicing.engine import voci
from crm.invoicing.engine.codici import RegolaSdI
from crm.tessera_sanitaria.engine.codici import (
	SOGGETTI_CON_CODICE_PROPRIETARIO,
	SoggettoInviante,
	tipi_spesa_ammessi,
)


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
				"natural person cannot go through the SdI. Set the electronic invoice to «{0}», or "
				"turn the Sistema TS duty off."
			).format(_(voci.etichetta("regola_sdi", RegolaSdI.VIETATO)))
		)

	if doc.ts_required and not tipi_spesa_ammessi(doc.sender_category):
		frappe.throw(
			_(
				"«{0}» has no expense type of the Sistema TS: choose the category the Sistema TS "
				"enrolled this profession under"
			).format(_(voci.etichetta("soggetto_inviante", doc.sender_category)) or "-")
		)


def valida_servizio(doc, metodo=None):
	if doc.ts_expense_type and not doc.is_healthcare:
		frappe.throw(
			_(
				"An expense type of the Sistema TS on a service that is not healthcare: the Sistema "
				"TS only knows healthcare expenses. Either the service is healthcare, or the expense "
				"type goes."
			)
		)
	if doc.ts_expense_flag and doc.ts_expense_type not in ("TK", "SR"):
		frappe.throw(
			_("«{0}» only goes with the expense type «{1}» or «{2}», not with «{3}»").format(
				_(voci.etichetta("flag_tipo_spesa", doc.ts_expense_flag)),
				_(voci.etichetta("tipo_spesa", "TK")),
				_(voci.etichetta("tipo_spesa", "SR")),
				_(voci.etichetta("tipo_spesa", doc.ts_expense_type)) or "-",
			)
		)


def MANCANO_I_CODICI() -> str:
	"""Said where the codes are asked for, the same everywhere."""
	return _(
		"A facility, a pharmacy or an optician reports with the Region, ASL and facility codes of its Sistema TS authorisation (the Codice Proprietario): all three are needed"
	)


def valida_azienda(doc, metodo=None):
	categoria = doc.sender_category or SoggettoInviante.NON_SANITARIO
	if categoria == SoggettoInviante.NON_SANITARIO:
		return
	if categoria in SOGGETTI_CON_CODICE_PROPRIETARIO:
		if not (doc.region_code and doc.asl_code and doc.ssa_code):
			frappe.throw(MANCANO_I_CODICI())
	elif any((doc.region_code, doc.asl_code, doc.ssa_code)):
		frappe.throw(
			_(
				"Whoever invoices in their own name reports with their codice fiscale: the Region, ASL and facility codes stay empty"
			)
		)
	# Deliberately not a throw. The intended mode is the centre's own credentials,
	# and a centre is set up before its credentials arrive - blocking the save
	# would stop onboarding at a field that will be filled next week. The gap
	# shows in the checklist, and the send refuses on its own until it is closed.
	# Nothing about invoicing waits on any of it.
	if not doc.fiscal_code and not doc.tax_id:
		frappe.throw(_("The Sistema TS needs a codice fiscale or a VAT number for the owner"))
