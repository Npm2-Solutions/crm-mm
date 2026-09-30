# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who may do what: levels, capabilities, and the centre's plan.

The CRM used to fold three different things into one (doc 30). They are kept apart
here:

- the **level** (*livello*) is what the CRM shows and assigns to a person: Front
  Desk, Practitioner, Manager, and a few optional ones. In Frappe it is a Role
  Profile, and a person may hold more than one - the owner who also sees patients is
  Manager and Practitioner;
- the **role** is Frappe's brick for document permissions. Every module brings its
  own few, and the CRM never shows them;
- the **capability** (*capacità*) is a thing one can do, with a name -
  ``fatture.emetti``, ``agenda.turni``. The code checks capabilities, never roles,
  and the frontend receives them from the server.

A capability also has a **scope** (*ambito*): on which records it holds - the whole
centre, the team, or one's own.

And a second key: the **plan**. A capability holds when the person's level grants it
*and* the module it belongs to is active in the centre's plan. A module that was
switched off keeps its data readable: only what writes goes away.

Every module contributes its roles, its capabilities and the levels they go to, by
calling the ``registra_*`` functions when it loads - the way invoicing takes its
extensions in ``crm/invoicing/estensioni.py``. This file only puts them together.

The computation (`calcola`) is pure, so the whole matrix is provable with
``unittest`` and no site. What needs Frappe - reading a user's profiles, the plan,
syncing Role Profiles - sits at the bottom, behind small functions.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps

# ---------------------------------------------------------------------------
# Scopes. On which records a capability holds, widest first.

CENTRO = "centro"
"""The whole centre."""
TEAM = "team"
"""One's own records and those of one's team in the hierarchy."""
SUOI = "suoi"
"""One's own: assigned to them, their appointments, their clients or patients."""
MASCHERATO = "mascherato"
"""Every record, with tax code, phone and email masked."""
LIBERO_OCCUPATO = "libero_occupato"
"""The agenda as free and busy slots, without who or what."""
A_SCELTA = "a_scelta"
"""Off by default: the Manager turns it on for that person."""

#: How wide each scope is, to pick one when a person holds several levels.
#: The owner who is Manager and Practitioner sees the whole centre, not their own.
_AMPIEZZA = {CENTRO: 5, TEAM: 4, SUOI: 3, MASCHERATO: 2, LIBERO_OCCUPATO: 1}

# Plan module states.
ATTIVO = "attivo"
PROVA = "prova"
SOLA_LETTURA = "sola_lettura"
SPENTO = "spento"

#: The level that takes every write away from the levels it is added to.
SOLA_LETTURA_LIVELLO = "sola_lettura"

#: The role that shows people's email and phone numbers in full. Frappe masks the
#: fields marked `mask` for whoever lacks the "mask" permission, and this role has
#: it: every level carries it but those that work on masked data (Marketing).
RUOLO_RECAPITI = "Contact Details"

#: Roles that stay the agency's: whoever has them manages the site, not the centre.
RUOLI_AGENZIA = frozenset({"System Manager"})

#: Roles Frappe gives by itself and never stores on a user (`AUTOMATIC_ROLES`).
RUOLI_AUTOMATICI = frozenset({"All", "Guest", "Desk User", "Administrator"})


@dataclass(frozen=True)
class ModuloPiano:
	"""A part of the product the centre buys: Base, Clinic, Marketing, Phone…"""

	chiave: str
	etichetta: str
	#: Whether a site whose plan says nothing about it has it. True for what the CRM
	#: already did before plans existed, so no existing site loses anything.
	predefinito: bool = True
	descrizione: str = ""
	ordine: int = 0
	#: The modules it comprises: on with it, whatever the plan says of them. The
	#: clinic comprises the client area.
	comprende: tuple[str, ...] = ()


@dataclass(frozen=True)
class Livello:
	chiave: str
	#: The Role Profile that carries it. Prefixed, so the CRM only ever rewrites
	#: profiles it owns.
	profilo: str
	etichetta: str
	descrizione: str = ""
	#: Base levels are offered everywhere; the others only when someone needs them.
	base: bool = True
	#: The plan module the level belongs to: Medical Director comes with the clinic.
	piano: str = "base"
	ordine: int = 0
	#: Whether it keeps the Desk's other modules. Front desk and practitioners work in
	#: the CRM, and see only its modules there, as Sales Users always did.
	desk: bool = False
	#: Whether it sees people's email and phone numbers in full (`RUOLO_RECAPITI`).
	#: Marketing works on masked data (doc 30).
	recapiti: bool = True
	#: Added to another level, never alone: Read only takes writes away and gives
	#: nothing of its own.
	aggiuntivo: bool = False


