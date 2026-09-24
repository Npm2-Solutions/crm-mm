# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The dashboard: a catalogue of widgets, and the dashboards built out of them.

A widget is a question the business asks every day — how many people are waiting
for an answer, how full is tomorrow, what did the ads cost per customer — with
one function that answers it. Widgets live in ``crm.dashboard.widgets``, one
module per part of the product, and each one says what it needs to make sense:
a WhatsApp widget needs WhatsApp connected, an agenda widget needs an agenda.
The catalogue a person sees is the one their site can actually answer.

A dashboard is a layout of widgets. The ready-made ones (``templates``) follow
the site: until someone rearranges them by hand, they are rebuilt from the
template every time they are opened, so connecting WhatsApp puts the WhatsApp
widgets on the conversations dashboard without anybody touching it.
"""
