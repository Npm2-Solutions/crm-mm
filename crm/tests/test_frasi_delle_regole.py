# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# The rules without a site say what is wrong as a `Problema` (plans, programmes,
# quotes, teeth, foods) or an `Errore` (the forms' schema): English words with
# their arguments, translated when they are said (`testo(_)`). The catalog's
# extraction reads only `_()` literals and never sees them, so their English has
# to be in the Italian catalog by hand: a quote with an empty row said «Row 2:
# choose the service» to an Italian dentist.

import ast
import unittest
from pathlib import Path

from crm.tests.test_frasi_del_motore import APP, _costanti, _msgid

#: the class that carries the sentence, and where the sentence sits among its
#: arguments
FRASI = {"Problema": 0, "Errore": 2}


def frasi() -> list[tuple[str, int, str]]:
	"""Every sentence a rule says: (file, line, English)."""
	trovate = []
	for percorso in sorted(APP.rglob("*.py")):
		if "tests" in percorso.parts:
			continue
		sorgente = percorso.read_text(encoding="utf-8")
		if not any(f"{classe}(" in sorgente for classe in FRASI):
			continue
		albero = ast.parse(sorgente)
		costanti = _costanti(albero)
		nome = percorso.relative_to(APP.parent).as_posix()
		for nodo in ast.walk(albero):
			if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)):
				continue
			posto = FRASI.get(nodo.func.id)
			if posto is None or len(nodo.args) <= posto:
				continue
			argomento = nodo.args[posto]
			if isinstance(argomento, ast.Constant) and isinstance(argomento.value, str):
				trovate.append((nome, nodo.lineno, argomento.value))
			elif isinstance(argomento, ast.Name) and argomento.id in costanti:
				trovate.append((nome, nodo.lineno, costanti[argomento.id]))
	return trovate


class LeFrasiDelleRegole(unittest.TestCase):
	def test_ogni_frase_e_nel_catalogo_italiano(self):
		catalogo = _msgid()
		mancanti = [f"{nome}:{riga} {frase!r}" for nome, riga, frase in frasi() if frase not in catalogo]
		self.assertEqual(mancanti, [], "not in crm/locale/it.po")

	def test_le_frasi_ci_sono(self):
		# a scan that finds nothing passes too: it has to find the ones we know
		inglesi = {frase for _nome, _riga, frase in frasi()}
		self.assertIn("Row {0}: choose the service", inglesi)
		self.assertIn("{0} is not a tooth", inglesi)
		self.assertIn("Write the habit", inglesi)
		self.assertIn("{0} is too long", inglesi)
