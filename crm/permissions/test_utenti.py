# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Levels on real users: profiles, giving levels, the migration, invitations, the plan.

What `test_livelli.py` proves on paper, here on a site: Frappe rebuilds a profiled
user's roles from their profiles at every save, so whatever a level promises has to
survive a real `User.save()`.
"""

from unittest.mock import patch

import frappe
from frappe.model.document import clear_document_cache
from frappe.tests import IntegrationTestCase

from crm.api import check_app_permission, invite_by_email
from crm.api.session import get_permissions
from crm.api.user import (
	add_existing_users,
	remove_crm_roles_from_user,
	set_user_capability,
	set_user_levels,
	update_user_role,
)
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_hierarchy_node, make_user

MANAGER = "levels.manager@example.com"
DESK = "levels.desk@example.com"
AGENCY = "levels.agency@example.com"
NEWBIE = "levels.newbie@example.com"


def roles_of(user: str) -> set[str]:
	return set(frappe.get_all("Has Role", filters={"parenttype": "User", "parent": user}, pluck="role"))


def levels_of(user: str) -> list[str]:
	return livelli.livelli_di(user)


class LevelsCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		utenti.sincronizza()
		make_user(AGENCY, roles=["System Manager", "Sales Manager", "Sales User"])
		make_user(NEWBIE)
		for user in (MANAGER, DESK):
			make_user(user)
		utenti.assegna_livelli(MANAGER, ["manager"])
		utenti.assegna_livelli(DESK, ["segreteria"])
		livelli.dimentica_cache()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def as_user(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()


class TestProfili(LevelsCase):
	def test_ogni_livello_ha_il_suo_profilo_con_i_ruoli_del_registro(self):
		for livello in livelli.livelli():
			ruoli = set(
				frappe.get_all(
					"Has Role",
					filters={"parenttype": "Role Profile", "parent": livello.profilo},
					pluck="role",
				)
			)
			self.assertEqual(ruoli, set(livelli.ruoli_del_livello(livello.chiave)), livello.chiave)

	def test_sincronizzare_due_volte_non_cambia_niente(self):
		prima = frappe.db.get_value("Role Profile", "CRM Front Desk", "modified")
		utenti.sincronizza()
		self.assertEqual(frappe.db.get_value("Role Profile", "CRM Front Desk", "modified"), prima)

	def test_un_profilo_toccato_a_mano_torna_come_il_registro(self):
		frappe.get_doc(
			{
				"doctype": "Has Role",
				"parenttype": "Role Profile",
				"parentfield": "roles",
				"parent": "CRM Front Desk",
				"role": "Sales Manager",
			}
		).db_insert()
		clear_document_cache("Role Profile", "CRM Front Desk")
		frappe.get_doc("User", DESK).save(ignore_permissions=True)
		self.assertIn("Sales Manager", roles_of(DESK))

		utenti.sincronizza()
		self.assertNotIn("Sales Manager", roles_of(DESK))
		self.assertEqual(
			set(frappe.get_all("Has Role", filters={"parent": "CRM Front Desk"}, pluck="role")),
			set(livelli.ruoli_del_livello("segreteria")),
		)


class TestAssegnare(LevelsCase):
	def test_il_livello_porta_i_suoi_ruoli_e_niente_altro(self):
		self.assertEqual(
			roles_of(DESK), {"Sales User", "Front Desk", "Invoicing User", livelli.RUOLO_RECAPITI}
		)
		self.assertEqual(levels_of(DESK), ["segreteria"])

	def test_un_ruolo_messo_a_mano_sparisce_al_salvataggio(self):
		"""The reason levels are all or nothing: Frappe rebuilds the roles."""
		doc = frappe.get_doc("User", DESK)
		doc.append_roles("Sales Manager")
		doc.save(ignore_permissions=True)
		self.assertNotIn("Sales Manager", roles_of(DESK))

	def test_piu_livelli_sommano_i_ruoli(self):
		utenti.assegna_livelli(DESK, ["segreteria", "operatore"])
		self.assertEqual(levels_of(DESK), ["segreteria", "operatore"])
		self.assertIn("Practitioner", roles_of(DESK))
		self.assertIn("Front Desk", roles_of(DESK))

	def test_la_segreteria_vede_solo_i_moduli_del_crm_nel_desk(self):
		bloccati = set(frappe.get_all("Block Module", filters={"parent": DESK}, pluck="module"))
		for modulo in frappe.get_module_list("crm"):
			self.assertNotIn(modulo, bloccati, "invoicing is the CRM's too")
		self.assertIn("Core", bloccati)

	def test_entra_nel_crm(self):
		self.as_user(DESK)
		self.assertTrue(check_app_permission())

	def test_togliere_dal_crm_toglie_livelli_e_ruoli(self):
		utenti.togli_dal_crm(DESK)
		self.assertEqual(roles_of(DESK) & set(livelli.ruoli_registrati()), set())
		self.assertEqual(frappe.get_all("User Role Profile", filters={"parent": DESK}), [])


class TestApiUtenti(LevelsCase):
	def test_il_manager_da_ogni_livello(self):
		self.as_user(MANAGER)
		set_user_levels(DESK, ["operatore", "manager"])
		self.assertEqual(levels_of(DESK), ["operatore", "manager"])

	def test_chi_non_gestisce_utenti_non_cambia_niente(self):
		self.as_user(DESK)
		self.assertRaises(frappe.PermissionError, set_user_levels, MANAGER, ["segreteria"])
		self.assertRaises(frappe.PermissionError, remove_crm_roles_from_user, MANAGER)

	def test_gli_utenti_dell_agenzia_non_si_toccano_dal_crm(self):
		self.as_user(MANAGER)
		self.assertRaises(frappe.PermissionError, set_user_levels, AGENCY, ["segreteria"])
		self.assertIn("System Manager", roles_of(AGENCY))

	def test_nessun_livello_porta_system_manager(self):
		self.as_user(MANAGER)
		self.assertRaises(frappe.PermissionError, update_user_role, NEWBIE, "System Manager")
		self.assertNotIn("System Manager", roles_of(NEWBIE))

	def test_il_manager_non_si_toglie_il_livello_da_solo(self):
		self.as_user(MANAGER)
		self.assertRaises(frappe.PermissionError, set_user_levels, MANAGER, ["segreteria"])
		self.assertEqual(levels_of(MANAGER), ["manager"])

	def test_un_livello_che_non_esiste_si_rifiuta(self):
		self.as_user(MANAGER)
		self.assertRaises(frappe.ValidationError, set_user_levels, DESK, ["amministratore"])
		self.assertRaises(frappe.ValidationError, set_user_levels, DESK, [])

	def test_chi_guida_la_gerarchia_resta_manager(self):
		make_hierarchy_node(DESK, is_group=1)
		utenti.assegna_livelli(DESK, ["manager"])
		self.as_user(MANAGER)
		self.assertRaises(frappe.ValidationError, set_user_levels, DESK, ["segreteria"])

	def test_chi_ha_ruoli_di_altre_app_non_li_perde(self):
		"""Levels rebuild the roles: a user with another app's role is refused, not stripped."""
		make_user("levels.other.app@example.com", roles=["Website Manager"])
		self.as_user(MANAGER)
		self.assertRaises(
			frappe.ValidationError, set_user_levels, "levels.other.app@example.com", ["segreteria"]
		)
		self.assertIn("Website Manager", roles_of("levels.other.app@example.com"))
		self.assertEqual(
			frappe.get_all("User Role Profile", filters={"parent": "levels.other.app@example.com"}), []
		)

	def test_un_invito_non_toglie_i_ruoli_a_chi_ha_gia_un_account(self):
		make_user("levels.existing@example.com", roles=["Website Manager"])
		invitation = frappe.get_doc(
			{"doctype": "CRM Invitation", "email": "levels.existing@example.com", "levels": "segreteria"}
		)
		with patch.object(frappe, "sendmail"):
			invitation.insert()
		self.assertRaises(frappe.ValidationError, invitation.accept)
		self.assertIn("Website Manager", roles_of("levels.existing@example.com"))

	def test_i_livelli_accettano_anche_una_chiave_sola(self):
		self.as_user(MANAGER)
		set_user_levels(NEWBIE, "operatore")
		self.assertEqual(levels_of(NEWBIE), ["operatore"])
		set_user_levels(NEWBIE, "operatore,manager")
		self.assertEqual(levels_of(NEWBIE), ["operatore", "manager"])

	def test_aggiungere_utenti_esistenti(self):
		self.as_user(MANAGER)
		add_existing_users([NEWBIE], levels=["operatore"])
		self.assertEqual(levels_of(NEWBIE), ["operatore"])

	def test_il_vecchio_update_user_role_da_il_livello_del_ruolo(self):
		self.as_user(MANAGER)
		update_user_role(NEWBIE, "Sales User")
		self.assertEqual(levels_of(NEWBIE), ["segreteria"])
		update_user_role(NEWBIE, "Sales Manager")
		self.assertEqual(levels_of(NEWBIE), ["manager"])

	def test_l_agenzia_rende_agenzia(self):
		self.as_user(AGENCY)
		update_user_role(DESK, "System Manager")
		self.assertIn("System Manager", roles_of(DESK))
		self.assertEqual(frappe.get_all("User Role Profile", filters={"parent": DESK}), [])
		# and the next save does not take it away
		frappe.get_doc("User", DESK).save(ignore_permissions=True)
		self.assertIn("System Manager", roles_of(DESK))


