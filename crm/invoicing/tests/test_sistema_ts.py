# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The Sistema TS tracciato: two schemas, and the rules that keep rows out of the
January reject pile."""

from __future__ import annotations

import zipfile
from datetime import date
from decimal import Decimal
from io import BytesIO
from xml.etree import ElementTree as ET

from crm.invoicing.engine.codici import OperazioneTS, SoggettoInviante, TipoDocumentoTS
from crm.invoicing.engine.sistema_ts import (
	NAMESPACE_SINCRONO,
	CifratoreFittizio,
	DocumentoSpesa,
	ErroreTS,
	IdSpesa,
	Proprietario,
	VoceSpesa,
	costruisci_file_allegato,
	crea_zip,
	nome_file,
	nome_file_valido,
	prepara_batch,
	scadenza_invio,
	scrivi_documento_sincrono,
	valida_documento,
)
from crm.invoicing.tests.base import UnitTestCase

CF_PAZIENTE = "RSSMRA80A01H501U"
CF_MEDICO = "BNCLCU75B41F205Z"


def documento(**kwargs) -> DocumentoSpesa:
	base = {
		"proprietario": Proprietario(
			cf_proprietario=CF_MEDICO, soggetto=SoggettoInviante.PROFESSIONISTA_SANITARIO
		),
		"id_spesa": IdSpesa(
			p_iva="00743110157", data_emissione=date(2026, 3, 10), num_documento="2026/S/128"
		),
		"data_pagamento": date(2026, 3, 10),
		"voci": [VoceSpesa(tipo_spesa="SP", importo=Decimal("100.00"), natura_iva="N4")],
		"cf_cittadino": CF_PAZIENTE,
		"pagamento_tracciato": True,
	}
	base.update(kwargs)
	return DocumentoSpesa(**base)


def figli(elemento) -> list[str]:
	return [f.tag.split("}")[-1] for f in elemento]


class ValidazioneTest(UnitTestCase):
	def test_un_documento_corretto_passa(self):
		esito = valida_documento(documento())
		self.assertTrue(esito.valido, esito.errori)

	def test_il_professionista_non_porta_il_codice_proprietario(self):
		esito = valida_documento(
			documento(
				proprietario=Proprietario(
					cf_proprietario=CF_MEDICO,
					soggetto=SoggettoInviante.PROFESSIONISTA_SANITARIO,
					codice_regione="030",
					codice_asl="201",
					codice_ssa="123456",
				)
			)
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("are omitted" in e for e in esito.errori))

	def test_la_struttura_senza_codice_proprietario_non_passa(self):
		esito = valida_documento(
			documento(
				proprietario=Proprietario(
					cf_proprietario="00743110157", soggetto=SoggettoInviante.STRUTTURA_AUTORIZZATA
				),
				voci=[VoceSpesa(tipo_spesa="SR", importo=Decimal("100.00"), natura_iva="N4")],
			)
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("Codice Proprietario" in e for e in esito.errori))

	def test_il_tipo_spesa_segue_l_albo_di_chi_emette(self):
		esito = valida_documento(
			documento(voci=[VoceSpesa(tipo_spesa="SR", importo=Decimal("100.00"), natura_iva="N4")])
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("register of whoever issues" in e for e in esito.errori))

	def test_l_opposizione_esclude_il_codice_fiscale(self):
		esito = valida_documento(documento(flag_opposizione=True))
		self.assertFalse(esito.valido)
		self.assertTrue(any("must be absent" in e for e in esito.errori))

	def test_con_opposizione_e_senza_cf_il_documento_si_trasmette(self):
		esito = valida_documento(documento(flag_opposizione=True, cf_cittadino=None))
		self.assertTrue(esito.valido, esito.errori)

	def test_senza_cf_e_senza_opposizione_manca_una_scelta(self):
		esito = valida_documento(documento(cf_cittadino=None))
		self.assertFalse(esito.valido)
		self.assertTrue(any("explicit choice" in e for e in esito.errori))

	def test_un_cf_in_omocodia_e_valido(self):
		omocodo = "RSSMRA80A01H50MM"
		esito = valida_documento(documento(cf_cittadino=omocodo))
		self.assertTrue(esito.valido, esito.errori)

	def test_il_numero_documento_ha_un_alfabeto_ristretto(self):
		esito = valida_documento(
			documento(
				id_spesa=IdSpesa(
					p_iva="00743110157",
					data_emissione=date(2026, 3, 10),
					num_documento="2026 S #128",
				)
			)
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("numDocumento" in e for e in esito.errori))

	def test_aliquota_e_natura_sono_alternative(self):
		esito = valida_documento(
			documento(
				voci=[
					VoceSpesa(
						tipo_spesa="SP",
						importo=Decimal("100.00"),
						aliquota_iva=Decimal("22.00"),
						natura_iva="N4",
					)
				]
			)
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("alternatives" in e for e in esito.errori))

	def test_il_pagamento_anticipato_va_dichiarato(self):
		esito = valida_documento(documento(data_pagamento=date(2025, 12, 20)))
		self.assertFalse(esito.valido)
		self.assertTrue(any("flagPagamentoAnticipato" in e for e in esito.errori))

	def test_col_pacchetto_prepagato_l_anno_e_quello_del_pagamento(self):
		spesa = documento(data_pagamento=date(2025, 12, 20), flag_pagamento_anticipato=True)
		self.assertTrue(valida_documento(spesa).valido)
		self.assertEqual(spesa.anno_competenza, 2025)

	def test_il_pagamento_non_tracciato_costa_la_detrazione(self):
		esito = valida_documento(documento(pagamento_tracciato=False))
		self.assertTrue(esito.valido)
		self.assertTrue(any("19% deduction" in a for a in esito.avvisi))

	def test_il_rimborso_vuole_il_documento_originario(self):
		esito = valida_documento(documento(flag_operazione=OperazioneTS.RIMBORSO))
		self.assertFalse(esito.valido)
		self.assertTrue(any("idRimborso" in e for e in esito.errori))

	def test_l_importo_e_sempre_positivo(self):
		esito = valida_documento(
			documento(voci=[VoceSpesa(tipo_spesa="SP", importo=Decimal("-10.00"), natura_iva="N4")])
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("refunds included" in e for e in esito.errori))

	def test_un_soggetto_non_sanitario_non_appartiene_al_tracciato(self):
		esito = valida_documento(
			documento(
				proprietario=Proprietario(cf_proprietario=CF_MEDICO, soggetto=SoggettoInviante.NON_SANITARIO)
			)
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("not a Sistema TS subject" in e for e in esito.errori))

	def test_le_fatture_hanno_dispositivo_uno(self):
		esito = valida_documento(
			documento(
				id_spesa=IdSpesa(
					p_iva="00743110157",
					data_emissione=date(2026, 3, 10),
					num_documento="2026/S/128",
					dispositivo=3,
				)
			)
		)
		self.assertFalse(esito.valido)
		self.assertTrue(any("dispositivo is always 1" in e for e in esito.errori))

	def test_solleva_se_invalido_alza_erroreTS(self):
		with self.assertRaises(ErroreTS):
			valida_documento(documento(cf_cittadino=None)).solleva_se_invalido()


class TracciatoTest(UnitTestCase):
	"""Two schemas, not one with a switch."""

	def test_l_allegato_non_ha_namespace(self):
		file_xml = costruisci_file_allegato([documento()], CifratoreFittizio())
		radice = ET.fromstring(file_xml)
		self.assertEqual(radice.tag, "precompilata")
		self.assertNotIn("}", radice[0].tag)

	def test_l_allegato_ha_un_solo_proprietario_per_file(self):
		file_xml = costruisci_file_allegato([documento(), documento()], CifratoreFittizio())
		radice = ET.fromstring(file_xml)
		self.assertEqual(len(radice.findall("proprietario")), 1)
		self.assertEqual(len(radice.findall("documentoSpesa")), 2)

	def test_due_proprietari_nello_stesso_file_sono_rifiutati(self):
		altro = documento(
			proprietario=Proprietario(
				cf_proprietario=CF_PAZIENTE, soggetto=SoggettoInviante.PROFESSIONISTA_SANITARIO
			)
		)
		with self.assertRaises(ErroreTS):
			costruisci_file_allegato([documento(), altro], CifratoreFittizio())

	def test_l_ordine_dell_allegato_mette_le_voci_in_fondo(self):
		file_xml = costruisci_file_allegato([documento()], CifratoreFittizio())
		radice = ET.fromstring(file_xml)
		self.assertEqual(
			figli(radice.find("documentoSpesa")),
			[
				"idSpesa",
				"dataPagamento",
				"flagOperazione",
				"cfCittadino",
				"pagamentoTracciato",
				"tipoDocumento",
				"flagOpposizione",
				"voceSpesa",
			],
		)

	def test_l_ordine_del_sincrono_mette_le_voci_prima_dei_flag(self):
		radice = ET.Element("wrapper")
		scrivi_documento_sincrono(radice, documento(), "CIFRATO", "idInserimentoDocumentoFiscale")
		nodo = radice[0]
		self.assertEqual(
			figli(nodo),
			[
				"idSpesa",
				"dataPagamento",
				"cfCittadino",
				"voceSpesa",
				"pagamentoTracciato",
				"tipoDocumento",
				"flagOpposizione",
			],
		)

	def test_il_sincrono_e_qualificato(self):
		radice = ET.Element("wrapper")
		nodo = scrivi_documento_sincrono(radice, documento(), "CIFRATO", "idInserimentoDocumentoFiscale")
		self.assertTrue(nodo.tag.startswith(f"{{{NAMESPACE_SINCRONO}}}"))

	def test_il_numero_documento_sta_dentro_num_documento_fiscale(self):
		file_xml = costruisci_file_allegato([documento()], CifratoreFittizio())
		radice = ET.fromstring(file_xml)
		numero = radice.find("documentoSpesa/idSpesa/numDocumentoFiscale")
		self.assertEqual(figli(numero), ["dispositivo", "numDocumento"])

	def test_con_opposizione_il_cf_non_viene_scritto(self):
		file_xml = costruisci_file_allegato(
			[documento(flag_opposizione=True, cf_cittadino=None)], CifratoreFittizio()
		)
		radice = ET.fromstring(file_xml)
		self.assertIsNone(radice.find("documentoSpesa/cfCittadino"))
		self.assertEqual(radice.find("documentoSpesa/flagOpposizione").text, "1")

	def test_l_importo_e_sempre_positivo_anche_nei_rimborsi(self):
		file_xml = costruisci_file_allegato(
			[documento(voci=[VoceSpesa(tipo_spesa="SP", importo=Decimal("100.00"), natura_iva="N4")])],
			CifratoreFittizio(),
		)
		radice = ET.fromstring(file_xml)
		self.assertEqual(radice.find("documentoSpesa/voceSpesa/importo").text, "100.00")

	def test_il_cifratore_fittizio_si_dichiara(self):
		import base64

		file_xml = costruisci_file_allegato([documento()], CifratoreFittizio())
		radice = ET.fromstring(file_xml)
		testo = radice.find("proprietario/cfProprietario").text
		self.assertTrue(base64.b64decode(testo).startswith(b"NONCIFRATO:"))


class BatchTest(UnitTestCase):
	def test_lo_zip_e_riproducibile(self):
		contenuto = b"<precompilata/>"
		self.assertEqual(crea_zip("TS730_2026.xml", contenuto), crea_zip("TS730_2026.xml", contenuto))

	def test_lo_zip_contiene_l_xml(self):
		archivio = crea_zip("TS730_2026.xml", b"<precompilata/>")
		with zipfile.ZipFile(BytesIO(archivio)) as zip_file:
			self.assertEqual(zip_file.namelist(), ["TS730_2026.xml"])

	def test_il_nome_file_rispetta_il_tracciato(self):
		nome = nome_file("STUDIOBIANCHI", 2026)
		self.assertTrue(nome_file_valido(nome))
		self.assertTrue(nome.endswith(".zip"))
		self.assertLessEqual(len(nome), 60)

	def test_il_nome_file_non_e_parlante(self):
		nome = nome_file("Studio Psicoterapia Rossi", 2026)
		self.assertNotIn(" ", nome)
		self.assertTrue(nome_file_valido(nome))

	def test_il_batch_si_spezza_sotto_il_limite(self):
		documenti = [
			documento(
				id_spesa=IdSpesa(
					p_iva="00743110157",
					data_emissione=date(2026, 3, 10),
					num_documento=f"2026/S/{i}",
				)
			)
			for i in range(40)
		]
		parti = prepara_batch(documenti, CifratoreFittizio(), "STUDIO", 2026, limite=600)
		self.assertGreater(len(parti), 1)
		self.assertEqual(sum(len(p.documenti) for p in parti), 40)
		for parte in parti:
			self.assertLessEqual(parte.dimensione, 600)
			self.assertEqual(parte.parti_totali, len(parti))

	def test_un_batch_che_sta_in_uno_zip_resta_uno(self):
		parti = prepara_batch([documento()], CifratoreFittizio(), "STUDIO", 2026)
		self.assertEqual(len(parti), 1)
		self.assertEqual(parti[0].parte, 1)

	def test_un_batch_vuoto_non_produce_zip(self):
		self.assertEqual(prepara_batch([], CifratoreFittizio(), "STUDIO", 2026), [])


class ScadenzeTest(UnitTestCase):
	def test_la_scadenza_ordinaria_e_il_31_gennaio(self):
		self.assertEqual(scadenza_invio(2026), date(2027, 1, 31))

	def test_i_veterinari_hanno_la_loro(self):
		self.assertEqual(scadenza_invio(2026, veterinario=True), date(2027, 3, 16))
