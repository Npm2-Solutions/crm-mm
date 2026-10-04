# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's forms (Settings > Clients > Forms), through the forms' own code.

The manager published the privacy notice with its two consents and the welcome
questionnaire, both asked of everybody who has not signed them yet; the sheet the
physiotherapist writes after a session; the website's request form.

What is signed is signed today, with its PDF and its evidence: a signature is never
dated back. So the centre started with its forms this morning. The desk sent the link
to who comes in the next days, and many have already signed at home - opening the
link, asking for the code, reading it in their email (`crm.demo.registro.posta_per`:
nothing leaves), filling, signing - some stopped half-way, others have not opened it
yet; today's arrivals signed on the desk's tablet, and the reception desk still asks
the others when they come in; the physiotherapist wrote up the sheets of her last
sessions; a few people wrote from the website.
"""

from __future__ import annotations

import base64
import datetime
import io
import json
import re

import frappe
from frappe import _

from crm.demo import registro
from crm.demo.contesto import Contesto, indirizzo
from crm.demo.simulazione import numero, persone_della_demo

MODELLO = "CRM Form Template"

INFORMATIVA = {
	"sections": [
		{
			"id": "informativa",
			"title": "Informativa sul trattamento dei dati",
			"fields": [
				{
					"id": "testo",
					"type": "paragraph",
					"text": "Trattiamo i tuoi dati per prenotare e svolgere le prestazioni, per "
					"le fatture e per gli obblighi di legge. Restano al centro e nei sistemi che "
					"usa per gestirli; puoi chiedere in ogni momento di vederli, correggerli o "
					"cancellarli scrivendo alla segreteria.",
				},
				{
					"id": "letta",
					"type": "consent",
					"label": "Ho letto l'informativa",
					"consent_type": "privacy_notice",
					"must_accept": True,
				},
				{
					"id": "novita",
					"type": "consent",
					"label": "Novità e promemoria",
					"consent_type": "marketing",
					"required": True,
				},
				{"id": "firma", "type": "signature", "label": "Firma", "required": True},
			],
		}
	]
}

COME = ("Passaparola", "Google", "Instagram", "Il mio medico", "Passavo di qui")
QUANDO = ("Mattina", "Pausa pranzo", "Pomeriggio", "Sera", "Sabato")
OBIETTIVI = (
	"Tornare a correre senza dolore",
	"Stare meglio con la schiena in ufficio",
	"Perdere qualche chilo con calma",
	"Rimettermi in forma dopo la gravidanza",
	"Preparare la stagione di sci",
	"Muovermi di più, con qualcuno che mi segua",
)

BENVENUTO = {
	"sections": [
		{
			"id": "conoscerti",
			"title": "Per conoscerti",
			"fields": [
				{
					"id": "come",
					"type": "choice",
					"label": "Come ci hai conosciuto?",
					"options": [{"label": voce} for voce in COME],
					"required": True,
				},
				{"id": "obiettivo", "type": "text", "label": "Cosa vorresti ottenere?", "multiline": True},
				{
					"id": "quando",
					"type": "choice",
					"label": "Quando preferisci venire?",
					"options": [{"label": voce} for voce in QUANDO],
					"multiple": True,
				},
				{"id": "sport", "type": "yesno", "label": "Pratichi uno sport?"},
				{
					"id": "quale",
					"type": "text",
					"label": "Quale?",
					"show_if": [[{"field": "sport", "operator": "equals", "value": "1"}]],
				},
			],
		}
	]
}

FATTO = ("Terapia manuale", "Esercizi di mobilità", "Rinforzo", "Stretching", "Tecar")
NOTE_SEDUTA = (
	"Bene: meno rigidità del solito.",
	"Ripetere gli esercizi a casa due volte al giorno.",
	"Ancora fastidio alla fine: la prossima volta più leggeri.",
	"Ottima risposta, si può aumentare il carico.",
)

SCHEDA = {
	"sections": [
		{
			"id": "seduta",
			"title": "La seduta",
			"fields": [
				{
					"id": "fatto",
					"type": "choice",
					"label": "Cosa abbiamo fatto",
					"options": [{"label": voce} for voce in FATTO],
					"multiple": True,
					"required": True,
				},
				{"id": "casa", "type": "yesno", "label": "Esercizi da fare a casa"},
				{"id": "note", "type": "text", "label": "Note per la prossima volta", "multiline": True},
			],
		}
	]
}

SERVIZI_DEL_SITO = ("Fisioterapia", "Osteopatia", "Nutrizione", "Pilates", "Ginnastica posturale")

RICHIESTA_DAL_SITO = {
	"sections": [
		{
			"id": "contatti",
			"title": "Scrivici",
			"fields": [
				{
					"id": "nome",
					"type": "text",
					"label": "Nome e cognome",
					"person": "full_name",
					"required": True,
				},
				{"id": "email", "type": "text", "label": "Email", "person": "email", "required": True},
				{"id": "cellulare", "type": "text", "label": "Cellulare", "person": "mobile_no"},
				{
					"id": "interesse",
					"type": "choice",
					"label": "Cosa ti interessa",
					"options": [{"label": voce} for voce in SERVIZI_DEL_SITO],
					"required": True,
				},
				{"id": "messaggio", "type": "text", "label": "Messaggio", "multiline": True},
				{
					"id": "letta",
					"type": "consent",
					"label": "Ho letto l'informativa",
					"consent_type": "privacy_notice",
					"must_accept": True,
				},
				{
					"id": "novita",
					"type": "consent",
					"label": "Novità e promemoria",
					"consent_type": "marketing",
				},
			],
		}
	]
}

#: Who wrote from the website this morning: name, surname, the service, the message.
DAL_SITO = (
	(
		"Federica",
		"Orlandi",
		"Pilates",
		"Buongiorno, vorrei sapere se ci sono posti nel corso del martedì sera e quanto costa.",
	),
	(
		"Matteo",
		"Bellini",
		"Fisioterapia",
		"Ho una distorsione alla caviglia di due settimane fa: potete vedermi questa settimana?",
	),
	(
		"Silvia",
		"Fontana",
		"Nutrizione",
		"Vorrei un appuntamento con la nutrizionista, preferibilmente il sabato mattina.",
	),
)


def crea(ctx: Contesto) -> None:
	from crm.moduli import modelli

	ctx.avanza(_("Forms and consents"))
	manager = ctx.squadra("manager") or ctx.utente
	fatti = {}
	with ctx.come(manager):
		fatti["informativa"] = _pubblica(
			ctx,
			"informativa",
			"Informativa privacy e consensi",
			INFORMATIVA,
			use=modelli.FORMA,
			ask_on="First appointment",
			validity="Forever",
			send_before=2,
			description="L'informativa sul trattamento dei dati e il consenso alle novità: si "
			"firma una volta, alla prima visita.",
		)
		fatti["benvenuto"] = _pubblica(
			ctx,
			"benvenuto",
			"Questionario di benvenuto",
			BENVENUTO,
			use=modelli.FORMA,
			ask_on="First appointment",
			validity="Forever",
			send_before=2,
			description="Come ci ha conosciuto, cosa cerca, quando preferisce venire.",
		)
		fatti["scheda"] = _pubblica(
			ctx,
			"scheda",
			"Scheda della seduta",
			SCHEDA,
			use=modelli.SCHEDA,
			ask_on="By hand",
			description="Cosa si è fatto in seduta e cosa resta per la prossima volta.",
		)
		if modelli.puo_costruire(modelli.SITO):
			fatti["sito"] = _pubblica(
				ctx,
				"sito",
				"Richiedi informazioni",
				RICHIESTA_DAL_SITO,
				use=modelli.SITO,
				button_label="Invia",
				success_message="Grazie: ti rispondiamo entro un giorno lavorativo.",
			)
	firmati = _al_tablet(ctx, fatti)
	_col_link(ctx, fatti, firmati)
	_le_schede(ctx, fatti.get("scheda"))
	_dal_sito(ctx, fatti.get("sito"))


def _pubblica(ctx: Contesto, chiave: str, titolo: str, schema: dict, **campi) -> str:
	from crm.moduli import modelli

	fatto = modelli.save_template(title=titolo, schema=json.dumps(schema), enabled=1, **campi)
	modelli.publish_template(fatto["name"])
	ctx.ricorda(MODELLO, fatto["name"], f"form_template.{chiave}")
	return fatto["name"]


def _di_oggi(ctx: Contesto) -> list[dict]:
	"""Today's places of the demo's people, in the order they come: the person, the
	appointment, its service, whether they are in."""
	persone = persone_della_demo(ctx)
	if not persone:
		return []
	return frappe.db.sql(
		"""select p.party as lead, p.status, a.name as appuntamento, a.service, a.starts_on
		from `tabCRM Appointment Participant` p
		join `tabCRM Appointment` a on a.name = p.parent
		where p.parenttype = 'CRM Appointment' and p.party_type = 'CRM Lead'
			and p.party in %(persone)s and a.status != 'Cancelled' and p.status != 'Cancelled'
			and a.starts_on between %(dal)s and %(al)s
		order by a.starts_on, p.idx""",
		{
			"persone": persone,
			"dal": datetime.datetime.combine(ctx.oggi, datetime.time.min),
			"al": datetime.datetime.combine(ctx.oggi, datetime.time.max),
		},
		as_dict=True,
	)


def _al_tablet(ctx: Contesto, fatti: dict) -> set[str]:
	"""Today's arrivals had the tablet from the desk: they read the privacy notice,
	answered the questionnaire and signed; one in four was in a hurry and signs next
	time. Who is still on the way is asked when they come in. Returns who signed."""
	from crm.moduli import richieste

	desk = ctx.squadra("desk") or ctx.utente
	moduli = _da_mandare(fatti)
	firmati, visti = set(), set()
	for posto in _di_oggi(ctx):
		if not moduli or posto.status not in ("Arrived", "Attended") or posto.lead in visti:
			continue
		visti.add(posto.lead)
		if ctx.rng.random() < 0.25:
			continue
		with ctx.come(desk):
			try:
				consegna = richieste.hand_over_tablet(posto.lead, moduli, appointment=posto.appuntamento)
			except frappe.ValidationError:
				# a child, with nobody among the related people to answer for them
				frappe.clear_last_message()
				continue
		token = _token(consegna["url"])
		with ctx.come("Guest"):
			sessione = richieste.open_request(token)["session"]
			_compila(ctx, fatti, token, sessione)
		firmati.add(posto.lead)
	return firmati


def _da_mandare(fatti: dict) -> list[str]:
	return [fatti[chiave] for chiave in ("informativa", "benvenuto") if fatti.get(chiave)]


def _compila(ctx: Contesto, fatti: dict, token: str, sessione: str, a_meta: bool = False) -> None:
	"""The forms of a link, as the page fills them: each opened, answered, signed - or,
	``a_meta``, the first one answered in part and left there."""
	from crm.moduli import richieste

	chiavi = {nome: chiave for chiave, nome in fatti.items()}
	for voce in richieste.get_request_forms(token, sessione)["forms"]:
		if voce["status"] not in richieste.APERTE:
			continue
		richieste.get_request_form(token, voce["id"], sessione)
		chiave = chiavi.get(frappe.db.get_value(richieste.RICHIESTA, voce["id"], "template"))
		risposte = RISPOSTE[chiave](ctx) if chiave in RISPOSTE else {}
		if a_meta:
			parziali = dict(list(risposte.items())[: max(1, len(risposte) // 2)])
			richieste.save_request_answers(token, voce["id"], json.dumps(parziali), sessione)
			return
		richieste.save_request_answers(token, voce["id"], json.dumps(risposte), sessione)
		if voce["sign_at_desk"]:
			richieste.finish_request(token, voce["id"], json.dumps(risposte), sessione)
			continue
		firme = {"firma": _tratto(ctx)} if chiave == "informativa" else {}
		richieste.sign_request(token, voce["id"], json.dumps(risposte), json.dumps(firme), sessione)


def _risposte_informativa(ctx: Contesto) -> dict:
	return {"letta": True, "novita": ctx.rng.random() < 0.7}


def _risposte_benvenuto(ctx: Contesto) -> dict:
	sport = ctx.rng.random() < 0.5
	risposte = {
		"come": ctx.scegli_pesato(((COME[0], 5), (COME[1], 3), (COME[2], 2), (COME[3], 2), (COME[4], 1))),
		"obiettivo": ctx.rng.choice(OBIETTIVI),
		"quando": sorted(ctx.rng.sample(QUANDO, ctx.rng.randint(1, 2)), key=QUANDO.index),
		"sport": sport,
	}
	if sport:
		risposte["quale"] = ctx.rng.choice(("Corsa", "Calcetto", "Nuoto", "Tennis", "Ciclismo"))
	return risposte


RISPOSTE = {"informativa": _risposte_informativa, "benvenuto": _risposte_benvenuto}


def _col_link(ctx: Contesto, fatti: dict, firmati: set[str]) -> None:
	"""This morning the desk sent the link to who comes in the next days, as the
	templates ask: half of them have already signed at home, a few stopped half-way,
	the others have not opened it yet."""
	from crm.moduli import richieste

	desk = ctx.squadra("desk") or ctx.utente
	moduli = _da_mandare(fatti)
	persone = persone_della_demo(ctx)
	if not moduli or not persone:
		return
	prossimi = frappe.db.sql(
		"""select p.party as lead, min(a.name) as appuntamento
		from `tabCRM Appointment Participant` p
		join `tabCRM Appointment` a on a.name = p.parent
		where p.parenttype = 'CRM Appointment' and p.party_type = 'CRM Lead'
			and p.party in %(persone)s and a.status != 'Cancelled' and p.status != 'Cancelled'
			and a.starts_on > %(dal)s and a.starts_on <= %(al)s
		group by p.party order by min(a.starts_on)""",
		{
			"persone": persone,
			"dal": ctx.adesso,
			"al": datetime.datetime.combine(ctx.giorno(7), datetime.time.max),
		},
		as_dict=True,
	)
	for riga in [riga for riga in prossimi if riga.lead not in firmati][: ctx.quanti(30)]:
		with ctx.come(desk):
			try:
				richieste.send_form_link(riga.lead, moduli, appointment=riga.appuntamento)
			except frappe.ValidationError:
				# nobody to send it to: the desk hands over the tablet when they come
				frappe.clear_last_message()
				continue
		caso = ctx.rng.random()
		if caso < 0.3:
			continue
		# the person opens the email, then the link, asks for the code and types it
		email = richieste.destinatario(riga.lead).get("email")
		token = _token(_ultima(email)["message"])
		with ctx.come("Guest"):
			richieste.open_request(token)
			richieste.send_code(token)
			sessione = richieste.verify_code(token, _il_codice(_ultima(email)))["session"]
			_compila(ctx, fatti, token, sessione, a_meta=caso < 0.42)


def _ultima(email: str | None) -> dict:
	"""The last email the demo person had: what the link and the code are read from."""
	posta = registro.posta_per(email or "")
	if not posta:
		raise frappe.ValidationError(f"No email for {email}")
	return posta[-1]


def _token(testo: str) -> str:
	return re.search(r"/modulo/([A-Za-z0-9_-]+)", testo).group(1)


def _il_codice(email: dict) -> str:
	return re.search(r"\b(\d{6})\b", f"{email['subject']} {email['message']}").group(1)


def _le_schede(ctx: Contesto, scheda: str | None) -> None:
	"""The physiotherapist wrote up the sheets of her last sessions: the ones done
	today, and those of the last two days she had not written yet."""
	from crm.moduli import compilazioni

	fisio = ctx.trova("service.fisio")
	giulia = ctx.squadra("giulia")
	persone = persone_della_demo(ctx)
	if not scheda or not fisio or not giulia or not persone:
		return
	sedute = frappe.db.sql(
		"""select p.party as lead, a.name as appuntamento
		from `tabCRM Appointment Participant` p
		join `tabCRM Appointment` a on a.name = p.parent
		where p.parenttype = 'CRM Appointment' and p.party_type = 'CRM Lead'
			and p.party in %(persone)s and a.service = %(fisio)s
			and p.status in ('Arrived', 'Attended') and a.status != 'Cancelled'
			and a.starts_on between %(dal)s and %(al)s
		order by a.starts_on desc""",
		{
			"persone": persone,
			"fisio": fisio,
			"dal": datetime.datetime.combine(ctx.giorno(-2), datetime.time.min),
			"al": ctx.adesso,
		},
		as_dict=True,
	)
	for seduta in sedute[: ctx.quanti(14)]:
		risposte = {
			"fatto": sorted(ctx.rng.sample(FATTO, ctx.rng.randint(2, 3)), key=FATTO.index),
			"casa": ctx.rng.random() < 0.6,
			"note": ctx.rng.choice(NOTE_SEDUTA),
		}
		with ctx.come(giulia):
			modulo = compilazioni.start_form(seduta.lead, scheda, appointment=seduta.appuntamento)
			compilazioni.sign_form(modulo["name"], json.dumps(risposte), json.dumps({}))


def _dal_sito(ctx: Contesto, sito: str | None) -> None:
	"""This morning's requests from the website, sent through the page's own path:
	the person found or made, their answers kept as their form, the consents, the
	deal."""
	from crm.moduli import sito as pagina

	if not sito:
		return
	modello = frappe.get_doc(MODELLO, sito)
	for nome, cognome, servizio, messaggio in DAL_SITO[: ctx.quanti(len(DAL_SITO))]:
		risposte = {
			"nome": f"{nome} {cognome}",
			"email": _indirizzo_libero(nome, cognome),
			"cellulare": _cellulare_libero(ctx),
			"interesse": servizio,
			"messaggio": messaggio,
			"letta": True,
			"novita": ctx.rng.random() < 0.6,
		}
		with ctx.come("Guest"):
			fatto = pagina.manda(modello, risposte)
		# the PDF a job would make once the page answered
		if fatto.get("form"):
			pagina.fai_il_pdf(fatto["form"])


def _indirizzo_libero(nome: str, cognome: str) -> str:
	"""A demo address nobody has yet: the page would find its owner, and book for them."""
	for coda in (0, *range(2, 100)):
		email = indirizzo(nome, cognome, coda)
		if not frappe.db.exists("Contact Email", {"email_id": email}):
			return email
	return indirizzo(nome, cognome, 100)


def _cellulare_libero(ctx: Contesto) -> str:
	"""A demo mobile nobody has yet, for the same reason."""
	while True:
		cellulare = numero(ctx)
		if not frappe.db.exists("Contact Phone", {"phone": cellulare}):
			return cellulare


def _tratto(ctx: Contesto) -> str:
	"""A signature's stroke as the tablet sends it: a PNG, a little different each time."""
	from PIL import Image, ImageDraw

	immagine = Image.new("RGBA", (320, 110), (255, 255, 255, 0))
	matita = ImageDraw.Draw(immagine)
	x, y = 14, ctx.rng.randint(60, 80)
	punti = [(x, y)]
	while x < 300:
		x += ctx.rng.randint(14, 30)
		y = max(15, min(95, y + ctx.rng.randint(-28, 28)))
		punti.append((x, y))
	matita.line(punti, fill=(25, 25, 60, 255), width=3, joint="curve")
	memoria = io.BytesIO()
	immagine.save(memoria, format="PNG")
	return "data:image/png;base64," + base64.b64encode(memoria.getvalue()).decode()
