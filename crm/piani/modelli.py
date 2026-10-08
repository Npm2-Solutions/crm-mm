# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Plans kept to start others from: a «1,800 kcal Mediterranean», a «Back,
first month», written once and given to the next person in a minute.

- **What a template keeps** (`CRM Plan Template`): a plan's moments and items,
  what the person reads and what a module keeps besides (a diet's targets and
  calories), never a person: nothing in it is health data.
- **Whose it is**: its author's; shared, it is offered to whoever of the centre
  writes plans of its kind (`api.tipi_consentiti`). Only its author changes or
  removes it.
- **Starting from one** gives the editor a new draft's content with keys of its
  own; what the library no longer offers (an exercise switched off) is left out,
  and said.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import frappe
from frappe import _
from frappe.utils import cint, get_fullname

from crm.permissions import livelli
from crm.piani import api
from crm.piani import regole as R

MODELLO = "CRM Plan Template"
#: What a template keeps of a plan besides its moments and items.
CAMPI = ("instructions", "show_calories", "targets")


def _visibili(user: str, tipo: str | None = None) -> list[dict]:
	"""The templates ``user`` may start from: their own and the shared ones, of the
	kinds they write."""
	tipi = api.tipi_consentiti(user)
	if tipo:
		tipi = [tipo] if tipo in tipi else []
	if not tipi:
		return []
	return frappe.get_all(
		MODELLO,
		filters={"plan_type": ("in", tipi)},
		or_filters=[["practitioner", "=", user], ["shared", "=", 1]],
		fields=["name", "title", "plan_type", "practitioner", "shared", "content", "modified"],
		order_by="modified desc",
	)


def _contenuto(riga) -> dict:
	try:
		return json.loads(riga.content or "{}") if isinstance(riga.content, str) else (riga.content or {})
	except ValueError:
		return {}


@frappe.whitelist()
def get_templates(plan_type: str | None = None) -> list[dict]:
	"""The templates the session may start from: its own and the centre's shared
	ones, of the kinds it writes."""
	livelli.verifica("piani.scrivi")
	user = frappe.session.user
	risposta = []
	for riga in _visibili(user, plan_type):
		contenuto = _contenuto(riga)
		risposta.append(
			{
				"name": riga.name,
				"title": riga.title,
				"plan_type": riga.plan_type,
				"shared": cint(riga.shared),
				"mine": riga.practitioner == user,
				"practitioner_name": get_fullname(riga.practitioner),
				"moments": len(contenuto.get("moments") or []),
				"items": len(contenuto.get("items") or []),
			}
		)
	return risposta


@frappe.whitelist(methods=["POST"])
def save_template(data: dict | str, title: str, shared: int | str = 0, name: str | None = None) -> dict:
	"""What the editor holds, kept as a template: a new one, or one of the
	session's own written again."""
	livelli.verifica("piani.scrivi")
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	tipo = dati.get("plan_type")
	if tipo not in api.tipi_consentiti():
		frappe.throw(_("Your qualification does not write a plan of this kind"), frappe.PermissionError)
	titolo = (title or "").strip()
	if not titolo:
		frappe.throw(_("A template has a title"))
	momenti, voci = api._righe(dati)
	if not voci:
		frappe.throw(_("A template has something in it"))
	api._controlla(tipo, momenti, voci)
	contenuto = {
		**{campo: dati.get(campo) for campo in CAMPI if dati.get(campo) not in (None, "")},
		"moments": momenti,
		"items": [{k: v for k, v in voce.items() if v not in (None, "")} for voce in voci],
	}
	# the same title of one's own, of the same kind, is that template written again
	name = name or frappe.db.get_value(
		MODELLO, {"practitioner": frappe.session.user, "plan_type": tipo, "title": titolo[:140]}
	)
	if name:
		doc = frappe.get_doc(MODELLO, name)
		if doc.practitioner != frappe.session.user:
			frappe.throw(_("A template is changed by who wrote it"), frappe.PermissionError)
	else:
		doc = frappe.new_doc(MODELLO)
		doc.practitioner = frappe.session.user
	doc.title = titolo[:140]
	doc.plan_type = tipo
	doc.shared = 1 if cint(shared) else 0
	doc.content = json.dumps(contenuto, ensure_ascii=False)
	if name:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)
	return {"name": doc.name, "title": doc.title, "shared": doc.shared}


@frappe.whitelist(methods=["POST"])
def delete_template(name: str) -> None:
	"""A template taken away by who wrote it; the plans made from it stay."""
	livelli.verifica("piani.scrivi")
	if frappe.db.get_value(MODELLO, name, "practitioner") != frappe.session.user:
		frappe.throw(_("A template is removed by who wrote it"), frappe.PermissionError)
	frappe.delete_doc(MODELLO, name, ignore_permissions=True)


@frappe.whitelist()
def use_template(name: str) -> dict:
	"""A template's content for a new draft: new keys, each item with what its
	library says of it; what the library no longer offers left out, and counted."""
	livelli.verifica("piani.scrivi")
	user = frappe.session.user
	riga = next((r for r in _visibili(user) if r.name == name), None)
	if not riga:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	contenuto = _contenuto(riga)
	nuove = {}
	momenti = []
	for momento in contenuto.get("moments") or []:
		nuove[momento.get("key")] = api._chiave()
		momenti.append({**momento, "key": nuove[momento.get("key")]})
	voci = []
	for voce in contenuto.get("items") or []:
		if voce.get("moment") not in nuove:
			continue
		voci.append({**voce, "key": api._chiave(), "moment": nuove[voce["moment"]]})
	voci, tolte = _ancora_in_libreria(voci)
	finto = SimpleNamespace(
		moments=[
			frappe._dict(
				moment_key=m["key"],
				label=m.get("label"),
				day=m.get("day") or R.OGNI_GIORNO,
				time=m.get("time"),
				note=m.get("note"),
			)
			for m in momenti
		],
		items=[frappe._dict({**v, "item_key": v["key"], "moment_key": v["moment"]}) for v in voci],
	)
	momenti_letti, voci_lette = api.righe_del_piano(finto)
	return {
		"plan_type": riga.plan_type,
		"title": riga.title,
		**{campo: contenuto.get(campo) for campo in CAMPI if campo in contenuto},
		"moments": momenti_letti,
		"items": voci_lette,
		"left_out": tolte,
	}


def _ancora_in_libreria(voci: list[dict]) -> tuple[list[dict], int]:
	"""The items whose library entry is still offered; how many were not."""
	tenute, tolte = [], 0
	for chiave, genere in api._generi.items():
		if not (genere.campo and genere.libreria):
			continue
		nomi = {v.get(genere.campo) for v in voci if v.get("kind") == chiave and v.get(genere.campo)}
		if not nomi:
			continue
		offerti = set(
			frappe.get_all(genere.libreria, filters={"name": ("in", list(nomi)), "enabled": 1}, pluck="name")
		)
		for voce in voci:
			if voce.get("kind") == chiave and voce.get(genere.campo) not in offerti:
				voce["_tolta"] = True
	for voce in voci:
		if voce.pop("_tolta", False):
			tolte += 1
		else:
			tenute.append(voce)
	return tenute, tolte
