# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo data's parts, and the register of every record they make.

A part is what one module shows a centre that opens DottorCloud on demo data:
the base (the team, the agenda, the people and their deals), and whatever each
module adds (invoices, forms, the client area, the clinic). A module registers its
part from its own `registra()`, as it registers its capabilities; the parts of the
modules the plan has on are made, each after the ones it needs (`dopo`).

Every record made while a part runs is written down in `CRM Demo Record`, the
ones the controllers make on their own as well: a person's contact and company,
assignments, notifications, comments, versions. Taking the demo away starts from
this register (`crm.demo.togli`), and the guards that keep anything from reaching a
demo person read it (`crm.demo.guardie`).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import frappe

REGISTRO = "CRM Demo Record"

#: "1" while the demo data are in: the boot and the sidebar read it, as before.
STATO = "crm_demo_data_created"
#: The parts made whole, as a JSON list: a part that failed half-way is not one.
FATTE = "crm_demo_data_parts"
#: While a job makes them: when it started, so a job that died is not waited for.
LAVORO = "crm_demo_data_job"
#: The name counters as they were before the demo first came: what it takes away
#: goes back to them.
SERIE = "crm_demo_data_series"
#: When the demo first came, on the site's clock: nothing older is a trace of it.
INIZIO = "crm_demo_data_since"

#: Never written down: the register itself.
NON_ANNOTARE = frozenset({REGISTRO})


@dataclass(frozen=True)
class Parte:
	"""One module's share of the demo data."""

	chiave: str
	#: In English, translated where it is shown.
	etichetta: str
	#: ``crea(ctx)``: makes the records, through the same code paths as the screens.
	crea: Callable
	#: The plan module that must be on (or in trial) for the part to be made.
	modulo: str = "base"
	#: The parts it builds on, made first when they are made at all.
	dopo: tuple[str, ...] = ()
	#: One line on what it adds, in English.
	descrizione: str = ""
	#: The parts that take what it makes, made after it: a module registered later
	#: that gives an earlier one something to use - the dentist's visits, invoiced.
	prima: tuple[str, ...] = ()


_parti: dict[str, Parte] = {}


def registra_parte(parte: Parte) -> None:
	_parti[parte.chiave] = parte


def tutte_le_parti() -> list[Parte]:
	from crm.registrazione import carica

	carica()
	return in_ordine(list(_parti.values()))


def accesa(parte: Parte) -> bool:
	"""Whether the plan has the part's module on, or in trial."""
	from crm.permissions import livelli

	stato = livelli.stato_modulo(parte.modulo, livelli.moduli_attivi())
	return stato in (livelli.ATTIVO, livelli.PROVA)


def in_ordine(parti: list[Parte]) -> list[Parte]:
	"""The parts in the order they are made: each after those it needs, the others
	in the order they were registered. Pure."""
	per_chiave = {parte.chiave: parte for parte in parti}
	ordine: list[Parte] = []
	visti: set[str] = set()
	# what comes after a part says so in its `dopo`, or the part in its `prima`
	dopo = {parte.chiave: list(parte.dopo) for parte in parti}
	for parte in parti:
		for seguente in parte.prima:
			if seguente in dopo and parte.chiave not in dopo[seguente]:
				dopo[seguente].append(parte.chiave)

	def visita(parte: Parte, catena: tuple[str, ...]) -> None:
		if parte.chiave in visti:
			return
		if parte.chiave in catena:
			raise ValueError(f"demo parts depend on each other: {' -> '.join((*catena, parte.chiave))}")
		for prima in dopo[parte.chiave]:
			if prima in per_chiave:
				visita(per_chiave[prima], (*catena, parte.chiave))
		visti.add(parte.chiave)
		ordine.append(parte)

	for parte in parti:
		visita(parte, ())
	return ordine


def da_fare() -> list[Parte]:
	"""The parts to make now: those of the modules that are on, not made yet."""
	fatte = parti_fatte()
	return [p for p in tutte_le_parti() if accesa(p) and p.chiave not in fatte]


