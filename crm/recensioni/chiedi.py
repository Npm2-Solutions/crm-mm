# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Asking how a visit went, on the site: the settings, the gate an automation's
message passes before it leaves, the request it writes, the link it carries.

An automation asks for a review by writing `{{ review_link }}` in a message (an
email, an SMS, a WhatsApp template's variable); it asks for a questionnaire with
the step «Send a form» on a survey. Before such a message leaves, the engine asks
`perche_no` - the rules are `crm.recensioni.regole`'s - and logs the reason as a
skipped step; a review request is then written (`CRM Review Request`), before the
message leaves, and the link in it is the request's own, which counts the click
and sends the person on to Google (`vai`). Whatever automation asks, the same
person is asked once every so many months.

The settings say only where the review is written, how often, and which services
nobody is asked after: never whom, since Google forbids choosing who is asked.
"""

from __future__ import annotations

import hashlib
import hmac

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import get_datetime, get_url, now_datetime

from crm.permissions import livelli
from crm.recensioni import regole

IMPOSTAZIONI = "CRM Review Settings"
RICHIESTA = "CRM Review Request"
CAPACITA = "automazioni.gestisci"

#: The channel a step speaks on, as the request keeps it.
CANALI = {"send_email": "Email", "send_sms": "SMS", "send_whatsapp_template": "WhatsApp"}
CANALI_DEL_MODULO = {"email": "Email", "sms": "SMS", "whatsapp": "WhatsApp"}
#: The forms' use for a survey (registered by `crm.recensioni.registra`).
SONDAGGIO = "Survey"


def impostazioni():
	return frappe.get_cached_doc(IMPOSTAZIONI)


def link_di_google() -> str | None:
	doc = impostazioni()
	return regole.link_di_google(doc.google_review_link, doc.google_place_id)


def controlla(doc) -> None:
	"""The settings as they are saved: a link the browser opens, a place id
	Google would know, the months within reason, each service once."""
	doc.google_review_link = (doc.google_review_link or "").strip() or None
	doc.google_place_id = (doc.google_place_id or "").strip() or None
	if doc.google_review_link and not regole.link_valido(doc.google_review_link):
		frappe.throw(_("The review link is a web address starting with https://"))
	if doc.google_place_id and not regole.place_id_valido(doc.google_place_id):
		frappe.throw(_("A Google Place ID is made of letters, digits, dashes and underscores"))
	doc.months_between = regole.mesi_tra(doc.months_between)
	doc.excluded_services = "\n".join(regole.servizi(doc.excluded_services)) or None


# ------------------------------------------------------------------ the gate


def persona_di(ref_doc) -> str | None:
	if ref_doc.doctype == "CRM Lead":
		return ref_doc.name
	return ref_doc.get("lead")


def puo_essere_chiesto(lead: str | None) -> bool:
	"""Whether this person agreed to be asked how a visit went (`regole.puo_chiedere`)."""
	from crm.moduli import consensi

	if not lead:
		return False
	return regole.puo_chiedere(consensi.stato(lead, regole.CONSENSO), consensi.stato(lead, regole.MARKETING))


def chiede_una_recensione(step: dict) -> bool:
	return regole.chiede_una_recensione(
		step.get("subject"), step.get("message"), step.get("template_parameters")
	)


def chiede_un_questionario(step: dict) -> bool:
	"""A «Send a form» step whose form is a survey."""
	if step.get("type") != "send_form" or not step.get("template"):
		return False
	from crm.moduli import modelli

	return modelli.uso(frappe.db.get_value(modelli.MODELLO, step["template"], "use")).chiave == SONDAGGIO


def _appuntamento(payload: dict) -> str | None:
	nome = (payload or {}).get("appointment")
	return nome if nome and frappe.db.exists("CRM Appointment", nome) else None


def _non_e_venuto(appuntamento: str, ref_doc) -> bool:
	"""Whether the person this enrollment follows did not come to that appointment."""
	from crm.clienti import regole as clienti

	stato = frappe.db.get_value("CRM Appointment", appuntamento, "status")
	for riga in frappe.get_all(
		"CRM Appointment Participant",
		filters={"parent": appuntamento, "parenttype": "CRM Appointment", "party": ref_doc.name},
		fields=["status"],
	):
		if clienti.presente(stato, riga.status):
			return False
	return True


def ultima_richiesta(lead: str, eccetto: str | None = None):
	"""When this person was last asked for a review, by any automation but
	``eccetto`` (the enrollment asking now, whose second message is no second
	request)."""
	filtri = {"lead": lead}
	if eccetto:
		filtri["enrollment"] = ("!=", eccetto)
	return frappe.db.get_value(RICHIESTA, filtri, "sent_on", order_by="sent_on desc")


def perche_no(step: dict, enrollment, ref_doc, payload: dict | None = None) -> str | None:
	"""Why this message asking how a visit went must not leave, in words for the
	automation's runs; None when it may, or when it asks nothing of the kind."""
	recensione = chiede_una_recensione(step)
	if not recensione and not chiede_un_questionario(step):
		return None
	lead = persona_di(ref_doc)
	if not puo_essere_chiesto(lead):
		return _("Did not agree to be asked how a visit went: not sent")
	appuntamento = _appuntamento(payload or {})
	if appuntamento and _non_e_venuto(appuntamento, ref_doc):
		return _("Did not come to the appointment: not sent")
	if not recensione:
		return None
	doc = impostazioni()
	if not link_di_google():
		return _("No Google review link in Settings > Marketing > Review requests: not sent")
	servizio = (payload or {}).get("service")
	if regole.escluso(servizio, doc.excluded_services):
		return _("No review is asked after this service: not sent")
	ultima = ultima_richiesta(lead, enrollment.name if enrollment else None)
	if regole.troppo_presto(get_datetime(ultima) if ultima else None, now_datetime(), doc.months_between):
		return _("Asked for a review less than {0} months ago: not sent").format(
			regole.mesi_tra(doc.months_between)
		)
	return None


def _firma(nome: str) -> str:
	"""The request's link carries its name and this signature: nothing is kept that
	opens it, and the SMS and the email of the same request carry the same link."""
	segreto = (frappe.local.conf.get("encryption_key") or frappe.local.site).encode()
	return hmac.new(segreto, f"recensione|{nome}".encode(), hashlib.sha256).hexdigest()[:20]


def link_della_richiesta(nome: str) -> str:
	return get_url(f"/api/method/crm.recensioni.chiedi.vai?r={nome}.{_firma(nome)}")


def _richiesta_del_link(r) -> str | None:
	if not isinstance(r, str) or len(r) > 80 or "." not in r:
		return None
	nome, _punto, firma = r.partition(".")
	return nome if hmac.compare_digest(firma, _firma(nome)) else None


def prepara(step: dict, enrollment, ref_doc, payload: dict | None = None) -> str | None:
	"""The link a review request carries, its request written first: once per
	enrollment, its second message (an email after the SMS) the same request.
	None for a message that asks no review."""
	if not chiede_una_recensione(step):
		return None
	nome = enrollment and frappe.db.get_value(RICHIESTA, {"enrollment": enrollment.name}, "name")
	if not nome:
		payload = payload or {}
		servizio = payload.get("service")
		richiesta = frappe.get_doc(
			{
				"doctype": RICHIESTA,
				"lead": persona_di(ref_doc),
				"appointment": _appuntamento(payload),
				"service": servizio if servizio and frappe.db.exists("CRM Service", servizio) else None,
				"sent_on": now_datetime(),
				"channel": CANALI.get(step.get("type")) or CANALI_DEL_MODULO.get(step.get("via")),
				"automation": enrollment.automation if enrollment else None,
				"enrollment": enrollment.name if enrollment else None,
			}
		).insert(ignore_permissions=True)
		nome = richiesta.name
	return link_della_richiesta(nome)


# nosemgrep: guest-whitelisted-method — the request's own link, opened by a browser with no session, 120/h
@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=120, seconds=60 * 60)
def vai(r: str | None = None):
	"""The link of a review request: the first opening is counted, then Google.
	Nothing about the person goes to Google with it."""
	destinazione = link_di_google() or get_url("/")
	nome = _richiesta_del_link(r)
	if nome and frappe.db.exists(RICHIESTA, {"name": nome, "clicked_on": ("is", "not set")}):
		frappe.db.set_value(RICHIESTA, nome, "clicked_on", now_datetime(), update_modified=False)
		frappe.db.commit()  # nosemgrep: frappe-manual-commit, whitelisted-side-effect-on-get — a link is a GET by design, and a GET is rolled back
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = destinazione