@dataclass(frozen=True)
class Capacita:
	nome: str
	piano: str = "base"
	#: Whether it changes something. A read-only level, or a module switched off,
	#: keeps only the capabilities that do not.
	scrive: bool = True
	#: Technical: keys, webhooks, raw logs, code. The agency's, never a level's.
	agenzia: bool = False
	#: Clinical data. The agency does not get it for being the agency.
	clinica: bool = False
	descrizione: str = ""
	#: Something the site must have for the capability to mean anything: the site
	#: pages need Frappe Builder. Checked by the function registered under this key.
	requisito: str | None = None


@dataclass
class _Registro:
	moduli: dict[str, ModuloPiano] = field(default_factory=dict)
	livelli: dict[str, Livello] = field(default_factory=dict)
	capacita: dict[str, Capacita] = field(default_factory=dict)
	#: capability -> level -> scope
	concessioni: dict[str, dict[str, str]] = field(default_factory=dict)
	#: level -> roles, from every module
	ruoli_livello: dict[str, set[str]] = field(default_factory=dict)
	#: role -> description, for the roles modules bring
	ruoli: dict[str, str] = field(default_factory=dict)
	#: roles that open the CRM at all, from every module
	ruoli_accesso: set[str] = field(default_factory=set)
	#: roles Frappe itself creates (System Manager, and the ones CRM doctypes name)
	ruoli_esistenti: set[str] = field(default_factory=set)
	#: role -> level it stands for, for users that predate levels
	livelli_impliciti: list[tuple[str, str]] = field(default_factory=list)
	#: requirement -> function that says whether this site meets it
	requisiti: dict[str, Callable[[], bool]] = field(default_factory=dict)

	def copia(self) -> _Registro:
		return _Registro(
			moduli=dict(self.moduli),
			livelli=dict(self.livelli),
			capacita=dict(self.capacita),
			concessioni={k: dict(v) for k, v in self.concessioni.items()},
			ruoli_livello={k: set(v) for k, v in self.ruoli_livello.items()},
			ruoli=dict(self.ruoli),
			ruoli_accesso=set(self.ruoli_accesso),
			ruoli_esistenti=set(self.ruoli_esistenti),
			livelli_impliciti=list(self.livelli_impliciti),
			requisiti=dict(self.requisiti),
		)


#: Process-wide, filled once when the app loads, like invoicing's extensions.
_r = _Registro()


# ---------------------------------------------------------------------------
# Registration. Called by each module when it loads; every call is idempotent.


def registra_modulo_piano(modulo: ModuloPiano) -> None:
	_r.moduli[modulo.chiave] = modulo


def registra_livello(livello: Livello, ruoli: Iterable[str] = ()) -> None:
	_r.livelli[livello.chiave] = livello
	aggiungi_ruoli(livello.chiave, ruoli)


def registra_ruolo(
	nome: str,
	descrizione: str = "",
	livelli: Iterable[str] = (),
	accesso: bool = True,
	di_frappe: bool = False,
) -> None:
	"""A role a module brings, and the levels it goes to by default.

	``accesso`` says whether holding it is enough to open the CRM. ``di_frappe``
	marks a role Frappe creates by itself - System Manager, or one the doctypes
	name - which the CRM must not create as a custom role of its own.
	"""
	_r.ruoli[nome] = descrizione or _r.ruoli.get(nome, "")
	if accesso:
		_r.ruoli_accesso.add(nome)
	if di_frappe:
		_r.ruoli_esistenti.add(nome)
	for livello in livelli:
		aggiungi_ruoli(livello, [nome])


def aggiungi_ruoli(livello: str, ruoli: Iterable[str]) -> None:
	_r.ruoli_livello.setdefault(livello, set()).update(ruoli)


def registra_capacita(capacita: Capacita, livelli: Mapping[str, str] | None = None) -> None:
	_r.capacita[capacita.nome] = capacita
	concedi(capacita.nome, livelli or {})


def concedi(nome: str, livelli: Mapping[str, str]) -> None:
	"""Give a capability to levels, with the scope each one gets.

	Separate from `registra_capacita` because the module that brings a level is not
	always the one that brings the capability: the clinic's Medical Director sees
	the whole agenda, which is the CRM's.
	"""
	_r.concessioni.setdefault(nome, {}).update(livelli)