# -- what a part made, while it runs ---------------------------------------------------


@dataclass
class Raccolta:
	"""The records one part made, in the order they were made."""

	parte: str
	creati: list[tuple[str, str]] = field(default_factory=list)
	#: (doctype, name) -> the key a later part finds it by
	chiavi: dict[tuple[str, str], str] = field(default_factory=dict)
	#: the browser's channel as it was before the part muted it: the progress
	pubblica: Callable | None = None
	#: what is already in the register, so that writing it down as the part goes
	#: never writes a record twice
	scritti: set[tuple[str, str]] = field(default_factory=set)
	chiavi_scritte: set[tuple[str, str, str]] = field(default_factory=set)
	#: the emails the part's paths would have sent, kept here instead: a demo person
	#: reads the link or the code in theirs, as somebody would in their mailbox
	posta: list[dict] = field(default_factory=list)


def posta_per(indirizzo: str) -> list[dict]:
	"""What the part being made would have sent to ``indirizzo``, the latest last."""
	corrente = raccolta()
	if corrente is None:
		return []
	return [email for email in corrente.posta if indirizzo in email["recipients"]]


def raccolta() -> Raccolta | None:
	"""The part being made in this request or job, if any."""
	return getattr(frappe.local, "dati_di_prova", None)


def annota(doc, method=None) -> None:
	"""`after_insert` of every doctype: while the demo is made, the record is the
	demo's. Anything else returns at once."""
	corrente = raccolta()
	if corrente is None or doc.doctype in NON_ANNOTARE:
		return
	corrente.creati.append((doc.doctype, str(doc.name)))


def annota_a_mano(doctype: str, name: str, chiave: str | None = None) -> None:
	"""A record written without the ORM's hooks (`db_insert`): the demo's too."""
	corrente = raccolta()
	if corrente is None:
		return
	corrente.creati.append((doctype, str(name)))
	if chiave:
		corrente.chiavi[(doctype, str(name))] = chiave


@contextmanager
def fuori_dal_registro() -> Iterator[None]:
	"""What is made here is the product's, not the demo's: it stays when the demo is
	taken away (the new clients pipeline, made as the product makes it)."""
	corrente = raccolta()
	frappe.local.dati_di_prova = None
	try:
		yield
	finally:
		frappe.local.dati_di_prova = corrente


def ricorda(doctype: str, name: str, chiave: str) -> None:
	"""A later part will look for this record by ``chiave``."""
	corrente = raccolta()
	if corrente is not None:
		corrente.chiavi[(doctype, str(name))] = chiave


def scrivi(corrente: Raccolta, esistenti_soltanto: bool = False) -> int:
	"""Write down what a part made so far, once each, a thousand rows a statement.
	Called as the part goes, before each commit: nothing it committed is left out of
	the register, whatever happens next.

	``esistenti_soltanto``: after a part failed and its work was rolled back, only
	what is still there - what was committed before - is the demo's."""
	if not corrente.scritti:
		corrente.scritti = {
			(r.ref_doctype, r.ref_name) for r in frappe.get_all(REGISTRO, fields=["ref_doctype", "ref_name"])
		}
	gia = corrente.scritti
	righe = []
	for doctype, name in corrente.creati:
		if not name or (doctype, name) in gia:
			continue
		if esistenti_soltanto and not frappe.db.exists(doctype, name):
			continue
		gia.add((doctype, name))
		righe.append(
			(
				frappe.generate_hash(length=14),
				doctype,
				name,
				corrente.parte,
				corrente.chiavi.get((doctype, name)),
			)
		)
	# a key given after its record was written down already
	for (doctype, name), chiave in corrente.chiavi.items():
		if (doctype, name) in gia and (doctype, name, chiave) not in corrente.chiavi_scritte:
			if not any(riga[1] == doctype and riga[2] == name for riga in righe):
				frappe.db.set_value(REGISTRO, {"ref_doctype": doctype, "ref_name": name}, "chiave", chiave)
		corrente.chiavi_scritte.add((doctype, name, chiave))
	adesso = frappe.utils.now_datetime()
	utente = frappe.session.user
	for inizio in range(0, len(righe), 1000):
		frappe.db.bulk_insert(
			REGISTRO,
			fields=[
				"name",
				"ref_doctype",
				"ref_name",
				"parte",
				"chiave",
				"creation",
				"modified",
				"owner",
				"modified_by",
			],
			values=[(*riga, adesso, adesso, utente, utente) for riga in righe[inizio : inizio + 1000]],
		)
	return len(righe)


