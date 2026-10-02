# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the space spends, without a site: this month by kind, the alert's amount,
what to do with Twilio's trigger (doc 52, fifth part)."""

import unittest
from decimal import Decimal

from crm.telephony import consumi_regole as R

INDIRIZZO = "https://aurora.example/api/method/crm.integrations.twilio.api.spend_reached"


def riga(price, count=0, usage=0, usage_unit="", price_unit="usd"):
	return {
		"price": price,
		"count": count,
		"usage": usage,
		"usage_unit": usage_unit,
		"price_unit": price_unit,
	}


class IlMese(unittest.TestCase):
	def test_per_voce_e_il_totale_di_twilio(self):
		mese = R.consumi(
			{
				"calls": riga("12.345", count=40, usage=310, usage_unit="minutes"),
				"sms": riga("9.30", count=100, usage=100, usage_unit="messages"),
				"phonenumbers": riga("45", count=1),
				"recordings": riga("0.78", count=12, usage=310, usage_unit="minutes"),
				"recordingstorage": riga("0.05"),
				"transcriptions": riga("1"),
				"totalprice": riga("70.50"),
			}
		)
		self.assertEqual(mese["currency"], "USD")
		self.assertEqual(mese["total"], "70.50")
		voci = {voce["key"]: voce for voce in mese["items"]}
		self.assertEqual(
			(voci["calls"]["count"], voci["calls"]["minutes"], voci["calls"]["price"]), (40, 310, "12.35")
		)
		self.assertEqual((voci["sms"]["count"], voci["sms"]["minutes"]), (100, None))
		self.assertEqual(voci["numbers"]["price"], "45.00")
		# recordings, keeping them and transcriptions are one kind
		self.assertEqual(voci["recordings"]["price"], "1.83")
		# what the total holds besides them
		self.assertEqual(voci["other"]["price"], "2.03")
		self.assertEqual(
			[voce["key"] for voce in mese["items"]], ["calls", "sms", "numbers", "recordings", "other"]
		)

	def test_un_mese_appena_cominciato(self):
		mese = R.consumi({})
		self.assertEqual((mese["total"], mese["currency"]), ("0.00", ""))
		self.assertNotIn("other", [voce["key"] for voce in mese["items"]])
		self.assertTrue(all(voce["price"] == "0.00" for voce in mese["items"]))

	def test_numeri_storti(self):
		mese = R.consumi({"calls": riga("NaN"), "totalprice": riga("abc")})
		self.assertEqual(mese["total"], "0.00")


class LAvviso(unittest.TestCase):
	def test_la_soglia(self):
		self.assertIsNone(R.soglia(None))
		self.assertIsNone(R.soglia(""))
		self.assertIsNone(R.soglia(0))
		self.assertEqual(R.soglia("50"), Decimal("50.00"))
		self.assertEqual(R.soglia(12.5), Decimal("12.50"))
		for storta in (-5, "nan", "inf", "200000", "abc"):
			with self.assertRaises(ValueError, msg=storta):
				R.soglia(storta)

	def test_che_cosa_fare_del_trigger(self):
		self.assertEqual(R.cosa_fare_del_trigger(None, None, INDIRIZZO), "")
		self.assertEqual(R.cosa_fare_del_trigger(None, Decimal("50"), INDIRIZZO), "create")
		attuale = {"trigger_value": "50", "callback_url": INDIRIZZO}
		self.assertEqual(R.cosa_fare_del_trigger(attuale, Decimal("50.00"), INDIRIZZO), "")
		# Twilio does not change a trigger's amount
		self.assertEqual(R.cosa_fare_del_trigger(attuale, Decimal("80"), INDIRIZZO), "replace")
		self.assertEqual(R.cosa_fare_del_trigger(attuale, Decimal("50"), "https://nuovo.example/x"), "update")
		self.assertEqual(R.cosa_fare_del_trigger(attuale, None, INDIRIZZO), "delete")
