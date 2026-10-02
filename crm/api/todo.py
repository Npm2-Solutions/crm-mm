import frappe

from crm.fcrm.doctype.crm_notification.crm_notification import nome_di
from crm.notifiche import regole as R
from crm.notifiche.avvisi import avvisa, nome_utente


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
	"""Somebody assigned a person, a deal or a task, or took it back: the one it is
	for reads it in their panel, the person or deal it belongs to a click away."""
	da = frappe.session.user
	if doc.reference_type == "CRM Task":
		compito = frappe.db.get_value(
			"CRM Task", doc.reference_name, ["title", "reference_doctype", "reference_docname"], as_dict=True
		)
		if not compito:
			return
		frase = R.COMPITO_TOLTO if is_cancelled else R.COMPITO
		nomi = [nome_utente(da), compito.title or doc.reference_name]
		riguarda = (compito.reference_doctype, compito.reference_docname)
	else:
		trattativa = doc.reference_type == "CRM Deal"
		if is_cancelled:
			frase = R.TOLTA_TRATTATIVA if trattativa else R.TOLTA
		else:
			frase = R.ASSEGNATA_TRATTATIVA if trattativa else R.ASSEGNATA
		nomi = [nome_utente(da), nome_di(doc.reference_type, doc.reference_name)]
		riguarda = (doc.reference_type, doc.reference_name)

	avvisa(
		doc.allocated_to,
		"Assignment",
		frase,
		nomi,
		da=da,
		riguarda=riguarda,
		oggetto=(doc.reference_type, doc.reference_name),
	)
