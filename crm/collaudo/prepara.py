# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A centre made ready on an empty test site, as its manager and the agency would
set it up through the screens' own code: the centre the simulation of a week plays
(e2e/simulazione), and the one the team tries on staging (docs/crm/64).

    bench --site <site> execute crm.collaudo.prepara.centro
    bench --site <site> execute crm.collaudo.prepara.centro --kwargs "{'persone': '/path/team.json', 'servizi_finti': 0}"

Only where the site's config says ``"dottorcloud_collaudo": 1``, only for the
agency. It refuses a site that already has people or appointments that are not the
simulation's (an address outside example.com), unless ``forza=1``; made again on
its own centre it finds what it made and goes on.

- **The centre**: its name, logo, Italian, Rome's clock; the plan with every module
  and extra; two locations, their rooms; the team by levels (`crm.permissions.
  utenti`), their qualifications and shifts; the services; the health fund in
  direct form; the company that issues, in test, set up as a medical centre
  (`crm.tessera_sanitaria.preimpostazione`); the subscriptions; reminders, payment
  reminders, the area, the waiting list, online booking, review requests and quotes
  in instalments switched on; the clinical sheets DottorCloud ships, published by
  the medical director.
- **``persone``**: a JSON file, role -> {email, first_name, last_name}: the team's
  real users on staging; without it, the simulation's at example.com. Every one
  gets the known password (``dottorcloud_collaudo_password`` in the site's config,
  else `regole.PASSWORD`).
- **``servizi_finti=1``**: Stripe on the simulation's fake (``stripe_api``), connected
  as the centre connects its own; the email muted and read from the queue; the
  online visits' rooms on a host of example.com. ``0`` (staging) sets up nothing
  outside: the team connects the real sandboxes from the screens.
"""

from __future__ import annotations

import io
import json

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate

from crm.collaudo import regole as R
from crm.collaudo import verifica

#: Where the role -> user of the simulation's team is kept, once made.
SQUADRA = "crm_collaudo_squadra"
#: The fakes' address when the site's config names none.
FINTI = "http://127.0.0.1:8791"
#: A key of the fake Stripe: test mode, as the centre would paste its own.
CHIAVE_STRIPE = "sk_test_51CollaudoSimulazioneDottorCloud0000"
CODICI_TS = {"region_code": "030", "asl_code": "999", "ssa_code": "999999"}


@frappe.whitelist(methods=["POST"])
def centro(persone: str | None = None, servizi_finti: int | str = 1, forza: int | str = 0) -> dict:
	"""Make the centre ready; returns its photograph, what does not hold together
	(nothing, when it worked) and the team's users with their password."""
	verifica()
	_estranei(cint(forza))
	squadra = R.utenti(_leggi(persone))
	_lingua_e_nome()
	_piano()
	sedi = _sedi()
	stanze = _stanze(sedi)
	festivita = _festivita()
	utenti = _squadra(squadra, sedi, festivita)
	servizi = _servizi(utenti, stanze, sedi)
	azienda = _fatturazione(sedi)
	_convenzione(servizi)
	_abbonamenti(servizi)
	_impostazioni(cint(servizi_finti))
	_schede_cliniche(utenti["medico"])
	_moduli(utenti["responsabile"])
	_automazioni()
	if cint(servizi_finti):
		_finti()
	frappe.db.set_default(SQUADRA, json.dumps(utenti))
	frappe.db.commit()
	foto = fotografia()
	return {
		"centre": R.NOME_DEL_CENTRO,
		"company": azienda,
		"team": {ruolo: {"email": email, "password": password()} for ruolo, email in utenti.items()},
		"problems": R.problemi(foto, finti=bool(cint(servizi_finti))),
		"photo": foto,
	}


def _automazioni() -> None:
	"""The campaign and the review request marketing set up, switched on."""
	for definizione in R.AUTOMAZIONI:
		nome = frappe.db.get_value("CRM Automation", {"title": definizione["title"]})
		doc = frappe.get_doc("CRM Automation", nome) if nome else frappe.new_doc("CRM Automation")
		doc.update(
			{
				"title": definizione["title"],
				"enabled": 1,
				"marketing_consent": definizione["marketing_consent"],
				"steps": json.dumps(definizione["steps"]),
			}
		)
		doc.set("triggers", [{"trigger_event": definizione["trigger"]}])
		doc.save(ignore_permissions=True)


