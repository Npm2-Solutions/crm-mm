# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Linked people on a real site: the booking pages, the invoice, the person's page.

**A contact belongs to its owner.** Somebody booked by somebody else - a child by
their mother - gets a record of their own without the mother's email and phone:
those stay hers, a call from that number is still hers, and the messages about the
child's appointments reach her through the booking. The child is linked to her,
and she books for them.

**Who a booking is for** (`trova_per_nome`): the contact finds its owner, and the
name says whether it is them or one of the people linked to them. A name nobody
has is somebody new, linked to the owner - never somebody else's record.

The rules, without a site, are in `crm.persone.legami`.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from crm.permissions import livelli, org_hierarchy
from crm.persone import legami

DOCTYPE = "CRM Related Person"
_CAMPI = ["name", "person", "related_person", "relation", "pays", "books", "represents", "note"]
#: How far from the contact's owner a name is looked for: their people, and theirs.
_GIRI = 2
_AL_MASSIMO = 50


# ------------------------------------------------------------------ the links


def legami_di(lead: str) -> list[dict]:
	"""Every link of a person, from either side, as stored."""
	return frappe.get_all(
		DOCTYPE,
		or_filters={"person": lead, "related_person": lead},
		fields=_CAMPI,
		order_by="creation asc",
	)


def collegate_a(lead: str) -> list[str]:
	return [riga.related_person if riga.person == lead else riga.person for riga in legami_di(lead)]


def famiglia(lead: str) -> list[str]:
	"""The people linked to a person, and the people linked to those: a family.

	The father who books with the mother's email finds himself through their child.
	"""
	visti, giro = {lead}, [lead]
	trovate: list[str] = []
	for _passo in range(_GIRI):
		prossimo = []
		for persona in giro:
			for altra in collegate_a(persona):
				if altra not in visti:
					visti.add(altra)
					trovate.append(altra)
					prossimo.append(altra)
		giro = prossimo
		if len(trovate) >= _AL_MASSIMO:
			break
	return trovate[:_AL_MASSIMO]


def chi_fa(lead: str, azione: str) -> list[str]:
	"""Who does ``azione`` - pays, books, represents - for this person."""
	if azione not in legami.AZIONI:
		raise ValueError(azione)
	return frappe.get_all(
		DOCTYPE, filters={"person": lead, azione: 1}, pluck="related_person", order_by="creation asc"
	)


def pagante_di(lead: str) -> str | None:
	"""Whom their invoices are made out to, when one person pays for them.

	Two people paying is a choice the desk makes invoice by invoice.
	"""
	paganti = chi_fa(lead, legami.PAGA)
	return paganti[0] if len(paganti) == 1 else None


def rappresentanti_di(lead: str) -> list[str]:
	"""Who signs and decides for them: a parent of a minor child, a guardian."""
	return chi_fa(lead, legami.RAPPRESENTA)


def _riga_della_coppia(uno: str, altro: str) -> str | None:
	return frappe.db.get_value(
		DOCTYPE,
		{"person": ("in", (uno, altro)), "related_person": ("in", (uno, altro))},
		"name",
	)


def assicura_legame(persona: str, collegata: str, relazione: str, **azioni) -> str:
	"""``collegata`` does ``azioni`` for ``persona``: link them, or add to their link.

	For the booking pages: they know who booked for whom, not what the desk wrote
	about the two. An existing relation stays as the desk wrote it; a link written
	the other way round, with nobody acting, is turned to say who acts now.
	"""
	nome = _riga_della_coppia(persona, collegata)
	riga = frappe.get_doc(DOCTYPE, nome) if nome else frappe.new_doc(DOCTYPE)
	if not nome:
		riga.update({"person": persona, "related_person": collegata, "relation": relazione})
	elif riga.person != persona:
		if any(riga.get(azione) for azione in legami.AZIONI):
			# the other way round, and somebody acts already: the desk's word stands
			return riga.name
		riga.update(
			{"person": persona, "related_person": collegata, "relation": legami.inversa(riga.relation)}
		)
	for azione, valore in azioni.items():
		if valore and azione in legami.AZIONI:
			riga.set(azione, 1)
	riga.flags.ignore_permissions = True
	riga.save()
	return riga.name


