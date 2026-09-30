# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The events of a document, in a register that only grows (`CRM Audit Log`).

Sent, opened, code sent, code checked, signed, the PDF made, a consent recorded:
each with the server's time, who, from which address and device. Every event
carries the SHA-256 of the one before it on the same document, so removing or
changing one breaks the chain after it - and `verifica_catena` says where.

Written the way `CRM Invoice Log` is (docs/gestionale-medico/design.md, "Le prove
di ogni firma"), with the chain added: a form signed today is evidence in years.
"""

from __future__ import annotations

import hashlib
import json

import frappe
from frappe.utils import get_datetime, now_datetime

REGISTRO = "CRM Audit Log"


def _canonico(valori: dict) -> str:
	return json.dumps(valori, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def impronta_evento(precedente: str | None, evento: dict) -> str:
	"""The hash of an event: its own content, chained to the one before."""
	return hashlib.sha256(((precedente or "") + _canonico(evento)).encode("utf-8")).hexdigest()


def _contenuto(riga) -> dict:
	"""What the hash is taken on: everything the event says, nothing Frappe adds."""
	return {
		"reference_doctype": riga.get("reference_doctype"),
		"reference_name": riga.get("reference_name"),
		"event": riga.get("event"),
		"occurred_on": str(get_datetime(riga.get("occurred_on"))),
		"user": riga.get("user"),
		"ip_address": riga.get("ip_address"),
		"user_agent": riga.get("user_agent"),
		"detail": riga.get("detail"),
		"payload": riga.get("payload"),
	}


def ultima_impronta(doctype: str, nome: str) -> str | None:
	ultima = frappe.get_all(
		REGISTRO,
		filters={"reference_doctype": doctype, "reference_name": nome},
		fields=["hash"],
		order_by="creation desc, name desc",
		limit=1,
	)
	return ultima[0].hash if ultima else None


def _richiesta() -> tuple[str | None, str | None]:
	richiesta = getattr(frappe.local, "request", None)
	if not richiesta:
		return None, None
	return (
		getattr(frappe.local, "request_ip", None),
		(richiesta.headers.get("User-Agent") or "")[:500] or None,
	)


def traccia(
	doctype: str,
	nome: str,
	evento: str,
	dettaglio: str | None = None,
	dati: dict | None = None,
	*,
	utente: str | None = None,
) -> str:
	"""Add an event to a document's register. Returns its hash."""
	ip, dispositivo = _richiesta()
	riga = {
		"doctype": REGISTRO,
		"reference_doctype": doctype,
		"reference_name": nome,
		"event": evento,
		"occurred_on": now_datetime(),
		"user": utente or (None if frappe.session.user == "Guest" else frappe.session.user),
		"ip_address": ip,
		"user_agent": dispositivo,
		"detail": dettaglio,
		"payload": _canonico(dati) if dati is not None else None,
	}
	precedente = ultima_impronta(doctype, nome)
	riga["previous_hash"] = precedente
	riga["hash"] = impronta_evento(precedente, _contenuto(riga))
	doc = frappe.get_doc(riga)
	doc.flags.dalla_traccia = True
	doc.insert(ignore_permissions=True)
	return riga["hash"]


def eventi(doctype: str, nome: str) -> list[dict]:
	return frappe.get_all(
		REGISTRO,
		filters={"reference_doctype": doctype, "reference_name": nome},
		fields=[
			"name",
			"reference_doctype",
			"reference_name",
			"event",
			"occurred_on",
			"user",
			"ip_address",
			"user_agent",
			"detail",
			"payload",
			"previous_hash",
			"hash",
		],
		order_by="creation asc, name asc",
	)


def verifica_catena(doctype: str, nome: str) -> dict:
	"""Whether a document's register is whole: every hash is its content's, and
	each event points at the one before it. `rotto_a` is the first that is not."""
	precedente = None
	elenco = eventi(doctype, nome)
	for posizione, riga in enumerate(elenco):
		if riga.previous_hash != precedente or riga.hash != impronta_evento(precedente, _contenuto(riga)):
			return {"integra": False, "eventi": len(elenco), "rotto_a": posizione, "evento": riga.name}
		precedente = riga.hash
	return {"integra": True, "eventi": len(elenco), "rotto_a": None, "evento": None}
