# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A deposit's advance invoice makes nobody a client (doc 60).

Since the deposits paid at /prenota were invoiced the day they arrived, their
advance invoice counted as a sale: whoever booked was «Client since» the day they
paid, before they ever came - and stayed one after a late cancellation kept the
deposit. The rules now leave the advance out; the people it made clients get their
first real fact as the date, or are contacts again, announcing nothing
(`cliente.ricalcola_dagli_acconti`). The clinic recounts its patients in its own
patch, after this one.
"""

from crm.clienti import cliente


def execute():
	cliente.ricalcola_dagli_acconti()
