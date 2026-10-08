# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A questionnaire's total followed over time: the person's signed forms (and,
with the clinic, the visits on its sheets) of the same template, each score's
total by date, with its band (`andamenti.py` reads them, the person's page
draws them).

A score is worked out by the engine from the answers kept (`schema.valuta`), as
it was when the form was signed: never a number saved apart, which a new
version's bands could not read. A series takes its words and bands from its
newest form: what the template says now.

Pure: no database, no request. Runs with plain ``unittest``.
"""

from __future__ import annotations

from crm.moduli import schema as S


def punteggi(schema, risposte) -> list[dict]:
	"""The totals a signed form has: each score shown, worked out, with its band."""
	stato = S.valuta(schema, risposte or {})
	trovati = []
	for campo in S.campi(schema):
		chiave = campo.get("id")
		if campo.get("type") != "score" or not stato["visible"].get(chiave):
			continue
		valore = stato["values"].get(chiave)
		if valore is None:
			continue
		trovati.append(
			{
				"field": chiave,
				"label": campo.get("label") or "",
				"value": valore,
				"band": stato["bands"].get(chiave),
				"bands": [
					{"from": S.numero(b.get("from")), "to": S.numero(b.get("to")), "label": b.get("label")}
					for b in campo.get("bands") or []
					if isinstance(b, dict)
					and S.numero(b.get("from")) is not None
					and S.numero(b.get("to")) is not None
				],
			}
		)
	return trovati


def serie(compilati: list[dict]) -> list[dict]:
	"""Each score of each template over time. ``compilati``: the signed ones, each
	with ``name``, ``template``, ``title``, ``date``, ``schema``, ``answers`` (and
	``kind``: a form or a visit). A series: ``template``, ``title``, ``field``,
	``label``, ``bands``, and its ``points`` oldest first (``date``, ``value``,
	``band``, ``name``, ``kind``)."""
	per_chiave: dict[tuple, dict] = {}
	for compilato in sorted(compilati, key=lambda c: str(c.get("date") or "")):
		for totale in punteggi(compilato.get("schema"), compilato.get("answers")):
			chiave = (compilato.get("template"), totale["field"])
			voce = per_chiave.setdefault(chiave, {"template": compilato.get("template"), "points": []})
			# the newest form's words and bands: what the template says now
			voce.update(
				title=compilato.get("title") or "",
				field=totale["field"],
				label=totale["label"],
				bands=totale["bands"],
			)
			voce["points"].append(
				{
					"date": compilato.get("date"),
					"value": totale["value"],
					"band": totale["band"],
					"name": compilato.get("name"),
					"kind": compilato.get("kind") or "form",
				}
			)
	return sorted(per_chiave.values(), key=lambda voce: (voce["title"].lower(), voce["label"].lower()))
