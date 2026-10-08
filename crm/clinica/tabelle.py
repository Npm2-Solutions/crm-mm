# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The food tables as the clinic's library keeps them, without a site (design.md,
"I piani", "Le librerie"; ricerca-design.md §2.3). The exercises dataset is the
CRM's (`crm.piani.dataset`).

- **The library DottorCloud ships** (`dati/alimenti.json`) is made here from CIQUAL
  as ANSES publishes it, the sheet in English (`libreria_ciqual`): each food with
  its code, its name in Italian (NPM2's, kept by code from one version to the
  next), ANSES's English, its group and its values for 100 g. The centre never
  imports a table: an Italian one (BDA-IEO with the licence for software, CREA with
  the written permission) NPM2 adds the same way.
- **A table is a sheet**: a row a food, a column a value for 100 g. The columns
  are recognised by their names, in Italian, French or English.
- **The numbers are the table's**: "4,63" is 4.63; "-" is not known and is not
  counted; "traces" and "< 0,15" (under what the laboratory measures) count as
  nothing. Energy only in kJ becomes kcal; carbohydrates "by difference" lose the
  fibre they include. A value no food can have (more than 100 g in 100 g) is
  dropped. A row without a name or without a single value is not a food.
- **Energy the table leaves out** (CIQUAL does for a food in four, when one
  component is missing) is computed from proteins, carbohydrates, fats, fibre and
  alcohol with the factors of the Regulation EU 1169/2011 - the table's own way,
  within a few kcal where both exist - and the food says so.
- **The group** comes from the table's own category, by its words, in Italian,
  French or English; where the words say the wrong group, NPM2 says the right one
  (`GRUPPI_CIQUAL`). The centre puts a food in another group as it likes.
