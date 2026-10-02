# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# The sentences of the invoicing and Sistema TS engines reach the desk through
# `crm.invoicing.documento.in_parole`, which looks them up at run time: the
# catalog's extraction, which reads only `_()` literals, never sees them. Their
# English has to be in the Italian catalog by hand, or the person reads English;
# and a sentence with a value in it has to be a `Messaggio`, or no catalog finds it.

import ast
import re
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
CATALOGO = APP / "locale" / "it.po"

#: The engines whose sentences somebody reads before issuing, or on an issued
#: document: the classification, the computation, the SdI's checks on the XML, the
#: Sistema TS's own.
MOTORI = (
	APP / "invoicing" / "engine" / "classificazione.py",
	APP / "invoicing" / "engine" / "calcolo.py",
	APP / "invoicing" / "engine" / "fatturapa.py",
	APP / "tessera_sanitaria" / "engine" / "classificazione.py",
	APP / "tessera_sanitaria" / "engine" / "tracciato.py",
)

#: Where a sentence is collected.
RACCOGLITORI = ("errori", "avvisi", "problemi")
FRASE = ("Messaggio", "Frase", "Rilievo")


def _msgid() -> set[str]:
	testo = CATALOGO.read_text(encoding="utf-8")
	return {
		m.group(1).encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
		for m in re.finditer(r'^msgid "(.*)"$', testo, re.M)
	}


def _costanti(albero: ast.Module) -> dict[str, str]:
	return {
		nodo.targets[0].id: nodo.value.value
		for nodo in albero.body
		if isinstance(nodo, ast.Assign)
		and len(nodo.targets) == 1
		and isinstance(nodo.targets[0], ast.Name)
		and isinstance(nodo.value, ast.Constant)
		and isinstance(nodo.value.value, str)
	}


def _raccoglitore(nodo: ast.Call) -> bool:
	"""`errori.append(...)`, `esito.avvisi.append(...)`: a sentence being collected."""
	if not (isinstance(nodo.func, ast.Attribute) and nodo.func.attr == "append" and nodo.args):
		return False
	dove = nodo.func.value
	nome = dove.attr if isinstance(dove, ast.Attribute) else getattr(dove, "id", "")
	return nome.endswith(RACCOGLITORI)


def frasi() -> tuple[list[tuple[str, int, str]], list[tuple[str, int]]]:
	"""Every sentence the engines collect: (file, line, English); and the f-strings,
	which no catalog can translate."""
	trovate, fstring = [], []
	for percorso in MOTORI:
		albero = ast.parse(percorso.read_text(encoding="utf-8"))
		costanti = _costanti(albero)
		nome = percorso.relative_to(APP.parent).as_posix()

		def testo(valore):
			if isinstance(valore, ast.Constant) and isinstance(valore.value, str):
				return valore.value
			if isinstance(valore, ast.Name):
				return costanti.get(valore.id)
			return None

		for nodo in ast.walk(albero):
			if not isinstance(nodo, ast.Call):
				continue
			if isinstance(nodo.func, ast.Name) and nodo.func.id in FRASE and nodo.args:
				# a finding says the SdI's code first, its sentence after
				posto = 1 if nodo.func.id == "Rilievo" else 0
				if len(nodo.args) > posto and (modello := testo(nodo.args[posto])) is not None:
					trovate.append((nome, nodo.lineno, modello))
			elif _raccoglitore(nodo):
				argomento = nodo.args[0]
				if isinstance(argomento, ast.JoinedStr):
					fstring.append((nome, nodo.lineno))
				elif (frase := testo(argomento)) is not None:
					trovate.append((nome, nodo.lineno, frase))
	return trovate, fstring


class LeFrasiDelMotore(unittest.TestCase):
	def test_ogni_frase_e_nel_catalogo_italiano(self):
		catalogo = _msgid()
		mancanti = [f"{nome}:{riga} {frase!r}" for nome, riga, frase in frasi()[0] if frase not in catalogo]
		self.assertEqual(mancanti, [], "not in crm/locale/it.po")

	def test_una_frase_con_un_valore_e_un_messaggio(self):
		self.assertEqual(
			[f"{nome}:{riga}" for nome, riga in frasi()[1]],
			[],
			"an f-string no catalog can translate: make it a Messaggio",
		)

	def test_le_frasi_sugli_indirizzi_sono_nel_catalogo(self):
		# kept in a table, one per side of the invoice: the scan above does not see them
		from crm.invoicing.engine.fatturapa import _SEDE

		catalogo = _msgid()
		mancanti = [frase for frasi in _SEDE.values() for frase in frasi.values() if frase not in catalogo]
		self.assertEqual(mancanti, [], "not in crm/locale/it.po")

	def test_le_frasi_ci_sono(self):
		# a scan that finds nothing passes too: it has to find the ones we know
		inglesi = {frase for _nome, _riga, frase in frasi()[0]}
		self.assertIn("nothing on the document goes to the Sistema TS", inglesi)
		self.assertIn('"{0}" only goes with the expense type "{1}", not with "{2}"', inglesi)
		self.assertIn("the document has no VAT summary", inglesi)
