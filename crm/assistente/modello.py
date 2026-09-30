# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Asking the model, and writing it down.

One adapter, two ways of speaking, so where the model runs is an address in the
settings and not a branch of this file (design.md, "I dati"):

- **Anthropic**'s Messages API: Claude, through the address the agency sets up -
  in the EU, a gateway that pins the region.
- **OpenAI compatible** chat completions: OpenAI with EU residency, Azure, or a
  model on the centre's own server.

Every request leaves an event in the register (`CRM AI Event`), a failure too:
the function, who asked, the model, the provider, the region, the fingerprints of
what went in and came out, the time. What the model wrote is a draft; `accetta`
records what a person made of it, and `scarta` that they threw it away.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import frappe
import requests
from frappe import _
from frappe.utils import cint, get_fullname, now_datetime

from crm.assistente import funzione, funzioni, regole
from crm.permissions import livelli

IMPOSTAZIONI = "CRM Assistant Settings"
EVENTO = "CRM AI Event"
VERSIONE_ANTHROPIC = "2023-06-01"


@dataclass
class Risposta:
	evento: str
	testo: str = ""
	dati: dict | None = None
	errore: str | None = None


def impostazioni():
	return frappe.get_cached_doc(IMPOSTAZIONI)


def mancano(chiave: str | None = None) -> list[str]:
	"""What stops the assistant, or one of its functions: nothing, or the list."""
	livelli.carica()
	cfg = impostazioni()
	problemi = regole.pronto(cfg.enabled, cfg.provider, cfg.base_url, cfg.model, cfg.no_retention)
	voce = funzione(chiave) if chiave else None
	if voce and voce.interruttore and not cint(cfg.get(voce.interruttore)):
		problemi.append("This function is off in the assistant's settings")
	return problemi


def acceso(chiave: str | None = None) -> bool:
	return not mancano(chiave)


def verifica_acceso(chiave: str) -> None:
	problemi = mancano(chiave)
	if problemi:
		frappe.throw("<br>".join(_(p) for p in problemi), title=_("The assistant is not available"))


def _indirizzo(base: str, percorso: str) -> str:
	base = (base or "").rstrip("/")
	return base + percorso if not base.endswith("/v1") else base + percorso.removeprefix("/v1")


