# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Issuing, calculating, formatting, preserving and transmitting documents.

For any sector. This module knows nothing about healthcare: no patients, no spesa
types, no delega. What it does know is that a qualification can be VAT-exempt,
barred from the SdI, or owe a report to some system it has never heard of - and it
records all three without interpreting the last.

`crm.tessera_sanitaria` is what gives that last one meaning, by registering into
`crm.invoicing.estensioni`. Removing it leaves this working.
"""

from __future__ import annotations


def registra() -> None:
	"""Put the stored register in front of the shipped one.

	What the practice edited wins over what shipped, because the choices that decide
	fiscal correctness belong to the practice owner and not to a file only a
	developer can change. Needs a site, so it is the app that calls it.
	"""
	from crm.invoicing import estensioni, registro

	estensioni.registra_risolutore(registro.risolutore())