def cancella_con_la_persona(doc, method=None) -> None:
	"""A person was deleted: their links go with them, from either side."""
	for nome in frappe.get_all(
		DOCTYPE, or_filters={"person": doc.name, "related_person": doc.name}, pluck="name"
	):
		frappe.delete_doc(DOCTYPE, nome, ignore_permissions=True, force=True)


# ---------------------------------------------------------- who a booking is for


def _nome(lead: str) -> str | None:
	return frappe.db.get_value("CRM Lead", lead, "lead_name")


def trova_per_nome(
	nome: str | None, email: str | None = None, telefono: str | None = None
) -> tuple[str | None, str | None]:
	"""``(person, owner)``: the record a booking with this name and contact goes to,
	and who owns the contact. ``(None, owner)`` is somebody new, booked by the owner;
	``(None, None)`` somebody nobody knows."""
	from crm.api.lead import find_person

	titolare = find_person(email=email, phone=telefono)
	if not titolare:
		return None, None
	candidati = [(persona, _nome(persona)) for persona in famiglia(titolare)]
	return legami.per_chi(nome, (titolare, _nome(titolare)), candidati), titolare


def cerca_per_conto(chi: str, nome: str | None) -> str | None:
	"""Among the people of ``chi``, the one this name means, if one alone."""
	return legami.scegli(nome, [(persona, _nome(persona)) for persona in famiglia(chi)])


def persona_per_conto(chi: str, nome: str, relazione: str = legami.ALTRO, fonte: str | None = None) -> str:
	"""The person ``chi`` books for: found among their people by name, or made.

	Made without a contact of their own - the one typed is ``chi``'s - and linked to
	``chi``, who books for them. ``relazione`` is what ``chi`` is to them.
	"""
	trovata = cerca_per_conto(chi, nome)
	if not trovata:
		from crm.api.form import _default_status

		nome_proprio, cognome = legami.dividi(nome)
		persona = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": nome_proprio,
				"last_name": cognome,
				"status": _default_status("CRM Lead"),
				"source": fonte,
			}
		)
		persona.insert(ignore_permissions=True)
		trovata = persona.name
	if relazione not in legami.RELAZIONI:
		relazione = legami.ALTRO
	assicura_legame(trovata, chi, relazione, books=1)
	return trovata


def raggiunta_tramite(lead: str) -> list[str]:
	"""Who a person without an email or a phone of their own is reached through."""
	propri = frappe.db.get_value("CRM Lead", lead, ["email", "mobile_no", "phone"], as_dict=True)
	if not propri or any(propri.values()):
		return []
	return chi_fa(lead, legami.PRENOTA)


@frappe.whitelist()
def get_contact_for(lead: str) -> dict:
	"""Where the messages about this person's appointments go: their own contact, or
	the contact of whoever books for them - a child is reached through a parent."""
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	persona = frappe.db.get_value(
		"CRM Lead", lead, ["lead_name", "email", "mobile_no", "phone"], as_dict=True
	)
	risposta = {
		"name": lead,
		"lead_name": persona.lead_name,
		"email": persona.email,
		"phone": persona.mobile_no or persona.phone,
		"booked_by": None,
		"booked_by_name": None,
	}
	tramite = raggiunta_tramite(lead)
	if tramite:
		chi = frappe.db.get_value(
			"CRM Lead", tramite[0], ["name", "lead_name", "email", "mobile_no", "phone"], as_dict=True
		)
		risposta.update(
			{
				"email": chi.email,
				"phone": chi.mobile_no or chi.phone,
				"booked_by": chi.name,
				"booked_by_name": chi.lead_name,
			}
		)
	return risposta


# ------------------------------------------------------------- who reads them


def get_permission_query_conditions(user: str | None = None) -> str:
	"""A link is part of both people: listed to whoever sees either of them."""
	visibili = org_hierarchy.visible_leads(user)
	if visibili is None:
		return ""
	riga = frappe.qb.DocType(DOCTYPE)
	condizione = riga.person.isin(visibili) | riga.related_person.isin(visibili)
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


def _legge(persona: str, user: str) -> bool:
	return bool(frappe.has_permission("CRM Lead", "read", doc=persona, user=user))


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	persone = [p for p in (doc.get("person"), doc.get("related_person")) if p]
	if (ptype or "read") in ("read", "print", "export", "report", "email", "share"):
		return not persone or any(_legge(persona, user) for persona in persone)
	# a link is written by whoever writes people, between two people they both see
	if livelli.nel_crm(user) and not livelli.puo("persone.scrivi", user):
		return False
	return all(_legge(persona, user) for persona in persone)


