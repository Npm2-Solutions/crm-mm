# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The Sistema TS's share of the demo's invoicing (doc 53): before the cards of its
services are made, the demo's company answers the healthcare setup's three questions
as a centre answers them (doc 46) - a facility, the ordinary regime, the Region's
codes. Registered into invoicing's part, which never asks for it by name."""

from __future__ import annotations

#: The Region's codes the healthcare setup asks a facility for: an ASL that does not
#: exist, so no real facility's (and the Sistema TS is never sent to from a test).
CODICI_TS = {"region_code": "030", "asl_code": "999", "ssa_code": "999999"}


def prepara(azienda: str) -> dict:
	"""The three questions answered for ``azienda``: what a new card of its starts from."""
	from . import preimpostazione
	from .engine.codici import SoggettoInviante

	preimpostazione.apply_setup(
		company=azienda, issuer=SoggettoInviante.STRUTTURA_AUTORIZZATA, regime="RF01", **CODICI_TS
	)
	return preimpostazione.get_setup(azienda)["card_defaults"]