def password() -> str:
	return frappe.conf.get("dottorcloud_collaudo_password") or R.PASSWORD


def squadra() -> dict[str, str]:
	"""The team the simulation made: role -> user."""
	return json.loads(frappe.db.get_default(SQUADRA) or "{}")


def _leggi(persone: str | dict | None) -> dict:
	if not persone:
		return {}
	if isinstance(persone, dict):
		return persone
	testo = persone.strip()
	if not testo.startswith("{"):
		with open(testo, encoding="utf-8") as file:
			testo = file.read()
	try:
		return json.loads(testo)
	except ValueError:
		frappe.throw(_("The team's file is not JSON: role, then email, first_name, last_name"))


def _estranei(forza: int) -> None:
	"""A site with people of its own is no test bench: refused, unless forced."""
	if forza:
		return
	if frappe.db.count("CRM Demo Record"):
		frappe.throw(_("This site has the demo data: take it away first, or use an empty site"))
	persone = frappe.get_all("CRM Lead", fields=["name", "email", "mobile_no"], limit=5000)
	# somebody with an address or a number of their own; a child booked by a parent
	# of the simulation has neither
	estranee = [
		p.name
		for p in persone
		if (p.email and not R.della_simulazione(p.email)) or (not p.email and p.mobile_no)
	]
	if estranee:
		frappe.throw(
			_(
				"This site already has people who are not the simulation's ({0}): it is not an empty "
				"test site. Use an empty one, or pass forza=1"
			).format(len(estranee))
		)


def _trova_o_crea(doctype: str, chiave: dict, valori: dict | None = None):
	"""The record ``chiave`` finds, brought up to ``valori``; made when there is none."""
	nome = frappe.db.get_value(doctype, chiave, "name")
	if nome:
		doc = frappe.get_doc(doctype, nome)
		if valori:
			doc.update(valori)
			doc.save(ignore_permissions=True)
		return doc
	return frappe.get_doc({"doctype": doctype, **chiave, **(valori or {})}).insert(ignore_permissions=True)


# -- the centre ------------------------------------------------------------------------------


def _lingua_e_nome() -> None:
	"""The first opening's two screens (`crm.benvenuto`): Italian, the centre's name,
	Rome's clock; then its logo."""
	from crm import benvenuto, lingue

	lingue.italia_dove_nessuno_ha_scelto()
	benvenuto.choose_language("it")
	benvenuto.finish(R.NOME_DEL_CENTRO, "Europe/Rome")
	impostazioni = frappe.get_single("FCRM Settings")
	if not impostazioni.brand_logo:
		file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "poliambulatorio-san-luca.png",
				"content": _logo(),
				"is_private": 0,
				"attached_to_doctype": "FCRM Settings",
				"attached_to_name": "FCRM Settings",
				"attached_to_field": "brand_logo",
			}
		).insert(ignore_permissions=True)
		impostazioni.brand_logo = file.file_url
	impostazioni.currency = impostazioni.currency or "EUR"
	impostazioni.flags.ignore_permissions = True
	impostazioni.save()


def _logo() -> bytes:
	"""The centre's own mark: a square with its initials, as a small centre's logo is."""
	from PIL import Image, ImageDraw, ImageFont

	immagine = Image.new("RGB", (512, 512), "#FFFFFF")
	disegno = ImageDraw.Draw(immagine)
	disegno.rounded_rectangle((32, 32, 480, 480), radius=96, fill="#1F6F78")
	try:
		carattere = ImageFont.load_default(size=220)
	except TypeError:
		carattere = ImageFont.load_default()
	disegno.text((256, 262), "SL", fill="#FFFFFF", font=carattere, anchor="mm")
	uscita = io.BytesIO()
	immagine.save(uscita, format="PNG")
	return uscita.getvalue()


