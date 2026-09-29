# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The consent register, on the site: writing answers, withdrawing them, reading
a person's state, and the calls behind the "Consents" panel and its settings.

An answer is written once and never edited (`CRM Consent`). The state of a person
for a kind of consent is their latest answer; where a module asked for it, a field
of the person mirrors it, so lists and automations can filter on "may we write to
them" without reading the register.
"""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.moduli import registro
from crm.permissions import livelli, org_hierarchy

TIPO = "CRM Consent Type"
REGISTRO = "CRM Consent"

_CAMPI_RIGA = (
	"name",
	"consent_type",
	"status",
	"answered_on",
	"channel",
	"note",
	"withdrawn_on",
	"withdrawal_channel",
	"recorded_by",
	"given_by",
	"given_by_name",
	"creation",
)


def assicura_tipi() -> None:
	"""Create the registered kinds that are not there yet, in the site's language.

	Never touches one that exists: its text is the centre's, checked by whoever
	answers for privacy there, and a migration must not put the shipped one back.
	"""
	from crm.registrazione import carica

	carica()
	lingua = frappe.db.get_single_value("System Settings", "language")
	for tipo in registro.tipi():
		if frappe.db.exists(TIPO, tipo.chiave):
			continue
		frappe.get_doc(
			{
				"doctype": TIPO,
				"key": tipo.chiave,
				"label": tipo.etichetta,
				"kind": tipo.natura,
				"text": registro.testo_per_lingua(tipo, lingua),
				"description": tipo.descrizione,
				"standard": 1,
				"plan_module": tipo.piano,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)


def _nel_piano(tipi: list[dict]) -> list[dict]:
	"""The kinds whose plan module is on: a clinic's dossier is nothing to a gym."""
	# registered first: the registry counts a module nobody declared as on
	livelli.carica()
	moduli = livelli.moduli_attivi()
	return [
		tipo
		for tipo in tipi
		if livelli.stato_modulo(tipo.get("plan_module") or "base", moduli) != livelli.SPENTO
	]


def puo_vedere(chiave: str) -> bool:
	"""Whether the session may see this kind: some say more than they seem to.

	An answer about a health dossier says the person is a patient, and sales and
	marketing are not told who is one.
	"""
	livelli.carica()
	tipo = registro.tipo(chiave)
	return not (tipo and tipo.capacita) or livelli.puo(tipo.capacita)


def _tipo(chiave: str):
	if not frappe.db.exists(TIPO, chiave):
		assicura_tipi()
	tipo = frappe.db.get_value(
		TIPO, chiave, ["name", "label", "kind", "enabled", "text", "text_version"], as_dict=True
	)
	if not tipo:
		frappe.throw(_("There is no consent called {0}").format(chiave))
	return tipo


def testo_attuale(chiave: str) -> str | None:
	"""The words a person reads today for this consent, if it is switched on."""
	tipo = _tipo(chiave)
	return tipo.text if tipo.enabled else None


def risposte(lead: str, chiave: str | None = None) -> list[dict]:
	filtri = {"lead": lead}
	if chiave:
		filtri["consent_type"] = chiave
	return frappe.get_all(REGISTRO, filters=filtri, fields=list(_CAMPI_RIGA))


def risposta_attuale(lead: str, chiave: str) -> dict | None:
	return registro.stato_attuale(risposte(lead, chiave))


def stato(lead: str, chiave: str) -> str | None:
	"""Given, Refused, Withdrawn, or None when the person was never asked."""
	attuale = risposta_attuale(lead, chiave)
	return attuale["status"] if attuale else None


def ha_il_consenso(lead: str, chiave: str) -> bool:
	return stato(lead, chiave) == registro.DATO


def registra_risposta(
	lead: str,
	chiave: str,
	stato: str = registro.DATO,
	canale: str = "At the desk",
	*,
	testo: str | None = None,
	fonte: tuple[str, str] | None = None,
	nota: str | None = None,
	allegato: str | None = None,
	ip: str | None = None,
	browser: str | None = None,
	dato_da: str | None = None,
) -> str:
	"""Write an answer, on the words the person read.

	``testo`` is for a page that shows its own words (the privacy tick of
	/prenota, in the visitor's language); otherwise the kind's current text and
	its version are copied onto the answer. ``dato_da`` is the person who
	answered for them: the parent of a minor child, whoever booked for them.
	"""
	if dato_da == lead:
		dato_da = None
	if stato not in (registro.DATO, registro.RIFIUTATO):
		frappe.throw(_("An answer says yes or no; a withdrawal is recorded on the consent it withdraws"))
	if canale not in registro.CANALI:
		frappe.throw(_("Unknown channel: {0}").format(canale))
	tipo = _tipo(chiave)
	# One "Given" row per person and kind at most, and it is the current one: a
	# second yes writes nothing, a no after a yes is a withdrawal. Whoever asks
	# "did they agree?" of the table directly - the clinical record does, for the
	# dossier - can trust a "Given" row.
	attuale = risposta_attuale(lead, chiave)
	if attuale and attuale["status"] == registro.DATO:
		if stato == registro.DATO:
			return attuale["name"]
		return revoca(lead, chiave, canale, nota)
	risposta = frappe.get_doc(
		{
			"doctype": REGISTRO,
			"lead": lead,
			"consent_type": tipo.name,
			"status": stato,
			"answered_on": now_datetime(),
			"channel": canale,
			"recorded_by": None if frappe.session.user == "Guest" else frappe.session.user,
			"source_doctype": fonte[0] if fonte else None,
			"source_name": fonte[1] if fonte else None,
			"ip_address": ip,
			"user_agent": (browser or "")[:500] or None,
			"text": testo or tipo.text,
			# a page's own words are not a version of the kind's text
			"text_version": None if testo else tipo.text_version,
			"note": nota,
			"attachment": allegato,
			"given_by": dato_da,
		}
	)
	risposta.insert(ignore_permissions=True)
	rispecchia(lead, chiave)
	return risposta.name


