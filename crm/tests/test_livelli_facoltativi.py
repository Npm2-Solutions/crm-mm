# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""The optional levels (doc 30, PR 4): Marketing, Accounting, Read only.

Marketing sees people with email and phone masked, by Frappe's own masking: the
fields are marked `mask`, and only the Contact Details role, which every other
level carries, sees them in full. It reads no conversation, call or note.
Accounting reads people and does the invoices. Read only takes every write away
from the level it is added to. And writing a person or a deal now asks for its
capability: seeing one is not enough.
"""

import frappe
from frappe.tests import IntegrationTestCase

from crm.permissions import livelli, utenti

MARKETING = "facoltativi.marketing@example.com"
AMMINISTRAZIONE = "facoltativi.accounting@example.com"
SEGRETERIA = "facoltativi.desk@example.com"
SOLA_LETTURA = "facoltativi.readonly@example.com"
OPERATORE = "facoltativi.practitioner@example.com"
MANAGER = "facoltativi.manager@example.com"

EMAIL = "mario.rossi@studio.test"
CELLULARE = "+393331234567"

LIVELLI = (
	(MARKETING, ["marketing"]),
	(AMMINISTRAZIONE, ["amministrazione"]),
	(SEGRETERIA, ["segreteria"]),
	(SOLA_LETTURA, ["segreteria", "sola_lettura"]),
	(OPERATORE, ["operatore"]),
	(MANAGER, ["manager"]),
)


def make_user(email: str):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"roles": [{"role": "Sales User"}],
			}
		).insert(ignore_permissions=True)


class FacoltativiTestCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		utenti.sincronizza()
		for user, chiavi in LIVELLI:
			make_user(user)
			utenti.assegna_livelli(user, chiavi)
		livelli.dimentica_cache()
		self.persona = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Mario",
				"last_name": "Rossi",
				"email": EMAIL,
				"mobile_no": CELLULARE,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def come(self, user: str):
		frappe.set_user(user)
		livelli.dimentica_cache()


class TestMarketingSeesMasked(FacoltativiTestCase):
	def test_the_person_comes_masked(self):
		self.come(MARKETING)
		doc = frappe.client.get("CRM Lead", self.persona.name)
		self.assertEqual(doc["first_name"], "Mario")
		self.assertEqual(doc["email"], "XXXXXX@studio.test")
		self.assertEqual(doc["mobile_no"], "+39XXXXXX")

	def test_and_so_does_the_list(self):
		self.come(MARKETING)
		righe = frappe.get_list(
			"CRM Lead", filters={"name": self.persona.name}, fields=["name", "email", "mobile_no"]
		)
		self.assertEqual(righe[0].email, "XXXXXX@studio.test")
		self.assertEqual(righe[0].mobile_no, "+39XXXXXX")

	def test_every_other_level_sees_them_in_full(self):
		for user in (SEGRETERIA, AMMINISTRAZIONE, MANAGER):
			self.come(user)
			doc = frappe.client.get("CRM Lead", self.persona.name)
			self.assertEqual(doc["email"], EMAIL, user)

	def test_a_send_from_a_webhook_goes_to_the_real_number(self):
		"""A webhook's session may not see people: every logged-in user holds the Guest
		role, so no rule could unmask it alone. What sends reads the number as stored."""
		from crm.api.whatsapp import numbers_of

		self.come("Guest")
		self.assertEqual(numbers_of("CRM Lead", self.persona.name), [CELLULARE])
		self.assertFalse(frappe.has_permission("CRM Lead", "read", user="Guest"))

	def test_saving_does_not_write_the_mask_back(self):
		self.come(MANAGER)
		doc = frappe.get_doc("CRM Lead", self.persona.name)
		doc.first_name = "Marco"
		doc.save()
		self.assertEqual(frappe.db.get_value("CRM Lead", self.persona.name, "email"), EMAIL)


class TestMarketingReadsNoConversation(FacoltativiTestCase):
	def test_no_email_about_a_person(self):
		"""The CRM reads emails through a person's history; the rule here closes the
		other ways in, the list and the document, to whoever does not converse."""
		from crm.permissions import seguono

		email = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"subject": "Visita",
				"content": "A domani",
				"reference_doctype": "CRM Lead",
				"reference_name": self.persona.name,
			}
		).insert(ignore_permissions=True)
		self.come(MARKETING)
		self.assertFalse(seguono.has_communication_permission(email, "read", MARKETING))
		self.assertFalse(frappe.has_permission("Communication", "read", doc=email.name))
		self.assertTrue(seguono.get_communication_permission_query_conditions(MARKETING))
		self.come(SEGRETERIA)
		self.assertTrue(seguono.has_communication_permission(email, "read", SEGRETERIA))
		self.assertEqual(seguono.get_communication_permission_query_conditions(SEGRETERIA), "")

	def test_no_call_and_no_note(self):
		nota = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": "Allergia",
				"content": "Da ricordare",
				"reference_doctype": "CRM Lead",
				"reference_docname": self.persona.name,
			}
		).insert(ignore_permissions=True)
		self.come(MARKETING)
		self.assertEqual(frappe.get_list("FCRM Note", filters={"name": nota.name}), [])
		self.assertFalse(frappe.has_permission("FCRM Note", "read", doc=nota.name))
		self.come(SEGRETERIA)
		self.assertTrue(frappe.has_permission("FCRM Note", "read", doc=nota.name))

	def test_the_history_leaves_them_out_and_keeps_the_mask(self):
		from crm.api.activities import get_lead_activities

		frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": "Allergia",
				"content": "Da ricordare",
				"reference_doctype": "CRM Lead",
				"reference_docname": self.persona.name,
			}
		).insert(ignore_permissions=True)
		persona = frappe.get_doc("CRM Lead", self.persona.name)
		persona.email = "mario@altro.test"
		# Frappe keeps no version in tests unless asked
		persona.save(ignore_permissions=True, ignore_version=False)

		self.come(MARKETING)
		activities, calls, notes, _tasks, _attachments = get_lead_activities(self.persona.name)
		self.assertEqual(notes, [])
		self.assertEqual(calls, [])
		self.assertFalse([a for a in activities if a["activity_type"] in ("communication", "note")])
		versioni = [
			v
			for a in activities
			for v in (a, *(a.get("other_versions") or ()))
			if isinstance(v.get("data"), dict)
		]
		cambio = next(v for v in versioni if v["data"].get("field") == "email")
		self.assertEqual(cambio["data"]["value"], "XXXXXX@altro.test")
		self.assertNotIn("mario", str(activities))

	def test_no_address_book(self):
		contatto = frappe.get_doc(
			{"doctype": "Contact", "first_name": "Mario", "email_ids": [{"email_id": EMAIL, "is_primary": 1}]}
		).insert(ignore_permissions=True)
		self.come(MARKETING)
		self.assertFalse(frappe.has_permission("Contact", "read", doc=contatto.name))
		self.assertEqual(frappe.get_list("Contact", filters={"name": contatto.name}), [])


class TestMarketingWork(FacoltativiTestCase):
	def test_it_configures_the_marketing(self):
		self.come(MARKETING)
		for capacita in ("automazioni.gestisci", "meta.gestisci", "tracciamento.gestisci", "social.pubblica"):
			self.assertTrue(livelli.puo(capacita), capacita)
		link = frappe.get_doc(
			{"doctype": "CRM Tracked Link", "title": "Autunno", "destination_url": "https://studio.test"}
		)
		self.assertTrue(frappe.has_permission("CRM Tracked Link", "create", doc=link))
		self.assertTrue(frappe.has_permission("CRM Tracking Settings", "write"))

	def test_it_does_not_change_people(self):
		self.come(MARKETING)
		doc = frappe.get_doc("CRM Lead", self.persona.name)
		doc.first_name = "Marco"
		with self.assertRaises(frappe.PermissionError):
			doc.save()


class TestAccounting(FacoltativiTestCase):
	def test_it_reads_people_and_does_the_invoices(self):
		self.come(AMMINISTRAZIONE)
		self.assertTrue(frappe.has_permission("CRM Lead", "read", doc=self.persona.name))
		for capacita in ("fatture.emetti", "fatture.annulla", "fatture.configura", "persone.dati_fiscali"):
			self.assertTrue(livelli.puo(capacita), capacita)
		self.assertIn("Invoicing Manager", frappe.get_roles())

	def test_it_does_not_change_people(self):
		self.come(AMMINISTRAZIONE)
		doc = frappe.get_doc("CRM Lead", self.persona.name)
		doc.first_name = "Marco"
		with self.assertRaises(frappe.PermissionError):
			doc.save()


class TestReadOnly(FacoltativiTestCase):
	def test_it_reads_what_its_level_reads(self):
		self.come(SOLA_LETTURA)
		doc = frappe.client.get("CRM Lead", self.persona.name)
		self.assertEqual(doc["email"], EMAIL)

	def test_it_writes_nothing(self):
		self.come(SOLA_LETTURA)
		doc = frappe.get_doc("CRM Lead", self.persona.name)
		doc.first_name = "Marco"
		with self.assertRaises(frappe.PermissionError):
			doc.save()
		nota = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": "Prova",
				"reference_doctype": "CRM Lead",
				"reference_docname": self.persona.name,
			}
		)
		with self.assertRaises(frappe.PermissionError):
			nota.insert()

	def test_it_goes_with_another_level(self):
		with self.assertRaises(frappe.ValidationError):
			utenti.verifica_livelli(["sola_lettura"])


class TestWritingAsksTheCapability(FacoltativiTestCase):
	def test_only_the_manager_deletes_a_person(self):
		frappe.db.set_value("CRM Lead", self.persona.name, "lead_owner", OPERATORE)
		self.come(OPERATORE)
		self.assertTrue(frappe.has_permission("CRM Lead", "write", doc=self.persona.name))
		self.assertFalse(frappe.has_permission("CRM Lead", "delete", doc=self.persona.name))
		self.come(MANAGER)
		self.assertTrue(frappe.has_permission("CRM Lead", "delete", doc=self.persona.name))


class TestTheUsersOfBefore(FacoltativiTestCase):
	def test_saving_gives_them_the_role(self):
		prima = "facoltativi.saved@example.com"
		make_user(prima)
		self.assertIn(livelli.RUOLO_RECAPITI, frappe.get_roles(prima))

	def test_they_keep_seeing_email_and_phone(self):
		"""A user saved before the role existed gets it from the patch."""
		from crm.patches.v1_0 import contact_details_for_users_outside_levels as patch

		prima = "facoltativi.before@example.com"
		make_user(prima)
		frappe.db.delete("Has Role", {"parent": prima, "role": livelli.RUOLO_RECAPITI})
		frappe.clear_cache(user=prima)
		self.assertNotIn(livelli.RUOLO_RECAPITI, frappe.get_roles(prima))
		patch.execute()
		frappe.clear_cache(user=prima)
		self.assertIn(livelli.RUOLO_RECAPITI, frappe.get_roles(prima))
		self.come(prima)
		frappe.db.set_value("CRM Lead", self.persona.name, "lead_owner", prima)
		self.assertEqual(frappe.client.get("CRM Lead", self.persona.name)["email"], EMAIL)


class TestReadOnlyReadsItsLevel(FacoltativiTestCase):
	"""Reading has capabilities of its own: Read only keeps them, and loses the writes."""

	def test_notes_and_emails(self):
		from crm.permissions import seguono

		nota = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": "Allergia",
				"reference_doctype": "CRM Lead",
				"reference_docname": self.persona.name,
			}
		).insert(ignore_permissions=True)
		self.come(SOLA_LETTURA)
		self.assertTrue(frappe.has_permission("FCRM Note", "read", doc=nota.name))
		self.assertFalse(frappe.has_permission("FCRM Note", "write", doc=nota.name))
		self.assertEqual(seguono.get_communication_permission_query_conditions(SOLA_LETTURA), "")

	def test_a_whatsapp_thread_to_read_not_to_write(self):
		from crm.api.whatsapp import validate_access

		self.come(SOLA_LETTURA)
		validate_access("CRM Lead", self.persona.name)
		with self.assertRaises(frappe.PermissionError):
			validate_access("CRM Lead", self.persona.name, "write")
		self.come(MARKETING)
		with self.assertRaises(frappe.PermissionError):
			validate_access("CRM Lead", self.persona.name)

	def test_no_email_from_the_person(self):
		for user in (SOLA_LETTURA, MARKETING):
			self.come(user)
			self.assertFalse(frappe.has_permission("CRM Lead", "email", doc=self.persona.name), user)
		self.come(SEGRETERIA)
		self.assertTrue(frappe.has_permission("CRM Lead", "email", doc=self.persona.name))


class TestSharedIsNotAWayAround(FacoltativiTestCase):
	"""The CRM shares every person and deal with its owner, for writing, and Frappe
	grants what is shared without asking the `has_permission` hooks."""

	def test_the_practitioner_answers_on_a_deal_it_does_not_change(self):
		from crm.api.whatsapp import validate_access
		from crm.permissions.test_org_hierarchy import make_deal

		trattativa = make_deal(OPERATORE)
		self.come(OPERATORE)
		validate_access("CRM Deal", trattativa.name, "write")
		doc = frappe.get_doc("CRM Deal", trattativa.name)
		doc.probability = 40
		doc.flags.ignore_links = True  # the helper's organization is only a name
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_read_only_does_not_change_what_it_owns(self):
		frappe.db.set_value("CRM Lead", self.persona.name, "lead_owner", SOLA_LETTURA)
		frappe.share.add_docshare(
			"CRM Lead", self.persona.name, SOLA_LETTURA, write=1, flags={"ignore_share_permission": True}
		)
		self.come(SOLA_LETTURA)
		self.assertTrue(frappe.has_permission("CRM Lead", "write", doc=self.persona.name))
		doc = frappe.get_doc("CRM Lead", self.persona.name)
		doc.first_name = "Marco"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_what_the_server_saves_for_itself_goes_through(self):
		self.come(SOLA_LETTURA)
		doc = frappe.get_doc("CRM Lead", self.persona.name)
		doc.first_name = "Marco"
		doc.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("CRM Lead", self.persona.name, "first_name"), "Marco")


class TestTheScreenAsksTheServer(FacoltativiTestCase):
	def test_the_record_comes_to_read(self):
		from crm.api.doc import get_doc_permissions

		for user in (MARKETING, AMMINISTRAZIONE, SOLA_LETTURA):
			self.come(user)
			permessi = get_doc_permissions("CRM Lead", self.persona.name)["permissions"]
			self.assertEqual(permessi["read"], 1, user)
			self.assertFalse(permessi.get("write"), user)
			self.assertFalse(permessi.get("delete"), user)
		self.come(SEGRETERIA)
		permessi = get_doc_permissions("CRM Lead", self.persona.name)["permissions"]
		self.assertEqual(permessi["write"], 1)
		self.assertFalse(permessi.get("delete"))
		self.come(MANAGER)
		self.assertEqual(get_doc_permissions("CRM Lead", self.persona.name)["permissions"]["delete"], 1)

	def test_the_call_buttons_are_for_who_calls(self):
		from unittest.mock import MagicMock, patch

		from crm.integrations.api import is_call_integration_enabled

		provider = MagicMock()
		provider.as_dict.return_value = {"name": "Twilio", "enabled": True}
		with patch("crm.telephony.providers.all_providers", return_value=[provider]):
			self.come(MARKETING)
			self.assertEqual(is_call_integration_enabled()["integrations"], {"Twilio": False})
			self.come(SEGRETERIA)
			self.assertEqual(
				is_call_integration_enabled()["integrations"], {"Twilio": livelli.puo("telefono.chiama")}
			)


class TestAssigning(FacoltativiTestCase):
	def assign(self, user: str):
		import json

		from crm.permissions import documenti

		self.come(user)
		return documenti.assegna(
			{"doctype": "CRM Lead", "name": self.persona.name, "assign_to": json.dumps([SEGRETERIA])}
		)

	def test_who_may_not_assign(self):
		for user in (MARKETING, AMMINISTRAZIONE, SOLA_LETTURA, OPERATORE):
			with self.assertRaises(frappe.PermissionError, msg=user):
				self.assign(user)

	def test_the_front_desk_assigns(self):
		self.assign(SEGRETERIA)
		frappe.set_user("Administrator")
		self.assertTrue(
			frappe.db.exists(
				"ToDo",
				{
					"reference_type": "CRM Lead",
					"reference_name": self.persona.name,
					"allocated_to": SEGRETERIA,
				},
			)
		)

	def test_the_screen_goes_through_the_check(self):
		overrides = frappe.get_hooks("override_whitelisted_methods")
		self.assertEqual(overrides["frappe.desk.form.assign_to.add"][-1], "crm.permissions.documenti.assegna")


class TestReadOnlyDashboards(FacoltativiTestCase):
	"""Reading the numbers is not making dashboards: Read only opens them, and keeps
	the numbers of the level it is added to."""

	def test_it_opens_them_and_makes_none(self):
		from crm.api.dashboard import get_dashboards
		from crm.dashboard import store

		self.come(SOLA_LETTURA)
		self.assertFalse(get_dashboards()["can_create"])
		with self.assertRaises(frappe.PermissionError):
			store.create("Mine", private=True)
		self.come(SEGRETERIA)
		self.assertTrue(get_dashboards()["can_create"])

	def test_a_read_only_manager_keeps_the_centres_numbers(self):
		from crm.dashboard.context import is_manager, shares

		manager_in_lettura = "facoltativi.readonly.manager@example.com"
		make_user(manager_in_lettura)
		utenti.assegna_livelli(manager_in_lettura, ["manager", "sola_lettura"])
		self.come(manager_in_lettura)
		self.assertTrue(is_manager())
		self.assertFalse(shares())
