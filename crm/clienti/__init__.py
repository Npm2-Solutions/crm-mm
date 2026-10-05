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
- **Who they are** (`CRM Lead.relationship`): a contact, then a client - on the
  person's page, in the lists and their filters.

The rules decide in every centre: whoever came to a Pilates class is a client of a
medical centre too. A module adds its own step above the client and keeps it (the
clinic: a patient, the person who had a health service or whose health data the
centre keeps), with its own event; the client's door never takes it back down.
"""
