# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What invoicing needs to know about whoever performed the service.

This is the seam between the two modules. Invoicing routes and taxes a line from
six facts about a qualification, and **none of them is healthcare**: a qualification
can be VAT-exempt, can be barred from the SdI, can carry a reporting duty to some
other system. Invoicing records all three and interprets only the first two.

Which qualifications exist, and why a physiotherapist is barred from the SdI while
an osteopath is compelled onto it, is knowledge that belongs to whoever supplies
the register - `crm.tessera_sanitaria` here, nothing at all in an installation that
only issues ordinary invoices.

The default answer is deliberately dull: taxable at the ordinary rate, SdI optional,
nothing to report anywhere. That is the correct answer for a plumber, and it is what
makes this module work with no healthcare code installed at all.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol, runtime_checkable

from .codici import RegolaSdI


@runtime_checkable
class Qualifica(Protocol):
	"""The shape of an answer about a qualification.

	A Protocol rather than a base class: the register that supplies these lives in
	another module, and inheritance across that line would be the dependency this
	whole split exists to avoid.
	"""

	codice: str
	etichetta: str
	#: VAT exemption attaches to the qualification, not to the service.
	esente_iva: bool
	#: Whether the SdI is mandatory, forbidden or optional for this qualification.
	regola_sdi: str
	aliquota_iva_default: Decimal
	#: A reporting duty towards a system that is not the SdI. Invoicing records it
	#: and never acts on it beyond keeping such a line off the SdI.
	comunicazione_esterna: bool
	#: How the supplying module identifies this qualification in that other system.
	soggetto_comunicazione: str | None


@dataclass(frozen=True)
class QualificaNeutra:
	"""No exemption, no bar, no duty elsewhere.

	The answer for a line whose qualification nobody has anything special to say
	about - which is every line in an installation that sells ordinary services.
	"""

	codice: str = ""
	etichetta: str = ""
	esente_iva: bool = False
	regola_sdi: str = RegolaSdI.AMMESSO
	aliquota_iva_default: Decimal = Decimal("22.00")
	comunicazione_esterna: bool = False
	soggetto_comunicazione: str | None = None
	da_verificare: tuple[str, ...] = field(default_factory=tuple)


Risolutore = Callable[[str], Qualifica]


def risolutore_neutro(codice: str) -> Qualifica:
	"""Every code resolves to the dull answer. The floor this module stands on."""
	return QualificaNeutra(codice=codice or "", etichetta=codice or "")
