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

	def test_la_fatturazione_risolve_le_proprie_qualifiche_da_sola(self):
		"""With nothing registered, a lawyer still gets Cassa Forense and withholding.

		This is the property the split nearly lost. Cassa and ritenuta are **ordinary
		invoicing** - Cassa Forense at 4%, Inarcassa at 4%, withholding at 20% - and an
		installation that never sees a patient still has to get them right. Resolving
		to a neutral answer there is not a missing feature, it is a wrong invoice.
		"""
		from crm.invoicing import estensioni

		estensioni.dimentica_risolutore()
		try:
			risolvi = estensioni.risolutore()
			avvocato = risolvi("avvocato")
			self.assertEqual(avvocato.cassa, "TC01")
			self.assertTrue(avvocato.ritenuta_applicabile)
			self.assertFalse(avvocato.esente_iva)
			# And nothing here claims a duty towards a system it has never heard of.
			self.assertFalse(avvocato.comunicazione_esterna)
			self.assertIsNone(avvocato.soggetto_comunicazione)
		finally:
			estensioni.dimentica_risolutore()

	def test_una_qualifica_sanitaria_non_si_risolve_senza_il_suo_modulo(self):
		"""And it is refused rather than guessed.

		A masseur without the healthcare register has no VAT regime here. Answering
		"taxable at 22%" would be an invention, and an exempt service invoiced with VAT
		is wrong in a way the client notices and the practice pays for.
		"""
		from crm.invoicing import estensioni

		estensioni.dimentica_risolutore()
		try:
			with self.assertRaises(KeyError):
				estensioni.risolutore()("massoterapista")
		finally:
			estensioni.dimentica_risolutore()


class FormaStudioTest(UnitTestCase):
	"""What the interface may hide, and what it may never hide.

	The provider field is the one that flips: for a centre it decides the VAT
	regime, the fund and whether the SdI may carry the document at all; for
	somebody working alone it has exactly one possible value. Hiding it in the
	second case is a saving of sixty interactions a day. Hiding it in the first
	would be a silent fiscal error.

	These pin the rule that decides which of the two it is, so that a change to
	`practice_shape` cannot quietly start hiding a field a centre needs.
	"""

	def test_uno_solo_e_singolo(self):
		self.assertTrue(self._solo(1))

	def test_due_sono_un_centro(self):
		self.assertFalse(self._solo(2))

	def test_nessun_erogatore_non_e_un_singolo(self):
		"""Zero is not one.

		An empty register must not read as "solo" and pre-fill nothing while hiding
		the field: that is a document with no qualification at all, which is exactly
		what the engine refuses to guess.
		"""
		self.assertFalse(self._solo(0))

	@staticmethod
	def _solo(quanti: int) -> bool:
		# The rule itself, without a database: one enabled provider and no more.
		return quanti == 1
