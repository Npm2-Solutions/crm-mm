# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Taking the demo away: everything it made, and everything that tells of it.

It starts from the register (`crm.demo.registro`) and goes by the database, not by
the controllers: a record that refuses to be deleted on screen (a signed form, an
issued test invoice, a patient's record, a pipeline with deals) is the demo's like
any other here, and nothing waits on hooks run a thousand times. In order:

1. What the centre took over stays: a service, a room, a price list the centre's own
   records use is the centre's now, and leaves the register.
2. What is about the demo goes with it, whoever made it: a note the centre wrote on a
   demo person, an appointment it booked for one, an email to one. What only points at
   the demo (a person of the centre's whose company was a demo one) stays, without it.
3. The rows go, with their child rows; then everything the framework kept beside
   them - versions, comments, emails, assignments, shares, notifications, the global
   search, deleted documents, logs - and the demo users with their roles, settings
   and sessions; the files on disk; the counters the names were numbered by.

Nothing of the demo is left to read: the tests look for its names in every table.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass

import frappe

from crm.demo import guardie, registro

#: What the framework keeps beside a record: it goes with what it is about.
TRACCE = frozenset(
	{
		"Version",
		"Comment",
		"Communication",
		"Communication Link",
		"ToDo",
		"DocShare",
		"Notification Log",
		"CRM Notification",
		"View Log",
		"Access Log",
		"Activity Log",
		"Email Queue",
		"Tag Link",
		"Document Follow",
		"Deleted Document",
		"Error Log",
		"Submission Queue",
		"Integration Request",
		"Event",
		"Event Participants",
		"File",
		"Route History",
		"Permission Log",
	}
)

#: The framework's tables that name a record by two columns, not all of them links.
COPPIE = (
	("Version", "ref_doctype", "docname"),
	("Comment", "reference_doctype", "reference_name"),
	("Communication", "reference_doctype", "reference_name"),
	("Communication Link", "link_doctype", "link_name"),
	("ToDo", "reference_type", "reference_name"),
	("DocShare", "share_doctype", "share_name"),
	("Notification Log", "document_type", "document_name"),
	("CRM Notification", "reference_doctype", "reference_name"),
	("CRM Notification", "notification_type_doctype", "notification_type_doc"),
	("View Log", "reference_doctype", "reference_name"),
	("Access Log", "export_from", "reference_document"),
	("Activity Log", "reference_doctype", "reference_name"),
	("Activity Log", "timeline_doctype", "timeline_name"),
	("Email Queue", "reference_doctype", "reference_name"),
	("Tag Link", "document_type", "document_name"),
	("Document Follow", "ref_doctype", "ref_docname"),
	("Deleted Document", "deleted_doctype", "deleted_name"),
	("Error Log", "reference_doctype", "reference_name"),
	("Submission Queue", "ref_doctype", "ref_docname"),
	("Integration Request", "reference_doctype", "reference_docname"),
	("Event", "reference_doctype", "reference_docname"),
	("Event Participants", "reference_doctype", "reference_docname"),
	("File", "attached_to_doctype", "attached_to_name"),
)

#: Setup a centre may have taken over: kept when its own records use it.
IMPOSTAZIONI = frozenset(
	{
		"CRM Service",
		"CRM Resource",
		"CRM Price List",
		"CRM Holiday List",
		"CRM Lead Source",
		"CRM Industry",
		"CRM Lost Reason",
		"CRM Service Provider",
		"CRM Subscription Type",
		"CRM Billable Service",
		"CRM Form Template",
		"CRM Consent Type",
		"CRM Invoicing Company",
		"CRM Pipeline",
		"CRM Deal Status",
		"CRM Professional Qualification",
		"Email Template",
		"WhatsApp Templates",
	}
)

#: A record that points at one of these is about a person, and goes with them.
PERSONE = frozenset({"CRM Lead", "CRM Deal", "Contact"})
#: ...unless it is a person or a company itself: then it only stops pointing.
ANAGRAFICHE = frozenset({"CRM Lead", "Contact", "CRM Organization", "User"})

#: Never taken away, whatever the register says: the site's own structure.
MAI = frozenset(
	{"DocType", "DocField", "Custom Field", "Property Setter", "Role", "Role Profile", "Module Def"}
)


@dataclass(frozen=True)
class Campo:
	doctype: str
	fieldname: str
	tipo: str
	opzioni: str
	obbligatorio: bool
	figlia: bool
	singola: bool


def togli(avanza: Callable[[str], None] | None = None) -> dict:
	"""Take the demo away. Returns how many records of each kind went, and the setup
	the centre kept."""
	avanza = avanza or (lambda _testo: None)
	_svuota_la_ricerca_in_coda()

	via = defaultdict(set)
	for doctype, nomi in registro.registrati().items():
		if doctype not in MAI:
			via[doctype].update(nomi)
	utenti = set(via.pop("User", set()))
	indirizzi = _indirizzi(via, utenti)
	tabelle = _tabelle()
	campi = _campi(tabelle)

	avanza("What the centre uses")
	tenuti = _tenuti(via, campi, tabelle)

	avanza("What is about the demo")
	figlie = _a_cascata(via, utenti, campi, tabelle)
	_specchi(via, tabelle)

	avanza("Records")
	file_su_disco = _file(via, tabelle)
	contati = {}
	for doctype, nomi in via.items():
		if nomi and _tabella(doctype) in tabelle:
			contati[doctype] = _cancella(doctype, nomi, tabelle)
	for doctype, nomi in figlie.items():
		_cancella_righe(doctype, nomi)

	avanza("What was left pointing at it")
	_svuota_i_riferimenti(via, utenti, campi, tabelle)
	_utenti(utenti, tabelle)
	contati["User"] = len(utenti)
	_ricerca(via)
	_posta(indirizzi)
	_errori()
	_contatori(via)

	frappe.db.delete(registro.REGISTRO)
	for chiave in (registro.STATO, registro.FATTE, registro.LAVORO, registro.SERIE):
		frappe.db.set_default(chiave, None)
	frappe.db.commit()

	# what a job synced into the global search while this ran: once more, now
	_svuota_la_ricerca_in_coda()
	_ricerca(via)
	frappe.db.commit()

	_cancella_dal_disco(file_su_disco)
	_autoincrementi(via, tabelle)
	guardie.dimentica()
	frappe.clear_cache()
	return {
		"removed": {doctype: numero for doctype, numero in contati.items() if numero},
		"kept": {doctype: sorted(nomi) for doctype, nomi in tenuti.items() if nomi},
	}


# -- the database's shape -------------------------------------------------------------------


def _tabella(doctype: str) -> str:
	return f"tab{doctype}"


def _tabelle() -> set[str]:
	return set(frappe.db.get_tables(cached=False))


def _campi(tabelle: set[str]) -> list[Campo]:
	"""Every Link and Dynamic Link of every doctype with a table, its own and custom."""
	righe = frappe.db.sql(
		"""
		select df.parent as doctype, df.fieldname, df.fieldtype, df.options, df.reqd,
			dt.istable, dt.issingle
		from `tabDocField` df join `tabDocType` dt on dt.name = df.parent
		where df.fieldtype in ('Link', 'Dynamic Link') and ifnull(dt.is_virtual, 0) = 0
		union all
		select cf.dt, cf.fieldname, cf.fieldtype, cf.options, cf.reqd, dt.istable, dt.issingle
		from `tabCustom Field` cf join `tabDocType` dt on dt.name = cf.dt
		where cf.fieldtype in ('Link', 'Dynamic Link') and ifnull(dt.is_virtual, 0) = 0
		""",
		as_dict=True,
	)
	campi = []
	for riga in righe:
		singola = bool(riga.issingle)
		if not singola and _tabella(riga.doctype) not in tabelle:
			continue
		campi.append(
			Campo(
				doctype=riga.doctype,
				fieldname=riga.fieldname,
				tipo=riga.fieldtype,
				opzioni=riga.options or "",
				obbligatorio=bool(riga.reqd),
				figlia=bool(riga.istable),
				singola=singola,
			)
		)
	return campi


def _a_pezzi(nomi: Iterable, quanti: int = 500) -> Iterable[list[str]]:
	# a table numbered by the database gives its names as numbers
	elenco = sorted({str(nome) for nome in nomi})
	for inizio in range(0, len(elenco), quanti):
		yield elenco[inizio : inizio + quanti]


def _chi_punta(campi: list[Campo], bersagli: dict[str, set[str]], tabelle: set[str]):
	"""Every row pointing at one of ``bersagli``: (field, row's doctype, row's name,
	its parent's doctype and name for a child row, the record pointed at)."""
	if not any(bersagli.values()):
		return
	tutti = set().union(*bersagli.values())
	for campo in campi:
		if campo.singola:
			continue
		tabella = _tabella(campo.doctype)
		if campo.tipo == "Link":
			nomi = bersagli.get(campo.opzioni)
			if not nomi:
				continue
			for pezzo in _a_pezzi(nomi):
				# nosemgrep: frappe-sql-format-injection — tables and columns from the DocTypes' metadata, the names bound
				for riga in frappe.db.sql(
					f"""select {_di_chi(campo)}, `{campo.fieldname}` as bersaglio
					from `{tabella}` where `{campo.fieldname}` in %(nomi)s""",
					{"nomi": pezzo},
					as_dict=True,
				):
					yield campo, riga, campo.opzioni
		else:
			if not campo.opzioni:
				continue
			for pezzo in _a_pezzi(tutti):
				# nosemgrep: frappe-sql-format-injection — tables and columns from the DocTypes' metadata, the names bound
				for riga in frappe.db.sql(
					f"""select {_di_chi(campo)}, `{campo.opzioni}` as tipo,
						`{campo.fieldname}` as bersaglio
					from `{tabella}` where `{campo.fieldname}` in %(nomi)s
						and `{campo.opzioni}` in %(tipi)s""",
					{"nomi": pezzo, "tipi": sorted(bersagli)},
					as_dict=True,
				):
					if str(riga.bersaglio) in bersagli.get(riga.tipo, ()):
						yield campo, riga, riga.tipo


def _di_chi(campo: Campo) -> str:
	"""The columns that say whose a row is: only child tables have a parent."""
	if campo.figlia:
		return "name, parent, parenttype"
	return "name, null as parent, null as parenttype"


def _proprietario(campo: Campo, riga) -> tuple[str, str]:
	"""Whose the row is: a child row is its parent's."""
	if campo.figlia:
		return riga.parenttype, str(riga.parent) if riga.parent is not None else None
	return campo.doctype, str(riga.name)


# -- 1. what the centre took over -----------------------------------------------------------------


def _tenuti(via: dict[str, set[str]], campi: list[Campo], tabelle: set[str]) -> dict[str, set[str]]:
	tenuti = defaultdict(set)
	while True:
		bersagli = {doctype: via[doctype] for doctype in IMPOSTAZIONI if via.get(doctype)}
		nuovi = defaultdict(set)
		for campo, riga, doctype in _chi_punta(campi, bersagli, tabelle):
			chi, nome = _proprietario(campo, riga)
			if not chi or nome in via.get(chi, ()) or chi in TRACCE or chi == registro.REGISTRO:
				continue
			nuovi[doctype].add(str(riga.bersaglio))
		if not any(nuovi.values()):
			return tenuti
		for doctype, nomi in nuovi.items():
			via[doctype] -= nomi
			tenuti[doctype] |= nomi


# -- 2. what is about the demo -------------------------------------------------------------------


def _riguarda(campo: Campo, bersaglio: str, chi: str) -> bool:
	"""Whether a record pointing at a demo record by ``campo`` is about it."""
	if campo.tipo == "Dynamic Link" or campo.obbligatorio:
		return True
	return bersaglio in PERSONE and chi not in ANAGRAFICHE


def _a_cascata(
	via: dict[str, set[str]], utenti: set[str], campi: list[Campo], tabelle: set[str]
) -> dict[str, set[str]]:
	"""Add to ``via`` what is about the demo; return the child rows of the centre's
	records that are (a participant, a link in an address book entry)."""
	figlie = defaultdict(set)
	nuovi = {doctype: set(nomi) for doctype, nomi in via.items() if doctype not in IMPOSTAZIONI}
	if utenti:
		nuovi["User"] = set(utenti)
	while any(nuovi.values()):
		trovati = defaultdict(set)
		for campo, riga, bersaglio in _chi_punta(campi, nuovi, tabelle):
			chi, nome = _proprietario(campo, riga)
			if not chi or not nome or nome in via.get(chi, ()):
				continue
			if chi in TRACCE:
				trovati[chi].add(nome)
			elif bersaglio == "User":
				# the demo's colleagues: a row of theirs in somebody's table goes, a
				# field naming them is emptied afterwards
				if campo.figlia and campo.obbligatorio:
					figlie[campo.doctype].add(str(riga.name))
			elif campo.figlia:
				if _riguarda(campo, bersaglio, chi):
					figlie[campo.doctype].add(str(riga.name))
			elif _riguarda(campo, bersaglio, chi):
				trovati[chi].add(nome)
		for tabella_traccia, colonna_tipo, colonna_nome in COPPIE:
			if _tabella(tabella_traccia) not in tabelle:
				continue
			for doctype, nomi in nuovi.items():
				for pezzo in _a_pezzi(nomi):
					for nome in frappe.db.sql_list(
						f"""select name from `tab{tabella_traccia}`
						where `{colonna_tipo}` = %(doctype)s and `{colonna_nome}` in %(nomi)s""",
						{"doctype": doctype, "nomi": pezzo},
					):
						if str(nome) not in via.get(tabella_traccia, ()):
							trovati[tabella_traccia].add(str(nome))
		nuovi = defaultdict(set)
		for doctype, nomi in trovati.items():
			nomi = nomi - via.get(doctype, set())
			if nomi:
				via[doctype] |= nomi
				nuovi[doctype] |= nomi
	return figlie


def _specchi(via: dict[str, set[str]], tabelle: set[str]) -> None:
	"""The calendar events an appointment of the demo was mirrored into, once the
	centre moved it."""
	appuntamenti = via.get("CRM Appointment")
	if not appuntamenti or "tabEvent" not in tabelle:
		return
	for pezzo in _a_pezzi(appuntamenti):
		eventi = frappe.db.sql_list(
			"select event from `tabCRM Appointment` where name in %(nomi)s and ifnull(event, '') != ''",
			{"nomi": pezzo},
		)
		via["Event"].update(eventi)


# -- 3. the rows ---------------------------------------------------------------------------------


def _cancella(doctype: str, nomi: set[str], tabelle: set[str]) -> int:
	meta = frappe.get_meta(doctype)
	cancellati = 0
	for pezzo in _a_pezzi(nomi):
		for campo in meta.get_table_fields():
			tabella_figlia = _tabella(campo.options)
			if tabella_figlia in tabelle:
				# nosemgrep: frappe-sql-format-injection — tables and columns from the DocTypes' metadata, the names bound
				frappe.db.sql(
					f"""delete from `{tabella_figlia}`
					where parenttype = %(doctype)s and parent in %(nomi)s""",
					{"doctype": doctype, "nomi": pezzo},
				)
		# nosemgrep: frappe-sql-format-injection — tables and columns from the DocTypes' metadata, the names bound
		frappe.db.sql(f"delete from `tab{doctype}` where name in %(nomi)s", {"nomi": pezzo})
		cancellati += len(pezzo)
	return cancellati


def _cancella_righe(doctype: str, nomi: set[str]) -> None:
	for pezzo in _a_pezzi(nomi):
		# nosemgrep: frappe-sql-format-injection — tables and columns from the DocTypes' metadata, the names bound
		frappe.db.sql(f"delete from `tab{doctype}` where name in %(nomi)s", {"nomi": pezzo})


def _svuota_i_riferimenti(
	via: dict[str, set[str]], utenti: set[str], campi: list[Campo], tabelle: set[str]
) -> None:
	"""What stays stops pointing at what went: a field naming a demo record or a demo
	colleague is emptied, in the records and in the settings."""
	andati = {doctype: nomi for doctype, nomi in via.items() if nomi}
	if utenti:
		andati["User"] = utenti
	for campo in campi:
		if campo.tipo != "Link":
			continue
		nomi = andati.get(campo.opzioni)
		if not nomi:
			continue
		for pezzo in _a_pezzi(nomi):
			if campo.singola:
				frappe.db.sql(
					"""delete from `tabSingles` where doctype = %(doctype)s and field = %(campo)s
					and value in %(nomi)s""",
					{"doctype": campo.doctype, "campo": campo.fieldname, "nomi": pezzo},
				)
			else:
				# nosemgrep: frappe-sql-format-injection — tables and columns from the DocTypes' metadata, the names bound
				frappe.db.sql(
					f"""update `tab{campo.doctype}` set `{campo.fieldname}` = null
					where `{campo.fieldname}` in %(nomi)s""",
					{"nomi": pezzo},
				)
	if utenti:
		_assegnazioni(utenti, tabelle)


def _assegnazioni(utenti: set[str], tabelle: set[str]) -> None:
	"""The demo's colleagues out of whom a record is assigned to."""
	for (tabella,) in frappe.db.sql(
		"""select table_name from information_schema.columns
		where table_schema = database() and column_name = '_assign'"""
	):
		if tabella not in tabelle:
			continue
		# nosemgrep: frappe-sql-format-injection — a table the database itself lists, the pattern bound
		for nome, valore in frappe.db.sql(
			f"select name, `_assign` from `{tabella}` where `_assign` like %(dominio)s",
			{"dominio": "%@%"},
		):
			try:
				assegnati = json.loads(valore or "[]")
			except ValueError:
				continue
			restano = [utente for utente in assegnati if utente not in utenti]
			if len(restano) != len(assegnati):
				# nosemgrep: frappe-sql-format-injection — a table the database itself lists, the values bound
				frappe.db.sql(
					f"update `{tabella}` set `_assign` = %(valore)s where name = %(nome)s",
					{"valore": json.dumps(restano) if restano else None, "nome": nome},
				)


def _utenti(utenti: set[str], tabelle: set[str]) -> None:
	"""The demo's colleagues, and what the framework keeps for a user."""
	if not utenti:
		return
	for pezzo in _a_pezzi(utenti):
		_cancella("User", set(pezzo), tabelle)
		# a user's own settings, named after them, with their child rows
		for doctype in ("Notification Settings", "Dashboard Settings"):
			if _tabella(doctype) in tabelle:
				_cancella(doctype, set(pezzo), tabelle)
		for tabella, colonna in (
			("tabDefaultValue", "parent"),
			("__UserSettings", "user"),
			("tabSessions", "user"),
			("tabUser Permission", "user"),
			("tabRoute History", "user"),
		):
			if tabella in tabelle:
				# nosemgrep: frappe-sql-format-injection — table and column from the tuples above, the names bound
				frappe.db.sql(f"delete from `{tabella}` where `{colonna}` in %(nomi)s", {"nomi": pezzo})
		if "__Auth" in tabelle:
			frappe.db.sql("delete from `__Auth` where doctype = 'User' and name in %(nomi)s", {"nomi": pezzo})


def _ricerca(via: dict[str, set[str]]) -> None:
	"""The global search's rows of what went."""
	for doctype, nomi in via.items():
		for pezzo in _a_pezzi(nomi):
			frappe.db.sql(
				"delete from `__global_search` where doctype = %(doctype)s and name in %(nomi)s",
				{"doctype": doctype, "nomi": pezzo},
			)


def _indirizzi(via: dict[str, set[str]], utenti: set[str]) -> set[str]:
	"""The demo's email addresses: its people's, its address book's, its colleagues'."""
	indirizzi = set(utenti)
	for pezzo in _a_pezzi(via.get("CRM Lead", ())):
		indirizzi.update(
			frappe.db.sql_list(
				"select email from `tabCRM Lead` where name in %(nomi)s and ifnull(email, '') != ''",
				{"nomi": pezzo},
			)
		)
	for pezzo in _a_pezzi(via.get("Contact", ())):
		indirizzi.update(
			frappe.db.sql_list(
				"""select email_id from `tabContact Email`
				where parenttype = 'Contact' and parent in %(nomi)s""",
				{"nomi": pezzo},
			)
		)
	return {indirizzo.strip().lower() for indirizzo in indirizzi if indirizzo}


def _posta(indirizzi: set[str]) -> None:
	"""An email queued to the demo's addresses: their rows go, and the email with them
	when nobody else was in it."""
	if not indirizzi:
		return
	code = set()
	for pezzo in _a_pezzi(indirizzi):
		code.update(
			frappe.db.sql_list(
				"select distinct parent from `tabEmail Queue Recipient` where lower(recipient) in %(indirizzi)s",
				{"indirizzi": pezzo},
			)
		)
		frappe.db.sql(
			"delete from `tabEmail Queue Recipient` where lower(recipient) in %(indirizzi)s",
			{"indirizzi": pezzo},
		)
	# the ones the guard emptied before they were queued (crm.demo.guardie)
	code.update(
		frappe.db.sql_list(
			"select name from `tabEmail Queue` where status = 'Error' and error like %s",
			(f"{guardie.NON_INVIATA}%",),
		)
	)
	for pezzo in _a_pezzi(code):
		vuote = frappe.db.sql_list(
			"""select name from `tabEmail Queue` q where name in %(nomi)s and not exists (
				select 1 from `tabEmail Queue Recipient` r where r.parent = q.name)""",
			{"nomi": pezzo},
		)
		if vuote:
			frappe.db.sql("delete from `tabEmail Queue` where name in %(nomi)s", {"nomi": vuote})


def _errori() -> None:
	"""The logs of a part that could not be made: they tell of the demo's people."""
	frappe.db.sql("delete from `tabError Log` where method like %s", ("Demo data: %",))


def _svuota_la_ricerca_in_coda() -> None:
	"""What waits to enter the global search enters it now, so that it is found and
	taken away rather than written after the demo is gone."""
	try:
		from frappe.utils.global_search import sync_global_search

		sync_global_search()
	except Exception:
		frappe.log_error(title="Demo data: global search not synced before removal")


# -- files, counters ---------------------------------------------------------------------------------


def _file(via: dict[str, set[str]], tabelle: set[str]) -> list[str]:
	"""The paths of the demo's files that no file of the centre's shares."""
	nomi = via.get("File")
	if not nomi or "tabFile" not in tabelle:
		return []
	percorsi = set()
	for pezzo in _a_pezzi(nomi):
		for (url,) in frappe.db.sql(
			"select file_url from `tabFile` where name in %(nomi)s and ifnull(is_folder, 0) = 0",
			{"nomi": pezzo},
		):
			if url and url.startswith(("/files/", "/private/files/")):
				percorsi.add(url)
	condivisi = set()
	for pezzo in _a_pezzi(percorsi):
		condivisi.update(
			frappe.db.sql_list(
				"select distinct file_url from `tabFile` where file_url in %(url)s and name not in %(nomi)s",
				{"url": pezzo, "nomi": sorted(nomi)},
			)
		)
	return sorted(percorsi - condivisi)


def _cancella_dal_disco(percorsi: list[str]) -> None:
	for url in percorsi:
		relativo = url.lstrip("/")
		percorso = frappe.get_site_path(*relativo.split("/"))
		if relativo.startswith("files/"):
			percorso = frappe.get_site_path("public", *relativo.split("/"))
		try:
			if os.path.isfile(percorso):
				os.remove(percorso)
		except OSError:
			frappe.log_error(title="Demo data: a file could not be removed from the disk")


def _serie(nome: str) -> str | None:
	"""The prefix a name was numbered under: "CRM-LEAD-2026-00042" -> "CRM-LEAD-2026-"."""
	trovato = re.match(r"^(.*?)(\d+)$", nome)
	if not trovato or not trovato.group(1):
		return None
	return trovato.group(1)


def _numerato_da_una_serie(doctype: str) -> bool:
	"""Whether ``doctype``'s names come from a series: not a record named after
	another one (a patient after their person), which only looks numbered."""
	try:
		autoname = (frappe.get_meta(doctype).autoname or "").strip()
	except frappe.DoesNotExistError:
		return False
	return autoname.startswith("naming_series:") or (
		"#" in autoname and not autoname.startswith(("field:", "hash", "Prompt", "prompt"))
	)


def _schema_del_formato(autoname: str) -> re.Pattern | None:
	"""The names a "format:APPT-{#####}" rule makes, with the number as their group;
	None for a rule that numbers nothing that way."""
	if not autoname.startswith("format:") or "{#" not in autoname:
		return None
	schema, numerato = "", False
	for testo, parametro in re.findall(r"([^{]*)(?:\{([^}]*)\})?", autoname[len("format:") :]):
		schema += re.escape(testo)
		if parametro.startswith("#"):
			schema += r"\d+" if numerato else r"(\d+)"
			numerato = True
		elif parametro:
			schema += ".*?"
	return re.compile(f"^{schema}$")


def _formati_numerati() -> dict[str, re.Pattern]:
	"""Every doctype with a table named by a "format:…{#####}" rule. The framework numbers
	each braced part on its own, from nothing before it: they all share the series with
	no name, whatever their prefix ("APPT-", "SMS-", "BOOK-")."""
	doctypes = set(
		frappe.db.sql_list("select name from `tabDocType` where autoname like %s", ("format:%{#%",))
	) | set(
		frappe.db.sql_list(
			"select doc_type from `tabProperty Setter` where property = 'autoname' and value like %s",
			("format:%{#%",),
		)
	)
	formati = {}
	for doctype in sorted(doctypes):
		try:
			meta = frappe.get_meta(doctype)
		except frappe.DoesNotExistError:
			continue
		schema = _schema_del_formato((meta.autoname or "").strip())
		if schema and not meta.is_virtual and frappe.db.table_exists(doctype):
			formati[doctype] = schema
	return formati


def _ultimo_in_uso(doctype: str, prefisso: str, schema: re.Pattern | None, tetto: int) -> int:
	"""The highest number ``doctype`` still holds on the series ``prefisso``, up to
	``tetto``, where the series is: a name above it was never one of its numbers."""
	if schema:
		nomi = frappe.db.sql_list(f"select name from `tab{doctype}`")
	else:
		nomi = frappe.db.sql_list(
			f"select name from `tab{doctype}` where name like %(prefisso)s",
			{"prefisso": f"{prefisso}%"},
		)
	ultimo = 0
	for nome in nomi:
		if schema:
			trovato = schema.match(str(nome))
			numero = trovato.group(1) if trovato else None
		else:
			trovato = re.match(r"^(.*?)(\d+)$", str(nome))
			numero = trovato.group(2) if trovato and trovato.group(1) == prefisso else None
		if numero and int(numero) <= tetto:
			ultimo = max(ultimo, int(numero))
	return ultimo


def _contatori(via: dict[str, set[str]]) -> None:
	"""A series the demo numbered goes back to the last number still in use, so the
	centre's first record is not its two-hundredth: never raised, never below what is
	there in any doctype the series numbers, nor below where it was before the demo
	came. One the demo started, with nothing left in it, goes."""
	serie = {riga[0]: riga[1] or 0 for riga in frappe.db.sql("select name, current from `tabSeries`")}
	prima = frappe.parse_json(frappe.db.get_default(registro.SERIE) or "null")
	formati = _formati_numerati()
	per_prefisso: dict[str, set[str]] = defaultdict(set)
	for doctype, nomi in via.items():
		if doctype in formati:
			# the series with no name: every doctype that shares it holds its numbers
			if nomi and "" in serie:
				per_prefisso[""].update(formati)
			continue
		if not _numerato_da_una_serie(doctype):
			continue
		for prefisso in {_serie(nome) for nome in nomi} - {None}:
			if prefisso in serie:
				per_prefisso[prefisso].add(doctype)
	for prefisso, doctypes in per_prefisso.items():
		ultimo = 0
		for doctype in doctypes:
			schema = formati.get(doctype) if prefisso == "" else None
			ultimo = max(ultimo, _ultimo_in_uso(doctype, prefisso, schema, serie[prefisso]))
		if prima is not None and prefisso not in prima and not ultimo:
			frappe.db.sql("delete from `tabSeries` where name = %s", (prefisso,))
			continue
		ultimo = max(ultimo, int((prima or {}).get(prefisso) or 0))
		if ultimo < serie[prefisso]:
			frappe.db.sql("update `tabSeries` set current = %s where name = %s", (ultimo, prefisso))


def _autoincrementi(via: dict[str, set[str]], tabelle: set[str]) -> None:
	"""A table numbered by the database starts again after its last row."""
	for doctype in via:
		if _tabella(doctype) not in tabelle:
			continue
		try:
			if frappe.get_meta(doctype).autoname != "autoincrement":
				continue
		except frappe.DoesNotExistError:
			continue
		# nosemgrep: frappe-sql-format-injection — a DocType of the register, numbered by the database
		ultimo = frappe.db.sql(f"select max(name) from `tab{doctype}`")[0][0] or 0
		try:
			frappe.db.sql_ddl(f"alter table `tab{doctype}` auto_increment = {int(ultimo) + 1}")
		except Exception:
			frappe.log_error(title=f"Demo data: {doctype}'s numbering not reset")
