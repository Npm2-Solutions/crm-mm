# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What the SdI says back, and what it means.

Six kinds of notice and only one of them is good news. The one that gets misread
is `MC`: it is not a failure, the invoice is issued and waiting in the client's
reserved area - what is owed is telling the client, because the SdI will not.
"""

from __future__ import annotations

from datetime import datetime

from crm.invoicing.engine.codici import StatoSdI
from crm.invoicing.engine.ricevute import (
	ESITO_ACCETTAZIONE,
	ESITO_RIFIUTO,
	TipoRicevuta,
	analizza,
	e_ricevuta,
	riferimento_da_nome,
	tipo_da_nome,
)
from crm.invoicing.tests.base import UnitTestCase

CONSEGNA = b"""<?xml version="1.0" encoding="UTF-8"?>
<ns3:RicevutaConsegna xmlns:ns3="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/RicevutaConsegna_v1.0">
	<IdentificativoSdI>1234567890</IdentificativoSdI>
	<NomeFile>IT01234567890_00001.xml</NomeFile>
	<DataOraRicezione>2026-03-10T09:12:33.000+01:00</DataOraRicezione>
	<DataOraConsegna>2026-03-10T09:15:00.000+01:00</DataOraConsegna>
	<MessageId>987654</MessageId>
</ns3:RicevutaConsegna>"""

SCARTO = b"""<?xml version="1.0" encoding="UTF-8"?>
<ns2:RicevutaScarto xmlns:ns2="http://x">
	<IdentificativoSdI>1234567890</IdentificativoSdI>
	<NomeFile>IT01234567890_00001.xml</NomeFile>
	<ListaErrori>
		<Errore><Codice>00423</Codice><Descrizione>Imponibile non congruente</Descrizione></Errore>
		<Errore><Codice>00421</Codice><Descrizione>Imposta non congruente</Descrizione></Errore>
	</ListaErrori>
</ns2:RicevutaScarto>"""

MANCATA = b"""<?xml version="1.0"?>
<ns:RicevutaImpossibilitaRecapito xmlns:ns="http://x">
	<IdentificativoSdI>1234567890</IdentificativoSdI>
	<NomeFile>IT01234567890_00001.xml</NomeFile>
	<Descrizione>Canale non disponibile</Descrizione>
</ns:RicevutaImpossibilitaRecapito>"""

ESITO = b"""<?xml version="1.0"?>
<ns:NotificaEsito xmlns:ns="http://x">
	<IdentificativoSdI>1234567890</IdentificativoSdI>
	<EsitoCommittente>
		<Esito>EC02</Esito>
		<Descrizione>Importi non concordati</Descrizione>
	</EsitoCommittente>
</ns:NotificaEsito>"""

DECORRENZA = b"""<?xml version="1.0"?>
<ns:NotificaDecorrenzaTermini xmlns:ns="http://x">
	<IdentificativoSdI>1234567890</IdentificativoSdI>
	<NomeFile>IT01234567890_00001.xml</NomeFile>
