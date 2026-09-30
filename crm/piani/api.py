# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Plans on the person's page: written by somebody of the centre, followed in the area.

- **Who writes which** (`piani.scrivi`): the kinds switched on here, of the
  author's qualification (`regole.tipi_per`): a training and habits whoever
  writes plans; the kinds a module brings, the qualifications it says - a diet a
  doctor, a biologist nutritionist or a dietitian.
- **Who reads it**: its author, always; once published, whoever reads the
  person's plans (`piani.vedi`, `piani.scrivi`) and sees the person. A plan with
  health data (`clinical`: its kind's mark, or its author's - with the clinic on,
  what a health professional writes) is read by the rule the clinic registers
  instead (`registra_lettore_clinico`), like a visit, and every opening goes in
  the access log; with nobody registered, only its author reads it.
- **Published, a plan is not rewritten.** A new version starts as a draft that
  replaces it once published, or the plan is closed. Publishing closes the
  person's other plan of the same kind - one diet at a time - and who enters the
  area gets an email that says only that there is news.
- **What a module adds**: how its items name their library and read
  (`registra_genere`), what its kinds keep besides the rows (`registra_estensione`)
  - the clinic's foods, a menu's targets and calories.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass, field

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_fullname, getdate, now_datetime

from crm.permissions import livelli, org_hierarchy
from crm.piani import regole as R

PIANO = "CRM Personal Plan"
ESERCIZIO = "CRM Exercise"
REGISTRO = "CRM Personal Plan Log"
BOZZA, PUBBLICATO, CHIUSO = "Draft", "Published", "Closed"
#: How far back a plan shows how the days went.
GIORNI_ANDAMENTO = 14


# ------------------------------------------------------------------ what a module adds


@dataclass(frozen=True)
class Genere:
	"""A kind of item at work: the library it names an entry of, and how it reads."""

	chiave: str
	#: The item's field that names an entry of a library, and the library.
	campo: str | None = None
	libreria: str | None = None
	#: The library's entries, by name, with what the pages read of them.
	dettagli: Callable[[set[str]], dict[str, dict]] | None = None
	#: What the author reads of an item besides its fields: the entry's name, its numbers.
	per_l_autore: Callable[[dict, dict | None], dict] | None = None
	#: What the person reads in their area: (item, plan, what the day's items need).
	per_la_persona: Callable[[dict, object, dict], dict] | None = None
	#: What a day's items of this kind need, once: an exchange diet's choices.
	contesto: Callable[[list[dict]], dict] | None = None
	#: Its fields that are numbers, and how they are read.
	numeri: dict[str, Callable] = field(default_factory=dict)


@dataclass(frozen=True)
class Estensione:
	"""What a module keeps on a plan besides its rows: a menu's targets and calories."""

	#: What a plan's reading adds.
	legge: Callable[[object], dict]
	#: What a draft's writing takes from what was sent.
	scrive: Callable[[object, dict], None]
	#: The fields a new version copies.
	copia: tuple[str, ...] = ()


@dataclass(frozen=True)
class LettoreClinico:
	"""Who reads a plan with health data where a module says so: the clinic, like a visit."""

	legge: Callable[[object, str], bool]
	#: The same, as a condition on the table; None: nobody but the author.
	condizione: Callable[[object, str], object | None]
	#: Whether a plan or a programme is health data whatever its kind: what a
	#: health professional writes for a patient.
	marca: Callable[[object], bool] | None = None


_generi: dict[str, Genere] = {}
_estensioni: list[Estensione] = []
_lettore: dict[str, LettoreClinico] = {}


def registra_genere(genere: Genere) -> None:
	_generi[genere.chiave] = genere


def registra_estensione(estensione: Estensione) -> None:
	if estensione not in _estensioni:
		_estensioni.append(estensione)


def registra_lettore_clinico(lettore: LettoreClinico) -> None:
	_lettore["clinico"] = lettore


def genere(chiave: str | None) -> Genere | None:
	return _generi.get(chiave or "")


# ------------------------------------------------------------------ who reads, who writes


