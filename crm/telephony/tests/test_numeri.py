# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A new Italian number, asked from DottorCloud, on a real site (doc 52, second part).

The manager of Centro Aurora, connected to Twilio, chooses a mobile number: its
price a month is Twilio's, the fields Twilio asks come with the centre's invoicing
details in them, the documents are uploaded here. Twilio's evaluation says what is
missing before anything goes for review; sent again, the draft of before leaves
Twilio. Only a file the manager uploaded for this goes to Twilio - never a person's
records. Every hour DottorCloud asks how it went and tells the manager; approved,
the files go, and the number is chosen and bought, already answering on DottorCloud.
The same documents buy the next number of the kind at once; a geographic one only
in its area. A number of the space is released from here.
"""

from functools import cache
from io import BytesIO
from unittest.mock import patch

import frappe
from pypdf import PdfWriter

from crm import marchio
from crm.notifiche import regole as N
from crm.telephony import collegamento, numeri
from crm.telephony import numeri_regole as R
from crm.telephony.tests.test_collegamento import SMS, VOCE, TwilioCase
from crm.tests.test_documenti_del_core import FRONT_DESK, MANAGER

RICHIESTA = numeri.RICHIESTA
AZIENDA = "CRM Invoicing Company"
#: what the legal representative's name is, which invoicing does not keep for a company
RAPPRESENTANTE = {"first_name": "Anna", "last_name": "Bianchi"}


@cache
def _pdf() -> bytes:
	"""A real PDF of one page: the site reads what it is given."""
	scritto = PdfWriter()
	scritto.add_blank_page(width=200, height=200)
	contenuto = BytesIO()
	scritto.write(contenuto)
	return contenuto.getvalue()


class NumeriCase(TwilioCase):
	def setUp(self):
		super().setUp()
		self.collega()
		frappe.db.delete(RICHIESTA)
		frappe.db.delete("CRM Notification", {"type": "Phone"})
		azienda = frappe.get_doc(
			{
				"doctype": AZIENDA,
				"company_name": f"Centro Aurora srl {frappe.generate_hash(length=6)}",
				"tax_id": "00743110157",
				"address_line": "Via Roma",
				"civic_number": "1",
				"postal_code": "20121",
				"city": "Milano",
				"province": "MI",
				"tax_regime": "RF01",
				"email": "info@aurora.example",
				"pec": "aurora@pec.example",
			}
		).insert(ignore_permissions=True)
		frappe.db.set_single_value("CRM Invoicing Settings", "default_company", azienda.name)
		self.azienda = azienda
		finto = patch("crm.telephony.numeri._posta", self.mondo.carica)
		finto.start()
		self.addCleanup(finto.stop)
		frappe.set_user(MANAGER)

	# ------------------------------------------------------------------ helpers

	def file(self, nome="visura.pdf", **valori) -> str:
		return (
			frappe.get_doc(
				{"doctype": "File", "file_name": nome, "content": _pdf(), "is_private": 1, **valori}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def documenti(self, requisiti, file=None) -> list[dict]:
		"""The first document of each requirement, as the page sends it."""
		scelti = []
		for requisito in requisiti["documents"]:
			documento = requisito["accepted"][0]
			scelti.append(
				{
					"requirement": requisito["requirement"],
					"type": documento["type"],
					"fields": documento["fields"],
					"address": documento["address"],
					"values": {c["name"]: c["value"] for c in documento["inputs"]},
					"file": None if documento["address"] else (file or self.file()),
				}
			)
		return scelti

	def manda(self, tipo="mobile", zona=None, togli=(), documenti=None, **altro):
		requisiti = numeri.get_number_requirements(tipo, None, zona)
		valori = {c["name"]: c["value"] for c in requisiti["fields"]} | RAPPRESENTANTE
		for campo in togli:
			valori.pop(campo, None)
		return numeri.send_number_request(
			tipo,
			requisiti["regulation"],
			{k: v for k, v in valori.items() if k in {c["name"] for c in requisiti["fields"]}},
			self.documenti(requisiti) if documenti is None else documenti,
			address=requisiti["address"],
			area_code=zona,
			**altro,
		)

	def pacchetto(self, richiesta: str):
		return self.mondo.pacchetti[frappe.db.get_value(RICHIESTA, richiesta, "bundle_sid")]

	def approva(self, richiesta: str, stato="twilio-approved"):
		self.pacchetto(richiesta).status = stato
		frappe.set_user("Administrator")
		mosse = numeri.aggiorna_le_richieste()
		frappe.set_user(MANAGER)
		return mosse


class CosaSiOffre(NumeriCase):
	def test_i_tipi_con_il_prezzo_di_twilio(self):
		offerta = numeri.get_number_offer()
		self.assertEqual([t["key"] for t in offerta["kinds"]], ["mobile", "local", "toll_free"])
		self.assertEqual([t["price"] for t in offerta["kinds"]], [45.0, 4.25, 27.0])
		self.assertEqual({t["currency"] for t in offerta["kinds"]}, {"USD"})
		self.assertEqual(
			(offerta["owner"], offerta["email"], offerta["requests"]), ("business", "info@aurora.example", [])
		)
		self.assertEqual([o["key"] for o in offerta["owners"]], ["business", "individual"])

	def test_i_campi_con_i_dati_del_centro(self):
		requisiti = numeri.get_number_requirements("mobile")
		self.assertEqual(requisiti["regulation"], self.mondo.regole[("mobile", "business")])
		valori = {c["name"]: c["value"] for c in requisiti["fields"]}
		self.assertEqual(valori["business_name"], self.azienda.company_name)
		self.assertEqual(valori["business_registration_number"], "00743110157")
		self.assertEqual(
			requisiti["address"],
			{"street": "Via Roma 1", "city": "Milano", "region": "MI", "postal_code": "20121"},
		)
		# Twilio writes to an ordinary mailbox, never to the PEC
		self.assertEqual(requisiti["email"], "info@aurora.example")
		indirizzo, registro = requisiti["documents"]
		self.assertTrue(indirizzo["accepted"][0]["address"])
		# Twilio's two kinds of visura are one choice
		self.assertEqual([d["type"] for d in registro["accepted"]], ["business_registration"])
		self.assertEqual(registro["accepted"][0]["label"], "Business register extract (visura camerale)")

	def test_un_professionista_ha_i_suoi_documenti(self):
		requisiti = numeri.get_number_requirements("mobile", "individual")
		self.assertEqual(requisiti["end_user_type"], "individual")
		self.assertEqual([c["name"] for c in requisiti["fields"]], ["first_name", "last_name"])
		self.assertEqual(requisiti["documents"][0]["accepted"][0]["type"], "government_issued_document")

	def test_un_geografico_chiede_la_zona(self):
		with self.assertRaises(frappe.ValidationError):
			numeri.get_number_requirements("local")

	def test_la_segreteria_no(self):
		frappe.set_user(FRONT_DESK)
		for chiamata in (
			numeri.get_number_offer,
			lambda: numeri.get_number_requirements("mobile"),
			lambda: numeri.search_numbers("mobile"),
			lambda: numeri.release_number("+393331234567"),
		):
			with self.assertRaises(frappe.PermissionError):
				chiamata()


class IDocumentiATwilio(NumeriCase):
	def test_tutto_in_regola_va_in_verifica(self):
		esito = self.manda()
		self.assertEqual((esito["status"], esito["missing"]), (R.IN_VERIFICA, []))
		richiesta = frappe.get_doc(RICHIESTA, esito["request"])
		pacchetto = self.pacchetto(richiesta.name)
		self.assertEqual(pacchetto.status, "pending-review")
		self.assertEqual(pacchetto.email, "info@aurora.example")
		self.assertTrue(pacchetto.friendly_name.startswith(f"{marchio.nome()} · "))
		# whose the number is, as written
		utente = self.mondo.utenti[richiesta.end_user_sid]
		self.assertEqual((utente.type, utente.attributes["last_name"]), ("business", "Bianchi"))
		# the address, and the document that proves it
		indirizzo = self.mondo.indirizzi[richiesta.address_sid]
		self.assertEqual(
			(indirizzo.street, indirizzo.city, indirizzo.iso_country), ("Via Roma 1", "Milano", "IT")
		)
		# the file is the request's now, and Twilio has it
		(nome_del_file,) = frappe.get_all(
			"File", {"attached_to_doctype": RICHIESTA, "attached_to_name": richiesta.name}, pluck="file_name"
		)
		self.assertTrue(nome_del_file.startswith("visura") and nome_del_file.endswith(".pdf"))
		(caricato,) = self.mondo.caricati
		self.assertEqual(caricato[1:3], ("business_registration", nome_del_file))
		self.assertEqual(caricato[3]["business_registration_number"], "00743110157")
		self.assertEqual((richiesta.requested_by, richiesta.email), (MANAGER, "info@aurora.example"))

	def test_quello_che_manca_prima_di_mandarlo(self):
		esito = self.manda(togli=("last_name",))
		self.assertEqual(esito["status"], R.BOZZA)
		self.assertEqual(len(esito["missing"]), 1)
		self.assertIn("Surname", esito["missing"][0])
		prima = self.pacchetto(esito["request"])
		# nothing went for review
		self.assertEqual(prima.status, "draft")

		# put right and sent again: the same request, and the draft of before leaves Twilio
		requisiti = numeri.get_number_requirements("mobile")
		valori = {c["name"]: c["value"] for c in requisiti["fields"]} | RAPPRESENTANTE
		di_nuovo = numeri.send_number_request(
			"mobile",
			requisiti["regulation"],
			valori,
			self.documenti(requisiti, file=self.allegato(esito["request"])),
			address=requisiti["address"],
			request=esito["request"],
		)
		self.assertEqual((di_nuovo["request"], di_nuovo["status"]), (esito["request"], R.IN_VERIFICA))
		self.assertNotIn(prima.sid, self.mondo.pacchetti)
		self.assertEqual(frappe.db.count(RICHIESTA), 1)

	def test_rimandandola_ritrova_quello_che_era_scritto(self):
		esito = self.manda(togli=("last_name",))
		di_prima = numeri.get_number_requirements("mobile", None, None, esito["request"])["previous"]
		self.assertEqual(di_prima["request"], esito["request"])
		self.assertEqual(
			(di_prima["values"]["first_name"], di_prima["email"]), ("Anna", "info@aurora.example")
		)
		self.assertEqual(di_prima["choices"]["business_registration_info"], "business_registration")
		self.assertEqual(
			di_prima["files"]["business_registration_info"]["name"], self.allegato(esito["request"])
		)
		self.assertEqual(di_prima["address"]["city"], "Milano")
		# a request with Twilio has nothing to write again
		self.manda(request=esito["request"], togli=())
		self.assertIsNone(numeri.get_number_requirements("mobile", None, None, esito["request"])["previous"])

	def allegato(self, richiesta: str) -> str:
		return frappe.get_all(
			"File", {"attached_to_doctype": RICHIESTA, "attached_to_name": richiesta}, pluck="name"
		)[0]

	def test_in_verifica_non_si_rimanda(self):
		esito = self.manda()
		with self.assertRaises(frappe.ValidationError):
			self.manda(request=esito["request"])
		with self.assertRaises(frappe.ValidationError):
			numeri.delete_number_request(esito["request"])

	def test_una_bozza_si_toglie_anche_da_twilio(self):
		esito = self.manda(togli=("last_name",))
		pacchetto = self.pacchetto(esito["request"]).sid
		file_doc = self.allegato(esito["request"])
		numeri.delete_number_request(esito["request"])
		self.assertFalse(frappe.db.exists(RICHIESTA, esito["request"]))
		self.assertFalse(frappe.db.exists("File", file_doc))
		self.assertNotIn(pacchetto, self.mondo.pacchetti)


class SoloIFileGiusti(NumeriCase):
	"""Only a file uploaded for this goes to Twilio: nothing else of the site's."""

	def manda_con(self, file_doc: str):
		requisiti = numeri.get_number_requirements("mobile")
		return self.manda(documenti=self.documenti(requisiti, file=file_doc))

	def assert_rifiutato(self, file_doc: str, parole: str = "uploaded here"):
		with self.assertRaises(frappe.ValidationError) as rifiuto:
			self.manda_con(file_doc)
		self.assertIn(parole, str(rifiuto.exception))
		self.assertFalse(self.mondo.caricati)
		self.assertFalse([c for c in self.mondo.cambi if c[1] in ("create Bundle", "create EndUser")])
		self.assertFalse(frappe.db.count(RICHIESTA))

	def test_quello_di_un_altro(self):
		frappe.set_user(FRONT_DESK)
		suo = self.file()
		frappe.set_user(MANAGER)
		self.assert_rifiutato(suo)

	def test_quello_di_una_persona(self):
		persona = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Laura", "last_name": "Rossi"}).insert(
			ignore_permissions=True
		)
		self.assert_rifiutato(
			self.file("referto.pdf", attached_to_doctype="CRM Lead", attached_to_name=persona.name)
		)

	def test_uno_pubblico(self):
		self.assert_rifiutato(self.file(is_private=0))

	def test_uno_che_twilio_non_prende(self):
		self.assert_rifiutato(self.file("visura.docx"), "PDF")
		troppo = self.file()
		frappe.db.set_value("File", troppo, "file_size", R.MASSIMO + 1)
		self.assert_rifiutato(troppo, "5 MB")

	def test_un_documento_senza_file(self):
		requisiti = numeri.get_number_requirements("mobile")
		documenti = self.documenti(requisiti)
		documenti[1]["file"] = None
		with self.assertRaises(frappe.ValidationError):
			self.manda(documenti=documenti)


