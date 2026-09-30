# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's documents on a site without the clinic: a gym's contract, a beauty
centre's signed consent.

The desk adds Anna's contract. It is read by whoever reads documents and sees her
(the manager, the trainer who follows her), never by sales, and the lists follow
the same rule. The kinds are the CRM's own: without the clinic there is no report
or test result, and nothing is health data, so nothing goes in the access log. A
document is put right, never given another file. Added by mistake, it goes the
same day by whoever added it; the next day only the manager takes it away, and the
audit log keeps why.

Given by hand, the delivery says to whom. Online, it stays for the days chosen:
30 unless said, never more than 90. The link goes to /documento with a code given
another way. A module may keep a kind offline, or for fewer days. In her area
Anna finds the document and downloads it after a code.
"""

import hashlib
from unittest import mock

import frappe
from frappe.utils import add_days, getdate, now_datetime, nowdate

from crm.area.tests.test_area import ANNA, DESK, MANAGER, OPERATORE, SALES, AreaCase
from crm.documenti import api as documenti
from crm.documenti import area, consegna
from crm.documenti import regole as R
from crm.moduli import traccia

LINK = "link-del-documento"


class DocumentiCase(AreaCase):
	def carica(self, user=DESK, contenuto="Contratto annuale firmato", nome="contratto.txt", privato=1):
		"""A file the user uploads, attached to nothing yet: what the dialog does first."""
		self.come(user)
		return frappe.get_doc(
			{"doctype": "File", "file_name": nome, "is_private": privato, "content": contenuto}
		).insert()

	def aggiunge(self, user=DESK, **campi):
		allegato = self.carica(user, contenuto=campi.pop("contenuto", f"Contratto di {user}"))
		campi.setdefault("title", "Contratto annuale")
		campi.setdefault("document_type", R.CONTRATTO)
		return documenti.add_document(self.anna.name, allegato.name, **campi)

	def vede(self, user, nome):
		self.come(user)
		return nome in [d["name"] for d in documenti.get_documents(self.anna.name)["documents"]]

	def online(self, documento, user=DESK, **altro):
		self.come(user)
		with mock.patch.object(consegna, "_segreto", return_value=LINK):
			return consegna.deliver_online(documento, **altro)


class LAggiunta(DocumentiCase):
	def test_la_segreteria_aggiunge_un_contratto(self):
		allegato = self.carica(contenuto="Contratto annuale firmato")
		riga = documenti.add_document(
			self.anna.name,
			allegato.name,
			title="Contratto annuale",
			document_type=R.CONTRATTO,
			document_date="2026-09-20",
			source="Firmato in sede",
		)
		self.assertEqual((riga["added_by"], riga["practitioner"], riga["clinical"]), (DESK, None, 0))
		self.assertEqual(riga["file_hash"], hashlib.sha256(b"Contratto annuale firmato").hexdigest())
		self.assertTrue(riga["file"].startswith("/private/"))
		frappe.set_user("Administrator")
		self.assertEqual(
			frappe.db.get_value("File", allegato.name, ["attached_to_doctype", "attached_to_name"]),
			(documenti.DOCTYPE, riga["name"]),
		)

	def test_lo_legge_chi_legge_i_documenti_e_vede_la_persona(self):
		riga = self.aggiunge()
		for user in (DESK, MANAGER, OPERATORE):
			self.assertTrue(self.vede(user, riga["name"]), user)
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			documenti.get_documents(self.anna.name)
		self.assertFalse(frappe.has_permission(documenti.DOCTYPE, "read", doc=riga["name"]))
		# the lists follow the same rule
		self.assertEqual(frappe.get_list(documenti.DOCTYPE, pluck="name"), [])
		self.come(MANAGER)
		self.assertEqual(frappe.get_list(documenti.DOCTYPE, pluck="name"), [riga["name"]])
		# not health data: no access log
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("View Log", {"reference_name": riga["name"]}))

	def test_un_file_pubblico_o_di_altri_no(self):
		pubblico = self.carica(privato=0)
		with self.assertRaises(frappe.ValidationError):
			documenti.add_document(
				self.anna.name, pubblico.name, title="Contratto", document_type=R.CONTRATTO
			)
		altrui = self.carica(MANAGER)
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			documenti.add_document(self.anna.name, altrui.name, title="Contratto", document_type=R.CONTRATTO)

	def test_chi_non_aggiunge_non_aggiunge(self):
		allegato = self.carica(SALES)
		with self.assertRaises(frappe.PermissionError):
			documenti.add_document(
				self.anna.name, allegato.name, title="Contratto", document_type=R.CONTRATTO
			)


class ITipiDelCrm(DocumentiCase):
	def test_senza_la_clinica_nessun_referto(self):
		self.come(DESK)
		scelte = documenti.get_choices()
		self.assertEqual(
			[tipo["value"] for tipo in scelte["types"]],
			[R.MODULO_FIRMATO, R.CONTRATTO, R.CERTIFICATO, R.IDENTITA, R.FOTO, R.ALTRO],
		)
		self.assertFalse(any(tipo["clinical"] for tipo in scelte["types"]))
		for clinico in ("Test result", "Report", "Inventato"):
			with self.assertRaises(frappe.ValidationError, msg=clinico):
				self.aggiunge(document_type=clinico)

	def test_per_chi_segue_la_persona(self):
		frappe.set_user("Administrator")
		frappe.get_doc(
			{
				"doctype": "CRM Service Provider",
				"provider_name": "Trainer Area",
				"qualification": "formatore",
				"user": OPERATORE,
			}
		).insert(ignore_permissions=True)
		self.come(DESK)
		self.assertIn(OPERATORE, [p["value"] for p in documenti.get_choices()["practitioners"]])
		riga = self.aggiunge(
			title="Certificato sportivo", document_type=R.CERTIFICATO, practitioner=OPERATORE
		)
		self.assertEqual((riga["practitioner"], riga["clinical"]), (OPERATORE, 0))
		# somebody who provides none of the centre's services is nobody's "for"
		with self.assertRaises(frappe.ValidationError):
			self.aggiunge(practitioner=SALES)


class CorrettoOTolto(DocumentiCase):
	def test_si_corregge_e_il_file_resta(self):
		riga = self.aggiunge()
		self.come(DESK)
		corretto = documenti.update_document(
			riga["name"], title="Contratto semestrale", document_type=R.ALTRO
		)
		self.assertEqual((corretto["title"], corretto["document_type"]), ("Contratto semestrale", R.ALTRO))
		self.assertEqual(corretto["file"], riga["file"])
		altro = self.carica(contenuto="Un altro contratto")
		frappe.set_user("Administrator")
		doc = frappe.get_doc(documenti.DOCTYPE, riga["name"])
		doc.file = altro.file_url
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		# who did not add it does not put it right
		self.come(MANAGER)
		with self.assertRaises(frappe.PermissionError):
			documenti.update_document(riga["name"], title="Altro", document_type=R.ALTRO)

	def test_tolto_lo_stesso_giorno_da_chi_lo_ha_aggiunto(self):
		riga = self.aggiunge()
		self.come(OPERATORE)
		with self.assertRaises(frappe.PermissionError):
			documenti.remove_document(riga["name"], "Non è suo")
		self.come(DESK)
		with self.assertRaises(frappe.ValidationError):
			documenti.remove_document(riga["name"], " ")
		documenti.remove_document(riga["name"], "Di un'altra persona")
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists(documenti.DOCTYPE, riga["name"]))
		[evento] = traccia.eventi(documenti.DOCTYPE, riga["name"])
		self.assertEqual((evento.event, evento.detail), ("removed", "Di un'altra persona"))

	def test_il_giorno_dopo_solo_il_manager(self):
		riga = self.aggiunge()
		frappe.set_user("Administrator")
		frappe.db.set_value(documenti.DOCTYPE, riga["name"], "added_on", add_days(now_datetime(), -1))
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			documenti.remove_document(riga["name"], "Doppio")
		self.come(MANAGER)
		documenti.remove_document(riga["name"], "Doppio")
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists(documenti.DOCTYPE, riga["name"]))


class LaConsegna(DocumentiCase):
	def setUp(self):
		super().setUp()
		self.documento = self.aggiunge(contenuto="Contratto di Anna")["name"]

	def apri(self, codice):
		frappe.set_user("Guest")
		return consegna.open_document(LINK, codice)

	def test_a_mano_dice_a_chi(self):
		self.come(DESK)
		fatto = consegna.deliver_by_hand(self.documento)
		[riga] = fatto["deliveries"]
		self.assertEqual(
			(riga["channel"], riga["status"], riga["delivered_to"]),
			(consegna.A_MANO, consegna.CONSEGNATO, "Anna Area"),
		)
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			consegna.deliver_by_hand(self.documento)

	def test_online_trenta_giorni_se_non_si_dice(self):
		self.come(DESK)
		stato = consegna.get_deliveries(self.documento)
		self.assertEqual(stato["online"], {"reason": None, "days": 30, "max_days": 90})
		self.assertEqual(stato["email"], ANNA)
		fatto = self.online(self.documento, send_email=0)
		self.assertEqual(getdate(fatto["expires_on"]), getdate(add_days(nowdate(), 30)))
		# a new code takes the place of the old one; never more than 90 days
		fatto = self.online(self.documento, send_email=0, days=365)
		self.assertEqual(getdate(fatto["expires_on"]), getdate(add_days(nowdate(), 90)))
		stati = [riga["status"] for riga in consegna.consegne(self.documento)]
		self.assertEqual(sorted(stati), [consegna.DISPONIBILE, consegna.RITIRATO])

	def test_il_link_per_email_il_codice_a_voce(self):
		fatto = self.online(self.documento)
		self.assertTrue(fatto["link"].endswith(f"/documento/{LINK}"))
		self.assertEqual((len(fatto["code"]), fatto["email"]), (6, ANNA))
		frappe.set_user("Administrator")
		[posta] = frappe.get_all("Email Queue", fields=["message"], order_by="creation desc", limit=1)
		self.assertIn(f"/documento/{LINK}", posta.message)
		self.assertNotIn(fatto["code"], posta.message)
		self.assertNotIn("Contratto annuale", posta.message)
		sbagliato = "000000" if fatto["code"] != "000000" else "111111"
		with self.assertRaises(frappe.ValidationError):
			self.apri(sbagliato)
		aperto = self.apri(fatto["code"])
		self.assertEqual(aperto["title"], "Contratto annuale")
		consegna.download_document(LINK, aperto["session"])
		self.assertEqual(frappe.local.response.filecontent, b"Contratto di Anna")
		frappe.set_user("Administrator")
		nome = frappe.db.get_value(consegna.CONSEGNA, {"document": self.documento}, "name")
		eventi = [e.event for e in traccia.eventi(consegna.CONSEGNA, nome)]
		self.assertEqual(eventi, ["online", "code_wrong", "opened", "downloaded"])

	def test_una_regola_del_modulo(self):
		regola = consegna.Regola(
			ferma=lambda doc: "A contract stays at the centre" if doc.document_type == R.CONTRATTO else None,
			giorni=lambda doc: 7,
		)
		with mock.patch.object(consegna, "_regole", [regola]):
			self.come(DESK)
			stato = consegna.get_deliveries(self.documento)
			self.assertEqual(
				stato["online"], {"reason": "A contract stays at the centre", "days": 7, "max_days": 7}
			)
			with self.assertRaises(frappe.ValidationError):
				self.online(self.documento, send_email=0)
			self.come(DESK)
			documenti.update_document(self.documento, title="Certificato", document_type=R.CERTIFICATO)
			fatto = self.online(self.documento, send_email=0, days=30)
			self.assertEqual(getdate(fatto["expires_on"]), getdate(add_days(nowdate(), 7)))


class NellArea(DocumentiCase):
	def test_il_documento_dato_online_dopo_un_codice(self):
		documento = self.aggiunge(contenuto="Contratto di Anna")["name"]
		self.invita()
		self.entra()
		from crm.area import api

		[persona] = api.get_me()["people"]
		self.assertFalse(persona["sections"]["documents"])
		self.online(documento, send_email=0)
		self.entra()
		[persona] = api.get_me()["people"]
		self.assertTrue(persona["sections"]["documents"])
		[voce] = area.get_documents(self.anna.name)["documents"]
		self.assertEqual((voce["title"], voce["document_type"]), ("Contratto annuale", R.CONTRATTO))
		area.download_document(self.anna.name, voce["name"])
		self.assertEqual(frappe.local.response.filecontent, b"Contratto di Anna")
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(consegna.CONSEGNA, voce["name"], "status"), consegna.SCARICATO)
