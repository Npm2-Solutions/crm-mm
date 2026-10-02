# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a notification says: the sentences, their names, the words of the ones
written before, the first words of a message, the kinds. Without a site."""

from __future__ import annotations

import re
from pathlib import Path

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.notifiche import regole as R

CATALOGO = Path(__file__).resolve().parents[2] / "locale" / "it.po"


def _catalogo() -> dict[str, str]:
	"""The Italian catalogue, msgid to msgstr, without the entries with a context."""
	testo = CATALOGO.read_text(encoding="utf-8")
	voci = {}
	for m in re.finditer(r'^(msgctxt ".*"\n)?msgid "(.*)"\nmsgstr "(.*)"$', testo, re.M):
		if m.group(1):
			continue

		def leggi(s):
			return s.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")

		voci[leggi(m.group(2))] = leggi(m.group(3))
	return voci


class LaFrase(UnitTestCase):
	def test_i_nomi_in_grassetto(self):
		self.assertEqual(
			R.frase(R.MENZIONE, ["Anna Neri", "Laura Bianchi"]),
			"<b>Anna Neri</b> mentioned you in a comment on <b>Laura Bianchi</b>",
		)

	def test_un_nome_non_scrive_html(self):
		testo = R.frase(R.WHATSAPP, ["<script>x</script> & Co"])
		self.assertNotIn("<script>", testo)
		self.assertIn("&lt;script&gt;x&lt;/script&gt; &amp; Co", testo)

	def test_le_parole_della_frase_sono_testo(self):
		self.assertEqual(R.frase("a < b: {0}", ["c"]), "a &lt; b: <b>c</b>")

	def test_una_traduzione_sbagliata_si_legge_in_inglese(self):
		# a translation that lost a place falls back on the sentence it translates
		self.assertEqual(
			R.frase("{0} ha scritto {2}", ["Anna", "Luca"], "{0} wrote to {1}"),
			"<b>Anna</b> wrote to <b>Luca</b>",
		)

	def test_quanti_messaggi(self):
		self.assertEqual(
			R.frase(R.WHATSAPP_MOLTI, ["Laura", 3]),
			"You received <b>3</b> WhatsApp messages from <b>Laura</b>",
		)


class LeParoleDiPrima(UnitTestCase):
	"""What the CRM wrote before the sentences were kept apart reads the same way."""

	def test_una_menzione_di_prima(self):
		prima = """
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">Anna</span> mentioned you in a
                comment on <span class="font-medium text-ink-gray-9">Laura</span>
            </div>
        """
		self.assertEqual(R.testo_vecchio(prima), "<b>Anna</b> mentioned you in a comment on <b>Laura</b>")

	def test_un_testo_semplice(self):
		self.assertEqual(
			R.testo_vecchio("3 appointments today have no outcome"), "3 appointments today have no outcome"
		)

	def test_un_nome_con_e_commerciale(self):
		# the area's names were escaped before they were glued in
		self.assertEqual(R.testo_vecchio("Rossi &amp; figli asked"), "Rossi &amp; figli asked")

	def test_niente(self):
		self.assertEqual(R.testo_vecchio(None), "")


class LePrimeParole(UnitTestCase):
	def test_senza_markup_su_una_riga(self):
		self.assertEqual(
			R.solo_testo("<p>Ciao <span data-type='mention'>@Anna</span>, a domani</p><p>Luca</p>"),
			"Ciao @Anna, a domani Luca",
		)

	def test_tagliata_a_una_parola(self):
		testo = "parola " * 40
		anteprima = R.anteprima(testo, 30)
		self.assertTrue(anteprima.endswith("…"))
		self.assertLessEqual(len(anteprima), 31)
		self.assertTrue(anteprima[:-1].endswith("parola"))

	def test_corta_resta_intera(self):
		self.assertEqual(R.anteprima("Grazie!"), "Grazie!")


class ChiTipoE(UnitTestCase):
	def test_assegnata_e_tolta(self):
		self.assertEqual(R.genere("Assignment", "CRM Lead", R.ASSEGNATA), "assigned")
		self.assertEqual(R.genere("Assignment", "CRM Deal", R.TOLTA_TRATTATIVA), "unassigned")

	def test_un_attivita(self):
		self.assertEqual(R.genere("Assignment", "CRM Task", R.COMPITO), "task")
		self.assertEqual(R.genere("Assignment", "CRM Task", R.COMPITO_TOLTO), "task_removed")

	def test_gli_altri(self):
		for tipo, genere in (
			("Mention", "mention"),
			("WhatsApp", "whatsapp"),
			("SMS", "sms"),
			("Agenda", "agenda"),
			("Area", "area"),
			("Invoicing", "invoicing"),
			("Automation", "automation"),
			("Something new", "other"),
		):
			self.assertEqual(R.genere(tipo), genere)


class IlCatalogo(UnitTestCase):
	"""Every sentence is read in Italian, with the same places as the English: a
	place lost or added would print the wrong name, or none."""

	def test_ogni_frase_e_tradotta(self):
		voci = _catalogo()
		for frase in R.FRASI:
			self.assertIn(frase, voci, frase)
			self.assertTrue(voci[frase], frase)

	def test_con_gli_stessi_posti(self):
		voci = _catalogo()
		for frase in R.FRASI:
			self.assertEqual(
				sorted(re.findall(r"\{\d\}", voci[frase])), sorted(re.findall(r"\{\d\}", frase)), frase
			)
