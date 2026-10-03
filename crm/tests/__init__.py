import json
import os

import frappe


def before_tests():
	load_crm_user_test_records()


def load_crm_user_test_records():
	"""Load CRM user test records from crm/tests/test_records.json"""
	test_records_path = os.path.join(os.path.dirname(__file__), "test_records.json")

	if os.path.exists(test_records_path):
		with open(test_records_path) as f:
			test_records = json.load(f)

		for record in test_records:
			if not frappe.db.exists("User", record.get("email")):
				doc = frappe.get_doc(record)
				doc.insert(ignore_permissions=True, ignore_if_duplicate=True)


def con_whatsapp() -> bool:
	"""Whether this bench has frappe_whatsapp. The CI's has only frappe and crm:
	what needs WhatsApp's DocTypes is skipped there, and runs where the app is."""
	from crm.api.whatsapp import is_whatsapp_installed

	return is_whatsapp_installed()


def serve_whatsapp(caso) -> None:
	"""Skip ``caso`` where frappe_whatsapp is not installed."""
	if not con_whatsapp():
		caso.skipTest("frappe_whatsapp is not installed on this bench")
