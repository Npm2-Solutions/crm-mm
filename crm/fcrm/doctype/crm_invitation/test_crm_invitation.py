# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
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
from frappe.api.v1 import read_doc
from frappe.desk import reportview
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now, sha256_hash

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

	def test_an_expired_invitation_can_be_sent_again(self):
		invitation, _key = self.invite("newcomer@example.com")
		frappe.db.set_value("CRM Invitation", invitation.name, "status", "Expired")

		frappe.set_user(SALES_MANAGER)
		with patch.object(frappe, "sendmail"):
			result = invite_by_email("newcomer@example.com", "Sales User")

		self.assertEqual(result["to_invite"], ["newcomer@example.com"])
		self.assertEqual(result["existing_invites"], [])

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

		self.assertEqual(
			frappe.db.get_value("CRM Invitation", invitation.name, ["status", "key"]), ("Expired", None)
		)
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

	# The key only ever reaches the invitee's inbox. Exploit 2: anyone who could
	# read CRM Invitation, Sales Users included, could list every pending key.

	def test_only_a_hash_of_the_key_is_stored(self):
		"""Whoever reads the record — Administrator, a backup, the database — gets nothing that opens it."""
		invitation, key = self.invite("future.admin@example.com", "System Manager")
		stored = frappe.db.get_value("CRM Invitation", invitation.name, "key")

		self.assertEqual(stored, sha256_hash(key))
		frappe.set_user("Guest")
		self.assertRaises(frappe.ValidationError, accept_invitation, key=stored)
		self.assertFalse(frappe.db.exists("User", "future.admin@example.com"))

	def test_an_invitation_made_on_the_desk_sends_a_working_link(self):
		"""Nobody may write `key` (permlevel 1), yet inserting as a System Manager must keep it."""
		frappe.set_user(SYSTEM_MANAGER)
		invitation, key = self.make_invitation("newcomer@example.com", "Sales User")

		self.assertEqual(frappe.db.get_value("CRM Invitation", invitation.name, "key"), sha256_hash(key))
		frappe.set_user("Guest")
		accept_invitation(key=key)
		self.assertIn("Sales User", frappe.get_roles("newcomer@example.com"))

	def test_readers_never_get_the_key_back(self):
		"""Managers still list invitations (Settings → Invite User), without the key or its hash."""
		invitation, key = self.invite("future.admin@example.com", "System Manager")
		stored = frappe.db.get_value("CRM Invitation", invitation.name, "key")

		for reader in (SALES_MANAGER, SYSTEM_MANAGER):
			with self.subTest(reader=reader):
				frappe.set_user(reader)
				answers = [
					# GET /api/resource/CRM Invitation, as the settings page and the Desk list do
					frappe.client.get_list("CRM Invitation", fields=["*"]),
					frappe.client.get_list("CRM Invitation", fields=["name", "email", "key"]),
					# GET /api/resource/CRM Invitation/<name>
					read_doc("CRM Invitation", invitation.name),
					frappe.client.get("CRM Invitation", invitation.name),
					frappe.client.get_value("CRM Invitation", ["name", "key"], invitation.name),
					report_view(
						doctype="CRM Invitation",
						fields=["`tabCRM Invitation`.`name`", "`tabCRM Invitation`.`key`"],
					),
				]
				self.assertTrue(any(invitation.name in frappe.as_json(answer) for answer in answers))
				self.assertNotIn(key, frappe.as_json(answers))
				self.assertNotIn(stored, frappe.as_json(answers))
				# nor can the key be guessed a character at a time through a filter
				self.assertRaises(
					frappe.PermissionError,
					frappe.client.get_list,
					"CRM Invitation",
					filters={"key": ["like", f"{stored[0]}%"]},
				)

	# Invitations are made through `invite_by_email` only, and only managers read them.

	def test_invitations_are_only_created_through_invite_by_email(self):
		for user in (SALES_MANAGER, SALES_USER):
			with self.subTest(user=user):
				frappe.set_user(user)
				with patch.object(frappe, "sendmail"), self.assertRaises(frappe.PermissionError):
					frappe.client.insert(
						{"doctype": "CRM Invitation", "email": "x@example.com", "role": "Sales User"}
					)

	def test_sales_users_cannot_read_invitations(self):
		self.invite("future.admin@example.com", "System Manager")

		frappe.set_user(SALES_USER)
		self.assertRaises(
			frappe.PermissionError, frappe.client.get_list, "CRM Invitation", fields=["name", "email"]
		)

	def test_a_sales_user_cannot_take_over_a_pending_invitation(self):
		"""The whole of exploit 2: list the pending keys, open a link, set the new admin's password."""
		self.invite("future.admin@example.com", "System Manager")

		frappe.set_user(SALES_USER)
		try:
			rows = frappe.client.get_list(
				"CRM Invitation", fields=["key"], filters={"email": "future.admin@example.com"}
			)
		except frappe.PermissionError:
			rows = []
		for key in [row.get("key") for row in rows if row.get("key")]:
			with self.watching_logins():
				accept_invitation(key=key)

		self.assertFalse(frappe.db.exists("User", "future.admin@example.com"))

	# The link logs no one in. Exploit 3: for an existing user it logged whoever
	# held it in as that user.

	def test_the_link_does_not_log_anyone_in(self):
		make_user("existing@example.com")
		invitation, key = self.make_invitation("existing@example.com", "Sales Manager")

		frappe.set_user("Guest")
		with self.watching_logins() as login_as:
			accept_invitation(key=key)

		login_as.assert_not_called()
		# the invitee is sent to log in first, and comes back to the same link
		self.assertEqual(frappe.local.response["type"], "redirect")
		location = urlparse(frappe.local.response["location"])
		self.assertEqual(location.path, "/login")
		self.assertEqual(
			parse_qs(location.query)["redirect-to"], [f"/api/method/crm.api.accept_invitation?key={key}"]
		)
		self.assertNotIn("Sales Manager", frappe.get_roles("existing@example.com"))
		self.assertEqual(frappe.db.get_value("CRM Invitation", invitation.name, "status"), "Pending")

	def test_an_existing_user_accepts_once_logged_in(self):
		make_user("existing@example.com")
		invitation, key = self.make_invitation("existing@example.com", "Sales Manager")

		frappe.set_user("existing@example.com")
		with self.watching_logins() as login_as:
			accept_invitation(key=key)

		login_as.assert_not_called()
		self.assertEqual(frappe.local.response["location"], "/crm")
		self.assertIn("Sales Manager", frappe.get_roles("existing@example.com"))
		self.assertEqual(frappe.db.get_value("CRM Invitation", invitation.name, "status"), "Accepted")

	def test_someone_else_cannot_accept_for_an_existing_user(self):
		make_user("existing@example.com")
		_invitation, key = self.make_invitation("existing@example.com", "Sales Manager")

		frappe.set_user(SALES_USER)
		with self.watching_logins() as login_as:
			self.assertRaises(frappe.PermissionError, accept_invitation, key=key)

		login_as.assert_not_called()
		self.assertNotIn("Sales Manager", frappe.get_roles("existing@example.com"))
		self.assertNotIn("Sales Manager", frappe.get_roles(SALES_USER))

	# Invitations sent before the fix

	def test_the_patch_expires_invitations_whose_key_was_readable(self):
		"""Every Sales User could read those keys: none of them may still open anything."""
		from crm.patches.v1_0.expire_invitations_with_readable_keys import execute

		readable = legacy_invitation("legacy@example.com", key="0123456789ab")
		already_expired = legacy_invitation("stale@example.com", key="ba9876543210", status="Expired")
		_recent, key = self.invite("recent@example.com")

		execute()

		for name in (readable, already_expired):
			self.assertEqual(
				frappe.db.get_value("CRM Invitation", name, ["status", "key"]), ("Expired", None)
			)
		frappe.set_user("Guest")
		self.assertRaises(frappe.ValidationError, accept_invitation, key="0123456789ab")
		accept_invitation(key=key)  # sent after the fix: untouched
		self.assertTrue(frappe.db.exists("User", "recent@example.com"))


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


def report_view(**params):
	"""What the Desk report view (`frappe.desk.reportview.get`) answers to a request with these params."""
	frappe.local.form_dict = frappe._dict(params)
	return reportview.get()


def legacy_invitation(email, key, status="Pending"):
	"""An invitation as the code before the fix left it, its key stored as is."""
	with patch.object(frappe, "sendmail"):
		invitation = frappe.get_doc(doctype="CRM Invitation", email=email, role="Sales User").insert()
	frappe.db.set_value(
		"CRM Invitation", invitation.name, {"key": key, "status": status}, update_modified=False
	)
	return invitation.name
