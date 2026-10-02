# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The Sistema TS's choices on a real site: the fields invoicing hands over in
words are the ones the pure test checks, and the expense types follow the issuer.

A physiotherapist invoicing in their own name has one expense type, and the
service card offers that one; a company that reports nothing narrows nothing.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_fields
from crm.invoicing import scelte
from crm.invoicing.engine import voci
from crm.tessera_sanitaria import tipi_spesa_offerti
from crm.tessera_sanitaria.tests.test_voci import CAMPI


def _categoria(valore):
	"""The issuer's category, whichever company is asked for."""
	return patch.object(frappe.db, "get_value", return_value=valore)


def _con_categoria(regola, doc):
	"""The registered rule, asked about a company whose category is a physiotherapist's."""
	with _categoria("professionista_sanitario"):
		return regola({"company": "Studio", **doc})


class LeSceltePerIlSistemaTS(IntegrationTestCase):
	def test_le_coppie_sono_quelle_del_test_puro(self):
		for (cartella, campo), famiglia in CAMPI.items():
			doctype = frappe.get_meta(
				frappe.unscrub(cartella.rsplit("/", 1)[-1]).replace("Crm ", "CRM ")
			).name
			self.assertEqual(scelte.famiglia_di(doctype, campo), famiglia, f"{doctype}.{campo}")

	def test_i_tipi_di_spesa_seguono_chi_emette(self):
		with _categoria("professionista_sanitario"):
			self.assertEqual(tipi_spesa_offerti({"company": "Studio"}), frozenset({"SP"}))
		with _categoria("non_sanitario"):
			self.assertIsNone(tipi_spesa_offerti({"company": "Studio"}))

	def test_la_scheda_della_prestazione_offre_il_solo_tipo_ammesso(self):
		regola = scelte._regole["tipo_spesa"]
		with (
			patch.object(scelte, "profilo", return_value=voci.SANITARIO),
			patch.dict(scelte._regole, {"tipo_spesa": lambda doc: _con_categoria(regola, doc)}),
		):
			campi = get_fields("CRM Billable Service")
		tipo = next(campo for campo in campi if campo.get("fieldname") == "ts_expense_type")
		self.assertEqual([s["value"] for s in tipo["options"]], ["", "SP"])
		self.assertEqual(tipo["options"][1]["label"], frappe._("Health professional's services"))
