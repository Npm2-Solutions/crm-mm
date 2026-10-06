# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

"""Loading and taking away the demo data: Settings > The centre > Demo data.

Loading is a job (a couple of minutes: three months of a centre), its progress sent
to whoever asked; each part of the modules that are on is made in turn, and a part
added later - a module switched on after the demo was loaded - is made the next time
somebody loads. Taking them away is one request (`crm.demo.togli`): a few seconds.
"""

from __future__ import annotations

import random

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from crm import verticali
from crm.demo import guardie, registro
from crm.demo.contesto import SEME, Contesto
from crm.demo.modo import in_prova

CAPACITA = "dati_prova.gestisci"
EVENTO = "crm_demo_data"
#: A job that said nothing for this long died: the page stops waiting for it.
MINUTI_SENZA_NOTIZIE = 20


def _verifica() -> None:
	from crm.permissions.livelli import verifica

	verifica(CAPACITA)


# -- what the settings page reads ------------------------------------------------------------------


@frappe.whitelist()
def get_demo_state() -> dict:
	"""Whether the demo data are in, the parts there are, which are made, and whether a
	job is making them now."""
	_verifica()
	fatte = registro.parti_fatte()
	# in the words of the vertical that is on: with the clinic, the patient area
	parola = verticali.traduttore()
	parti = [
		{
			"key": parte.chiave,
			"label": parola(parte.etichetta),
			"description": parola(parte.descrizione),
			"made": parte.chiave in fatte,
			"available": registro.accesa(parte),
		}
		for parte in registro.tutte_le_parti()
	]
	al_lavoro = _al_lavoro()
	lavoro = _lavoro() if al_lavoro else None
	return {
		"demo_data_created": registro.caricati(),
		"working": al_lavoro,
		"progress": {
			"part": lavoro.get("part"),
			"step": lavoro.get("step"),
			"done": lavoro.get("done") or 0,
			"total": lavoro.get("total") or 0,
		}
		if lavoro
		else None,
		"parts": parti,
		"to_make": [parte["key"] for parte in parti if parte["available"] and not parte["made"]],
		"counts": _conti() if registro.caricati() else {},
	}


def _lavoro() -> dict | None:
	"""What the job last said: when, the part, its step, how many parts are made."""
	valore = frappe.db.get_default(registro.LAVORO)
	if not valore:
		return None
	try:
		lavoro = frappe.parse_json(valore)
	except Exception:
		lavoro = None
	return lavoro if isinstance(lavoro, dict) else {"at": valore}


def _al_lavoro() -> bool:
	lavoro = _lavoro()
	if not lavoro:
		return False
	try:
		return (now_datetime() - get_datetime(lavoro.get("at"))).total_seconds() < MINUTI_SENZA_NOTIZIE * 60
	except Exception:
		return False


def _segna_il_lavoro(**avanzamento) -> None:
	"""The job is alive, and where it is: the page reads it when the socket is not
	there to tell it."""
	frappe.db.set_default(registro.LAVORO, frappe.as_json({"at": str(now_datetime()), **avanzamento}))


def _conti() -> dict:
	"""How much the demo holds, by what the screens call it."""
	righe = frappe.db.sql("select ref_doctype, count(*) from `tabCRM Demo Record` group by ref_doctype")
	per_doctype = dict(righe)
	# the colleagues: the people a client area lets in are users too, and the
	# page counted nineteen colleagues where the team was eight
	colleghi = frappe.db.sql(
		"""select count(*) from `tabCRM Demo Record` r join `tabUser` u on u.name = r.ref_name
		where r.ref_doctype = 'User' and u.user_type = 'System User'"""
	)
	return {
		"people": cint(per_doctype.get("CRM Lead")),
		"appointments": cint(per_doctype.get("CRM Appointment")),
		"deals": cint(per_doctype.get("CRM Deal")),
		"team": cint(colleghi[0][0]),
		"records": cint(sum(per_doctype.values())),
	}


