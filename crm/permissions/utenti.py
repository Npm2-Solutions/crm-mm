# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Levels on real users: the Role Profiles, giving levels, and the migration.

`livelli.py` is the registry and the pure computation. This is where they meet
Frappe, which imposes one rule on everything below: at every save of a user with
role profiles, `User.populate_role_profile_roles` rebuilds their roles from the
profiles, and a role added by hand disappears. So it is all levels or nothing:

- a level is a Role Profile carrying exactly the roles the registry lists for it;
- the agency's users (System Manager) hold no centre level, or their System
  Manager would be gone at the next save;
- optional capabilities are rows of `CRM User Capability`, not roles.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import clear_document_cache

from crm.permissions import livelli
from crm.permissions.livelli import ATTIVO, PROVA, carica

# ---------------------------------------------------------------------------
# Roles and Role Profiles, from the registry.


def assicura_ruoli() -> None:
	"""Every role the CRM brings as a Role record, and nothing else.

	Also before the doctypes sync: a DocPerm pointing at a role that does not exist
	yet fails link validation, and the invoices give Practitioner their own. The
	roles Frappe creates by itself are left to Frappe.
	"""
	carica()
	for nome, descrizione in livelli.ruoli_da_creare().items():
		_assicura_ruolo(nome, descrizione)


def sincronizza() -> None:
	"""Every registered role and level as Role and Role Profile. Idempotent.

	Runs at install, at every migrate and before the first levels are given: the
	registry is code, the profiles are records, and the records follow the code.
	"""
	assicura_ruoli()
	for livello in livelli.livelli():
		_assicura_profilo(livello)


def _assicura_ruolo(nome: str, descrizione: str) -> None:
	if frappe.db.exists("Role", nome):
		return
	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": nome,
			"desk_access": 1,
			"is_custom": 1,
			"search_bar": 1,
			"notifications": 1,
			"list_sidebar": 1,
			"form_sidebar": 1,
			"report": 1,
			"dashboard": 1,
			"description": descrizione,
		}
	).insert(ignore_permissions=True)


def _assicura_profilo(livello: livelli.Livello) -> None:
	ruoli = sorted(livelli.ruoli_del_livello(livello.chiave))
	if not frappe.db.exists("Role Profile", livello.profilo):
		frappe.get_doc(
			{
				"doctype": "Role Profile",
				"role_profile": livello.profilo,
				"roles": [{"role": ruolo} for ruolo in ruoli],
			}
		).insert(ignore_permissions=True)
		return

	attuali = frappe.get_all(
		"Has Role", filters={"parenttype": "Role Profile", "parent": livello.profilo}, pluck="role"
	)
	if set(attuali) == set(ruoli):
		return
	# Straight to the rows rather than through `save()`. Saving a Role Profile queues
	# a job that re-saves its users, and locks the profile until a worker has run it:
	# a second migrate before then would have to skip the change, and its users would
	# keep the roles of the level before. Here the users are re-saved now, instead.
	frappe.db.delete("Has Role", {"parenttype": "Role Profile", "parent": livello.profilo})
	for indice, ruolo in enumerate(ruoli, start=1):
		frappe.get_doc(
			{
				"doctype": "Has Role",
				"parenttype": "Role Profile",
				"parentfield": "roles",
				"parent": livello.profilo,
				"role": ruolo,
				"idx": indice,
			}
		).db_insert()
	frappe.db.set_value("Role Profile", livello.profilo, "modified", frappe.utils.now())
	clear_document_cache("Role Profile", livello.profilo)
	for user in frappe.get_all(
		"User Role Profile",
		filters={"role_profile": livello.profilo, "parenttype": "User"},
		pluck="parent",
	):
		frappe.get_doc("User", user).save(ignore_permissions=True)


def profili_crm() -> set[str]:
	return {livello.profilo for livello in livelli.livelli()}


# ---------------------------------------------------------------------------
# Giving levels.


def livelli_offerti() -> list[livelli.Livello]:
	"""The levels a Manager may give on this site: those whose module is on."""
	carica()
	moduli = livelli.moduli_attivi()
	return [lv for lv in livelli.livelli() if livelli.stato_modulo(lv.piano, moduli) in (ATTIVO, PROVA)]


