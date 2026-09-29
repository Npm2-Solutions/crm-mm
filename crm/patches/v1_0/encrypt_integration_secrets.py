import frappe
from frappe.utils.password import set_encrypted_password

# Data fields that became Password fields: the stored values move to __Auth, encrypted,
# and the column keeps the same mask of asterisks Frappe writes for any password.
SECRETS = {
	"FCRM Settings": ("access_key",),
	"CRM Meta Settings": ("webhook_verify_token",),
	"CRM Exotel Settings": ("api_key", "webhook_verify_token"),
	"ERPNext CRM Settings": ("api_key",),
	"CRM Booking Connection": ("webhook_token",),
}


def execute():
	for doctype, fieldnames in SECRETS.items():
		if frappe.get_meta(doctype).issingle:
			for fieldname in fieldnames:
				value = frappe.db.get_single_value(doctype, fieldname)
				if needs_encrypting(value):
					set_encrypted_password(doctype, doctype, value, fieldname)
					frappe.db.set_single_value(doctype, fieldname, "*" * len(value))
		else:
			for row in frappe.get_all(doctype, fields=["name", *fieldnames]):
				for fieldname in fieldnames:
					value = row.get(fieldname)
					if needs_encrypting(value):
						set_encrypted_password(doctype, row.name, value, fieldname)
						frappe.db.set_value(
							doctype, row.name, fieldname, "*" * len(value), update_modified=False
						)
		frappe.clear_cache(doctype=doctype)


def needs_encrypting(value: str | None) -> bool:
	# nothing stored, or already a mask whose secret is in __Auth: leave it
	return bool(value) and set(value) != {"*"}
