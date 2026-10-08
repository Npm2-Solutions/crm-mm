# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Online payments' rules, without a site: plain unittest."""

import unittest
from datetime import datetime, timedelta

from crm.pagamenti import regole as R

SEGRETO = "whsec_test_secret"
CORPO = b'{"id":"evt_test","object":"event"}'
MOMENTO = 1492774577
#: HMAC-SHA256 of "1492774577.<corpo>" with the secret, computed apart (openssl dgst).
ATTESA = "691252e266ce41cb94d709c84e9580d4172b117a510bbc81723f657d2cd5d215"


class TestChiave(unittest.TestCase):
	def test_modalita(self):
		self.assertEqual(R.modalita("sk_test_51abc"), R.TEST)
		self.assertEqual(R.modalita(" rk_test_51abc "), R.TEST)
		self.assertEqual(R.modalita("sk_live_51abc"), R.LIVE)
		self.assertEqual(R.modalita("rk_live_51abc"), R.LIVE)
		self.assertIsNone(R.modalita("pk_test_51abc"))
		self.assertIsNone(R.modalita(""))

	def test_cosa_manca(self):
		self.assertTrue(R.cosa_manca(""))
		self.assertIn("publishable", R.cosa_manca("pk_live_" + "x" * 30))
		self.assertTrue(R.cosa_manca("hello"))
		self.assertIsNone(R.cosa_manca("sk_test_" + "x" * 30))

	def test_mascherata(self):
		self.assertEqual(R.mascherata("sk_test_51Habcdefghij1234"), "sk_test_…1234")
		self.assertEqual(R.mascherata("short"), "")


class TestFirma(unittest.TestCase):
	def test_lo_schema_di_stripe(self):
		# the header Stripe writes: t=<timestamp>,v1=<hex HMAC-SHA256 of "t.body">
		self.assertEqual(R.firma(CORPO, SEGRETO, MOMENTO), f"t={MOMENTO},v1={ATTESA}")

	def test_buona(self):
		self.assertIsNone(R.perche_rifiutata(CORPO, f"t={MOMENTO},v1={ATTESA}", SEGRETO, MOMENTO + 10))

	def test_piu_firme_e_v0(self):
		# Stripe sends one v1 per secret while a secret is rolled, and a v0 in test
		intestazione = f"t={MOMENTO},v1=deadbeef,v1={ATTESA},v0=cafe"
		self.assertIsNone(R.perche_rifiutata(CORPO, intestazione, SEGRETO, MOMENTO))

	def test_sbagliata(self):
		self.assertEqual(
			R.perche_rifiutata(CORPO, f"t={MOMENTO},v1={'0' * 64}", SEGRETO, MOMENTO), "signature mismatch"
		)
		# the body changed by one byte
		self.assertEqual(
			R.perche_rifiutata(CORPO + b" ", f"t={MOMENTO},v1={ATTESA}", SEGRETO, MOMENTO),
			"signature mismatch",
		)
		# another secret
		self.assertEqual(
			R.perche_rifiutata(CORPO, f"t={MOMENTO},v1={ATTESA}", "whsec_other", MOMENTO),
			"signature mismatch",
		)

	def test_troppo_vecchia(self):
		self.assertEqual(
			R.perche_rifiutata(CORPO, f"t={MOMENTO},v1={ATTESA}", SEGRETO, MOMENTO + R.TOLLERANZA + 1),
			"too old",
		)
		# a signature from the future, beyond the tolerance, too
		self.assertEqual(
			R.perche_rifiutata(CORPO, f"t={MOMENTO},v1={ATTESA}", SEGRETO, MOMENTO - R.TOLLERANZA - 1),
			"too old",
		)

	def test_mancante(self):
		self.assertEqual(R.perche_rifiutata(CORPO, None, SEGRETO, MOMENTO), "no signature")
		self.assertEqual(R.perche_rifiutata(CORPO, "t=1", SEGRETO, MOMENTO), "no signature")
		self.assertEqual(R.perche_rifiutata(CORPO, "t=x,v1=ab", SEGRETO, MOMENTO), "bad timestamp")
		self.assertEqual(R.perche_rifiutata(CORPO, f"t={MOMENTO},v1={ATTESA}", "", MOMENTO), "no secret")


