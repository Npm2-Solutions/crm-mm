# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Online visits, without a site: the room and when the person enters."""

import datetime
import re
import unittest

from crm.scheduling import visite_online_regole as R


def ora(ore: int, minuti: int = 0) -> datetime.datetime:
	return datetime.datetime(2026, 10, 8, ore, minuti)


class LaStanza(unittest.TestCase):
	def test_un_nome_che_nessuno_indovina(self):
		nomi = {R.nome_della_stanza() for _ in range(200)}
		self.assertEqual(len(nomi), 200)
		for nome in nomi:
			self.assertRegex(nome, r"^[a-z2-7]{24}$")

	def test_il_server_dell_agenzia(self):
		self.assertEqual(R.base_del_server("https://video.example.eu/"), "https://video.example.eu")
		self.assertEqual(R.base_del_server({"url": "https://example.eu/meet/"}), "https://example.eu/meet")
		self.assertEqual(R.base_del_server(" https://video.example.eu "), "https://video.example.eu")
		for nessuno in (None, "", "http://video.example.eu", "video.example.eu", "https://x.eu/?a=1", 42, {}):
			self.assertIsNone(R.base_del_server(nessuno), nessuno)

	def test_solo_https(self):
		self.assertTrue(R.link_valido("https://meet.google.com/abc-defg-hij"))
		self.assertFalse(R.link_valido("http://meet.google.com/abc"))
		self.assertFalse(R.link_valido("javascript:alert(1)"))
		self.assertFalse(R.link_valido("https://"))
		self.assertFalse(R.link_valido("https://a b.eu"))
		self.assertFalse(R.link_valido(None))

	def test_quale_link(self):
		server = "https://video.example.eu"
		# the one it has stays: made once, or pasted by the desk
		self.assertEqual(R.link_da_dare("https://zoom.us/j/1", server, None), "https://zoom.us/j/1")
		self.assertEqual(R.link_da_dare(None, server, "https://meet.google.com/x", "abc"), f"{server}/abc")
		nuovo = R.link_da_dare("", server, None)
		self.assertTrue(re.fullmatch(r"https://video\.example\.eu/[a-z2-7]{24}", nuovo))
		self.assertEqual(
			R.link_da_dare(None, None, " https://meet.google.com/x "), "https://meet.google.com/x"
		)
		self.assertIsNone(R.link_da_dare(None, None, "http://meet.google.com/x"))
		self.assertIsNone(R.link_da_dare(None, None, None))


class QuandoSiEntra(unittest.TestCase):
	def test_da_un_quarto_d_ora_prima_alla_fine(self):
		inizio, fine, link = ora(10), ora(10, 45), "https://video.example.eu/abc"
		self.assertEqual(R.perche_no(inizio, fine, ora(9, 44), "Confirmed", "Booked", link), R.PRESTO)
		self.assertIsNone(R.perche_no(inizio, fine, ora(9, 45), "Confirmed", "Booked", link))
		self.assertIsNone(R.perche_no(inizio, fine, ora(10, 30), "Scheduled", "Arrived", link))
		self.assertEqual(R.perche_no(inizio, fine, ora(10, 45), "Confirmed", "Booked", link), R.FINITO)

	def test_annullato_o_senza_stanza(self):
		inizio, fine, link = ora(10), ora(11), "https://video.example.eu/abc"
		self.assertEqual(R.perche_no(inizio, fine, ora(10), "Cancelled", "Booked", link), R.ANNULLATO)
		self.assertEqual(R.perche_no(inizio, fine, ora(10), "Confirmed", "Cancelled", link), R.ANNULLATO)
		# marked done while it runs: the person may come back into the room until the end
		self.assertIsNone(R.perche_no(inizio, fine, ora(10), "Completed", "Attended", link))
		self.assertEqual(R.perche_no(inizio, fine, ora(11), "Completed", "Attended", link), R.FINITO)
		self.assertEqual(R.perche_no(inizio, fine, ora(10), "No Show", "No Show", link), R.FINITO)
		self.assertEqual(R.perche_no(inizio, fine, ora(10), "Confirmed", "No Show", link), R.FINITO)
		self.assertEqual(R.perche_no(inizio, fine, ora(10), "Confirmed", "Booked", None), R.SENZA_STANZA)

	def test_tra_quanto(self):
		self.assertEqual(
			R.tra_quanto(ora(10), ora(11), ora(9)),
			{"opens_in": 45 * 60, "closes_in": 2 * 3600, "opens_at": "09:45"},
		)
		self.assertEqual(
			R.tra_quanto(ora(10), ora(11), ora(12)), {"opens_in": 0, "closes_in": 0, "opens_at": "09:45"}
		)
		# no end: it closes when it starts
		self.assertEqual(R.tra_quanto(ora(10), None, ora(9, 50))["closes_in"], 600)


if __name__ == "__main__":
	unittest.main()
