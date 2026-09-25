# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Healthcare expenses, reported to the Sistema Tessera Sanitaria.

This module **extends** invoicing rather than being part of it. Invoicing issues,
calculates, formats and transmits documents for any sector and knows nothing about
patients, spesa types or a delega. What this adds is the healthcare half: the
register of qualifications that decides which lines the SdI may not carry, the
tracciato, the transmission, and the duties that come with them.

The dependency runs one way only - this imports invoicing, never the reverse - so
that lifting it out into a separate Frappe app later is a move, not a rewrite. A
test enforces the direction, because a boundary nobody checks is a boundary that
lasts a month.

Registration happens here, at import, and `crm/hooks.py` is what decides this module
is installed at all. Invoicing never asks for it by name.
"""

from __future__ import annotations


def registra_motore() -> None:
	"""The pure half: the shipped register and the spesa codes.

	No database, so the fiscal rules stay provable on a checkout and a Python
	interpreter - the property that makes this engine auditable by somebody who is
	not going to install a bench.
	"""
	from crm.invoicing import estensioni

	from .engine import classificazione, professioni

	estensioni.registra_risolutore(professioni.professione)
	estensioni.registra_arricchitore(classificazione.arricchisci)


def registra() -> None:
	"""Everything, including the parts that need a site.

	The stored register is invoicing's, not this module's: it holds ordinary
	qualifications too, and a practice that edits one is editing a fact about its own
	invoicing. What this adds is the healthcare half of the shipped register and the
	duties that come with it.
	"""
	from crm.invoicing import estensioni

	from . import registro as registro_sanitario

	registra_motore()
	estensioni.registra_risolutore(registro_sanitario.risolutore())
	estensioni.registra_controlli(controlli)
	estensioni.registra_verifica(verifica_tracciato)


def controlli(emittente: dict) -> list[dict]:
	"""The gaps this module's duties create, and only when they are owed.

	A company that reports no healthcare expenses is asked for no certificate, no
	credentials and no channel - the rows appear with the duty, not with the module.
	"""
	from frappe import _

	from crm.invoicing import registro
	from crm.invoicing.api import _riga_mancante
	from crm.tessera_sanitaria.engine.tracciato import richiede_credenziali

	voci: list[dict] = []
	if emittente.get("sender_category") not in (None, "", "non_sanitario"):
		voci.extend(
			riga
			for riga in (
				_riga_mancante(
					not emittente.get("ts_certificate"),
					_("Sistema TS certificate"),
					_("The expense file is built with a stand-in and cannot be submitted."),
					"ts_certificate",
				),
				_riga_mancante(
					richiede_credenziali(emittente.get("ts_mode")) and not emittente.get("ts_username"),
					_("Sistema TS credentials"),
					_("Submission falls back to export until they arrive."),
					"ts_username",
				),
				_riga_mancante(
					emittente.get("ts_mode") == "provider" and not emittente.get("ts_provider_endpoint"),
					_("Sistema TS channel"),
					_(
						"The Sistema TS is set to go through the provider but has no endpoint: the tracciato is built and nothing carries it. Configure it, or fall back to export and upload from the portal."
					),
					"ts_provider_endpoint",
				),
			)
			if riga
		)

	for qualifica in registro.da_verificare(emittente.get("name")):
		voci.append(
			{
				"title": _("Verify {0}").format(qualifica["qualification_name"]),
				"consequence": qualifica["needs_verification"],
				"field": "",
				"link": {
					"doctype": "CRM Professional Qualification",
					"name": qualifica["name"],
				},
			}
		)
	return voci


def verifica_tracciato(doc, preparato) -> None:
	"""Check the Sistema TS tracciato while the document is still a draft.

	In January, with four thousand rows behind it, a rejected row costs a search
	through a year. Here it costs a correction with the client still in the room.
	"""
	from crm.invoicing import documento

	from . import documento as ts

	esito = ts.verifica(doc, preparato["azienda"])
	if esito.errori or esito.avvisi:
		documento.registra(
			doc,
			"ts_prepared",
			"\n".join(esito.errori + esito.avvisi),
			stato="errori" if esito.errori else "avvisi",
		)
	if esito.errori:
		doc.db_set("warnings", "\n".join(esito.errori), update_modified=False)
