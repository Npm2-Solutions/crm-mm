# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Which `tipoSpesa` a line carries, and whether it can carry one at all.

This used to sit inside the invoicing classifier, where it made a module that
issues invoices for any sector look like it had opinions about healthcare expense
codes. It does not. It knows a line may owe a report to some other system; what
that system calls the line is here.

Plugged in through `crm.invoicing.estensioni.registra_arricchitore`.
"""

from __future__ import annotations

from crm.invoicing.engine.classificazione import RigaDaClassificare
from crm.invoicing.engine.messaggi import Messaggio

from .codici import FLAG_TIPO_SPESA_AMMESSO, tipi_spesa_ammessi
from .voci import FLAG_TIPO_SPESA, SOGGETTO_INVIANTE, TIPO_SPESA, nome, nomi


def risolvi_tipo_spesa(
	riga: RigaDaClassificare, emittente: str, erogatore: str
) -> tuple[str | None, list[str]]:
	"""(service, performer's qualification, **issuer's category**) -> `tipoSpesa`.

	Two different subjects, which coincide in a solo practice and diverge in a
	facility:

	* **whoever performs** decides whether the service is exempt and whether it goes
	  to the Sistema TS - the same session is `SR` from the doctor and `SP` from the
	  physiotherapist;
	* **whoever issues the fiscal document** decides which codes are *usable*,
	  because it is their category that ends up in `proprietario.soggetto`, and the
	  tracciato validates the field against it.

	When a facility does the invoicing the codes are its own - `SR CT PI IC AA` for
	an authorised one - and **`SP` is not among them**, however much a health
	professional performed the session. Picking from the profession would produce a
	document that is rejected at send time: with the invoice already issued and
	already handed to the patient.
	"""
	ammessi = tipi_spesa_ammessi(emittente)
	problemi: list[str] = []

	if riga.quota_non_a_carico and riga.quota_non_a_carico > 0 and "AA" in ammessi:
		return "AA", problemi

	candidato = riga.tipo_spesa_catalogo
	if candidato and candidato in ammessi:
		return candidato, problemi
	if candidato:
		problemi.append(
			Messaggio(
				'the service card says the expense type is "{0}", which is not admitted to whoever issues the invoice ("{1}" can only use {2}). The expense type follows who issues the invoice, not the service: correct the service card',
				nome(TIPO_SPESA, candidato),
				nome(SOGGETTO_INVIANTE, emittente),
				nomi(TIPO_SPESA, ammessi),
			)
		)
		return None, problemi

	if len(ammessi) == 1:
		# The health professional invoicing in their own name: `SP` and nothing else.
		return next(iter(ammessi)), problemi

	naturali = tipi_spesa_ammessi(erogatore)
	if erogatore != emittente and not (naturali & ammessi):
		problemi.append(
			Messaggio(
				'the expense type is not determinable: the service is performed by "{0}", who would use {1}, but the invoice is issued by "{2}", who can only use {3}. Choose it on the service card',
				nome(SOGGETTO_INVIANTE, erogatore),
				nomi(TIPO_SPESA, naturali),
				nome(SOGGETTO_INVIANTE, emittente),
				nomi(TIPO_SPESA, ammessi),
			)
		)
	else:
		problemi.append(
			Messaggio(
				'the expense type is not determinable: the service card does not say, and "{0}" can use more than one ({1}). Choose it on the service card',
				nome(SOGGETTO_INVIANTE, emittente),
				nomi(TIPO_SPESA, ammessi),
			)
		)
	return None, problemi


def arricchisci(riga, emittente: str | None, erogatore: str | None) -> tuple[str | None, list[str]]:
	"""The enricher invoicing calls: the code, plus anything wrong with it.

	The `flagTipoSpesa` rule travels with the code because it is the same knowledge:
	the flag is only admitted alongside particular codes, and checking it anywhere
	else would mean two modules holding half a rule each.
	"""
	tipo_spesa, problemi = risolvi_tipo_spesa(riga, emittente or "", erogatore or "")

	flag = getattr(riga, "flag_tipo_spesa", None)
	if flag and tipo_spesa:
		atteso = FLAG_TIPO_SPESA_AMMESSO.get(flag)
		if atteso != tipo_spesa:
			problemi.append(
				Messaggio(
					'"{0}" only goes with the expense type "{1}", not with "{2}"',
					nome(FLAG_TIPO_SPESA, flag),
					nome(TIPO_SPESA, atteso),
					nome(TIPO_SPESA, tipo_spesa),
				)
			)
	return tipo_spesa, problemi
