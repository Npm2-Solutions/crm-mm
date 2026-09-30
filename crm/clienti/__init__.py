# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""New clients: who becomes a client of the centre, when, and what it closes.

The first time a person comes - checked in at the desk, an appointment attended - or
their first confirmed invoice, they are a client (`CRM Lead.client_since`), once:
the first fact writes the moment, the ones after do nothing. A beauty centre, a gym
and a medical centre work the same way (docs/gestionale-medico/design.md, "Cosa
passa dalla clinica al CRM"), so it is the CRM's:

- **The rules** (`regole`): which facts say a person came, without a site.
- **The door** (`cliente`): `diventa_cliente`, and the clients already there.
- **Where they listen** (`eventi`): the agenda and invoicing, as document events.
- **The pipeline** (`pipeline`): "New clients". A booking moves an open deal to
  "appointment booked", becoming a client wins it, so the ads report says what a
  new client costs.
- **The automations** hear "Became Client", with the rule that fired; the
  dashboard counts the new clients and what one costs.

A module whose trade has rules of its own takes the CRM's place where it is on
(`cliente.registra_regole`): with the clinic, a client is a patient, and the clinic
says who becomes one.
"""