"""

from __future__ import annotations

import math
import re
import unicodedata

from crm.clinica.piani_regole import GRUPPI
from crm.importazione import foglio

CIBO_CAMPI = (
	"code",
	"name",
	"group",
	"kcal",
	"kj",
	"protein_g",
	"carbs_g",
	"fat_g",
	"fibre_g",
	"alcohol_g",
)
#: What the library keeps of a food: its values for 100 g.
VALORI = ("kcal", "protein_g", "carbs_g", "fat_g", "fibre_g")
ALTRO = "Other"
#: The most a table's sheet may hold: a table is a thousand foods, not a database.
MAX_RIGHE = 20000
#: How many rows the header is looked for in: a title or a note may come first.
RIGHE_INTESTAZIONE = 15
KCAL_MAX = 1000
KJ_PER_KCAL = 4.184
#: Energy from the nutrients (Regulation EU 1169/2011, annex XIV), kcal per gram:
#: what a table computes itself, for the foods it leaves without.
FATTORI_UE = {"protein_g": 4, "carbs_g": 4, "fat_g": 9, "fibre_g": 2, "alcohol_g": 7}


# ------------------------------------------------------------------ words


def normalizza(testo) -> str:
	"""Lower case, without accents or signs: "Protéines, N x 6.25 (g/100 g)" is
	"proteines n x 6 25 g 100 g"."""
	testo = str(testo if testo is not None else "")
	for legatura, lettere in (("œ", "oe"), ("Œ", "oe"), ("æ", "ae"), ("Æ", "ae"), ("ß", "ss")):
		testo = testo.replace(legatura, lettere)
	testo = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode()
	return re.sub(r"[^a-z0-9]+", " ", testo.lower()).strip()


def _parole(testo: str, radici) -> bool:
	"""Whether a word of ``testo`` starts with one of ``radici``; a root ending in
	"$" is a whole word."""
	for radice in radici:
		intera = radice.endswith("$")
		radice = radice.rstrip("$")
		if re.search(r"(?<![a-z0-9])" + re.escape(radice) + (r"(?![a-z0-9])" if intera else ""), testo):
			return True
	return False


# ------------------------------------------------------------------ reading a sheet


def leggi_foglio(nome_file: str, contenuto: bytes) -> list[list]:
	"""The rows of a table's first sheet: Excel (.xlsx, .xls) or text (.csv, .txt)
	with commas, semicolons or tabs (`crm.importazione.foglio`, the CRM's reader)."""
	return foglio.leggi(nome_file, contenuto, MAX_RIGHE)


# ------------------------------------------------------------------ the columns


def _gruppo_ciqual(testo: str) -> int | None:
	# CIQUAL's sub-group, then its group: the third level adds names, not groups
	for livello, peso in (("alim ssgrp nom", 0), ("alim grp nom", 1)):
		if testo.startswith(livello):
			return peso
	return None


def _priorita(campo: str, testo: str) -> int | None:
	"""How well a column's name says it is ``campo``: lower is better, None no."""
	parole = testo.split()
	prima = parole[0] if parole else ""
	if campo == "code":
		if testo in ("alim code", "codice", "codice alimento", "code", "food code", "cod", "id"):
			return 0
		if testo in ("fdc id", "ndb no", "ndb number", "codice bda", "codice crea", "id alimento"):
			return 1
		return None
	if campo == "name":
		if testo.startswith("alim nom") and not testo.startswith("alim nom sci"):
			return 0
		if testo in (
			"nome",
			"nome alimento",
			"alimento",
			"denominazione",
			"descrizione",
			"name",
			"food",
			"food name",
			"description",
			"food description",
			"nom",
			"aliment",
		):
			return 1
		return None
	if campo == "group":
		ciqual = _gruppo_ciqual(testo)
		if ciqual is not None:
			return ciqual
		if testo in ("sottogruppo", "sottocategoria", "subgroup", "sub group", "subcategory"):
			return 3
		if testo in (
			"categoria",
			"gruppo",
			"gruppo alimentare",
			"categoria alimentare",
			"categoria merceologica",
			"category",
			"group",
			"food group",
			"food category",
			"groupe",
			"categorie",
		):
			return 4
		return None
	if campo == "kcal":
		if "kcal" in parole:
			return 0 if "1169" in parole else 1
		if testo in ("calorie", "calories", "energia kcal"):
			return 2
		return None
	if campo == "kj":
		if "kj" in parole:
			return 0 if "1169" in parole else 1
		return None
	if campo == "protein_g":
		if prima not in ("protein", "proteins", "proteine", "proteines", "proteina", "proteinas"):
			return None
		if any(p in parole for p in ("animal", "animali", "animales", "vegetal", "vegetali", "vegetales")):
			return None
		return 1 if ("crude" in parole or "6 25" in testo) else 0
	if campo == "carbs_g":
		if prima not in ("carboidrati", "carbohydrate", "carbohydrates", "glucides", "carbohidratos"):
			return None
		if "difference" in parole:
			return 2
		if "totali" in parole or "total" in parole:
			return 1
		return 0
	if campo == "fat_g":
		if any(
			p in parole for p in ("acidi", "acides", "fatty", "saturi", "saturated", "animali", "vegetali")
		):
			return None
		if prima in ("lipidi", "lipides", "lipids", "fat", "fats", "grassi") or testo.startswith(
			"total lipid"
		):
			return 0
		return None
	if campo == "fibre_g":
		if prima not in ("fibra", "fibre", "fibres", "fiber", "fibers"):
			return None
		if any(p in parole for p in ("solubile", "insolubile", "soluble", "insoluble")):
			return None
		return 0
	if campo == "alcohol_g":
		return 0 if prima in ("alcool", "alcol", "alcohol", "ethanol", "etanolo") else None
	return None


def lingua_delle_colonne(intestazioni: list) -> str:
	"""The language of a table, from its columns: it, fr or en."""
	testi = [normalizza(t) for t in intestazioni]
	if any(t.startswith("alim nom fr") or t.startswith("alim grp nom fr") for t in testi):
		return "fr"
	if any(t.startswith("alim nom eng") or t.startswith("alim grp nom eng") for t in testi):
		return "en"
	parole = {p for t in testi for p in t.split()}
	if parole & {"proteine", "carboidrati", "lipidi", "fibra", "energia", "nome", "codice", "alimento"}:
		return "it"
	if parole & {"proteines", "glucides", "lipides", "fibres", "energie", "nom", "aliment"}:
		return "fr"
	return "en"


def riconosci(intestazioni: list) -> dict:
	"""Which column is which: ``{campo: indice}``; the group is a list of columns,
	the most precise first (CIQUAL's sub-group, then its group). A column serves
	one field only."""
	testi = [normalizza(t) for t in intestazioni]
	mappa: dict = {}
	usate: set[int] = set()
	for campo in CIBO_CAMPI:
		candidati = []
		for indice, testo in enumerate(testi):
			if indice in usate or not testo:
				continue
			priorita = _priorita(campo, testo)
			if priorita is not None:
				candidati.append((priorita, indice))
		if not candidati:
			continue
		candidati.sort()
		if campo == "group":
			mappa[campo] = [indice for _p, indice in candidati[:3]]
			usate.update(mappa[campo])
		else:
			mappa[campo] = candidati[0][1]
			usate.add(candidati[0][1])
	if "carbs_g" in mappa and "difference" in testi[mappa["carbs_g"]].split():
		# USDA's carbohydrates by difference hold the fibre: it is taken out
		mappa["carbs_with_fibre"] = True
	return mappa


def fonte_probabile(intestazioni: list) -> str | None:
	"""The source a table's columns tell: CIQUAL names its own."""
	if any(normalizza(t) == "alim code" for t in intestazioni):
		return "CIQUAL"
	return None


def trova_intestazione(righe: list[list]) -> int | None:
	"""The row with the columns' names: the first that names a food and a value."""
	for indice, riga in enumerate(righe[:RIGHE_INTESTAZIONE]):
		mappa = riconosci(riga)
		if "name" in mappa and any(campo in mappa for campo in ("kcal", "kj", "protein_g", "fat_g")):
			return indice
	return None


# ------------------------------------------------------------------ the numbers


_MANCA = {"", "-", "--", "nd", "n d", "na", "n a", "nr", "?", "x"}


def numero(valore) -> float | None:
	"""A value for 100 g as a table writes it: None when not known, 0 for traces
	and for what is under the laboratory's limit."""
	if valore is None or isinstance(valore, bool):
		return None
	if isinstance(valore, int | float):
		return float(valore) if math.isfinite(valore) and valore >= 0 else None
	testo = str(valore).strip().lower().replace(" ", " ")
	if normalizza(testo) in _MANCA:
		return None
	if testo.startswith("tr") or testo.startswith("<"):
		return 0.0
	testo = testo.replace(" ", "")
	if "," in testo and "." in testo:
		# the last sign is the decimal one: 1.234,5 and 1,234.5
		migliaia = "." if testo.rfind(",") > testo.rfind(".") else ","
		testo = testo.replace(migliaia, "")
	testo = testo.replace(",", ".")
	try:
		numero_letto = float(testo)
	except ValueError:
		return None
	return numero_letto if math.isfinite(numero_letto) and numero_letto >= 0 else None


def _cella(riga: list, indice) -> object:
	if indice is None or not isinstance(indice, int) or indice >= len(riga):
		return None
	return riga[indice]


def _testo(valore) -> str:
	if valore is None:
		return ""
	if isinstance(valore, float) and valore.is_integer():
		# a code Excel keeps as a number: 25601.0 is "25601"
		return str(int(valore))
	return str(valore).strip()


# ------------------------------------------------------------------ the groups

#: The library's group from a category's words, in order: the first that says it
#: wins. "Vegetable oils" are oils, "fruits de mer" fish, "fruit juices" drinks.
REGOLE_GRUPPI: tuple[tuple[str, tuple[str, ...], frozenset | None], ...] = (
	(
		ALTRO,
		(
			"baby",
			"infantil",
			"infanzia",
			"substitu",
			"sostitut",
			"ricett",
			"recipe",
			"piatt",
			"dish",
			"plats",
			"entree",
			"starter",
			"savoury pastr",
			"savory pastr",
			"feuillete",
			"sandwich",
			"pizza",
			"soup",
			"zupp",
			"prodotti vari",
			"varie$",
			"fast food",
		),
		None,
	),
	(
		"Oils and fats",
		(
			"oil",
			"oli$",
			"olio",
			"huile",
			"fats$",
			"fat$",
			"grassi",
			"matieres grasses",
			"butter",
			"burro",
			"beurre",
			"margarin",
			"strutto",
			"lard",
		),
		None,
	),
	(
		"Drinks",
		(
			"beverage",
			"drink",
			"bevand",
			"bibit",
			"boisson",
			"juice",
			"succh",
			"jus$",
			"water",
			"acqua",
			"acque",
			"eau$",
			"eaux",
			"wine",
			"vino",
			"vini$",
			"beer",
			"birr",
			"coffee",
			"caffe",
			"tea$",
			"tisan",
			"alcoholic",
			"alcolic",
			"alcoolis",
			"liquor",
		),
		None,
	),
	(
		"Cereals and tubers",
		("savoury biscuit", "savory biscuit", "biscuits aperitif", "cracker", "grissin", "fette biscottate"),
		None,
	),
	(
		"Sweets",
		(
			"sweet",
			"dolc",
			"sugar",
			"zuccher",
			"sucre",
			"chocolat",
			"cioccolat",
			"confection",
			"confiser",
			"honey",
			"miele",
			"miel$",
			"jam$",
			"marmellat",
			"confettur",
			"confiture",
			"ice cream",
			"gelat",
			"glace",
			"sorbet",
			"dessert",
			"cake",
			"torte",
			"gateau",
			"pastr",
			"pasticcer",
			"patisser",
			"viennois",
			"biscuit",
			"biscott",
			"merendin",
			"caramell",
			"cereal bar",
			"barres cereal",
			"barrett",
		),
		None,
	),
	(
		"Nuts and seeds",
		(
			"nuts$",
			"nut$",
			"seed",
			"frutta secca",
			"frutta a guscio",
			"semi$",
			"semi oleos",
			"oleagin",
			"fruits a coque",
			"graine",
			"noci$",
			"nocciol",
			"mandorl",
			"arachid",
			"pistacch",
			"peanut",
		),
		None,
	),
	(
		"Legumes",
		("legumi", "legumineuse", "pulse", "fagiol", "ceci$", "lenticch", "bean", "lentil"),
		None,
	),
	# English "legumes" are pulses; French "légumes" are vegetables
	("Legumes", ("legume",), frozenset({"it", "en"})),
	(
		"Fish",
		(
			"fish",
			"pesc",
			"seafood",
			"shellfish",
			"mollus",
			"crustace",
			"crostace",
			"frutti di mare",
			"fruits de mer",
			"poisson",
		),
		None,
	),
	("Eggs", ("egg", "uov", "uova", "oeuf"), None),
	(
		"Meat",
		(
			"meat",
			"carn",
			"salum",
			"pollam",
			"poultry",
			"insaccat",
			"sausage",
			"delicatessen",
			"frattagli",
			"offal",
			"viande",
			"volaille",
			"charcuter",
			"abats",
			"prosciutt",
			"ham$",
		),
		None,
	),
	(
		"Milk and dairy",
		(
			"milk",
			"latte$",
			"latticin",
			"lattier",
			"dairy",
			"chees",
			"formagg",
			"yogurt",
			"yoghurt",
			"lait",
			"fromage",
			"yaourt",
		),
		None,
	),
	(
		"Cereals and tubers",
		(
			"cereal",
			"cereale",
			"bread",
			"pane$",
			"pani$",
			"pain$",
			"pains$",
			"pasta",
			"pates",
			"rice",
			"riso",
			"riz$",
			"flour",
			"farin",
			"grain",
			"potato",
			"patat",
			"pomme de terre",
			"pommes de terre",
			"tuber",
			"prodotti da forno",
		),
		None,
	),
	(
		"Vegetables",
		("vegetabl", "verdur", "ortagg", "mushroom", "fungh", "champignon"),
		None,
	),
	("Vegetables", ("legumes",), frozenset({"fr"})),
	("Fruit", ("fruit", "frutt"), None),
)


def gruppo_da(testi, lingua: str = "it") -> str:
	"""The library's group of a food, from its table's categories, the most
	precise first: the first that says something decides; else "Other"."""
	for testo in testi:
		normale = normalizza(testo)
		if not normale:
			continue
		for gruppo, radici, lingue in REGOLE_GRUPPI:
			if lingue is not None and lingua not in lingue:
				continue
			if _parole(normale, radici):
				return gruppo
	return ALTRO


# ------------------------------------------------------------------ the foods


def energia(valori: dict, alcol: float | None = None) -> float | None:
	"""The kcal of 100 g from its nutrients, with the factors of the Regulation EU
	1169/2011: only when proteins, carbohydrates and fats are all known; fibre
	and alcohol count when they are."""
	if any(valori.get(campo) is None for campo in ("protein_g", "carbs_g", "fat_g")):
		return None
	totale = sum(
		FATTORI_UE[campo] * (valori.get(campo) or 0) for campo in ("protein_g", "carbs_g", "fat_g", "fibre_g")
	)
	totale += FATTORI_UE["alcohol_g"] * (alcol or 0)
	return round(totale, 1)


def _valori(riga: list, mappa: dict) -> tuple[dict[str, float | None], int, bool]:
	"""The values for 100 g of a row, how many were dropped as impossible, and
	whether the energy was computed from the nutrients."""
	valori = {campo: numero(_cella(riga, mappa.get(campo))) for campo in ("kcal", *VALORI[1:])}
	scartati = 0
	if valori["kcal"] is None and mappa.get("kj") is not None:
		kj = numero(_cella(riga, mappa["kj"]))
		if kj is not None:
			valori["kcal"] = round(kj / KJ_PER_KCAL, 1)
	if valori["kcal"] is not None and valori["kcal"] > KCAL_MAX:
		valori["kcal"] = None
		scartati += 1
	for campo in VALORI[1:]:
		if valori[campo] is not None and valori[campo] > 100:
			valori[campo] = None
			scartati += 1
	if mappa.get("carbs_with_fibre") and valori["carbs_g"] is not None and valori["fibre_g"] is not None:
		valori["carbs_g"] = round(max(valori["carbs_g"] - valori["fibre_g"], 0), 2)
	calcolata = False
	if valori["kcal"] is None:
		alcol = numero(_cella(riga, mappa.get("alcohol_g")))
		valori["kcal"] = energia(valori, alcol if alcol is not None and alcol <= 100 else None)
		calcolata = valori["kcal"] is not None
	return valori, scartati, calcolata


def categoria(riga: list, mappa: dict) -> list[str]:
	"""A row's categories in the table, the most precise first, without the empty
	ones ("-" is one)."""
	indici = mappa.get("group")
	if indici is None:
		return []
	if isinstance(indici, int):
		indici = [indici]
	testi = []
	for indice in indici:
		testo = _testo(_cella(riga, indice))
		if normalizza(testo) and testo not in testi:
			testi.append(testo)
	return testi


def alimenti(righe: list[list], mappa: dict, lingua: str = "it") -> dict:
	"""The foods of a table's rows (the header excluded): each with its code, name,
	category, group and values for 100 g. A row without a name or without a single
	value is left out, and counted; a code seen twice is taken once."""
	cibi: list[dict] = []
	senza_nome = senza_valori = doppi = scartati = 0
	visti: set[str] = set()
	for riga in righe:
		if not isinstance(riga, list | tuple):
			continue
		riga = list(riga)
		nome = re.sub(r"\s+", " ", _testo(_cella(riga, mappa.get("name"))))[:140]
		if not nome:
			if any(_testo(c) for c in riga):
				senza_nome += 1
			continue
		valori, fuori, calcolata = _valori(riga, mappa)
		scartati += fuori
		if all(valore is None for valore in valori.values()):
			senza_valori += 1
			continue
		codice = _testo(_cella(riga, mappa.get("code")))[:40] or None
		chiave = codice or normalizza(nome)
		if chiave in visti:
			doppi += 1
			continue
		visti.add(chiave)
		categorie = categoria(riga, mappa)
		cibi.append(
			{
				"code": codice,
				"name": nome,
				"category": (categorie[0] if categorie else "")[:140],
				"group": gruppo_da(categorie, lingua),
				**valori,
				"kcal_computed": calcolata,
			}
		)
	return {
		"foods": cibi,
		"without_name": senza_nome,
		"without_values": senza_valori,
		"twice": doppi,
		"dropped_values": scartati,
	}


# ------------------------------------------------------------------ the library DottorCloud ships

#: CIQUAL's categories whose words say the wrong group, by their code: a pastry
#: dough is flour, a plant-based alternative to meat is a pulse's.
GRUPPI_CIQUAL = {"0305": "Cereals and tubers", "040309": "Legumes"}


def _colonna(intestazioni: list, nome: str) -> int | None:
	testi = [normalizza(t) for t in intestazioni]
	return testi.index(nome) if nome in testi else None


def libreria_ciqual(righe: list[list], nomi: dict[str, str] | None = None) -> tuple[list[dict], list[str]]:
	"""The library DottorCloud ships, from CIQUAL's sheet in English as ANSES
	publishes it: each food with its code, its name in Italian (``nomi``, by code;
	else the English, and the code among the ones to translate), ANSES's English,
	its group and its values for 100 g. A food the table gives no energy for, not
	even from its nutrients, stays out: a diet counts calories, and 0 would be
	wrong. The foods and the codes still to translate."""
	nomi = nomi or {}
	indice = trova_intestazione(righe)
	if indice is None:
		raise ValueError("not CIQUAL's sheet")
	intestazioni = ["" if c is None else str(c) for c in righe[indice]]
	mappa = riconosci(intestazioni)
	sottogruppi = [
		i
		for i in (_colonna(intestazioni, n) for n in ("alim ssssgrp code", "alim ssgrp code"))
		if i is not None
	]
	gruppi_dei_codici = {}
	for riga in righe[indice + 1 :]:
		codice = _testo(_cella(list(riga), mappa.get("code")))
		for i in sottogruppi:
			sotto = _testo(_cella(list(riga), i))
			if sotto in GRUPPI_CIQUAL:
				gruppi_dei_codici[codice] = GRUPPI_CIQUAL[sotto]
				break
	voci, da_tradurre = [], []
	for cibo in alimenti(righe[indice + 1 :], mappa, lingua_delle_colonne(intestazioni))["foods"]:
		if cibo["kcal"] is None:
			continue
		nome = (nomi.get(cibo["code"]) or "").strip()
		if not nome:
			da_tradurre.append(cibo["code"])
		voci.append(
			{
				"code": cibo["code"],
				"name": (nome or cibo["name"])[:140],
				"name_en": cibo["name"],
				"group": gruppi_dei_codici.get(cibo["code"], cibo["group"]),
				**{campo: cibo[campo] for campo in VALORI},
				"kcal_computed": 1 if cibo["kcal_computed"] else 0,
			}
		)
	return voci, da_tradurre


def dalla_libreria(voce, lingua: str = "it") -> dict | None:
	"""A food of the library as the site keeps it: its name in the site's language
	(Italian, else ANSES's English), the English as the source's name, a group the
	library has, values a food can have. None for a record that is not one, or one
	without its energy."""
	if not isinstance(voce, dict):
		return None
	codice = _testo(voce.get("code"))[:40]
	inglese = re.sub(r"\s+", " ", _testo(voce.get("name_en")))[:140]
	italiano = re.sub(r"\s+", " ", _testo(voce.get("name")))[:140]
	nome = (italiano if lingua == "it" else "") or inglese or italiano
	if not codice or not nome:
		return None
	valori = {campo: numero(voce.get(campo)) for campo in VALORI}
	if valori["kcal"] is not None and valori["kcal"] > KCAL_MAX:
		valori["kcal"] = None
	for campo in VALORI[1:]:
		if valori[campo] is not None and valori[campo] > 100:
			valori[campo] = None
	if valori["kcal"] is None:
		return None
	return {
		"code": codice,
		"name": nome,
		"name_in_source": inglese or nome,
		"group": voce.get("group") if voce.get("group") in GRUPPI else ALTRO,
		**valori,
		"kcal_computed": 1 if voce.get("kcal_computed") else 0,
	}
