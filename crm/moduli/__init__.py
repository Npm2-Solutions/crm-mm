# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What every client of the CRM needs about forms and consents.

The consent register: who agreed to what, on which words, when and how. The form
templates and their versions (`schema`, `modelli`), and next the signatures and
the PDFs (phase 2 of the medical centre project, `docs/gestionale-medico/design.md`),
because a privacy notice or a marketing consent is not a clinical matter: a gym
needs them as much as a clinic does.

Other modules add their own kinds of consent through `registro.registra_tipo`, the
way they add capabilities: the clinic will bring the health dossier and online
reports.
"""

from __future__ import annotations

from crm.moduli.registro import CONSENSO, PRESA_VISIONE, TipoConsenso, registra_tipo

INFORMATIVA = TipoConsenso(
	chiave="privacy_notice",
	etichetta="Privacy notice",
	natura=PRESA_VISIONE,
	descrizione="The person read how their data is used. Information, not a consent: nothing to withdraw.",
	testi={
		"it": "Ho letto l'informativa sul trattamento dei dati personali.",
		"en": "I have read the privacy notice.",
	},
)

MARKETING = TipoConsenso(
	chiave="marketing",
	etichetta="Marketing",
	natura=CONSENSO,
	descrizione="News, offers and recalls by email, SMS and WhatsApp. Automations and campaigns ask about it.",
	testi={
		"it": (
			"Acconsento a ricevere da voi comunicazioni su servizi, novità e promozioni, "
			"anche via email, SMS e WhatsApp. Posso revocare il consenso in qualsiasi momento."
		),
		"en": (
			"I agree to receive news, offers and reminders from you, also by email, SMS and "
			"WhatsApp. I can withdraw this consent at any time."
		),
	},
	campo_persona="marketing_consent",
)


def registra() -> None:
	from crm.moduli import firme
	from crm.permissions.livelli import registra_modulo_piano

	registra_tipo(INFORMATIVA)
	registra_tipo(MARKETING)
	# the advanced signature, an extra of the plan: the simple one is everybody's
	registra_modulo_piano(firme.MODULO)
	# the forms a person owes, in their summary
	from crm.moduli import dovuti
	from crm.persone import riepilogo

	riepilogo.registra_voce(riepilogo.Voce("forms_due", dovuti.nel_riepilogo))
	# a first step of every centre: what people fill in and sign
	from crm.primi_passi import Passo, c_e, registra_passo

	registra_passo(
		Passo(
			"moduli",
			"Forms and consents",
			"What people fill in and sign before an appointment, and what they agree to.",
			lambda: c_e("CRM Form Template Version"),
			("moduli.configura",),
			pagina="Forms",
			ordine=50,
		)
	)
	# its share of the demo: the forms published, signed today, sent, from the website
	from crm.demo.registro import Parte, registra_parte
	from crm.moduli import demo

	registra_parte(
		Parte(
			"moduli",
			"Forms and consents",
			demo.crea,
			dopo=("clienti",),
			descrizione="The privacy notice with its consents, a welcome questionnaire, a session's "
			"sheet and the website's request form: sent this morning to who comes in the next days "
			"and already signed at home by many, signed on the desk's tablet by today's arrivals, "
			"the physiotherapist's sheets, requests from the website.",
		)
	)
