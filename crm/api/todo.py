import frappe
from frappe import _

from crm.fcrm.doctype.crm_notification.crm_notification import in_grassetto, notify_user


def after_insert(doc, method):
	if doc.reference_type in ["CRM Lead", "CRM Deal"] and doc.reference_name and doc.allocated_to:
		fieldname = "lead_owner" if doc.reference_type == "CRM Lead" else "deal_owner"
		# Mirror assign_to: the latest assignment owns the record, overriding any prior owner.
		frappe.db.set_value(
			doc.reference_type, doc.reference_name, fieldname, doc.allocated_to, update_modified=False
		)

	if doc.reference_type in ["CRM Lead", "CRM Deal", "CRM Task"] and doc.reference_name and doc.allocated_to:
		notify_assigned_user(doc)


def on_update(doc, method):
	if (
		doc.has_value_changed("status")
		and doc.status == "Cancelled"
		and doc.reference_type in ["CRM Lead", "CRM Deal", "CRM Task"]
		and doc.reference_name
		and doc.allocated_to
	):
		notify_assigned_user(doc, is_cancelled=True)
		clear_owner_on_unassign(doc)


def clear_owner_on_unassign(doc):
	# Owner concept only exists for Lead/Deal, not Task.
	if doc.reference_type not in ["CRM Lead", "CRM Deal"]:
		return
	fieldname = "lead_owner" if doc.reference_type == "CRM Lead" else "deal_owner"
	# Mirror assign_to: cancelling an assignment clears the owner. Wrinkle (accepted):
	# removing one of several manual co-assignees also clears, since owner is single-valued.
	frappe.db.set_value(doc.reference_type, doc.reference_name, fieldname, None, update_modified=False)


def notify_assigned_user(doc, is_cancelled=False):
	_doc = frappe.get_doc(doc.reference_type, doc.reference_name)
	owner = frappe.get_cached_value("User", frappe.session.user, "full_name")
	notification_text = get_notification_text(owner, doc, _doc, is_cancelled)

	# the same sentence, without its markup
	message = frappe.utils.strip_html(notification_text).strip()

	redirect_to_doctype, redirect_to_name = get_redirect_to_doc(doc)

	notify_user(
		{
			"owner": frappe.session.user,
			"assigned_to": doc.allocated_to,
			"notification_type": "Assignment",
			"message": message,
			"notification_text": notification_text,
			"reference_doctype": doc.reference_type,
			"reference_docname": doc.reference_name,
			"redirect_to_doctype": redirect_to_doctype,
			"redirect_to_docname": redirect_to_name,
		}
	)


def get_notification_text(owner, doc, reference_doc, is_cancelled=False):
	doctype = doc.reference_type

	if doctype in ["CRM Lead", "CRM Deal"]:
		name = (
			reference_doc.lead_name or doc.reference_name
			if doctype == "CRM Lead"
			else reference_doc.organization or reference_doc.lead_name or doc.reference_name
		)
		if is_cancelled:
			frase = (
				_("{0} removed your assignment on the deal {1}")
				if doctype == "CRM Deal"
				else _("{0} removed your assignment on {1}")
			)
		else:
			frase = (
				_("{0} assigned you the deal {1}") if doctype == "CRM Deal" else _("{0} assigned {1} to you")
			)
		return f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                {frase.format(in_grassetto(owner), in_grassetto(name))}
            </div>
        """

	if doctype == "CRM Task":
		if is_cancelled:
			return f"""
                <div class="mb-2 leading-5 text-ink-gray-5">
                    <span>{
				_("Your assignment on task {0} has been removed by {1}").format(
					f'<span class="font-medium text-ink-gray-9">{reference_doc.title}</span>',
					f'<span class="font-medium text-ink-gray-9">{owner}</span>',
				)
			}</span>
                </div>
            """
		return f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{owner}</span>
                <span>{
			_("assigned a new task {0} to you").format(
				f'<span class="font-medium text-ink-gray-9">{reference_doc.title}</span>'
			)
		}</span>
            </div>
        """


def get_redirect_to_doc(doc):
	if doc.reference_type == "CRM Task":
		reference_doc = frappe.get_doc(doc.reference_type, doc.reference_name)
		return reference_doc.reference_doctype, reference_doc.reference_docname

	return doc.reference_type, doc.reference_name
