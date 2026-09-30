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
#: The patient card is who is a patient, not what is wrong with them; the settings
#: say which pipelines are the centre's; an opening out of the care team says who
#: opened a record and why; a delivery, to whom a report was given; an access to
#: the patient area, who enters whose, with which passkey, told of news how. The
#: libraries say what a food or an exercise is, and where a table came from; a
#: plan's rows live inside their plan, a programme's stages inside their programme.
NON_CLINICI = {
	"clinic_patient",
	"clinic_settings",
	"clinic_access_grant",
	"clinic_report_delivery",
	"clinic_area_access",
	"clinic_area_passkey",
	"clinic_area_notice",
	"clinic_food",
	"clinic_exercise",
	"clinic_library_import",
	"clinic_plan_moment",
	"clinic_plan_item",
	"clinic_programme_stage",
}


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

	def test_ogni_documento_clinico_fa_un_paziente(self):
		"""Rule 1 lives in one base class: a clinical DocType that does not inherit it
		would store health data about somebody who is not a patient."""
		senza = []
		for cartella in sorted((CLINICA / "doctype").iterdir()):
			controller = cartella / f"{cartella.name}.py"
			if not controller.exists() or cartella.name in NON_CLINICI:
				continue
			classi = [n for n in ast.walk(ast.parse(controller.read_text())) if isinstance(n, ast.ClassDef)]
			basi = {
				getattr(base, "id", getattr(base, "attr", "")) for classe in classi for base in classe.bases
			}
			if "DocumentoClinico" not in basi:
				senza.append(cartella.name)
		self.assertEqual(
			senza, [], "clinical DocTypes that do not inherit DocumentoClinico: " + ", ".join(senza)
		)
