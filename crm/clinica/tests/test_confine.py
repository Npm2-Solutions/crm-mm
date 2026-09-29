# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The clinic's boundary, checked rather than promised.

Neither the CRM nor invoicing imports the clinic: it hooks onto them through
document events and registries, the way the Sistema TS hooks onto invoicing. The
one exception is the composition root, `crm/registrazione.py`, whose job is to say
which modules an installation has. That is what makes lifting the clinic into an
app of its own one day a move and not a rewrite.
"""

from __future__ import annotations

import ast
import pathlib

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the boundary is still checkable
	from unittest import TestCase as UnitTestCase

RADICE = pathlib.Path(__file__).resolve().parents[3]
CRM = RADICE / "crm"
CLINICA = CRM / "clinica"
VIETATO = "crm.clinica"
#: The composition root: deciding which modules exist is its whole job.
AMMESSI = {CRM / "registrazione.py"}


def _moduli_importati(sorgente: str) -> set[str]:
	nomi: set[str] = set()
	for nodo in ast.walk(ast.parse(sorgente)):
		if isinstance(nodo, ast.Import):
			nomi.update(alias.name for alias in nodo.names)
		elif isinstance(nodo, ast.ImportFrom) and nodo.module and not nodo.level:
			nomi.add(nodo.module)
	return nomi


class ConfineTest(UnitTestCase):
	def test_ne_il_crm_ne_la_fatturazione_importano_la_clinica(self):
		colpevoli = []
		for file in sorted(CRM.rglob("*.py")):
			if CLINICA in file.parents or file in AMMESSI:
				continue
			for modulo in _moduli_importati(file.read_text()):
				if modulo == VIETATO or modulo.startswith(VIETATO + "."):
					colpevoli.append(f"{file.relative_to(RADICE)} -> {modulo}")
		self.assertEqual(
			colpevoli,
			[],
			"the CRM imports the clinic. The dependency runs the other way: hook onto the CRM "
			"from the clinic, with a document event or a registry.\n" + "\n".join(colpevoli),
		)

	def test_la_clinica_si_registra_senza_un_sito(self):
		"""Its registration is data: it runs, and proves itself, with no bench."""
		from crm.clinica import registra
		from crm.permissions import livelli

		with livelli.registro_isolato():
			registra()
			self.assertIn("clinica", {m.chiave for m in livelli.moduli_piano()})
			self.assertFalse(next(m for m in livelli.moduli_piano() if m.chiave == "clinica").predefinito)
			self.assertIn("pazienti.vedi", livelli.capacita_registrate())
