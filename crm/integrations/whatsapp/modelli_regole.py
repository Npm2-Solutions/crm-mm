# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A WhatsApp template without a site: which numbers can send it, its buttons by
Meta's rules, and Meta's own description of it read into the fields we keep.

Meta keeps a template on the WhatsApp Business account (the WABA), never on a
number: every number of that account sends it, a number of another account
cannot, and Meta answers with a template name «that does not exist». Two
accounts can each have a template of the same name (`hello_world` is in every
one of them), which are two templates.

Pure, tested with plain `unittest` (`crm/integrations/whatsapp/tests`).
"""

import re
from dataclasses import dataclass

RISPOSTA = "QUICK_REPLY"
LINK = "URL"
CHIAMATA = "PHONE_NUMBER"
#: the buttons a template written here may have
TIPI = (RISPOSTA, LINK, CHIAMATA)

#: Meta's button types as frappe_whatsapp names them in its `WhatsApp Button`
#: rows, which is what it reads when it sends the template to Meta
DA_META = {
	"QUICK_REPLY": "Quick Reply",
	"URL": "Visit Website",
	"PHONE_NUMBER": "Call Phone",
	"FLOW": "Flow",
	"MPM": "Multi-Product Message",
	"CATALOG": "Catalog",
}
A_META = {nome: tipo for tipo, nome in DA_META.items()}

# Meta's limits on buttons ("Template components", buttons)
MAX_PULSANTI = 10
MAX_LINK = 2
MAX_CHIAMATE = 1
MAX_TESTO = 25
MAX_URL = 2000
MAX_TELEFONO = 20

#: a template Meta no longer has: deleted in WhatsApp Manager, or by another app
SPARITO = "DELETED"

SEGNAPOSTO = re.compile(r"\{\{\s*(\d+)\s*\}\}")
TELEFONO = re.compile(r"^\+[0-9]{6,19}$")


@dataclass(frozen=True)
class Problema:
	"""What is wrong, in English words to translate, with their arguments."""

	messaggio: str
	argomenti: tuple = ()

	def testo(self, traduci=lambda s: s) -> str:
		return traduci(self.messaggio).format(*self.argomenti)


def numeri_che_possono(account: str | None, numeri: list[dict], invia: str | None) -> list[str]:
	"""The numbers that can send a template kept on `account`.

	`numeri` are the site's numbers as {"name", "waba"}: the ones on the same
	WhatsApp Business account. A template whose account nobody wrote down goes
	out from the number that sends (`invia`), as it always did; one whose account
	has no WABA written is that account's only.
	"""
	if not account:
		return [invia] if invia else []
	waba = next((numero.get("waba") for numero in numeri if numero["name"] == account), None)
	if not waba:
		return [account] if any(numero["name"] == account for numero in numeri) else []
	return [numero["name"] for numero in numeri if numero.get("waba") == waba]


def stesso_account(uno: str | None, altro: str | None, numeri: list[dict]) -> bool:
	"""Whether two numbers send the same templates: the same one, or two of the
	same WhatsApp Business account."""
	if not uno or not altro or uno == altro:
		return True
	return altro in numeri_che_possono(uno, numeri, None)


def pulsanti_in_ordine(pulsanti: list[dict]) -> list[dict]:
	"""The quick replies first, then the links and the call: Meta refuses them
	mixed («must be organized into two groups»). Each group keeps its order."""
	return sorted(pulsanti, key=lambda pulsante: pulsante.get("type") != RISPOSTA)


def problemi_dei_pulsanti(pulsanti: list[dict]) -> list[Problema]:
	"""What Meta would refuse in a template's buttons, said before it is sent
	for review: a refusal comes back as a number, after the save."""
	problemi = []
	if len(pulsanti) > MAX_PULSANTI:
		problemi.append(Problema("A template has at most {0} buttons", (MAX_PULSANTI,)))
	if sum(1 for pulsante in pulsanti if pulsante.get("type") == LINK) > MAX_LINK:
		problemi.append(Problema("At most {0} buttons open a link", (MAX_LINK,)))
	if sum(1 for pulsante in pulsanti if pulsante.get("type") == CHIAMATA) > MAX_CHIAMATE:
		problemi.append(Problema("Only one button can call"))

	visti = set()
	for numero, pulsante in enumerate(pulsanti, start=1):
		tipo = pulsante.get("type")
		testo = (pulsante.get("text") or "").strip()
		if tipo not in TIPI:
			problemi.append(Problema("Button {0}: choose what it does", (numero,)))
			continue
		if not testo:
			problemi.append(Problema("Button {0}: write what it says", (numero,)))
		elif len(testo) > MAX_TESTO:
			problemi.append(Problema("Button {0}: at most {1} characters", (numero, MAX_TESTO)))
		elif testo.casefold() in visti:
			# the person's reply is the button's words: two alike cannot be told apart
			problemi.append(Problema("Two buttons say «{0}»", (testo,)))
		visti.add(testo.casefold())

		if tipo == LINK:
			indirizzo = (pulsante.get("url") or "").strip()
			if not indirizzo.startswith(("https://", "http://")):
				problemi.append(Problema("Button {0}: the link starts with https://", (numero,)))
			elif len(indirizzo) > MAX_URL:
				problemi.append(Problema("Button {0}: the link is too long", (numero,)))
			elif "{{" in indirizzo and not (pulsante.get("example") or "").strip():
				problemi.append(Problema("Button {0}: Meta wants an example of the link", (numero,)))
		elif tipo == CHIAMATA:
			telefono = (pulsante.get("phone") or "").replace(" ", "")
			if not TELEFONO.match(telefono) or len(telefono) > MAX_TELEFONO:
				problemi.append(
					Problema(
						"Button {0}: write the number with its country code, as +39 02 1234567", (numero,)
					)
				)
	return problemi


def righe_dei_pulsanti(pulsanti: list[dict]) -> list[dict]:
	"""The buttons written here as frappe_whatsapp's rows, in Meta's order."""
	righe = []
	for pulsante in pulsanti_in_ordine(pulsanti):
		tipo = pulsante.get("type")
		riga = {"button_type": DA_META[tipo], "button_label": (pulsante.get("text") or "").strip()}
		if tipo == LINK:
			# a link whose last part changes with each message ({{1}}) keeps the
			# example Meta reviewed it with
			dinamico = bool(pulsante.get("dynamic")) or "{{" in (pulsante.get("url") or "")
			riga.update(
				{
					"website_url": (pulsante.get("url") or "").strip(),
					"url_type": "Dynamic" if dinamico else "Static",
				}
			)
			if dinamico:
				riga["example_url"] = pulsante.get("example") or ""
		elif tipo == CHIAMATA:
			riga["phone_number"] = (pulsante.get("phone") or "").replace(" ", "")
		righe.append(riga)
	return righe


def pulsanti_delle_righe(righe: list[dict]) -> list[dict]:
	"""frappe_whatsapp's rows as the buttons the screens read."""
	pulsanti = []
	for riga in righe:
		tipo = A_META.get(riga.get("button_type"))
		if not tipo:
			continue
		pulsante = {"type": tipo, "text": riga.get("button_label") or ""}
		if tipo == LINK:
			pulsante["url"] = riga.get("website_url") or ""
			pulsante["dynamic"] = riga.get("url_type") == "Dynamic"
			if pulsante["dynamic"]:
				pulsante["example"] = riga.get("example_url") or ""
		elif tipo == CHIAMATA:
			pulsante["phone"] = riga.get("phone_number") or ""
		pulsanti.append(pulsante)
	return pulsanti