def cancella_con_la_persona(doc, method=None) -> None:
	"""The review requests a person was sent go with them."""
	for nome in frappe.get_all(RICHIESTA, filters={"lead": doc.name}, pluck="name"):
		frappe.delete_doc(RICHIESTA, nome, ignore_permissions=True, force=True)


# ------------------------------------------------------------------ the settings page


def _servizi() -> list[dict]:
	return [
		{"value": servizio.name, "label": servizio.service_name or servizio.name}
		for servizio in frappe.get_all(
			"CRM Service", filters={"enabled": 1}, fields=["name", "service_name"], order_by="service_name"
		)
	]


def _pagina() -> dict:
	doc = frappe.get_doc(IMPOSTAZIONI)
	return {
		"google_review_link": doc.google_review_link or "",
		"google_place_id": doc.google_place_id or "",
		"months_between": regole.mesi_tra(doc.months_between),
		"excluded_services": regole.servizi(doc.excluded_services),
		"review_link": regole.link_di_google(doc.google_review_link, doc.google_place_id),
		"services": _servizi(),
	}


@frappe.whitelist()
def get_settings() -> dict:
	livelli.verifica(CAPACITA)
	return _pagina()


@frappe.whitelist(methods=["POST"])
def save_settings(
	google_review_link: str | None = None,
	google_place_id: str | None = None,
	months_between: int | None = None,
	excluded_services: list | str | None = None,
) -> dict:
	livelli.verifica(CAPACITA)
	if not regole.mesi_validi(months_between):
		# a 0 typed is refused where it is typed, never kept as twelve in silence
		frappe.throw(_("From {0} to {1} months").format(1, regole.MESI_MASSIMI))
	esclusi = (
		frappe.parse_json(excluded_services) if isinstance(excluded_services, str) else excluded_services
	)
	doc = frappe.get_doc(IMPOSTAZIONI)
	doc.google_review_link = google_review_link
	doc.google_place_id = google_place_id
	doc.months_between = months_between
	doc.excluded_services = "\n".join(regole.servizi(esclusi or []))
	doc.save()
	return _pagina()