def qualifica_di(user: str) -> str | None:
	"""Somebody's qualification: the one of their provider record, if they have one."""
	return frappe.db.get_value("CRM Service Provider", {"user": user, "enabled": 1}, "qualification")


def legge_i_piani(user: str | None = None) -> bool:
	"""Whether ``user`` reads the plans of the people they see."""
	user = user or frappe.session.user
	return livelli.puo("piani.vedi", user) or livelli.puo("piani.scrivi", user)


def puo_leggere(doc, user: str | None = None) -> bool:
	"""Its author, always; the others once published: with health data by the
	clinic's rule, else whoever reads plans and sees the person."""
	user = user or frappe.session.user
	if doc.get("practitioner") == user:
		return True
	if doc.get("status") == BOZZA:
		return False
	if cint(doc.get("clinical")):
		lettore = _lettore.get("clinico")
		return bool(lettore and lettore.legge(doc, user))
	return legge_i_piani(user) and bool(
		frappe.has_permission("CRM Lead", "read", doc=doc.get("lead"), user=user)
	)


def condizione(tabella, user: str):
	"""Who reads a plan or a programme, as a condition on its table: the same rule."""
	proprio = tabella.practitioner == user
	altri = None
	if legge_i_piani(user):
		visibili = org_hierarchy.visible_leads(user)
		altri = tabella.clinical == 0
		if visibili is not None:
			altri = altri & tabella.lead.isin(visibili)
	lettore = _lettore.get("clinico")
	clinici = lettore.condizione(tabella, user) if lettore else None
	if clinici is not None:
		clinici = (tabella.clinical == 1) & clinici
		altri = clinici if altri is None else (altri | clinici)
	if altri is None:
		return proprio
	return proprio | ((tabella.status != BOZZA) & altri)


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return livelli.puo("piani.scrivi", user)
	if ptype in ("write", "delete"):
		# a draft is its author's; what is published is replaced or closed
		return doc.get("practitioner") == user and doc.get("status") == BOZZA
	if ptype in ("submit", "cancel", "amend"):
		return False
	return puo_leggere(doc, user)


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	return condizione(frappe.qb.DocType(PIANO), user).get_sql(
		with_namespace=True, quote_char="`", secondary_quote_char="'"
	)


def tipi_accesi() -> list[R.TipoPiano]:
	"""The kinds of plan switched on here: the CRM's, and a module's where it is on."""
	livelli.carica()
	moduli = livelli.moduli_attivi()
	return [
		tipo
		for tipo in R.tipi()
		if not tipo.modulo or livelli.stato_modulo(tipo.modulo, moduli) != livelli.SPENTO
	]


def tipi_consentiti(user: str | None = None) -> list[str]:
	"""The kinds of plan the session writes: none without `piani.scrivi`."""
	user = user or frappe.session.user
	if not livelli.puo("piani.scrivi", user):
		return []
	return R.tipi_per(qualifica_di(user), tipi_accesi())


def descrivi_tipo(chiave: str) -> dict:
	"""A kind as the screens use it: what it holds and what they offer for it."""
	tipo = R.tipo(chiave)
	if not tipo:
		return {"key": chiave, "items": [], "features": []}
	return {
		"key": tipo.chiave,
		"items": list(tipo.generi),
		"features": sorted(tipo.funzioni),
		"clinical": tipo.clinico,
	}


