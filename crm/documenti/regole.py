# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a person's document is, and how long it stays online, without a site
(docs/verticali/clinica/design.md, "Tre strati": "I documenti della persona").

- **The kinds are registered** (`TipoDocumento`): the CRM's own - a signed form, a
  contract, an identity document, a certificate, a photo, something else - and the
  ones a module brings: the clinic's report, test result, image, prescription. A
  kind may carry the mark "health data" (`clinico`), and one may be made elsewhere
  rather than added by hand: a report comes from a signed visit.
- **Online** for the days chosen when it is given: unless said, what the module
  whose rule applies says - the clinic's reports, 45 days - or `GIORNI_ONLINE`;
  never more than that module's days, nor than `GIORNI_MASSIMI`.
"""

from __future__ import annotations

from dataclasses import dataclass

MODULO_FIRMATO = "Signed form"
CONTRATTO = "Contract"
IDENTITA = "Identity document"
CERTIFICATO = "Certificate"
FOTO = "Photo"
ALTRO = "Other"

#: How long a document stays online when nobody says otherwise, and at most.
GIORNI_ONLINE = 30
GIORNI_MASSIMI = 90


@dataclass(frozen=True)
class TipoDocumento:
	"""A kind of document: whether it is health data, whether it is added by hand."""

	chiave: str
	#: Health data: read like the clinical record.
	clinico: bool = False
	#: Added from the person's page; False: made elsewhere (a signed visit's report).
	da_aggiungere: bool = True
	#: The plan's module that switches it on; None: always.
	modulo: str | None = None
	#: The capability that adds one besides `documenti.aggiungi`: the clinic's
	#: health data is added by who files it (`clinica.archivia`).
	capacita: str | None = None
	#: Where it goes among the others, smaller first.
	ordine: int = 50


_tipi: dict[str, TipoDocumento] = {}


def registra_tipo(tipo: TipoDocumento) -> None:
	_tipi[tipo.chiave] = tipo


def tipo(chiave: str | None) -> TipoDocumento | None:
	return _tipi.get(chiave or "")


def tipi() -> list[TipoDocumento]:
	"""Every kind registered, in their order."""
	return sorted(_tipi.values(), key=lambda t: (t.ordine, t.chiave))


def giorni_massimi(del_modulo: int | None = None) -> int:
	"""The most days a document stays online: its module's, never more than
	`GIORNI_MASSIMI`."""
	return min(del_modulo or GIORNI_MASSIMI, GIORNI_MASSIMI)


def giorni_online(chiesti, del_modulo: int | None = None) -> int:
	"""The days a document stays online: those asked; else its module's, or
	`GIORNI_ONLINE`. At least one, at most `giorni_massimi`."""
	predefinito = del_modulo or GIORNI_ONLINE
	try:
		giorni = int(chiesti) if chiesti not in (None, "") else predefinito
	except (TypeError, ValueError):
		giorni = predefinito
	return max(1, min(giorni, giorni_massimi(del_modulo)))


for _tipo in (
	TipoDocumento(MODULO_FIRMATO, ordine=10),
	TipoDocumento(CONTRATTO, ordine=20),
	TipoDocumento(CERTIFICATO, ordine=30),
	TipoDocumento(IDENTITA, ordine=40),
	TipoDocumento(FOTO, ordine=60),
	TipoDocumento(ALTRO, ordine=90),
):
	registra_tipo(_tipo)
