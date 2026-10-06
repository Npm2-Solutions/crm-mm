# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a list offers to choose, without a site."""

import unittest

from crm.liste import regole as R


def campo(nome, tipo="Data", etichetta=None, sezione=None, scheda="Details", **altro):
	return {
		"fieldname": nome,
		"fieldtype": tipo,
		"label": etichetta if etichetta is not None else nome.replace("_", " ").title(),
		"sezione": sezione,
		"scheda": scheda,
		**altro,
	}


def nomi(scelti):
	return [s["fieldname"] for s in scelti]


def etichette(scelti):
	return {s["fieldname"]: s["label"] for s in scelti}


class CosaSiOffre(unittest.TestCase):
	def test_mai_quello_della_macchina(self):
		campi = [
			campo("name", etichetta="Name"),
			campo("naming_series", "Select", "Series"),
			campo("_comments", "Text", "Comments"),
			campo("first_name", etichetta="First Name"),
			campo("visitor", "Link", "Visitor"),
		]
		for uso in R.USI:
			scelti = nomi(R.scegli(campi, uso, togli={"visitor"}))
			self.assertIn("first_name", scelti, uso)
			for della_macchina in ("name", "naming_series", "_comments", "visitor"):
				self.assertNotIn(della_macchina, scelti, uso)

	def test_mai_quello_nascosto_senza_nome_o_due_volte(self):
		campi = [
			campo("nascosto", hidden=1),
			campo("senza_nome", etichetta=""),
			campo("email", etichetta="Email"),
			campo("email", etichetta="Email"),
		]
		self.assertEqual(nomi(R.scegli(campi, "filtro"))[:1], ["email"])
		self.assertEqual(nomi(R.scegli(campi, "filtro")).count("email"), 1)
		self.assertNotIn("nascosto", nomi(R.scegli(campi, "filtro")))
		self.assertNotIn("senza_nome", nomi(R.scegli(campi, "filtro")))

	def test_ogni_uso_i_suoi_tipi(self):
		campi = [
			campo("stato", "Select", "Status"),
			campo("note", "Text Editor", "Notes"),
			campo("importo", "Currency", "Amount"),
			campo("arrivato", "Datetime", "Arrived On"),
			campo("giorno", "Date", "Day"),
			campo("riferimento", "Dynamic Link", "Reference"),
			campo("foto", "Attach Image", "Picture"),
		]
		self.assertEqual(
			[
				n
				for n in nomi(R.scegli(campi, "filtro"))
				if not n.startswith(("_", "owner", "creation", "modified"))
			],
			["stato", "note", "importo", "arrivato", "giorno", "riferimento"],
		)
		self.assertEqual(
			[n for n in nomi(R.scegli(campi, "ordine")) if n in {c["fieldname"] for c in campi}],
			["stato", "importo", "arrivato", "giorno"],
		)
		# a group is a value many share: never an amount, a moment, a text
		self.assertEqual(
			[n for n in nomi(R.scegli(campi, "gruppo")) if n in {c["fieldname"] for c in campi}],
			["stato", "giorno"],
		)
		self.assertNotIn("foto", nomi(R.scegli(campi, "colonna")))

	def test_un_uso_che_non_c_e(self):
		with self.assertRaises(ValueError):
			R.scegli([], "tabella")


class IStandard(unittest.TestCase):
	def test_dopo_i_campi_del_documento_con_i_loro_nomi(self):
		scelti = R.scegli([campo("first_name", etichetta="First Name")], "filtro")
		self.assertEqual(
			nomi(scelti), ["first_name", "_assign", "owner", "creation", "modified_by", "modified"]
		)
		self.assertEqual(etichette(scelti)["owner"], "Created By")
		self.assertEqual(etichette(scelti)["modified_by"], "Last Modified By")

	def test_quali_per_ogni_uso(self):
		self.assertEqual(nomi(R.scegli([], "gruppo")), ["owner"])
		self.assertEqual(nomi(R.scegli([], "ordine")), ["creation", "modified", "owner", "modified_by"])
		self.assertIn("_liked_by", nomi(R.scegli([], "colonna")))
		self.assertEqual(etichette(R.scegli([], "colonna"))["_liked_by"], "Favourite")
		self.assertNotIn("_liked_by", nomi(R.scegli([], "filtro")))

	def test_il_campo_del_documento_vince_su_quello_che_si_chiama_come_lui(self):
		# a task's «Assigned To» is whom it is for
		scelti = R.scegli([campo("assigned_to", "Link", "Assigned To", options="User")], "filtro")
		self.assertIn("assigned_to", nomi(scelti))
		self.assertNotIn("_assign", nomi(scelti))

	def test_quello_tolto_non_torna(self):
		self.assertNotIn("owner", nomi(R.scegli([], "filtro", togli={"owner"})))


