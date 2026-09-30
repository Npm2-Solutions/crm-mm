# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The kinds of document and the days online, without a site."""

import unittest

from crm.documenti import regole as R


class ITipi(unittest.TestCase):
	def test_quelli_del_crm_in_ordine(self):
		del_crm = [tipo.chiave for tipo in R.tipi() if not tipo.modulo]
		self.assertEqual(del_crm, [R.MODULO_FIRMATO, R.CONTRATTO, R.CERTIFICATO, R.IDENTITA, R.FOTO, R.ALTRO])
		self.assertFalse(any(R.tipo(chiave).clinico for chiave in del_crm))

	def test_un_modulo_porta_i_suoi(self):
		nuovo = R.TipoDocumento("Tessera", modulo="palestra", ordine=45)
		self.addCleanup(R._tipi.pop, "Tessera", None)
		R.registra_tipo(nuovo)
		self.assertIs(R.tipo("Tessera"), nuovo)
		chiavi = [tipo.chiave for tipo in R.tipi()]
		self.assertLess(chiavi.index(R.IDENTITA), chiavi.index("Tessera"))
		self.assertLess(chiavi.index("Tessera"), chiavi.index(R.FOTO))
		self.assertIsNone(R.tipo(None))
		self.assertIsNone(R.tipo("Nessuno"))


class IGiorniOnline(unittest.TestCase):
	def test_quelli_chiesti_o_trenta(self):
		self.assertEqual(R.giorni_online(None), R.GIORNI_ONLINE)
		self.assertEqual(R.giorni_online(""), 30)
		self.assertEqual(R.giorni_online("7"), 7)
		self.assertEqual(R.giorni_online("una settimana"), 30)

	def test_almeno_uno_al_massimo_novanta(self):
		self.assertEqual(R.giorni_online(0), 1)
		self.assertEqual(R.giorni_online(-5), 1)
		self.assertEqual(R.giorni_online(365), R.GIORNI_MASSIMI)
		self.assertEqual(R.giorni_massimi(), 90)

	def test_quelli_del_modulo(self):
		# the clinic's reports: 45 days unless fewer are chosen, never more
		self.assertEqual(R.giorni_online(None, 45), 45)
		self.assertEqual(R.giorni_online(10, 45), 10)
		self.assertEqual(R.giorni_online(60, 45), 45)
		self.assertEqual(R.giorni_massimi(45), 45)
		# a module never goes past the CRM's most
		self.assertEqual(R.giorni_massimi(120), 90)
		self.assertEqual(R.giorni_online(None, 120), 90)
