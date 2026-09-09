# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Test base class for the fiscal engine.

`frappe.tests.UnitTestCase` when there is a bench, plain `unittest.TestCase`
otherwise. The fallback is not a convenience: the engine is meant to be verifiable
by somebody with a checkout and a Python interpreter, and a suite that needs a
site to run is a suite an accountant never runs.
"""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the engine is still fully testable
	from unittest import TestCase as UnitTestCase

__all__ = ["UnitTestCase"]
