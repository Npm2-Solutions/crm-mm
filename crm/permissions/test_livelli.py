# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The matrix of doc 30, proved without a site.

Each test builds its own registry - the CRM's catalogue plus invoicing's column -
inside `registro_isolato`, so neither the order the suite runs in nor what the
process registered before can change an answer.
"""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the registry is still fully testable
	from unittest import TestCase as UnitTestCase

from crm.invoicing import capacita as capacita_fatturazione
from crm.permissions import catalogo, livelli
from crm.permissions.livelli import (
	A_SCELTA,
	ATTIVO,
	CENTRO,
	LIBERO_OCCUPATO,
	PROVA,
	SOLA_LETTURA,
	SPENTO,
	SUOI,
	TEAM,
	Capacita,
	Livello,
	calcola,
	registro_isolato,
)

SEG, OP, MAN, COM = catalogo.SEGRETERIA, catalogo.OPERATORE, catalogo.MANAGER, catalogo.COMMERCIALE
MKT, AMM = catalogo.LIV_MARKETING, catalogo.AMMINISTRAZIONE


class RegistroCase(UnitTestCase):
	def setUp(self):
		super().setUp()
		self._isolato = registro_isolato()
		self._isolato.__enter__()
		catalogo.registra()
		capacita_fatturazione.registra()

	def tearDown(self):
		self._isolato.__exit__(None, None, None)
		super().tearDown()


class TestCatalogo(RegistroCase):
	def test_ogni_concessione_nomina_un_livello_che_esiste(self):
		registrati = {lv.chiave for lv in livelli.livelli()}
		for nome in livelli.capacita_registrate():
			for chiave in livelli.concessioni(nome):
				self.assertIn(chiave, registrati, f"{nome} is granted to an unknown level {chiave!r}")

	def test_ogni_ambito_e_uno_di_quelli_noti(self):
		noti = {CENTRO, TEAM, SUOI, livelli.MASCHERATO, LIBERO_OCCUPATO, A_SCELTA}
		for nome in livelli.capacita_registrate():
			for ambito in livelli.concessioni(nome).values():
				self.assertIn(ambito, noti, f"{nome}: unknown scope {ambito!r}")

	def test_le_capacita_tecniche_non_vanno_a_nessun_livello(self):
		for nome, capacita in livelli.capacita_registrate().items():
			if capacita.agenzia:
				self.assertEqual(livelli.concessioni(nome), {}, nome)

	def test_ogni_capacita_appartiene_a_un_modulo_del_piano(self):
		moduli = {m.chiave for m in livelli.moduli_piano()}
		for nome, capacita in livelli.capacita_registrate().items():
			self.assertIn(capacita.piano, moduli, nome)

	def test_i_profili_sono_del_crm(self):
		"""The CRM rewrites the Role Profiles it owns, and only those."""
		for livello in livelli.livelli():
			self.assertTrue(livello.profilo.startswith("CRM "), livello.profilo)

	def test_nessun_livello_porta_system_manager(self):
		"""Frappe rebuilds a profiled user's roles from their profiles: a level carrying
		System Manager would hand the site to whoever the Manager gives it to."""
		for livello in livelli.livelli():
			self.assertNotIn("System Manager", livelli.ruoli_del_livello(livello.chiave))

	def test_ogni_livello_apre_il_crm(self):
		"""Every level on its own; Read only is only ever added to another."""
		accesso = livelli.ruoli_di_accesso()
		for livello in livelli.livelli():
			if livello.aggiuntivo:
				self.assertEqual(livelli.ruoli_del_livello(livello.chiave), frozenset(), livello.chiave)
				continue
			self.assertTrue(accesso & livelli.ruoli_del_livello(livello.chiave), livello.chiave)

	def test_i_recapiti_in_chiaro_tranne_il_marketing(self):
		"""Frappe masks email and phone for whoever lacks the role (PR 4)."""
		for livello in livelli.livelli():
			chi_li_vede = livelli.RUOLO_RECAPITI in livelli.ruoli_del_livello(livello.chiave)
			atteso = livello.chiave not in (catalogo.LIV_MARKETING, catalogo.SOLA_LETTURA)
			self.assertEqual(chi_li_vede, atteso, livello.chiave)
		self.assertNotIn(livelli.RUOLO_RECAPITI, livelli.ruoli_di_accesso())

	def test_i_ruoli_della_fatturazione_da_soli_non_aprono_il_crm(self):
		self.assertNotIn("Invoicing Manager", livelli.ruoli_di_accesso())
		self.assertNotIn("Invoicing User", livelli.ruoli_di_accesso())

	def test_i_ruoli_di_ogni_livello(self):
		R = livelli.RUOLO_RECAPITI
		self.assertEqual(livelli.ruoli_del_livello(SEG), {"Sales User", "Front Desk", "Invoicing User", R})
		self.assertEqual(livelli.ruoli_del_livello(OP), {"Sales User", "Practitioner", R})
		self.assertEqual(
			livelli.ruoli_del_livello(MAN),
			{"Sales User", "Sales Manager", "Invoicing Manager", "Invoicing User", R},
		)
		self.assertEqual(livelli.ruoli_del_livello(COM), {"Sales User", R})
		self.assertEqual(livelli.ruoli_del_livello(MKT), {"Sales User", "Marketing"})
		self.assertEqual(
			livelli.ruoli_del_livello(AMM), {"Sales User", "Invoicing Manager", "Invoicing User", R}
		)
		self.assertEqual(livelli.ruoli_del_livello(catalogo.SOLA_LETTURA), frozenset())

	def test_il_marketing_si_offre_con_il_suo_modulo(self):
		self.assertEqual(livelli.livello(MKT).piano, catalogo.MARKETING)


class TestMatrice(RegistroCase):
	"""Column by column, the rows of doc 30 that differ most between levels."""

	def test_marketing(self):
		c = calcola([MKT])
		self.assertEqual(c["persone.vedi"], livelli.MASCHERATO)
		self.assertEqual(c["trattative.vedi"], CENTRO)
		for sua in (
			"automazioni.gestisci",
			"social.pubblica",
			"meta.gestisci",
			"tracciamento.gestisci",
			"moduli_lead.gestisci",
			"modelli_messaggio.gestisci",
			"numeri.marketing",
		):
			self.assertEqual(c[sua], CENTRO, sua)
		for vietata in (
			"persone.scrivi",
			"trattative.scrivi",
			"conversazioni.usa",
			"note.scrivi",
			"agenda.vedi",
			"telefono.registro",
			"consensi.vedi",
			"fatture.vedi",
			"numeri.economici",
			"utenti.gestisci",
		):
			self.assertNotIn(vietata, c)

	def test_amministrazione(self):
		c = calcola([AMM])
		self.assertEqual(c["persone.vedi"], CENTRO)
		self.assertEqual(c["persone.dati_fiscali"], CENTRO)
		self.assertEqual(c["agenda.vedi"], CENTRO)
		for fattura in (
			"fatture.vedi",
			"fatture.emetti",
			"fatture.incassi",
			"fatture.annulla",
			"fatture.invia",
			"fatture.esporta",
			"fatture.configura",
		):
			self.assertEqual(c[fattura], CENTRO, fattura)
		self.assertEqual(c["numeri.economici"], CENTRO)
		for vietata in (
			"persone.scrivi",
			"trattative.scrivi",
			"conversazioni.usa",
			"agenda.prenota",
			"automazioni.gestisci",
		):
			self.assertNotIn(vietata, c)

	def test_sola_lettura_si_aggiunge_e_toglie_le_scritture(self):
		da_solo = calcola([catalogo.SOLA_LETTURA])
		self.assertEqual(da_solo, {})
		c = calcola([SEG, catalogo.SOLA_LETTURA])
		self.assertEqual(c["persone.vedi"], CENTRO)
		self.assertEqual(c["agenda.vedi"], CENTRO)
		for scrittura in (
			"persone.scrivi",
			"agenda.prenota",
			"fatture.emetti",
			"conversazioni.usa",
			"note.scrivi",
			"persone.assegna",
		):
			self.assertNotIn(scrittura, c)

	def test_sola_lettura_tiene_i_numeri_del_centro(self):
		c = calcola([MAN, catalogo.SOLA_LETTURA])
		self.assertEqual(c["dashboard.centro"], CENTRO)
		self.assertNotIn("dashboard.condivise", c)
		self.assertNotIn("dashboard.personali", c)

	def test_sola_lettura_legge_conversazioni_e_note_del_suo_livello(self):
		"""Reading has its own capability, as for people and deals: Read only keeps it."""
		c = calcola([OP, catalogo.SOLA_LETTURA])
		self.assertEqual(c["conversazioni.vedi"], SUOI)
		self.assertEqual(c["note.vedi"], SUOI)
		self.assertEqual(c["telefono.registro"], SUOI)
		for livello in (MKT, AMM):
			for lettura in ("conversazioni.vedi", "note.vedi"):
				self.assertNotIn(lettura, calcola([livello]), (livello, lettura))

	def test_segreteria(self):
		c = calcola([SEG])
		self.assertEqual(c["persone.vedi"], CENTRO)
		self.assertEqual(c["agenda.vedi"], CENTRO)
		self.assertEqual(c["agenda.turni"], CENTRO)
		self.assertEqual(c["fatture.emetti"], CENTRO)
		self.assertEqual(c["telefono.registrazioni"], SUOI)
		for vietata in (
			"utenti.gestisci",
			"pipeline.configura",
			"agenda.configura",
			"fatture.annulla",
			"persone.elimina",
		):
			self.assertNotIn(vietata, c)

	def test_operatore(self):
		c = calcola([OP])
		self.assertEqual(c["persone.vedi"], SUOI)
		self.assertEqual(c["agenda.vedi"], SUOI)
		self.assertEqual(c["fatture.vedi"], SUOI)
		self.assertEqual(c["numeri.economici"], SUOI)
		for vietata in (
			"trattative.scrivi",
			"persone.assegna",
			"fatture.emetti",
			"impostazioni.generali",
			"numeri.marketing",
		):
			self.assertNotIn(vietata, c)

	def test_manager(self):
		c = calcola([MAN])
		for nome, capacita in livelli.capacita_registrate().items():
			if capacita.agenzia:
				self.assertNotIn(nome, c, f"the Manager does not get the agency's {nome}")
		for nome in (
			"utenti.gestisci",
			"agenda.configura",
			"fatture.configura",
			"automazioni.gestisci",
			"sito.gestisci",
		):
			self.assertEqual(c[nome], CENTRO)

	def test_commerciale(self):
		c = calcola([COM])
		self.assertEqual(c["persone.vedi"], TEAM)
		self.assertEqual(c["trattative.scrivi"], TEAM)
		self.assertEqual(c["agenda.vedi"], LIBERO_OCCUPATO)
		self.assertEqual(c["agenda.prenota"], CENTRO)
		self.assertNotIn("fatture.vedi", c)

	def test_piu_livelli_prendono_l_ambito_piu_largo(self):
		"""The owner who also sees patients sees the whole centre, not their own."""
		c = calcola([OP, MAN])
		self.assertEqual(c["persone.vedi"], CENTRO)
		self.assertEqual(c["agenda.vedi"], CENTRO)

	def test_a_scelta_e_spento_finche_il_manager_non_lo_accende(self):
		self.assertNotIn("agenda.sovrapponi", calcola([SEG]))
		self.assertNotIn("fatture.invia", calcola([SEG]))
		acceso = calcola([SEG], a_scelta=["agenda.sovrapponi"])
		self.assertEqual(acceso["agenda.sovrapponi"], CENTRO)
		self.assertNotIn("fatture.invia", acceso)

	def test_a_scelta_non_da_a_un_livello_quello_che_non_ha(self):
		self.assertNotIn("agenda.sovrapponi", calcola([OP], a_scelta=["agenda.sovrapponi"]))

	def test_senza_livelli_niente(self):
		self.assertEqual(calcola([]), {})


class TestPiano(RegistroCase):
	def test_un_piano_che_non_dice_niente_lascia_tutto_come_prima(self):
		self.assertEqual(calcola([MAN]), calcola([MAN], moduli={}))
		self.assertIn("automazioni.gestisci", calcola([MAN]))
		self.assertIn("telefono.chiama", calcola([MAN]))

	def test_un_modulo_spento_toglie_le_sue_capacita(self):
		c = calcola([MAN], moduli={catalogo.MARKETING: SPENTO})
		self.assertNotIn("automazioni.gestisci", c)
		self.assertNotIn("automazioni.vedi", c)
		self.assertIn("persone.vedi", c)

	def test_un_modulo_scaduto_resta_da_leggere(self):
		"""Nothing is deleted when a module ends: its data stays readable."""
		c = calcola([MAN], moduli={catalogo.MARKETING: SOLA_LETTURA})
		self.assertIn("automazioni.vedi", c)
		self.assertIn("numeri.marketing", c)
		self.assertNotIn("automazioni.gestisci", c)
		self.assertNotIn("sito.gestisci", c)

	def test_la_prova_vale_come_attivo(self):
		self.assertEqual(
			calcola([MAN], moduli={catalogo.MARKETING: PROVA}),
			calcola([MAN], moduli={catalogo.MARKETING: ATTIVO}),
		)

	def test_un_modulo_nuovo_nasce_spento(self):
		with registro_isolato(vuoto=False):
			livelli.registra_modulo_piano(livelli.ModuloPiano("nuovo", "New", predefinito=False))
			livelli.registra_capacita(Capacita("nuovo.usa", piano="nuovo"), {MAN: CENTRO})
			self.assertNotIn("nuovo.usa", calcola([MAN]))
			self.assertIn("nuovo.usa", calcola([MAN], moduli={"nuovo": ATTIVO}))

	def test_il_piano_vale_anche_per_l_agenzia(self):
		c = calcola([], agenzia=True, moduli={catalogo.MARKETING: SPENTO})
		self.assertNotIn("automazioni.gestisci", c)
		# only the technical side stays, so whoever manages the site can switch it back
		self.assertIn("automazioni.webhook", c)
		self.assertIn("piano.gestisci", c)


class TestRequisiti(RegistroCase):
	def test_il_sito_senza_builder_non_e_di_nessuno(self):
		"""Installing Builder is the agency's job on the bench: without it there is no
		site to manage, for the manager or the agency."""
		self.assertNotIn("sito.gestisci", calcola([MAN], requisiti=set()))
		self.assertNotIn("sito.gestisci", calcola([], agenzia=True, requisiti=set()))
		self.assertIn("sito.gestisci", calcola([MAN], requisiti={"builder"}))

	def test_senza_requisiti_dichiarati_vale_tutto(self):
		self.assertIn("sito.gestisci", calcola([MAN]))

	def test_gli_altri_non_dipendono_da_builder(self):
		self.assertIn("automazioni.gestisci", calcola([MAN], requisiti=set()))


class TestAgenzia(RegistroCase):
	def test_l_agenzia_ha_tutto_quello_che_non_e_clinico(self):
		c = calcola([], agenzia=True)
		for nome in livelli.capacita_registrate():
			self.assertIn(nome, c, nome)
		self.assertIn("piano.gestisci", c)

	def test_i_dati_clinici_solo_con_l_accesso_concesso(self):
		with registro_isolato(vuoto=False):
			livelli.registra_capacita(Capacita("cartella.vedi", clinica=True, scrive=False), {OP: SUOI})
			self.assertNotIn("cartella.vedi", calcola([], agenzia=True))
			self.assertEqual(calcola([], agenzia=True, accessi_clinici=True)["cartella.vedi"], CENTRO)


class TestSolaLettura(RegistroCase):
	def test_sola_lettura_toglie_ogni_scrittura_al_livello_a_cui_si_aggiunge(self):
		with registro_isolato(vuoto=False):
			livelli.registra_livello(
				Livello(livelli.SOLA_LETTURA_LIVELLO, "CRM Read Only", "Read Only", base=False)
			)
			c = calcola([SEG, livelli.SOLA_LETTURA_LIVELLO])
			self.assertIn("persone.vedi", c)
			self.assertIn("agenda.vedi", c)
			self.assertNotIn("persone.scrivi", c)
			self.assertNotIn("fatture.emetti", c)


class TestImpliciti(RegistroCase):
	"""Users from before levels keep exactly what their roles gave them."""

	def test_dai_ruoli_ai_livelli(self):
		self.assertEqual(livelli.livelli_impliciti({"Sales Manager", "Sales User"}), [MAN, COM])
		self.assertEqual(livelli.livelli_impliciti({"Sales User"}), [COM])
		self.assertEqual(livelli.livelli_impliciti({"Invoicing Manager"}), [])

	def test_il_sales_user_di_prima_resta_nel_suo_ambito(self):
		c = calcola(livelli.livelli_impliciti({"Sales User"}))
		self.assertEqual(c["persone.vedi"], TEAM)
		self.assertNotIn("pipeline.configura", c)


class TestMigrazione(RegistroCase):
	def test_il_sales_manager_diventa_manager(self):
		self.assertEqual(catalogo.livelli_iniziali({"Sales Manager", "Sales User"}, gerarchia=False), [MAN])

	def test_il_sales_user_diventa_segreteria(self):
		self.assertEqual(catalogo.livelli_iniziali({"Sales User"}, gerarchia=False), [SEG])

	def test_con_la_gerarchia_il_sales_user_resta_commerciale(self):
		"""A site that turned the hierarchy on wants people to see their team only."""
		self.assertEqual(catalogo.livelli_iniziali({"Sales User"}, gerarchia=True), [COM])

	def test_l_agenzia_non_si_tocca(self):
		self.assertIsNone(catalogo.livelli_iniziali({"System Manager", "Sales Manager"}, gerarchia=False))

	def test_chi_ha_ruoli_di_altre_app_non_si_tocca(self):
		"""Frappe rebuilds a profiled user's roles from the profiles: giving a level to
		someone with a role from another app would take that role away."""
		self.assertIsNone(catalogo.livelli_iniziali({"Sales User", "Accounts User"}, gerarchia=False))

	def test_chi_non_e_nel_crm_non_si_tocca(self):
		self.assertIsNone(catalogo.livelli_iniziali({"Invoicing Manager"}, gerarchia=False))
		self.assertIsNone(catalogo.livelli_iniziali(set(), gerarchia=False))

	def test_i_ruoli_della_fatturazione_seguono_nel_livello(self):
		self.assertEqual(catalogo.livelli_iniziali({"Sales User", "Invoicing User"}, gerarchia=False), [SEG])
		self.assertEqual(
			catalogo.livelli_iniziali({"Sales Manager", "Invoicing Manager"}, gerarchia=False), [MAN]
		)

	def test_nessuno_perde_un_ruolo(self):
		"""Front Desk reads invoices; someone who also issued them keeps their roles."""
		self.assertIsNone(catalogo.livelli_iniziali({"Sales User", "Invoicing Manager"}, gerarchia=False))
		self.assertIsNone(catalogo.livelli_iniziali({"Sales User", "Invoicing User"}, gerarchia=True))


class TestIsolamento(UnitTestCase):
	def test_il_registro_isolato_rimette_tutto_a_posto(self):
		prima = livelli.capacita_registrate()
		with registro_isolato():
			livelli.registra_capacita(Capacita("segnaposto.prova"))
			self.assertIn("segnaposto.prova", livelli.capacita_registrate())
		self.assertEqual(livelli.capacita_registrate(), prima)
