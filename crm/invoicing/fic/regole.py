# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Fatture in Cloud without a site: what is handed over for an invoice, which of
the centre's VAT types and accounts in Fatture in Cloud stands for each of ours,
and what its states mean here.

A centre that invoices with Fatture in Cloud keeps doing so: an invoice made here
is born there, takes its number there and leaves for the SdI from there. What was
computed here is handed over line by line, and Fatture in Cloud adds it up first
(`/issued_documents/totals`): the two totals must be the same to the cent, or
nothing is made there (`totali_diversi`).

Pure: plain dicts in, plain dicts out, tested with plain `unittest`. What is wrong
is a `Problema`, English words translated where they are said.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0.00")
CENTESIMO = Decimal("0.01")

#: Our document types, as Fatture in Cloud names them. Nothing else is handed over.
TIPI = {"TD01": "invoice", "TD04": "credit_note"}
NOTA_DI_CREDITO = "credit_note"

#: Who receives it, as Fatture in Cloud calls them.
DESTINATARI = {
	"persona_fisica": "person",
	"soggetto_iva": "company",
	"pubblica_amministrazione": "pa",
}

#: The INPS 4% rivalsa: Fatture in Cloud keeps it apart from the other funds.
RIVALSA_INPS = "TC22"
#: The withholdings Fatture in Cloud calls its own; the others are "other".
RITENUTE_PROPRIE = ("RT01", "RT02")

#: What is written on the line of a re-charged stamp duty, as in our own XML: the
#: words of the document, Italian whatever language the screens speak.
RIGA_BOLLO = "Recupero imposta di bollo"

#: Fatture in Cloud's e-invoice states, and ours. A state not here moves nothing.
STATI_SDI = {
	"attempt": "inviato",
	"pending": "inviato",
	"processing": "inviato",
	"sent": "consegnata",
	"not_delivered": "mancata_consegna",
	"discarded": "scartata",
	"error": "errore",
	"accepted": "esito_pa",
	"manual_accepted": "esito_pa",
	"rejected": "esito_pa",
	"manual_rejected": "esito_pa",
	"no_response": "decorrenza_termini",
}
#: The ones a person has to act on: the invoice counts as not issued, or the
#: public body refused it.
DA_CORREGGERE = ("discarded", "rejected", "manual_rejected")
#: The ones after which nothing is asked any more.
FINALI = (
	"sent",
	"not_delivered",
	"discarded",
	"accepted",
	"manual_accepted",
	"rejected",
	"manual_rejected",
	"no_response",
)

#: Words in a payment account's name that say what it holds, by payment method:
#: cash, a card, a bank. Lower case, looked for inside the name.
CONTI_PER_METODO = {
	"MP01": ("cassa", "contant"),
	"MP08": ("pos", "carta", "card", "sumup", "nexi", "stripe", "satispay"),
	"MP05": ("banca", "bonific", "conto corrente", "iban"),
	"MP02": ("banca", "assegn", "conto corrente"),
	"MP12": ("banca", "riba", "conto corrente"),
	"MP19": ("banca", "sepa", "conto corrente"),
}


@dataclass
class Problema:
	"""What is wrong, in English words to translate, with their arguments."""

	messaggio: str
	argomenti: tuple = ()

	def testo(self, traduci=lambda s: s) -> str:
		return traduci(self.messaggio).format(*self.argomenti)


