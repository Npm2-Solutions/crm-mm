import frappe
from frappe.query_builder import Order


@frappe.whitelist()
def get_notifications():
	Notification = frappe.qb.DocType("CRM Notification")
	query = (
		frappe.qb.from_(Notification)
		.select("*")
		.where(Notification.to_user == frappe.session.user)
		.orderby("creation", order=Order.desc)
	)
	notifications = query.run(as_dict=True)

	_notifications = []
	for notification in notifications:
		_notifications.append(
			{
				"creation": notification.creation,
				"from_user": {
					"name": notification.from_user,
					"full_name": frappe.get_value("User", notification.from_user, "full_name"),
				},
				"type": notification.type,
				"to_user": notification.to_user,
				"read": notification.read,
				"hash": get_hash(notification),
				"notification_text": notification.notification_text,
				"notification_type_doctype": notification.notification_type_doctype,
				"notification_type_doc": notification.notification_type_doc,
				"reference_doctype": ("deal" if notification.reference_doctype == "CRM Deal" else "lead"),
				"reference_name": notification.reference_name,
				"route_name": _route_of(notification),
			}
		)

	return _notifications


@frappe.whitelist()
def mark_as_read(doc: str | None = None):
	user = frappe.session.user
	filters = {"to_user": user, "read": False}
	or_filters = []
	if doc:
		or_filters = [
			{"comment": doc},
			{"notification_type_doc": doc},
		]
	for n in frappe.get_all("CRM Notification", filters=filters, or_filters=or_filters):
		d = frappe.get_doc("CRM Notification", n.name)
		d.read = True
		d.save()


def _route_of(notification) -> str:
	# "did they come?" opens the desk's day, where the answers are given
	if notification.type == "Agenda":
		return "Today"
	return "Deal" if notification.reference_doctype == "CRM Deal" else "Lead"


def get_hash(notification):
	_hash = ""
	if notification.type == "Mention" and notification.notification_type_doc:
		_hash = "#" + notification.notification_type_doc

	if notification.type == "WhatsApp":
		_hash = "#whatsapp"

	# a question from the patient area: on the person's board, in the Clinic tab
	if notification.type == "Area":
		_hash = "#clinic"

	# the person's tasks, while the task is still theirs (the sentence is in the
	# language of whoever assigned it: it is not what says so)
	if notification.type == "Assignment" and notification.notification_type_doctype == "CRM Task":
		ancora = frappe.db.exists(
			"ToDo",
			{
				"reference_type": "CRM Task",
				"reference_name": notification.notification_type_doc,
				"allocated_to": notification.to_user,
				"status": ("!=", "Cancelled"),
			},
		)
		_hash = "#tasks" if ancora else ""
	return _hash
