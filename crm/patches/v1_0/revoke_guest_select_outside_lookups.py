import frappe

from crm.api.form import GUEST_LINKABLE_DOCTYPES, _link_target_doctypes


def execute():
	"""Take back the Guest `select` the form builder granted outside the lookup lists.

	grant_guest_link_access used to accept any doctype a lead or deal field links to,
	User and Contact included, and every grant let anyone holding a form link list
	those records. The rows it wrote are recognisable: Guest, level 0, `select` and
	nothing else, on a Link target of a CRM form. Anything shaped otherwise was set up
	by hand in Role Permissions and is left alone.
	"""
	for doctype in _link_target_doctypes() - set(GUEST_LINKABLE_DOCTYPES):
		rows = frappe.get_all(
			"Custom DocPerm",
			filters={
				"parent": doctype,
				"role": "Guest",
				"permlevel": 0,
				"if_owner": 0,
				"select": 1,
				"read": 0,
				"write": 0,
				"create": 0,
				"delete": 0,
			},
			pluck="name",
		)
		if not rows:
			continue
		frappe.db.delete("Custom DocPerm", {"name": ("in", rows)})
		frappe.clear_cache(doctype=doctype)