def _piano() -> None:
	"""Every module of the plan on, and the size of a polyclinic: what the simulation
	tries is everything a centre can have."""
	from crm.permissions import livelli

	livelli.carica()
	piano = frappe.get_single("CRM Plan")
	piano.size = "Polyclinic"
	presenti = {riga.module: riga for riga in piano.modules}
	for modulo in livelli.moduli_piano():
		riga = presenti.get(modulo.chiave)
		if riga:
			riga.status = "Active"
			riga.trial_until = None
			riga.expires_on = None
		else:
			piano.append("modules", {"module": modulo.chiave, "status": "Active"})
	piano.flags.ignore_permissions = True
	piano.save()


def _sedi() -> dict[str, str]:
	sedi = {}
	for chiave, nome, via, cap, citta, provincia, telefono, orari in R.SEDI:
		doc = _trova_o_crea(
			"CRM Location",
			{"location_name": nome},
			{
				"enabled": 1,
				"address_line": via,
				"pincode": cap,
				"city": citta,
				"province": provincia,
				"phone": telefono,
				"opening_hours": orari,
			},
		)
		sedi[chiave] = doc.name
	from crm.scheduling import sedi as delle_sedi

	delle_sedi.dimentica()
	return sedi


def _stanze(sedi: dict[str, str]) -> dict[str, str]:
	stanze = {}
	for chiave, nome, sede, posti, colore, descrizione in R.STANZE:
		doc = _trova_o_crea(
			"CRM Resource",
			{"resource_name": nome},
			{
				"resource_type": "Room",
				"capacity": 1,
				"seats": posti,
				"color": colore,
				"description": descrizione,
				"currency": "EUR",
				"centre_location": sedi[sede],
				"enabled": 1,
			},
		)
		stanze[chiave] = doc.name
	return stanze


def _festivita() -> str:
	anno = getdate(nowdate()).year
	giorni = [
		{"date": giorno, "description": nome} for a in (anno, anno + 1) for giorno, nome in R.festivita(a)
	]
	doc = _trova_o_crea(
		"CRM Holiday List",
		{"holiday_list_name": "Festività nazionali"},
		{"from_date": getdate(f"{anno}-01-01"), "to_date": getdate(f"{anno + 1}-12-31"), "holidays": giorni},
	)
	return doc.name


def _squadra(squadra: dict[str, dict], sedi: dict[str, str], festivita: str) -> dict[str, str]:
	"""Each colleague: their user with the levels of their role, their qualification
	as who performs services, their shifts in the locations."""
	from frappe.utils.password import update_password

	from crm.permissions import utenti as dei_livelli

	fatto = {}
	for collega in R.SQUADRA:
		dati = squadra[collega.ruolo]
		email = dati["email"]
		if not frappe.db.exists("User", email):
			utente = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": dati["first_name"],
					"last_name": dati["last_name"],
					"mobile_no": collega.cellulare,
					"user_type": "System User",
					"send_welcome_email": 0,
					"enabled": 1,
				}
			)
			utente.flags.no_welcome_mail = True
			utente.insert(ignore_permissions=True)
		dei_livelli.assegna_livelli(email, list(collega.livelli))
		update_password(email, password())
		fatto[collega.ruolo] = email
		if collega.ruolo == "segreteria":
			# the desk works in Milan: the reception desk opens on it
			from crm.scheduling import sedi as delle_sedi

			delle_sedi.imposta_sede_abituale(sedi["milano"], email)
		if collega.qualifica:
			_trova_o_crea(
				"CRM Service Provider",
				{"user": email},
				{
					"provider_name": f"{dati['first_name']} {dati['last_name']}",
					"qualification": collega.qualifica,
					"enabled": 1,
				},
			)
		if collega.turni:
			_trova_o_crea(
				"CRM Staff Schedule",
				{"user": email},
				{
					"enabled": 1,
					"bookable_online": 1,
					"public_title": collega.titolo,
					"holiday_list": festivita,
					"availability": [
						{
							"workday": giorno,
							"start_time": inizio,
							"end_time": fine,
							"centre_location": sedi[sede],
						}
						for giorno, fasce in collega.turni.items()
						for inizio, fine, sede in fasce
					],
				},
			)
	return fatto