def verifica_livelli(chiavi: list[str]) -> list[str]:
	"""The keys, checked: registered, offered here, and at least one."""
	offerti = {lv.chiave for lv in livelli_offerti()}
	chiavi = list(dict.fromkeys(chiavi or []))
	if not chiavi:
		frappe.throw(_("Choose at least one level"))
	for chiave in chiavi:
		if chiave not in offerti:
			frappe.throw(_("{0} is not a level that can be given here").format(frappe.bold(chiave)))
	if all(livelli.livello(chiave).aggiuntivo for chiave in chiavi):
		# Read only takes away; it needs a level to take from
		frappe.throw(_("Read only goes with another level"))
	return chiavi


def verifica_gestione(user: str) -> None:
	"""Stop unless the session may change ``user``'s access from the CRM."""
	livelli.verifica("utenti.gestisci", messaggio=_("Only a manager can change who does what"))
	if livelli.e_agenzia(user):
		frappe.throw(
			_("{0} manages the site: their access is set by the agency, from the Desk").format(user),
			frappe.PermissionError,
		)


def assegna_livelli(user: str, chiavi: list[str]) -> None:
	"""Give ``user`` exactly these levels, and the roles they carry. Checks are the
	caller's: this is also what the migration and invitations use."""
	carica()
	if not all(frappe.db.exists("Role Profile", livelli.livello(c).profilo) for c in chiavi):
		sincronizza()

	doc = frappe.get_doc("User", user)
	crm = profili_crm()
	altri = [riga.role_profile for riga in doc.role_profiles if riga.role_profile not in crm]
	nuovi = [livelli.livello(chiave).profilo for chiave in chiavi]
	persi = ruoli_che_si_perderebbero(doc, altri + nuovi)
	if persi:
		frappe.throw(
			_(
				"{0} also has roles the levels do not carry ({1}): giving levels would take them away. "
				"The agency sets their access, from the Desk."
			).format(user, ", ".join(sorted(persi)))
		)
	doc.set("role_profiles", [{"role_profile": profilo} for profilo in altri + nuovi])
	# the deprecated single field still holds the first profile of before, and Frappe
	# puts it back into the table at save when it is not there
	doc.role_profile_name = None
	if not doc.role_profiles:
		_togli_ruoli_crm(doc)
	_moduli_desk(doc, chiavi)
	# a person's email reaches whoever follows them in DottorCloud's panel
	# (crm.posta.ingresso): the framework's copy to their own mailbox would be a
	# second one, outside DottorCloud, and a patient's words in a private inbox
	if chiavi:
		doc.thread_notify = 0
	doc.save(ignore_permissions=True)
	livelli.dimentica_cache()


def ruoli_che_si_perderebbero(doc, profili: list[str]) -> set[str]:
	"""The roles ``doc`` would lose if its profiles became ``profili``.

	Frappe rebuilds a profiled user's roles from their profiles: whatever the
	profiles do not carry goes. For the CRM's own roles that is the point - a new
	level replaces the old one's - but another app's role, or the agency's System
	Manager, must never go as a side effect of giving someone a level.
	"""
	restano: set[str] = set()
	for profilo in profili:
		restano |= set(
			frappe.get_all(
				"Has Role", filters={"parenttype": "Role Profile", "parent": profilo}, pluck="role"
			)
		)
	del_crm = set(livelli.ruoli_registrati()) - livelli.RUOLI_AGENZIA
	return {riga.role for riga in doc.roles} - restano - del_crm - livelli.RUOLI_AUTOMATICI


def togli_dal_crm(user: str) -> None:
	"""Take every CRM level and role from ``user``, with what hangs off them."""
	carica()
	doc = frappe.get_doc("User", user)
	crm = profili_crm()
	doc.set("role_profiles", [riga for riga in doc.role_profiles if riga.role_profile not in crm])
	doc.role_profile_name = None
	if not doc.role_profiles:
		_togli_ruoli_crm(doc)
	doc.save(ignore_permissions=True)

	for nome in frappe.get_all("CRM User Capability", filters={"user": user}, pluck="name"):
		frappe.delete_doc("CRM User Capability", nome, ignore_permissions=True)
	nodo = frappe.db.get_value("CRM Sales Hierarchy", {"user": user}, "name")
	if nodo:
		frappe.delete_doc("CRM Sales Hierarchy", nodo, ignore_permissions=True)
	livelli.dimentica_cache()


