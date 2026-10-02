# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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

	from .engine import classificazione, professioni, voci

	# shipped: asked after every register the practice edits
	estensioni.registra_risolutore(professioni.professione, spedito=True)
	estensioni.registra_arricchitore(classificazione.arricchisci)
	# its choices, in words, for the screens invoicing draws
	voci.registra()


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
	estensioni.registra_controllo_bozza(controlla_bozza)
	# the expense types offered are the ones the issuer's category may use
	from crm.invoicing import scelte

	scelte.registra_regola("tipo_spesa", tipi_spesa_offerti)


def tipi_spesa_offerti(doc: dict) -> frozenset[str] | None:
	"""The expense types the issuer may use: the invoice's company, else the default
	one. A category that reports nothing narrows nothing."""
	import frappe

	from .engine.codici import SoggettoInviante, tipi_spesa_ammessi

	azienda = doc.get("company") or frappe.db.get_single_value("CRM Invoicing Settings", "default_company")
	if not azienda:
		azienda = frappe.db.get_value("CRM Invoicing Company", {"is_default": 1, "enabled": 1}, "name")
	categoria = frappe.db.get_value("CRM Invoicing Company", azienda, "sender_category") if azienda else None
	if not categoria or categoria == SoggettoInviante.NON_SANITARIO:
		return None
	return tipi_spesa_ammessi(categoria)


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


def controlla_bozza(doc, preparato) -> tuple[list, list]:
	"""What the Sistema TS would refuse in this draft, said before it is issued.

	An issued document is frozen: a report refused in January is a credit note and a
	phone call. So the tracciato is checked on the draft, with the number it does not
	have yet standing in, and what belongs to the document stops the issue. What
	belongs to the company (its codes, its codice fiscale) is said, and does not stop
	the invoice the patient is waiting for. What invoicing already says about the
	patient and the payment is left to it, not said twice.
	"""
	if not preparato["classificazione"].ts_richiesto:
		return [], []

	from crm.invoicing.engine.messaggi import Messaggio

	from .documento import documento_spesa
	from .engine import tracciato

	spesa = documento_spesa(doc, preparato["azienda"])
	if not spesa.id_spesa.num_documento:
		# the number comes at issue; its format was checked when the company chose it
		spesa.id_spesa.num_documento = "1"
	esito = tracciato.valida_documento(spesa)
	del_centro = tracciato.valida_proprietario(spesa.proprietario).errori

	def gia_detto(errore) -> bool:
		modello = getattr(errore, "modello", errore)
		if modello == tracciato.SERVE_IL_PAGAMENTO:
			return not doc.payment_method
		return modello in tracciato.GIA_DETTI

	errori = [errore for errore in esito.errori if errore not in del_centro and not gia_detto(errore)]
	avvisi = list(esito.avvisi) + [
		Messaggio(
			"the Sistema TS will refuse its report until the issuing company is complete: {0}",
			errore if isinstance(errore, Messaggio) else Messaggio(errore),
		)
		for errore in del_centro
	]
	return errori, avvisi


def verifica_tracciato(doc, preparato) -> None:
	"""Check the Sistema TS tracciato while the document is still a draft.

	In January, with four thousand rows behind it, a rejected row costs a search
	through a year. Here it costs a correction with the client still in the room.
	"""
	from crm.invoicing import documento

	from . import documento as ts

	esito = ts.verifica(doc, preparato["azienda"])
	errori = [documento.in_parole(errore) for errore in esito.errori]
	avvisi = [documento.in_parole(avviso) for avviso in esito.avvisi]
	if errori or avvisi:
		documento.registra(
			doc,
			"ts_prepared",
			"\n".join(errori + avvisi),
			stato="errori" if errori else "avvisi",
		)
	if errori:
		doc.db_set("warnings", "\n".join(errori), update_modified=False)