# -- reading the register ----------------------------------------------------------------


def registrati() -> dict[str, set[str]]:
	"""Doctype -> the names of its records that are the demo's."""
	per_doctype: dict[str, set[str]] = {}
	for riga in frappe.get_all(REGISTRO, fields=["ref_doctype", "ref_name"]):
		per_doctype.setdefault(riga.ref_doctype, set()).add(riga.ref_name)
	return per_doctype


def trova(chiave: str) -> str | None:
	"""The name of the record a part wrote down with ``chiave``."""
	corrente = raccolta()
	if corrente is not None:
		for (_doctype, name), sua in corrente.chiavi.items():
			if sua == chiave:
				return name
	return frappe.db.get_value(REGISTRO, {"chiave": chiave}, "ref_name")


def con_chiave(prefisso: str) -> dict[str, str]:
	"""Every key starting with ``prefisso`` -> its record's name."""
	trovati = {
		riga.chiave: riga.ref_name
		for riga in frappe.get_all(
			REGISTRO, filters={"chiave": ["like", f"{prefisso}%"]}, fields=["chiave", "ref_name"]
		)
	}
	corrente = raccolta()
	if corrente is not None:
		trovati.update(
			{chiave: name for (_d, name), chiave in corrente.chiavi.items() if chiave.startswith(prefisso)}
		)
	return trovati


def di_prova(doctype: str, name: str | None) -> bool:
	"""Whether a record is the demo's."""
	if not name:
		return False
	corrente = raccolta()
	if corrente is not None:
		# while a part runs, whatever it makes is the demo's, written down or not yet
		return True
	if not caricati():
		return False
	return bool(frappe.db.exists(REGISTRO, {"ref_doctype": doctype, "ref_name": name}))


def nomi_di_prova(doctype: str) -> set[str]:
	"""The names of ``doctype``'s records that are the demo's, once per request."""
	if not caricati():
		return set()
	cache = getattr(frappe.local, "crm_demo_nomi", None)
	if cache is None:
		cache = frappe.local.crm_demo_nomi = {}
	if doctype not in cache:
		cache[doctype] = set(frappe.get_all(REGISTRO, filters={"ref_doctype": doctype}, pluck="ref_name"))
	return cache[doctype]


def parti_fatte() -> set[str]:
	return set(frappe.parse_json(frappe.db.get_default(FATTE) or "[]") or [])


def segna_fatta(chiave: str) -> None:
	fatte = parti_fatte() | {chiave}
	frappe.db.set_default(FATTE, frappe.as_json(sorted(fatte)))


def caricati() -> bool:
	"""Whether the demo data are in."""
	return frappe.db.get_default(STATO) == "1"


def segna_l_inizio() -> None:
	"""The demo comes now, unless some of it is in already."""
	if frappe.db.get_default(INIZIO) is None or not frappe.db.count(REGISTRO):
		frappe.db.set_default(INIZIO, frappe.utils.now())


def cominciata() -> datetime | None:
	"""When the demo first came. The framework gives the name of the last record
	deleted again: a demo record may carry the name of one the centre threw in the
	bin before, and what is older than the demo is never its trace. A register
	written before this was kept starts an hour before its first row."""
	quando = frappe.db.get_default(INIZIO)
	if quando:
		return frappe.utils.get_datetime(quando)
	prima = frappe.get_all(REGISTRO, fields=["creation"], order_by="creation asc", limit=1)
	return prima[0].creation - timedelta(hours=1) if prima else None