def _della_persona(lead: str) -> None:
	if not legge_i_piani():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _piano(name: str):
	doc = frappe.get_doc(PIANO, name)
	frappe.has_permission("CRM Lead", "read", doc=doc.lead, throw=True)
	if not puo_leggere(doc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc


def _mio_in_bozza(name: str):
	doc = _piano(name)
	if doc.practitioner != frappe.session.user:
		frappe.throw(_("A plan is changed by who wrote it"), frappe.PermissionError)
	if doc.status != BOZZA:
		frappe.throw(_("A published plan is not rewritten: make a new version"))
	return doc


def _aperto(doc) -> None:
	"""A plan with health data opened: in the access log, with the record's."""
	if cint(doc.get("clinical")):
		doc.add_viewed()


# ------------------------------------------------------------------ reading


def _andamento(piani: list[str], dal) -> dict[str, list]:
	"""The check-ins of these plans from ``dal``, by plan."""
	per_piano: dict[str, list] = {}
	if not piani:
		return per_piano
	for riga in frappe.get_all(
		REGISTRO,
		filters={"plan": ("in", piani), "log_date": (">=", dal)},
		fields=["plan", "item_key", "log_date", "outcome", "effort", "note"],
		order_by="log_date asc",
	):
		per_piano.setdefault(riga.plan, []).append(riga)
	return per_piano


def _riga(doc, andamento: list | None = None) -> dict:
	return {
		"name": doc.name,
		"title": doc.title,
		"plan_type": doc.plan_type,
		"status": doc.status,
		"starts_on": doc.starts_on,
		"ends_on": doc.ends_on,
		"practitioner": doc.practitioner,
		"practitioner_name": get_fullname(doc.practitioner),
		"published_on": doc.published_on,
		"closed_on": doc.closed_on,
		"replaces": doc.replaces,
		"replaced_by": doc.replaced_by,
		"mine": doc.practitioner == frappe.session.user,
		"items": len(doc.items),
		"clinical": cint(doc.get("clinical")),
		# how the last days went, counted: not a score
		"summary": R.riepilogo([r.outcome for r in andamento or []]),
	}


@frappe.whitelist()
def get_plans(lead: str) -> dict:
	"""The person's plans the session reads, newest first, with the kinds it writes."""
	_della_persona(lead)
	documenti = [
		doc
		for doc in (
			frappe.get_doc(PIANO, nome)
			for nome in frappe.get_all(PIANO, filters={"lead": lead}, pluck="name", order_by="creation desc")
		)
		if puo_leggere(doc)
	]
	# a programme's stage plans are read inside their programme
	documenti = [doc for doc in documenti if not doc.get("programme")]
	# "done this week": from Monday, as the person's week goes
	lunedi, _domenica = R.settimana(getdate())
	andamento = _andamento([d.name for d in documenti if d.status != BOZZA], lunedi)
	return {
		"plans": [_riga(doc, andamento.get(doc.name)) for doc in documenti],
		"kinds": [descrivi_tipo(tipo) for tipo in tipi_consentiti()],
	}


def dettagli(genere_voce: str, nomi: set[str]) -> dict[str, dict]:
	"""The entries of a kind's library, by name, as the pages read them."""
	del_genere = genere(genere_voce)
	if not nomi or not del_genere or not del_genere.dettagli:
		return {}
	return del_genere.dettagli(nomi)


def righe_del_piano(doc) -> tuple[list[dict], list[dict]]:
	"""The moments and the items of a plan, the items with what their library says
	of the entry they name: an exercise, a food."""
	momenti = [
		{
			"key": m.moment_key,
			"label": m.label,
			"day": m.day,
			"time": str(m.time) if m.time else None,
			"note": m.note,
		}
		for m in doc.moments
	]
	campi = R.campi_voce()
	per_genere: dict[str, dict[str, dict]] = {}
	for chiave, del_genere in _generi.items():
		if del_genere.campo:
			nomi = {
				v.get(del_genere.campo) for v in doc.items if v.kind == chiave and v.get(del_genere.campo)
			}
			per_genere[chiave] = dettagli(chiave, nomi)
	voci = []
	for voce in doc.items:
		riga = {"key": voce.item_key, "moment": voce.moment_key, **{c: voce.get(c) for c in campi}}
		del_genere = genere(voce.kind)
		if del_genere and del_genere.campo and del_genere.per_l_autore:
			dettaglio = per_genere.get(voce.kind, {}).get(voce.get(del_genere.campo))
			riga.update(del_genere.per_l_autore(riga, dettaglio))
		voci.append(riga)
	return momenti, voci


@frappe.whitelist()
def get_plan(name: str) -> dict:
	"""A plan to read or to go on writing, with how the last two weeks went. A plan
	with health data goes in the access log."""
	doc = _piano(name)
	_aperto(doc)
	momenti, voci = righe_del_piano(doc)
	dal = add_days(getdate(), -(GIORNI_ANDAMENTO - 1))
	del_tipo = descrivi_tipo(doc.plan_type)
	risposta = {
		**_riga(doc),
		"lead": doc.lead,
		"instructions": doc.instructions,
		"moments": momenti,
		"items": voci,
		# what the kind holds, as the editor offers it, and what its screens offer
		"item_kinds": del_tipo["items"],
		"features": del_tipo["features"],
		"logs": _andamento([doc.name], dal).get(doc.name, []),
		"days": [str(add_days(dal, giorno)) for giorno in range(GIORNI_ANDAMENTO)],
		"can_edit": doc.practitioner == frappe.session.user and doc.status == BOZZA,
		"can_close": doc.practitioner == frappe.session.user
		and doc.status == PUBBLICATO
		and not doc.get("programme"),
		# a stage's plan changes with its programme, not by a version of its own
		"can_version": doc.status != BOZZA
		and not doc.get("programme")
		and doc.plan_type in tipi_consentiti()
		and not doc.replaced_by
		and not frappe.db.exists(PIANO, {"replaces": doc.name, "status": BOZZA}),
		"programme": doc.get("programme"),
		"programme_title": frappe.db.get_value("CRM Programme", doc.programme, "title")
		if doc.get("programme")
		else None,
	}
	# what the kind keeps besides its rows, a module's: a menu's targets
	for estensione in _estensioni:
		risposta.update(estensione.legge(doc))
	return risposta


# ------------------------------------------------------------------ writing


def _chiave() -> str:
	return secrets.token_hex(4)


def _righe(dati: dict) -> tuple[list[dict], list[dict]]:
	"""The moments and items as sent, each with its key: kept if it had one, so the
	check-ins of an item stay with it."""
	momenti = []
	for momento in dati.get("moments") or []:
		momenti.append(
			{
				"key": (momento.get("key") or _chiave()),
				"label": (momento.get("label") or "").strip(),
				"day": momento.get("day") or R.OGNI_GIORNO,
				"time": momento.get("time") or None,
				"note": (momento.get("note") or "").strip() or None,
			}
		)
	campi = R.campi_voce()
	voci = []
	for voce in dati.get("items") or []:
		riga = {c: voce.get(c) for c in campi}
		riga["key"] = voce.get("key") or _chiave()
		riga["moment"] = voce.get("moment")
		# "every time" is no weekly count
		riga["times_per_week"] = cint(voce.get("times_per_week")) or None
		voci.append(riga)
	return momenti, voci


def _controlla(tipo: str, momenti: list[dict], voci: list[dict]) -> None:
	problemi = R.valida(tipo, momenti, voci)
	if problemi:
		frappe.throw(
			"<br>".join(dict.fromkeys(p.testo(_) for p in problemi)), title=_("The plan is not ready")
		)
	# what the items name is still in its library
	for chiave, del_genere in _generi.items():
		if not (del_genere.campo and del_genere.libreria):
			continue
		nomi = {v[del_genere.campo] for v in voci if v.get("kind") == chiave and v.get(del_genere.campo)}
		if not nomi:
			continue
		trovati = set(
			frappe.get_all(
				del_genere.libreria, filters={"name": ("in", list(nomi)), "enabled": 1}, pluck="name"
			)
		)
		if nomi - trovati:
			frappe.throw(_("Something in the plan is no longer in the library"))


def _voce_da_scrivere(voce: dict) -> dict:
	campi = R.campi_voce()
	riga = {
		"item_key": voce["key"],
		"moment_key": voce["moment"],
		**{c: voce.get(c) for c in campi},
		"times_per_week": cint(voce.get("times_per_week")) or None,
	}
	del_genere = genere(voce.get("kind"))
	# the numbers are numbers; what the person reads is text
	for campo, leggi in del_genere.numeri.items() if del_genere else ():
		riga[campo] = leggi(voce.get(campo)) or None
	return riga


def _scrivi(doc, dati: dict, momenti: list[dict], voci: list[dict]) -> None:
	doc.title = (dati.get("title") or "").strip() or _(doc.plan_type)
	doc.starts_on = dati.get("starts_on") or None
	doc.ends_on = dati.get("ends_on") or None
	if doc.starts_on and doc.ends_on and getdate(doc.ends_on) < getdate(doc.starts_on):
		frappe.throw(_("A plan ends after it starts"))
	doc.instructions = (dati.get("instructions") or "").strip() or None
	for estensione in _estensioni:
		estensione.scrive(doc, dati)
	doc.set(
		"moments",
		[
			{
				"moment_key": m["key"],
				"label": m["label"],
				"day": m["day"],
				"time": m["time"],
				"note": m["note"],
			}
			for m in momenti
		],
	)
	doc.set("items", [_voce_da_scrivere(v) for v in voci])


def sanitario(doc) -> bool:
	"""Whether a plan or a programme is health data by who wrote it, as the module
	that reads health data says: the clinic's health professionals."""
	lettore = _lettore.get("clinico")
	return bool(lettore and lettore.marca and lettore.marca(doc))


def marca(doc) -> None:
	"""The mark "health data" a plan carries: its kind's, or its author's."""
	tipo = R.tipo(doc.plan_type)
	doc.clinical = 1 if (tipo and tipo.clinico) or sanitario(doc) else 0


@frappe.whitelist(methods=["POST"])
def save_plan(lead: str, data: dict | str, name: str | None = None) -> dict:
	"""A draft of the session's own, new or carried on."""
	livelli.verifica("piani.scrivi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	if name:
		doc = _mio_in_bozza(name)
		if doc.lead != lead:
			frappe.throw(_("This plan belongs to somebody else"))
	else:
		doc = frappe.new_doc(PIANO)
		doc.lead = lead
		doc.practitioner = frappe.session.user
		doc.status = BOZZA
	tipo = dati.get("plan_type") or doc.plan_type
	if tipo not in tipi_consentiti():
		frappe.throw(_("Your qualification does not write a plan of this kind"), frappe.PermissionError)
	doc.plan_type = tipo
	doc.discipline = qualifica_di(frappe.session.user)
	marca(doc)
	momenti, voci = _righe(dati)
	_controlla(tipo, momenti, voci)
	_scrivi(doc, dati, momenti, voci)
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	return get_plan(doc.name)


@frappe.whitelist(methods=["POST"])
def publish_plan(name: str) -> dict:
	"""The draft goes to the person's area. It closes the plan it replaces, and the
	person's other plan of the same kind: one at a time."""
	doc = _mio_in_bozza(name)
	if doc.get("programme"):
		frappe.throw(_("A stage's plan is published when its stage opens"))
	if doc.plan_type not in tipi_consentiti():
		frappe.throw(_("Your qualification does not write a plan of this kind"), frappe.PermissionError)
	pubblica(doc)
	avvisa(doc.lead)
	return get_plan(doc.name)


def pubblica(doc, dal=None, al=None) -> None:
	"""A draft followed from now: checked, published, and the person's other plan of
	the same kind closed. A programme's stage publishes its plan this way, for its
	days."""
	momenti, voci = righe_del_piano(doc)
	if not voci:
		frappe.throw(_("A plan to follow has something in it"))
	_controlla(doc.plan_type, momenti, voci)
	adesso = now_datetime()
	for vecchio in frappe.get_all(
		PIANO,
		filters={
			"lead": doc.lead,
			"plan_type": doc.plan_type,
			"status": PUBBLICATO,
			"name": ("!=", doc.name),
		},
		pluck="name",
	):
		_chiudi(frappe.get_doc(PIANO, vecchio), adesso, sostituito_da=doc.name)
	doc.flags.dal_piano = True
	doc.status = PUBBLICATO
	doc.published_on = adesso
	if dal:
		doc.starts_on = dal
	if al:
		doc.ends_on = al
	doc.save(ignore_permissions=True)


def _chiudi(doc, adesso, sostituito_da: str | None = None) -> None:
	doc.flags.dal_piano = True
	doc.status = CHIUSO
	doc.closed_on = adesso
	if sostituito_da:
		doc.replaced_by = sostituito_da
	doc.save(ignore_permissions=True)


def avvisa(lead: str) -> None:
	"""News in the person's area: the email says only that there is some."""
	from crm.area import messaggi

	messaggi._avvisa(lead)


@frappe.whitelist(methods=["POST"])
def close_plan(name: str) -> dict:
	"""No longer to follow: it leaves the area and stays with the person."""
	doc = _piano(name)
	if doc.practitioner != frappe.session.user:
		frappe.throw(_("A plan is closed by who wrote it"), frappe.PermissionError)
	if doc.status != PUBBLICATO:
		frappe.throw(_("Only a published plan is closed"))
	if doc.get("programme"):
		frappe.throw(_("A stage's plan is closed when its stage is finished"))
	_chiudi(doc, now_datetime())
	return get_plan(doc.name)


@frappe.whitelist(methods=["POST"])
def new_version(name: str) -> dict:
	"""A draft copy of a published or closed plan, to change and publish in its place."""
	vecchio = _piano(name)
	if vecchio.status == BOZZA:
		frappe.throw(_("A draft is changed as it is"))
	if vecchio.get("programme"):
		frappe.throw(_("A stage's plan changes with its programme"))
	if vecchio.plan_type not in tipi_consentiti():
		frappe.throw(_("Your qualification does not write a plan of this kind"), frappe.PermissionError)
	gia = frappe.db.get_value(PIANO, {"replaces": vecchio.name, "status": BOZZA}, "name")
	if gia:
		frappe.throw(_("A new version of this plan is already being written"))
	nuovo = frappe.new_doc(PIANO)
	nuovo.update(
		{
			"lead": vecchio.lead,
			"plan_type": vecchio.plan_type,
			"title": vecchio.title,
			"status": BOZZA,
			"practitioner": frappe.session.user,
			"discipline": qualifica_di(frappe.session.user),
			"starts_on": None,
			"ends_on": vecchio.ends_on,
			"instructions": vecchio.instructions,
			"replaces": vecchio.name,
		}
	)
	marca(nuovo)
	for estensione in _estensioni:
		for campo in estensione.copia:
			nuovo.set(campo, vecchio.get(campo))
	campi = R.campi_voce()
	for momento in vecchio.moments:
		nuovo.append("moments", {c: momento.get(c) for c in ("moment_key", "label", "day", "time", "note")})
	for voce in vecchio.items:
		nuovo.append(
			"items",
			{"item_key": voce.item_key, "moment_key": voce.moment_key, **{c: voce.get(c) for c in campi}},
		)
	nuovo.insert(ignore_permissions=True)
	return get_plan(nuovo.name)


@frappe.whitelist(methods=["POST"])
def delete_draft(name: str) -> None:
	"""A draft is thrown away by who wrote it; a published plan never. A stage's plan
	thrown away leaves its stage without one."""
	doc = _mio_in_bozza(name)
	programma = doc.get("programme")
	if programma:
		frappe.db.set_value(
			"CRM Programme Stage",
			{"parent": programma, "plan": doc.name},
			"plan",
			None,
			update_modified=False,
		)
	frappe.delete_doc(PIANO, doc.name, ignore_permissions=True)
	if programma:
		# the programme's mark follows the plans its stages still have
		from crm.piani import programmi

		del_programma = frappe.get_doc(programmi.PROGRAMMA, programma)
		programmi.marca(del_programma)
		frappe.db.set_value(
			programmi.PROGRAMMA, programma, "clinical", del_programma.clinical, update_modified=False
		)


# ------------------------------------------------------------------ the CRM's own kinds of item


def _esercizi(nomi: set[str]) -> dict[str, dict]:
	"""The exercises of a plan, with their pictures: the centre's own, or the
	library's from where the agency hosts them (`librerie.media`)."""
	from crm.piani.librerie import media

	return {
		riga.name: frappe._dict({**riga, **media(riga)})
		for riga in frappe.get_all(
			ESERCIZIO,
			filters={"name": ("in", list(nomi))},
			fields=[
				"name",
				"exercise_name",
				"body_part",
				"equipment",
				"image",
				"video_url",
				"instructions",
				"attribution",
				"source",
				"media_path",
				"animation_path",
			],
		)
	}


def _esercizio_per_l_autore(voce: dict, esercizio: dict | None) -> dict:
	if not esercizio:
		return {}
	return {"exercise_name": esercizio.exercise_name, "exercise_detail": esercizio}


def _immagine(url: str | None) -> str | None:
	"""A picture the area can show: a public file of the site, or an address."""
	if url and (url.startswith("/files/") or url.startswith("https://")):
		return url
	return None


def figura(esercizio: dict) -> tuple[str | None, str | None]:
	"""What the person sees of an exercise, and whose it is: the centre's own
	picture; else the library's animation or picture, with the name of their
	owner; the author of a centre's exercise always."""
	from crm.piani.dataset import DATASET

	propria = _immagine(esercizio.get("image"))
	della_libreria = esercizio.get("animation") or (
		None if esercizio.get("image") else esercizio.get("picture")
	)
	dal_dataset = esercizio.get("source") == DATASET
	if propria or not della_libreria:
		return propria, None if dal_dataset else esercizio.get("attribution")
	return della_libreria, esercizio.get("attribution")


def _esercizio_per_la_persona(voce: dict, piano, contesto: dict) -> dict:
	esercizio = voce.get("exercise_detail") or {}
	immagine, autore = figura(esercizio)
	return {
		"exercise_name": voce.get("exercise_name"),
		"sets": voce.get("sets"),
		"reps": voce.get("reps"),
		"duration": voce.get("duration"),
		"rest": voce.get("rest"),
		"load": voce.get("load"),
		"instructions": esercizio.get("instructions"),
		"image": immagine,
		"video_url": esercizio.get("video_url"),
		"attribution": autore,
	}


def _abitudine_per_la_persona(voce: dict, piano, contesto: dict) -> dict:
	return {"text": voce.get("text")}


registra_genere(
	Genere(
		R.ESERCIZIO,
		campo="exercise",
		libreria=ESERCIZIO,
		dettagli=_esercizi,
		per_l_autore=_esercizio_per_l_autore,
		per_la_persona=_esercizio_per_la_persona,
		numeri={"sets": cint},
	)
)
registra_genere(Genere(R.ABITUDINE, per_la_persona=_abitudine_per_la_persona))


# ------------------------------------------------------------------ the exercises' library


def _cerca(doctype: str, campo: str, testo: str | None, filtri: dict, campi: list[str]) -> list[dict]:
	filtri = {"enabled": 1, **{k: v for k, v in filtri.items() if v}}
	parole = (testo or "").strip()
	if parole:
		filtri[campo] = ("like", f"%{parole}%")
	return frappe.get_all(doctype, filters=filtri, fields=campi, order_by=f"{campo} asc", limit=30)


def cerca(doctype: str, campo: str, testo: str | None, filtri: dict, campi: list[str]) -> list[dict]:
	"""A library's entries whose name has these words, for whoever writes plans."""
	livelli.verifica("piani.scrivi")
	return _cerca(doctype, campo, testo, filtri, campi)


@frappe.whitelist()
def search_exercises(text: str | None = None, body_part: str | None = None) -> list[dict]:
	return cerca(
		ESERCIZIO,
		"exercise_name",
		text,
		{"body_part": body_part},
		["name", "exercise_name", "body_part", "equipment", "image", "video_url"],
	)


@frappe.whitelist(methods=["POST"])
def add_exercise(
	exercise_name: str,
	body_part: str | None = None,
	instructions: str | None = None,
	video_url: str | None = None,
) -> dict:
	"""An exercise of the centre: how it is done, and a video of the centre's if any."""
	livelli.verifica("piani.scrivi")
	doc = frappe.get_doc(
		{
			"doctype": ESERCIZIO,
			"exercise_name": (exercise_name or "").strip(),
			"body_part": body_part or None,
			"instructions": instructions,
			"video_url": (video_url or "").strip() or None,
		}
	).insert(ignore_permissions=True)
	return {
		"name": doc.name,
		"exercise_name": doc.exercise_name,
		"body_part": doc.body_part,
		"video_url": doc.video_url,
	}
