# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A sheet of people from another program, without a site: which column is what,
a row as a person, what is wrong with it, how a person already here is found.
Tested with plain `unittest`.

Every program exports its own way. The columns are recognised by the words they
are usually called by - Italian first, as the centres' software writes them - and
the person's eye on the preview decides the rest. A value is read the way an
Italian sheet writes it: 02/01/1980, 333 123 4567, «ROSSI MARIO».
"""

from __future__ import annotations

import datetime
import re
import unicodedata

#: A person's field and the names its column goes by, written plain (`semplice`).
COLONNE = {
	"full_name": (
		"nominativo",
		"paziente",
		"cliente",
		"cognome e nome",
		"cognome nome",
		"nome e cognome",
		"nome cognome",
		"nome completo",
		"full name",
		"name and surname",
	),
	"first_name": ("nome", "first name", "firstname", "given name"),
	"last_name": ("cognome", "last name", "lastname", "surname", "family name"),
	"email": ("email", "e mail", "mail", "posta elettronica", "indirizzo email"),
	"mobile_no": (
		"cellulare",
		"cell",
		"tel cellulare",
		"telefono cellulare",
		"mobile",
		"mobile phone",
		"cellulare 1",
	),
	"phone": ("telefono", "tel", "telefono fisso", "fisso", "tel fisso", "telefono casa", "phone"),
	"fiscal_code": ("codice fiscale", "cf", "cod fiscale", "c f", "codicefiscale", "fiscal code", "tax code"),
	"birth_date": (
		"data di nascita",
		"data nascita",
		"nato il",
		"nata il",
		"nascita",
		"birth date",
		"date of birth",
		"dob",
	),
	"sex": ("sesso", "genere", "sex", "gender"),
	"address_line": ("indirizzo", "via", "address", "residenza"),
	"civic_number": ("civico", "numero civico", "n civico", "nr civico"),
	"postal_code": ("cap", "codice postale", "zip", "postal code"),
	"city": ("citta", "comune", "localita", "city", "comune di residenza"),
	"province": ("provincia", "prov", "pr", "province"),
	"notes": ("note", "annotazioni", "osservazioni", "notes"),
	"external_id": (
		"id",
		"codice paziente",
		"codice cliente",
		"id paziente",
		"n scheda",
		"numero scheda",
		"codice",
	),
}

#: The order a column called only «nominativo» or «paziente» puts the names in:
#: Italian clinical software writes the surname first.
COGNOME_PRIMA = ("nominativo", "paziente", "cliente", "cognome e nome", "cognome nome")

CODICE_FISCALE = re.compile(
	r"^[A-Z]{6}[0-9LMNPQRSTUV]{2}[ABCDEHLMPRST][0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{3}[A-Z]$"
)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MESI_CF = "ABCDEHLMPRST"
OMOCODIA = {
	"L": "0",
	"M": "1",
	"N": "2",
	"P": "3",
	"Q": "4",
	"R": "5",
	"S": "6",
	"T": "7",
	"U": "8",
	"V": "9",
}

#: Problems, in English, said in the centre's language by whoever shows them.
SENZA_NOME = "No name"
EMAIL_SBAGLIATA = "The email {0} is not an email"
CF_SBAGLIATO = "The fiscal code {0} is not valid"
DATA_SBAGLIATA = "The date {0} is not a date"


def semplice(testo) -> str:
	"""A column's name to compare: lowercase, no accents, only letters, digits and
	single spaces. «Data di Nascita», «data_di_nascita» and «DATA-DI-NASCITA»
	are one."""
	testo = unicodedata.normalize("NFKD", str(testo or "")).encode("ascii", "ignore").decode()
	return " ".join(re.sub(r"[^a-z0-9]+", " ", testo.lower()).split())


def riconosci(intestazione: list) -> dict[int, str]:
	"""Which column is which field: by its name, each field once, the first column
	that says it."""
	per_nome = {alias: campo for campo, nomi in COLONNE.items() for alias in nomi}
	mappa: dict[int, str] = {}
	presi: set[str] = set()
	for indice, nome in enumerate(intestazione):
		campo = per_nome.get(semplice(nome))
		if campo and campo not in presi:
			mappa[indice] = campo
			presi.add(campo)
	return mappa


def data(valore, anche_futura: bool = False) -> datetime.date | None:
	"""A date as a sheet gives it: a date, Excel's serial number, «02/01/1980»,
	«2-1-80», «1980-01-02». None when it is empty; ValueError when it is not one.
	A birth is never in the future; ``anche_futura`` for a date that may be (an
	appointment)."""
	if valore in (None, ""):
		return None
	if isinstance(valore, datetime.datetime):
		return valore.date()
	if isinstance(valore, datetime.date):
		return valore
	if isinstance(valore, (int, float)):
		# Excel counts days from 30/12/1899
		return datetime.date(1899, 12, 30) + datetime.timedelta(days=int(valore))
	testo = str(valore).strip().split(" ")[0]
	for formato in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"):
		try:
			giorno = datetime.datetime.strptime(testo, formato).date()
		except ValueError:
			continue
		if giorno.year > datetime.date.today().year and not anche_futura:
			# «80» is 1980, never 2080
			giorno = giorno.replace(year=giorno.year - 100)
		return giorno
	raise ValueError(testo)


def telefono(valore) -> str:
	"""A number as DottorCloud keeps it: an Italian one with +39, spaces gone;
	one with its own prefix as it is."""
	testo = str(valore or "").strip()
	if testo.endswith(".0"):
		# a number Excel read as a number
		testo = testo[:-2]
	cifre = re.sub(r"[^\d+]", "", testo)
	if not cifre:
		return ""
	if cifre.startswith("00"):
		return "+" + cifre[2:]
	if cifre.startswith("+"):
		return cifre
	if cifre.startswith(("3", "0")) and 6 <= len(cifre) <= 11:
		return "+39" + cifre
	return cifre


def ultime_nove(numero: str) -> str:
	"""The last nine digits: how two ways of writing one number meet (as the
	phone's search does)."""
	return re.sub(r"\D", "", numero or "")[-9:]


def sesso(valore, codice_fiscale: str = "") -> str:
	"""«M» or «F» from what the sheet says, or from the fiscal code."""
	parola = semplice(valore)
	if parola in ("m", "maschio", "uomo", "male", "maschile"):
		return "M"
	if parola in ("f", "femmina", "donna", "female", "femminile"):
		return "F"
	if codice_fiscale and CODICE_FISCALE.match(codice_fiscale):
		giorno = int("".join(OMOCODIA.get(c, c) for c in codice_fiscale[9:11]))
		return "F" if giorno > 40 else "M"
	return ""


def nascita_dal_codice(codice_fiscale: str) -> datetime.date | None:
	"""The birth date a fiscal code carries; the century the one that is not in
	the future."""
	if not CODICE_FISCALE.match(codice_fiscale or ""):
		return None
	cifre = lambda testo: int("".join(OMOCODIA.get(c, c) for c in testo))  # noqa: E731
	anno = cifre(codice_fiscale[6:8])
	mese = MESI_CF.index(codice_fiscale[8]) + 1
	giorno = cifre(codice_fiscale[9:11]) % 40
	oggi = datetime.date.today()
	secolo = 2000 if 2000 + anno <= oggi.year else 1900
	try:
		return datetime.date(secolo + anno, mese, giorno)
	except ValueError:
		return None


def nome_proprio(testo: str) -> str:
	"""«ROSSI» is «Rossi», «de luca» «De Luca»; a name written with its capitals
	stays as it is."""
	testo = " ".join(str(testo or "").split())
	if testo.isupper() or testo.islower():
		# «D'AMICO» is «D'Amico», «ROSSI-BIANCHI» «Rossi-Bianchi»
		return re.sub(
			r"[^\s'’-]+", lambda pezzo: pezzo.group(0)[:1].upper() + pezzo.group(0)[1:].lower(), testo
		)
	return testo


def dividi(nome_completo: str, cognome_prima: bool) -> tuple[str, str]:
	"""A full name in first and last: the surname is the first word when the
	column puts it first, else the last."""
	parole = nome_completo.split()
	if len(parole) < 2:
		return (nome_completo, "")
	if cognome_prima:
		return (" ".join(parole[1:]), parole[0])
	return (" ".join(parole[:-1]), parole[-1])


def persona(riga: list, mappa: dict[int, str], intestazione: list) -> tuple[dict, list[tuple[str, str]]]:
	"""A row as a person: their fields, read and put right, and what is wrong
	with it (a sentence and its value). A row without a name is not a person."""
	grezzi = {campo: riga[indice] for indice, campo in mappa.items() if indice < len(riga)}
	dati: dict = {}
	problemi: list[tuple[str, str]] = []

	nome = nome_proprio(grezzi.get("first_name") or "")
	cognome = nome_proprio(grezzi.get("last_name") or "")
	if not (nome or cognome) and grezzi.get("full_name"):
		colonna = next(semplice(intestazione[i]) for i, c in mappa.items() if c == "full_name")
		nome, cognome = dividi(nome_proprio(grezzi["full_name"]), colonna in COGNOME_PRIMA)
	if not (nome or cognome):
		problemi.append((SENZA_NOME, ""))
	dati["first_name"], dati["last_name"] = nome, cognome

	email = str(grezzi.get("email") or "").strip().lower()
	if email and not EMAIL.match(email):
		problemi.append((EMAIL_SBAGLIATA, email))
		email = ""
	dati["email"] = email
	dati["mobile_no"] = telefono(grezzi.get("mobile_no"))
	dati["phone"] = telefono(grezzi.get("phone"))
	if not dati["mobile_no"] and dati["phone"].startswith("+393"):
		# a mobile in the only column of numbers
		dati["mobile_no"], dati["phone"] = dati["phone"], ""

	codice = re.sub(r"\s", "", str(grezzi.get("fiscal_code") or "")).upper()
	if codice and not CODICE_FISCALE.match(codice):
		problemi.append((CF_SBAGLIATO, codice))
		codice = ""
	dati["fiscal_code"] = codice

	try:
		nascita = data(grezzi.get("birth_date"))
	except ValueError as errore:
		problemi.append((DATA_SBAGLIATA, str(errore)))
		nascita = None
	dati["birth_date"] = nascita or nascita_dal_codice(codice)
	dati["sex"] = sesso(grezzi.get("sex"), codice)

	for campo in ("address_line", "civic_number", "city", "notes", "external_id"):
		dati[campo] = " ".join(str(grezzi.get(campo) or "").split())
	if dati["city"]:
		dati["city"] = nome_proprio(dati["city"])
	cap = str(grezzi.get("postal_code") or "").strip()
	dati["postal_code"] = cap[:-2] if cap.endswith(".0") else cap
	if dati["postal_code"].isdigit():
		dati["postal_code"] = dati["postal_code"].zfill(5)
	dati["province"] = str(grezzi.get("province") or "").strip().upper()[:2]
	return dati, problemi


def chiavi(dati: dict) -> list[tuple[str, str]]:
	"""How a person already here is found, the surest first: their fiscal code,
	their email, their mobile, else their name with their birth date."""
	trovate = []
	if dati.get("fiscal_code"):
		trovate.append(("fiscal_code", dati["fiscal_code"]))
	if dati.get("email"):
		trovate.append(("email", dati["email"]))
	if ultime_nove(dati.get("mobile_no")):
		trovate.append(("mobile_no", ultime_nove(dati["mobile_no"])))
	nascita = dati.get("birth_date")
	if nascita and (dati.get("first_name") or dati.get("last_name")):
		quando = nascita.isoformat() if hasattr(nascita, "isoformat") else str(nascita)
		trovate.append(
			(
				"name_birth",
				"|".join((semplice(dati.get("first_name")), semplice(dati.get("last_name")), quando)),
			)
		)
	return trovate
