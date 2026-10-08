# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a list offers to choose (docs/crm/55): the fields one filters
by, sorts by, groups by, adds as a column or onto a board's card.

Not every field a document keeps. Never what only the machine reads: a code, a
series, another system's id, the framework's own bookkeeping. Never a kind of
value the use cannot take: a long text to sort by, an amount or a moment to the
second to group by. Each field once, in the reader's words, told apart from
another of the same name by where it sits («Sorgente (Primo contatto)»).

No site: a document's fields come in as plain dicts, in their order, with the
section and the tab they sit in (`crm.liste.campi` reads them off the meta),
and the translator is handed in."""

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

_FILTRO = frozenset(
	{
		"Check",
		"Currency",
		"Data",
		"Date",
		"Datetime",
		"Duration",
		"Dynamic Link",
		"Float",
		"Int",
		"Link",
		"Long Text",
		"Percent",
		"Rating",
		"Select",
		"Small Text",
		"Text",
		"Text Editor",
	}
)

# the kinds of value each use takes
TIPI = {
	"filtro": _FILTRO,
	# what has an order of its own: never a long text, a picture, a code of
	# whatever document a row points at
	"ordine": frozenset(
		{
			"Check",
			"Currency",
			"Data",
			"Date",
			"Datetime",
			"Duration",
			"Float",
			"Int",
			"Link",
			"Percent",
			"Rating",
			"Select",
			"Time",
		}
	),
	# a group is a value many rows share: a choice, a link, a day; never an
	# amount, a moment to the second, a text
	"gruppo": frozenset({"Check", "Data", "Date", "Link", "Select"}),
	# a column or a card shows whatever a filter reads, and a time
	"colonna": _FILTRO | {"Time"},
	# a record's own layout (its fields, its side panel, a table's columns)
	# takes any kind of field: the editor that draws it says which it can't
	"scheda": None,
}
USI = tuple(TIPI)

# what lays a document out, never a field of it
STRUTTURA = frozenset({"Column Break", "Section Break", "Tab Break"})

# what no list offers, on any document: its code and its series, the
# framework's bookkeeping (comments, tags, who saw it, a child's place)
DELLA_MACCHINA = frozenset(
	{
		"_comments",
		"_seen",
		"_user_tags",
		"docstatus",
		"idx",
		"name",
		"naming_series",
		"parent",
		"parentfield",
		"parenttype",
	}
)


@dataclass(frozen=True)
class Standard:
	"""One of the framework's own columns, as the lists name it."""

	fieldname: str
	fieldtype: str
	label: str
	options: str | None = None


# the framework's own columns, in the words the lists read them by: «Created
# By» is who made the record (never «Owner», which the lists read as the
# person's or the deal's owner)
STANDARD = {
	s.fieldname: s
	for s in (
		Standard("_assign", "Text", "Assigned To"),
		Standard("owner", "Link", "Created By", "User"),
		Standard("creation", "Datetime", "Created On"),
		Standard("modified_by", "Link", "Last Modified By", "User"),
		Standard("modified", "Datetime", "Last Modified"),
		# the heart a list draws in a column of its own
		Standard("_liked_by", "Data", "Favourite"),
	)
}

# the names the framework gave three of them, still in the views lists saved:
# «Owner» read as the person's or the deal's owner, «Like» as the filter's
# «like»
DI_PRIMA = {"owner": "Owner", "modified_by": "Modified By", "_liked_by": "Like"}

# which of them each use takes, after the document's own fields: whom a record
# is assigned to is a list, the same on hardly two records, never a group; the
# heart is a column, filtered by its own heading
STANDARD_PER_USO = {
	"filtro": ("_assign", "owner", "creation", "modified_by", "modified"),
	"ordine": ("creation", "modified", "owner", "modified_by"),
	"gruppo": ("owner",),
	"colonna": ("_assign", "owner", "creation", "modified_by", "modified", "_liked_by"),
	"scheda": (),
}


def scegli(
	campi: Iterable[dict[str, Any]],
	uso: str,
	t: Callable[[str], str] = str,
	togli: Iterable[str] = (),
) -> list[dict[str, Any]]:
	"""The fields `uso` offers out of a document's `campi` (dicts with
	`fieldname`, `fieldtype`, `label`, `options`, `hidden`, and the labels of
	the `sezione` and `scheda` they sit in), then the framework's own the use
	takes. `togli` names what this document keeps only for the machine. Each
	comes back as `fieldname`, `fieldtype`, `label` (in the reader's words, by
	`t`) and `options`."""
	if uso not in TIPI:
		raise ValueError(f"Unknown use: {uso}")
	tipi = TIPI[uso]
	togli = set(togli)
	scelti: list[dict[str, Any]] = []
	visti: set[str] = set()
	for campo in campi:
		nome = campo.get("fieldname")
		if (
			not nome
			or not campo.get("label")
			or campo.get("hidden")
			or nome in visti
			or nome in DELLA_MACCHINA
			or nome in togli
			or campo.get("fieldtype") in STRUTTURA
			or (tipi is not None and campo.get("fieldtype") not in tipi)
		):
			continue
		visti.add(nome)
		scelti.append(
			{
				"fieldname": nome,
				"fieldtype": campo["fieldtype"],
				"label": t(campo["label"]),
				"options": campo.get("options"),
				"_sezione": campo.get("sezione"),
				"_scheda": campo.get("scheda"),
			}
		)

	propri = {s["label"] for s in scelti}
	for nome in STANDARD_PER_USO[uso]:
		standard = STANDARD[nome]
		etichetta = t(standard.label)
		# the document's own field of that name is the one meant: a task's
		# «Assigned To» is whom it is for, not the framework's assignments
		if nome in visti or nome in togli or etichetta in propri:
			continue
		scelti.append(
			{
				"fieldname": nome,
				"fieldtype": standard.fieldtype,
				"label": etichetta,
				"options": standard.options,
			}
		)
	return distinti(scelti, t)


def distinti(scelti: list[dict[str, Any]], t: Callable[[str], str] = str) -> list[dict[str, Any]]:
	"""Fields of the same name told apart by the section they sit in
	(«Sorgente (Primo contatto)», «Sorgente (Ultimo contatto)»), the one that
	sits straight in its tab keeping its name («Sorgente»); what still shares a
	name, by its tab."""
	quanti = Counter(s["label"] for s in scelti)
	for s in scelti:
		if quanti[s["label"]] > 1 and s.get("_sezione"):
			s["label"] = f"{s['label']} ({t(s['_sezione'])})"
			s["_detto"] = True
	quanti = Counter(s["label"] for s in scelti)
	for s in scelti:
		if quanti[s["label"]] > 1 and s.get("_scheda") and not s.get("_detto"):
			s["label"] = f"{s['label']} ({t(s['_scheda'])})"
	for s in scelti:
		for chiave in ("_sezione", "_scheda", "_detto"):
			s.pop(chiave, None)
	return scelti


def nome_della_colonna(chiave: str | None, etichetta: str | None) -> str | None:
	"""A saved column's name: one of the framework's own columns, saved under
	the name the framework gave it, reads as the lists name it; any other as it
	was written."""
	if chiave in DI_PRIMA and etichetta == DI_PRIMA[chiave]:
		return STANDARD[chiave].label
	return etichetta