def _servizi(utenti: dict[str, str], stanze: dict[str, str], sedi: dict[str, str]) -> dict[str, str]:
	fatto = {}
	for servizio in R.SERVIZI:
		classe = servizio.posti > 1
		valori = {
			"category": servizio.categoria,
			"enabled": 1,
			"color": servizio.colore,
			"description": servizio.descrizione,
			"duration": servizio.minuti,
			"default_price": servizio.prezzo,
			"price_per_participant": 1 if classe else 0,
			"currency": "EUR",
			"min_participants": 1,
			"max_participants": servizio.posti,
			"online_max_participants": 1,
			"bookable_online": 1 if servizio.online else 0,
			"online_payment": servizio.pagamento,
			"online_deposit": servizio.acconto if servizio.pagamento == "Deposit" else 0,
			"online_visit": 1 if servizio.visita_online else 0,
			"staff_selection": "Any one",
			"staff": [
				{"user": utenti[ruolo], "bookable_online": 1 if servizio.online else 0}
				for ruolo in servizio.chi
			],
			"resources": [{"resource": stanze[servizio.stanza], "quantity": 1, "required": 1}],
			"availability": [
				{"workday": giorno, "start_time": inizio, "end_time": fine, "centre_location": sedi["milano"]}
				for giorno, fasce in servizio.orari.items()
				for inizio, fine in fasce
			],
		}
		doc = _trova_o_crea("CRM Service", {"service_name": servizio.nome}, valori)
		fatto[servizio.chiave] = doc.name
	return fatto


def _fatturazione(sedi: dict[str, str]) -> str:
	"""The company that issues, in test, set up as a medical centre answers the
	healthcare setup's three questions; a card for each service."""
	from crm.tessera_sanitaria import preimpostazione
	from crm.tessera_sanitaria.engine.codici import SoggettoInviante

	azienda = _trova_o_crea(
		"CRM Invoicing Company",
		{"company_name": f"{R.NOME_DEL_CENTRO} S.r.l."},
		{
			"tax_id": R.PARTITA_IVA,
			"fiscal_code": R.PARTITA_IVA,
			"tax_regime": "RF01",
			"address_line": "Via Washington",
			"civic_number": "70",
			"postal_code": "20146",
			"city": "Milano",
			"province": "MI",
			"email": f"amministrazione@{R.DOMINIO}",
			"phone": "+39 02 0000 0300",
			"iban": "IT60X0542811101000000123456",
			"bank_name": "Banca di prova",
		},
	)
	if azienda.provider_environment != "sandbox":
		frappe.throw(_("The simulation's company is not in test: it issues nothing real"))
	preimpostazione.apply_setup(
		company=azienda.name, issuer=SoggettoInviante.STRUTTURA_AUTORIZZATA, regime="RF01", **CODICI_TS
	)
	frappe.db.set_value("CRM Invoicing Company", azienda.name, "is_default", 1)
	impostazioni = frappe.get_single("CRM Invoicing Settings")
	impostazioni.enabled = 1
	impostazioni.default_company = azienda.name
	impostazioni.flags.ignore_permissions = True
	impostazioni.save()
	preimpostazione.cards_from_services(azienda.name)
	for sede in sedi.values():
		frappe.db.set_value("CRM Location", sede, "company", azienda.name)
	return azienda.name


def _convenzione(servizi: dict[str, str]) -> None:
	"""The health fund, in direct form with its authorisation first: the fund pays
	its price list less the person's share, billed once a month."""
	from crm.invoicing import anagrafica

	dati = R.CONVENZIONE
	fondo = frappe.db.get_value("CRM Organization", {"organization_name": dati["azienda"]}, "name")
	if not fondo:
		fondo = (
			frappe.get_doc({"doctype": "CRM Organization", "organization_name": dati["azienda"]})
			.insert(ignore_permissions=True)
			.name
		)
	anagrafica.save_billing_profile(
		"CRM Organization",
		fondo,
		{
			"billing_name": dati["azienda"],
			"tax_id": dati["partita_iva"],
			"fiscal_code": dati["partita_iva"],
			"recipient_code": "0000000",
			"pec": f"fondo@pec.{R.DOMINIO}",
			"address_line": "Via Larga",
			"civic_number": "8",
			"postal_code": "20122",
			"city": "Milano",
			"province": "MI",
			"country": "IT",
		},
	)
	listino = _trova_o_crea(
		"CRM Price List",
		{"price_list_name": dati["listino"]},
		{"enabled": 1, "is_default": 0, "currency": "EUR", "description": "Le tariffe del fondo."},
	)
	for chiave, prezzo in dati["prezzi"].items():
		_trova_o_crea(
			"CRM Service Price",
			{"price_list": listino.name, "service": servizi[chiave]},
			{"price": prezzo, "currency": "EUR", "enabled": 1},
		)
	_trova_o_crea(
		"CRM Convention",
		{"convention_name": dati["nome"]},
		{
			"kind": "Health fund",
			"enabled": 1,
			"organization": fondo,
			"direct": 1,
			"indirect": 1,
			"requires_authorisation": 1,
			"show_online": 1,
			"price_mode": "Price list",
			"price_list": listino.name,
			"share_mode": "Percentage",
			"share_percent": dati["quota"],
		},
	)


