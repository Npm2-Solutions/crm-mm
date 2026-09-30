# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import sha256_hash

from crm.marchio import nome
from crm.permissions import livelli, utenti

INVITABLE_ROLES = ("Sales User", "Sales Manager", "System Manager")


class CRMInvitation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		accepted_at: DF.Datetime | None
		email: DF.Data
		email_sent_at: DF.Datetime | None
		invited_by: DF.Link | None
		key: DF.Data | None
		levels: DF.SmallText | None
		role: DF.Literal["", "Sales User", "Sales Manager", "System Manager"]
		status: DF.Literal["", "Pending", "Accepted", "Expired"]
	# end: auto-generated types

	def before_insert(self):
		frappe.utils.validate_email_address(self.email, True)

		self.set_key()
		self.invited_by = frappe.session.user
		self.status = "Pending"

	def set_key(self):
		# The key is a credential: it sets a new user's password and hands out a role. So it
		# only goes into the link mailed to the invitee, and what is stored is its hash, as
		# Frappe does for password reset keys: reading the record gives nothing that opens it.
		self._key = frappe.generate_hash()
		self.key = sha256_hash(self._key)
		# `key` sits on a permlevel nobody has, which would reset it on a Desk or REST insert
		self.flags.ignore_permlevel_for_fields = ["key"]

	def validate(self):
		# Whoever accepts a pending invitation gets its levels (or, the old way, its role),
		# so it may only carry what its inviter could grant: the rule `invite_by_email`
		# applies, enforced here for every way in (REST, Desk, code). Address, levels,
		# role and inviter can't change afterwards (set_only_once), and `accept` asks
		# again in case the inviter lost the right.
		if not self.status == "Pending":
			return
		if self.chiavi_livelli():
			if not can_grant_levels(self.invited_by, self.chiavi_livelli()):
				frappe.throw(
					_("{0} is not allowed to invite users with these levels").format(self.invited_by),
					frappe.PermissionError,
				)
		elif not self.role:
			frappe.throw(_("An invitation needs at least one level"))
		elif not can_grant_role(self.invited_by, self.role):
			frappe.throw(
				_("{0} is not allowed to invite users as {1}").format(self.invited_by, _(self.role)),
				frappe.PermissionError,
			)

	def chiavi_livelli(self) -> list[str]:
		return [riga.strip() for riga in (self.levels or "").splitlines() if riga.strip()]

	def can_be_granted_by(self, user: str | None) -> bool:
		if self.chiavi_livelli():
			return can_grant_levels(user, self.chiavi_livelli())
		return can_grant_role(user, self.role)

	def after_insert(self):
		self.invite_via_email(self._key)

	def invite_via_email(self, key):
		invite_link = frappe.utils.get_url(f"/api/method/crm.api.accept_invitation?key={key}")
		if frappe.local.dev_server:
			print(f"Invite link for {self.email}: {invite_link}")  # nosemgrep

		# the centre's name where it set one, the product's otherwise
		title = frappe.db.get_single_value("FCRM Settings", "brand_name") or nome()
		template = "crm_invitation"

		frappe.sendmail(
			recipients=self.email,
			subject=_("You have been invited to join {0}").format(title),
			template=template,
			args={"title": title, "invite_link": invite_link},
			now=True,
		)
		self.db_set("email_sent_at", frappe.utils.now())

	@frappe.whitelist()
	def accept_invitation(self):
		livelli.verifica("utenti.gestisci")
		# accepting on the invitee's behalf hands out the access just as inviting does
		if not self.can_be_granted_by(frappe.session.user):
			frappe.throw(_("You are not allowed to grant this access"), frappe.PermissionError)
		if self.accept():
			# the invitee was not around to set a password, mail them a link to do it
			frappe.get_doc("User", self.email).send_welcome_mail_to_user()

	def accept(self):
		if self.status != "Pending":
			frappe.throw(_("Invalid or expired key"))

		# checked when the invitation was sent, but the inviter may have lost the right since
		if not self.can_be_granted_by(self.invited_by):
			frappe.throw(_("This invitation is no longer valid"), frappe.PermissionError)

		user, is_new_user = self.create_user_if_not_exists()
		if self.chiavi_livelli():
			utenti.assegna_livelli(user.name, self.chiavi_livelli())
		else:
			user.append_roles(self.role)
			if self.role == "System Manager":
				user.append_roles("Sales Manager", "Sales User")
			elif self.role == "Sales Manager":
				user.append_roles("Sales User")
			if self.role == "Sales User":
				self.update_module_in_user(user, "FCRM")
			user.save(ignore_permissions=True)

		self.status = "Accepted"
		self.accepted_at = frappe.utils.now()
		self.key = None
		self.save(ignore_permissions=True)

		return is_new_user

	def update_module_in_user(self, user, module):
		block_modules = frappe.get_all(
			"Module Def",
			fields=["name as module"],
			filters={"name": ["!=", module]},
		)

		if block_modules:
			user.set("block_modules", block_modules)

	def create_user_if_not_exists(self):
		if not frappe.db.exists("User", self.email):
			first_name = self.email.split("@")[0].title()
			user = frappe.get_doc(
				doctype="User",
				user_type="System User",
				email=self.email,
				send_welcome_email=0,
				first_name=first_name,
				default_app="crm",
			).insert(ignore_permissions=True)
			return user, True

		return frappe.get_doc("User", self.email), False


def can_grant_levels(user: str | None, chiavi: list[str]) -> bool:
	"""Whether `user` may invite someone with these levels.

	Whoever manages users - a Manager, or the agency - gives any level this site
	offers. Never System Manager: no level carries it.
	"""
	if not user or not chiavi:
		return False
	if not frappe.db.get_value("User", user, "enabled"):
		return False
	if not livelli.puo("utenti.gestisci", user):
		return False
	offerti = {livello.chiave for livello in utenti.livelli_offerti()}
	return all(chiave in offerti for chiave in chiavi)


def can_grant_role(user: str | None, role: str) -> bool:
	"""Whether `user` may invite someone as `role`: the rule `invite_by_email` applies.

	Sales Managers invite Sales Users; managers and admins are invited by System
	Managers only; a disabled account invites nobody.
	"""
	if not user or role not in INVITABLE_ROLES:
		return False
	if not frappe.db.get_value("User", user, "enabled"):
		return False

	roles = frappe.get_roles(user)
	if role == "Sales User":
		return "Sales Manager" in roles or "System Manager" in roles
	return "System Manager" in roles


def expire_invitations():
	"""expire invitations after 3 days"""
	from frappe.utils import add_days, now

	days = 3
	invitations_to_expire = frappe.db.get_all(
		"CRM Invitation", filters={"status": "Pending", "creation": ["<", add_days(now(), -days)]}
	)
	for invitation in invitations_to_expire:
		invitation = frappe.get_doc("CRM Invitation", invitation.name)
		invitation.status = "Expired"
		invitation.key = None
		invitation.save(ignore_permissions=True)