# --------------------------------------------------------- the person's page


def _della_persona(lead: str) -> None:
	livelli.verifica_nel_crm("persone.vedi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _puo_scrivere() -> bool:
	if livelli.nel_crm() and not livelli.puo("persone.scrivi"):
		return False
	return bool(frappe.has_permission(DOCTYPE, "create"))


@frappe.whitelist()
def get_related_people(lead: str) -> dict:
	"""The people linked to this person, each as this person's page reads them."""
	_della_persona(lead)
	persone = []
	for riga in legami_di(lead):
		vista = legami.dal_lato_di(riga, lead)
		altra = frappe.db.get_value("CRM Lead", vista["other"], ["name", "lead_name", "image"], as_dict=True)
		if not altra:
			continue
		persone.append(
			{
				"name": riga.name,
				"other": altra.name,
				"other_name": altra.lead_name or altra.name,
				"image": altra.image,
				"relation": vista["relation"],
				"acts": vista["acts"],
				"pays": riga.pays,
				"books": riga.books,
				"represents": riga.represents,
				"note": riga.note,
				"can_open": _legge(altra.name, frappe.session.user),
			}
		)
	tramite = set(raggiunta_tramite(lead))
	io = frappe.db.get_value("CRM Lead", lead, ["first_name", "lead_name"], as_dict=True) or {}
	return {
		# the page writes "pays for Luca", "Luca books for them"
		"first_name": io.get("first_name") or io.get("lead_name") or lead,
		"people": persone,
		"reached_through": [p["other_name"] for p in persone if p["other"] in tramite],
		"relations": list(legami.RELAZIONI),
		"can_edit": _puo_scrivere(),
	}


def _per_scrivere(lead: str) -> None:
	livelli.verifica_nel_crm("persone.scrivi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _nuova_persona(nome: str | None, cognome: str | None) -> str:
	from crm.api.form import _default_status

	if not (nome or "").strip():
		frappe.throw(_("Pick a person, or write the first name of a new one"))
	persona = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"first_name": nome.strip(),
			"last_name": (cognome or "").strip(),
			"status": _default_status("CRM Lead"),
			# whoever makes a person from the page owns them, as the new-person form does
			"lead_owner": frappe.session.user,
		}
	)
	persona.insert()
	return persona.name


@frappe.whitelist(methods=["POST"])
def save_related_person(
	lead: str,
	relation: str,
	acts: str | None = None,
	other: str | None = None,
	first_name: str | None = None,
	last_name: str | None = None,
	pays: int = 0,
	books: int = 0,
	represents: int = 0,
	note: str | None = None,
	name: str | None = None,
) -> dict:
	"""Link this person to another - existing, or new by name - or change their link.

	``relation`` is what the other is to this person, ``acts`` who acts for whom
	(`crm.persone.legami.VERSI`).
	"""
	_per_scrivere(lead)
	riga = None
	if name:
		riga = frappe.get_doc(DOCTYPE, name)
		if lead not in (riga.person, riga.related_person):
			frappe.throw(_("This link is not this person's"))
		other = riga.related_person if riga.person == lead else riga.person
	elif not other:
		other = _nuova_persona(first_name, last_name)
	frappe.has_permission("CRM Lead", "read", doc=other, throw=True)

	verso = acts or legami.NESSUNO
	try:
		legame = legami.orienta(lead, other, relation, verso)
	except ValueError:
		frappe.throw(_("Pick who they are to this person, and who acts for whom"))
	riga = riga or frappe.new_doc(DOCTYPE)
	riga.update(
		{
			"person": legame.persona,
			"related_person": legame.collegata,
			"relation": legame.relazione,
			"note": note,
			**legami.azioni(
				{"pays": cint(pays), "books": cint(books), "represents": cint(represents)}, verso
			),
		}
	)
	riga.save()
	return get_related_people(lead)


@frappe.whitelist(methods=["POST"])
def remove_related_person(lead: str, name: str) -> dict:
	"""Unlink two people. Neither of them goes anywhere."""
	_per_scrivere(lead)
	riga = frappe.get_doc(DOCTYPE, name)
	if lead not in (riga.person, riga.related_person):
		frappe.throw(_("This link is not this person's"))
	riga.delete()
	return get_related_people(lead)