# -- loading ------------------------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def load_demo_data() -> dict:
	"""Make the parts not made yet, in a job; the page follows its progress."""
	_verifica()
	if _al_lavoro():
		return {"queued": False, "working": True}
	if not registro.da_fare():
		return {"queued": False, "working": False}
	_accoda(frappe.session.user)
	return {"queued": True, "working": True}


def create_demo_data(_args: dict | None = None) -> None:
	"""After the setup wizard, and from the Desk's button: the demo is made in a job,
	once."""
	if registro.caricati() or _al_lavoro():
		return
	_accoda(frappe.session.user)


def _accoda(utente: str) -> None:
	_segna_il_lavoro()
	frappe.enqueue(
		"crm.demo.api.crea",
		queue="long",
		timeout=3600,
		job_id=f"{frappe.local.site}::crm_demo_data",
		deduplicate=True,
		enqueue_after_commit=True,
		utente=utente,
	)


def crea(utente: str | None = None, scala: float = 1.0) -> dict:
	"""The job: every part to make, in order, each whole or not at all."""
	utente = utente or frappe.session.user
	_pronto_a_scrivere(utente)
	parti = registro.da_fare()
	if frappe.db.get_default(registro.SERIE) is None:
		# the counters before the demo's first record: taking it away puts them back
		frappe.db.set_default(
			registro.SERIE, frappe.as_json(dict(frappe.db.sql("select name, current from `tabSeries`")))
		)
	registro.segna_l_inizio()
	# kept whatever the first part does: a part that fails rolls its own work back
	frappe.db.commit()
	contesto = Contesto(utente=utente, scala=scala)
	fatte, fallite = [], []
	try:
		for indice, parte in enumerate(parti):

			def avanzamento(testo: str, parte=parte, indice=indice) -> None:
				etichetta = verticali.parola(parte.etichetta)
				_annuncia(utente, "progress", parte=etichetta, step=testo, done=indice, total=len(parti))
				_segna_il_lavoro(part=etichetta, step=testo, done=indice, total=len(parti))

			contesto.avanzamento = avanzamento
			# each part draws its own chances: the same part is the same whichever came before
			contesto.rng = random.Random(f"{SEME}:{parte.chiave}")
			avanzamento("")
			try:
				with in_prova(parte.chiave):
					parte.crea(contesto)
			except Exception:
				frappe.log_error(title=f"Demo data: the part {parte.chiave} was not made")
				fallite.append(parte.chiave)
				continue
			registro.segna_fatta(parte.chiave)
			fatte.append(parte.chiave)
			if not registro.caricati():
				frappe.db.set_default(registro.STATO, "1")
			frappe.db.commit()
	finally:
		frappe.db.set_default(registro.LAVORO, None)
		guardie.dimentica()
		frappe.db.commit()
		_annuncia(utente, "done", made=fatte, failed=fallite)
	return {"made": fatte, "failed": fallite}


def _pronto_a_scrivere(utente: str) -> None:
	"""Nothing is made unless it is written down: the hooks a process kept from before
	this release are read again, and a demo that could not be registered is refused."""
	if not _registro_attivo():
		frappe.clear_cache()
	if not _registro_attivo():
		frappe.throw(_("The demo data cannot be made now: try again after the next update."))
	# dates are written in a language: the one of whoever asked, as their requests do
	if not frappe.local.lang:
		from frappe.translate import get_user_lang

		frappe.local.lang = get_user_lang(utente)


def _registro_attivo() -> bool:
	gestori = (frappe.get_hooks("doc_events") or {}).get("*", {}).get("after_insert") or []
	return "crm.demo.registro.annota" in gestori


def _annuncia(utente: str, stato: str, **dati) -> None:
	frappe.publish_realtime(EVENTO, {"state": stato, **dati}, user=utente, after_commit=False)


# -- taking them away -----------------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def clear_demo_data() -> dict | None:
	"""Take the demo away, all of it, now."""
	_verifica()
	if _al_lavoro():
		frappe.throw(_("The demo data are still being made: try again in a minute."))
	if not registro.caricati() and not frappe.db.count(registro.REGISTRO):
		return None
	from crm.demo.togli import togli

	return togli()
