# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Fatture in Cloud, for a centre that invoices with it.

The invoice is still made here - from the appointment, the cycle, the
subscription, the dialog - computed and checked here; it is born in Fatture in
Cloud, which numbers it, sends it to the SdI and keeps it (`emissione`). The
connection is the centre's own, made by its manager (`collegamento`); what is
handed over is decided without a site (`regole`).
"""
