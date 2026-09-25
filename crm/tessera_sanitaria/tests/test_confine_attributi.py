# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

"""The other half of the boundary: the attributes, not just the imports.

`crm.invoicing.tests.test_confine` proves that invoicing never *imports* this
module. That is necessary and it is not enough, because a dataclass crosses a
boundary without an import: `elenco()` hands back `Professione` objects, and
reading `.obbligo_ts` off one of them is a leak that no import checker and no
linter can see.

It is not hypothetical. The seeder in `crm/invoicing/install.py` was written by
copying this module's and keeping four healthcare-only lines. Every suite stayed
green - nothing here can import `install.py`, which needs a bench - and the
install died at `after_install` with `'Professione' object has no attribute
'soggetto_inviante'`, leaving the site half-created.

So the forbidden set is **derived**, never listed: whatever
`ProfessioneSanitaria` adds to `Professione` is off limits upstream, and a field
added here tomorrow is covered the day it is added.
"""

from __future__ import annotations

import ast
import pathlib

from crm.invoicing.engine.professioni import Professione
from crm.invoicing.tests.base import UnitTestCase
from crm.tessera_sanitaria.engine.professioni import ProfessioneSanitaria

RADICE = pathlib.Path(__file__).resolve().parents[3]
FATTURAZIONE = RADICE / "crm" / "invoicing"


def esclusivi_del_sanitario() -> set[str]:
	"""What the healthcare dataclass adds, fields and properties alike."""
	return {
		nome for nome in set(dir(ProfessioneSanitaria)) - set(dir(Professione)) if not nome.startswith("__")
	}


class ConfineDegliAttributiTest(UnitTestCase):
	def test_il_set_vietato_non_e_vuoto(self):
		"""A derived rule that derives nothing passes every file and proves nothing."""
		self.assertIn("soggetto_inviante", esclusivi_del_sanitario())

	def test_la_fatturazione_non_legge_attributi_solo_sanitari(self):
		vietati = esclusivi_del_sanitario()
		colpevoli = []
		for file in sorted(FATTURAZIONE.rglob("*.py")):
			for nodo in ast.walk(ast.parse(file.read_text())):
				if isinstance(nodo, ast.Attribute) and nodo.attr in vietati:
					colpevoli.append(f"{file.relative_to(RADICE)}:{nodo.lineno} -> .{nodo.attr}")
		self.assertEqual(
			colpevoli,
			[],
			"invoicing reads an attribute only the healthcare dataclass has. An ordinary "
			"Professione does not carry it, so this raises AttributeError the first time a "
			"non-healthcare qualification goes through. Read it here, or add a neutral "
			"default to the base class through crm.invoicing.estensioni.\n" + "\n".join(colpevoli),
		)