def _abbonamenti(servizi: dict[str, str]) -> None:
	scheda = frappe.db.get_value("CRM Billable Service", {"crm_service": servizi["pilates"]}, "name")
	for _chiave, nome, mesi, pagamento, prezzo, a_settimana, online, descrizione in R.ABBONAMENTI:
		_trova_o_crea(
			"CRM Subscription Type",
			{"type_name": nome},
			{
				"enabled": 1,
				"description": descrizione,
				"months": mesi,
				"payment": pagamento,
				"price": prezzo,
				"currency": "EUR",
				"billable_service": scheda,
				"issue_invoices": 1,
				"sold_online": 1 if online else 0,
				"services": [{"service": servizi["pilates"]}],
				"entries": "Per week" if a_settimana else "Unlimited",
				"entries_count": a_settimana,
				"can_suspend": 1,
				"max_suspension_days": 30,
				"remind_days": 7,
			},
		)


def _singolo(doctype: str, valori: dict) -> None:
	doc = frappe.get_single(doctype)
	doc.update(valori)
	doc.flags.ignore_permissions = True
	doc.save()


def _impostazioni(finti: int) -> None:
	"""What the week counts on, switched on as the manager switches it on in Settings."""
	_singolo(
		"CRM Scheduling Settings",
		{
			"timezone": "Europe/Rome",
			"online_booking_enabled": 1,
			"require_privacy_consent": 1,
			"ask_marketing_consent": 1,
			"booking_page_title": R.NOME_DEL_CENTRO,
			"video_server": f"https://video.{R.DOMINIO}" if finti else None,
		},
	)
	_singolo(
		"CRM Reminder Settings",
		{"enabled": 1, "hours_before": 24, "use_email": 1, "use_sms": 0, "cancel_on_reply": 1},
	)
	_singolo(
		"CRM Payment Reminder Settings",
		{
			"enabled": 1,
			"first_after_days": 3,
			"every_days": 7,
			"max_reminders": 2,
			"minimum_amount": 10,
			"use_email": 1,
			"use_sms": 0,
			"how_to_pay": "Bonifico su IT60 X054 2811 1010 0000 0123 456 intestato a Poliambulatorio "
			"San Luca S.r.l., oppure in contanti o con la carta in segreteria.",
		},
	)
	_singolo("CRM Area Settings", {"email_new_documents": 1, "self_check_in": 1})
	_singolo("CRM Waiting List Settings", {"enabled": 1, "online_join": 1, "area_join": 1})
	_singolo(
		"CRM Review Settings",
		{
			"google_review_link": f"https://www.{R.DOMINIO}/recensioni/poliambulatorio-san-luca",
			"months_between": 12,
		},
	)
	_singolo(
		"CRM Quote Settings",
		{
			"valid_days": 30,
			"instalment_invoicing": "Each instalment when due",
			"issue_instalment_invoices": 1,
		},
	)


def _schede_cliniche(medico: str) -> None:
	"""The clinical sheets DottorCloud ships, published by the medical director as
	the forms' builder publishes them."""
	from crm.clinica import schede_pronte
	from crm.moduli import modelli

	schede_pronte.carica_schede(forza=True)
	prima = frappe.session.user
	frappe.set_user(medico)
	try:
		for nome in frappe.get_all(
			modelli.MODELLO,
			filters={"use": modelli.SCHEDA, "clinical": 1, "current_version": ["is", "not set"]},
			pluck="name",
		):
			modelli.publish_template(nome)
	finally:
		frappe.set_user(prima)


