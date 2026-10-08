# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinical sheets DottorCloud ships, without a site: a sheet in the centre's
language, and the fingerprint that tells a sheet nobody touched from one the
centre changed (`schede_pronte.py` loads them).

A sheet is written once, in English, with its words in Italian beside it
(`dati/schede_pronte.json`, «words»): its title, specialty and description, a
section's title, a question's words, an option, a band, a column, a phrase. A
condition that asks for an option asks for it in the same words, so it is
translated with it; a unit (kg, cm, °) is the same in every language.

Pure: no database, no request. Runs with plain ``unittest``.
"""

from __future__ import annotations

import copy
import hashlib

from crm.moduli import schema as S

#: What a question says, in words to translate.
PAROLE_DEL_CAMPO = ("label", "description", "placeholder", "text", "stop_message", "min_label", "max_label")
PAROLE_DELLA_SCHEDA = ("title", "description", "specialty")
CONDIZIONI = ("show_if", "required_if", "stop_if")


def _condizioni(gruppi):
	for gruppo in gruppi or []:
		for condizione in gruppo or []:
			if isinstance(condizione, dict):
				yield condizione


def _percorri(scheda: dict, cambia) -> dict:
	"""The sheet with every word passed through ``cambia``: a copy."""
	nuova = copy.deepcopy(scheda)
	for chiave in PAROLE_DELLA_SCHEDA:
		if nuova.get(chiave):
			nuova[chiave] = cambia(nuova[chiave])
	for sezione in S.sezioni(nuova.get("schema")):
		for chiave in ("title", "description"):
			if sezione.get(chiave):
				sezione[chiave] = cambia(sezione[chiave])
		for condizione in _condizioni(sezione.get("show_if")):
			if isinstance(condizione.get("value"), str) and condizione["value"] not in ("0", "1"):
				condizione["value"] = cambia(condizione["value"])
		for campo in S.campi_della_sezione(sezione):
			for chiave in PAROLE_DEL_CAMPO:
				if campo.get(chiave):
					campo[chiave] = cambia(campo[chiave])
			for elenco in ("options", "bands", "columns"):
				for voce in campo.get(elenco) or []:
					if voce.get("label"):
						voce["label"] = cambia(voce["label"])
			if campo.get("phrases"):
				campo["phrases"] = [cambia(frase) for frase in campo["phrases"]]
			for nome in CONDIZIONI:
				for condizione in _condizioni(campo.get(nome)):
					# an option asked for by its words: "1" and "0" are a yes and a no
					if isinstance(condizione.get("value"), str) and condizione["value"] not in ("0", "1"):
						condizione["value"] = cambia(condizione["value"])
	return nuova


def parole(scheda: dict) -> list[str]:
	"""Every word of a sheet that is translated, in the order met."""
	trovate: list[str] = []
	_percorri(scheda, lambda testo: trovate.append(testo) or testo)
	return list(dict.fromkeys(trovate))


def nella_lingua(scheda: dict, dizionari: dict, lingua: str) -> dict:
	"""The sheet in ``lingua``: its own English, or the words the file gives for it.
	A word without its translation stays as it is."""
	dizionario = (dizionari or {}).get(lingua) or {}
	return _percorri(scheda, lambda testo: dizionario.get(testo, testo))


def impronta(titolo: str | None, descrizione: str | None, specialita: str | None, schema) -> str:
	"""What a template says, as one fingerprint: its title, description and
	specialty, and its questions as a version would keep them (`normalizza`). The
	same for a sheet just loaded and for the template it became, until somebody
	changes it."""
	parti = S.canonico(
		{
			"title": (titolo or "").strip(),
			"description": (descrizione or "").strip(),
			"specialty": (specialita or "").strip(),
			"schema": S.normalizza(schema),
		}
	)
	return hashlib.sha256(parti.encode("utf-8")).hexdigest()
