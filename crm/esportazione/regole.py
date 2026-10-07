# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What goes in the centre's archive, without a site: which document types, a
record as a row of a table, the names inside the ZIP. Tested with plain
`unittest`."""

from __future__ import annotations

import csv
import datetime
import decimal
import io
import json
import re

#: The framework's document types that hold the centre's data with DottorCloud's:
#: the address book, emails and the comments on records, assignments, the files'
#: records.
DEL_FRAMEWORK = ("Contact", "Address", "Communication", "Comment", "ToDo", "File")

#: DottorCloud's document types that are no data of the centre's: how a browser is
#: reached, links that enter the area once, what the demo made, the half-way states
#: of a sign-up. They hold keys or fingerprints, never anything a centre needs elsewhere.
SOLO_PER_LA_MACCHINA = frozenset(
	{
		"CRM Push Subscription",
		"CRM Area Link",
		"CRM Demo Record",
		"WhatsApp Signup Session",
		"CRM Visitor Session",
	}
)

#: Fields of the framework every record has that say nothing to whoever reads it
#: elsewhere.
CAMPI_TECNICI = frozenset({"docstatus", "idx", "_user_tags", "_comments", "_assign", "_liked_by", "_seen"})

#: Kinds of field that hold no value: layout, or a password the framework keeps apart.
SENZA_VALORE = frozenset(
	{
		"Section Break",
		"Column Break",
		"Tab Break",
		"HTML",
		"Button",
		"Image",
		"Fold",
		"Heading",
		"Password",
		"Table",
		"Table MultiSelect",
	}
)


def da_esportare(tipi: list[dict]) -> list[str]:
	"""The document types that go in the archive, from their metas
	(`name`, `module_app`, `istable`, `issingle`, `is_virtual`): DottorCloud's
	and the framework's of `DEL_FRAMEWORK`; never a child table (it goes with its
	record), a single (a settings page, with its keys), a virtual one, nor what is
	only for the machine. In name order, so two archives compare."""
	scelti = []
	for tipo in tipi:
		nome = tipo["name"]
		if tipo.get("istable") or tipo.get("issingle") or tipo.get("is_virtual"):
			continue
		if nome in SOLO_PER_LA_MACCHINA:
			continue
		if tipo.get("module_app") == "crm" or nome in DEL_FRAMEWORK:
			scelti.append(nome)
	return sorted(set(scelti))


def nome_di_file(testo: str) -> str:
	"""A name a ZIP and every system take: letters, digits, dots, dashes; the
	rest an underscore. «CRM Lead» is «crm-lead», «Rossi/Maria 1.pdf»
	«Rossi_Maria_1.pdf»."""
	pulito = re.sub(r"[^\w.\-]+", "_", (testo or "").strip(), flags=re.UNICODE).strip("._")
	return pulito[:120] or "senza-nome"


def nome_del_tipo(doctype: str) -> str:
	return nome_di_file(doctype.lower().replace(" ", "-"))


def valore(v):
	"""A value as JSON writes it: a date in ISO, a decimal as a number."""
	if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
		return v.isoformat()
	if isinstance(v, datetime.timedelta):
		return str(v)
	if isinstance(v, decimal.Decimal):
		return float(v)
	if isinstance(v, bytes):
		return v.decode("utf-8", "replace")
	return v


def riga(record: dict, campi: list[str], figli: set[str]) -> dict:
	"""A record as it goes in the archive: its own fields, with its child tables'
	rows as lists of their own fields; never what the framework keeps for itself."""
	fuori = {}
	for campo in ["name", "creation", "modified", "owner", "modified_by", *campi]:
		if campo in CAMPI_TECNICI or campo not in record:
			continue
		v = record[campo]
		if campo in figli:
			fuori[campo] = [
				{
					k: valore(x)
					for k, x in figlio.items()
					if k not in CAMPI_TECNICI and not k.startswith("parent")
				}
				for figlio in (v or [])
			]
		else:
			fuori[campo] = valore(v)
	return fuori


def jsonl(righe: list[dict]) -> str:
	"""One record a line: a program reads a big table a line at a time."""
	return "".join(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n" for r in righe)


def tabella(righe: list[dict], intestazione: list[str]) -> str:
	"""The records as a table Excel opens: the fields as columns, a child table's
	rows as their count (they are whole in the JSON); a semicolon and a BOM, as an
	Italian Excel reads it."""
	uscita = io.StringIO()
	scrittore = csv.writer(uscita, delimiter=";", lineterminator="\r\n")
	scrittore.writerow(intestazione)
	for r in righe:
		celle = []
		for campo in intestazione:
			v = r.get(campo)
			if isinstance(v, list):
				v = len(v)
			elif isinstance(v, dict):
				v = json.dumps(v, ensure_ascii=False)
			celle.append("" if v is None else v)
		scrittore.writerow(celle)
	return "﻿" + uscita.getvalue()


def percorso_del_file(doctype: str | None, nome: str | None, file_name: str, file_id: str) -> str:
	"""Where a file goes in the archive: by the record it is attached to, its own
	name kept, the File's id in front so two files of one name never collide."""
	cartella = f"{nome_del_tipo(doctype)}/{nome_di_file(nome)}" if doctype and nome else "non-allegati"
	return f"file/{cartella}/{nome_di_file(file_id)[:12]}-{nome_di_file(file_name)}"


LEGGIMI = """Questo archivio contiene i dati del centro come li tiene {marchio}, il {giorno}.

- dati/<tipo>.jsonl: ogni documento su una riga, con le sue tabelle dentro. È il formato
  completo, da dare al prossimo programma.
- tabelle/<tipo>.csv: gli stessi documenti come tabella, da aprire con Excel; le righe
  delle tabelle interne sono contate, e stanno intere nel .jsonl.
- file/: i file allegati, in una cartella per documento.
- elenco.json: quanti documenti di ogni tipo e quali file.

Contiene dati sanitari: va conservato con le stesse cautele della cartella clinica.

This archive holds the centre's data as {marchio} keeps them, on {giorno}: the full
records in dati/*.jsonl, the same as tables in tabelle/*.csv, the attached files in file/.
It holds health data.
"""