def registra_livello_implicito(ruolo: str, livello: str) -> None:
	"""A user from before levels who holds ``ruolo`` counts as holding ``livello``.

	In the order given: the first role that matches wins, so the widest goes first.
	"""
	if (ruolo, livello) not in _r.livelli_impliciti:
		_r.livelli_impliciti.append((ruolo, livello))


def registra_requisito(chiave: str, funzione: Callable[[], bool]) -> None:
	"""How to tell whether this site meets ``chiave``, for the capabilities that need it."""
	_r.requisiti[chiave] = funzione


@contextmanager
def registro_isolato(vuoto: bool = True):
	"""A registry for the length of a block, and the real one put back exactly.

	The registry is process-wide. A test that empties it and leaves it empty breaks
	every test that runs after it in the same process - the lesson invoicing's
	`senza_estensioni` records.
	"""
	global _r
	salvato = _r
	_r = _Registro() if vuoto else salvato.copia()
	try:
		yield _r
	finally:
		_r = salvato


# ---------------------------------------------------------------------------
# Reading the registry.


def livelli() -> list[Livello]:
	return sorted(_r.livelli.values(), key=lambda livello: (livello.ordine, livello.chiave))


def livello(chiave: str) -> Livello | None:
	return _r.livelli.get(chiave)


def livello_del_profilo(profilo: str) -> Livello | None:
	return next((lv for lv in _r.livelli.values() if lv.profilo == profilo), None)


def ruoli_del_livello(chiave: str) -> frozenset[str]:
	ruoli = set(_r.ruoli_livello.get(chiave, ()))
	registrato = _r.livelli.get(chiave)
	if registrato and registrato.recapiti and not registrato.aggiuntivo:
		ruoli.add(RUOLO_RECAPITI)
	return frozenset(ruoli)


def ruoli_registrati() -> dict[str, str]:
	return dict(_r.ruoli)


def ruoli_da_creare() -> dict[str, str]:
	"""The registered roles the CRM creates itself: all but Frappe's own."""
	return {nome: descrizione for nome, descrizione in _r.ruoli.items() if nome not in _r.ruoli_esistenti}


def ruoli_di_accesso() -> frozenset[str]:
	"""Every role that opens the CRM, from every module that registered one."""
	return frozenset(_r.ruoli_accesso)


def moduli_piano() -> list[ModuloPiano]:
	return sorted(_r.moduli.values(), key=lambda m: (m.ordine, m.chiave))


def capacita_registrate() -> dict[str, Capacita]:
	return dict(_r.capacita)


def concessioni(nome: str) -> dict[str, str]:
	return dict(_r.concessioni.get(nome, {}))


def a_scelta_dei_livelli(chiavi: Iterable[str]) -> list[str]:
	"""The optional capabilities these levels offer: what the Manager may turn on."""
	chiavi = set(chiavi)
	return sorted(
		nome
		for nome, livelli_concessi in _r.concessioni.items()
		if nome in _r.capacita and any(livelli_concessi.get(chiave) == A_SCELTA for chiave in chiavi)
	)


def nel_crm(user: str | None = None) -> bool:
	"""Whether ``user`` works in the CRM through levels, their own or implied, or is the
	agency. Someone outside - an accountant with an invoicing role, on the Desk - keeps
	the rules of before: their roles' document permissions."""
	frappe = _frappe()
	user = user or frappe.session.user
	return e_agenzia(user) or bool(livelli_di(user))


def verifica_nel_crm(nome: str, user: str | None = None, messaggio: str | None = None) -> None:
	"""`verifica`, for whoever works in the CRM through levels; the others pass."""
	if nel_crm(user):
		verifica(nome, user, messaggio)


def livelli_impliciti(ruoli: Iterable[str]) -> list[str]:
	"""The levels a user from before levels stands for, from their roles."""
	ruoli = set(ruoli)
	trovati: list[str] = []
	for ruolo, chiave in _r.livelli_impliciti:
		if ruolo in ruoli and chiave not in trovati:
			trovati.append(chiave)
	return trovati


# ---------------------------------------------------------------------------
# The computation. Pure: everything it needs comes in as arguments.


def piu_ampio(a: str | None, b: str | None) -> str | None:
	"""The wider of two scopes; either may be missing."""
	if a is None:
		return b
	if b is None:
		return a
	return a if _AMPIEZZA.get(a, 0) >= _AMPIEZZA.get(b, 0) else b


#: From the most to the least: a module comprised by two takes the better state.
_ORDINE_STATI = (ATTIVO, PROVA, SOLA_LETTURA, SPENTO)


