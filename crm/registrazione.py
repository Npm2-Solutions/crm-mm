# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Which modules this installation has, registered once per process.

Invoicing takes its healthcare half through `crm.invoicing.estensioni`, and the
permission registry takes every module's roles, levels and capabilities through
`crm.permissions.livelli`. Both are process-wide lists that each module fills when
it registers - so every process has to run the registration before it serves
anything.

`crm/hooks.py` used to be the only place that did, at import. That is not enough:
outside developer mode Frappe keeps the hooks in its cache, and a worker that finds
them there never imports `crm/hooks.py` at all. Such a worker resolved no healthcare
qualification ("'fisioterapista' is not in the register") and ran no Sistema TS
check on the invoices it validated. So registration hangs off `before_request` and
`before_job` as well, and anything that reads a registry can call `carica()` itself.

The wiring stays in the app, not in the modules: deciding which modules an
installation has is the app's job. Removing a line here leaves the rest working.
"""

from __future__ import annotations

_caricato = False


def carica(*args, **kwargs) -> None:
	"""Register every module, the first time a process asks. Cheap afterwards.

	Accepts and ignores arguments: Frappe calls `before_job` hooks with the job's
	method and kwargs.
	"""
	global _caricato
	if _caricato:
		return
	# set first: a module that reads a registry while registering must not recurse
	_caricato = True
	try:
		from crm.area import registra as registra_area
		from crm.assistente import registra as registra_assistente
		from crm.clinica import registra as registra_clinica
		from crm.invoicing import registra as registra_fatturazione
		from crm.moduli import registra as registra_moduli
		from crm.permissions import catalogo
		from crm.piani import registra as registra_piani
		from crm.tessera_sanitaria import registra as registra_tessera_sanitaria

		catalogo.registra()
		registra_moduli()
		registra_fatturazione()
		registra_tessera_sanitaria()
		# the assistant: on every site, switched on by the plan
		registra_assistente()
		# the client area: on every site, switched on by the plan
		registra_area()
		# plans and programmes, followed in the area
		registra_piani()
		# the clinic, a vertical: on every site, switched on by the plan; it adds to
		# the area, so after it
		registra_clinica()
	except Exception:
		# half a registration must not pass for a whole one: the next caller retries,
		# and fails loudly the same way
		_caricato = False
		raise
