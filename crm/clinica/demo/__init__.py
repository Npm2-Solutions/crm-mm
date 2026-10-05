# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's share of the demo data (doc 53), made only where the plan's
"clinica" module is on, through the clinic's own code.

- `cartelle`: the medical director joins the team and publishes the clinical sheets;
  this morning the practitioners wrote the last weeks' visits in the record, signed,
  each with its report; the summary, the dossier's consents, an episode obscured, a
  record opened out of care with its reason; reports and test results filed, one
  report given online.
- `dentista`: a dentist joins with the dental chair and its services; the first
  visits of the last weeks with the odontogram and the care plan; the treatments
  booked for who said yes.
- `diete`: the dietitian's menus with the library's foods and an exchange diet, the
  physiotherapist's exercises at home; ticked in the area.
"""

from __future__ import annotations


def registra() -> None:
	from crm.clinica import PIANO
	from crm.clinica.demo import cartelle, dentista, diete
	from crm.demo.registro import Parte, registra_parte

	registra_parte(
		Parte(
			"clinica",
			"Clinical record",
			cartelle.crea,
			modulo=PIANO,
			dopo=("clienti", "moduli", "documenti", "area"),
			descrizione="The medical director and the clinical sheets; the last weeks' visits written "
			"in the record this morning and signed, each with its report; the summary, the dossier's "
			"consents, an episode obscured, a record opened out of care; reports and test results "
			"filed, one given online.",
		)
	)
	registra_parte(
		Parte(
			"dentista",
			"Dentistry",
			dentista.crea,
			modulo=PIANO,
			dopo=("clinica",),
			# his visits are invoiced with the others, each on its day
			prima=("fatturazione",),
			descrizione="A dentist with the dental chair and the services; the first visits of the "
			"last weeks with the odontogram and the care plan; the treatments booked for who said "
			"yes.",
		)
	)
	registra_parte(
		Parte(
			"diete",
			"Diets and exercises at home",
			diete.crea,
			modulo=PIANO,
			dopo=("clinica", "piani"),
			descrizione="The dietitian's menus with the foods of the library and an exchange diet, the "
			"physiotherapist's exercises at home; ticked in the area.",
		)
	)