def _stato_proprio(chiave: str, moduli: Mapping[str, str] | None) -> str:
	if moduli and chiave in moduli:
		return moduli[chiave]
	modulo = _r.moduli.get(chiave)
	if modulo is None:
		# a capability of a module nobody declared: not something a plan can sell
		return ATTIVO
	return ATTIVO if modulo.predefinito else SPENTO


def _migliore(a: str, b: str) -> str:
	indice = {stato: i for i, stato in enumerate(_ORDINE_STATI)}
	return a if indice.get(a, len(indice)) <= indice.get(b, len(indice)) else b


def stato_modulo(chiave: str, moduli: Mapping[str, str] | None) -> str:
	"""A module's state: what the plan says, or its default when the plan is silent;
	and at least that of a module comprising it, as the clinic does the client area."""
	stato = _stato_proprio(chiave, moduli)
	for modulo in _r.moduli.values():
		if chiave in modulo.comprende and modulo.chiave != chiave:
			stato = _migliore(stato, _stato_proprio(modulo.chiave, moduli))
	return stato


def calcola(
	livelli_utente: Iterable[str],
	*,
	moduli: Mapping[str, str] | None = None,
	a_scelta: Iterable[str] = (),
	agenzia: bool = False,
	accessi_clinici: bool = False,
	requisiti: Iterable[str] | None = None,
) -> dict[str, str]:
	"""Every capability a person has, with its scope.

	- ``livelli_utente``: the person's levels. With several, each capability takes
	  the widest scope any of them gives.
	- ``moduli``: the plan, module -> state. A module that is off takes its
	  capabilities away; one that is read-only keeps those that do not write.
	- ``a_scelta``: the optional capabilities the Manager turned on for this person.
	- ``agenzia``: the agency sees and configures everything that is not clinical,
	  including what is technical; clinical data only with ``accessi_clinici``, the
	  time-limited access the centre grants.
	- ``requisiti``: what the site has (``"builder"``…). A capability that needs
	  something the site lacks is nobody's, the agency's included: there is no site
	  to manage without Builder. None means every requirement is met.
	"""
	livelli_utente = set(livelli_utente)
	a_scelta = set(a_scelta)
	requisiti = None if requisiti is None else set(requisiti)
	sola_lettura = SOLA_LETTURA_LIVELLO in livelli_utente
	risultato: dict[str, str] = {}

	for nome, capacita in _r.capacita.items():
		if capacita.requisito and requisiti is not None and capacita.requisito not in requisiti:
			continue
		ambito: str | None = None
		if agenzia and (not capacita.clinica or accessi_clinici):
			ambito = CENTRO
		elif not capacita.agenzia:
			for chiave, concesso in _r.concessioni.get(nome, {}).items():
				if chiave not in livelli_utente:
					continue
				if concesso == A_SCELTA:
					if nome not in a_scelta:
						continue
					concesso = CENTRO
				ambito = piu_ampio(ambito, concesso)
		if ambito is None:
			continue

		if capacita.scrive and sola_lettura and not agenzia:
			continue
		# the plan decides for everyone, the agency included: switching a module
		# off is what the plan is for. Only the technical side stays reachable, so
		# whoever manages the site can still switch it back on.
		if not capacita.agenzia:
			stato = stato_modulo(capacita.piano, moduli)
			if stato == SPENTO:
				continue
			if stato == SOLA_LETTURA and capacita.scrive:
				continue
		risultato[nome] = ambito

	return risultato


# ---------------------------------------------------------------------------
# The Frappe edge: users, the plan, Role Profiles.


def carica() -> None:
	"""Make sure every module has registered, in this process.

	Frappe serves hooks from its cache: a worker that never missed it never imports
	``crm/hooks.py``, so registering there alone is not enough. The composition root
	does it once per process.
	"""
	from crm.registrazione import carica as carica_moduli

	carica_moduli()


def _frappe():
	import frappe

	return frappe


def e_agenzia(user: str) -> bool:
	"""Whether ``user`` manages the site rather than works in the centre."""
	frappe = _frappe()
	if user == "Administrator":
		return True
	return bool(RUOLI_AGENZIA & set(frappe.get_roles(user)))


def profili_di(user: str) -> list[str]:
	frappe = _frappe()
	return frappe.get_all(
		"User Role Profile",
		filters={"parent": user, "parenttype": "User"},
		pluck="role_profile",
		order_by="idx asc",
	)


