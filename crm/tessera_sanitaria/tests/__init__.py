# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Registering the module before its tests run.

These tests exercise what this module contributes to invoicing - the register of
qualifications, the spesa codes, the guard - so the contribution has to be in place
before the first assertion. In a running site `crm/hooks.py` registers everything, the
editable register included; here only the pure half goes in, which is also a small
proof that the engine half needs no database at all.
"""

from crm.tessera_sanitaria import registra_motore

registra_motore()