def _moduli(responsabile: str) -> None:
	"""The privacy notice every new patient signs before their first appointment,
	sent with the booking: published by the manager in the forms' builder."""
	from crm.moduli import modelli

	if frappe.db.exists(modelli.MODELLO, {"title": "Informativa privacy e consensi"}):
		return
	prima = frappe.session.user
	frappe.set_user(responsabile)
	try:
		fatto = modelli.save_template(
			title="Informativa privacy e consensi",
			schema=json.dumps(R.INFORMATIVA),
			use=modelli.FORMA,
			ask_on="First appointment",
			validity="Forever",
			send_before=1,
			enabled=1,
			description="L'informativa sul trattamento dei dati e il consenso alle novità: si firma una "
			"volta, prima della prima visita.",
		)
		modelli.publish_template(fatto["name"])
	finally:
		frappe.set_user(prima)


def _finti() -> None:
	"""Stripe on the simulation's fake, connected as the centre connects its own; its
	options as the week wants them."""
	from frappe.installer import update_site_config

	from crm.pagamenti import collegamento

	indirizzo = (frappe.conf.get("dottorcloud_collaudo_finti") or FINTI).rstrip("/") + "/v1/"
	if frappe.conf.get("stripe_api") != indirizzo:
		update_site_config("stripe_api", indirizzo)
		frappe.local.conf["stripe_api"] = indirizzo
	collegamento.connect_stripe(CHIAVE_STRIPE)
	collegamento.save_stripe_options(refund_on_cancel=1, refund_hours=24, sell_in_area=1, card_charges=1)


# -- the photograph ---------------------------------------------------------------------------


def fotografia() -> dict:
	"""The centre as it is now, in the words `regole.problemi` checks."""
	from crm.clinica.paziente import clinica_accesa
	from crm.permissions import livelli as registro

	squadra_ = squadra()
	livelli = {}
	turni = {}
	for ruolo, email in squadra_.items():
		livelli[ruolo] = sorted(registro.livelli_di(email))
		orario = frappe.db.get_value("CRM Staff Schedule", {"user": email, "enabled": 1})
		turni[ruolo] = bool(
			orario
			and frappe.db.count("CRM Service Day", {"parenttype": "CRM Staff Schedule", "parent": orario})
		)
	servizi = {}
	for servizio in frappe.get_all(
		"CRM Service",
		filters={"enabled": 1},
		fields=["name", "service_name", "bookable_online", "online_payment"],
	):
		servizi[servizio.service_name] = {
			"staff": frappe.get_all(
				"CRM Service Staff",
				filters={"parent": servizio.name, "parenttype": "CRM Service"},
				pluck="user",
			),
			"stanze": frappe.get_all(
				"CRM Service Resource",
				filters={"parent": servizio.name, "parenttype": "CRM Service"},
				pluck="resource",
			),
			"online": servizio.bookable_online,
			"pagamento": servizio.online_payment or "",
			"scheda": frappe.db.get_value("CRM Billable Service", {"crm_service": servizio.name}),
		}
	azienda = frappe.db.get_single_value("CRM Invoicing Settings", "default_company")
	return {
		"squadra": squadra_,
		"livelli": livelli,
		"turni": turni,
		"servizi": servizi,
		"sedi": frappe.get_all("CRM Location", filters={"enabled": 1}, pluck="name"),
		"azienda": {
			"nome": azienda,
			"ambiente": frappe.db.get_value("CRM Invoicing Company", azienda, "provider_environment"),
		}
		if azienda
		else {},
		"accesi": {
			"clinica": clinica_accesa(),
			"promemoria": cint(frappe.db.get_single_value("CRM Reminder Settings", "enabled")),
			"solleciti": cint(frappe.db.get_single_value("CRM Payment Reminder Settings", "enabled")),
			"attese": cint(frappe.db.get_single_value("CRM Waiting List Settings", "enabled")),
			"prenotazione_online": cint(
				frappe.db.get_single_value("CRM Scheduling Settings", "online_booking_enabled")
			),
			"stripe": cint(frappe.db.get_single_value("CRM Stripe Settings", "enabled")),
		},
		"prezzi": {
			s.service_name: flt(s.default_price)
			for s in frappe.get_all("CRM Service", fields=["service_name", "default_price"])
		},
	}