class TestCapacitaAScelta(LevelsCase):
	def test_il_manager_accende_una_capacita_per_una_persona(self):
		self.assertFalse(livelli.puo("agenda.sovrapponi", DESK))
		self.as_user(MANAGER)
		set_user_capability(DESK, "agenda.sovrapponi", 1)
		livelli.dimentica_cache()
		self.assertTrue(livelli.puo("agenda.sovrapponi", DESK))
		set_user_capability(DESK, "agenda.sovrapponi", 0)
		livelli.dimentica_cache()
		self.assertFalse(livelli.puo("agenda.sovrapponi", DESK))

	def test_solo_quelle_che_il_livello_offre(self):
		utenti.assegna_livelli(NEWBIE, ["operatore"])
		self.as_user(MANAGER)
		self.assertRaises(frappe.ValidationError, set_user_capability, NEWBIE, "agenda.sovrapponi", 1)
		self.assertRaises(frappe.ValidationError, set_user_capability, DESK, "utenti.gestisci", 1)


class TestSessione(LevelsCase):
	def test_la_sessione_riceve_livelli_capacita_e_piano(self):
		self.as_user(DESK)
		permessi = get_permissions()
		self.assertEqual(permessi["levels"], ["segreteria"])
		self.assertFalse(permessi["agency"])
		self.assertEqual(permessi["capabilities"]["persone.vedi"], livelli.CENTRO)
		self.assertNotIn("utenti.gestisci", permessi["capabilities"])
		self.assertEqual(permessi["modules"]["base"], livelli.ATTIVO)

	def test_chi_non_e_nel_crm_non_riceve_niente(self):
		self.as_user(NEWBIE)
		self.assertRaises(frappe.PermissionError, get_permissions)


