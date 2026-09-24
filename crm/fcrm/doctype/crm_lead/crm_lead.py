# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.desk.form.assign_to import _add as assign
from frappe.model.document import Document
from frappe.utils import validate_email_address

from crm.api.mirror import FROM_LEAD, FROM_ORGANIZATION
from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
	add_status_change_log,
)
from crm.utils import digits_of, to_e164

LEAD_DEAL_FIELD_MAP = {"lead_owner": "deal_owner"}


class CRMLead(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_lead_facebook_submission.crm_lead_facebook_submission import (
			CRMLeadFacebookSubmission,
		)
		from crm.fcrm.doctype.crm_products.crm_products import CRMProducts
		from crm.fcrm.doctype.crm_rolling_response_time.crm_rolling_response_time import (
			CRMRollingResponseTime,
		)
		from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import CRMStatusChangeLog

		annual_revenue: DF.Currency
		communication_status: DF.Link | None
		conversation_assigned_to: DF.Link | None
		conversation_seen_by: DF.Link | None
		conversation_snoozed_until: DF.Datetime | None
		conversation_status: DF.Literal["Open", "Handled"]
		conversation_unread: DF.Check
		conversation_seen_until: DF.Datetime | None
		converted: DF.Check
		email: DF.Data | None
		facebook_form_id: DF.Data | None
		facebook_lead_id: DF.Data | None
		facebook_submissions: DF.Table[CRMLeadFacebookSubmission]
		first_name: DF.Data
		first_responded_on: DF.Datetime | None
		first_response_time: DF.Duration | None
		first_touch_campaign: DF.Data | None
		first_touch_category: (
			DF.Literal[
				"",
				"Paid Search",
				"Paid Social",
				"Organic Search",
				"Organic Social",
				"Email",
				"SMS",
				"Affiliate",
				"Referral",
				"Direct Traffic",
				"CRM UI",
				"Third Party",
				"Unknown",
			]
			| None
		)
		first_touch_content: DF.Data | None
		first_touch_landing_page: DF.SmallText | None
		first_touch_medium: DF.Data | None
		first_touch_on: DF.Datetime | None
		first_touch_referrer: DF.SmallText | None
		first_touch_session: DF.Link | None
		first_touch_source: DF.Data | None
		first_touch_term: DF.Data | None
		gender: DF.Link | None
		image: DF.AttachImage | None
		industry: DF.Link | None
		job_title: DF.Data | None
		last_name: DF.Data | None
		last_responded_on: DF.Datetime | None
		last_response_time: DF.Duration | None
		last_answered_on: DF.Datetime | None
		last_conversation_channel: DF.Literal["", "WhatsApp", "SMS", "Email"]
		last_conversation_direction: DF.Literal["", "Incoming", "Outgoing"]
		last_conversation_on: DF.Datetime | None
		last_conversation_preview: DF.SmallText | None
		last_touch_campaign: DF.Data | None
		last_touch_category: (
			DF.Literal[
				"",
				"Paid Search",
				"Paid Social",
				"Organic Search",
				"Organic Social",
				"Email",
				"SMS",
				"Affiliate",
				"Referral",
				"Direct Traffic",
				"CRM UI",
				"Third Party",
				"Unknown",
			]
			| None
		)
		last_touch_content: DF.Data | None
		last_touch_landing_page: DF.SmallText | None
		last_touch_medium: DF.Data | None
		last_touch_on: DF.Datetime | None
		last_touch_referrer: DF.SmallText | None
		last_touch_session: DF.Link | None
		last_touch_source: DF.Data | None
		last_touch_term: DF.Data | None
		lead_name: DF.Data | None
		lead_owner: DF.Link | None
		lost_notes: DF.Text | None
		lost_reason: DF.Link | None
		middle_name: DF.Data | None
		mobile_no: DF.Data | None
		naming_series: DF.Literal["CRM-LEAD-.YYYY.-"]
		net_total: DF.Currency
		no_of_employees: DF.Literal["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
		organization: DF.Link | None
		phone: DF.Data | None
		products: DF.Table[CRMProducts]
		response_by: DF.Datetime | None
		rolling_responses: DF.Table[CRMRollingResponseTime]
		salutation: DF.Link | None
		sla: DF.Link | None
		sla_creation: DF.Datetime | None
		sla_status: DF.Literal["", "First Response Due", "Rolling Response Due", "Failed", "Fulfilled"]
		source: DF.Link | None
		status: DF.Link
		status_change_log: DF.Table[CRMStatusChangeLog]
		territory: DF.Link | None
		total: DF.Currency
		visitor: DF.Link | None
		website: DF.Data | None
	# end: auto-generated types

	def before_insert(self):
		# apply CRM enrichment (source/contact) when created via a web form
		from crm.api.form import enrich_form_submission

		enrich_form_submission(self)

	def _validate_links(self):
		"""Make the company real before Frappe checks that it is.

		The company is a Link now, so two people from the same firm are two
		people of one company instead of two strings that look alike. But a
		company name arrives from everywhere — a lead ad answer, a web form, an
		enrichment, somebody typing — and Frappe validates links BEFORE any hook
		on insert, so a `validate` would be too late and the lead would be
		rejected rather than saved.

		This runs at the only moment that covers every path in and both insert
		and save, because every one of them goes through here.
		"""
		self.ensure_organization()
		return super()._validate_links()

	def ensure_organization(self):
		"""The company named on this person, created if the CRM has none.

		`CRM Organization` is named after itself, so a name that is already a
		company is already the link — there is nothing to do for it. A new one
		is born with what this person knows about it, which is more than a name
		and would otherwise be lost.
		"""
		if not self.organization or frappe.db.exists("CRM Organization", self.organization):
			return
		organization = frappe.new_doc("CRM Organization")
		organization.update(
			{
				"organization_name": self.organization,
				"website": self.website,
				"territory": self.territory,
				"industry": self.industry,
				"annual_revenue": self.annual_revenue,
				"no_of_employees": self.no_of_employees,
				"company_description": self.company_description,
			}
		)
		organization.flags.ignore_mandatory = True
		organization.insert(ignore_permissions=True)
		self.organization = organization.name

	def before_validate(self):
		self.set_sla()

	def validate(self):
		self.sync_with_contact()
		self.set_full_name()
		self.set_lead_name()
		self.set_title()
		self.validate_email()
		if not self.is_new() and self.has_value_changed("lead_owner") and self.lead_owner:
			self.share_with_agent(self.lead_owner)
			self.assign_agent(self.lead_owner)
		if self.has_value_changed("status"):
			add_status_change_log(self)

	def after_insert(self):
		self.ensure_contact()

		if self.lead_owner:
			if self.lead_owner != frappe.session.user:
				self.share_with_agent(self.lead_owner)
			self.assign_agent(self.lead_owner)

		# Auto-enrich a new Lead from its website (best-effort, background job).
		from crm.domain_enrichment.tasks import auto_enrich_on_create

		auto_enrich_on_create(self)

	def before_save(self):
		self.apply_sla()

	def set_full_name(self):
		if self.first_name:
			self.lead_name = " ".join(
				name
				for name in [
					self.salutation,
					self.first_name,
					self.middle_name,
					self.last_name,
				]
				if name
			)

	def set_lead_name(self):
		if not self.lead_name:
			# Check for leads being created through data import
			if not self.organization and not self.email and not self.flags.ignore_mandatory:
				frappe.throw(_("A Lead requires either a person's name or an organization's name"))
			elif self.organization:
				self.lead_name = self.organization
			elif self.email:
				self.lead_name = self.email.split("@")[0]
			else:
				self.lead_name = "Unnamed Lead"

	def set_title(self):
		self.title = self.organization or self.lead_name

	def validate_email(self):
		if self.email:
			if not self.flags.ignore_email_validation:
				validate_email_address(self.email, throw=True)

			if self.email == self.lead_owner:
				frappe.throw(_("Lead Owner cannot be same as the Lead Email Address"))

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					# the agent is already set as an assignee
					return

		assign({"assign_to": [agent], "doctype": "CRM Lead", "name": self.name}, ignore_permissions=True)

	def share_with_agent(self, agent):
		if not agent:
			return

		docshares = frappe.get_all(
			"DocShare",
			filters={"share_name": self.name, "share_doctype": self.doctype},
			fields=["name", "user"],
		)

		shared_with = [d.user for d in docshares] + [agent]

		for user in shared_with:
			if user == agent and not frappe.db.exists(
				"DocShare",
				{"user": agent, "share_name": self.name, "share_doctype": self.doctype},
			):
				frappe.share.add_docshare(
					self.doctype,
					self.name,
					agent,
					write=1,
					flags={"ignore_share_permission": True},
				)
			elif user != agent:
				frappe.share.remove(
					self.doctype,
					self.name,
					user,
					flags={"ignore_share_permission": True, "ignore_permissions": True},
				)

	def sync_with_contact(self) -> None:
		"""Keep the person and their address book entry saying the same thing.

		One person, one entry, one number, one email — decided, not discovered.
		The entry is what an incoming message is resolved through; the fields here
		are the copy the two hundred places that read `lead.mobile_no` use, and
		editing them writes through instead of quietly drifting apart.
		"""
		if self.is_new() or not self.contact:
			return

		self.validate_one_person_per_contact()

		edited_here = [field for field in ("email", "mobile_no") if self.has_value_changed(field)]
		if edited_here:
			self.push_to_contact(edited_here)
		else:
			self.pull_from_contact()

	def validate_one_person_per_contact(self) -> None:
		"""One address book entry belongs to one person.

		Two people sharing an entry means one number with two owners: a reply
		would land on whichever the CRM happened to find first. Refused here
		rather than repaired later, because by then nobody knows which of the two
		the conversation was with.
		"""
		other = frappe.db.get_value("CRM Lead", {"contact": self.contact, "name": ["!=", self.name]}, "name")
		if other:
			frappe.throw(
				_("This address book entry already belongs to {0}").format(other),
				title=_("One person, one entry"),
			)

	def pull_from_contact(self) -> None:
		# the landline is not in the address book (see push_to_contact): it lives
		# here and nowhere else, so there is nothing to pull for it
		contact = frappe.db.get_value("Contact", self.contact, ["email_id", "mobile_no"], as_dict=True)
		if not contact:
			return
		self.email = contact.email_id or self.email
		self.mobile_no = contact.mobile_no or self.mobile_no

	def push_to_contact(self, fields: list[str]) -> None:
		"""Carry an edit made here over to the contact that owns it.

		The landline is deliberately not carried: the address book entry holds the
		one number the system writes to, and that is the mobile. A second number
		in there would be a second possible recipient, which is the doubt we
		decided not to have.
		"""
		doc = frappe.get_doc("Contact", self.contact)
		changed = False

		if "email" in fields and self.email:
			changed |= only_row(doc, "email_ids", "email_id", self.email, "is_primary")
		if "mobile_no" in fields and self.mobile_no:
			changed |= only_row(doc, "phone_nos", "phone", self.mobile_no, "is_primary_mobile_no")

		if changed:
			doc.save(ignore_permissions=True)

		# and the lead shows what the contact settled on: the same number, written
		# with its prefix, so nobody has to wonder whether to type one
		for field, source in (("email", "email_id"), ("mobile_no", "mobile_no")):
			if field in fields and doc.get(source):
				self.set(field, doc.get(source))

	def ensure_contact(self) -> None:
		"""Every lead is a person, and a person's details live in one place.

		Creating the contact here instead of at conversion is what stops the same
		person from existing twice: by the time the deal is opened there is
		nothing left to copy. A lead whose email already belongs to a contact
		joins that contact rather than making a second one.

		It never stops a lead from being created. This runs inside the insert's
		own transaction, so raising here would roll the lead back — and a lead
		that cannot be saved because of its address book is a worse outcome than
		a lead whose address book arrives a moment later, at conversion.
		"""
		if self.contact:
			return
		if not (self.first_name or self.last_name or self.email or self.mobile_no or self.phone):
			# an address book entry with a company name and nothing to reach it by
			# is not worth creating
			return

		try:
			existing = self.contact_exists(throw=False)
			if existing and not self.someone_elses(existing):
				self.db_set("contact", existing, update_modified=False)
				return

			self.db_set("contact", self.create_contact(throw=False), update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"CRM Lead: could not give {self.name} a contact")

	def someone_elses(self, contact: str) -> bool:
		"""Is this address book entry already somebody's?

		An entry belongs to one person. Sharing the one that matches this email
		would give one number two owners, and a reply would land on whichever the
		CRM found first — so this lead gets its own entry instead. Two entries
		with the same email is the lesser evil, and the entry points that dedupe a
		person (`crm.api.lead.find_person`) are what keep it rare.
		"""
		owner = frappe.db.get_value("CRM Lead", {"contact": contact, "name": ["!=", self.name]}, "name")
		return bool(owner)

	def create_contact(self, existing_contact=None, throw=True):
		if not self.lead_name:
			self.set_full_name()
			self.set_lead_name()

		existing_contact = existing_contact or self.contact_exists(throw)
		if existing_contact:
			self.update_lead_contact(existing_contact)
			return existing_contact

		contact = frappe.new_doc("Contact")
		contact.update(
			{
				"first_name": self.first_name or self.lead_name,
				"last_name": self.last_name,
				"salutation": self.salutation,
				"gender": self.gender,
				"designation": self.job_title,
				"company_name": self.organization,
				"image": self.image or "",
			}
		)

		if self.email:
			contact.append("email_ids", {"email_id": self.email, "is_primary": 1})

		# the landline is not an address book entry: it stays on the person, so the
		# entry holds the one number the system writes to
		if self.mobile_no:
			contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

		contact.insert(ignore_permissions=True)
		contact.reload()  # load changes by hooks on contact

		return contact.name

	def create_organization(self, existing_organization=None):
		"""The company this deal belongs to.

		Nothing is created here any more: the person is already linked to their
		company, because `ensure_organization` made it when the name was first
		written. What is left is the choice of somebody converting by hand, who
		may point the deal at a different company than the one on the person.
		"""
		organization = existing_organization or self.organization
		if not organization:
			return
		if organization != self.organization:
			# db_set writes past validation, so check first: a person pointed at
			# a company that does not exist is a link nothing would catch later
			if not frappe.db.exists("CRM Organization", organization):
				frappe.throw(_("Organization {0} does not exist").format(organization))
			self.db_set("organization", organization)
		self.copy_enrichment_from_organization()
		return organization

	def copy_enrichment_from_organization(self):
		"""Fill-empty copy of a linked enriched Organization's fields onto this Lead.

		Called when an existing (already-enriched) CRM Organization is linked. The
		shared helper mutates ``self`` in place (fill-empty, user data preserved);
		any filled native fields are then persisted with ``db_set`` to match this
		branch's already-saved flow. Best-effort -- never blocks the Lead save.
		"""
		from crm.domain_enrichment.cross_record import copy_enrichment_from_organization

		enriched_fields = (
			"organization_logo",
			"company_description",
			"industry",
			"linkedin",
			"twitter",
			"facebook",
		)
		before = {f: self.get(f) for f in enriched_fields if self.meta.has_field(f)}

		filled = copy_enrichment_from_organization(self)

		for fieldname, old_value in before.items():
			new_value = self.get(fieldname)
			if new_value != old_value:
				self.db_set(fieldname, new_value)
		return filled

	def update_lead_contact(self, contact):
		contact = frappe.get_cached_doc("Contact", contact)
		frappe.db.set_value(
			"CRM Lead",
			self.name,
			{
				"salutation": contact.salutation,
				"first_name": contact.first_name,
				"last_name": contact.last_name,
				"email": contact.email_id,
				"mobile_no": contact.mobile_no,
			},
		)

	def contact_exists(self, throw=True):
		# Match only on email which uniquely identifies a person
		if not self.email:
			return False

		email_exist = frappe.db.exists("Contact Email", {"email_id": self.email})
		if not email_exist:
			return False

		contact = frappe.db.get_value("Contact Email", email_exist, "parent")

		if throw:
			frappe.throw(
				_("Contact already exists with Email: {0}").format(self.email),
				title=_("Contact Already Exists"),
			)

		return contact

	def create_deal(self, contact, organization, deal=None):
		new_deal = frappe.new_doc("CRM Deal")

		restricted_fieldtypes = [
			"Tab Break",
			"Section Break",
			"Column Break",
			"HTML",
			"Button",
			"Attach",
		]
		restricted_map_fields = [
			"name",
			"naming_series",
			"creation",
			"owner",
			"modified",
			"modified_by",
			"idx",
			"docstatus",
			"status",
			"email",
			"mobile_no",
			"phone",
			"sla",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"communication_status",
			"sla_creation",
			"status_change_log",
		]
		# the person and the company are not copied any more: the deal mirrors
		# them from the lead and the organization it is linked to, so there is
		# one place where a name is right (see crm/api/mirror.py)
		restricted_map_fields += list(FROM_LEAD) + list(FROM_ORGANIZATION)

		for field in self.meta.fields:
			if field.fieldtype in restricted_fieldtypes:
				continue
			if field.fieldname in restricted_map_fields:
				continue

			fieldname = get_deal_fieldname(field, new_deal.meta)

			if fieldname:
				if fieldname == "organization":
					new_deal.update({fieldname: organization})
				else:
					new_deal.update({fieldname: self.get(field.fieldname)})

		new_deal.update(
			{
				"lead": self.name,
				"contacts": [{"contact": contact}],
			}
		)

		if self.first_responded_on:
			new_deal.update(
				{
					"sla_creation": self.sla_creation,
					"response_by": self.response_by,
					"sla_status": self.sla_status,
					"communication_status": self.communication_status,
					"first_response_time": self.first_response_time,
					"first_responded_on": self.first_responded_on,
				}
			)

		if deal:
			new_deal.update(deal)

		# Attribution needs no special handling here: the deal carries the same
		# fieldnames, so the generic copy above brings the two snapshots and the
		# visitor across, and the `bind_visitor` after_insert hook then hands the
		# browsing history to the deal as well.
		new_deal.insert(ignore_permissions=True)

		for user in self.get_assigned_users():
			if user and user != new_deal.deal_owner:
				new_deal.assign_agent(user)

		return new_deal.name

	def set_sla(self):
		"""
		Find an SLA to apply to the lead.
		"""
		if self.sla:
			return

		sla = get_sla(self)
		if not sla:
			self.first_responded_on = None
			self.first_response_time = None
			return
		self.sla = sla.name

	def apply_sla(self):
		"""
		Apply SLA if set.
		"""
		if not self.sla:
			return
		sla = frappe.get_last_doc("CRM Service Level Agreement", {"name": self.sla})
		if sla:
			sla.apply(self)

	def convert_to_deal(self, deal=None):
		return convert_to_deal(lead=self.name, doc=self, deal=deal)

	@staticmethod
	def get_non_filterable_fields():
		return ["converted"]

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Full Name",
				"type": "Data",
				"key": "lead_name",
				"width": "12rem",
			},
			{
				"label": "Organization",
				"type": "Link",
				"key": "organization",
				"options": "CRM Organization",
				"width": "10rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email",
				"width": "12rem",
			},
			{
				"label": "Mobile No.",
				"type": "Data",
				"key": "mobile_no",
				"width": "11rem",
			},
			{
				"label": "Assigned To",
				"type": "Text",
				"key": "_assign",
				"width": "10rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"lead_name",
			"organization",
			"email",
			"mobile_no",
			"lead_owner",
			"first_name",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"modified",
			"_assign",
			"image",
		]
		return {"columns": columns, "rows": rows}


@frappe.whitelist()
def convert_to_deal(
	lead: str,
	doc: Document | None = None,
	deal: str | dict | None = None,
	existing_contact: str | None = None,
	existing_organization: str | None = None,
):
	if not (doc and doc.flags.get("ignore_permissions")) and not frappe.has_permission(
		"CRM Lead", "write", lead
	):
		frappe.throw(_("Not allowed to convert Lead to Deal"), frappe.PermissionError)

	lead = frappe.get_cached_doc("CRM Lead", lead)
	# no status: the sale has one scale of states and it lives on the deal (doc 26)
	lead.db_set("converted", 1)
	if lead.sla and frappe.db.exists("CRM Communication Status", "Replied"):
		lead.db_set("communication_status", "Replied")
	# the contact was born with the lead: converting has nothing left to copy.
	# `existing_contact` still wins when the person is picked by hand, and a lead
	# from before this existed gets one made now.
	contact = existing_contact or lead.contact or lead.create_contact(throw=False)
	if contact != lead.contact:
		lead.db_set("contact", contact, update_modified=False)
	organization = lead.create_organization(existing_organization)
	_deal = lead.create_deal(contact, organization, deal)
	return _deal


def only_row(doc, table: str, fieldname: str, value: str, primary: str) -> bool:
	"""Leave `value` as the ONE number (or email) of this address book entry.

	One person, one way to reach them. A second number is a second question at
	every send — which one, and was the reply on the other one? — and the answer
	was worth less than the doubt. So this replaces rather than appends: the row
	that already holds the same number is kept (its id is referenced elsewhere)
	and everything else goes.

	"The same number" is the number itself, not how somebody typed it: with
	spaces, without the prefix, or with a plus, `3703400189` and `+393703400189`
	are one person — comparing the raw text made them two.
	"""
	rows = doc.get(table) or []
	same = (
		(lambda number: digits_of(to_e164(number)))
		if table == "phone_nos"
		else (lambda text: (text or "").strip().lower())
	)
	match = next((row for row in rows if same(row.get(fieldname)) == same(value)), None)

	if match and match.get(primary) and len(rows) == 1:
		return False

	if match:
		match.set(fieldname, value)
		match.set(primary, 1)
		doc.set(table, [match])
	else:
		doc.set(table, [])
		doc.append(table, {fieldname: value, primary: 1})
	return True


def get_deal_fieldname(field, deal_meta):
	mapped_fieldname = LEAD_DEAL_FIELD_MAP.get(field.fieldname)
	if mapped_fieldname:
		return mapped_fieldname if deal_meta.has_field(mapped_fieldname) else None
	if deal_meta.has_field(field.fieldname):
		return field.fieldname
	if not is_custom_field(field):
		return None
	return get_matching_custom_deal_field(field, deal_meta)


def get_matching_custom_deal_field(field, deal_meta):
	matches = [
		deal_field.fieldname for deal_field in deal_meta.fields if is_matching_custom_field(field, deal_field)
	]
	return matches[0] if len(matches) == 1 else None


def is_matching_custom_field(lead_field, deal_field):
	return (
		is_custom_field(deal_field)
		and lead_field.label == deal_field.label
		and lead_field.fieldtype == deal_field.fieldtype
	)


def is_custom_field(field):
	return bool(
		field.get("is_custom_field")
		or field.get("custom")
		or (field.fieldname or "").startswith("custom_")
		or field.name == f"{field.parent}-{field.fieldname}"
	)
