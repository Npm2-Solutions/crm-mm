# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Telnyx's REST API (v2) through `requests`: JSON in, JSON out (doc 65).

No SDK: a few dozen calls, and one dependency less on the bench. The key travels
in variables named ``*_secret``, which a traceback hides, and an error is logged
with Telnyx's status and code only - never the key, never the body. A fake Telnyx
in the tests stands in for `_trasporto`.
"""

from __future__ import annotations

import frappe
import requests

API = "https://api.telnyx.com/v2/"
ATTESA = 20
#: The most rows Telnyx gives a page of most lists, and how many pages DottorCloud
#: reads at most: a centre's account holds tens of numbers, not thousands.
PAGINA, PAGINE = 250, 20


def _api() -> str:
	"""Telnyx's address; on a test bench, a fake Telnyx's (``telnyx_api`` in the site's
	config, never set on a centre's site)."""
	return frappe.conf.get("telnyx_api") or API


class ErroreTelnyx(Exception):
	"""Telnyx refused, or did not answer (``stato`` None): its HTTP status, its own
	code ("10009", "40300"), its title and detail."""

	def __init__(
		self,
		stato: int | None,
		codice: str | int | None = None,
		titolo: str | None = None,
		dettaglio: str | None = None,
	):
		self.stato, self.codice, self.titolo, self.dettaglio = stato, codice, titolo, dettaglio
		super().__init__(f"Telnyx {stato} {codice or ''} {titolo or ''}".strip())

	def in_parole(self) -> str:
		"""What went wrong, in the reader's words."""
		from frappe import _

		from crm.telephony.telnyx import errori
		from crm.telephony.telnyx import errori_regole as E
		from crm.telephony.telnyx import regole as R

		if self.stato not in (None, 401, 403) and E.frase(self.codice):
			return errori.in_parole(self.codice)
		frase, argomenti = R.errore_in_parole(self.stato, self.codice, self.dettaglio)
		return _(frase).format(*argomenti)


def _trasporto(
	metodo: str,
	indirizzo: str,
	intestazioni: dict,
	parametri,
	corpo: dict | None,
	file: dict | None,
	dati: dict | None,
	attesa: int,
):
	"""One HTTP request: (status, JSON) - or its text, for the one answer that is
	not JSON (a browser's token). Replaced by the tests' fake Telnyx."""
	risposta = requests.request(
		metodo,
		indirizzo,
		headers=intestazioni,
		params=parametri,
		json=corpo,
		files=file,
		data=dati,
		timeout=attesa,
	)
	try:
		risposto = risposta.json()
	except ValueError:
		risposto = risposta.text or ""
	return risposta.status_code, risposto


def chiama(
	metodo: str,
	percorso: str,
	telnyx_secret: str,
	parametri=None,
	corpo: dict | None = None,
	file: dict | None = None,
	dati: dict | None = None,
	attesa: int = ATTESA,
) -> dict | str:
	"""Ask Telnyx; the answer's JSON (its text, when it is not JSON), or
	`ErroreTelnyx`."""
	intestazioni = {"Authorization": f"Bearer {telnyx_secret}", "Accept": "application/json"}
	try:
		stato, risposto = _trasporto(
			metodo,
			_api() + percorso.lstrip("/"),
			intestazioni,
			parametri,
			corpo,
			file,
			dati,
			attesa,
		)
	except requests.RequestException as errore:
		raise ErroreTelnyx(None) from errore
	if stato >= 400:
		errori = (risposto or {}).get("errors") if isinstance(risposto, dict) else None
		primo = errori[0] if errori and isinstance(errori[0], dict) else {}
		raise ErroreTelnyx(stato, primo.get("code"), primo.get("title"), primo.get("detail"))
	if isinstance(risposto, dict | str):
		return risposto
	# a bare list: requirement groups come without the `data` around them
	return {"data": risposto}


def tutte(percorso: str, telnyx_secret: str, parametri: dict | None = None, pagina: int = PAGINA) -> list:
	"""Every row of a list, page after page, at most `PAGINE` pages."""
	righe = []
	for numero in range(1, PAGINE + 1):
		risposto = chiama(
			"GET",
			percorso,
			telnyx_secret,
			parametri={**(parametri or {}), "page[number]": numero, "page[size]": pagina},
		)
		righe.extend(risposto.get("data") or [])
		meta = risposto.get("meta") or {}
		totale = meta.get("total_pages")
		if not risposto.get("data") or (totale is not None and numero >= int(totale)):
			break
		if totale is None and len(risposto.get("data") or []) < pagina:
			break
	return righe


def registra(titolo: str, errore: Exception) -> None:
	"""An error of Telnyx's in the log, with its status and code and never the key."""
	stato = getattr(errore, "stato", "")
	codice = getattr(errore, "codice", "")
	frappe.log_error(title=titolo, message=f"{type(errore).__name__} {stato} {codice}"[:1000])