class ComeEAndata(NumeriCase):
	def test_approvata_avvisa_e_toglie_i_file(self):
		esito = self.manda()
		file_doc = frappe.get_all("File", {"attached_to_doctype": RICHIESTA}, pluck="name")
		self.assertEqual(self.approva(esito["request"]), [esito["request"]])
		richiesta = frappe.get_doc(RICHIESTA, esito["request"])
		self.assertEqual((richiesta.status, richiesta.details), (R.APPROVATA, None))
		self.assertFalse(frappe.db.exists("File", file_doc[0]))
		avviso = frappe.get_all(
			"CRM Notification", {"to_user": MANAGER, "type": "Phone"}, ["sentence", "notification_type_doc"]
		)
		self.assertEqual(avviso, [{"sentence": N.NUMERO_APPROVATO, "notification_type_doc": richiesta.name}])
		# asked again, nothing moves and nobody is told twice
		self.assertEqual(self.approva(esito["request"]), [])
		self.assertEqual(frappe.db.count("CRM Notification", {"type": "Phone"}), 1)

	def test_rifiutata_dice_dove_ha_scritto_twilio(self):
		esito = self.manda()
		self.approva(esito["request"], "twilio-rejected")
		(riga,) = numeri.richieste()
		self.assertEqual(riga["status"], R.RIFIUTATA)
		self.assertEqual(riga["failures"], ["Twilio wrote why to info@aurora.example."])
		self.assertTrue(riga["may_resend"])
		# the files stay, to send them again
		self.assertTrue(frappe.get_all("File", {"attached_to_doctype": RICHIESTA}))
		self.assertEqual(
			frappe.db.get_value("CRM Notification", {"type": "Phone"}, "sentence"), N.NUMERO_RIFIUTATO
		)

	def test_ancora_in_verifica_niente(self):
		esito = self.manda()
		self.assertEqual(self.approva(esito["request"], "in-review"), [])
		self.assertFalse(frappe.db.count("CRM Notification", {"type": "Phone"}))