class TestInviti(LevelsCase):
	def invite(self, email, levels, by):
		self.as_user(by)
		with patch.object(frappe, "sendmail"):
			invite_by_email(email, levels=levels)
		frappe.set_user("Administrator")
		name = frappe.db.get_value("CRM Invitation", {"email": email, "status": "Pending"})
		return frappe.get_doc("CRM Invitation", name)

	def test_il_manager_invita_con_i_livelli(self):
		invitation = self.invite("levels.invitee@example.com", ["operatore"], MANAGER)
		self.assertEqual(invitation.chiavi_livelli(), ["operatore"])
		invitation.accept()
		self.assertEqual(levels_of("levels.invitee@example.com"), ["operatore"])
		self.assertIn("Practitioner", roles_of("levels.invitee@example.com"))

	def test_il_manager_invita_altri_manager(self):
		"""Doc 30: the Manager names front desk, practitioners and other managers."""
		invitation = self.invite("levels.boss@example.com", ["manager"], MANAGER)
		invitation.accept()
		self.assertEqual(levels_of("levels.boss@example.com"), ["manager"])

	def test_la_segreteria_non_invita(self):
		self.as_user(DESK)
		with patch.object(frappe, "sendmail"):
			self.assertRaises(
				frappe.PermissionError, invite_by_email, "levels.x@example.com", levels=["segreteria"]
			)

	def test_un_invito_non_si_scrive_a_mano_con_livelli_che_chi_invita_non_da(self):
		self.as_user(DESK)
		invitation = frappe.get_doc(
			{"doctype": "CRM Invitation", "email": "levels.y@example.com", "levels": "manager"}
		)
		with patch.object(frappe, "sendmail"):
			self.assertRaises(frappe.PermissionError, invitation.insert, ignore_permissions=True)

	def test_accettando_si_ricontrolla_chi_ha_invitato(self):
		invitation = self.invite("levels.late@example.com", ["segreteria"], MANAGER)
		utenti.assegna_livelli(MANAGER, ["segreteria"])
		livelli.dimentica_cache()
		self.assertRaises(frappe.PermissionError, invitation.accept)
		self.assertFalse(frappe.db.exists("User", "levels.late@example.com"))


