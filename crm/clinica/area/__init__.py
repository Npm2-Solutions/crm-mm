# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The patient area, `/area`: the person's own window on the centre.

Who enters is a user of the site with the "Clinic Patient" role, never staff,
invited by the centre for one or more people (themselves, a child, an elderly
parent who said yes: `Clinic Area Access`). Every call derives "my people" on the
server from that list and never takes a person the session was not given
(design.md, "L'area cliente"). The door is a code by email (`accesso`); what is
inside, `api`.
"""
