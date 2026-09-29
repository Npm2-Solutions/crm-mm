# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Forms filled away from the operator's screen: a link at home, the desk's tablet.

The link says nothing of the forms until the code; the code goes where the link
went and is tied to it; the tablet's page opens once, in the browser it was
handed over on. Signed there, a form is the same as one signed at the desk: the
same checks, the same evidence, and nobody from the centre as its author. A form
the person cannot sign alone is filled away and signed at the desk.
"""

import json
from unittest import mock

import frappe
from frappe.utils import add_to_date, now_datetime

from crm.moduli import compilazioni, modelli, richieste, traccia
from crm.moduli.tests.test_compilazioni import DESK, OTHER, PRIVACY, SALES, CompilazioniCase, tratto
from crm.persone import collegate, legami

LINK = "link-" + "a" * 27
LINK_2 = "link-" + "b" * 27
SESSIONE = "sessione-" + "c" * 23


class RichiesteCase(CompilazioniCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_value("CRM Lead", self.giulia.name, "email", "giulia.modulo@example.com")
		self.giulia.reload()
		# the centre's outgoing email: the links and the codes are queued on it
		frappe.local.outgoing_email_account = {}
		posta = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Centro Moduli",
				"email_id": "centro.moduli@example.com",
				"enable_outgoing": 1,
				"default_outgoing": 1,
			}
		)
		posta.flags.ignore_mandatory = True
		posta.flags.ignore_validate = True
		posta.insert(ignore_permissions=True)
		# a bench without built assets has no map of them; the mail's styles are not the point
		stili = mock.patch("frappe.utils.get_assets_json", return_value={})
		stili.start()
		self.addCleanup(stili.stop)

	def tearDown(self):
		super().tearDown()
		frappe.local.outgoing_email_account = {}

	def manda(self, modelli=None, lead=None, token=LINK):
		self.come(DESK)
		with mock.patch.object(richieste, "_segreto", return_value=token):
			fatto = richieste.send_form_link(lead or self.giulia.name, json.dumps(modelli or [self.privacy]))
		frappe.set_user("Guest")
		return fatto

	def entra(self, token=LINK, codice="123456"):
		"""As the person: open the link, ask the code, type it. Returns the session."""
		frappe.set_user("Guest")
		richieste.open_request(token)
		with mock.patch.object(richieste, "_codice", return_value=codice):
			richieste.send_code(token)
		with mock.patch.object(richieste, "_segreto", return_value=SESSIONE + token[-1]):
			return richieste.verify_code(token, codice)["session"]

	def risposte(self):
		return json.dumps({"read": True, "marketing": True, "weight": "61"})


class IlLinkACasa(RichiesteCase):
	def test_il_messaggio_non_dice_quale_modulo(self):
		fatto = self.manda()
		frappe.set_user("Administrator")
		[riga] = fatto["requests"]
		self.assertEqual((riga["channel"], riga["status"]), ("Link", "Sent"))
		self.assertTrue(riga["sent_to"].startswith("g") and "@example.com" in riga["sent_to"])
		self.assertNotIn("url", fatto)
		posta = frappe.get_last_doc("Email Queue", filters={"reference_name": riga["name"]})
		self.assertIn("giulia.modulo@example.com", [r.recipient for r in posta.recipients])
		self.assertNotIn("Privacy", posta.message)
		# only the hash of the link is kept
		self.assertEqual(
			frappe.db.get_value(richieste.RICHIESTA, riga["name"], "token_hash"), richieste._impronta(LINK)
		)
		self.assertNotIn(
			LINK, json.dumps(frappe.get_doc(richieste.RICHIESTA, riga["name"]).as_dict(), default=str)
		)

	def test_col_codice_si_apre_si_compila_e_si_firma(self):
		[riga] = self.manda()["requests"]
		vista = richieste.open_request(LINK)
		# before the code, not a word about the forms
		self.assertTrue(vista["needs_code"])
		self.assertNotIn("forms", vista)
		with self.assertRaises(frappe.PermissionError):
			richieste.get_request_forms(LINK)

		sessione = self.entra()
		elenco = richieste.get_request_forms(LINK, session=sessione)
		self.assertEqual(
			[(f["id"], f["title"], f["status"]) for f in elenco["forms"]],
			[(riga["name"], "Privacy", "Opened")],
		)
		self.assertEqual(elenco["person"], "Giulia")
		modulo = richieste.get_request_form(LINK, riga["name"], session=sessione)
		self.assertEqual(modulo["answers"], {})
		salvate = richieste.save_request_answers(
			LINK, riga["name"], json.dumps({"weight": "61"}), session=sessione
		)
		self.assertEqual(salvate["answers"], {"weight": 61})
		# the same link opens them again where they were left
		self.assertEqual(
			richieste.get_request_form(LINK, riga["name"], session=sessione)["answers"], {"weight": 61}
		)

		esito = richieste.sign_request(
			LINK, riga["name"], self.risposte(), json.dumps({"sign": tratto()}), session=sessione
		)
		self.assertEqual((esito["signed"], esito["done"]), (True, True))

		frappe.set_user("Administrator")
		richiesta = frappe.get_doc(richieste.RICHIESTA, riga["name"])
		doc = frappe.get_doc(compilazioni.MODULO, richiesta.form)
		self.assertEqual((richiesta.status, doc.docstatus, doc.channel), ("Signed", 1, "Link"))
		# the person filled it: nobody from the centre is its author
		self.assertIsNone(doc.filled_by)
		self.assertEqual(doc.request, richiesta.name)
		[firma] = doc.signatures
		self.assertEqual(
			(firma.signer, firma.signer_lead, firma.method), ("patient", self.giulia.name, "Drawn")
		)
		self.assertTrue(doc.pdf_file)
		self.assertEqual(
			frappe.db.get_value(
				"CRM Consent", {"lead": self.giulia.name, "consent_type": "marketing"}, "channel"
			),
			"Web form",
		)
		eventi = [e.event for e in traccia.eventi(richieste.RICHIESTA, richiesta.name)]
		self.assertEqual(eventi, ["sent", "opened", "code_sent", "code_verified", "signed"])
		self.assertTrue(traccia.verifica_catena(richieste.RICHIESTA, richiesta.name)["integra"])

	def test_la_copia_firmata_si_scarica_nella_sessione(self):
		[riga] = self.manda()["requests"]
		sessione = self.entra()
		richieste.sign_request(
			LINK, riga["name"], self.risposte(), json.dumps({"sign": tratto()}), session=sessione
		)
		richieste.signed_copy(LINK, riga["name"], session=sessione)
		self.assertTrue(frappe.local.response.filecontent.startswith(b"%PDF"))
		with self.assertRaises(frappe.PermissionError):
			richieste.signed_copy(LINK, riga["name"], session="another-session-altogether")

	def test_il_codice_sbagliato_si_prova_poche_volte(self):
		self.manda()
		frappe.set_user("Guest")
		with mock.patch.object(richieste, "_codice", return_value="123456"):
			richieste.send_code(LINK)
		for _volta in range(richieste.TENTATIVI_CODICE):
			with self.assertRaises(frappe.ValidationError):
				richieste.verify_code(LINK, "000000")
		# now even the right one is refused: a new code is needed
		with self.assertRaises(frappe.ValidationError):
			richieste.verify_code(LINK, "123456")
		frappe.set_user("Administrator")
		capo = frappe.get_doc(richieste.RICHIESTA, {"token_hash": richieste._impronta(LINK)})
		self.assertEqual(capo.code_attempts, richieste.TENTATIVI_CODICE)
		self.assertNotEqual(capo.code_hash, richieste._impronta("123456"))

	def test_un_codice_apre_solo_il_suo_link(self):
		self.manda(token=LINK)
		self.manda(token=LINK_2)
		frappe.set_user("Guest")
		with mock.patch.object(richieste, "_codice", return_value="111111"):
			richieste.send_code(LINK)
		with self.assertRaises(frappe.ValidationError):
			richieste.verify_code(LINK_2, "111111")

	def test_una_sessione_apre_solo_i_moduli_del_suo_link(self):
		[primo] = self.manda(token=LINK)["requests"]
		[secondo] = self.manda(token=LINK_2)["requests"]
		sessione = self.entra(LINK)
		with self.assertRaises(frappe.PermissionError):
			richieste.get_request_form(LINK, secondo["name"], session=sessione)
		with self.assertRaises(frappe.PermissionError):
			richieste.get_request_forms(LINK_2, session=sessione)
		self.assertEqual(
			richieste.get_request_form(LINK, primo["name"], session=sessione)["id"], primo["name"]
		)

	def test_un_link_scaduto_o_ritirato_non_apre(self):
		[riga] = self.manda()["requests"]
		frappe.set_user("Administrator")
		frappe.db.set_value(
			richieste.RICHIESTA, riga["name"], "expires_on", add_to_date(now_datetime(), hours=-1)
		)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			richieste.open_request(LINK)
		self.assertEqual(frappe.db.get_value(richieste.RICHIESTA, riga["name"], "status"), "Expired")

		[riga] = self.manda(token=LINK_2)["requests"]
		self.come(DESK)
		richieste.cancel_request(riga["name"])
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			richieste.open_request(LINK_2)

	def test_un_indirizzo_inventato_non_dice_niente(self):
		frappe.set_user("Guest")
		for inventato in (None, "", "corto", "x" * 40, "y" * 500):
			with self.assertRaises(frappe.PermissionError):
				richieste.open_request(inventato)

	def test_senza_email_non_parte(self):
		frappe.db.set_value("CRM Lead", self.giulia.name, "email", None)
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			richieste.send_form_link(self.giulia.name, json.dumps([self.privacy]))
		self.assertFalse(frappe.db.exists(richieste.RICHIESTA, {"lead": self.giulia.name}))


class PiuModuliUnLink(RichiesteCase):
	def test_un_link_per_piu_moduli(self):
		altro = self.pubblica(PRIVACY, "Questionario")
		righe = self.manda([self.privacy, altro, self.privacy])["requests"]
		# the same form twice is one form
		self.assertEqual([r["title"] for r in righe], ["Privacy", "Questionario"])
		self.assertEqual(righe[1]["via"], righe[0]["name"])
		sessione = self.entra()
		elenco = richieste.get_request_forms(LINK, session=sessione)
		self.assertEqual([f["title"] for f in elenco["forms"]], ["Privacy", "Questionario"])
		esito = richieste.sign_request(
			LINK, righe[1]["name"], self.risposte(), json.dumps({"sign": tratto()}), session=sessione
		)
		self.assertFalse(esito["done"])
		stati = {f["id"]: f["status"] for f in richieste.get_request_forms(LINK, session=sessione)["forms"]}
		self.assertEqual(stati, {righe[0]["name"]: "Opened", righe[1]["name"]: "Signed"})
		# withdrawn one by one, the link still opens the other
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			richieste.cancel_request(righe[1]["name"])
		richieste.cancel_request(righe[0]["name"])
		frappe.set_user("Guest")
		self.assertTrue(richieste.open_request(LINK)["done"])


class IlTablet(RichiesteCase):
	def consegna(self, **altro):
		self.come(DESK)
		with mock.patch.object(richieste, "_segreto", return_value=LINK):
			fatto = richieste.hand_over_tablet(self.giulia.name, json.dumps([self.privacy]), **altro)
		frappe.set_user("Guest")
		return fatto

	def test_si_apre_una_volta_senza_codice(self):
		fatto = self.consegna()
		self.assertTrue(fatto["url"].endswith("/modulo/" + LINK))
		[riga] = fatto["requests"]
		with mock.patch.object(richieste, "_segreto", return_value=SESSIONE):
			vista = richieste.open_request(LINK)
		self.assertFalse(vista["needs_code"])
		self.assertEqual(vista["session"], SESSIONE)
		# the same address, opened again elsewhere, gets no session
		self.assertNotIn("session", richieste.open_request(LINK))
		with self.assertRaises(frappe.PermissionError):
			richieste.get_request_forms(LINK)
		with self.assertRaises(frappe.ValidationError):
			richieste.send_code(LINK)

		esito = richieste.sign_request(
			LINK, riga["name"], self.risposte(), json.dumps({"sign": tratto()}), session=SESSIONE
		)
		self.assertTrue(esito["done"])
		# the last form signed, the tablet shows nothing more
		with self.assertRaises(frappe.PermissionError):
			richieste.get_request_forms(LINK, session=SESSIONE)
		frappe.set_user("Administrator")
		doc = frappe.get_doc(compilazioni.MODULO, {"request": riga["name"]})
		self.assertEqual((doc.docstatus, doc.channel, doc.filled_by), (1, "Tablet", None))
		self.assertEqual(
			frappe.db.get_value(
				"CRM Consent", {"lead": self.giulia.name, "consent_type": "marketing"}, "channel"
			),
			"At the desk",
		)

	def test_chi_tiene_il_tablet_per_un_minore(self):
		paola = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Paola", "last_name": "Modulo"}).insert(
			ignore_permissions=True
		)
		sconosciuta = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Estranea", "last_name": "Modulo"}
		).insert(ignore_permissions=True)
		collegate.assicura_legame(self.giulia.name, paola.name, legami.GENITORE, represents=1)
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			richieste.hand_over_tablet(
				self.giulia.name, json.dumps([self.privacy]), given_by=sconosciuta.name
			)
		[riga] = self.consegna(given_by=paola.name)["requests"]
		with mock.patch.object(richieste, "_segreto", return_value=SESSIONE):
			richieste.open_request(LINK)
		richieste.sign_request(
			LINK, riga["name"], self.risposte(), json.dumps({"sign": tratto()}), session=SESSIONE
		)
		frappe.set_user("Administrator")
		doc = frappe.get_doc(compilazioni.MODULO, {"request": riga["name"]})
		[firma] = doc.signatures
		# the parent answered, and the hand that signed is hers
		self.assertEqual(doc.given_by, paola.name)
		self.assertEqual((firma.signer, firma.signer_lead), ("guardian", paola.name))


class PerChiFirmaUnAltro(RichiesteCase):
	def test_il_link_va_a_chi_firma_per_la_persona(self):
		paola = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Paola",
				"last_name": "Modulo",
				"email": "paola@example.com",
			}
		).insert(ignore_permissions=True)
		collegate.assicura_legame(self.giulia.name, paola.name, legami.GENITORE, represents=1)
		self.come(DESK)
		opzioni = richieste.get_send_options(self.giulia.name)
		self.assertEqual(opzioni["link"]["to"], paola.lead_name)
		self.assertTrue(opzioni["link"]["for_them"])
		[riga] = self.manda()["requests"]
		frappe.set_user("Administrator")
		posta = frappe.get_last_doc("Email Queue", filters={"reference_name": riga["name"]})
		self.assertEqual([r.recipient for r in posta.recipients], ["paola@example.com"])
		self.assertEqual(frappe.db.get_value(richieste.RICHIESTA, riga["name"], "given_by"), paola.name)
		# and the code goes to her too
		sessione = self.entra()
		self.assertIn("Giulia", json.dumps(richieste.get_request_forms(LINK, session=sessione)))
		frappe.set_user("Administrator")
		codici = frappe.get_all(
			"Email Queue", filters={"reference_name": riga["name"]}, fields=["name"], order_by="creation desc"
		)
		self.assertEqual(
			[r.recipient for r in frappe.get_doc("Email Queue", codici[0].name).recipients],
			["paola@example.com"],
		)

	def test_nessuno_con_una_email(self):
		paola = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Paola", "last_name": "Modulo"}).insert(
			ignore_permissions=True
		)
		collegate.assicura_legame(self.giulia.name, paola.name, legami.GENITORE, represents=1)
		self.come(DESK)
		self.assertTrue(richieste.get_send_options(self.giulia.name)["link"]["reason"])
		# her own email is not where a form she does not sign for herself goes
		with self.assertRaises(frappe.ValidationError):
			richieste.send_form_link(self.giulia.name, json.dumps([self.privacy]))


OPERATORE = {
	"sections": [
		{
			"id": "consenso",
			"title": "Consenso",
			"fields": [
				{"id": "capito", "type": "yesno", "label": "Ho capito", "required": True},
				{"id": "paziente", "type": "signature", "label": "Paziente", "required": True},
				{
					"id": "medico",
					"type": "signature",
					"label": "Medico",
					"signer": "operator",
					"required": True,
				},
			],
		}
	]
}


class SiFirmaAlBanco(RichiesteCase):
	def test_si_compila_a_casa_e_si_firma_al_banco(self):
		consenso = self.pubblica(OPERATORE, "Consenso con il medico")
		self.come(DESK)
		scelte = {m["name"]: m for m in richieste.get_send_options(self.giulia.name)["templates"]}
		self.assertTrue(scelte[consenso]["sign_at_desk"])
		self.assertFalse(scelte[self.privacy]["sign_at_desk"])
		[riga] = self.manda([consenso])["requests"]
		sessione = self.entra()
		self.assertTrue(richieste.get_request_form(LINK, riga["name"], session=sessione)["sign_at_desk"])
		with self.assertRaises(frappe.ValidationError):
			richieste.sign_request(
				LINK,
				riga["name"],
				json.dumps({"capito": True}),
				json.dumps({"paziente": tratto()}),
				session=sessione,
			)
		# the answers are checked all the same, the signatures are left for the desk
		with self.assertRaises(frappe.ValidationError):
			richieste.finish_request(LINK, riga["name"], json.dumps({}), session=sessione)
		self.assertTrue(
			richieste.finish_request(LINK, riga["name"], json.dumps({"capito": True}), session=sessione)[
				"done"
			]
		)
		with self.assertRaises(frappe.ValidationError):
			richieste.save_request_answers(
				LINK, riga["name"], json.dumps({"capito": False}), session=sessione
			)

		self.come(DESK)
		nome = frappe.db.get_value(richieste.RICHIESTA, riga["name"], "form")
		self.assertEqual(compilazioni.get_form(nome)["answers"], {"capito": True})
		firmato = compilazioni.sign_form(
			nome, json.dumps({"capito": True}), json.dumps({"paziente": tratto(), "medico": tratto()})
		)
		self.assertEqual(firmato["docstatus"], 1)
		self.assertEqual(frappe.db.get_value(richieste.RICHIESTA, riga["name"], "status"), "Signed")

	def test_la_firma_dell_operatore_non_si_da_da_soli(self):
		consenso = self.pubblica(OPERATORE, "Consenso con il medico")
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, consenso)["name"]
		doc = frappe.get_doc(compilazioni.MODULO, nome)
		with self.assertRaises(frappe.ValidationError):
			compilazioni.firma(
				doc, {"capito": True}, {"paziente": tratto(), "medico": tratto()}, da_solo=True
			)

	def test_scartata_la_bozza_il_link_non_la_riapre(self):
		[riga] = self.manda()["requests"]
		sessione = self.entra()
		richieste.get_request_form(LINK, riga["name"], session=sessione)
		self.come(DESK)
		compilazioni.discard_form(frappe.db.get_value(richieste.RICHIESTA, riga["name"], "form"))
		self.assertEqual(frappe.db.get_value(richieste.RICHIESTA, riga["name"], "status"), "Cancelled")
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			richieste.open_request(LINK)


class ChiVedeLeRichieste(RichiesteCase):
	def test_seguono_la_persona(self):
		[riga] = self.manda()["requests"]
		self.come(SALES)
		self.assertEqual([r["name"] for r in richieste.get_requests(self.giulia.name)], [riga["name"]])
		self.come(OTHER)
		with self.assertRaises(frappe.PermissionError):
			richieste.get_requests(self.giulia.name)
		self.assertNotIn(riga["name"], frappe.get_list(richieste.RICHIESTA, pluck="name"))
		with self.assertRaises(frappe.PermissionError):
			richieste.cancel_request(riga["name"])

	def test_i_moduli_sanitari_non_si_mandano_senza_la_cura(self):
		clinico = self.pubblica(PRIVACY, "Anamnesi")
		# marked by hand: here the clinic, which gives the mark, is off
		frappe.db.set_value(modelli.MODELLO, clinico, "clinical", 1)
		frappe.db.set_value(
			modelli.VERSIONE, frappe.db.get_value(modelli.MODELLO, clinico, "current_version"), "clinical", 1
		)
		self.come(DESK)
		self.assertNotIn(
			clinico, [m["name"] for m in richieste.get_send_options(self.giulia.name)["templates"]]
		)
		with self.assertRaises(frappe.PermissionError):
			richieste.send_form_link(self.giulia.name, json.dumps([clinico]))
