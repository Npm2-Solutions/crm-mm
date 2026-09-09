# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The last ten centimetres: sending to the Sistema TS.

Everything up to here is one pipeline. This module is the only part that changes
between the three modes, and it holds three rules:

1. **Nobody is born here.** A company starts in `export`, and `export` stays a
   working, tested path even when every company is on automatic - it is the plan B
   of every other failure, including this file being unreachable.
2. **A failure here never stops invoicing.** The patient has their invoice whether
   or not the Sistema TS answers. Nothing on the issue path calls this.
3. **Demotion is loud.** An expired PINCODE, a changed mandate, a 105 or a 106
   sends the company back to `export` with an alert. It does not retry, and it does
   not go quiet.

Authentication is **preemptive** HTTP Basic: the service does not issue a 401
challenge, so the header goes out with the first request. And the rule that is not
negotiable anywhere in here: **credentials never appear in a log or in an error
message.** A traceback that prints a doctor's PINCODE is a data breach, not an
inconvenience.
"""

from __future__ import annotations

import time

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils.password import get_decrypted_password

from crm.invoicing import documento, ts
from crm.invoicing.engine.codici import (
	CODICE_DELEGA_ASSENTE,
	CODICE_DELEGA_PRESENTE,
	CODICI_RETROCESSIONE,
	descrivi_esito,
)
from crm.invoicing.engine.sistema_ts import (
	OPERAZIONE_DA_FLAG,
	Ambiente,
	Credenziali,
	Esito,
	Operazione,
	analizza_risposta,
	canale_per_modalita,
	costruisci_busta,
	destinazione,
	soap_action,
)

#: HTTP statuses worth retrying: the service is down, the request is not wrong.
STATI_RITENTABILI = frozenset({429, 500, 502, 503, 504})

TENTATIVI = 3
ATTESA_INIZIALE = 2.0
FATTORE_BACKOFF = 2.0
TIMEOUT = 30.0


class ErroreTrasporto(Exception):
	"""The Sistema TS could not be reached, or answered something unusable."""

	def __init__(self, messaggio: str, stato: int | None = None):
		self.stato = stato
		super().__init__(messaggio)


def _credenziali(emittente: dict) -> Credenziali:
	"""Read the credentials. They are the practice's, and they are never logged."""
	nome = emittente.get("name")
	utente = emittente.get("ts_username")
	password = get_decrypted_password("CRM Invoicing Company", nome, "ts_password", raise_exception=False)
	pincode = get_decrypted_password("CRM Invoicing Company", nome, "ts_pincode", raise_exception=False)
	if not (utente and password and pincode):
		raise ErroreTrasporto(
			_("The Sistema TS credentials for {0} are incomplete. Submission stays on export.").format(nome)
		)
	return Credenziali(
		utente=utente,
		password=password,
		pincode=pincode,
		# On the Entratel channel: `codicefiscale-sedetelematica`.
		opzionale1=emittente.get("ts_intermediary_reference") or None,
	)


def _ambiente() -> str:
	"""Test until somebody says otherwise. Production is an explicit act."""
	valore = (frappe.conf.get("sistema_ts_ambiente") or "test").strip().lower()
	return Ambiente.PRODUZIONE if valore.startswith("prod") else Ambiente.TEST


def _post(url: str, corpo: bytes, intestazioni: dict, credenziali: Credenziali) -> bytes:
	attesa = ATTESA_INIZIALE
	ultimo: Exception | None = None
	sessione = frappe.utils.get_request_session()
	for tentativo in range(1, TENTATIVI + 1):
		try:
			risposta = sessione.post(
				url,
				data=corpo,
				headers=intestazioni,
				# requests sends Basic preemptively; the service never challenges.
				auth=(credenziali.utente, credenziali.password),
				timeout=TIMEOUT,
				allow_redirects=False,
			)
		except Exception as errore:
			# The message may carry the URL but never the credentials: they are in the
			# auth tuple, not in the string.
			ultimo = ErroreTrasporto(_("The Sistema TS is unreachable: {0}").format(errore))
		else:
			if risposta.status_code == 200:
				return risposta.content
			if risposta.status_code == 401:
				# Never a network problem: either the credentials are wrong, or the
				# wrong family of endpoints is being called. The three are not
				# interchangeable.
				raise ErroreTrasporto(
					_(
						"401 from the Sistema TS: the credentials are not valid, or this is the wrong "
						"channel. The three channels are not interchangeable."
					),
					stato=401,
				)
			if risposta.status_code not in STATI_RITENTABILI:
				raise ErroreTrasporto(
					_("The Sistema TS answered {0}").format(risposta.status_code),
					stato=risposta.status_code,
				)
			ultimo = ErroreTrasporto(
				_("The Sistema TS answered {0}").format(risposta.status_code),
				stato=risposta.status_code,
			)
		if tentativo < TENTATIVI:
			time.sleep(attesa)
			attesa *= FATTORE_BACKOFF
	raise ultimo or ErroreTrasporto(_("Submission to the Sistema TS failed"))