def _togli_ruoli_crm(doc) -> None:
	# without profiles Frappe rebuilds nothing, so the CRM's roles go by hand; the
	# agency's stay, and so does every other app's
	crm = set(livelli.ruoli_registrati()) - livelli.RUOLI_AGENZIA
	doc.set("roles", [riga for riga in doc.roles if riga.role not in crm])


def _moduli_desk(doc, chiavi: list[str]) -> None:
	"""Which Desk modules the user keeps.

	Front desk and practitioners work in the CRM: the Desk shows them only the CRM
	app's modules, as it always did for Sales Users - invoicing and the Sistema TS
	included, which the old block took away. A Manager keeps what they had.
	"""
	app = set(frappe.get_module_list("crm"))
	if any(livelli.livello(chiave).desk for chiave in chiavi):
		doc.set("block_modules", [riga for riga in doc.block_modules if riga.module not in app])
		return
	doc.set(
		"block_modules",
		[{"module": modulo} for modulo in frappe.get_all("Module Def", pluck="name") if modulo not in app],
	)


def recapiti_fuori_dai_livelli(doc, method=None) -> None:
	"""`validate` of User: whoever works in the CRM outside the levels, with the roles
	of before, counts as the level those roles imply (PR 1), and every such level sees
	email and phone in full. They get the role that shows them (PR 4); a user with
	levels gets it, or not, from the levels' profiles."""
	carica()
	if doc.name in ("Administrator", "Guest") or not frappe.db.exists("Role", livelli.RUOLO_RECAPITI):
		return
	crm = profili_crm()
	if any(riga.role_profile in crm for riga in doc.get("role_profiles") or []):
		return
	ruoli = {riga.role for riga in doc.get("roles") or []}
	if livelli.RUOLO_RECAPITI in ruoli or not ruoli & livelli.ruoli_di_accesso():
		return
	doc.append("roles", {"role": livelli.RUOLO_RECAPITI})


def imposta_capacita(user: str, nome: str, attiva: bool) -> None:
	"""Turn one of ``user``'s optional capabilities on or off. Checks are the caller's."""
	carica()
	offerte = livelli.a_scelta_dei_livelli(livelli.livelli_di(user))
	if nome not in offerte:
		frappe.throw(_("{0} is not optional for this person's level").format(frappe.bold(nome)))
	chiave = f"{user}|{nome}"
	if frappe.db.exists("CRM User Capability", chiave):
		doc = frappe.get_doc("CRM User Capability", chiave)
		doc.enabled = 1 if attiva else 0
		doc.save(ignore_permissions=True)
	elif attiva:
		frappe.get_doc(
			{
				"doctype": "CRM User Capability",
				"user": user,
				"capability": nome,
				"enabled": 1,
				"granted_by": frappe.session.user,
			}
		).insert(ignore_permissions=True)
	livelli.dimentica_cache()


# ---------------------------------------------------------------------------
# The migration: users from before levels.


def migra_utenti() -> list[tuple[str, list[str]]]:
	"""Give levels to the users who predate them. Nobody loses a role.

	Who fits gets the levels `catalogo.livelli_iniziali` picks; the agency, anyone
	with another app's roles and anyone the levels would not cover keep their roles
	as they are, and count as the levels their roles imply.
	"""
	from crm.permissions import catalogo
	from crm.permissions.org_hierarchy import hierarchy_enabled

	carica()
	sincronizza()
	gerarchia = hierarchy_enabled()
	con_profilo = set(frappe.get_all("User Role Profile", filters={"parenttype": "User"}, pluck="parent"))
	candidati = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "role": ["in", sorted(livelli.ruoli_di_accesso())]},
		pluck="parent",
		distinct=True,
	)
	fatti = []
	for user in sorted(set(candidati)):
		if user in frappe.STANDARD_USERS or user in con_profilo:
			continue
		ruoli = set(frappe.get_all("Has Role", filters={"parenttype": "User", "parent": user}, pluck="role"))
		scelti = catalogo.livelli_iniziali(ruoli, gerarchia)
		if not scelti:
			continue
		assegna_livelli(user, scelti)
		fatti.append((user, scelti))
	return fatti
