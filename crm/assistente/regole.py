# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What the assistant may do, and how its words are kept: the rules, without a site.

The assistant is office work first (design.md, "L'assistente"): a paper form that
becomes a template, then drafts a professional checks. It writes only what was
said or written - no diagnosis, no advice - and nothing it writes is saved by
itself: a person accepts it, changes it, or throws it away, and the register keeps
the model, the provider, the region, the fingerprints of what went in and came out,
the draft and how far the final text went from it.

- **One sentence on its purpose**, everywhere it shows: documentation support; the
  professional reviews the drafts.
- **The mark** a draft carries once a person checks it: an AI draft, checked by
  whom and when (AI Act art. 50; L. 132/2025).
- **What comes back** is text or a JSON object; a model that wraps the JSON in a
  fence or a sentence is read anyway, and a model that returns something else is
  refused, never guessed at.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re

#: The purpose, in the words the design gives it: never a better diagnosis.
SCOPO = "Documentation support: the professional reviews every draft."
#: The mark of a checked draft: who checked it, and when.
SEGNO = "AI draft, checked by {0} on {1}"

ANTHROPIC = "Anthropic"
COMPATIBILE_OPENAI = "OpenAI compatible"
FORNITORI = (ANTHROPIC, COMPATIBILE_OPENAI)

BOZZA, ACCETTATA, SCARTATA, FALLITA = "Draft", "Accepted", "Discarded", "Failed"
#: An answer given to a person as it came, not a draft: the patients' chat.
CONSEGNATA = "Answered"
STATI = (BOZZA, ACCETTATA, SCARTATA, FALLITA, CONSEGNATA)

#: The most text a request sends: a paper form of a few pages, a visit's note.
MAX_TESTO = 60_000

_RECINTO = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def impronta(testo: str | bytes | None) -> str:
	"""The SHA-256 of what went in or came out: the register keeps it, not always the text."""
	dati = testo if isinstance(testo, bytes) else (testo or "").encode("utf-8")
	return hashlib.sha256(dati).hexdigest()


def estrai_json(testo: str | None) -> dict | None:
	"""The JSON object a model answered with: bare, in a fence, or inside a sentence.
	None when there is no object to read."""
	if not isinstance(testo, str) or not testo.strip():
		return None
	candidati = [m.group(1) for m in _RECINTO.finditer(testo)] + [testo]
	for candidato in candidati:
		letto = _oggetto(candidato.strip())
		if letto is not None:
			return letto
	return None


def _oggetto(testo: str) -> dict | None:
	try:
		letto = json.loads(testo)
		return letto if isinstance(letto, dict) else None
	except ValueError:
		pass
	# the first "{" to its matching "}": a sentence around the object is dropped
	inizio = testo.find("{")
	while inizio != -1:
		profondita, in_stringa, escape = 0, False, False
		for i in range(inizio, len(testo)):
			c = testo[i]
			if in_stringa:
				if escape:
					escape = False
				elif c == "\\":
					escape = True
				elif c == '"':
					in_stringa = False
				continue
			if c == '"':
				in_stringa = True
			elif c == "{":
				profondita += 1
			elif c == "}":
				profondita -= 1
				if profondita == 0:
					try:
						letto = json.loads(testo[inizio : i + 1])
						return letto if isinstance(letto, dict) else None
					except ValueError:
						break
		inizio = testo.find("{", inizio + 1)
	return None


def differenza(bozza: str | None, finale: str | None) -> str:
	"""How the final text went from the draft, line by line: what the monthly
	review reads."""
	return "\n".join(
		difflib.unified_diff(
			(bozza or "").splitlines(),
			(finale or "").splitlines(),
			fromfile="draft",
			tofile="final",
			lineterm="",
		)
	)


def quanto_cambiata(bozza: str | None, finale: str | None) -> float:
	"""0 when the draft was taken as it was, 1 when nothing of it stayed.

	Word by word, and every word counts: on a long text difflib would otherwise
	take the commonest letters for noise, and two names filled in would read as
	a letter rewritten."""
	if not (bozza or finale):
		return 0.0
	confronto = difflib.SequenceMatcher(None, (bozza or "").split(), (finale or "").split(), autojunk=False)
	return round(1 - confronto.ratio(), 3)


def taglia(testo: str | None, massimo: int = MAX_TESTO) -> str:
	"""What is sent, at most ``massimo`` characters: a long document is cut, and says so."""
	testo = testo or ""
	if len(testo) <= massimo:
		return testo
	return testo[:massimo] + "\n[…]"


def pronto(abilitato, fornitore, indirizzo, modello, senza_conservazione) -> list[str]:
	"""What is missing before the assistant may run: nothing, or the list."""
	mancano = []
	if not abilitato:
		mancano.append("The assistant is off")
	if fornitore not in FORNITORI:
		mancano.append("Choose the provider")
	if not (indirizzo or "").startswith("https://") and not _locale(indirizzo):
		mancano.append("The endpoint is an https address")
	if not modello:
		mancano.append("Choose the model")
	if not senza_conservazione:
		mancano.append("The contract says the provider keeps nothing and trains on nothing")
	return mancano


def _locale(indirizzo: str | None) -> bool:
	"""A model on the centre's own machine may speak plain http."""
	return bool(re.match(r"^http://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?(/|$)", indirizzo or ""))
