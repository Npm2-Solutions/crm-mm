# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The form templates engine: what a template may contain, and what answers mean.

A template is a versioned schema - sections, fields, the text to read, the
components - and a form the patient fills, a clinical sheet and a plan are the
same object with three uses (docs/verticali/clinica/design.md, "Il motore dei
modelli"). This module is the one place that says what a schema may hold and what
a set of answers means for it: which questions show, which are required, what the
calculations give, when to stop and tell the operator.

**The same rules run in the browser** (`frontend/src/utils/moduli.js`), and
`tests/casi_schema.json` holds the cases both must agree on: a form is not saved
incomplete by any road, and what the person saw while filling it is what the
server decides.

Three rules keep the two in step, and the logic simple:

* **A question looks back.** Whether a section or a question shows, a calculation
  and a score may only use the answers that come before them. One pass, in order,
  settles everything: no loops, no order to guess. "Required if" and "stop if"
  may look anywhere, the question itself included (the pacemaker before the shock
  waves), because they change no answer.
* **A hidden answer does not count.** It is not shown, not required, not used by
  what follows, and not kept.
* **Numbers are plain floats**, rounded the same way on both sides.

Pure: no database, no request. Runs with plain ``unittest``.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import date

#: What an answer is, for conditions and for cleaning.
TESTO = "text"
NUMERO = "number"
SCELTA = "choice"
BOOLEANO = "bool"
DATA = "date"
TABELLA = "table"
LATI = "sides"
FILE = "file"
FIRMA = "signature"

#: How a component may appear in a condition.
TUTTI_GLI_OPERATORI = "all"
SOLO_PRESENZA = "presence"

OPERATORI = ("equals", "not_equals", "contains", "is_set", "is_not_set", "greater_than", "less_than")
SENZA_VALORE = ("is_set", "is_not_set")

FIRMATARI = ("patient", "operator", "guardian")
#: The level a signature needs is the template's choice, not the operator's
#: (design.md, "La firma"): simple for notices and questionnaires, advanced for
#: an informed consent, qualified for the professional's countersignature.
LIVELLI_FIRMA = ("simple", "advanced", "qualified")
TIPI_COLONNA = ("text", "number", "date", "yesno")
TIPI_LATO = ("number", "text")

MAX_SEZIONI = 50
MAX_CAMPI = 400
MAX_OPZIONI = 100
MAX_COLONNE = 20
MAX_RIGHE = 200
MAX_TESTO = 20000
MAX_DECIMALI = 6

_ID = re.compile(r"^[a-z][a-z0-9_]{0,59}$")
_NUMERO_TESTO = re.compile(r"^\s*-?[0-9]+(?:[.,][0-9]+)?\s*$")
_DATA = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def _testo(valore) -> str:
	"""Words written in the schema, or nothing: a number where words go is not words."""
	return valore.strip() if isinstance(valore, str) else ""


def _id_valido(valore) -> bool:
	return isinstance(valore, str) and bool(_ID.match(valore))


def _lista(valore) -> list:
	"""A list in the schema, or none: an option list that is a number lists nothing."""
	return valore if isinstance(valore, list) else []


def _dizionario(valore) -> dict:
	return valore if isinstance(valore, dict) else {}


def _cifra(carattere: str) -> bool:
	# "0" to "9" only: str.isdigit() would take "²" and other digits the browser does not
	return "0" <= carattere <= "9"


#: What every field may carry, whatever its type.
PROPRIETA_COMUNI = [
	"id",
	"type",
	"label",
	"description",
	"required",
	"show_if",
	"required_if",
	"stop_if",
	"stop_message",
]
PROPRIETA_SEZIONE = ("id", "title", "description", "show_if", "fields")


@dataclass(frozen=True)
class Componente:
	tipo: str
	etichetta: str
	#: what its answer is; None for what only shows (a text to read)
	valore: str | None
	#: whoever fills the form answers it; a calculation is worked out instead
	risposta: bool = True
	#: how a condition may ask about it
	condizione: str | None = TUTTI_GLI_OPERATORI
	#: a number a calculation or a score may use
	numerico: bool = False
	#: what it carries beyond the common properties
	proprieta: tuple[str, ...] = ()


_componenti: dict[str, Componente] = {}


def registra_componente(componente: Componente) -> None:
	"""Another module's component: the clinic's body map and clinical photo, the
	plans' meal and exercise. Their rules are theirs; this module only needs to
	know what kind of answer they give."""
	_componenti[componente.tipo] = componente


def registra_proprieta_comune(nome: str) -> None:
	"""A property every field may carry, for a module that reads it (the clinic's
	"goes to the patient's summary")."""
	if nome not in PROPRIETA_COMUNI:
		PROPRIETA_COMUNI.append(nome)


def componenti() -> list[Componente]:
	return list(_componenti.values())


def componente(tipo) -> Componente | None:
	return _componenti.get(tipo) if isinstance(tipo, str) else None


for _c in (
	Componente("text", "Text", TESTO, proprieta=("placeholder", "multiline", "phrases")),
	Componente(
		"number",
		"Number",
		NUMERO,
		numerico=True,
		proprieta=("placeholder", "unit", "min", "max", "decimals"),
	),
	Componente("choice", "Choice", SCELTA, proprieta=("options", "multiple", "display")),
	Componente("yesno", "Yes or no", BOOLEANO, proprieta=("scores",)),
	Componente("date", "Date", DATA),
	Componente("scale", "Scale", NUMERO, numerico=True, proprieta=("min", "max", "min_label", "max_label")),
	Componente("table", "Table", TABELLA, condizione=SOLO_PRESENZA, proprieta=("columns", "max_rows")),
	Componente("paragraph", "Text to read", None, risposta=False, condizione=None, proprieta=("text",)),
	Componente(
		"calc",
		"Calculation",
		NUMERO,
		risposta=False,
		numerico=True,
		proprieta=("formula", "decimals", "unit"),
	),
	Componente("score", "Score", NUMERO, risposta=False, numerico=True, proprieta=("sources", "bands")),
	Componente("sides", "Left and right", LATI, condizione=SOLO_PRESENZA, proprieta=("input", "unit")),
	Componente("attachment", "Attachment", FILE, condizione=SOLO_PRESENZA, proprieta=("accept", "multiple")),
	Componente("signature", "Signature", FIRMA, condizione=SOLO_PRESENZA, proprieta=("signer", "level")),
	# the words are the register's: frozen into the version when it is published
	Componente(
		"consent",
		"Consent",
		BOOLEANO,
		proprieta=("consent_type", "must_accept", "text", "text_version"),
	),
):
	registra_componente(_c)


# ------------------------------------------------------------------ the errors


@dataclass(frozen=True)
class Errore:
	"""What is wrong, with a code the browser and the tests agree on, and English
	words to translate with their arguments."""

	codice: str
	campo: str | None
	messaggio: str
	argomenti: tuple = ()

	def testo(self, traduci=lambda s: s) -> str:
		return traduci(self.messaggio).format(*self.argomenti)

	def come_dict(self, traduci=lambda s: s) -> dict:
		return {"code": self.codice, "field": self.campo, "message": self.testo(traduci)}


# ------------------------------------------------------------------ the values


def vuoto(valore) -> bool:
	"""Not answered. A "no" is an answer; an empty row or side is not."""
	if valore is None or valore == "":
		return True
	if isinstance(valore, list):
		return len(valore) == 0
	if isinstance(valore, dict):
		return all(vuoto(v) for v in valore.values())
	return False


def numero(valore) -> float | None:
	"""A number, from a number or from what a person typed ("70", "70,5")."""
	if isinstance(valore, bool) or valore is None:
		return None
	if isinstance(valore, int | float):
		try:
			return float(valore) if math.isfinite(valore) else None
		except OverflowError:  # an integer too big for a float: Infinity in the browser
			return None
	if isinstance(valore, str) and _NUMERO_TESTO.match(valore):
		return float(valore.strip().replace(",", "."))
	return None


def _intero_se_puo(x: float) -> int | float:
	return int(x) if float(x).is_integer() else x


def arrotonda(x: float, decimali: int) -> float:
	"""Half up, the same in the browser: `Math.floor(x * 10 ** d + 0.5) / 10 ** d`.
	Python's own `round` rounds half to even, and the two would disagree."""
	decimali = max(0, min(int(decimali), 10))
	fattore = 10**decimali
	scalato = x * fattore + 0.5
	if not math.isfinite(scalato):
		return x
	return math.floor(scalato) / fattore


# ------------------------------------------------------------------ the schema


def sezioni(schema) -> list[dict]:
	if not isinstance(schema, dict) or not isinstance(schema.get("sections"), list):
		return []
	return [s for s in schema["sections"] if isinstance(s, dict)]


def campi_della_sezione(sezione: dict) -> list[dict]:
	campi = sezione.get("fields")
	return [c for c in campi if isinstance(c, dict)] if isinstance(campi, list) else []


def campi(schema) -> list[dict]:
	"""Every field, in the order a person meets them."""
	return [campo for sezione in sezioni(schema) for campo in campi_della_sezione(sezione)]


# ------------------------------------------------------------------ conditions


def _come_testo(valore) -> str:
	if valore is None:
		return ""
	if isinstance(valore, bool):
		return "1" if valore else "0"
	if isinstance(valore, list | dict):
		# a condition compares single answers: a list has no words to compare
		return ""
	n = numero(valore)
	if n is not None and not isinstance(valore, str):
		return str(_intero_se_puo(n))
	return str(valore).strip()


def _uguale(attuale, atteso) -> bool:
	if isinstance(attuale, list | dict) or isinstance(atteso, list | dict):
		return False
	if isinstance(attuale, bool):
		return _come_testo(attuale) == _come_testo(atteso)
	a, b = numero(attuale), numero(atteso)
	if a is not None and b is not None:
		return a == b
	return _come_testo(attuale) == _come_testo(atteso)


def _ordina(attuale, atteso) -> int | None:
	"""-1, 0, 1 between two numbers or two dates; None when they do not compare."""
	a, b = numero(attuale), numero(atteso)
	if a is not None and b is not None:
		return (a > b) - (a < b)
	if isinstance(attuale, str) and isinstance(atteso, str):
		x, y = attuale.strip(), atteso.strip()
		if _DATA.match(x) and _DATA.match(y):
			return (x > y) - (x < y)
	return None


def condizione_vera(condizione: dict, valori: dict) -> bool:
	operatore = condizione.get("operator") or "equals"
	attuale = valori.get(condizione.get("field"))
	atteso = condizione.get("value")
	if operatore == "is_set":
		return not vuoto(attuale)
	if operatore == "is_not_set":
		return vuoto(attuale)
	if vuoto(attuale):
		# nothing answered is not equal, not different, not bigger: the question
		# that depends on it waits for the answer
		return False
	if isinstance(atteso, list | dict):
		# a condition compares with one value, as the builder writes it
		return False
	if isinstance(attuale, list):
		if operatore == "equals":
			return any(_uguale(v, atteso) for v in attuale)
		if operatore == "not_equals":
			return not any(_uguale(v, atteso) for v in attuale)
		if operatore == "contains":
			cercato = _come_testo(atteso).lower()
			return any(cercato in _come_testo(v).lower() for v in attuale)
		return False
	if operatore == "equals":
		return _uguale(attuale, atteso)
	if operatore == "not_equals":
		return not _uguale(attuale, atteso)
	if operatore == "contains":
		return _come_testo(atteso).lower() in _come_testo(attuale).lower()
	if operatore in ("greater_than", "less_than"):
		ordine = _ordina(attuale, atteso)
		if ordine is None:
			return False
		return ordine > 0 if operatore == "greater_than" else ordine < 0
	return False


def soddisfatta(gruppi, valori: dict) -> bool:
	"""Groups of conditions, as the automations write them: any group whose
	conditions all hold. None or nothing is always."""
	gruppi = pulisci_gruppi(gruppi)
	if not gruppi:
		return True
	return any(all(condizione_vera(c, valori) for c in gruppo) for gruppo in gruppi)


def pulisci_gruppi(gruppi) -> list[list[dict]]:
	"""The groups with a question in each row: an empty row or group, which the
	builder leaves while one is being written, asks nothing."""
	if not isinstance(gruppi, list):
		return []
	puliti = []
	for gruppo in gruppi:
		if not isinstance(gruppo, list):
			continue
		righe = [c for c in gruppo if isinstance(c, dict) and isinstance(c.get("field"), str) and c["field"]]
		if righe:
			puliti.append(righe)
	return puliti


def campi_delle_condizioni(gruppi) -> list[str]:
	return [
		c.get("field")
		for gruppo in (gruppi or [])
		if isinstance(gruppo, list)
		for c in gruppo
		if isinstance(c, dict) and c.get("field")
	]


# ------------------------------------------------------------------ formulas


class ErroreFormula(ValueError):
	pass


FUNZIONI = {"round": (1, 2), "min": (1, 20), "max": (1, 20), "abs": (1, 1), "sqrt": (1, 1)}
_SIMBOLI = "+-*/^(),"


def _gettoni(formula: str) -> list[tuple[str, str]]:
	gettoni = []
	i = 0
	while i < len(formula):
		carattere = formula[i]
		if carattere.isspace():
			i += 1
			continue
		if _cifra(carattere):
			fine = i
			while fine < len(formula) and _cifra(formula[fine]):
				fine += 1
			if fine < len(formula) - 1 and formula[fine] == "." and _cifra(formula[fine + 1]):
				fine += 1
				while fine < len(formula) and _cifra(formula[fine]):
					fine += 1
			gettoni.append(("num", formula[i:fine]))
			i = fine
			continue
		if "a" <= carattere <= "z":
			fine = i
			while fine < len(formula) and (
				"a" <= formula[fine] <= "z" or _cifra(formula[fine]) or formula[fine] == "_"
			):
				fine += 1
			gettoni.append(("nome", formula[i:fine]))
			i = fine
			continue
		if carattere in _SIMBOLI:
			gettoni.append(("simbolo", carattere))
			i += 1
			continue
		raise ErroreFormula(f"unexpected {carattere!r}")
	return gettoni


class _Lettore:
	def __init__(self, gettoni):
		self.gettoni = gettoni
		self.i = 0

	def guarda(self):
		return self.gettoni[self.i] if self.i < len(self.gettoni) else (None, None)

	def prendi(self):
		gettone = self.guarda()
		self.i += 1
		return gettone

	def aspetta(self, simbolo: str):
		tipo, valore = self.prendi()
		if tipo != "simbolo" or valore != simbolo:
			raise ErroreFormula(f"expected {simbolo!r}")

	# espressione := termine (("+" | "-") termine)*
	def espressione(self):
		nodo = self.termine()
		while self.guarda() in (("simbolo", "+"), ("simbolo", "-")):
			operatore = self.prendi()[1]
			nodo = ("bin", operatore, nodo, self.termine())
		return nodo

	# termine := unario (("*" | "/") unario)*
	def termine(self):
		nodo = self.unario()
		while self.guarda() in (("simbolo", "*"), ("simbolo", "/")):
			operatore = self.prendi()[1]
			nodo = ("bin", operatore, nodo, self.unario())
		return nodo

	# unario := "-" unario | potenza   (so -2^2 is -(2^2), as on paper)
	def unario(self):
		if self.guarda() == ("simbolo", "-"):
			self.prendi()
			return ("neg", self.unario())
		return self.potenza()

	# potenza := primario ("^" unario)?   (right-associative)
	def potenza(self):
		nodo = self.primario()
		if self.guarda() == ("simbolo", "^"):
			self.prendi()
			return ("bin", "^", nodo, self.unario())
		return nodo

	def primario(self):
		tipo, valore = self.prendi()
		if tipo == "num":
			return ("num", float(valore))
		if tipo == "nome":
			if self.guarda() == ("simbolo", "("):
				if valore not in FUNZIONI:
					raise ErroreFormula(f"unknown function {valore}")
				self.prendi()
				argomenti = [self.espressione()]
				while self.guarda() == ("simbolo", ","):
					self.prendi()
					argomenti.append(self.espressione())
				self.aspetta(")")
				minimo, massimo = FUNZIONI[valore]
				if not minimo <= len(argomenti) <= massimo:
					raise ErroreFormula(f"{valore} takes {minimo} to {massimo} values")
				return ("fn", valore, argomenti)
			return ("var", valore)
		if (tipo, valore) == ("simbolo", "("):
			nodo = self.espressione()
			self.aspetta(")")
			return nodo
		raise ErroreFormula("incomplete formula")


def leggi_formula(formula: str):
	"""The formula as a tree; ErroreFormula when it is not one."""
	if not isinstance(formula, str) or not formula.strip():
		raise ErroreFormula("empty formula")
	if len(formula) > 500:
		raise ErroreFormula("formula too long")
	lettore = _Lettore(_gettoni(formula))
	albero = lettore.espressione()
	if lettore.i != len(lettore.gettoni):
		raise ErroreFormula("unexpected text after the formula")
	return albero


def riferimenti(albero) -> list[str]:
	if albero[0] == "var":
		return [albero[1]]
	if albero[0] == "neg":
		return riferimenti(albero[1])
	if albero[0] == "bin":
		return riferimenti(albero[2]) + riferimenti(albero[3])
	if albero[0] == "fn":
		return [nome for argomento in albero[2] for nome in riferimenti(argomento)]
	return []


def _finito(x: float) -> float | None:
	return x if math.isfinite(x) else None


def _calcola(albero, valori: dict) -> float | None:
	tipo = albero[0]
	if tipo == "num":
		return albero[1]
	if tipo == "var":
		return numero(valori.get(albero[1]))
	if tipo == "neg":
		x = _calcola(albero[1], valori)
		return None if x is None else -x
	if tipo == "bin":
		a, b = _calcola(albero[2], valori), _calcola(albero[3], valori)
		if a is None or b is None:
			return None
		operatore = albero[1]
		if operatore == "+":
			return _finito(a + b)
		if operatore == "-":
			return _finito(a - b)
		if operatore == "*":
			return _finito(a * b)
		if operatore == "/":
			return None if b == 0 else _finito(a / b)
		try:
			return _finito(math.pow(a, b))
		except (ValueError, OverflowError):
			return None
	argomenti = [_calcola(argomento, valori) for argomento in albero[2]]
	if any(x is None for x in argomenti):
		return None
	nome = albero[1]
	if nome == "round":
		return arrotonda(argomenti[0], int(argomenti[1]) if len(argomenti) > 1 else 0)
	if nome == "min":
		return min(argomenti)
	if nome == "max":
		return max(argomenti)
	if nome == "abs":
		return abs(argomenti[0])
	return math.sqrt(argomenti[0]) if argomenti[0] >= 0 else None


def calcola(formula: str, valori: dict, decimali=None) -> int | float | None:
	"""What the formula gives with these answers; None while something it uses is
	missing, or when it has no answer (a division by zero)."""
	try:
		risultato = _calcola(leggi_formula(formula), valori)
	except ErroreFormula:
		return None
	if risultato is None:
		return None
	decimali = numero(decimali)
	return _intero_se_puo(arrotonda(risultato, 2 if decimali is None else decimali))


# ------------------------------------------------------------------ scores


def _punti_di(campo: dict, valore) -> float | None:
	tipo = campo.get("type")
	if tipo == "choice":
		punti = {
			o["label"]: numero(o.get("score")) or 0.0
			for o in _lista(campo.get("options"))
			if isinstance(o, dict) and isinstance(o.get("label"), str)
		}
		scelti = valore if isinstance(valore, list) else [valore]
		return float(sum(punti.get(v, 0.0) if isinstance(v, str) else 0.0 for v in scelti))
	if tipo == "yesno":
		punti = _dizionario(campo.get("scores"))
		return numero(punti.get("yes" if valore else "no")) or 0.0
	return numero(valore)


def punteggio(campo: dict, valori: dict, visibili: dict, per_id: dict) -> int | float | None:
	"""The sum of the answers it counts; None while one it counts is missing."""
	totale = 0.0
	contati = 0
	for fonte in _lista(campo.get("sources")):
		if not isinstance(fonte, str) or not visibili.get(fonte) or fonte not in per_id:
			continue
		valore = valori.get(fonte)
		if vuoto(valore):
			return None
		punti = _punti_di(per_id[fonte], valore)
		if punti is None:
			return None
		totale += punti
		contati += 1
	return _intero_se_puo(arrotonda(totale, 2)) if contati else None


def fascia(campo: dict, totale) -> str | None:
	if totale is None:
		return None
	for banda in _lista(campo.get("bands")):
		if not isinstance(banda, dict):
			continue
		da, a = numero(banda.get("from")), numero(banda.get("to"))
		if da is not None and a is not None and da <= totale <= a:
			return banda.get("label") or None
	return None


# ------------------------------------------------------------------ evaluation


def valuta(schema, valori: dict | None) -> dict:
	"""What these answers mean for the schema: what shows, what is worked out,
	what is required and missing, where to stop and tell the operator."""
	valori = valori or {}
	per_id = {campo["id"]: campo for campo in campi(schema) if isinstance(campo.get("id"), str)}
	effettivi: dict = {}
	visibili: dict = {}
	sezioni_visibili: dict = {}
	fasce: dict = {}
	for sezione in sezioni(schema):
		vista = soddisfatta(sezione.get("show_if"), effettivi)
		if isinstance(sezione.get("id"), str):
			sezioni_visibili[sezione["id"]] = vista
		for campo in campi_della_sezione(sezione):
			chiave = campo.get("id")
			if not isinstance(chiave, str):
				continue
			tipo = componente(campo.get("type"))
			visto = vista and soddisfatta(campo.get("show_if"), effettivi)
			visibili[chiave] = visto
			valore = None
			if visto and tipo is not None and tipo.valore is not None:
				if campo.get("type") == "calc":
					valore = calcola(campo.get("formula"), effettivi, campo.get("decimals"))
				elif campo.get("type") == "score":
					valore = punteggio(campo, effettivi, visibili, per_id)
					fasce[chiave] = fascia(campo, valore)
				else:
					valore = valori.get(chiave)
			effettivi[chiave] = valore

	richiesti, mancanti, fermi = [], [], []
	for campo in campi(schema):
		chiave = campo.get("id")
		tipo = componente(campo.get("type"))
		if not isinstance(chiave, str) or not visibili.get(chiave) or tipo is None:
			continue
		if tipo.risposta and (
			campo.get("required")
			or campo.get("must_accept")
			or (campo.get("required_if") and soddisfatta(campo.get("required_if"), effettivi))
		):
			richiesti.append(chiave)
			valore = effettivi.get(chiave)
			if vuoto(valore) or (campo.get("must_accept") and valore is not True):
				mancanti.append(chiave)
		if campo.get("stop_if") and soddisfatta(campo.get("stop_if"), effettivi):
			fermi.append({"field": chiave, "message": campo.get("stop_message") or ""})

	return {
		"values": effettivi,
		"sections": sezioni_visibili,
		"visible": visibili,
		"required": richiesti,
		"missing": mancanti,
		"stops": fermi,
		"bands": fasce,
	}


# ------------------------------------------------------------------ cleaning


def _converti_semplice(tipo: str, valore):
	"""A cell of a table, a side: text, number, date or yes/no. Raises ValueError."""
	if vuoto(valore):
		return None
	if tipo == "number":
		n = numero(valore)
		if n is None:
			raise ValueError
		return _intero_se_puo(n)
	if tipo == "date":
		if not isinstance(valore, str) or not _DATA.match(valore.strip()):
			raise ValueError
		date.fromisoformat(valore.strip())
		return valore.strip()
	if tipo == "yesno":
		return _booleano(valore)
	testo = _come_parola(valore).strip()
	if len(testo) > MAX_TESTO:
		raise ValueError
	return testo or None


def _come_parola(valore) -> str:
	"""What a person typed: text, or a number typed where text goes. A list or an
	object is not typed by anybody."""
	if isinstance(valore, bool) or not isinstance(valore, str | int | float):
		raise ValueError
	return str(valore)


def _booleano(valore) -> bool:
	if isinstance(valore, bool):
		return valore
	if valore in (1, 0) and not isinstance(valore, float):
		return bool(valore)
	if isinstance(valore, str) and valore.strip().lower() in ("1", "true", "yes"):
		return True
	if isinstance(valore, str) and valore.strip().lower() in ("0", "false", "no"):
		return False
	raise ValueError


def _converti(campo: dict, valore):
	"""The answer as the field keeps it, or an Errore."""
	tipo = campo.get("type")
	chiave = campo.get("id")
	if vuoto(valore):
		return None, None
	try:
		if tipo == "text":
			testo = _come_parola(valore)
			if len(testo) > MAX_TESTO:
				return None, Errore("too_long", chiave, "{0} is too long", (campo.get("label"),))
			testo = testo.strip() if campo.get("multiline") else " ".join(testo.split())
			return testo or None, None
		if tipo == "number":
			n = numero(valore)
			if n is None:
				return None, Errore("not_a_number", chiave, "{0} is a number", (campo.get("label"),))
			minimo, massimo = numero(campo.get("min")), numero(campo.get("max"))
			if minimo is not None and n < minimo:
				return None, Errore(
					"below_min", chiave, "{0} is at least {1}", (campo.get("label"), _intero_se_puo(minimo))
				)
			if massimo is not None and n > massimo:
				return None, Errore(
					"above_max", chiave, "{0} is at most {1}", (campo.get("label"), _intero_se_puo(massimo))
				)
			decimali = numero(campo.get("decimals"))
			if decimali is not None:
				n = arrotonda(n, decimali)
			return _intero_se_puo(n), None
		if tipo == "choice":
			ammesse = [o.get("label") for o in _lista(campo.get("options")) if isinstance(o, dict)]
			if campo.get("multiple"):
				scelte = valore if isinstance(valore, list) else [valore]
				if any(v not in ammesse for v in scelte):
					return None, Errore(
						"invalid_option", chiave, "{0}: not one of the choices", (campo.get("label"),)
					)
				return [v for v in ammesse if v in scelte], None
			if valore not in ammesse:
				return None, Errore(
					"invalid_option", chiave, "{0}: not one of the choices", (campo.get("label"),)
				)
			return valore, None
		if tipo in ("yesno", "consent"):
			return _booleano(valore), None
		if tipo == "date":
			return _converti_semplice("date", valore), None
		if tipo == "scale":
			n = numero(valore)
			minimo = numero(campo.get("min"))
			massimo = numero(campo.get("max"))
			minimo = 0.0 if minimo is None else minimo
			massimo = 10.0 if massimo is None else massimo
			if n is None or not n.is_integer() or not minimo <= n <= massimo:
				return None, Errore(
					"out_of_scale",
					chiave,
					"{0} goes from {1} to {2}",
					(campo.get("label"), _intero_se_puo(minimo), _intero_se_puo(massimo)),
				)
			return int(n), None
		if tipo == "table":
			if not isinstance(valore, list):
				raise ValueError
			colonne = [c for c in _lista(campo.get("columns")) if isinstance(c, dict)]
			righe = []
			for riga in valore[:MAX_RIGHE]:
				if not isinstance(riga, dict):
					raise ValueError
				pulita = {
					c.get("id"): _converti_semplice(c.get("type") or "text", riga.get(c.get("id")))
					for c in colonne
				}
				pulita = {k: v for k, v in pulita.items() if v is not None}
				if pulita:
					righe.append(pulita)
			return righe or None, None
		if tipo == "sides":
			if not isinstance(valore, dict):
				raise ValueError
			genere = campo.get("input") or "number"
			lati = {lato: _converti_semplice(genere, valore.get(lato)) for lato in ("left", "right")}
			lati = {k: v for k, v in lati.items() if v is not None}
			return lati or None, None
		if tipo == "attachment":
			file = valore if isinstance(valore, list) else [valore]
			if not all(isinstance(f, str) and f.strip() for f in file):
				raise ValueError
			file = [f.strip() for f in file]
			return (file if campo.get("multiple") else file[0]), None
		# a signature, and another module's component: theirs to check
		return valore, None
	except (ValueError, TypeError):
		return None, Errore("invalid_value", chiave, "{0}: the answer is not valid", (campo.get("label"),))


def pulisci(schema, valori: dict | None) -> tuple[dict, list[Errore], dict]:
	"""The answers as they are kept: typed, the hidden and the unknown ones
	dropped, the calculations worked out. With what is wrong about the visible
	ones, and the evaluation they give."""
	valori = valori or {}
	tipizzati, errori = {}, []
	for campo in campi(schema):
		tipo = componente(campo.get("type"))
		chiave = campo.get("id")
		if tipo is None or not tipo.risposta or not isinstance(chiave, str) or chiave not in valori:
			continue
		valore, errore = _converti(campo, valori[chiave])
		if errore:
			errori.append(errore)
		else:
			tipizzati[chiave] = valore
	stato = valuta(schema, tipizzati)
	puliti = {chiave: valore for chiave, valore in stato["values"].items() if not vuoto(valore)}
	return puliti, [e for e in errori if stato["visible"].get(e.campo)], stato


# ------------------------------------------------------------------ validation


def _e_gruppi(gruppi) -> bool:
	return gruppi is None or (
		isinstance(gruppi, list)
		and all(isinstance(g, list) and all(isinstance(c, dict) for c in g) for g in gruppi)
	)


def _controlla_condizioni(
	errori: list, gruppi, dove: str | None, prima: dict, tutti: dict, solo_prima: bool, etichetta: str
) -> None:
	if gruppi in (None, []):
		return
	if not _e_gruppi(gruppi):
		errori.append(Errore("invalid_condition", dove, "{0}: the condition is not valid", (etichetta,)))
		return
	for gruppo in gruppi:
		for condizione in gruppo:
			nome = condizione.get("field")
			if not isinstance(nome, str) or not nome:
				continue
			operatore = condizione.get("operator") or "equals"
			if operatore not in OPERATORI:
				errori.append(
					Errore("invalid_operator", dove, "{0}: unknown operator {1}", (etichetta, operatore))
				)
				continue
			bersaglio = (prima if solo_prima else tutti).get(nome)
			if bersaglio is None:
				codice = "later_reference" if solo_prima and nome in tutti else "unknown_reference"
				messaggio = (
					"{0}: a condition can only use the questions before it ({1})"
					if codice == "later_reference"
					else "{0}: the condition uses {1}, which is not in the form"
				)
				errori.append(Errore(codice, dove, messaggio, (etichetta, nome)))
				continue
			tipo = componente(bersaglio.get("type"))
			if tipo is None or tipo.condizione is None:
				errori.append(
					Errore("invalid_condition", dove, "{0}: {1} cannot be asked about", (etichetta, nome))
				)
			elif tipo.condizione == SOLO_PRESENZA and operatore not in SENZA_VALORE:
				errori.append(
					Errore(
						"invalid_operator",
						dove,
						"{0}: of {1} one can only ask whether it was given",
						(etichetta, nome),
					)
				)


def _controlla_campo(errori: list, campo: dict, prima: dict, tutti: dict, posto: int = 0) -> None:
	chiave = campo.get("id") if _id_valido(campo.get("id")) else None
	tipo = componente(campo.get("type"))
	etichetta = _testo(campo.get("label")) or chiave or ""
	if tipo is None:
		errori.append(
			Errore("unknown_type", chiave, "{0}: unknown kind of field {1}", (etichetta, campo.get("type")))
		)
		return
	if tipo.valore is not None and not _testo(campo.get("label")):
		# named by its place in the form, never by its key: «signature» told nobody which
		errori.append(Errore("missing_label", chiave, "Question {0} needs its words", (posto,)))

	nome = campo.get("type")
	if nome in ("number", "scale"):
		minimo, massimo = numero(campo.get("min")), numero(campo.get("max"))
		if nome == "scale":
			minimo = 0.0 if minimo is None else minimo
			massimo = 10.0 if massimo is None else massimo
			if not (
				minimo.is_integer() and massimo.is_integer() and minimo < massimo and massimo - minimo <= 100
			):
				errori.append(
					Errore(
						"invalid_scale",
						chiave,
						"{0}: a scale goes up in whole steps, at most 100",
						(etichetta,),
					)
				)
		elif minimo is not None and massimo is not None and minimo > massimo:
			errori.append(Errore("min_above_max", chiave, "{0}: the least is above the most", (etichetta,)))
	if nome in ("number", "calc") and campo.get("decimals") is not None:
		d = numero(campo.get("decimals"))
		if d is None or not d.is_integer() or not 0 <= d <= MAX_DECIMALI:
			errori.append(Errore("invalid_decimals", chiave, "{0}: decimals go from 0 to 6", (etichetta,)))
	if nome == "choice":
		opzioni = campo.get("options")
		if not isinstance(opzioni, list) or not opzioni:
			errori.append(Errore("missing_options", chiave, "{0}: a choice needs its options", (etichetta,)))
		else:
			viste = set()
			for opzione in opzioni[: MAX_OPZIONI + 1]:
				testo = _testo(opzione.get("label")) if isinstance(opzione, dict) else ""
				if not testo or testo in viste:
					errori.append(
						Errore(
							"duplicate_option", chiave, "{0}: every option has its own words", (etichetta,)
						)
					)
					break
				viste.add(testo)
				if opzione.get("score") not in (None, "") and numero(opzione.get("score")) is None:
					errori.append(Errore("invalid_score", chiave, "{0}: a score is a number", (etichetta,)))
					break
			if len(opzioni) > MAX_OPZIONI:
				errori.append(
					Errore("too_many", chiave, "{0}: at most {1} options", (etichetta, MAX_OPZIONI))
				)
	if nome == "yesno":
		punti = campo.get("scores") or {}
		if not isinstance(punti, dict) or any(
			v not in (None, "") and numero(v) is None for v in punti.values()
		):
			errori.append(Errore("invalid_score", chiave, "{0}: a score is a number", (etichetta,)))
	if nome == "table":
		colonne = campo.get("columns")
		if not isinstance(colonne, list) or not colonne:
			errori.append(Errore("missing_columns", chiave, "{0}: a table needs its columns", (etichetta,)))
		else:
			viste = set()
			for colonna in colonne:
				ok = (
					isinstance(colonna, dict)
					and _id_valido(colonna.get("id"))
					and colonna.get("id") not in viste
					and _testo(colonna.get("label"))
					and (colonna.get("type") or "text") in TIPI_COLONNA
				)
				if not ok:
					errori.append(
						Errore("invalid_column", chiave, "{0}: a column is not valid", (etichetta,))
					)
					break
				viste.add(colonna.get("id"))
			if len(colonne) > MAX_COLONNE:
				errori.append(
					Errore("too_many", chiave, "{0}: at most {1} columns", (etichetta, MAX_COLONNE))
				)
	if nome == "paragraph" and not _testo(campo.get("text")):
		errori.append(Errore("missing_text", chiave, "A text to read needs its words ({0})", (chiave,)))
	if nome == "calc":
		try:
			# once each: "a * a" is one question used twice
			usati = list(dict.fromkeys(riferimenti(leggi_formula(campo.get("formula")))))
		except ErroreFormula as errore:
			errori.append(
				Errore(
					"invalid_formula", chiave, "{0}: the formula is not valid ({1})", (etichetta, str(errore))
				)
			)
			usati = []
		for usato in usati:
			if usato not in prima:
				codice = "later_reference" if usato in tutti else "unknown_reference"
				messaggio = (
					"{0}: a calculation can only use the questions before it ({1})"
					if codice == "later_reference"
					else "{0}: the formula uses {1}, which is not in the form"
				)
				errori.append(Errore(codice, chiave, messaggio, (etichetta, usato)))
			elif not (componente(prima[usato].get("type")) or Componente("", "", None)).numerico:
				errori.append(
					Errore("not_a_number_reference", chiave, "{0}: {1} is not a number", (etichetta, usato))
				)
	if nome == "score":
		fonti = campo.get("sources")
		if not isinstance(fonti, list) or not fonti:
			errori.append(
				Errore("missing_sources", chiave, "{0}: a score counts some questions", (etichetta,))
			)
		else:
			for fonte in fonti:
				bersaglio = prima.get(fonte) if isinstance(fonte, str) else None
				if bersaglio is None or bersaglio.get("type") not in ("choice", "yesno", "scale", "number"):
					errori.append(
						Errore(
							"invalid_source",
							chiave,
							"{0}: a score counts choices, yes or no, scales and numbers before it ({1})",
							(etichetta, fonte),
						)
					)
		for banda in _lista(campo.get("bands")):
			da = numero(banda.get("from")) if isinstance(banda, dict) else None
			a = numero(banda.get("to")) if isinstance(banda, dict) else None
			if da is None or a is None or da > a or not _testo(banda.get("label")):
				errori.append(
					Errore(
						"invalid_band",
						chiave,
						"{0}: a band goes from a number to a bigger one, with a name",
						(etichetta,),
					)
				)
				break
	if nome == "sides" and (campo.get("input") or "number") not in TIPI_LATO:
		errori.append(
			Errore("invalid_sides_input", chiave, "{0}: each side is a number or a text", (etichetta,))
		)
	if nome == "signature":
		if (campo.get("signer") or "patient") not in FIRMATARI:
			errori.append(Errore("invalid_signer", chiave, "{0}: who signs is not valid", (etichetta,)))
		if (campo.get("level") or "simple") not in LIVELLI_FIRMA:
			errori.append(
				Errore(
					"invalid_signature_level",
					chiave,
					"{0}: the level of the signature is not valid",
					(etichetta,),
				)
			)
	if nome == "consent" and not _testo(campo.get("consent_type")):
		errori.append(Errore("missing_consent_type", chiave, "{0}: which consent it records", (etichetta,)))

	_controlla_condizioni(errori, campo.get("show_if"), chiave, prima, tutti, True, etichetta)
	_controlla_condizioni(errori, campo.get("required_if"), chiave, prima, tutti, False, etichetta)
	_controlla_condizioni(errori, campo.get("stop_if"), chiave, prima, tutti, False, etichetta)


def valida_schema(schema) -> list[Errore]:
	"""What is wrong with a schema: nothing, or the list, each with its field."""
	if not isinstance(schema, dict) or not isinstance(schema.get("sections"), list):
		return [Errore("not_a_schema", None, "This is not a form")]
	errori: list[Errore] = []
	lista_sezioni = schema["sections"]
	if len(lista_sezioni) > MAX_SEZIONI:
		errori.append(Errore("too_many", None, "At most {0} sections", (MAX_SEZIONI,)))
	tutti: dict[str, dict] = {}
	for campo in campi(schema):
		if _id_valido(campo.get("id")) and campo["id"] not in tutti:
			tutti[campo["id"]] = campo
	if len(campi(schema)) > MAX_CAMPI:
		errori.append(Errore("too_many", None, "At most {0} fields", (MAX_CAMPI,)))

	prima: dict[str, dict] = {}
	id_sezioni: set = set()
	id_campi: set = set()
	posto = 0
	for sezione in lista_sezioni:
		if not isinstance(sezione, dict):
			errori.append(Errore("not_a_schema", None, "This is not a form"))
			continue
		chiave = sezione.get("id") if _id_valido(sezione.get("id")) else None
		if chiave is None or chiave in id_sezioni:
			errori.append(
				Errore("invalid_id", chiave, "Every section has its own key ({0})", (chiave or "",))
			)
		id_sezioni.add(chiave)
		if not isinstance(sezione.get("fields", []), list):
			errori.append(Errore("not_a_schema", chiave, "This is not a form"))
		_controlla_condizioni(
			errori, sezione.get("show_if"), chiave, prima, tutti, True, _testo(sezione.get("title")) or chiave
		)
		for campo in campi_della_sezione(sezione):
			posto += 1
			chiave_campo = campo.get("id") if _id_valido(campo.get("id")) else None
			if chiave_campo is None or chiave_campo in id_campi:
				errori.append(
					Errore(
						"invalid_id",
						chiave_campo,
						"Every question has its own key: lowercase letters, digits and _ ({0})",
						(chiave_campo or "",),
					)
				)
			_controlla_campo(errori, campo, prima, tutti, posto)
			if chiave_campo is not None:
				id_campi.add(chiave_campo)
				prima.setdefault(chiave_campo, campo)
	return errori


def pronto_da_pubblicare(schema) -> list[Errore]:
	"""A version people will fill: valid, and with at least one question."""
	errori = valida_schema(schema)
	if not any((componente(c.get("type")) or Componente("", "", None)).risposta for c in campi(schema)):
		errori.append(Errore("empty", None, "A form asks something: add a question"))
	return errori


# ------------------------------------------------------------------ keeping it


def _niente(valore) -> bool:
	# identity for False: a 0 (the least of a scale) is something
	return valore is None or valore is False or valore == "" or valore == [] or valore == {}


def _solo(voci, chiavi: tuple[str, ...]) -> list[dict]:
	return [
		{k: voce[k] for k in chiavi if k in voce and not _niente(voce[k])}
		for voce in _lista(voci)
		if isinstance(voce, dict)
	]


def _parte(origine: dict, chiavi) -> dict:
	parte = {}
	for chiave in chiavi:
		valore = origine.get(chiave)
		if chiave in ("show_if", "required_if", "stop_if"):
			valore = [
				[{k: c[k] for k in ("field", "operator", "value") if k in c} for c in gruppo]
				for gruppo in pulisci_gruppi(valore)
			]
		elif chiave == "options":
			valore = _solo(valore, ("label", "score"))
		elif chiave == "columns":
			valore = _solo(valore, ("id", "label", "type"))
		elif chiave == "bands":
			valore = _solo(valore, ("from", "to", "label"))
		elif chiave == "scores" and isinstance(valore, dict):
			valore = {k: valore[k] for k in ("yes", "no") if not _niente(valore.get(k))}
		elif chiave in ("phrases", "sources") and isinstance(valore, list):
			valore = [v for v in valore if isinstance(v, str) and v.strip()]
		if not _niente(valore):
			parte[chiave] = valore
	return parte


def normalizza(schema) -> dict:
	"""The schema with only what each part may carry, and nothing empty: a property
	left over from a field's earlier type, or a condition left half-written, does
	not travel into a version, nor into its hash."""
	risultato = []
	for sezione in sezioni(schema):
		nuova = _parte(sezione, [k for k in PROPRIETA_SEZIONE if k != "fields"])
		nuova["fields"] = []
		for campo in campi_della_sezione(sezione):
			tipo = componente(campo.get("type"))
			nuova["fields"].append(
				_parte(campo, list(PROPRIETA_COMUNI) + list(tipo.proprieta if tipo else ()))
			)
		risultato.append(nuova)
	return {"sections": risultato}


def canonico(schema) -> str:
	"""One way of writing the same schema: the bytes its hash is taken on."""
	return json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def impronta(schema) -> str:
	"""SHA-256 of the schema: what a filled form points at, to prove years later
	which questions and which words it was."""
	return hashlib.sha256(canonico(schema).encode("utf-8")).hexdigest()
