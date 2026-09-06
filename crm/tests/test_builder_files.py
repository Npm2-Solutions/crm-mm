# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""What we ship to Frappe Builder must be well-formed before Builder ever sees it.

These records are imported by Builder's `sync_standard_builder_pages` at install and
migrate time — a malformed block tree or a data script with a syntax error surfaces as a
broken page on a customer's site, not as a test failure. So the shape is checked here.

The structural checks run whether or not Builder is installed; the round-trip through
`get_component_data` only runs when it is.
"""

import json
import os
import re

import frappe
from frappe.tests import IntegrationTestCase

import crm

COMPONENTS_PATH = os.path.join(os.path.dirname(crm.__file__), "builder_files", "components")

# keys Builder's Block dataclass understands (builder/utils.py); anything else is a typo
KNOWN_BLOCK_KEYS = {
	"blockId",
	"children",
	"baseStyles",
	"mobileStyles",
	"tabletStyles",
	"rawStyles",
	"attributes",
	"classes",
	"dataKey",
	"blockName",
	"element",
	"draggable",
	"innerText",
	"innerHTML",
	"extendedFromComponent",
	"componentVersion",
	"originalElement",
	"isChildOfComponent",
	"referenceBlockId",
	"isRepeaterBlock",
	"visibilityCondition",
	"elementBeforeConversion",
	"customAttributes",
	"dynamicValues",
	"props",
	"clientScript",
}

VALID_COMES_FROM = {"props", "componentData", "dataScript"}


def iter_blocks(block):
	yield block
	for child in block.get("children") or []:
		yield from iter_blocks(child)


def component_files():
	if not os.path.isdir(COMPONENTS_PATH):
		return []
	return [
		(name, os.path.join(COMPONENTS_PATH, name, f"{name}.json"))
		for name in sorted(os.listdir(COMPONENTS_PATH))
		if os.path.isdir(os.path.join(COMPONENTS_PATH, name)) and name != "__pycache__"
	]


class TestBuilderFiles(IntegrationTestCase):
	def test_at_least_one_component_is_shipped(self):
		self.assertTrue(component_files(), "no Builder components found in crm/builder_files/components")

	def test_fixtures_are_importable(self):
		"""make_records() looks for <folder>/<folder>.json and imports it by `name`."""
		for folder, path in component_files():
			with self.subTest(component=folder):
				self.assertTrue(os.path.exists(path), f"{path} missing — folder and file must match")
				doc = json.loads(open(path, encoding="utf-8").read())
				self.assertEqual(doc.get("doctype"), "Builder Component")
				# Builder Component is autonamed `field:component_id`
				self.assertEqual(doc.get("name"), doc.get("component_id"))
				self.assertTrue(doc.get("component_name"), "component_name is what the editor shows")

	def test_block_trees_are_well_formed(self):
		for folder, path in component_files():
			with self.subTest(component=folder):
				doc = json.loads(open(path, encoding="utf-8").read())
				root = json.loads(doc["block"])
				seen_ids = set()

				for block in iter_blocks(root):
					unknown = set(block) - KNOWN_BLOCK_KEYS
					self.assertFalse(unknown, f"unknown block keys: {sorted(unknown)}")
					self.assertTrue(block.get("element"), "every block needs an element")

					block_id = block.get("blockId")
					self.assertTrue(block_id, "every block needs a blockId")
					self.assertNotIn(block_id, seen_ids, f"duplicate blockId {block_id}")
					seen_ids.add(block_id)

					for dv in block.get("dynamicValues") or []:
						self.assertIn(dv.get("comesFrom"), VALID_COMES_FROM)
						self.assertTrue(dv.get("key"))
						self.assertTrue(dv.get("property"))

					if block.get("isRepeaterBlock"):
						# get_block_html reads children[0] and nothing else
						self.assertEqual(
							len(block.get("children") or []),
							1,
							"a repeater renders exactly one child",
						)
						data_key = block.get("dataKey") or {}
						self.assertTrue(data_key.get("key"), "a repeater needs a dataKey")
						self.assertIn(data_key.get("comesFrom"), VALID_COMES_FROM)

	def test_data_scripts_compile(self):
		"""A syntax error here would only show up as a broken page on a customer's site."""
		for folder, path in component_files():
			with self.subTest(component=folder):
				doc = json.loads(open(path, encoding="utf-8").read())
				script = doc.get("component_data_script") or ""
				if not script:
					continue
				compile(script, f"<{folder}>", "exec")
				self.assertNotIn("import ", script, "safe_exec forbids imports")
				self.assertNotIn("__", script, "safe_exec forbids dunder access")

	def test_props_referenced_by_blocks_exist_on_the_root(self):
		for folder, path in component_files():
			with self.subTest(component=folder):
				doc = json.loads(open(path, encoding="utf-8").read())
				root = json.loads(doc["block"])
				declared = set(root.get("props") or {})
				for block in iter_blocks(root):
					for dv in block.get("dynamicValues") or []:
						if dv.get("comesFrom") == "props":
							self.assertIn(dv["key"], declared, f"prop {dv['key']} is not declared")

	def test_component_data_round_trip(self):
		"""With Builder installed, the shipped script must actually return rows."""
		if "builder" not in frappe.get_installed_apps():
			self.skipTest("builder app is not installed on this site")

		from builder.builder.doctype.builder_component.builder_component import get_component_data

		if not frappe.db.exists("Builder Component", "crm-servizi"):
			self.skipTest("crm-servizi not synced — run `bench --site <site> migrate`")

		service = frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": "Spike Service",
				"enabled": 1,
				"duration": 30,
				"publish_on_website": 1,
			}
		).insert(ignore_permissions=True)
		try:
			data = get_component_data("crm-servizi")
			self.assertIn("servizi", data)
			names = [row["nome"] for row in data["servizi"]]
			self.assertIn("Spike Service", names)
			self.assertEqual(data["vuoto"], 0)
		finally:
			service.delete(ignore_permissions=True)

	def test_jinja_calls_in_blocks_are_registered_methods(self):
		"""A block whose markup calls `{{ crm_form_html(...) }}` renders nothing unless the
		method is in `hooks.jinja`. That mismatch is silent on a live page, so it is caught
		here instead."""
		registered = set()
		for path in frappe.get_hooks("jinja").get("methods") or []:
			registered.add(path.rsplit(".", 1)[-1])

		called = re.compile(r"\{\{\s*([a-zA-Z_][\w]*)\s*\(")
		for folder, path in component_files():
			doc = json.loads(open(path, encoding="utf-8").read())
			for block in iter_blocks(json.loads(doc["block"])):
				for name in called.findall(block.get("innerHTML") or ""):
					with self.subTest(component=folder, method=name):
						self.assertIn(name, registered, f"{name}() is not registered in hooks.jinja")

	def test_shipped_components_cover_the_crm_blocks(self):
		"""The set a page needs to be a CRM site rather than a brochure."""
		shipped = {folder for folder, _path in component_files()}
		for expected in ("crm_servizi", "crm_prodotti", "crm_form", "crm_prenota", "crm_contatti"):
			self.assertIn(expected, shipped)