class IlNumero(NumeriCase):
	def test_quelli_che_twilio_ha(self):
		trovati = numeri.search_numbers("mobile")["numbers"]
		self.assertEqual(
			[n["phone_number"] for n in trovati], ["+393331234567", "+393337654321", "+393401112233"]
		)
		self.assertEqual(trovati[0]["label"], "+39 333 123 4567")
		milano = numeri.search_numbers("local", "02")["numbers"]
		self.assertEqual([n["phone_number"] for n in milano], ["+390212345678", "+390287654321"])
		self.assertEqual(milano[0]["locality"], "Milano")
		self.assertEqual(
			[n["phone_number"] for n in numeri.search_numbers("local", "+39 06")["numbers"]],
			["+390612345678"],
		)
		with self.assertRaises(frappe.ValidationError):
			numeri.search_numbers("local")

	def test_si_compra_solo_con_i_documenti_approvati(self):
		esito = self.manda()
		with self.assertRaises(frappe.ValidationError):
			numeri.buy_number(esito["request"], "+393331234567")

	def test_comprato_risponde_su_dottorcloud(self):
		esito = self.manda()
		self.approva(esito["request"])
		comprato = numeri.buy_number(esito["request"], "+393331234567")
		self.assertEqual(comprato["phone_number"], "+393331234567")
		spazio = frappe.db.get_single_value(collegamento.IMPOSTAZIONI, "space_sid")
		(numero,) = self.mondo.numeri[spazio]
		self.assertTrue(numero.voice_url.endswith(VOCE))
		self.assertTrue(numero.sms_url.endswith(SMS))
		self.assertEqual(numero.bundle_sid, self.pacchetto(esito["request"]).sid)
		self.assertEqual(numero.address_sid, frappe.db.get_value(RICHIESTA, esito["request"], "address_sid"))
		# among the numbers, reaching DottorCloud
		self.assertEqual(frappe.db.get_value("CRM Caller ID", "+393331234567", "routes_to_crm"), 1)
		(riga,) = numeri.richieste()
		self.assertEqual(riga["numbers"], [{"number": "+393331234567", "label": "+39 333 123 4567"}])

	def test_non_di_un_altro_tipo(self):
		esito = self.manda()
		self.approva(esito["request"])
		with self.assertRaises(frappe.ValidationError):
			numeri.buy_number(esito["request"], "+390212345678")

	def test_il_secondo_subito_con_gli_stessi_documenti(self):
		esito = self.manda()
		self.approva(esito["request"])
		numeri.buy_number(esito["request"], "+393331234567")
		self.assertEqual(numeri.get_number_requirements("mobile")["approved"], esito["request"])
		numeri.buy_number(esito["request"], "+393337654321")
		(riga,) = numeri.richieste()
		self.assertEqual([n["number"] for n in riga["numbers"]], ["+393331234567", "+393337654321"])
		# a professional's documents are others
		self.assertIsNone(numeri.get_number_requirements("mobile", "individual")["approved"])

	def test_un_geografico_della_sua_zona(self):
		esito = self.manda("local", "02")
		self.approva(esito["request"])
		with self.assertRaises(frappe.ValidationError):
			numeri.buy_number(esito["request"], "+390612345678")
		numeri.buy_number(esito["request"], "+390212345678")
		self.assertEqual(numeri.get_number_requirements("local", None, "02")["approved"], esito["request"])
		self.assertIsNone(numeri.get_number_requirements("local", None, "06")["approved"])

	def test_si_rilascia_dallo_spazio(self):
		esito = self.manda()
		self.approva(esito["request"])
		numeri.buy_number(esito["request"], "+393331234567")
		numeri.release_number("+393331234567")
		spazio = frappe.db.get_single_value(collegamento.IMPOSTAZIONI, "space_sid")
		self.assertEqual(self.mondo.numeri[spazio], [])
		self.assertEqual(frappe.db.get_value("CRM Caller ID", "+393331234567", "enabled"), 0)

	def test_non_da_un_account_collegato_a_mano(self):
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, "account_owner", "")
		with self.assertRaises(frappe.ValidationError):
			numeri.release_number("+393331234567")