def decimale(valore) -> Decimal:
	return Decimal(str(valore or 0)).quantize(CENTESIMO, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------- VAT types


def chiave_iva(aliquota, natura: str | None = None) -> str:
	"""Our way of saying a VAT treatment: «22», or «0|N4» for a rate with no tax."""
	valore = Decimal(str(aliquota or 0))
	testo = f"{valore:.2f}".rstrip("0").rstrip(".")
	if valore == 0:
		return f"0|{(natura or '').strip()}"
	return testo


def dividi_chiave(chiave: str) -> tuple[Decimal, str]:
	aliquota, _, natura = chiave.partition("|")
	return Decimal(aliquota or "0"), natura


def candidati(chiave: str, tipi: list[dict]) -> list[dict]:
	"""The company's VAT types in Fatture in Cloud that say the same as `chiave`:
	the same rate, and with no tax the same nature. Never a switched-off one."""
	aliquota, natura = dividi_chiave(chiave)
	trovati = []
	for tipo in tipi or []:
		if tipo.get("is_disabled") or tipo.get("id") is None:
			continue
		if Decimal(str(tipo.get("value") or 0)) != aliquota:
			continue
		if aliquota == 0 and (tipo.get("ei_type") or "").strip() != natura:
			continue
		trovati.append(tipo)
	return trovati


def scegli_tipo(chiave: str, tipi: list[dict], scelto=None) -> int | None:
	"""The VAT type that stands for `chiave`: the one the centre chose while it is
	still one of the candidates, else the only candidate, else the company's default
	among them. Several and none the default: the centre chooses."""
	trovati = candidati(chiave, tipi)
	if scelto not in (None, "") and any(str(tipo["id"]) == str(scelto) for tipo in trovati):
		return int(scelto)
	if len(trovati) == 1:
		return int(trovati[0]["id"])
	predefiniti = [tipo for tipo in trovati if tipo.get("default")]
	if len(predefiniti) == 1:
		return int(predefiniti[0]["id"])
	return None


def conto_suggerito(metodo: str, conti: list[dict], scelto=None) -> int | None:
	"""The account a payment made by `metodo` is recorded on: the one the centre
	chose while it is there, else the only account, else the only one whose name
	says it holds that kind of money (the till for cash, the POS for a card)."""
	presenti = [conto for conto in conti or [] if conto.get("id") is not None]
	if scelto not in (None, "") and any(str(conto["id"]) == str(scelto) for conto in presenti):
		return int(scelto)
	if len(presenti) == 1:
		return int(presenti[0]["id"])
	parole = CONTI_PER_METODO.get(metodo, ())
	adatti = [
		conto
		for conto in presenti
		if any(parola in (conto.get("name") or "").lower() for parola in parole)
		or (metodo != "MP01" and "banca" in parole and conto.get("type") == "bank")
	]
	if len(adatti) == 1:
		return int(adatti[0]["id"])
	return None


def numerazioni(info: dict, anno: int) -> list[str]:
	"""The numerations Fatture in Cloud has for a year: the main one («») first."""
	dell_anno = ((info or {}).get("numerations") or {}).get(str(anno)) or {}
	return sorted({"", *dell_anno.keys()}, key=lambda numerazione: (numerazione != "", numerazione))


def numero_stampato(numero, numerazione: str | None) -> str:
	"""The number as Fatture in Cloud prints it: 12, or 12/A."""
	return f"{numero}{numerazione or ''}"


# -------------------------------------------------------------------- the invoice


def _entita(destinatario: dict) -> dict:
	tipo_nostro = destinatario.get("tipo") or "persona_fisica"
	partita_iva = (destinatario.get("partita_iva") or "").strip()
	if tipo_nostro == "estero":
		tipo = "company" if partita_iva else "person"
	else:
		tipo = DESTINATARI.get(tipo_nostro, "person")
	paese = (destinatario.get("paese") or "IT").strip().upper()
	indirizzo = " ".join(
		parte for parte in (destinatario.get("indirizzo"), destinatario.get("civico")) if parte
	).strip()
	entita = {
		"type": tipo,
		"name": destinatario.get("nome") or "",
		"vat_number": partita_iva,
		"tax_code": (destinatario.get("codice_fiscale") or "").strip(),
		"address_street": indirizzo,
		"address_postal_code": destinatario.get("cap") or "",
		"address_city": destinatario.get("citta") or "",
		"address_province": destinatario.get("provincia") or "",
		"country_iso": paese,
	}
	if paese == "IT":
		entita["country"] = "Italia"
	if tipo == "person":
		entita["first_name"] = destinatario.get("nome_proprio") or ""
		entita["last_name"] = destinatario.get("cognome") or ""
	if destinatario.get("codice_destinatario"):
		entita["ei_code"] = destinatario["codice_destinatario"].strip()
	if destinatario.get("pec"):
		entita["certified_email"] = destinatario["pec"].strip()
	return entita


def _prezzo(riga: dict) -> tuple[Decimal, Decimal, Decimal]:
	"""Quantity, unit price and discount (a percentage) that make the line's amount.

	A discount written as an amount has no percentage: the line goes with its net
	price, or as one of its amount where the price would need a third decimal."""
	quantita = Decimal(str(riga.get("quantita") or 1))
	importo = decimale(riga.get("importo"))
	if not Decimal(str(riga.get("sconto_importo") or 0)):
		return quantita, Decimal(str(riga.get("prezzo") or 0)), Decimal(str(riga.get("sconto") or 0))
	unitario = importo / quantita if quantita else importo
	if unitario == unitario.quantize(CENTESIMO):
		return quantita, unitario.quantize(CENTESIMO), ZERO
	return Decimal("1"), importo, ZERO


def _righe(righe: list[dict]) -> list[tuple[str, str]]:
	"""Name and description of each line: the first line of our description is the
	name, the rest its description."""
	parti = []
	for riga in righe:
		testo = (riga.get("descrizione") or "").strip()
		nome, _, resto = testo.partition("\n")
		parti.append((nome.strip(), resto.strip()))
	return parti


def documento(fattura: dict, mappa: dict) -> tuple[dict, list[Problema]]:
	"""What Fatture in Cloud is given for `fattura`, and what stops it.

	`fattura` is our invoice as `emissione.fattura_per_fic` reads it: its type,
	date, client, lines with their VAT key, the fund, the withholding, the stamp
	duty, the payment, the Sistema TS when Fatture in Cloud reports it. `mappa`
	says which VAT type and which account of the company's stands for ours
	(`iva`, `conti`) and the numerations (`numerazioni`).
	"""
	problemi: list[Problema] = []
	tipo = TIPI.get(fattura.get("tipo") or "TD01")
	if not tipo:
		problemi.append(
			Problema(
				"Fatture in Cloud is given invoices and credit notes from here: make this document in Fatture in Cloud"
			)
		)
		return {}, problemi

	elettronica = bool(fattura.get("elettronica"))
	iva = (mappa or {}).get("iva") or {}
	parole_iva = fattura.get("iva_in_parole") or {}

	def tipo_iva(chiave: str) -> int | None:
		scelto = iva.get(chiave)
		if scelto in (None, ""):
			problemi.append(
				Problema(
					"Choose the VAT rate of Fatture in Cloud that stands for {0}: Settings > Invoicing > Fatture in Cloud",
					(parole_iva.get(chiave, chiave),),
				)
			)
			return None
		return int(scelto)

	cassa = fattura.get("cassa") or {}
	ritenuta = fattura.get("ritenuta") or {}
	righe = fattura.get("righe") or []
	nomi = _righe(righe)
	voci = []
	gia_detti = set()
	for indice, riga in enumerate(righe):
		chiave = riga.get("chiave_iva") or chiave_iva(riga.get("aliquota"), riga.get("natura"))
		identificativo = tipo_iva(chiave) if chiave not in gia_detti else iva.get(chiave)
		gia_detti.add(chiave)
		quantita, prezzo, sconto = _prezzo(riga)
		nome, descrizione = nomi[indice]
		voce = {
			"name": nome,
			"qty": float(quantita),
			"net_price": float(prezzo),
			"discount": float(sconto),
			"not_taxable": bool(riga.get("anticipazione")),
			# the fund and the withholding fall on the fee, never on an advance
			"apply_withholding_taxes": not riga.get("anticipazione"),
		}
		if descrizione:
			voce["description"] = descrizione
		if identificativo not in (None, ""):
			voce["vat"] = {"id": int(identificativo)}
		voci.append(voce)

	bollo = decimale(fattura.get("bollo"))
	riaddebito = decimale(fattura.get("bollo_riaddebitato"))
	if elettronica and riaddebito > ZERO:
		# the re-charged duty is part of the fee (Risposta AdE 428/2022): it takes
		# the VAT of the service it follows, and the withholding with it. Fatture in
		# Cloud puts the fund on what it withholds on, and the fund is not on it here
		chiave = fattura.get("chiave_iva_bollo") or (righe[0].get("chiave_iva") if righe else "0|N4")
		voce = {
			"name": RIGA_BOLLO,
			"qty": 1.0,
			"net_price": float(riaddebito),
			"discount": 0.0,
			"not_taxable": False,
			"apply_withholding_taxes": bool(ritenuta) and not cassa,
		}
		if iva.get(chiave) not in (None, ""):
			voce["vat"] = {"id": int(iva[chiave])}
		elif chiave not in gia_detti:
			tipo_iva(chiave)
		voci.append(voce)

	dati: dict = {
		"type": tipo,
		"date": fattura.get("data"),
		"subject": fattura.get("marcatore") or "",
		"entity": _entita(fattura.get("destinatario") or {}),
		"e_invoice": elettronica,
		"use_gross_prices": False,
		"use_split_payment": bool(fattura.get("split_payment")),
		"items_list": voci,
	}
	numerazione = _numerazione(mappa, tipo, elettronica)
	if numerazione is not None:
		dati["numeration"] = numerazione
	if fattura.get("causale"):
		dati["visible_subject"] = fattura["causale"]

	# the stamp duty: on an electronic invoice the duty the company pays (its F24),
	# the re-charge being a line of the fee; on paper, what the client is charged
	if elettronica:
		dati["stamp_duty"] = float(bollo)
	else:
		dati["stamp_duty"] = float(riaddebito)

	if cassa:
		percentuale = float(decimale(cassa.get("percentuale")))
		if cassa.get("tipo") == RIVALSA_INPS:
			dati["rivalsa"] = percentuale
		else:
			dati["cassa"] = percentuale
			dati["cassa_taxable"] = 100.0
			if cassa.get("tipo"):
				dati["ei_cassa_type"] = cassa["tipo"]
	if ritenuta:
		percentuale = float(decimale(ritenuta.get("percentuale")))
		if (ritenuta.get("tipo") or "RT01") in RITENUTE_PROPRIE:
			dati["withholding_tax"] = percentuale
			dati["withholding_tax_taxable"] = 100.0
			if ritenuta.get("causale"):
				dati["ei_withholding_tax_causal"] = ritenuta["causale"]
		else:
			dati["other_withholding_tax"] = percentuale
			dati["ei_other_withholding_tax_type"] = ritenuta["tipo"]
			if ritenuta.get("causale"):
				dati["ei_other_withholding_tax_causal"] = ritenuta["causale"]

	if elettronica:
		ei_data = {"payment_method": fattura.get("metodo_pagamento") or "MP05"}
		if fattura.get("split_payment"):
			ei_data["vat_kind"] = "S"
		riferimento = fattura.get("riferimento") or {}
		if tipo == NOTA_DI_CREDITO and riferimento:
			ei_data["invoice_number"] = riferimento.get("numero")
			ei_data["invoice_date"] = riferimento.get("data")
		for campo, chiave in (("cig", "cig"), ("cup", "cup")):
			if fattura.get(chiave):
				ei_data[campo] = fattura[chiave]
		if fattura.get("ordine"):
			ei_data["original_document_type"] = "ordine"
			ei_data["od_number"] = fattura["ordine"]
		dati["ei_data"] = ei_data

	pagamento = _pagamento(fattura, mappa, problemi)
	if pagamento:
		dati["payments_list"] = [pagamento]

	dati["extra_data"] = _sistema_ts(fattura, righe, nomi, problemi)
	return dati, problemi


def _numerazione(mappa: dict, tipo: str, elettronica: bool) -> str | None:
	numerazioni_ = (mappa or {}).get("numerazioni") or {}
	if tipo == NOTA_DI_CREDITO:
		return numerazioni_.get("note")
	return numerazioni_.get("sdi" if elettronica else "carta")


def _pagamento(fattura: dict, mappa: dict, problemi: list[Problema]) -> dict | None:
	"""The one payment: what the client pays, when, and - paid at the desk - on
	which of the company's accounts the money went."""
	pagamento = fattura.get("pagamento") or {}
	importo = decimale(pagamento.get("importo"))
	if importo == ZERO:
		return None
	voce = {
		"amount": float(importo),
		"due_date": pagamento.get("scadenza") or fattura.get("data"),
		"status": "not_paid",
	}
	if pagamento.get("pagato_il"):
		metodo = fattura.get("metodo_pagamento") or ""
		conto = ((mappa or {}).get("conti") or {}).get(metodo)
		if conto in (None, ""):
			problemi.append(
				Problema(
					"Choose where Fatture in Cloud records the payments made by {0}: Settings > Invoicing > Fatture in Cloud",
					((fattura.get("metodi_in_parole") or {}).get(metodo, metodo),),
				)
			)
		else:
			voce.update(
				{"status": "paid", "paid_date": pagamento["pagato_il"], "payment_account": {"id": int(conto)}}
			)
	return voce


def _sistema_ts(
	fattura: dict, righe: list[dict], nomi: list[tuple[str, str]], problemi: list[Problema]
) -> dict:
	"""What Fatture in Cloud is told about the Sistema TS: nothing to send when it is
	reported from here, else the one kind of expense of the whole invoice."""
	ts = fattura.get("ts")
	if not ts:
		return {"ts_communication": False}
	tipi = sorted({riga.get("tipo_spesa") for riga in righe if riga.get("al_ts") and riga.get("tipo_spesa")})
	if len(tipi) > 1:
		problemi.append(
			Problema(
				"Fatture in Cloud reports one kind of expense per invoice to the Sistema TS, and this one has {0}: make two invoices, or report the Sistema TS from here (Settings > Invoicing > Fatture in Cloud)",
				(", ".join(tipi),),
			)
		)
	for indice, riga in enumerate(righe):
		if not riga.get("al_ts"):
			problemi.append(
				Problema(
					"Fatture in Cloud reports the whole invoice to the Sistema TS, and «{0}» does not go there: make two invoices, or report the Sistema TS from here (Settings > Invoicing > Fatture in Cloud)",
					(nomi[indice][0] or str(indice + 1),),
				)
			)
			break
	dati = {
		"ts_communication": True,
		"ts_tipo_spesa": tipi[0] if tipi else None,
		"ts_pagamento_tracciato": bool(ts.get("tracciato")),
		"ts_opposizione": bool(ts.get("opposizione")),
		"ts_full_amount": True,
	}
	bandiera = next((riga.get("bandiera_spesa") for riga in righe if riga.get("bandiera_spesa")), None)
	if bandiera and str(bandiera).isdigit():
		dati["ts_flag_tipo_spesa"] = int(bandiera)
	return dati


# --------------------------------------------------------------------- the totals

#: What is compared, in the order it is said: Fatture in Cloud's name, ours. The
#: total is not: how Fatture in Cloud counts a paper invoice's stamp duty in it is
#: its own, while what the client pays, the VAT and the withholding are the facts.
CONFRONTI = (
	(
		"amount_vat",
		"iva",
		"Fatture in Cloud makes the VAT {0}, here it is {1}: nothing was made in Fatture in Cloud",
	),
	(
		"amount_withholding_tax",
		"ritenuta",
		"Fatture in Cloud makes the withholding {0}, here it is {1}: nothing was made in Fatture in Cloud",
	),
	(
		"amount_due",
		"da_pagare",
		"Fatture in Cloud makes the amount to pay {0}, here it is {1}: nothing was made in Fatture in Cloud",
	),
)


def totali_diversi(nostri: dict, loro: dict) -> list[Problema]:
	"""Where Fatture in Cloud's sums are not ours, to the cent. The amounts go in the
	problem as numbers: the site writes them as the reader writes euros."""
	problemi = []
	for campo_loro, campo_nostro, frase in CONFRONTI:
		if campo_nostro not in nostri:
			continue
		a_loro = decimale((loro or {}).get(campo_loro))
		a_noi = decimale(nostri.get(campo_nostro))
		if a_loro != a_noi:
			problemi.append(Problema(frase, (a_loro, a_noi)))
	return problemi


# ------------------------------------------------------------------ the SdI states


def stato_sdi(ei_status: str | None) -> str | None:
	"""Our state for Fatture in Cloud's: None for one that moves nothing."""
	return STATI_SDI.get((ei_status or "").strip())


def finale(ei_status: str | None) -> bool:
	return (ei_status or "").strip() in FINALI


def da_correggere(ei_status: str | None) -> bool:
	return (ei_status or "").strip() in DA_CORREGGERE


# -------------------------------------------------------------- the companies


def aziende(risposta: dict) -> list[dict]:
	"""The companies the person who connected may invoice for, from `/user/companies`:
	their own and, for an accountant, the ones they look after."""
	trovate: dict[int, dict] = {}
	for azienda in ((risposta or {}).get("data") or {}).get("companies") or []:
		if azienda.get("type") == "company" and azienda.get("id") is not None:
			trovate[int(azienda["id"])] = azienda
		for seguita in azienda.get("controlled_companies") or []:
			if seguita.get("id") is not None:
				trovate.setdefault(int(seguita["id"]), seguita)
	return [
		{
			"id": identificativo,
			"name": azienda.get("name") or "",
			"vat_number": azienda.get("vat_number") or "",
			"tax_code": azienda.get("tax_code") or "",
		}
		for identificativo, azienda in sorted(
			trovate.items(), key=lambda voce: (voce[1].get("name") or "").lower()
		)
	]


def stessa_partita_iva(nostra: str | None, loro: str | None) -> bool:
	"""Whether the company in Fatture in Cloud is the one that issues here: the same
	VAT number, its country code or not. Nobody wrote ours yet: not ours to refuse."""
	nostra_ = "".join(carattere for carattere in (nostra or "").upper() if carattere.isalnum())
	loro_ = "".join(carattere for carattere in (loro or "").upper() if carattere.isalnum())
	if not nostra_ or not loro_:
		return True
	return nostra_.removeprefix("IT") == loro_.removeprefix("IT")
