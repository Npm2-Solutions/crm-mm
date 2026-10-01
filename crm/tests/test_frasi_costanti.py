# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# A sentence the server translates from a constant - `_(SEGNO)`, `_(regole.SCOPO)` -
# is invisible to the catalog's extraction, which reads only literals: its English
# has to be in the Italian catalog by hand, or the person reads English
# ("AI draft, checked by …" in a patient's messages).

import ast
import re
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
CATALOGO = APP / "locale" / "it.po"


def _msgid() -> set[str]:
	testo = CATALOGO.read_text(encoding="utf-8")
	return {
		m.group(1).encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
		for m in re.finditer(r'^msgid "(.*)"$', testo, re.M)
	}


def _costanti(albero: ast.Module) -> dict[str, str]:
	"""The module's string constants, by name."""
	trovate = {}
	for nodo in albero.body:
		if (
			isinstance(nodo, ast.Assign)
			and len(nodo.targets) == 1
			and isinstance(nodo.targets[0], ast.Name)
			and isinstance(nodo.value, ast.Constant)
			and isinstance(nodo.value.value, str)
		):
			trovate[nodo.targets[0].id] = nodo.value.value
	return trovate


def _moduli_importati(albero: ast.Module) -> dict[str, Path]:
	"""`from crm.x import y [as z]`: the name the file uses, and y's file."""
	trovati = {}
	for nodo in albero.body:
		if isinstance(nodo, ast.ImportFrom) and (nodo.module or "").startswith("crm"):
			for alias in nodo.names:
				percorso = APP.parent.joinpath(*nodo.module.split("."), alias.name + ".py")
				if percorso.exists():
					trovati[alias.asname or alias.name] = percorso
	return trovati


def frasi_da_costanti() -> list[tuple[str, str, str]]:
	"""Every `_(NAME)` and `_(module.NAME)` of the app on a string constant:
	(file, name, English)."""
	cache: dict[Path, dict[str, str]] = {}

	def costanti_di(percorso: Path) -> dict[str, str]:
		if percorso not in cache:
			cache[percorso] = _costanti(ast.parse(percorso.read_text(encoding="utf-8")))
		return cache[percorso]

	frasi = []
	for percorso in sorted(APP.rglob("*.py")):
		if "tests" in percorso.parts or "node_modules" in percorso.parts:
			continue
		albero = ast.parse(percorso.read_text(encoding="utf-8"))
		moduli = _moduli_importati(albero)
		for nodo in ast.walk(albero):
			if not (
				isinstance(nodo, ast.Call)
				and isinstance(nodo.func, ast.Name)
				and nodo.func.id == "_"
				and nodo.args
			):
				continue
			argomento = nodo.args[0]
			testo = None
			if isinstance(argomento, ast.Name):
				nome = argomento.id
				testo = costanti_di(percorso).get(nome)
			elif isinstance(argomento, ast.Attribute) and isinstance(argomento.value, ast.Name):
				nome = argomento.attr
				modulo = moduli.get(argomento.value.id)
				testo = costanti_di(modulo).get(nome) if modulo else None
			if testo:
				frasi.append((str(percorso.relative_to(APP.parent)), nome, testo))
	return frasi


class TestFrasiDaCostanti(unittest.TestCase):
	def test_some_are_found(self):
		# the finder sees the assistant's mark: if it saw nothing, the next test
		# would pass for nothing
		self.assertIn("SEGNO", {nome for _file, nome, _testo in frasi_da_costanti()})

	def test_every_one_is_in_the_italian_catalog(self):
		catalogo = _msgid()
		mancano = [
			f"{file}: {nome} = {testo!r}"
			for file, nome, testo in frasi_da_costanti()
			if testo not in catalogo
		]
		self.assertEqual(mancano, [], "\n".join(mancano))
