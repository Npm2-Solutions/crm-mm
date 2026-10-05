# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's Meta ads (doc 53), with the plan's "marketing" module.

The centre's page with its two lead forms, the campaigns with their ads, the ad
account and what each ad spent day by day: stored as the Meta connection stores what
Meta sends (`oauth.upsert_page`, `insights._store_insight`, the ads' cache), never
asked of Meta - the page has no token and nothing is synced. Made before the people:
whoever the story brings "from Instagram" or "from Facebook" while an ad for what
they need was running arrives through its lead form, as Meta hands a lead over
(`leads.store_lead`: the person, their answers, the ledger, the paid-social channel,
the deal), and then books, comes and pays like everybody else - so the cost of a new
client is counted.

Made only where the centre has no Meta page nor ad account of its own: its leads and
its spend never meet the demo's. Nothing about the demo reaches Meta afterwards
either (`crm.demo.guardie.mai_fuori`): not a conversion, not an ad's preview.
"""

from __future__ import annotations

import datetime
import random
from dataclasses import dataclass

import frappe
from frappe import _

from crm.demo import dati
from crm.demo.contesto import SEME, Contesto

PAGINA = "Facebook Page"
MODULO = "Facebook Lead Form"
ANNUNCIO = "Facebook Ad"
ACCOUNT = "Facebook Ad Account"
IMPORTAZIONE = "Facebook Lead Import"
#: The sources whose people Meta may bring, and Meta's name for the platform.
PIATTAFORME = {"Instagram": "ig", "Facebook": "fb"}
#: Who stands for Meta's webhook on the server.
SISTEMA = "Administrator"


def crea(ctx: Contesto) -> None:
	if _del_centro():
		# a centre that has Meta connected: its leads and its spend are its own
		return
	from crm.integrations.meta import ads, insights, leads, oauth
	from crm.moduli.richieste import nome_del_centro

	ctx.avanza(_("Meta ads"))
	centro = nome_del_centro() or "Centro"
	pagina = _id(ctx.rng, 15)
	inizio = ctx.giorno(-max(campagna[4][0] for campagna in dati.META_CAMPAGNE) - 7)
	with ctx.come(SISTEMA):
		oauth.upsert_page(
			{
				"id": pagina,
				"name": f"{centro} (dati di prova)",
				"category": "Medical & Health",
				"tasks": ["ADVERTISE", "ANALYZE", "CREATE_CONTENT"],
			}
		)
		ctx.ricorda(PAGINA, pagina, "meta.pagina")
		ctx.retrodata(PAGINA, pagina, ctx.alle(inizio, "10:00"), SISTEMA)
		for chiave, (nome, domande) in dati.META_MODULI.items():
			modulo = _id(ctx.rng, 16)
			oauth._upsert_form(
				pagina,
				{
					"id": modulo,
					"name": nome,
					"status": "ACTIVE",
					"questions": [{"key": k, "label": e, "type": t} for k, e, t in domande],
				},
			)
			ctx.ricorda(MODULO, modulo, f"meta.modulo.{chiave}")
			ctx.retrodata(MODULO, modulo, ctx.alle(inizio, "10:05"), SISTEMA)
		account = insights.remember_account(
			{
				"id": f"act_{_id(ctx.rng, 15)}",
				"name": f"{centro} (dati di prova)",
				"currency": "EUR",
				"account_status": 1,
			}
		)
		ctx.ricorda(ACCOUNT, account, "meta.account")
		ctx.retrodata(ACCOUNT, account, ctx.alle(inizio, "10:10"), SISTEMA)
		for _chiave, campagna, gruppo, _percorsi, (dal, al), annunci in dati.META_CAMPAGNE:
			campagna_id = _id(ctx.rng, 17)
			for chiave_annuncio, nome, titolo, parole, _modulo in annunci:
				annuncio = _id(ctx.rng, 17)
				nomi = {
					"ad_name": nome,
					"adset_name": gruppo,
					"campaign_id": campagna_id,
					"campaign_name": campagna,
				}
				# what the leads and the previews read: the names, and the ad's own words,
				# as Meta described it the day the campaign started
				leads._remember_ad(annuncio, nomi)
				ads._remember(
					annuncio,
					{
						"creative_title": titolo,
						"creative_body": parole,
						"creative_fetched_on": frappe.utils.now(),
						"effective_status": "ACTIVE" if not al else "PAUSED",
					},
				)
				ctx.ricorda(ANNUNCIO, annuncio, f"meta.annuncio.{chiave_annuncio}")
				ctx.retrodata(ANNUNCIO, annuncio, ctx.alle(ctx.giorno(-dal), "09:00"), SISTEMA)
				_spesa(ctx, insights, account, annuncio, nomi, dal, al)
	ctx.salva()


def _del_centro() -> bool:
	"""Whether the centre has a Meta page or ad account of its own."""
	from crm.demo import registro

	for doctype in (PAGINA, ACCOUNT):
		propri = set(frappe.get_all(doctype, pluck="name")) - registro.nomi_di_prova(doctype)
		if propri:
			return True
	return False


def _id(rng: random.Random, cifre: int) -> str:
	"""A number shaped like Meta's ids, the demo's own."""
	return str(rng.randint(10 ** (cifre - 1), 10**cifre - 1))


def _spesa(ctx: Contesto, insights, account: str, annuncio: str, nomi: dict, dal: int, al: int) -> None:
	"""What the ad spent each day it ran, up to yesterday: Meta's daily rows."""
	for giorni_fa in range(dal, max(al, 1) - 1, -1):
		spesa = round(max(0.5, ctx.rng.uniform(*dati.META_SPESA) * ctx.scala), 2)
		impressioni = int(spesa * ctx.rng.uniform(*dati.META_IMPRESSIONI))
		insights._store_insight(
			account,
			{
				"ad_id": annuncio,
				**nomi,
				"date_start": str(ctx.giorno(-giorni_fa)),
				"spend": spesa,
				"impressions": impressioni,
				"clicks": int(impressioni * ctx.rng.uniform(*dati.META_CLIC)),
			},
		)


# -- the people Meta brings ---------------------------------------------------------------------


@dataclass(frozen=True)
class Annuncio:
	annuncio: str
	modulo: str
	chiave_modulo: str
	nomi: dict
	percorsi: tuple[str, ...]
	dal: int
	al: int


class Annunci:
	"""The demo's ads, for the simulation: who arrives from Meta, through which ad.

	Its chances are its own: the people's story is the same with Meta's part or
	without it, only the way some of them arrive changes."""

	def __init__(self, ctx: Contesto):
		self.ctx = ctx
		self.rng = random.Random(f"{SEME}:meta.arrivi")
		self.annunci: list[Annuncio] = []
		for _chiave, _campagna, _gruppo, percorsi, (dal, al), annunci in dati.META_CAMPAGNE:
			for chiave_annuncio, _nome, _titolo, _parole, chiave_modulo in annunci:
				annuncio = ctx.trova(f"meta.annuncio.{chiave_annuncio}")
				modulo = ctx.trova(f"meta.modulo.{chiave_modulo}")
				if not (annuncio and modulo):
					continue
				valori = frappe.db.get_value(
					ANNUNCIO,
					annuncio,
					["ad_name", "adset_name", "campaign_id", "campaign_name"],
					as_dict=True,
				)
				self.annunci.append(
					Annuncio(annuncio, modulo, chiave_modulo, dict(valori or {}), percorsi, dal, al)
				)

	@classmethod
	def della_demo(cls, ctx: Contesto) -> Annunci | None:
		"""The demo's ads, where its Meta part was made."""
		if not ctx.trova("meta.pagina"):
			return None
		annunci = cls(ctx)
		return annunci if annunci.annunci else None

	def per(self, fonte: str, percorso: str | None, quando: datetime.datetime) -> Annuncio | None:
		"""The ad that brought somebody from ``fonte`` for ``percorso`` at ``quando``: one
		running then for what they need, or none - then they found the centre by
		themselves."""
		if fonte not in PIATTAFORME:
			return None
		giorni_fa = (self.ctx.oggi - quando.date()).days
		adatti = [
			annuncio
			for annuncio in self.annunci
			if (percorso or "lezioni") in annuncio.percorsi and annuncio.al <= giorni_fa <= annuncio.dal
		]
		return self.rng.choice(adatti) if adatti else None

	def arriva(
		self,
		annuncio: Annuncio,
		*,
		fonte: str,
		nome: str,
		cognome: str,
		email: str | None,
		cellulare: str | None,
		percorso: str | None,
		creata: datetime.datetime,
	) -> str | None:
		"""Meta hands the lead over, as its webhook does: the person, their answers, the
		ledger, the paid-social channel and the deal. Returns the person, or None when
		Meta's import would not take them."""
		from crm.integrations.meta import leads

		ctx = self.ctx
		risposte = [{"name": "full_name", "values": [f"{nome} {cognome}"]}]
		if email:
			risposte.append({"name": "email", "values": [email]})
		if cellulare:
			risposte.append({"name": "phone_number", "values": [cellulare]})
		if annuncio.chiave_modulo == "prima":
			motivi = dati.META_MOTIVI.get(percorso or "")
			if motivi:
				risposte.append({"name": "motivo", "values": [self.rng.choice(motivi)]})
		else:
			risposte.append({"name": "quando", "values": [self.rng.choice(dati.META_QUANDO)]})
		lead = {
			"id": _id(self.rng, 16),
			"created_time": str(creata),
			"ad_id": annuncio.annuncio,
			**annuncio.nomi,
			"platform": PIATTAFORME[fonte],
			"field_data": risposte,
		}
		with ctx.come(SISTEMA):
			if leads.store_lead(lead, annuncio.modulo) != "created":
				return None
		persona = frappe.db.get_value("CRM Lead", {"facebook_lead_id": lead["id"]}, "name")
		if not persona:
			return None
		# the ledger and the first touch at the moment Meta handed the lead over
		frappe.db.set_value(IMPORTAZIONE, lead["id"], "imported_on", creata, update_modified=False)
		ctx.retrodata(IMPORTAZIONE, lead["id"], creata, SISTEMA)
		frappe.db.set_value(
			"CRM Lead",
			persona,
			{"first_touch_on": creata, "last_touch_on": creata},
			update_modified=False,
		)
		return persona
