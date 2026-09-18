# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Rules that `bench migrate` enforces, checked before anybody deploys.

A doctype that breaks one of these does not fail a test — it fails the
migration, halfway through, on the site. That is an expensive place to find out,
and the checks themselves are three lines of JSON reading.
"""

import json
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parent.parent

# frappe/database/schema.py: a Data column is a varchar and is refused outside
# this range. A long URL belongs in Small Text, which is a TEXT column.
MAX_DATA_LENGTH = 1000


def doctype_files():
	return sorted(APP.glob("*/doctype/*/*.json"))


class TestDocTypeSchema(unittest.TestCase):
	def test_no_data_field_is_longer_than_a_varchar(self):
		too_long = []
		for path in doctype_files():
			doc = json.loads(path.read_text())
			if doc.get("doctype") != "DocType":
				continue
			for field in doc.get("fields", []):
				length = field.get("length") or 0
				if field.get("fieldtype") == "Data" and length > MAX_DATA_LENGTH:
					too_long.append(f"{doc.get('name')}.{field['fieldname']} ({length})")
		self.assertEqual(too_long, [], f"Data fields longer than a varchar: {too_long}")

	def test_every_field_order_entry_exists(self):
		"""A name in `field_order` with no field behind it silently disappears
		from the form, which is the kind of thing nobody notices for months."""
		missing = []
		for path in doctype_files():
			doc = json.loads(path.read_text())
			if doc.get("doctype") != "DocType":
				continue
			known = {field["fieldname"] for field in doc.get("fields", [])}
			for name in doc.get("field_order", []):
				if name not in known:
					missing.append(f"{doc.get('name')}.{name}")
		self.assertEqual(missing, [], f"field_order names with no field: {missing}")
