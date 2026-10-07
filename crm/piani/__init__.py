# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Plans and programmes: what the centre writes for a person to follow in their
area, one tap at a time (docs/verticali/clinica/design.md, "I piani").

A gym's trainer, a beauty centre's therapist, a medical centre's nutritionist: each
writes plans, so they are the CRM's, not the clinic's ("Tre strati").

- **The engine** (`regole`): moments and items, the week, one tap, versions; the
  kinds of plan and of item registered - the CRM's own a training and habits, an
  exercise and a habit.
- **A module adds its kinds** with who writes them, what they hold and what their
  screens offer: the clinic its diets and exercises at home, the foods
  (`crm.clinica.piani`). A kind may carry the mark "health data": its plans are
  read like the clinical record, by the rule the clinic registers
  (`crm.permissions.sanitari`).
- **Programmes of stages** (`programmi`): stages that open with time or one after
  the other, each maybe with its plan.
- **The exercises' library** (`librerie`): the library DottorCloud ships
  (`dati/esercizi.json`, loaded at install and migrate) and the centre's own, its
  pictures from where the agency hosts them.
- **In the area** (`area`): the day's moments, one tap an item, what is left this
  week; the programmes stage by stage.

It goes with the client area: a plan is followed there.
"""

from __future__ import annotations

from crm.permissions.livelli import A_SCELTA, CENTRO, SUOI, Capacita, registra_capacita

#: The plan's module plans go with: the client area, where they are followed.
PIANO = "area"

CAPACITA = (
	(
		Capacita(
			"piani.scrivi",
			PIANO,
			descrizione="Write and publish plans and programmes - a training, habits, and the kinds "
			"one's qualification allows",
		),
		{"operatore": SUOI},
	),
	(
		Capacita(
			"piani.vedi",
			PIANO,
			scrive=False,
			descrizione="Read the plans and programmes of the people one sees, and how they are going",
		),
		{"operatore": SUOI, "segreteria": CENTRO, "manager": CENTRO},
	),
	# the libraries the plans are written with: the manager, and whoever of the
	# practitioners the manager chooses
	(
		Capacita(
			"piani.librerie",
			PIANO,
			# the centre never imports: the library is DottorCloud's, the centre
			# corrects it and adds its own (crm.piani.librerie)
			descrizione="Keep the centre's libraries the plans are written with: correct names and "
			"groups, add the centre's own, switch an item off",
		),
		{"manager": CENTRO, "operatore": A_SCELTA},
	),
)


def registra() -> None:
	from crm.area.sezioni import Sezione, registra_sezione
	from crm.piani import area

	for capacita, concessioni in CAPACITA:
		registra_capacita(capacita, concessioni)
	# "Plans" in the area, to whoever follows one now
	registra_sezione(Sezione("plans", area.piani_in_corso))
	# its share of the demo: plans and programmes, ticked in the area
	from crm.demo.registro import Parte, registra_parte
	from crm.piani import demo

	registra_parte(
		Parte(
			"piani",
			"Plans and programmes",
			demo.crea,
			modulo=PIANO,
			dopo=("area",),
			descrizione="The kinesiologist's trainings to do at home and the dietitian's habits, given "
			"at the last session; a programme of each, written this morning; what people ticked in "
			"the area these last days.",
		)
	)
