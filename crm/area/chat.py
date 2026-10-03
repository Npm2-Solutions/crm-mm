# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The chat in the client area: administration only (design.md, "L'assistente",
point 6).

- **It says it is an AI**, above the conversation and on every answer (AI Act,
  art. 50).
- **An emergency first**: the words of one get 112 at once, in fixed words;
  nothing goes to the model or to anybody (`chat_regole.classifica`). Whatever the
  centre - a gym as much as a clinic - somebody may write that they feel ill.
- **Health is a person's**: a question about symptoms, medicines, results gets no
  answer from the chat, but the offer to pass it to the centre. Passed on, it is
  a question on the person's board (`CRM Area Message`, "Question"), which the
  desk reads and answers there; the desk hears of it in its notifications.
- **The rest from what the centre wrote**: its opening hours and closures, where
  bookings are, what it wants said and its frequent questions (Settings >
  Assistant). The model answers from that only; what it does not know it says,
  and offers a person too.
- **Nothing about the person goes to the model**: the question and the last
  turns of the conversation, not who asks. The conversation is not kept: the
  register keeps each answer, for the manager to read.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days, get_fullname, getdate, now_datetime, strip_html

from crm.area import CHAT, messaggi
from crm.area import chat_regole as C
from crm.area.api import _mia
from crm.assistente import modello
from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa
from crm.permissions import livelli
from crm.scheduling.timeutils import hhmm

SCOPO = (
	"Administrative support for the centre's clients: opening hours, bookings and the centre's "
	"frequent questions. Health questions go to a person."
)
GIORNI_CHIUSURE = 60
GIORNI = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

ISTRUZIONI = """{scopo}
You are the virtual assistant of {centro}: an AI, not a person. You answer one
of the centre's clients in their private area, only about the centre's
administration: opening hours, closures, bookings, and what the centre wrote
below. Use only that information and never make anything up.

Never talk about health: symptoms, medicines, doses, results, diagnoses, what to
do about a health problem. If the client asks about health, or asks something
the information below does not answer, say briefly that a person at the centre
can answer and set "handoff" to true; if it could be urgent, tell them to call
112. Keep answers short and plain, in the client's language.

Answer with JSON only: {{"answer": "...", "handoff": false}}

{contesto}"""


def _ora(valore) -> str:
	"""A Time as the database gives it (a timedelta) or as text: HH:MM."""
	return hhmm(valore) or ""


def _orari() -> list[str]:
	"""The studio's hours, day by day, as Settings > Agenda > Hours & shifts says."""
	cfg = frappe.get_cached_doc("CRM Scheduling Settings")
	per_giorno: dict[str, list[str]] = {}
	for riga in cfg.get("default_availability") or []:
		if riga.workday and riga.start_time and riga.end_time:
			per_giorno.setdefault(riga.workday, []).append(f"{_ora(riga.start_time)}-{_ora(riga.end_time)}")
	righe = [f"{giorno}: {', '.join(per_giorno[giorno])}" for giorno in GIORNI if giorno in per_giorno]
	chiusi = [giorno for giorno in GIORNI if giorno not in per_giorno]
	if righe and chiusi:
		righe.append(f"Closed: {', '.join(chiusi)}")
	return righe


def _chiusure() -> list[str]:
	"""The holidays of the next weeks, from the studio's holiday list."""
	lista = frappe.db.get_single_value("CRM Scheduling Settings", "default_holiday_list")
	if not lista or not frappe.db.exists("CRM Holiday List", lista):
		return []
	oggi = getdate()
	fine = add_days(oggi, GIORNI_CHIUSURE)
	righe = []
	for festa in frappe.get_cached_doc("CRM Holiday List", lista).get("holidays") or []:
		# the weekly day off is in the hours already
		if festa.weekly_off or not festa.date:
			continue
		giorno = getdate(festa.date)
		if oggi <= giorno <= fine:
			perche = strip_html(festa.description or "").strip()
			righe.append(giorno.isoformat() + (f" ({perche})" if perche else ""))
	return righe


def contesto() -> str:
	"""What the model knows of the centre: what the centre wrote, nothing else."""
	from crm.moduli.richieste import nome_del_centro

	cfg = modello.impostazioni()
	parti = [f"The centre: {nome_del_centro() or 'the centre'}"]
	orari = _orari()
	if orari:
		parti.append("Opening hours:\n" + "\n".join(orari))
	chiusure = _chiusure()
	if chiusure:
		parti.append("Closed on:\n" + "\n".join(chiusure))
	prenota = frappe.db.get_single_value("CRM Scheduling Settings", "online_booking_enabled")
	parti.append(
		"Bookings: the client's appointments are on the Agenda page of this area, where each can be "
		"moved or cancelled as the centre allows."
		+ (" New appointments can be booked online from the centre's booking page." if prenota else "")
	)
	if (cfg.get("chat_about") or "").strip():
		parti.append("What the centre wants you to know:\n" + cfg.chat_about.strip())
	domande = [
		f"Q: {riga.question.strip()}\nA: {riga.answer.strip()}"
		for riga in cfg.get("chat_faq") or []
		if (riga.question or "").strip() and (riga.answer or "").strip()
	]
	if domande:
		parti.append("Frequent questions:\n" + "\n\n".join(domande))
	return "\n\n".join(parti)


