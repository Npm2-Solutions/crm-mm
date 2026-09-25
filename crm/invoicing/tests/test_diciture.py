# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The legal wording, and the 2027 handover.

Without the doubling, every invoice issued in January 2027 cites repealed
articles. The tests pin both sides of the date.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from crm.invoicing.engine import diciture
from crm.invoicing.tests.base import UnitTestCase

PRIMA = date(2026, 6, 1)
DOPO = date(2027, 6, 1)


class RiferimentiTest(UnitTestCase):
	def test_prima_del_2027_si_citano_entrambe_le_norme(self):
		testo = diciture.esenzione(PRIMA)
		self.assertIn("art. 10, n. 18, del D.P.R. 633/1972", testo)
		self.assertIn("D.Lgs. 10/2026", testo)

	def test_dal_2027_resta_solo_il_testo_unico(self):
		testo = diciture.esenzione(DOPO)
		self.assertNotIn("633/1972", testo)
		self.assertIn("art. 37, comma 1, lett. t), del D.Lgs. 10/2026", testo)

	def test_la_struttura_cita_il_numero_19(self):
		self.assertIn("n. 19", diciture.esenzione(PRIMA, struttura=True))
		self.assertIn("lett. u)", diciture.esenzione(DOPO, struttura=True))


class BolloTest(UnitTestCase):
	def test_il_bollo_virtuale_senza_estremi_e_un_errore(self):
		with self.assertRaises(ValueError):
			diciture.bollo_virtuale(PRIMA, None, None, "Milano")

	def test_il_bollo_virtuale_con_estremi_li_riporta(self):
		testo = diciture.bollo_virtuale(PRIMA, "12345", date(2025, 1, 15), "Milano")
		self.assertIn("n. 12345 del 15/01/2025", testo)
		self.assertIn("Milano", testo)

	def test_il_contrassegno_non_puo_essere_successivo_alla_fattura(self):
		with self.assertRaises(ValueError):
			diciture.bollo_su_originale("01234567890123", date(2026, 7, 1), PRIMA)

	def test_il_contrassegno_anteriore_va_bene(self):
		testo = diciture.bollo_su_originale("01234567890123", date(2026, 5, 1), PRIMA)
		self.assertIn("01234567890123", testo)

	def test_senza_estremi_resta_la_formula_generica(self):
		self.assertIn("conservato presso lo studio", diciture.bollo_su_originale(None, None, PRIMA))


class AltreDicitureTest(UnitTestCase):
	def test_il_forfettario_ha_le_sue_due_righe(self):
		righe = diciture.forfettario()
		self.assertEqual(len(righe), 2)
		self.assertIn("L. 190/2014", righe[0])

	def test_l_opposizione_resta_neutra(self):
		testo = diciture.opposizione()
		self.assertIn("precompilata", testo)
		# The wording must say nothing about what the service was.
		self.assertNotIn("sanitar", testo.lower())

	def test_lo_split_payment_si_dichiara(self):
		self.assertIn("Scissione dei pagamenti", diciture.scissione_pagamenti(PRIMA))

	def test_la_ritenuta_riporta_aliquota_e_importo(self):
		testo = diciture.ritenuta_acconto(PRIMA, Decimal("20"), Decimal("200.00"))
		self.assertIn("20%", testo)
		self.assertIn("200.00", testo)

	def test_il_reverse_charge_spiega_di_che_caso_si_tratta(self):
		self.assertIn("subappalto", diciture.inversione_contabile("N6.3"))

	def test_il_duplice_esemplare_distingue_originale_e_copia(self):
		self.assertEqual(diciture.duplice_esemplare(1), "Originale")
		self.assertIn("Copia per il cliente", diciture.duplice_esemplare(2))

	def test_il_pagamento_non_tracciato_lo_dice_al_paziente(self):
		self.assertIn("detrazione del 19%", diciture.pagamento("MP01", False))
		self.assertNotIn("detrazione", diciture.pagamento("MP05", True))
