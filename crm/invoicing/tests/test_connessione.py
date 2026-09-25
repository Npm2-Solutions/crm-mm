# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

"""How long a token is trusted for.

The provider's contract does not state a token lifetime; it states an expiry on
each answer. So nothing here may invent a duration - what is tested is that an
absent, malformed or absurd expiry all end somewhere safe rather than somewhere
convenient.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from crm.invoicing.engine.busta import DURATA_MASSIMA, DURATA_PRUDENTE, MARGINE
from crm.invoicing.engine.busta import durata_token as _durata
from crm.invoicing.tests.base import UnitTestCase


class DurataTokenTest(UnitTestCase):
	def test_nessuna_scadenza_dichiarata_vale_poco(self):
		# Re-authenticating an hour early costs one call. Trusting a number nobody
		# stated costs a failed invoice at the worst possible moment.
		self.assertEqual(_durata(None), DURATA_PRUDENTE)
		self.assertEqual(_durata(""), DURATA_PRUDENTE)

	def test_una_scadenza_illeggibile_vale_altrettanto_poco(self):
		self.assertEqual(_durata("domani"), DURATA_PRUDENTE)
		self.assertEqual(_durata("2026-13-45 99:99:99"), DURATA_PRUDENTE)

	def test_una_scadenza_vera_viene_rispettata_con_margine(self):
		fra_due_ore = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
		durata = _durata(fra_due_ore)
		self.assertLess(durata, 2 * 3600)
		self.assertGreater(durata, 2 * 3600 - MARGINE - 5)

	def test_una_scadenza_gia_passata_non_diventa_negativa(self):
		ieri = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
		self.assertEqual(_durata(ieri), MARGINE)

	def test_una_scadenza_assurda_viene_capata(self):
		# A provider claiming a year is either wrong or compromised; either way the
		# cache does not hold a credential that long.
		fra_un_anno = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
		self.assertEqual(_durata(fra_un_anno), DURATA_MASSIMA)