def _invia(cfg, istruzioni: str, testo: str) -> tuple[str, int | None, int | None]:
	"""The model's answer, and the tokens it counted."""
	chiave = cfg.get_password("api_key", raise_exception=False)
	attesa = cint(cfg.request_timeout) or 120
	massimo = cint(cfg.max_output_tokens) or 4000
	if cfg.provider == regole.ANTHROPIC:
		intestazioni = {"anthropic-version": VERSIONE_ANTHROPIC, "content-type": "application/json"}
		if chiave:
			intestazioni["x-api-key"] = chiave
		risposta = requests.post(
			_indirizzo(cfg.base_url, "/v1/messages"),
			json={
				"model": cfg.model,
				"max_tokens": massimo,
				"system": istruzioni,
				"messages": [{"role": "user", "content": testo}],
			},
			headers=intestazioni,
			timeout=attesa,
		)
		risposta.raise_for_status()
		dati = risposta.json()
		scritto = "".join(b.get("text", "") for b in dati.get("content", []) if b.get("type") == "text")
		uso = dati.get("usage") or {}
		return scritto, uso.get("input_tokens"), uso.get("output_tokens")
	intestazioni = {"Authorization": f"Bearer {chiave}"} if chiave else {}
	risposta = requests.post(
		_indirizzo(cfg.base_url, "/v1/chat/completions"),
		json={
			"model": cfg.model,
			"max_tokens": massimo,
			"messages": [{"role": "system", "content": istruzioni}, {"role": "user", "content": testo}],
		},
		headers=intestazioni,
		timeout=attesa,
	)
	risposta.raise_for_status()
	dati = risposta.json()
	scritto = ((dati.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
	uso = dati.get("usage") or {}
	return scritto, uso.get("prompt_tokens"), uso.get("completion_tokens")


def _errore(eccezione: Exception) -> str:
	if isinstance(eccezione, requests.HTTPError) and eccezione.response is not None:
		return f"HTTP {eccezione.response.status_code}"
	if isinstance(eccezione, requests.Timeout):
		return "The model did not answer in time"
	return eccezione.__class__.__name__


def chiedi(
	chiave: str,
	istruzioni: str,
	testo: str,
	*,
	json_atteso: bool = False,
	riferimento: tuple[str, str] | None = None,
) -> Risposta:
	"""Ask the model for one of the registered functions. The event is written
	whatever happens; a failure comes back as ``errore``, never as a guess."""
	voce = funzione(chiave)
	if not voce:
		frappe.throw(_("{0} is not something the assistant does").format(chiave))
	verifica_acceso(chiave)
	cfg = impostazioni()
	inviato = regole.taglia(testo)
	evento = frappe.get_doc(
		{
			"doctype": EVENTO,
			"function": chiave,
			"status": regole.BOZZA,
			"user": frappe.session.user,
			"provider": cfg.provider,
			"model": cfg.model,
			"region": cfg.region,
			"reference_doctype": riferimento[0] if riferimento else None,
			"reference_name": riferimento[1] if riferimento else None,
			"read_capability": voce.legge,
			"input_hash": regole.impronta(istruzioni + "\n\n" + inviato),
		}
	)
	inizio = time.monotonic()
	scritto, dati, errore = "", None, None
	try:
		scritto, entrati, usciti = _invia(cfg, istruzioni, inviato)
		evento.input_tokens, evento.output_tokens = cint(entrati), cint(usciti)
		if json_atteso:
			dati = regole.estrai_json(scritto)
			if dati is None:
				errore = "The answer is not what was asked"
	except Exception as eccezione:
		errore = _errore(eccezione)
	evento.duration_ms = int((time.monotonic() - inizio) * 1000)
	evento.output_hash = regole.impronta(scritto) if scritto else None
	evento.draft = scritto or None
	if errore:
		evento.status = regole.FALLITA
		evento.error = errore
	evento.insert(ignore_permissions=True)
	return Risposta(evento=evento.name, testo=scritto, dati=dati, errore=errore)


def _mio(nome: str):
	evento = frappe.get_doc(EVENTO, nome)
	if evento.user != frappe.session.user:
		frappe.throw(_("This draft was asked for by somebody else"), frappe.PermissionError)
	if evento.status != regole.BOZZA:
		frappe.throw(_("This draft has already been decided"))
	return evento


def accetta(
	nome: str,
	finale: str,
	riferimento: tuple[str, str] | None = None,
	confronto: str | None = None,
):
	"""A person made the draft theirs: what it became, how far from the draft, and
	the mark - checked by whom, and when. ``confronto`` is the draft written the way
	the final text is, when the model's words are not (a schema, say): the register
	keeps the model's own words as they came."""
	evento = _mio(nome)
	bozza = evento.draft if confronto is None else confronto
	evento.final = finale
	evento.difference = regole.differenza(bozza, finale)
	evento.change_ratio = regole.quanto_cambiata(bozza, finale)
	evento.status = regole.ACCETTATA
	evento.checked_by = frappe.session.user
	evento.checked_on = now_datetime()
	if riferimento:
		evento.reference_doctype, evento.reference_name = riferimento
	evento.save(ignore_permissions=True)
	return evento


def consegnata(nome: str) -> None:
	"""An answer given as it came, to whoever asked: no draft waits on it. The
	register keeps it for whoever reads the function's events."""
	if frappe.db.get_value(EVENTO, nome, "status") == regole.BOZZA:
		frappe.db.set_value(EVENTO, nome, "status", regole.CONSEGNATA, update_modified=False)


def scarta(nome: str) -> None:
	evento = _mio(nome)
	evento.status = regole.SCARTATA
	evento.save(ignore_permissions=True)


def segno(evento) -> str:
	"""The words a checked draft carries."""
	return _(regole.SEGNO).format(
		get_fullname(evento.checked_by), frappe.utils.format_datetime(evento.checked_on, "dd/MM/yyyy HH:mm")
	)


# ------------------------------------------------------------------ the register


def _legge(evento, user: str | None = None) -> bool:
	return bool(evento.get("read_capability")) and livelli.puo(evento.read_capability, user)


@frappe.whitelist()
def get_events(function: str | None = None, limit: int = 50) -> dict:
	"""The register, as the session may read it: newest first."""
	if not (livelli.puo("assistente.registro") or any(livelli.puo(f.legge) for f in funzioni())):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	filtri = {"function": function} if function else {}
	righe = []
	for nome in frappe.get_all(EVENTO, filters=filtri, pluck="name", order_by="creation desc", limit=500):
		evento = frappe.get_doc(EVENTO, nome)
		if not _legge(evento):
			continue
		righe.append(
			{
				"name": evento.name,
				"function": evento.function,
				"status": evento.status,
				"user": evento.user,
				"user_name": get_fullname(evento.user),
				"creation": evento.creation,
				"provider": evento.provider,
				"model": evento.model,
				"region": evento.region,
				"change_ratio": evento.change_ratio,
				"reviewed_on": evento.reviewed_on,
			}
		)
		if len(righe) >= min(cint(limit) or 50, 200):
			break
	return {"events": righe}


@frappe.whitelist()
def get_event(name: str) -> dict:
	"""One event, with the draft, the final text and the difference."""
	evento = frappe.get_doc(EVENTO, name)
	if not _legge(evento):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		**{
			campo: evento.get(campo)
			for campo in (
				"name",
				"function",
				"status",
				"user",
				"creation",
				"provider",
				"model",
				"region",
				"reference_doctype",
				"reference_name",
				"input_hash",
				"output_hash",
				"input_tokens",
				"output_tokens",
				"duration_ms",
				"draft",
				"final",
				"difference",
				"change_ratio",
				"error",
				"checked_by",
				"checked_on",
				"reviewed_by",
				"reviewed_on",
				"review_note",
			)
		},
		"user_name": get_fullname(evento.user),
	}


@frappe.whitelist(methods=["POST"])
def mark_reviewed(name: str, note: str | None = None) -> dict:
	"""The monthly sample: a person re-read this event, and says what they found."""
	evento = frappe.get_doc(EVENTO, name)
	if not _legge(evento):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	evento.reviewed_by = frappe.session.user
	evento.reviewed_on = now_datetime()
	evento.review_note = (note or "").strip()[:1000] or None
	evento.save(ignore_permissions=True)
	return get_event(name)


@frappe.whitelist()
def get_status() -> dict:
	"""Whether the assistant runs, for the screens that offer it."""
	return {
		"enabled": acceso(),
		"functions": {f.chiave: acceso(f.chiave) and livelli.puo(f.usa) for f in funzioni()},
		# the settings' switches some registered function uses: the clinic's drafts
		# show only where the clinic brings them
		"switches": sorted({f.interruttore for f in funzioni() if f.interruttore}),
		"purpose": _(regole.SCOPO),
	}