def revoca(lead: str, chiave: str, canale: str = "At the desk", nota: str | None = None) -> str:
	"""Withdraw the consent a person gave: stamped on the answer that gave it."""
	if canale not in registro.CANALI:
		frappe.throw(_("Unknown channel: {0}").format(canale))
	tipo = _tipo(chiave)
	attuale = risposta_attuale(lead, chiave)
	if not registro.puo_revocare(attuale, tipo.kind):
		frappe.throw(_("There is no consent given to withdraw"))
	risposta = frappe.get_doc(REGISTRO, attuale["name"])
	risposta.update(
		{
			"status": registro.REVOCATO,
			"withdrawn_on": now_datetime(),
			"withdrawal_channel": canale,
			"withdrawal_note": nota,
			"withdrawn_by": None if frappe.session.user == "Guest" else frappe.session.user,
		}
	)
	risposta.save(ignore_permissions=True)
	rispecchia(lead, chiave)
	return risposta.name


def rispecchia(lead: str, chiave: str) -> None:
	"""Copy the state onto the person, where the kind asked for it."""
	from crm.registrazione import carica

	carica()
	tipo = registro.tipo(chiave)
	if tipo and tipo.campo_persona and frappe.db.exists("CRM Lead", lead):
		frappe.db.set_value("CRM Lead", lead, tipo.campo_persona, stato(lead, chiave), update_modified=False)


def cancella_con_la_persona(doc, method=None) -> None:
	"""A person was deleted: their answers go with them.

	Kept, they would stop the deletion; and a right to be forgotten that keeps a
	record of what the forgotten person agreed to is not one.
	"""
	for nome in frappe.get_all(REGISTRO, filters={"lead": doc.name}, pluck="name"):
		frappe.delete_doc(REGISTRO, nome, ignore_permissions=True, force=True)


# ------------------------------------------------------------ who reads them


def _tipi_nascosti(user: str | None = None) -> list[str]:
	"""The kinds ``user`` may not see: a health dossier's answers, to sales."""
	livelli.carica()
	return [tipo.chiave for tipo in registro.tipi() if tipo.capacita and not livelli.puo(tipo.capacita, user)]


def get_permission_query_conditions(user: str | None = None) -> str:
	"""A person's consents follow the person: listed to whoever sees them, and
	only the kinds they may see."""
	registro_consensi = frappe.qb.DocType(REGISTRO)
	condizioni = []
	visibili = org_hierarchy.visible_leads(user)
	if visibili is not None:
		condizioni.append(registro_consensi.lead.isin(visibili))
	if nascosti := _tipi_nascosti(user):
		condizioni.append(registro_consensi.consent_type.notin(nascosti))
	if not condizioni:
		return ""
	condizione = condizioni[0]
	for altra in condizioni[1:]:
		condizione = condizione & altra
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	if doc.get("consent_type") in _tipi_nascosti(user):
		return False
	if not doc.get("lead"):
		return True
	return bool(frappe.has_permission("CRM Lead", "read", doc=doc.lead, user=user))


# ------------------------------------------------------------------ the panel