class TestImporti(unittest.TestCase):
	def test_centesimi(self):
		self.assertEqual(R.in_centesimi(30), 3000)
		self.assertEqual(R.in_centesimi("44.10"), 4410)
		self.assertEqual(R.in_centesimi(0.1 + 0.2), 30)
		self.assertEqual(R.in_centesimi(1.005), 101)
		self.assertEqual(R.in_centesimi(2.675), 268)
		self.assertEqual(R.in_centesimi(None), 0)
		self.assertEqual(R.in_centesimi(1500, "JPY"), 1500)

	def test_da_centesimi(self):
		self.assertEqual(R.da_centesimi(4410), 44.1)
		self.assertEqual(R.da_centesimi(1), 0.01)
		self.assertEqual(R.da_centesimi(1500, "jpy"), 1500.0)

	def test_acconto(self):
		self.assertEqual(R.acconto(R.ACCONTO, 30, 80), 30.0)
		# never more than the price
		self.assertEqual(R.acconto(R.ACCONTO, 100, 80), 80.0)
		self.assertEqual(R.acconto(R.TUTTO, 30, 80), 80.0)
		self.assertEqual(R.acconto("", 30, 80), 0.0)
		self.assertEqual(R.acconto(R.ACCONTO, -5, 80), 0.0)


class TestModulo(unittest.TestCase):
	def test_annidato(self):
		righe = R.modulo(
			{
				"mode": "payment",
				"line_items": [{"price_data": {"currency": "eur", "unit_amount": 3000}, "quantity": 1}],
				"metadata": {"site": "a.example", "payment": "PAY-1"},
				"enabled_events": ["charge.refunded", "checkout.session.expired"],
				"skip": None,
				"livemode": False,
			}
		)
		self.assertEqual(
			righe,
			[
				("mode", "payment"),
				("line_items[0][price_data][currency]", "eur"),
				("line_items[0][price_data][unit_amount]", "3000"),
				("line_items[0][quantity]", "1"),
				("metadata[site]", "a.example"),
				("metadata[payment]", "PAY-1"),
				("enabled_events[0]", "charge.refunded"),
				("enabled_events[1]", "checkout.session.expired"),
				("livemode", "false"),
			],
		)

	def test_percorso(self):
		self.assertEqual(R.percorso("checkout", "sessions", "cs_1/../x"), "checkout/sessions/cs_1%2F..%2Fx")


class TestSignificato(unittest.TestCase):
	def test_pagato(self):
		s = R.significato(
			{
				"type": "checkout.session.completed",
				"data": {
					"object": {
						"id": "cs_1",
						"payment_intent": "pi_1",
						"payment_status": "paid",
						"amount_total": 3000,
						"currency": "eur",
						"client_reference_id": "PAY-1",
						"metadata": {"site": "a.example"},
					}
				},
			}
		)
		self.assertEqual(
			(s.cosa, s.sessione, s.intento, s.importo, s.pagamento, s.sito),
			(R.PAGATO, "cs_1", "pi_1", 30.0, "PAY-1", "a.example"),
		)

	def test_non_ancora_pagato(self):
		self.assertIsNone(
			R.significato(
				{"type": "checkout.session.completed", "data": {"object": {"payment_status": "unpaid"}}}
			)
		)

	def test_scaduto_rimborsato_fallito(self):
		self.assertEqual(
			R.significato(
				{
					"type": "checkout.session.expired",
					"data": {"object": {"id": "cs_2", "metadata": {"payment": "PAY-2"}}},
				}
			).pagamento,
			"PAY-2",
		)
		r = R.significato(
			{
				"type": "charge.refunded",
				"data": {"object": {"payment_intent": "pi_1", "amount_refunded": 1500, "currency": "eur"}},
			}
		)
		self.assertEqual((r.cosa, r.intento, r.importo), (R.RIMBORSATO, "pi_1", 15.0))
		f = R.significato(
			{
				"type": "payment_intent.payment_failed",
				"data": {
					"object": {"id": "pi_3", "last_payment_error": {"message": "Your card was declined."}}
				},
			}
		)
		self.assertEqual((f.cosa, f.intento, f.errore), (R.NON_RIUSCITO, "pi_3", "Your card was declined."))

	def test_altro(self):
		self.assertIsNone(R.significato({"type": "customer.created", "data": {"object": {}}}))


class TestDisdetta(unittest.TestCase):
	def test_rimborsabile(self):
		inizio = datetime(2026, 10, 10, 10, 0)
		self.assertTrue(R.rimborsabile(inizio, inizio - timedelta(hours=25), True, 24))
		self.assertTrue(R.rimborsabile(inizio, inizio - timedelta(hours=24), True, 24))
		self.assertFalse(R.rimborsabile(inizio, inizio - timedelta(hours=23), True, 24))
		self.assertFalse(R.rimborsabile(inizio, inizio - timedelta(days=5), False, 24))
		self.assertTrue(R.rimborsabile(inizio, inizio - timedelta(minutes=1), True, 0))
		self.assertFalse(R.rimborsabile(inizio, inizio + timedelta(minutes=1), True, 0))

	def test_scaduto(self):
		ora = datetime(2026, 10, 10, 10, 0)
		self.assertFalse(R.scaduto(ora, ora))
		self.assertTrue(R.scaduto(ora - timedelta(minutes=6), ora))
		self.assertFalse(R.scaduto(None, ora))


if __name__ == "__main__":
	unittest.main()
