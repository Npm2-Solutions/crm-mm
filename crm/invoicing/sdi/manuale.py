# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Export: the file is written, and somebody uploads it.

The least clever channel and the one that has to keep working. Every other route
degrades to this one, so it is not the bottom rung - it is the floor everything
else stands on, and it stays tested even when nobody uses it.
"""

from __future__ import annotations

from frappe import _

from crm.invoicing.sdi.base import ErroreCanale, EsitoInvio

CODICE = "export"
ETICHETTA = "Manual export"


def invia(doc, emittente: dict) -> EsitoInvio:
	if not doc.xml_file:
		raise ErroreCanale(_("This invoice has no XML to hand over"))
	return EsitoInvio(
		canale=CODICE,
		inviato=True,
		file=doc.xml_file,
		nome_file=doc.sdi_filename,
		messaggio=_(
			"The file is ready. Upload it from the Fatture e Corrispettivi portal, or from your "
			"intermediary's, and record the outcome here when the notice arrives. The portal takes "
			"files up to 5 MB."
		),
	)
