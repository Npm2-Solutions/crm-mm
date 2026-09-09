# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Invoicing, end to end on a real site.

The engine is tested on its own in `crm/invoicing/tests`. What is checked here is
the part that only exists once there is a database: the number assigned inside the
transaction, the guard answering 403 through the API, the XML that ends up
attached to the record, and the refusal to cancel a document that has already left
the building.
"""

import frappe
from frappe.tests import IntegrationTestCase

from crm.invoicing import api
from crm.invoicing.engine import ricevute
from crm.invoicing.install import semina_qualifiche
from crm.invoicing.sdi import ricezione

CF_PAZIENTE = "RSSMRA80A01H501U"
CF_TITOLARE = "BNCLCU75B41F205Z"
PIVA = "00743110157"


class InvoicingBase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		semina_qualifiche()
		cls.azienda = cls.crea_azienda()
		cls.psicologo = cls.crea_erogatore("Dott.ssa Bianchi", "psicologo")
		cls.osteopata = cls.crea_erogatore("Dott. Verdi", "osteopata")
		cls.consulente = cls.crea_erogatore("Studio Neri", "societa_servizi")
		cls.seduta = cls.crea_servizio("Seduta di psicoterapia", healthcare=True, exempt=True)
		cls.trattamento = cls.crea_servizio("Trattamento osteopatico", healthcare=True, exempt=False)
		cls.consulenza = cls.crea_servizio("Consulenza", healthcare=False, exempt=False)
		frappe.db.commit()

	@staticmethod
	def crea_azienda():
		nome = "Studio Test Fatturazione"
		if frappe.db.exists("CRM Invoicing Company", nome):
			return frappe.get_doc("CRM Invoicing Company", nome)
		return frappe.get_doc(
			{
				"doctype": "CRM Invoicing Company",
				"company_name": nome,
				"first_name": "Lucia",
				"last_name": "Bianchi",
				"tax_id": PIVA,
				"fiscal_code": CF_TITOLARE,
				"tax_regime": "RF01",
				"address_line": "Via Roma 1",
				"postal_code": "20100",
				"city": "Milano",
				"province": "MI",
				"sender_category": "professionista_sanitario",
				"fund_type": "TC21",
				"fund_rate": 2,
				"fund_mandatory": 1,
				"series_electronic": "E",
				"series_healthcare": "S",
				"number_format": "{anno}/{serie}/{numero}",
				"is_default": 1,
			}
		).insert()

	@staticmethod
	def crea_erogatore(nome, qualifica):
		if frappe.db.exists("CRM Service Provider", nome):
			return frappe.get_doc("CRM Service Provider", nome)
		return frappe.get_doc(
			{
				"doctype": "CRM Service Provider",
				"provider_name": nome,
				"qualification": qualifica,
				"enabled": 1,
			}
		).insert()

	@staticmethod
	def crea_servizio(nome, healthcare, exempt):
		if frappe.db.exists("CRM Billable Service", nome):
			return frappe.get_doc("CRM Billable Service", nome)
		return frappe.get_doc(
			{
				"doctype": "CRM Billable Service",
				"service_name": nome,
				"fiscal_description": nome,
				"is_healthcare": int(healthcare),
				"vat_exempt": int(exempt),
				"exemption_reference": "art. 10, n. 18, DPR 633/72" if exempt else None,
				"vat_rate": 0 if exempt else 22,
				"ts_expense_type": "SP" if (healthcare and exempt) else None,
				"default_rate": 100,
				"enabled": 1,
			}
		).insert()

	def fattura(self, servizio, erogatore, **kwargs):
		valori = {
			"doctype": "CRM Invoice",
			"company": self.azienda.name,
			"recipient_type": "persona_fisica",
			"billing_name": "Mario Rossi",
			"first_name": "Mario",
			"last_name": "Rossi",
			"fiscal_code": CF_PAZIENTE,
			"address_line": "Via Verdi 3",
			"postal_code": "00100",
			"city": "Roma",
			"province": "RM",
			"payment_method": "MP08",
			"items": [{"billable_service": servizio, "service_provider": erogatore, "qty": 1, "rate": 100}],
		}
		valori.update(kwargs)
		return frappe.get_doc(valori).insert()

	def tearDown(self):
		frappe.db.rollback()


class EmissioneTest(InvoicingBase):
	def test_una_seduta_esce_dal_canale_sdi_e_va_al_sistema_ts(self):
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		self.assertEqual(documento.channel, "pdf_ts")
		documento.submit()
		self.assertTrue(documento.document_number)
		self.assertEqual(documento.series, "S")
		self.assertEqual(documento.ts_status, "da_inviare")
		self.assertEqual(documento.sdi_status, "non_applicabile")
		self.assertEqual(documento.items[0].ts_expense_type, "SP")

	def test_il_contributo_enpap_entra_nel_totale(self):
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		self.assertEqual(documento.fund_contribution, 2.0)
		self.assertEqual(documento.grand_total, 102.0)
		self.assertEqual(documento.ts_total, 102.0)

	def test_l_osteopata_prende_il_canale_sdi(self):
		documento = self.fattura(self.trattamento.name, self.osteopata.name)
		self.assertEqual(documento.channel, "sdi")
		documento.submit()
		self.assertEqual(documento.series, "E")
		self.assertEqual(documento.ts_status, "non_applicabile")
		self.assertTrue(documento.xml_file)
		self.assertTrue(documento.sdi_filename.startswith(f"IT{PIVA}_"))

	def test_il_numero_si_assegna_solo_all_emissione(self):
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		self.assertFalse(documento.document_number)
		documento.submit()
		self.assertTrue(documento.document_number)

	def test_i_numeri_non_hanno_buchi(self):
		numeri = []
		for _ in range(3):
			documento = self.fattura(self.seduta.name, self.psicologo.name)
			documento.submit()
			numeri.append(documento.sequence)
		self.assertEqual(numeri, sorted(numeri))
		self.assertEqual(numeri[-1] - numeri[0], 2)

	def test_le_annotazioni_di_legge_finiscono_sul_documento(self):
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		self.assertIn("esente", documento.legal_notes.lower())
		self.assertIn("D.Lgs. 10/2026", documento.legal_notes)


class GuardiaTest(InvoicingBase):
	def test_l_api_risponde_403_sul_sanitario_verso_persona_fisica(self):
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		documento.submit()
		with self.assertRaises(frappe.PermissionError):
			api.send_to_sdi(documento.name)

	def test_il_blocco_finisce_nel_registro(self):
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		documento.submit()
		try:
			api.send_to_sdi(documento.name)
		except frappe.PermissionError:
			pass
		self.assertTrue(
			frappe.db.exists("CRM Invoice Log", {"invoice": documento.name, "event": "sdi_blocked"})
		)

	def test_l_osteopata_non_viene_bloccato(self):
		documento = self.fattura(self.trattamento.name, self.osteopata.name)
		documento.submit()
		esito = api.send_to_sdi(documento.name)
		self.assertEqual(esito["mode"], "export")

	def test_il_documento_misto_non_si_emette(self):
		documento = self.fattura(
			self.seduta.name,
			self.psicologo.name,
			items=[
				{"billable_service": self.seduta.name, "service_provider": self.psicologo.name, "rate": 100},
				{
					"billable_service": self.trattamento.name,
					"service_provider": self.osteopata.name,
					"rate": 80,
				},
			],
		)
		with self.assertRaises(frappe.ValidationError):
			documento.submit()


class ValidazioneTest(InvoicingBase):
	def test_senza_codice_fiscale_il_sistema_ts_non_puo_ricevere(self):
		documento = self.fattura(self.seduta.name, self.psicologo.name, fiscal_code=None)
		with self.assertRaises(frappe.ValidationError):
			documento.submit()

	def test_con_opposizione_il_codice_fiscale_non_serve(self):
		documento = self.fattura(
			self.seduta.name, self.psicologo.name, fiscal_code=None, privacy_opposition=1
		)
		documento.submit()
		self.assertTrue(documento.opposition_recorded_on)

	def test_un_codice_fiscale_sbagliato_si_ferma_qui(self):
		documento = self.fattura(self.seduta.name, self.psicologo.name, fiscal_code="RSSMRA80A01H501A")
		with self.assertRaises(frappe.ValidationError):
			documento.submit()

	def test_il_pagamento_anticipato_va_dichiarato(self):
		documento = self.fattura(
			self.seduta.name, self.psicologo.name, payment_date=frappe.utils.add_days(None, -30)
		)
		with self.assertRaises(frappe.ValidationError):
			documento.submit()

	def test_una_nota_di_credito_deve_dire_cosa_corregge(self):
		documento = self.fattura(self.seduta.name, self.psicologo.name, document_type="TD04")
		with self.assertRaises(frappe.ValidationError):
			documento.submit()


class AnnullamentoTest(InvoicingBase):
	def test_un_documento_gia_trasmesso_non_si_annulla(self):
		documento = self.fattura(self.trattamento.name, self.osteopata.name)
		documento.submit()
		documento.db_set("sdi_status", "consegnata", update_modified=False)
		documento.reload()
		with self.assertRaises(frappe.ValidationError):
			documento.cancel()

	def test_un_documento_non_trasmesso_si_annulla(self):
		documento = self.fattura(self.trattamento.name, self.osteopata.name)
		documento.submit()
		documento.cancel()
		self.assertEqual(documento.docstatus, 2)


class ConfigurazioneTest(InvoicingBase):
	def test_un_formato_di_numerazione_col_cancelletto_non_passa(self):
		azienda = frappe.get_doc("CRM Invoicing Company", self.azienda.name)
		azienda.number_format = "Fattura #{numero}/{anno}"
		with self.assertRaises(frappe.ValidationError):
			azienda.save()

	def test_una_struttura_senza_codice_proprietario_non_passa(self):
		azienda = frappe.get_doc("CRM Invoicing Company", self.azienda.name)
		azienda.sender_category = "struttura_autorizzata"
		with self.assertRaises(frappe.ValidationError):
			azienda.save()

	def test_il_bollo_virtuale_vuole_gli_estremi(self):
		azienda = frappe.get_doc("CRM Invoicing Company", self.azienda.name)
		azienda.stamp_duty_mode = "virtuale"
		with self.assertRaises(frappe.ValidationError):
			azienda.save()

	def test_una_qualifica_esente_deve_essere_sanitaria(self):
		qualifica = frappe.get_doc("CRM Professional Qualification", "consulente")
		qualifica.vat_exempt = 1
		with self.assertRaises(frappe.ValidationError):
			qualifica.save()

	def test_il_registro_di_serie_e_seminato(self):
		self.assertTrue(frappe.db.exists("CRM Professional Qualification", "massoterapista"))
		self.assertTrue(frappe.db.exists("CRM Professional Qualification", "avvocato"))
		massoterapista = frappe.get_doc("CRM Professional Qualification", "massoterapista")
		self.assertEqual(massoterapista.sdi_rule, "vietato")
		self.assertTrue(massoterapista.ts_required)

	def test_la_checklist_dice_cosa_manca_e_cosa_costa(self):
		voci = api.onboarding_checklist(self.azienda.name)
		self.assertTrue(all("consequence" in voce for voce in voci))


class TrasmissioneTest(InvoicingBase):
	def _emessa_sdi(self):
		documento = self.fattura(self.trattamento.name, self.osteopata.name)
		documento.submit()
		documento.reload()
		return documento

	def test_export_consegna_il_file(self):
		documento = self._emessa_sdi()
		esito = api.send_to_sdi(documento.name)
		self.assertEqual(esito["mode"], "export")
		self.assertTrue(esito["sent"])
		self.assertTrue(esito["file"])

	def test_la_pec_senza_casella_lo_dice(self):
		frappe.db.set_value("CRM Invoicing Company", self.azienda.name, "sdi_mode", "pec")
		documento = self._emessa_sdi()
		with self.assertRaises(frappe.ValidationError) as errore:
			api.send_to_sdi(documento.name)
		self.assertIn("PEC", str(errore.exception))

	def test_il_provider_senza_endpoint_lo_dice(self):
		frappe.db.set_value("CRM Invoicing Company", self.azienda.name, "sdi_mode", "provider")
		documento = self._emessa_sdi()
		with self.assertRaises(frappe.ValidationError) as errore:
			api.send_to_sdi(documento.name)
		self.assertIn("endpoint", str(errore.exception).lower())

	def test_un_canale_sconosciuto_ripiega_su_export(self):
		frappe.db.set_value("CRM Invoicing Company", self.azienda.name, "sdi_mode", "inesistente")
		documento = self._emessa_sdi()
		self.assertEqual(api.send_to_sdi(documento.name)["mode"], "export")


class RicevuteTest(InvoicingBase):
	def _emessa_sdi(self):
		documento = self.fattura(self.trattamento.name, self.osteopata.name)
		documento.submit()
		documento.reload()
		return documento

	def _ricevuta(self, documento, tipo, corpo):
		nome = documento.sdi_filename.replace(".xml", f"_{tipo}_001.xml")
		return ricezione.applica_file(corpo, nome)

	def test_la_consegna_chiude_il_documento(self):
		documento = self._emessa_sdi()
		corpo = f"""<RicevutaConsegna><IdentificativoSdI>42</IdentificativoSdI>
			<NomeFile>{documento.sdi_filename}</NomeFile></RicevutaConsegna>""".encode()
		esito = self._ricevuta(documento, "RC", corpo)
		self.assertTrue(esito["applied"])
		documento.reload()
		self.assertEqual(documento.sdi_status, "consegnata")
		self.assertEqual(documento.sdi_identifier, "42")

	def test_lo_scarto_porta_i_codici_sul_documento(self):
		documento = self._emessa_sdi()
		corpo = f"""<RicevutaScarto><NomeFile>{documento.sdi_filename}</NomeFile>
			<ListaErrori><Errore><Codice>00423</Codice>
			<Descrizione>Imponibile non congruente</Descrizione></Errore></ListaErrori>
			</RicevutaScarto>""".encode()
		self._ricevuta(documento, "NS", corpo)
		documento.reload()
		self.assertEqual(documento.sdi_status, "scartata")
		self.assertIn("00423", documento.sdi_message)

	def test_la_mancata_consegna_non_e_uno_scarto(self):
		documento = self._emessa_sdi()
		corpo = f"""<RicevutaImpossibilitaRecapito><NomeFile>{documento.sdi_filename}</NomeFile>
			</RicevutaImpossibilitaRecapito>""".encode()
		self._ricevuta(documento, "MC", corpo)
		documento.reload()
		self.assertEqual(documento.sdi_status, "mancata_consegna")
		self.assertIn("area riservata", documento.sdi_message)

	def test_la_stessa_ricevuta_non_si_applica_due_volte(self):
		documento = self._emessa_sdi()
		corpo = f"<RicevutaConsegna><NomeFile>{documento.sdi_filename}</NomeFile></RicevutaConsegna>".encode()
		self.assertTrue(self._ricevuta(documento, "RC", corpo)["applied"])
		secondo = self._ricevuta(documento, "RC", corpo)
		self.assertFalse(secondo["applied"])
		self.assertIn("Already applied", secondo["reason"])

	def test_una_ricevuta_orfana_non_rompe_nulla(self):
		corpo = b"<RicevutaConsegna><NomeFile>IT99999999999_00001.xml</NomeFile></RicevutaConsegna>"
		esito = ricezione.applica_file(corpo, "IT99999999999_00001_RC_001.xml")
		self.assertFalse(esito["applied"])
		self.assertIn("No invoice matches", esito["reason"])

	def test_un_file_che_non_e_una_ricevuta_viene_ignorato(self):
		esito = ricezione.applica_file(b"<FatturaElettronica/>", "IT01234567890_00001.xml")
		self.assertFalse(esito["applied"])

	def test_il_registro_annota_la_ricevuta(self):
		documento = self._emessa_sdi()
		corpo = f"<RicevutaConsegna><NomeFile>{documento.sdi_filename}</NomeFile></RicevutaConsegna>".encode()
		self._ricevuta(documento, "RC", corpo)
		self.assertTrue(
			frappe.db.exists("CRM Invoice Log", {"invoice": documento.name, "event": "sdi_receipt"})
		)

	def test_i_tipi_di_ricevuta_coprono_gli_stati(self):
		for tipo in ricevute.TipoRicevuta:
			self.assertIn(tipo.value, ricevute.STATO_PER_TIPO)


class PdfTest(InvoicingBase):
	def test_la_fattura_emessa_porta_il_suo_pdf(self):
		frappe.db.set_single_value("CRM Invoicing Settings", "attach_pdf", 1)
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		documento.submit()
		documento.reload()
		self.assertTrue(documento.pdf_file)
		self.assertTrue(documento.pdf_hash)
		# Whatever came out, it is recorded rather than assumed.
		self.assertTrue(documento.pdf_conformita)

	def test_il_pdf_non_si_rigenera(self):
		frappe.db.set_single_value("CRM Invoicing Settings", "attach_pdf", 1)
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		documento.submit()
		documento.reload()
		esito = api.generate_pdf(documento.name)
		self.assertTrue(esito.get("skipped"))

	def test_il_nome_del_file_non_e_parlante(self):
		frappe.db.set_single_value("CRM Invoicing Settings", "attach_pdf", 1)
		documento = self.fattura(self.seduta.name, self.psicologo.name)
		documento.submit()
		documento.reload()
		self.assertNotIn("psicoterapia", (documento.pdf_file or "").lower())
		self.assertIn("documento_", documento.pdf_file)