def invia_documento(nome_fattura: str, operazione: str | None = None) -> dict:
	"""Send one issued invoice synchronously.

	Synchronous on purpose: the answer comes back the same day, not on 20 January
	with four thousand rows behind it. It is also what makes the mandate probe
	possible at all - the first real document tells the truth (`sonda_delega`).
	"""
	fattura = frappe.get_doc("CRM Invoice", nome_fattura)
	fattura.check_permission("submit")
	if fattura.docstatus != 1:
		frappe.throw(_("Only an issued invoice can be reported"))
	if fattura.ts_status not in ("da_inviare", "pronto_export", "scartato"):
		frappe.throw(_("This invoice is in state {0}: there is nothing to send").format(fattura.ts_status))

	emittente = documento.azienda(fattura)
	modalita = emittente.get("ts_mode") or "export"
	if modalita == "export":
		frappe.throw(
			_(
				"This company submits in export mode: prepare the file and upload it from the "
				"Sistema TS portal. Switch the mode once the credentials are in."
			)
		)

	spesa = ts.documento_spesa(fattura, emittente)
	esito_validazione = ts.verifica(fattura, emittente)
	if esito_validazione.errori:
		frappe.throw(
			"<br>".join(esito_validazione.errori), title=_("The document does not pass the tracciato")
		)

	scelta = Operazione(
		{
			"I": Operazione.INSERIMENTO,
			"V": Operazione.VARIAZIONE,
			"R": Operazione.RIMBORSO,
			"C": Operazione.CANCELLAZIONE,
		}[operazione or fattura.ts_operation or "I"]
	)
	dove = destinazione(canale_per_modalita(modalita), _ambiente())
	credenziali = _credenziali(emittente)
	busta = costruisci_busta(spesa, credenziali, dove, ts.cifratore(emittente), scelta)

	intestazioni = {
		"Content-Type": "text/xml; charset=utf-8",
		"SOAPAction": f'"{soap_action(scelta)}"',
	}
	try:
		risposta = _post(dove.url_sincrono, busta, intestazioni, credenziali)
	except ErroreTrasporto as errore:
		documento.registra(fattura, "ts_sent", str(errore), stato="errore")
		frappe.throw(str(errore), title=_("Sistema TS"))

	esito = analizza_risposta(risposta)
	_registra_esito(fattura, emittente, esito, modalita)
	return {
		"accepted": esito.accolto,
		"protocol": esito.protocollo,
		"codes": esito.codici_errore,
		"summary": esito.riassunto(),
	}


def _registra_esito(fattura, emittente: dict, esito: Esito, modalita: str) -> None:
	"""Write the outcome onto the invoice, and act on what it says about the mode."""
	if esito.accolto:
		fattura.db_set(
			{"ts_status": "accolto", "ts_year": fattura.ts_year or getdate(fattura.payment_date).year},
			update_modified=False,
		)
		documento.registra(
			fattura,
			"ts_accepted",
			esito.riassunto(),
			stato="accolto",
			payload={"protocol": esito.protocollo},
		)
		return

	fattura.db_set("ts_status", "scartato", update_modified=False)
	documento.registra(
		fattura,
		"ts_rejected",
		esito.riassunto(),
		stato="scartato",
		payload={"codes": esito.codici_errore},
	)
	_reagisci_ai_codici(emittente, esito, modalita)


def _reagisci_ai_codici(emittente: dict, esito: Esito, modalita: str) -> None:
	"""105 and 106 are answers, not failures.

	Nobody has to be asked who transmitted last year - practices answer it wrong
	without meaning to, they simply do not know. The Sistema TS says so
	unambiguously, and the company is moved to match rather than left guessing.
	"""
	codici = set(esito.codici_errore)
	azienda = emittente.get("name")

	if CODICE_DELEGA_ASSENTE in codici:
		_retrocedi(azienda, "assente", _("Sent on behalf of, with no active mandate (105)."))
	elif CODICE_DELEGA_PRESENTE in codici:
		_retrocedi(azienda, "presente", _("Sent in own name while a mandate is active (106)."))
	elif codici & CODICI_RETROCESSIONE:
		codice = sorted(codici & CODICI_RETROCESSIONE)[0]
		_retrocedi(azienda, None, descrivi_esito(codice))


def _retrocedi(azienda: str, delega: str | None, motivo: str) -> None:
	"""Back to `export`, with an alert. Invoicing does not stop for the last mile."""
	valori = {"ts_mode": "export"}
	if delega:
		valori["ts_delegation_status"] = delega
	frappe.db.set_value("CRM Invoicing Company", azienda, valori)
	from crm.invoicing.monitoraggio import avvisa

	avvisa(
		_("Sistema TS submission back to export"),
		azienda,
		_("{0} Submission is back on export until the configuration is fixed; invoicing continues.").format(
			motivo
		),
	)


def sonda_delega(azienda: str) -> dict:
	"""Find out whether an Entratel mandate exists, by trying.

	The first real document is sent in the practice's own name and the answer is
	read: `105` means there is no mandate, `106` means there is one. The alternative
	is asking, and the answer to that question is wrong often enough to be useless.
	"""
	if not frappe.db.exists("CRM Invoicing Company", azienda):
		frappe.throw(_("Unknown company {0}").format(azienda))
	emittente = frappe.get_cached_doc("CRM Invoicing Company", azienda).as_dict()
	candidata = frappe.db.get_value(
		"CRM Invoice",
		{"company": azienda, "docstatus": 1, "ts_status": ["in", ("da_inviare", "pronto_export")]},
		"name",
		order_by="posting_date asc",
	)
	if not candidata:
		return {
			"probed": False,
			"reason": _("No document waiting: the probe needs one real document to send."),
			"delegation": emittente.get("ts_delegation_status"),
		}
	esito = invia_documento(candidata)
	return {
		"probed": True,
		"invoice": candidata,
		"delegation": frappe.db.get_value("CRM Invoicing Company", azienda, "ts_delegation_status"),
		"summary": esito["summary"],
	}