</ns:NotificaDecorrenzaTermini>"""


class NomeFileTest(UnitTestCase):
	def test_il_tipo_si_legge_dal_nome(self):
		self.assertEqual(tipo_da_nome("IT01234567890_00001_RC_001.xml"), "RC")
		self.assertEqual(tipo_da_nome("IT01234567890_abc12_NS_01.xml"), "NS")

	def test_una_fattura_non_e_una_ricevuta(self):
		self.assertIsNone(tipo_da_nome("IT01234567890_00001.xml"))
		self.assertFalse(e_ricevuta("IT01234567890_00001.xml"))
		self.assertFalse(e_ricevuta(None))

	def test_il_nome_dice_a_quale_file_risponde(self):
		self.assertEqual(riferimento_da_nome("IT01234567890_00001_MC_001.xml"), "IT01234567890_00001.xml")

	def test_un_nome_qualunque_non_passa(self):
		self.assertIsNone(tipo_da_nome("ricevuta.xml"))
		self.assertIsNone(tipo_da_nome("IT01234567890_00001_ZZ_001.xml"))


class ConsegnaTest(UnitTestCase):
	def test_la_consegna_e_terminale(self):
		ricevuta = analizza(CONSEGNA, "IT01234567890_00001_RC_001.xml")
		self.assertEqual(ricevuta.tipo, TipoRicevuta.CONSEGNA)
		self.assertEqual(ricevuta.stato, StatoSdI.CONSEGNATA)
		self.assertTrue(ricevuta.terminale)
		self.assertFalse(ricevuta.scartata)

	def test_i_dati_di_riconciliazione_si_leggono(self):
		ricevuta = analizza(CONSEGNA, "IT01234567890_00001_RC_001.xml")
		self.assertEqual(ricevuta.identificativo_sdi, "1234567890")
		self.assertEqual(ricevuta.nome_file, "IT01234567890_00001.xml")
		self.assertEqual(ricevuta.message_id, "987654")
		self.assertEqual(ricevuta.data, datetime(2026, 3, 10, 9, 15, 0))


class ScartoTest(UnitTestCase):
	def test_lo_scarto_elenca_i_codici(self):
		ricevuta = analizza(SCARTO, "IT01234567890_00001_NS_001.xml")
		self.assertEqual(ricevuta.stato, StatoSdI.SCARTATA)
		self.assertTrue(ricevuta.scartata)
		self.assertFalse(ricevuta.terminale)
		self.assertEqual([e.codice for e in ricevuta.errori], ["00423", "00421"])

	def test_il_riassunto_spiega_il_codice(self):
		ricevuta = analizza(SCARTO, "IT01234567890_00001_NS_001.xml")
		riassunto = ricevuta.riassunto()
		self.assertIn("non emessa", riassunto)
		self.assertIn("00423", riassunto)

	def test_uno_scarto_senza_lista_usa_la_descrizione(self):
		ricevuta = analizza(
			b"<RicevutaScarto><Descrizione>File non integro</Descrizione></RicevutaScarto>",
			"IT01234567890_00001_NS_001.xml",
		)
		self.assertEqual(len(ricevuta.errori), 1)
		self.assertIn("File non integro", ricevuta.riassunto())


class MancataConsegnaTest(UnitTestCase):
	def test_la_mancata_consegna_non_e_un_fallimento(self):
		# The invoice is fiscally issued and sits in the client's reserved area.
		ricevuta = analizza(MANCATA, "IT01234567890_00001_MC_001.xml")
		self.assertEqual(ricevuta.stato, StatoSdI.MANCATA_CONSEGNA)
		self.assertFalse(ricevuta.scartata)
		self.assertTrue(ricevuta.terminale)
		self.assertIn("area riservata", ricevuta.riassunto())

	def test_la_grafia_alternativa_si_riconosce_lo_stesso(self):
		# The SdI has shipped both spellings over the years.
		ricevuta = analizza(
			b"<RicevutaImpossibultaRecapito><IdentificativoSdI>1</IdentificativoSdI></RicevutaImpossibultaRecapito>"
		)
		self.assertEqual(ricevuta.tipo, TipoRicevuta.MANCATA_CONSEGNA)


class EsitoCommittenteTest(UnitTestCase):
	def test_il_rifiuto_della_pa_e_uno_scarto(self):
		ricevuta = analizza(ESITO, "IT01234567890_00001_NE_001.xml")
		self.assertEqual(ricevuta.stato, StatoSdI.ESITO_PA)
		self.assertEqual(ricevuta.esito, ESITO_RIFIUTO)
		self.assertTrue(ricevuta.scartata)
		self.assertFalse(ricevuta.terminale)
		self.assertIn("rifiutata", ricevuta.riassunto())

	def test_l_accettazione_chiude_il_documento(self):
		ricevuta = analizza(ESITO.replace(b"EC02", b"EC01"), "IT01234567890_00001_NE_001.xml")
		self.assertEqual(ricevuta.esito, ESITO_ACCETTAZIONE)
		self.assertTrue(ricevuta.terminale)
		self.assertFalse(ricevuta.scartata)

	def test_il_silenzio_della_pa_chiude_comunque(self):
		ricevuta = analizza(DECORRENZA, "IT01234567890_00001_DT_001.xml")
		self.assertEqual(ricevuta.stato, StatoSdI.DECORRENZA_TERMINI)
		self.assertTrue(ricevuta.terminale)


class RobustezzaTest(UnitTestCase):
	def test_un_file_che_non_e_xml_torna_none(self):
		self.assertIsNone(analizza(b"non e' xml", "IT01234567890_00001_RC_001.xml"))

	def test_un_xml_che_non_e_una_ricevuta_torna_none(self):
		self.assertIsNone(analizza(b"<FatturaElettronica/>", "IT01234567890_00001.xml"))

	def test_una_radice_sconosciuta_si_salva_col_nome(self):
		ricevuta = analizza(
			b"<Qualcosa><Descrizione>x</Descrizione></Qualcosa>", "IT01234567890_00001_RC_001.xml"
		)
		self.assertEqual(ricevuta.tipo, TipoRicevuta.CONSEGNA)

	def test_il_parsing_ignora_i_namespace(self):
		ricevuta = analizza(
			b"""<RicevutaConsegna xmlns="http://un/namespace/qualunque">
			<IdentificativoSdI>42</IdentificativoSdI></RicevutaConsegna>"""
		)
		self.assertEqual(ricevuta.identificativo_sdi, "42")
