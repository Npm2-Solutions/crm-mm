# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

"""The boundary between the two modules, checked rather than promised.

`crm.invoicing` must not know that `crm.tessera_sanitaria` exists. That is the
whole property that makes lifting the second one into its own Frappe app a move
instead of a rewrite, and it is the kind of property that decays in a month unless
something fails when it does.

A comment saying "do not import upward" is not a boundary. This is.
"""

from __future__ import annotations

import ast
import pathlib

from crm.invoicing.tests.base import UnitTestCase

RADICE = pathlib.Path(__file__).resolve().parents[3]
FATTURAZIONE = RADICE / "crm" / "invoicing"
VIETATO = "crm.tessera_sanitaria"


def _moduli_importati(sorgente: str) -> set[str]:
	"""Every module named by an import, wherever the statement sits."""
	nomi: set[str] = set()
	for nodo in ast.walk(ast.parse(sorgente)):
		if isinstance(nodo, ast.Import):
			nomi.update(alias.name for alias in nodo.names)
		elif isinstance(nodo, ast.ImportFrom) and nodo.module and not nodo.level:
			nomi.add(nodo.module)
	return nomi


class ConfineTest(UnitTestCase):
	def test_la_fatturazione_non_importa_il_sistema_ts(self):
		colpevoli = []
		for file in sorted(FATTURAZIONE.rglob("*.py")):
			for modulo in _moduli_importati(file.read_text()):
				if modulo == VIETATO or modulo.startswith(VIETATO + "."):
					colpevoli.append(f"{file.relative_to(RADICE)} -> {modulo}")
		self.assertEqual(
			colpevoli,
			[],
			"invoicing imports the Sistema TS module. The dependency runs the other way: "
			"register into crm.invoicing.estensioni instead.\n" + "\n".join(colpevoli),
		)

	def test_la_fatturazione_classifica_senza_il_registro_sanitario(self):
		"""With nothing registered, a line is taxable and the SdI is open to it.

		This is the answer for a plumber, and proving it here is what says the module
		really does stand on its own rather than merely being arranged as if it did.
		"""
		from crm.invoicing import estensioni
		from crm.invoicing.engine.qualifica import risolutore_neutro

		estensioni.dimentica_risolutore()
		try:
			qualifica = estensioni.risolutore()("qualsiasi_codice")
			self.assertIs(estensioni.risolutore(), risolutore_neutro)
			self.assertFalse(qualifica.esente_iva)
			self.assertFalse(qualifica.comunicazione_esterna)
			self.assertIsNone(qualifica.soggetto_comunicazione)
		finally:
			estensioni.dimentica_risolutore()