def lingua(codice: str | None, lingue: set[str]) -> str | None:
	"""Meta's code for a language (it, en_US) as the framework names it (it,
	en-US), among the ones it has; nothing when it has none of them."""
	if not codice:
		return None
	candidati = [codice.replace("_", "-"), codice.split("_")[0]]
	per_minuscole = {nome.lower(): nome for nome in lingue}
	for candidato in candidati:
		if candidato.lower() in per_minuscole:
			return per_minuscole[candidato.lower()]
	return None


def esempi(corpo: str, esempi_di_meta: list | None) -> str:
	"""The examples of a body's variables, as frappe_whatsapp keeps them (comma
	separated). It sends as many values as there are examples, so a body with
	{{1}} and no example of Meta's gets its numbers: none would leave the
	variables out and Meta refuse the message."""
	if esempi_di_meta:
		return ",".join(str(valore) for valore in esempi_di_meta)
	quanti = len(set(SEGNAPOSTO.findall(corpo or "")))
	return ",".join(str(numero) for numero in range(1, quanti + 1))


def da_meta(modello: dict) -> dict:
	"""Meta's description of a template (`GET /<WABA>/message_templates`) in the
	fields the site keeps, its buttons as frappe_whatsapp's rows."""
	valori = {
		"id": modello.get("id"),
		"actual_name": modello.get("name"),
		"status": modello.get("status"),
		"category": modello.get("category"),
		"language_code": modello.get("language"),
		"header_type": "",
		"header": "",
		"template": "",
		"footer": "",
		"sample_values": "",
		"buttons": [],
	}
	for parte in modello.get("components") or []:
		tipo = (parte.get("type") or "").upper()
		if tipo == "HEADER":
			valori["header_type"] = parte.get("format") or ""
			if valori["header_type"] == "TEXT":
				valori["header"] = parte.get("text") or ""
		elif tipo == "BODY":
			valori["template"] = parte.get("text") or ""
			righe = ((parte.get("example") or {}).get("body_text") or [[]])[0]
			valori["sample_values"] = esempi(valori["template"], righe)
		elif tipo == "FOOTER":
			valori["footer"] = parte.get("text") or ""
		elif tipo == "BUTTONS":
			for pulsante in parte.get("buttons") or []:
				nome = DA_META.get(pulsante.get("type"))
				if not nome:
					continue
				riga = {"button_type": nome, "button_label": pulsante.get("text") or ""}
				if pulsante.get("type") == "URL":
					indirizzo = pulsante.get("url") or ""
					riga["website_url"] = indirizzo
					riga["url_type"] = "Dynamic" if "{{" in indirizzo else "Static"
					if pulsante.get("example"):
						riga["example_url"] = ",".join(pulsante["example"])
				elif pulsante.get("type") == "PHONE_NUMBER":
					riga["phone_number"] = pulsante.get("phone_number") or ""
				valori["buttons"].append(riga)
	return valori


def spariti(locali: list[dict], su_meta: set[str]) -> list[str]:
	"""The templates kept here whose Meta id is no longer among an account's.

	Only the ones Meta ever knew (an id) and not already marked: one being
	created has no id yet, and is not gone."""
	return [
		modello["name"]
		for modello in locali
		if modello.get("id") and modello["id"] not in su_meta and modello.get("status") != SPARITO
	]
