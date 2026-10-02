# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Every code in words, and only the ones a practice meets.

A code a DocType admits and the vocabulary does not name would reach a screen as
"RF04" or "TC13": the test reads the DocTypes' own options and wants each one named,
and translated. The healthcare profile is pinned value by value, because what it
leaves out is as much a decision as what it keeps.
"""

from __future__ import annotations

import json
import pathlib
import re

from crm.invoicing.engine import voci
from crm.invoicing.tests.base import UnitTestCase

RADICE = pathlib.Path(__file__).resolve().parents[3]
DOCTYPE = RADICE / "crm" / "invoicing" / "doctype"
CATALOGO_IT = RADICE / "crm" / "locale" / "it.po"

#: Kept here rather than imported from `crm.invoicing.scelte`, which needs a site:
#: the same pairs, checked against each other by `test_scelte`.
CAMPI_DEL_MOTORE = {
	("crm_invoicing_company", "tax_regime"): "regime_fiscale",
	("crm_invoicing_company", "sole_shareholder"): "socio_unico",
	("crm_invoicing_company", "liquidation_state"): "stato_liquidazione",
	("crm_invoicing_company", "fund_type"): "cassa",
	("crm_invoicing_company", "withholding_type"): "tipo_ritenuta",
	("crm_invoicing_company", "stamp_duty_mode"): "modalita_bollo",
	("crm_invoicing_company", "document_mode"): "modalita_documento",
	("crm_invoicing_company", "conservation_local"): "conservazione_locale",
	("crm_invoicing_company", "conservation_service"): "conservazione_sdi",
	("crm_invoicing_company", "sdi_mode"): "canale_sdi",
	("crm_invoicing_company", "sdi_flow"): "flusso_sdi",
	("crm_invoicing_company", "provider_environment"): "ambiente",
	("crm_billable_service", "vat_nature"): "natura",
	("crm_professional_qualification", "category"): "categoria_qualifica",
	("crm_professional_qualification", "sdi_rule"): "regola_sdi",
	("crm_professional_qualification", "fund_type"): "cassa",
	("crm_professional_qualification", "withholding_type"): "tipo_ritenuta",
	("crm_invoice", "document_type"): "tipo_documento",
	("crm_invoice", "recipient_type"): "tipo_destinatario",
	("crm_invoice", "fund_type"): "cassa",
	("crm_invoice", "withholding_type"): "tipo_ritenuta",
	("crm_invoice", "stamp_duty_mode"): "modalita_bollo",
	("crm_invoice", "payment_method"): "modalita_pagamento",
	("crm_invoice", "payment_terms"): "condizioni_pagamento",
	("crm_invoice", "channel"): "canale_documento",
	("crm_invoice", "payment_traced"): "pagamento_tracciato",
	("crm_invoice_item", "vat_nature"): "natura",
	("crm_invoice_payment", "payment_method"): "modalita_pagamento",
}


def opzioni_del_doctype(cartella: str, fieldname: str) -> set[str]:
	dati = json.loads((DOCTYPE / cartella / f"{cartella}.json").read_text())
	campo = next(f for f in dati["fields"] if f.get("fieldname") == fieldname)
	return {v for v in (campo.get("options") or "").split("\n") if v}


def msgid_tradotti() -> set[str]:
	"""Every msgid of the Italian catalogue that has a translation."""
	testo = CATALOGO_IT.read_text()
	coppie = re.findall(r'^msgid "(.*)"\nmsgstr "(.*)"', testo, re.M)
	return {msgid.replace('\\"', '"') for msgid, msgstr in coppie if msgstr}


class OgniCodiceHaUnNome(UnitTestCase):
	def test_ogni_valore_ammesso_dai_doctype_e_nel_suo_vocabolario(self):
		for (cartella, campo), famiglia in CAMPI_DEL_MOTORE.items():
			nominati = {voce.valore for voce in voci.tutte(famiglia)}
			mancanti = opzioni_del_doctype(cartella, campo) - nominati
			self.assertEqual(mancanti, set(), f"{cartella}.{campo}: no words for {sorted(mancanti)}")

	def test_valori_unici_e_nomi_presenti(self):
		for famiglia in voci.famiglie():
			valori = [voce.valore for voce in voci.tutte(famiglia)]
			self.assertEqual(len(valori), len(set(valori)), famiglia)
			for voce in voci.tutte(famiglia):
				self.assertTrue(voce.etichetta, f"{famiglia}.{voce.valore}")
				self.assertNotEqual(
					voce.etichetta, voce.valore, f"{famiglia}.{voce.valore} says only its code"
				)

	def test_ogni_parola_e_tradotta_in_italiano(self):
		tradotti = msgid_tradotti()
		mancanti = sorted(
			{
				testo
				for famiglia in voci.famiglie()
				for voce in voci.tutte(famiglia)
				for testo in (voce.etichetta, voce.spiegazione)
				if testo and testo not in tradotti
			}
		)
		self.assertEqual(mancanti, [], "not in crm/locale/it.po")

	def test_la_causale_sta_nei_due_caratteri_del_campo(self):
		for voce in voci.tutte("causale_pagamento"):
			self.assertLessEqual(len(voce.valore), 2, voce.valore)


class IlProfiloSanitario(UnitTestCase):
	def valori(self, famiglia, **opzioni):
		return [voce.valore for voce in voci.voci(famiglia, voci.SANITARIO, **opzioni)]

	def test_l_iva_di_un_centro_medico(self):
		self.assertEqual(self.valori("natura"), ["N4", "N2.2", "N1"])

	def test_i_regimi_di_un_centro_medico(self):
		self.assertEqual(self.valori("regime_fiscale"), ["RF01", "RF19", "RF02"])

	def test_solo_le_casse_della_sanita(self):
		self.assertEqual(self.valori("cassa"), ["TC09", "TC21", "TC20", "TC19", "TC11", "TC10", "TC22"])

	def test_i_documenti_e_i_pagamenti_che_servono(self):
		self.assertEqual(self.valori("tipo_documento"), ["TD01", "TD04", "TD05", "TD02", "TD06", "TD03"])
		self.assertEqual(
			self.valori("modalita_pagamento"), ["MP08", "MP01", "MP05", "MP02", "MP03", "MP19", "MP20"]
		)
		self.assertEqual(self.valori("tipo_ritenuta"), ["RT01", "RT02"])
		self.assertEqual(self.valori("causale_pagamento"), ["A", "M", "M2"])

	def test_il_profilo_generale_offre_tutto(self):
		self.assertEqual(len(voci.voci("natura")), len(voci.tutte("natura")))
		self.assertEqual(len(voci.voci("regime_fiscale")), 18)

	def test_un_valore_gia_scelto_resta(self):
		# a company that kept the regime of salt and tobacco still sees its own choice
		self.assertEqual(self.valori("regime_fiscale", attuale="RF05")[-1], "RF05")
		# and a value nobody named stays as it is, rather than vanishing
		self.assertEqual(self.valori("natura", attuale="N9")[-1], "N9")

	def test_una_colonna_tiene_i_valori_di_ogni_riga(self):
		valori = self.valori("natura", attuale=["N4", "N6.1", "", "N6.1"])
		self.assertEqual(valori, ["N4", "N2.2", "N1", "N6.1"])

	def test_una_regola_restringe(self):
		self.assertEqual(self.valori("natura", ammessi={"N4"}), ["N4"])

	def test_il_nome_di_un_valore(self):
		self.assertEqual(voci.etichetta("natura", "N4"), "Exempt (art. 10)")
		self.assertEqual(voci.etichetta("natura", "N9"), "N9")
		self.assertEqual(voci.etichetta("natura", ""), "")
