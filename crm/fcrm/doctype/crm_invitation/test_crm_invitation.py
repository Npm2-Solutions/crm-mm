# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Invitations: who may invite whom, and what the invitation link can do.

The key in the link is a credential — for a new user it sets the password, for
anyone it hands out a role. So it only ever reaches the invitee's inbox, the
role must be one the inviter could grant, and an existing account still has to
log in to take it.
"""

from contextlib import contextmanager
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import frappe
import frappe.client
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now

from crm.api import accept_invitation, invite_by_email

SYSTEM_MANAGER = "invitations.admin@example.com"
SALES_MANAGER = "invitations.manager@example.com"
SALES_USER = "invitations.user@example.com"


class TestCRMInvitation(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_user(SYSTEM_MANAGER, "System Manager")
		make_user(SALES_MANAGER, "Sales Manager")
		make_user(SALES_USER, "Sales User")
		frappe.local.form_dict = frappe._dict()
		frappe.local.response = frappe._dict(docs=[])

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def invite(self, email, role="Sales User", by="Administrator"):
		"""Invite `email` from the CRM settings as `by`: the invitation, and the key mailed to them."""
		frappe.set_user(by)
		with patch.object(frappe, "sendmail") as sendmail:
			invite_by_email(email, role)
		frappe.set_user("Administrator")
		name = frappe.db.get_value("CRM Invitation", {"email": email, "status": "Pending"})
		return frappe.get_doc("CRM Invitation", name), mailed_key(sendmail)

	def make_invitation(self, email="invitee@example.com", role="Sales User"):
		"""An invitation made on the Desk form, as a System Manager can — for an existing user too."""
		with patch.object(frappe, "sendmail") as sendmail:
			invitation = frappe.get_doc(doctype="CRM Invitation", email=email, role=role).insert()
		return invitation, mailed_key(sendmail)

	@contextmanager
	def watching_logins(self):
		with patch.object(frappe.local, "login_manager", create=True) as login_manager:
			yield login_manager.login_as

	# The normal flow: invite, accept, expire

	def test_invite_by_email_creates_a_pending_invitation(self):
		invitation, key = self.invite("newcomer@example.com", "Sales User", by=SALES_MANAGER)

		self.assertEqual(invitation.status, "Pending")
		self.assertEqual(invitation.role, "Sales User")
		self.assertEqual(invitation.invited_by, SALES_MANAGER)
		self.assertTrue(invitation.email_sent_at)
		self.assertTrue(key)

	def test_a_new_user_accepts_and_is_sent_to_set_a_password(self):
		invitation, key = self.invite("newcomer@example.com", "Sales Manager", by=SYSTEM_MANAGER)

		frappe.set_user("Guest")
		accept_invitation(key=key)

		self.assertEqual(frappe.local.response["type"], "redirect")
		self.assertIn("/update-password?key=", frappe.local.response["location"])
		invitation.reload()
		self.assertEqual(invitation.status, "Accepted")
		self.assertTrue(invitation.accepted_at)
		roles = frappe.get_roles("newcomer@example.com")
		self.assertIn("Sales Manager", roles)
		self.assertIn("Sales User", roles)
		self.assertEqual(frappe.db.get_value("User", "newcomer@example.com", "default_app"), "crm")

	def test_the_link_works_once(self):
		invitation, key = self.invite("newcomer@example.com")

		frappe.set_user("Guest")
		accept_invitation(key=key)

		self.assertIsNone(frappe.db.get_value("CRM Invitation", invitation.name, "key"))
		self.assertRaises(frappe.ValidationError, accept_invitation, key=key)

	def test_accept_already_accepted_raises(self):
		invitation, _key = self.make_invitation()
		invitation.accept()

		invitation.reload()
		with self.assertRaises(frappe.ValidationError):
			invitation.accept()

	def test_accept_expired_invitation_raises(self):
		invitation, _key = self.make_invitation()
		invitation.status = "Expired"
		invitation.save(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			invitation.accept()

	def test_accept_reports_newly_created_user(self):
		invitation, _key = self.make_invitation(email="brand-new@example.com")

		self.assertTrue(invitation.accept())

	def test_accept_reports_existing_user(self):
		make_user("already-there@example.com")
		invitation, _key = self.make_invitation(email="already-there@example.com")

		self.assertFalse(invitation.accept())

	def test_accept_invitation_logs_in_existing_user(self):
		"""An existing user already has a password, so log them straight in."""
		make_user("existing-invitee@example.com")
		_invitation, key = self.make_invitation(email="existing-invitee@example.com")

		with self.watching_logins() as login_as:
			accept_invitation(key=key)

		login_as.assert_called_once_with("existing-invitee@example.com")
		self.assertEqual(frappe.local.response["location"], "/crm")

	def test_desk_accept_mails_new_user_a_set_password_link(self):
		invitation, _key = self.make_invitation(email="desk-invitee@example.com")

		with patch("frappe.core.doctype.user.user.User.send_welcome_mail_to_user") as welcome_mail:
			invitation.accept_invitation()

		welcome_mail.assert_called_once()

	def test_desk_accept_does_not_mail_existing_user(self):
		make_user("desk-existing@example.com")
		invitation, _key = self.make_invitation(email="desk-existing@example.com")

		with patch("frappe.core.doctype.user.user.User.send_welcome_mail_to_user") as welcome_mail:
			invitation.accept_invitation()

		welcome_mail.assert_not_called()

	def test_expire_invitations_expires_old_pending_invites(self):
		from crm.fcrm.doctype.crm_invitation.crm_invitation import expire_invitations

		invitation, key = self.make_invitation(email="stale@example.com")
		frappe.db.set_value(
			"CRM Invitation", invitation.name, "creation", add_days(now(), -4), update_modified=False
		)

		expire_invitations()

		self.assertEqual(frappe.db.get_value("CRM Invitation", invitation.name, "status"), "Expired")
		self.assertRaises(frappe.ValidationError, accept_invitation, key=key)

	# Who may hand out which role. Exploit 1: a Sales Manager invited their own
	# address as System Manager through REST, read the key back, opened the link.

	def test_a_sales_manager_cannot_make_themselves_system_manager(self):
		frappe.set_user(SALES_MANAGER)
		with patch.object(frappe, "sendmail"), self.watching_logins():
			try:
				invitation = frappe.client.insert(
					{"doctype": "CRM Invitation", "email": SALES_MANAGER, "role": "System Manager"}
				)
				key = frappe.client.get_value("CRM Invitation", "key", invitation["name"])["key"]
				accept_invitation(key=key)
			except frappe.PermissionError:
				pass

		self.assertNotIn("System Manager", frappe.get_roles(SALES_MANAGER))

	def test_the_role_must_be_one_the_inviter_can_grant(self):
		"""However the invitation is inserted, it follows the rule `invite_by_email` applies."""
		cases = (
			(SALES_MANAGER, "Sales User", True),
			(SALES_MANAGER, "Sales Manager", False),
			(SALES_MANAGER, "System Manager", False),
			(SALES_USER, "Sales User", False),
			(SYSTEM_MANAGER, "Sales Manager", True),
			(SYSTEM_MANAGER, "System Manager", True),
		)
		for i, (inviter, role, allowed) in enumerate(cases):
			with self.subTest(inviter=inviter, role=role):
				frappe.set_user(inviter)
				invitation = frappe.get_doc(
					doctype="CRM Invitation", email=f"invitee{i}@example.com", role=role
				)
				with patch.object(frappe, "sendmail"):
					if allowed:
						invitation.insert(ignore_permissions=True)
					else:
						self.assertRaises(frappe.PermissionError, invitation.insert, ignore_permissions=True)

	def test_address_role_and_inviter_are_fixed_once_invited(self):
		"""Otherwise a harmless invitation could be edited into a manager one, or sent elsewhere."""
		invitation, _key = self.make_invitation("fixed@example.com", "Sales User")

		for field, value in (
			("email", "other@example.com"),
			("role", "Sales Manager"),
			("invited_by", SYSTEM_MANAGER),
		):
			with self.subTest(field=field):
				doc = frappe.get_doc("CRM Invitation", invitation.name)
				doc.set(field, value)
				self.assertRaises(frappe.CannotChangeConstantError, doc.save)

	def test_accepting_checks_the_inviter_again(self):
		"""An admin who has lost the role since sending the invitation no longer hands it out."""
		_invitation, key = self.invite("late@example.com", "Sales Manager", by=SYSTEM_MANAGER)
		frappe.get_doc("User", SYSTEM_MANAGER).remove_roles("System Manager")

		frappe.set_user("Guest")
		self.assertRaises(frappe.PermissionError, accept_invitation, key=key)
		self.assertFalse(frappe.db.exists("User", "late@example.com"))

	def test_a_disabled_inviter_hands_out_nothing(self):
		_invitation, key = self.invite("late@example.com", "Sales User", by=SALES_MANAGER)
		frappe.db.set_value("User", SALES_MANAGER, "enabled", 0)

		frappe.set_user("Guest")
		self.assertRaises(frappe.PermissionError, accept_invitation, key=key)
		self.assertFalse(frappe.db.exists("User", "late@example.com"))

	def test_accepting_on_the_desk_needs_someone_who_could_grant_the_role(self):
		invitation, _key = self.make_invitation("future.admin@example.com", "System Manager")

		frappe.set_user(SALES_MANAGER)
		with patch("frappe.core.doctype.user.user.User.send_welcome_mail_to_user"):
			self.assertRaises(frappe.PermissionError, invitation.accept_invitation)
		self.assertFalse(frappe.db.exists("User", "future.admin@example.com"))


def make_user(email, *roles):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			doctype="User",
			user_type="System User",
			email=email,
			first_name=email.split("@")[0],
			send_welcome_email=0,
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	if roles:
		user.add_roles(*roles)
	return user


def mailed_key(sendmail):
	"""The key in the link mailed to the invitee: the one place it is meant to exist."""
	link = sendmail.call_args.kwargs["args"]["invite_link"]
	return parse_qs(urlparse(link).query)["key"][0]
