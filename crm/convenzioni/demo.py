# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's conventions, through the conventions' own code (doc 61).

The agenda's part made the price list of «Convenzione Salute+»: here it becomes an
insurance in direct form - Salute+ authorises each visit and pays the centre, the
person pays a fifth - with the people it covers, their visits of the last weeks
authorised and done, and one to come still waiting for its authorisation. The
company the centre signed with gives its employees a tenth off, in indirect form.
Made before invoicing: the visits under Salute+ are invoiced to the person at
their share, as the desk would.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.convenzioni import api
from crm.convenzioni import regole as R
from crm.demo.contesto import Contesto, nome_libero
from crm.demo.simulazione import persone_della_demo

APPUNTAMENTO = "CRM Appointment"
#: A partita IVA with its check digit right, nobody's (the codice fiscale's «Y»
#: trick does not exist for a VAT number: it is made up and checked here).
PARTITA_IVA = "01234567897"


def crea(ctx: Contesto) -> None:
	ctx.avanza(_("Conventions and funds"))
	manager = ctx.squadra("manager") or ctx.utente
	desk = ctx.squadra("desk") or ctx.utente
	with ctx.come(manager):
		fondo = _salute_piu(ctx)
		azienda = _azienda(ctx)
	ctx.salva()
	with ctx.come(desk):
		if fondo:
			_assicurati(ctx, fondo)
		if azienda:
			_dipendenti(ctx, azienda)


def _salute_piu(ctx: Contesto) -> str | None:
	from crm.invoicing import anagrafica

	listino = ctx.trova("agenda.convenzione")
	if not listino:
		return None
	chi_paga = frappe.get_doc(
		{
			"doctype": "CRM Organization",
			"organization_name": nome_libero("CRM Organization", "Salute+ Assicurazioni S.p.A."),
		}
	).insert(ignore_permissions=True)
	anagrafica.save_billing_profile(
		"CRM Organization",
		chi_paga.name,
		{
			"billing_name": "Salute+ Assicurazioni S.p.A.",
			"tax_id": PARTITA_IVA,
			"fiscal_code": PARTITA_IVA,
			"recipient_code": "SPLUS01",
			"address_line": "Corso Italia",
			"civic_number": "40",
			"postal_code": "20122",
			"city": "Milano",
			"province": "MI",
			"country": "IT",
		},
	)
	nome = nome_libero(api.CONVENZIONE, "Salute+")
	api.save_convention(
		{
			"convention_name": nome,
			"kind": R.ASSICURAZIONE,
			"enabled": 1,
			"organization": chi_paga.name,
			"direct": 1,
			"indirect": 1,
			"requires_authorisation": 1,
			"show_online": 1,
			"price_mode": R.LISTINO,
			"price_list": listino,
			"share_mode": R.PERCENTUALE,
			"share_percent": 20,
			"notes": "Autorizzazione dalla centrale operativa Salute+ prima di ogni visita; "
			"estratto mensile caricato sul portale delle strutture entro il 10.",
		}
	)
	return nome


def _azienda(ctx: Contesto) -> str | None:
	chi = ctx.trova("company.studio_bianchi")
	if not chi:
		return None
	nome = nome_libero(api.CONVENZIONE, "Dipendenti Studio Bianchi")
	api.save_convention(
		{
			"convention_name": nome,
			"kind": R.AZIENDA,
			"enabled": 1,
			"organization": chi,
			"indirect": 1,
			"price_mode": R.SCONTO,
			"discount_percent": 10,
		}
	)
	return nome


def _visite(persona: str, servizi: list[str], dal, al) -> list[str]:
	"""A person's appointments alone, of these services, between two moments: no
	cycle, no subscription."""
	return [
		r[0]
		for r in frappe.db.sql(
			"""select a.name from `tabCRM Appointment` a
			join `tabCRM Appointment Participant` p on p.parent = a.name
			where p.party_type = 'CRM Lead' and p.party = %(persona)s and a.service in %(servizi)s
			and ifnull(a.session_cycle, '') = '' and ifnull(p.subscription, '') = ''
			and a.status != 'Cancelled' and a.starts_on between %(dal)s and %(al)s
			and (select count(*) from `tabCRM Appointment Participant` q where q.parent = a.name) = 1
			order by a.starts_on""",
			{"persona": persona, "servizi": servizi, "dal": dal, "al": al},
		)
	]


def _sotto(appuntamento: str, convenzione: str, forma: str, autorizzazione: str | None) -> bool:
	doc = frappe.get_doc(APPUNTAMENTO, appuntamento)
	doc.convention = convenzione
	doc.convention_form = forma
	doc.authorisation = autorizzazione
	try:
		doc.save()
	except frappe.ValidationError:
		# a clash the simulation kept, a subscription: left as it was
		frappe.clear_last_message()
		return False
	return True


def _assicurati(ctx: Contesto, fondo: str) -> None:
	"""Five people covered by Salute+: their visits of the last five weeks
	authorised and done, one to come still to authorise."""
	servizi = [
		s for s in (ctx.trova("service.osteo"), ctx.trova("service.nutri"), ctx.trova("service.fisio")) if s
	]
	if not servizi:
		return
	dal, al = ctx.giorno(-35), ctx.giorno(30)
	persone = [p for p in persone_della_demo(ctx) if _visite(p, servizi, dal, al)]
	scelte = ctx.rng.sample(persone, min(5, len(persone)))
	numero = 4100
	da_autorizzare = None
	for indice, persona in enumerate(scelte):
		api.save_cover(
			persona,
			{
				"convention": fondo,
				"card_number": f"SP{ctx.rng.randint(1000000, 9999999)}",
				"valid_from": str(ctx.giorno(-365)),
				"valid_upto": str(ctx.giorno(200)),
			},
		)
		for appuntamento in _visite(persona, servizi, dal, al):
			futuro = frappe.db.get_value(APPUNTAMENTO, appuntamento, "starts_on") > ctx.adesso
			numero += ctx.rng.randint(3, 40)
			# the first one to come waits for Salute+'s yes; the rest were authorised
			senza = futuro and da_autorizzare is None
			if _sotto(appuntamento, fondo, R.DIRETTA, None if senza else f"SP-2026-{numero}") and senza:
				da_autorizzare = appuntamento
		if indice == 0:
			ctx.ricorda("CRM Lead", persona, "convenzioni.assicurato")


def _dipendenti(ctx: Contesto, azienda: str) -> None:
	"""The people of the company come with its discount, paid at the desk."""
	chi = ctx.trova("company.studio_bianchi")
	persone = frappe.get_all(
		"CRM Lead",
		filters={"organization": chi, "name": ["in", persone_della_demo(ctx) or [""]]},
		pluck="name",
	)
	servizi = list(ctx.con_chiave("service.").values())
	for persona in persone:
		api.save_cover(persona, {"convention": azienda, "card_number": ""})
		for appuntamento in _visite(persona, servizi, ctx.giorno(-14), ctx.giorno(30))[:2]:
			_sotto(appuntamento, azienda, R.INDIRETTA, None)