class TestPiano(LevelsCase):
	def set_plan(self, **stati):
		piano = frappe.get_single("CRM Plan")
		piano.set(
			"modules", [{"module": m, "status": s, "trial_until": "2099-01-01"} for m, s in stati.items()]
		)
		piano.save(ignore_permissions=True)
		livelli.dimentica_cache()

	def test_un_modulo_spento_spegne_le_sue_capacita(self):
		self.assertTrue(livelli.puo("automazioni.gestisci", MANAGER))
		self.set_plan(marketing="Off")
		self.assertFalse(livelli.puo("automazioni.gestisci", MANAGER))
		self.assertFalse(livelli.puo("automazioni.vedi", MANAGER))
		self.assertTrue(livelli.puo("persone.vedi", MANAGER))

	def test_un_modulo_in_sola_lettura_resta_da_leggere(self):
		self.set_plan(marketing="Read only")
		self.assertTrue(livelli.puo("automazioni.vedi", MANAGER))
		self.assertFalse(livelli.puo("automazioni.gestisci", MANAGER))

	def test_una_prova_finita_diventa_sola_lettura(self):
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "marketing", "status": "Trial", "trial_until": "2000-01-01"}])
		piano.save(ignore_permissions=True)
		livelli.dimentica_cache()
		self.assertEqual(livelli.moduli_attivi()["marketing"], livelli.SOLA_LETTURA)

	def test_un_modulo_sconosciuto_si_rifiuta(self):
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "astrologia", "status": "Active"}])
		self.assertRaises(frappe.ValidationError, piano.save, ignore_permissions=True)

	def test_il_piano_lo_scrive_solo_l_agenzia(self):
		self.as_user(MANAGER)
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "marketing", "status": "Active"}])
		self.assertRaises(frappe.PermissionError, piano.save)


class TestMigrazione(LevelsCase):
	def test_la_migrazione_da_i_livelli_e_lascia_stare_chi_non_ci_sta(self):
		make_user("levels.old.user@example.com", roles=["Sales User"])
		make_user("levels.old.boss@example.com", roles=["Sales Manager", "Sales User"])
		make_user("levels.old.other@example.com", roles=["Sales User", "Website Manager"])
		make_user("levels.old.billing@example.com", roles=["Sales User", "Invoicing Manager"])
		fatti = dict(utenti.migra_utenti())

		self.assertEqual(fatti.get("levels.old.user@example.com"), ["segreteria"])
		self.assertEqual(fatti.get("levels.old.boss@example.com"), ["manager"])
		self.assertNotIn("levels.old.other@example.com", fatti)
		self.assertNotIn("levels.old.billing@example.com", fatti)
		self.assertNotIn(AGENCY, fatti)
		self.assertIn("Website Manager", roles_of("levels.old.other@example.com"))
		self.assertIn("Invoicing Manager", roles_of("levels.old.billing@example.com"))
		self.assertIn("System Manager", roles_of(AGENCY))

	def test_chi_non_ha_livelli_conta_per_i_suoi_ruoli(self):
		make_user("levels.legacy@example.com", roles=["Sales User"])
		self.assertEqual(levels_of("levels.legacy@example.com"), ["commerciale"])
		self.assertFalse(livelli.puo("pipeline.configura", "levels.legacy@example.com"))