def livelli_di(user: str | None = None) -> list[str]:
	"""The levels ``user`` holds, in the registry's order.

	Explicit ones from their Role Profiles. A user who predates levels, and holds
	none, counts as the levels their roles stand for.
	"""
	frappe = _frappe()
	carica()
	user = user or frappe.session.user
	espliciti = [lv.chiave for lv in map(livello_del_profilo, profili_di(user)) if lv]
	if espliciti:
		ordine = {lv.chiave: i for i, lv in enumerate(livelli())}
		return sorted(espliciti, key=lambda chiave: ordine.get(chiave, 99))
	if e_agenzia(user):
		return []
	return livelli_impliciti(frappe.get_roles(user))


def moduli_attivi() -> dict[str, str]:
	"""The plan: module -> state, today. Cached for the request."""
	frappe = _frappe()
	cache = getattr(frappe.local, "crm_moduli_attivi", None)
	if cache is not None:
		return cache
	from crm.fcrm.doctype.crm_plan.crm_plan import stati_moduli

	stati = stati_moduli()
	frappe.local.crm_moduli_attivi = stati
	return stati


def requisiti_soddisfatti() -> set[str]:
	"""The requirements this site meets. Cached for the request."""
	frappe = _frappe()
	cache = getattr(frappe.local, "crm_requisiti", None)
	if cache is not None:
		return cache
	soddisfatti = set()
	for chiave, funzione in _r.requisiti.items():
		try:
			if funzione():
				soddisfatti.add(chiave)
		except Exception:
			# a check that cannot answer is a requirement not met, never a broken page
			continue
	frappe.local.crm_requisiti = soddisfatti
	return soddisfatti


def capacita_a_scelta(user: str) -> list[str]:
	frappe = _frappe()
	return frappe.get_all(
		"CRM User Capability",
		filters={"user": user, "enabled": 1},
		pluck="capability",
	)


def capacita_di(user: str | None = None) -> dict[str, str]:
	"""Everything ``user`` may do, with the scope. Cached for the request."""
	frappe = _frappe()
	carica()
	user = user or frappe.session.user
	cache = getattr(frappe.local, "crm_capacita", None)
	if cache is None:
		cache = frappe.local.crm_capacita = {}
	if user in cache:
		return cache[user]

	if user == "Guest":
		risultato = {}
	else:
		agenzia = e_agenzia(user)
		risultato = calcola(
			livelli_di(user),
			moduli=moduli_attivi(),
			a_scelta=() if agenzia else capacita_a_scelta(user),
			agenzia=agenzia,
			requisiti=requisiti_soddisfatti(),
		)
	cache[user] = risultato
	return risultato


def puo(nome: str, user: str | None = None) -> bool:
	"""Whether ``user`` (the session's by default) may do ``nome``."""
	return nome in capacita_di(user)


def ambito(nome: str, user: str | None = None) -> str | None:
	"""On which records ``user`` may do ``nome``; None when they may not at all."""
	return capacita_di(user).get(nome)


def verifica(
	nome: str,
	user: str | None = None,
	messaggio: str | None = None,
	ambito_minimo: str | None = None,
) -> None:
	"""Stop the request unless ``user`` may do ``nome``.

	``ambito_minimo`` asks for at least that scope: the team rota is the whole
	team's, so the practitioner who may ask for their own holidays does not read it.
	"""
	frappe = _frappe()
	concesso = ambito(nome, user)
	if concesso is None or (ambito_minimo and _AMPIEZZA.get(concesso, 0) < _AMPIEZZA.get(ambito_minimo, 0)):
		frappe.throw(messaggio or frappe._("You are not permitted to do this."), frappe.PermissionError)


def richiede(*nomi: str) -> Callable:
	"""Decorator: the function runs only for who may do at least one of ``nomi``.

	Goes under ``@frappe.whitelist()``: the check runs on every call, from any
	route in.
	"""

	def decoratore(funzione):
		@wraps(funzione)
		def controllata(*args, **kwargs):
			frappe = _frappe()
			if not any(puo(nome) for nome in nomi):
				frappe.throw(frappe._("You are not permitted to do this."), frappe.PermissionError)
			return funzione(*args, **kwargs)

		return controllata

	return decoratore


def dimentica_cache() -> None:
	"""Forget what was worked out in this request: levels or the plan changed."""
	frappe = _frappe()
	for nome in ("crm_capacita", "crm_moduli_attivi", "crm_requisiti", "crm_ambiti", "crm_sola_lettura"):
		try:
			delattr(frappe.local, nome)
		except AttributeError:
			pass
