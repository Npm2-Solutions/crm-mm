"""The fiscal profile of whoever is invoiced: what an invoice takes from it, and
what a confirmed invoice gives back to it.

The codice fiscale and the address belong to the person, not to one invoice: a
patient who comes back should not be asked for them again, and neither should the
client of a consultant. They live once, in the profile, and travel both ways:

- a new invoice takes from the profile whatever it has left empty;
- a confirmed invoice fills the profile where the profile is empty, so the second
  document asks nothing.

Neither side ever overwrites the other. What is on an invoice is what was
confirmed at the desk, and what is in the profile is what somebody wrote there on
purpose: a value that differs is a decision, not a gap.

Pure: dictionaries in, dictionaries out. The rules can be checked without a site.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

from crm.invoicing.engine import codice_fiscale as cf
from crm.invoicing.engine.codici import TipoDestinatario

#: Who the invoice is made out to, beyond the name.
IDENTIFICATIVI = ("fiscal_code", "tax_id", "recipient_code", "pec")

#: The address travels as one block: a street from one place and a city from
#: another is an address nobody lives at.
INDIRIZZO = ("address_line", "civic_number", "postal_code", "city", "province", "country")

#: Every field the profile and the invoice have in common, with the same names.
CAMPI = ("billing_name", *IDENTIFICATIVI, *INDIRIZZO)

PAESE_PREDEFINITO = "IT"


def _vuoto(valore) -> bool:
	return valore is None or (isinstance(valore, str) and not valore.strip())


def ha_indirizzo(valori: dict) -> bool:
	"""An address says where: a street, a postal code or a city.

	The country alone is not an address. The invoice defaults it to IT, and
	treating that default as "an address is there" would stop the real one from
	ever being filled in.
	"""
	return any(not _vuoto(valori.get(campo)) for campo in ("address_line", "postal_code", "city"))


def _indirizzo(valori: dict) -> dict:
	blocco = {campo: valori.get(campo) or None for campo in INDIRIZZO}
	blocco["country"] = valori.get("country") or PAESE_PREDEFINITO
	return blocco


def _a_nome_di_una_persona(fattura: dict) -> bool:
	return (
		fattura.get("recipient_type") or TipoDestinatario.PERSONA_FISICA
	) == TipoDestinatario.PERSONA_FISICA


def da_compilare(fattura: dict, profilo: dict) -> dict:
	"""What a new invoice takes from the profile.

	Every identifier the invoice has left empty, and the address as a block when
	the invoice has none. The name only for a company or an office: a person's
	invoice carries their first name and surname, and a trade name written once in
	their profile would otherwise end up on a doctor's receipt.
	"""
	valori: dict = {}
	campi = IDENTIFICATIVI if _a_nome_di_una_persona(fattura) else ("billing_name", *IDENTIFICATIVI)
	for campo in campi:
		if _vuoto(fattura.get(campo)) and not _vuoto(profilo.get(campo)):
			valori[campo] = profilo[campo]
	if not ha_indirizzo(fattura) and ha_indirizzo(profilo):
		valori.update(_indirizzo(profilo))
	return valori


def da_completare(profilo: dict, fattura: dict) -> dict:
	"""What a confirmed invoice gives back to the profile: only where it is empty.

	The name is given back only from an invoice to a company or an office, for the
	same reason it is taken only by one.
	"""
	valori: dict = {}
	campi = IDENTIFICATIVI if _a_nome_di_una_persona(fattura) else ("billing_name", *IDENTIFICATIVI)
	for campo in campi:
		if _vuoto(profilo.get(campo)) and not _vuoto(fattura.get(campo)):
			valori[campo] = fattura[campo]
	if not ha_indirizzo(profilo) and ha_indirizzo(fattura):
		valori.update(_indirizzo(fattura))
	return valori


def _parole(*testi: str | None) -> frozenset[str]:
	insieme = " ".join(t for t in testi if t)
	senza_accenti = unicodedata.normalize("NFKD", insieme)
	senza_accenti = "".join(c for c in senza_accenti if not unicodedata.combining(c))
	return frozenset(re.findall(r"[a-z]+", senza_accenti.lower()))


def stessa_persona(fattura: dict, persona: dict) -> bool:
	"""The invoice is made out to this person, not to whoever pays for them.

	A child's visit is often invoiced to a parent: same record, the parent's name
	and codice fiscale on the document. Giving those back would write the parent's
	codice fiscale into the child's profile, and the next invoice would carry it.

	The words of the two names are compared, not the fields: a web form puts the
	whole name in the first name, and the desk splits it on the invoice. When one
	name holds all the words of the other it is the same person, written more or
	less completely; a first name that is not there at all is somebody else.
	"""
	sulla_fattura = _parole(fattura.get("first_name"), fattura.get("last_name"))
	nel_crm = _parole(persona.get("first_name"), persona.get("last_name"))
	if not (sulla_fattura and nel_crm):
		return False
	return sulla_fattura <= nel_crm or nel_crm <= sulla_fattura


# ----------------------------------------------------------------- the values


def normalizza(valori: dict) -> dict:
	"""The way each field is written, whoever typed it.

	Codes in capitals and without spaces, the PEC in lower case, the rest trimmed.
	Only the fields present are returned, so a partial update stays partial.
	"""
	pulito: dict = {}
	for campo, valore in valori.items():
		if campo not in CAMPI:
			continue
		if _vuoto(valore):
			pulito[campo] = None
			continue
		testo = str(valore).strip()
		if campo in ("fiscal_code", "tax_id", "recipient_code"):
			testo = re.sub(r"[\s.\-]", "", testo).upper()
		elif campo in ("province", "country"):
			testo = testo.upper()
		elif campo == "pec":
			testo = testo.lower()
		elif campo == "postal_code":
			testo = testo.replace(" ", "")
		else:
			testo = re.sub(r"\s+", " ", testo)
		pulito[campo] = testo
	return pulito


def errori(valori: dict) -> list[str]:
	"""The fields that are wrong in a way a machine can tell, by name.

	Blocking only what the invoice would refuse later anyway, at a worse moment: a
	codice fiscale that fails its check character, a VAT number of a known format
	that does not follow it, a codice destinatario of the wrong length, an Italian
	postal code or province that the SdI would reject.
	"""
	problemi: list[str] = []
	paese = (valori.get("country") or PAESE_PREDEFINITO).upper()
	italia = paese == "IT"

	codice = valori.get("fiscal_code")
	if codice:
		if len(codice) == 16:
			giusto = cf.valido(codice)
		elif len(codice) == 11 and codice.isdigit():
			# a company's codice fiscale: eleven digits with the VAT check digit
			giusto = cf.partita_iva_valida(codice)
		else:
			# abroad a tax number has any shape; in Italy it has one of two
			giusto = not italia
		if not giusto:
			problemi.append("fiscal_code")

	partita_iva = valori.get("tax_id")
	if partita_iva:
		prefisso, _numero = cf.separa_partita_iva_ue(partita_iva)
		stato = prefisso or paese
		if cf.formato_iva_noto(stato) and not cf.partita_iva_ue_valida(partita_iva, paese):
			problemi.append("tax_id")

	destinatario = valori.get("recipient_code")
	if destinatario and (len(destinatario) not in (6, 7) or not destinatario.isalnum()):
		problemi.append("recipient_code")

	if len(paese) != 2 or not paese.isalpha():
		problemi.append("country")
	if italia:
		cap = valori.get("postal_code")
		if cap and not re.fullmatch(r"\d{5}", cap):
			problemi.append("postal_code")
		provincia = valori.get("province")
		if provincia and not re.fullmatch(r"[A-Z]{2}", provincia):
			problemi.append("province")
	return problemi


def dati_dal_codice(codice: str | None) -> dict:
	"""Date of birth and sex, read out of a person's codice fiscale.

	Empty for anything that is not a valid sixteen-character code: a company's
	eleven digits encode neither, and a wrong code encodes somebody else.
	"""
	if not codice or len(codice) != 16 or not cf.valido(codice):
		return {"birth_date": None, "sex": None}
	dati = cf.analizza(codice)
	return {"birth_date": dati.data_nascita, "sex": dati.sesso}


def incoerenze(
	codice: str | None,
	*,
	cognome: str | None = None,
	nome: str | None = None,
	sesso: str | None = None,
	nascita: date | None = None,
) -> list[str]:
	"""Which of surname, first name, sex and date of birth the code contradicts.

	Keys, not sentences: whoever shows them decides the words. A plausibility check
	and never a block - double and foreign surnames produce false alarms, and those
	belong in front of a person, not in the way of a save.
	"""
	if not codice or len(codice) != 16 or not cf.valido(codice):
		return []
	contraddetti = []
	for chiave, argomenti in (
		("cognome", {"cognome": cognome}),
		("nome", {"nome": nome}),
		("sesso", {"sesso": sesso}),
		("nascita", {"data_nascita": nascita}),
	):
		if any(argomenti.values()) and cf.coerente_con_anagrafica(codice, **argomenti):
			contraddetti.append(chiave)
	return contraddetti