def _conversazione(storia: list[dict], domanda: str) -> str:
	chi = {"person": "Client", "assistant": "Assistant"}
	righe = [f"{chi[turno['role']]}: {turno['text']}" for turno in storia]
	return (
		"Conversation so far:\n" + "\n".join(righe) + "\n\n" if righe else ""
	) + f"The client asks: {domanda}"


def attiva() -> bool:
	"""On where the centre's plan has the assistant and the client area, the agency
	set the model up, and the centre turned the chat on."""
	from crm.area import MODULO as AREA
	from crm.assistente import MODULO

	moduli = livelli.moduli_attivi()
	return all(
		livelli.stato_modulo(m.chiave, moduli) == livelli.ATTIVO for m in (MODULO, AREA)
	) and modello.acceso(CHAT.chiave)


@frappe.whitelist()
def chat_status(person: str) -> dict:
	"""Whether the chat answers in this area."""
	_mia(person, anche_in_anteprima=True)
	return {"on": attiva()}


def _emergenza() -> dict:
	return {
		"kind": C.EMERGENZA,
		"answer": _(
			"If this is an emergency, call 112 now. The chat does not answer about health, and the centre "
			"may not read your message in time."
		),
		"can_pass": False,
	}


def _salute() -> dict:
	return {
		"kind": C.SALUTE,
		"answer": _(
			"Questions about your health are answered by a person, not by the chat. I can pass yours to the "
			"centre: they answer in your Messages. If it is urgent, call 112."
		),
		"can_pass": True,
	}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=40, seconds=60 * 60)
def ask(person: str, question: str, history: list | str | None = None) -> dict:
	"""One question to the chat: an emergency, a question for a person, or an answer
	from what the centre wrote."""
	_mia(person)
	domanda = (question or "").strip()[: C.MAX_DOMANDA]
	if not domanda:
		frappe.throw(_("Write your question"))
	# an emergency is answered before anything else, even with the chat off
	genere = C.classifica(domanda)
	if genere == C.EMERGENZA:
		return _emergenza()
	if not attiva():
		frappe.throw(_("The chat is not available: write to the centre in Messages"))
	if genere == C.SALUTE:
		return _salute()
	try:
		storia = C.storia(frappe.parse_json(history) if isinstance(history, str) else history)
	except ValueError:
		# a conversation that cannot be read is a conversation that starts now
		storia = []
	risposta = modello.chiedi(
		CHAT.chiave,
		ISTRUZIONI.format(scopo=SCOPO, centro=_centro(), contesto=contesto()),
		_conversazione(storia, domanda),
		json_atteso=True,
		riferimento=("CRM Lead", person),
	)
	letta = C.risposta(risposta.dati) if not risposta.errore else None
	if not letta:
		return {
			"kind": "unavailable",
			"answer": _("I cannot answer now. I can pass your question to the centre."),
			"can_pass": True,
		}
	modello.consegnata(risposta.evento)
	return {"kind": "answer", "answer": letta["answer"], "can_pass": letta["handoff"]}


def _centro() -> str:
	from crm.moduli.richieste import nome_del_centro

	return nome_del_centro() or "the centre"


def chi_avvisare() -> list[str]:
	"""Who hears of a question passed on: the desk; without one, whoever reads
	every person's board."""
	utenti = [
		utente
		for utente in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
		if utente not in ("Administrator", "Guest")
		and livelli.nel_crm(utente)
		and not livelli.e_agenzia(utente)
	]
	banco = [utente for utente in utenti if "segreteria" in livelli.livelli_di(utente)]
	return banco or [utente for utente in utenti if livelli.ambito("area.messaggi", utente) == livelli.CENTRO]


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def pass_on(person: str, question: str) -> dict:
	"""The person passes their question to the centre: a question on their board,
	read by the desk, answered there."""
	_mia(person)
	# only from the chat: the person does not write to the board otherwise
	if not attiva():
		frappe.throw(_("The chat is not available"))
	domanda = (question or "").strip()[: C.MAX_DOMANDA]
	if not domanda:
		frappe.throw(_("Write your question"))
	doc = frappe.get_doc(
		{
			"doctype": messaggi.MESSAGGIO,
			"lead": person,
			"kind": messaggi.DOMANDA,
			"author": frappe.session.user,
			"posted_on": now_datetime(),
			"body": domanda,
		}
	).insert(ignore_permissions=True)
	nome = frappe.db.get_value("CRM Lead", person, "lead_name") or person
	for utente in chi_avvisare():
		# the words stay on the board: the notification says only who asked
		avvisa(
			utente,
			"Area",
			N.DOMANDA_AREA,
			[nome],
			riguarda=("CRM Lead", person),
			oggetto=(messaggi.MESSAGGIO, doc.name),
		)
	return {"passed": True, "message": doc.name, "by": get_fullname(frappe.session.user)}
