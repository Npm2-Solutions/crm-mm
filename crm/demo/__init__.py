# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo data (docs/crm/53): a centre full of life to look around in,
and taken away without a trace.

The base's parts are here (`base`, `simulazione`); a module adds its own part from
its `registra()` with `crm.demo.registro.registra_parte`. How a part is made without
anything leaving the site is `modo`, what keeps the demo's people from being written
to afterwards is `guardie`, taking it all away is `togli`.
"""


def registra() -> None:
	from crm.demo import base

	base.registra()
