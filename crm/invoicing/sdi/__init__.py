# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Transmission channels to the Sistema di Interscambio.

The XML is built and checked before any of this runs, and the SdI guard has already
answered. What is left is only how the file leaves the building, which is why the
channels are interchangeable and why `export` never stops working.
"""

from __future__ import annotations

from frappe import _

from crm.invoicing.sdi import manuale, pec, provider
from crm.invoicing.sdi.base import ErroreCanale, EsitoInvio

CANALI = {
	manuale.CODICE: manuale,
	pec.CODICE: pec,
	provider.CODICE: provider,
}

ETICHETTE = {
	manuale.CODICE: manuale.ETICHETTA,
	pec.CODICE: pec.ETICHETTA,
	provider.CODICE: provider.ETICHETTA,
}


def canale(codice: str | None):
	"""The channel for a code. An unknown one falls back to export, loudly enough.

	Falling back rather than raising is deliberate: a mistyped configuration should
	leave the invoice transmissible by hand, not stuck.
	"""
	return CANALI.get((codice or "").strip() or manuale.CODICE, manuale)


def invia(doc, emittente: dict) -> EsitoInvio:
	scelto = canale(emittente.get("sdi_mode"))
	return scelto.invia(doc, emittente)


def opzioni() -> list[dict]:
	"""The channels, for a settings screen to offer."""
	return [{"value": codice, "label": _(etichetta)} for codice, etichetta in ETICHETTE.items()]


__all__ = ["CANALI", "ErroreCanale", "EsitoInvio", "canale", "invia", "opzioni"]