class NomiDistinti(unittest.TestCase):
	CAMPI = (
		campo("source", "Link", "Source"),
		campo("first_touch_source", etichetta="Source", sezione="First Touch", scheda="Tracking"),
		campo("last_touch_source", etichetta="Source", sezione="Last Touch", scheda="Tracking"),
		campo("lead_name", etichetta="Full Name"),
	)

	def test_li_distingue_la_sezione(self):
		scelti = etichette(R.scegli(self.CAMPI, "filtro"))
		self.assertEqual(scelti["source"], "Source")
		self.assertEqual(scelti["first_touch_source"], "Source (First Touch)")
		self.assertEqual(scelti["last_touch_source"], "Source (Last Touch)")
		self.assertEqual(scelti["lead_name"], "Full Name")

	def test_poi_la_scheda_e_mai_due_volte(self):
		campi = [
			campo("telefono", etichetta="Phone", scheda="Person"),
			campo("telefono_azienda", etichetta="Phone", scheda="Company"),
			campo("a", etichetta="Code", sezione="Card", scheda="One"),
			campo("b", etichetta="Code", sezione="Card", scheda="Two"),
		]
		scelti = etichette(R.scegli(campi, "filtro"))
		self.assertEqual(scelti["telefono"], "Phone (Person)")
		self.assertEqual(scelti["telefono_azienda"], "Phone (Company)")
		# once told apart by its section, never again by its tab
		self.assertEqual(scelti["a"], "Code (Card)")
		self.assertEqual(scelti["b"], "Code (Card)")

	def test_nelle_parole_di_chi_legge(self):
		parole = {"Source": "Sorgente", "First Touch": "Primo contatto", "Last Touch": "Ultimo contatto"}
		scelti = etichette(R.scegli(self.CAMPI, "gruppo", t=lambda testo: parole.get(testo, testo)))
		self.assertEqual(scelti["source"], "Sorgente")
		self.assertEqual(scelti["first_touch_source"], "Sorgente (Primo contatto)")

	def test_nessun_segno_di_lavoro_resta(self):
		for scelto in R.scegli(self.CAMPI, "colonna"):
			self.assertEqual(set(scelto), {"fieldname", "fieldtype", "label", "options"})


class IlNomeDiUnaColonna(unittest.TestCase):
	def test_quelle_del_framework_come_le_liste_le_chiamano(self):
		self.assertEqual(R.nome_della_colonna("owner", "Owner"), "Created By")
		self.assertEqual(R.nome_della_colonna("modified_by", "Modified By"), "Last Modified By")
		self.assertEqual(R.nome_della_colonna("_liked_by", "Like"), "Favourite")

	def test_il_resto_come_scritto(self):
		self.assertEqual(R.nome_della_colonna("owner", "Chi l'ha scritta"), "Chi l'ha scritta")
		self.assertEqual(R.nome_della_colonna("status", "Status"), "Status")
		self.assertIsNone(R.nome_della_colonna(None, None))


class LaScheda(unittest.TestCase):
	def test_ogni_tipo_ma_mai_la_struttura_ne_i_campi_del_framework(self):
		campi = [
			campo("righe", "Table", "Rows"),
			campo("nota", "HTML", "Note"),
			campo("colonna", "Column Break", "Column"),
			campo("sezione", "Section Break", "Section"),
			campo("nome", etichetta="First Name"),
		]
		self.assertEqual(nomi(R.scegli(campi, "scheda")), ["righe", "nota", "nome"])
		# a table is never a column, a filter, an order or a group
		for uso in ("filtro", "ordine", "gruppo", "colonna"):
			self.assertNotIn("righe", nomi(R.scegli(campi, uso)), uso)