def _della_persona(lead: str) -> None:
	livelli.verifica_nel_crm("consensi.vedi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


@frappe.whitelist()
def get_consents(lead: str) -> dict:
	"""Every kind of consent switched on, with this person's answer to it."""
	_della_persona(lead)
	per_tipo: dict[str, list[dict]] = {}
	for riga in risposte(lead):
		per_tipo.setdefault(riga.consent_type, []).append(riga)
	puo_raccogliere = livelli.puo("consensi.raccogli")
	tipi = []
	for tipo in _nel_piano(
		frappe.get_all(
			TIPO,
			filters={"enabled": 1},
			fields=["name", "label", "kind", "text", "text_version", "plan_module"],
			order_by="creation asc",
		)
	):
		if not puo_vedere(tipo.name):
			continue
		attuale = registro.stato_attuale(per_tipo.get(tipo.name, []))
		tipi.append(
			{
				"key": tipo.name,
				"label": _(tipo.label),
				"kind": tipo.kind,
				"text": tipo.text,
				"text_version": tipo.text_version,
				"current": attuale,
				"can_withdraw": puo_raccogliere and registro.puo_revocare(attuale, tipo.kind),
			}
		)
	return {
		"types": tipi,
		"can_record": puo_raccogliere,
		"channels": list(registro.CANALI_A_MANO),
		# who may answer for them: the people linked to them, whoever acts for them first
		"answered_by": _chi_risponde_per(lead),
	}


def _chi_risponde_per(lead: str) -> list[dict]:
	from crm.persone.collegate import collegate_a, rappresentanti_di

	rappresentanti = rappresentanti_di(lead)
	collegate = sorted(collegate_a(lead), key=lambda persona: persona not in rappresentanti)
	return [
		{
			"name": persona,
			"label": frappe.db.get_value("CRM Lead", persona, "lead_name") or persona,
			"represents": persona in rappresentanti,
		}
		for persona in collegate
	]


def _per_scrivere(lead: str, canale: str, chiave: str) -> None:
	livelli.verifica("consensi.raccogli")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	if not puo_vedere(chiave):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if canale not in registro.CANALI_A_MANO:
		frappe.throw(_("A consent recorded by hand is given at the desk, on paper, by phone or by email"))


@frappe.whitelist(methods=["POST"])
def record_consent(
	lead: str,
	consent_type: str,
	status: str = registro.DATO,
	channel: str = "At the desk",
	note: str | None = None,
	attachment: str | None = None,
	given_by: str | None = None,
) -> dict:
	"""Record an answer given outside the CRM's pages: at the desk, on paper, on the phone.

	``given_by`` is somebody linked to the person who answered for them - the parent
	of a minor child - and nobody else.
	"""
	_per_scrivere(lead, channel, consent_type)
	if given_by:
		from crm.persone.collegate import collegate_a

		if given_by not in collegate_a(lead):
			frappe.throw(_("Only somebody linked to this person can answer for them"))
	# a "no" from somebody who had said yes is written as the withdrawal it is
	registra_risposta(
		lead, consent_type, status, channel, nota=note, allegato=attachment, dato_da=given_by or None
	)
	return get_consents(lead)


@frappe.whitelist(methods=["POST"])
def withdraw_consent(
	lead: str, consent_type: str, channel: str = "At the desk", note: str | None = None
) -> dict:
	"""Withdrawing is as easy as giving: whoever records answers records this too."""
	_per_scrivere(lead, channel, consent_type)
	revoca(lead, consent_type, channel, note)
	return get_consents(lead)


# ------------------------------------------------------------- the settings


_CAMPI_TIPO = (
	"name",
	"label",
	"kind",
	"enabled",
	"standard",
	"plan_module",
	"text",
	"text_version",
	"text_updated_on",
	"description",
)


@frappe.whitelist()
def consent_types() -> list[dict]:
	livelli.verifica("consensi.configura")
	assicura_tipi()
	return _nel_piano(frappe.get_all(TIPO, fields=list(_CAMPI_TIPO), order_by="creation asc"))


@frappe.whitelist(methods=["POST"])
def save_consent_type(
	key: str,
	label: str | None = None,
	text: str | None = None,
	enabled: int | None = None,
	description: str | None = None,
) -> dict:
	"""Rewrite a kind of consent. A new text is a new version; the answers keep theirs."""
	livelli.verifica("consensi.configura")
	tipo = frappe.get_doc(TIPO, key)
	for campo, valore in (
		("label", label),
		("text", text),
		("enabled", enabled),
		("description", description),
	):
		if valore is not None:
			tipo.set(campo, valore)
	tipo.save(ignore_permissions=True)
	return {campo: tipo.get(campo) for campo in _CAMPI_TIPO}


@frappe.whitelist(methods=["POST"])
def new_consent_type(label: str, text: str, kind: str = registro.CONSENSO) -> dict:
	"""A consent of the centre's own: photos for the social pages, a newsletter."""
	livelli.verifica("consensi.configura")
	if kind not in (registro.CONSENSO, registro.PRESA_VISIONE):
		frappe.throw(_("Unknown kind of consent: {0}").format(kind))
	base = re.sub(r"[^a-z0-9]+", "_", frappe.scrub(label or "")).strip("_") or "consent"
	chiave, numero = base, 1
	while frappe.db.exists(TIPO, chiave):
		numero += 1
		chiave = f"{base}_{numero}"
	tipo = frappe.get_doc(
		{"doctype": TIPO, "key": chiave, "label": label, "kind": kind, "text": text, "enabled": 1}
	).insert(ignore_permissions=True)
	return {campo: tipo.get(campo) for campo in _CAMPI_TIPO}
