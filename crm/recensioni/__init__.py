# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Asking how a visit went: a review on Google, a questionnaire of the centre's.

A beauty centre, a gym and a medical centre ask the same way, so it is the CRM's,
and it rides on what is there: the automations send (a recipe asks for a review
two hours after a visit, off until the centre switches it on), the consent
register says who may be asked (`regole`, a kind of its own), the dashboard counts
the requests sent and scores the answers.

- **The rules** (`regole`): who may be asked, how often, the link, the score.
- **On the site** (`chiedi`): the settings (Settings > Marketing > Review
  requests), the gate an automation's message passes, the request it writes
  before it leaves, the link that counts the click.
- **The questionnaire**: a use of the forms, "Survey", opened by its link alone
  and sent by the automations' «Send a form»; its 0 to 10 question makes the
  dashboard's Net Promoter Score («Satisfaction (NPS)»).
"""

from __future__ import annotations

from crm.moduli.registro import CONSENSO, TipoConsenso
from crm.recensioni import regole

RICHIESTE_DI_RECENSIONE = TipoConsenso(
	chiave=regole.CONSENSO,
	etichetta="Review requests",
	natura=CONSENSO,
	descrizione="Asked after a visit how it went: a review on Google, a satisfaction questionnaire. "
	"A no here wins over a yes to marketing.",
	testi={
		"it": (
			"Acconsento a ricevere dopo una visita, via email, SMS o WhatsApp, la richiesta di dire "
			"com'è andata, con una recensione o un breve questionario. Posso revocare il consenso in "
			"qualsiasi momento."
		),
		"en": (
			"I agree to be asked after a visit, by email, SMS or WhatsApp, how it went, with a review "
			"or a short questionnaire. I can withdraw this consent at any time."
		),
	},
	piano="marketing",
)


def registra() -> None:
	from crm.moduli import modelli
	from crm.moduli.registro import registra_tipo
	from crm.recensioni import chiedi

	registra_tipo(RICHIESTE_DI_RECENSIONE)
	# a short questionnaire after a visit: filled by the person from its link alone,
	# sent by an automation's «Send a form» or by hand, never owed at a booking
	modelli.registra_uso(
		modelli.Uso(
			chiedi.SONDAGGIO,
			"Survey",
			"Filled in by the person after a visit, from its link alone: how it went, a score from 0 to 10",
			al_banco=False,
			senza_codice=True,
		)
	)
