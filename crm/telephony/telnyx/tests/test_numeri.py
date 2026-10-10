# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Italian numbers from the centre's Telnyx account, on a real site (doc 64).

The kinds Telnyx sells in Italy - geographic and toll-free - with their price;
Telnyx's requirements with the centre's values in them; the number chosen first
and ordered with the documents, as PDF; every hour how the order went, told to
whoever asked; the documents good for the next number; a number given back. And
what the account spends, its alerts, a number verified with the code Telnyx
says, one of the centre's account taken into DottorCloud.
"""

import json
from io import BytesIO

import frappe
from pypdf import PdfWriter

from crm.notifiche import regole as N
from crm.telephony.telnyx import collegamento, consumi, numeri, trasloco, verificati
from crm.telephony.telnyx.tests.test_collegamento import TelnyxCase
from crm.tests.test_documenti_del_core import MANAGER

RICHIESTA = "CRM Phone Number Request"


def _pdf() -> bytes:
	"""A real PDF of one page: the site reads what it is given."""
	scritto = PdfWriter()
	scritto.add_blank_page(width=200, height=200)
	contenuto = BytesIO()
	scritto.write(contenuto)
	return contenuto.getvalue()


class NumeriCase(TelnyxCase):
	def setUp(self):
		super().setUp()
		frappe.db.delete(RICHIESTA, {"provider": "telnyx"})
		frappe.db.delete("CRM Notification", {"type": "Phone"})
		self.collega()
		# what Telnyx said of the account is kept ten minutes: not from one test to the next
		frappe.cache.delete_value(consumi._chiave(collegamento._impostazioni()))
		self.telnyx.in_vendita = {
			"local": ["+390212340001", "+390212340002", "+390612340003"],
			"toll_free": ["+39800123456"],
		}
		frappe.set_user(MANAGER)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def file(self, nome="visura.pdf"):
		return frappe.get_doc(
			{
				"doctype": "File",
				"file_name": nome,
				"is_private": 1,
				"content": _pdf() if nome.endswith(".pdf") else b"testo",
			}
		).insert(ignore_permissions=True)

	def manda(self, numero="+390212340001", tutti=True, nome_del_file="visura.pdf"):
		requisiti = numeri.get_number_requirements("local", "business", "02")
		valori = {campo["name"]: campo["value"] or "valore" for campo in requisiti["fields"]}
		documenti = []
		for requisito in requisiti["documents"]:
			accettato = requisito["accepted"][0]
			if accettato["address"]:
				documenti.append(
					{"requirement": requisito["requirement"], "type": accettato["type"], "address": True}
				)
			elif tutti:
				documenti.append(
					{
						"requirement": requisito["requirement"],
						"type": accettato["type"],
						"file": self.file(nome_del_file).name,
					}
				)
		return numeri.send_number_request(
			"local",
			requisiti["regulation"],
			json.dumps(valori),
			json.dumps(documenti),
			address=json.dumps(
				{"street": "Via Roma 1", "city": "Milano", "region": "MI", "postal_code": "20100"}
			),
			area_code="02",
			end_user_type="business",
			phone_number=numero,
		)


class LOfferta(NumeriCase):
	def test_i_tipi_con_il_prezzo(self):
		offerta = numeri.get_number_offer()
		tipi = {tipo["key"]: tipo for tipo in offerta["kinds"]}
		self.assertEqual(set(tipi), {"local", "toll_free"})
		self.assertEqual((tipi["local"]["price"], tipi["local"]["currency"]), (1.0, "USD"))
		self.assertTrue(offerta["number_first"])
		self.assertEqual(offerta["files"]["extensions"], ["pdf"])

	def test_i_numeri_della_zona(self):
		trovati = numeri.search_numbers("local", "02")["numbers"]
		self.assertEqual([n["phone_number"] for n in trovati], ["+390212340001", "+390212340002"])
		self.assertEqual(trovati[0]["locality"], "Milano")

	def test_i_requisiti(self):
		requisiti = numeri.get_number_requirements("local", "business", "02")
		campi = {campo["name"]: campo for campo in requisiti["fields"]}
		self.assertEqual(campi["r-tipo"]["value"], "legal_entity")
		self.assertTrue(any(d["accepted"][0]["address"] for d in requisiti["documents"]))


class LaRichiesta(NumeriCase):
	def test_mandata_con_il_numero_va_in_verifica(self):
		esito = self.manda()
		self.assertEqual((esito["status"], esito["missing"]), ("In review", []))
		richiesta = frappe.get_doc(RICHIESTA, esito["request"])
		self.assertEqual(richiesta.provider, "telnyx")
		(gruppo,) = self.telnyx.gruppi.values()
		valori = {r["requirement_id"]: r["field_value"] for r in gruppo["regulatory_requirements"]}
		self.assertEqual(valori["r-tipo"], "legal_entity")
		self.assertIn(valori["r-indirizzo"], self.telnyx.indirizzi)
		self.assertIn(valori["r-visura"], self.telnyx.documenti)
		(ordine,) = self.telnyx.ordini.values()
		self.assertEqual(ordine["phone_numbers"][0]["requirement_group_id"], gruppo["id"])
		self.assertEqual(ordine["connection_id"], collegamento._impostazioni().texml_application_id)
		self.assertEqual(json.loads(richiesta.pending_orders)[0]["number"], "+390212340001")

	def test_senza_un_documento_resta_una_bozza(self):
		esito = self.manda(tutti=False)
		with self.assertRaises(frappe.ValidationError):
			self.manda(tutti=True, nome_del_file="visura.txt")
		self.assertEqual(esito["status"], "Draft")
		self.assertIn("Telnyx asks for", esito["missing"][0])
		self.assertEqual(self.telnyx.ordini, {})

	def test_approvato_il_numero_e_del_centro(self):
		esito = self.manda()
		(ordine,) = self.telnyx.ordini
		self.telnyx.esito(ordine, "success")
		self.assertEqual(numeri.aggiorna_le_richieste(), [esito["request"]])
		richiesta = frappe.get_doc(RICHIESTA, esito["request"])
		self.assertEqual((richiesta.status, richiesta.numbers), ("Approved", "+390212340001"))
		self.assertFalse(frappe.get_all("File", filters={"attached_to_name": richiesta.name}))
		self.assertEqual(
			frappe.db.get_value("CRM Notification", {"type": "Phone"}, "sentence"), N.NUMERO_APPROVATO_TELNYX
		)
		self.assertEqual(frappe.db.get_value("CRM Caller ID", "+390212340001", "routes_to_crm"), 1)
		# the documents are good for the next number of the same kind and area
		self.assertEqual(
			numeri.get_number_requirements("local", "business", "02")["approved"], richiesta.name
		)
		numeri.buy_number(richiesta.name, "+390212340002")
		self.assertEqual(frappe.db.get_value(RICHIESTA, richiesta.name, "status"), "In review")
		self.assertEqual(len(self.telnyx.ordini), 2)

	def test_rifiutato_dice_perche(self):
		esito = self.manda()
		(ordine,) = self.telnyx.ordini
		richiesta = frappe.get_doc(RICHIESTA, esito["request"])
		self.telnyx.commenti.append(
			{
				"comment_record_id": richiesta.bundle_sid,
				"commenter_type": "admin",
				"body": "The proof of address is older than three months.",
			}
		)
		self.telnyx.esito(ordine, "failure")
		numeri.aggiorna_le_richieste()
		richiesta.reload()
		self.assertEqual(richiesta.status, "Rejected")
		self.assertIn("three months", richiesta.failure)
		self.assertEqual(
			frappe.db.get_value("CRM Notification", {"type": "Phone"}, "sentence"), N.NUMERO_RIFIUTATO_TELNYX
		)

	def test_si_rilascia_solo_uno_di_dottorcloud(self):
		nostro = self.telnyx.numero("+390299990000", tags=[collegamento.segno()])
		altro = self.telnyx.numero("+390299990001", connection_id=self.telnyx.connessione("PBX"))
		numeri.release_number(nostro["phone_number"])
		self.assertNotIn(nostro["id"], self.telnyx.numeri)
		with self.assertRaises(frappe.ValidationError):
			numeri.release_number(altro["phone_number"])
		self.assertIn(altro["id"], self.telnyx.numeri)


class LaSpesa(NumeriCase):
	def test_il_mese_il_bilancio_e_i_problemi(self):
		self.telnyx.uso = {
			"messaging": [{"cost": "1.50", "count": 20}],
			"call-control": [{"cost": "2.00", "connected": 4}],
		}
		self.telnyx.falliti = [{"errors": ["40001"], "created_at": "2026-10-09T10:00:00Z"}]
		dati = consumi.get_telnyx_usage()
		self.assertTrue(dati["visible"])
		self.assertEqual(dati["month"]["total"], "3.50")
		self.assertEqual(dati["balance"]["balance"], "120.00")
		(problema,) = dati["problems"]
		self.assertEqual((problema["code"], problema["count"]), (40001, 1))
		self.assertIn("landline", problema["sentence"])

	def test_gli_avvisi_una_volta(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, {"spend_alert": 3, "balance_alert": 200})
		self.telnyx.uso = {"messaging": [{"cost": "5.00", "count": 20}]}
		dette = consumi.controlla_gli_avvisi()
		self.assertEqual(dette, [N.SPESA_TELNYX, N.CREDITO_TELNYX])
		self.assertEqual(consumi.controlla_gli_avvisi(), [])
		# topped up: the low balance is told again only after it goes down again
		self.telnyx.bilancio["balance"] = "500.00"
		consumi.controlla_gli_avvisi()
		self.assertFalse(frappe.db.get_single_value(collegamento.IMPOSTAZIONI, "balance_alert_told"))
		self.telnyx.bilancio["balance"] = "50.00"
		self.assertEqual(consumi.controlla_gli_avvisi(), [N.CREDITO_TELNYX])


class IlNumeroVerificato(NumeriCase):
	def test_il_codice_di_telnyx_scritto_qui(self):
		stato = verificati.verify_number("+390687654321", "Fisso dello studio")
		self.assertEqual((stato["status"], stato["enabled"]), ("Pending", False))
		self.assertEqual(frappe.db.get_value("CRM Caller ID", "+390687654321", "provider"), "telnyx")
		with self.assertRaises(frappe.ValidationError):
			verificati.confirm_code("+390687654321", "000000")
		stato = verificati.confirm_code("+390687654321", "123456")
		self.assertEqual((stato["status"], stato["enabled"]), ("Verified", True))
		verificati.remove_verified("+390687654321")
		self.assertNotIn("+390687654321", self.telnyx.verificati)
		self.assertEqual(frappe.db.get_value("CRM Caller ID", "+390687654321", "enabled"), 0)


class GiaNelConto(NumeriCase):
	def test_si_prende_dall_altra_app_non_dal_centralino(self):
		altra = self.telnyx.connessione("Vecchia app", "texml_application")
		dall_app = self.telnyx.numero("+390655550001", connection_id=altra)
		centralino = self.telnyx.connessione("PBX", "ip_connection")
		self.telnyx.numero("+390655550002", connection_id=centralino)
		righe = {r["number"]: r for r in trasloco.get_account_numbers()}
		self.assertEqual(righe["+390655550001"]["now_on"], "Vecchia app")
		self.assertTrue(righe["+390655550002"]["reason"])
		trasloco.move_number(dall_app["id"])
		self.assertEqual(dall_app["connection_id"], collegamento._impostazioni().texml_application_id)
		self.assertIn(collegamento.segno(), dall_app["tags"])
		self.assertEqual(frappe.db.get_value("CRM Caller ID", "+390655550001", "routes_to_crm"), 1)
