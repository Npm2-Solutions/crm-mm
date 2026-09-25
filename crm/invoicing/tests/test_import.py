# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

"""Every reference to this app's own code resolves to something that exists.

Three kinds, and none of them is covered by running the tests.

Half this app cannot be imported without a bench, so the suites prove the fiscal
rules and say nothing about whether the controllers still load. A module moved or
a name renamed leaves the tests green and the site broken at the first request -
and that failure lands on whoever opens an invoice, not on whoever refactored.

So this reads the imports instead of running them: for every `from crm.… import
X`, the module has to exist on disk and define `X`. It caught four real breakages
the day it was written, all of them in code paths no test can reach.

Imports inside `try`/`except ImportError` are skipped on purpose: a fallback
import is *meant* to fail on one of its branches.

The other two kinds are **strings**, which no import checker and no linter looks
at: the dotted paths the frontend calls over the API, and the ones `hooks.py`
hands to Frappe. Moving an endpoint between modules leaves both silently pointing
at nothing - the Python is clean, the tests pass, and a button does nothing. That
happened to four calls the day the Sistema TS endpoints moved out of invoicing.
"""

from __future__ import annotations

import ast
import pathlib

from crm.invoicing.tests.base import UnitTestCase

RADICE = pathlib.Path(__file__).resolve().parents[3]


def _modulo_su_disco(nome: str) -> pathlib.Path | None:
	diretto = RADICE / (nome.replace(".", "/") + ".py")
	if diretto.exists():
		return diretto
	cartella = RADICE / nome.replace(".", "/")
	if (cartella / "__init__.py").exists():
		return cartella / "__init__.py"
	# A namespace package has no __init__.py and imports perfectly well. Treating
	# the directory as absent would flag half of somebody else's app.
	return cartella if cartella.is_dir() else None


def _nomi_definiti(path: pathlib.Path) -> set[str]:
	"""Top-level names a module offers, imports it re-exports included.

	A namespace package offers only its submodules, which the caller checks for
	separately.
	"""
	if path.is_dir():
		return set()
	try:
		albero = ast.parse(path.read_text())
	except SyntaxError:
		return set()
	nomi: set[str] = set()
	for nodo in ast.walk(albero):
		if isinstance(nodo, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
			nomi.add(nodo.name)
		elif isinstance(nodo, ast.Assign):
			nomi.update(t.id for t in nodo.targets if isinstance(t, ast.Name))
		elif isinstance(nodo, ast.AnnAssign) and isinstance(nodo.target, ast.Name):
			nomi.add(nodo.target.id)
		elif isinstance(nodo, ast.Import | ast.ImportFrom):
			nomi.update((a.asname or a.name.split(".")[0]) for a in nodo.names)
	return nomi


def _righe_in_try(albero: ast.Module) -> set[int]:
	"""Lines inside a try block: a fallback import may legitimately not resolve."""
	righe: set[int] = set()
	for nodo in ast.walk(albero):
		if isinstance(nodo, ast.Try):
			for figlio in ast.walk(nodo):
				if hasattr(figlio, "lineno"):
					righe.add(figlio.lineno)
	return righe


class ImportTest(UnitTestCase):
	def test_ogni_import_interno_risolve(self):
		rotti: list[str] = []
		for file in sorted(RADICE.glob("crm/**/*.py")):
			if "node_modules" in str(file):
				continue
			try:
				albero = ast.parse(file.read_text())
			except SyntaxError as errore:
				rotti.append(f"{file.relative_to(RADICE)}: does not parse - {errore}")
				continue

			tollerate = _righe_in_try(albero)
			for nodo in ast.walk(albero):
				if not isinstance(nodo, ast.ImportFrom) or not nodo.module or nodo.level:
					continue
				if not nodo.module.startswith("crm.") or nodo.lineno in tollerate:
					continue

				dove = f"{file.relative_to(RADICE)}:{nodo.lineno}"
				target = _modulo_su_disco(nodo.module)
				if target is None:
					rotti.append(f"{dove} -> no such module {nodo.module}")
					continue

				definiti = _nomi_definiti(target)
				for alias in nodo.names:
					if alias.name == "*" or alias.name in definiti:
						continue
					if _modulo_su_disco(f"{nodo.module}.{alias.name}") is None:
						rotti.append(f"{dove} -> {nodo.module} does not define {alias.name!r}")

		self.assertEqual(
			rotti,
			[],
			"internal imports that would fail at runtime:\n" + "\n".join(rotti),
		)


def _riferimento_risolve(percorso: str) -> bool:
	"""Whether a dotted string names something this app actually defines.

	Walked from the longest module prefix down, because `a.b.c` can be a function
	`c` in module `a.b` or a name in module `a`.
	"""
	parti = percorso.split(".")
	for taglio in range(len(parti) - 1, 0, -1):
		modulo, attributi = ".".join(parti[:taglio]), parti[taglio:]
		target = _modulo_su_disco(modulo)
		if target is None or target.is_dir():
			continue
		return attributi[0] in _nomi_definiti(target)
	return False


class RiferimentiStringaTest(UnitTestCase):
	"""The paths that are written as text and checked by nobody."""

	def test_il_frontend_chiama_endpoint_che_esistono(self):
		import re

		mancanti = []
		sorgenti = list((RADICE / "frontend" / "src").rglob("*.vue"))
		sorgenti += list((RADICE / "frontend" / "src").rglob("*.js"))
		for file in sorted(sorgenti):
			for trovato in re.finditer(r"[\'\"](crm\.[a-zA-Z0-9_.]+)[\'\"]", file.read_text()):
				percorso = trovato.group(1)
				if percorso.count(".") >= 2 and not _riferimento_risolve(percorso):
					mancanti.append(f"{file.relative_to(RADICE)} -> {percorso}")

		self.assertEqual(
			mancanti,
			[],
			"the interface calls endpoints that do not exist:\n" + "\n".join(mancanti),
		)

	def test_i_percorsi_attivi_in_hooks_esistono(self):
		"""Commented-out lines are skipped: hooks.py ships full of boilerplate."""
		import re

		mancanti = []
		for numero, riga in enumerate((RADICE / "crm" / "hooks.py").read_text().splitlines(), start=1):
			if riga.lstrip().startswith("#"):
				continue
			for trovato in re.finditer(r"[\'\"](crm\.[a-z0-9_.]+)[\'\"]", riga):
				percorso = trovato.group(1)
				if percorso.count(".") >= 2 and not _riferimento_risolve(percorso):
					mancanti.append(f"hooks.py:{numero} -> {percorso}")

		self.assertEqual(
			mancanti,
			[],
			"hooks.py points at code that does not exist:\n" + "\n".join(mancanti),
		)
