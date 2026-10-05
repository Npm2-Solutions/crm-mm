# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's clinical record, through the clinic's own code.

The medical director joined the team and built the clinical sheets: the
physiotherapist's first visit and the dietitian's. This morning the practitioners
wrote in the record the visits of the last weeks from their notes - each on the day it
was, signed today: a signature is never dated back - and every visit has its report.
The physiotherapist added a line for the sessions after, and an addendum after a phone
call; the osteopath wrote his visits freely, one only for his discipline.

What the sheets proposed for the summary was mostly confirmed, now and then thrown
away, a few left to decide; the dietitian wrote a blood pressure by hand. The people
gave their consent to the health dossier and to the online reports; one asked that an
episode stay with whoever wrote it, and the director obscured it. The dietitian opened
the record of somebody she does not follow, with her reason. The desk filed the
reports people brought - a scan, the blood tests - and the director a prescription;
one visit's report was given online and downloaded. The practitioners wrote on the
board of who has the area, and read the records before their sessions: the access
log has them.
"""

from __future__ import annotations

import datetime
import json
import re

import frappe
from frappe import _
from frappe.utils import escape_html, formatdate, getdate

from crm.clinica.demo import dati as D
from crm.demo.base import collega
from crm.demo.contesto import Contesto
from crm.demo.simulazione import persone_della_demo, visti_da

RECORD = "Clinic Record"
MODELLO = "CRM Form Template"
DOCUMENTO = "CRM Document"


def crea(ctx: Contesto) -> None:
	ctx.avanza(_("Clinical record"))
	direttrice = collega(ctx, *D.DIRETTRICE)
	schede = _schede(ctx, direttrice)
	scritte = []
	scritte += _fisioterapia(ctx, schede.get("fisio"))
	scritte += _osteopatia(ctx)
	scritte += _nutrizione(ctx, schede.get("nutrizione"))
	ctx.salva()
	_sintesi(ctx, scritte)
	consensi_alla_visita(ctx, scritte)
	_oscura(ctx, direttrice, scritte)
	_fuori_equipe(ctx, scritte)
	ctx.salva()
	_documenti(ctx, direttrice, scritte)
	_online(ctx, scritte)
	_di_cura(ctx, scritte)
	_letture(ctx, direttrice, scritte)


def pubblica_scheda(
	ctx: Contesto, chi: str, chiave: str, titolo: str, schema: dict, specialita: str, descrizione: str
) -> str:
	"""A clinical sheet as the forms' builder publishes it; the dentist's part
	publishes its own so too."""
	from crm.moduli import modelli

	with ctx.come(chi):
		fatto = modelli.save_template(
			title=titolo,
			schema=json.dumps(schema),
			use=modelli.SCHEDA,
			clinical=1,
			specialty=specialita,
			description=descrizione,
			enabled=1,
		)
		modelli.publish_template(fatto["name"])
	ctx.ricorda(MODELLO, fatto["name"], f"clinic_sheet.{chiave}")
	return fatto["name"]


def _schede(ctx: Contesto, direttrice: str) -> dict[str, str]:
	"""The director builds the clinical sheets of the first visits."""
	return {
		"fisio": pubblica_scheda(
			ctx,
			direttrice,
			"fisio",
			"Valutazione fisioterapica",
			D.SCHEDA_FISIO,
			"Fisioterapia",
			"La prima visita del fisioterapista: il motivo, l'anamnesi, i test, il piano.",
		),
		"nutrizione": pubblica_scheda(
			ctx,
			direttrice,
			"nutrizione",
			"Prima visita nutrizionale",
			D.SCHEDA_NUTRIZIONE,
			"Nutrizione",
			"Le misure con l'indice di massa corporea, le abitudini, l'obiettivo.",
		),
	}


def appuntamenti(ctx: Contesto, servizio: str, utente: str | None, giorni: int) -> list:
	"""Where ``utente`` saw the demo's people for ``servizio`` in the last ``giorni``
	days and they came: one a person, the most recent first."""
	nome = ctx.trova(f"service.{servizio}")
	persone = persone_della_demo(ctx)
	if not (nome and utente and persone):
		return []
	righe = frappe.db.sql(
		"""select a.name as appointment, p.party as lead, a.starts_on, a.ends_on
		from `tabCRM Appointment` a
		join `tabCRM Appointment Staff` s on s.parent = a.name and s.parenttype = 'CRM Appointment'
		join `tabCRM Appointment Participant` p on p.parent = a.name and p.parenttype = 'CRM Appointment'
		where a.service = %(servizio)s and s.user = %(utente)s and p.party_type = 'CRM Lead'
		and p.party in %(persone)s and p.status = 'Attended' and a.status != 'Cancelled'
		and a.ends_on between %(da)s and %(adesso)s
		order by a.ends_on desc, a.name""",
		{
			"servizio": nome,
			"utente": utente,
			"persone": persone,
			"da": ctx.giorno(-giorni),
			"adesso": ctx.adesso,
		},
		as_dict=True,
	)
	visti, unici = set(), []
	for riga in righe:
		if riga.lead not in visti:
			visti.add(riga.lead)
			unici.append(riga)
	return unici


def anamnesi(ctx: Contesto) -> dict:
	"""What a person says of their allergies, medicines and illnesses."""
	return {
		"allergie": ctx.scegli_pesato(D.ALLERGIE),
		"farmaci": ctx.scegli_pesato(D.FARMACI),
		"patologie": ctx.scegli_pesato(D.PATOLOGIE),
	}


def visita_sulla_scheda(lead: str, scheda: str, appuntamento: str, quando, risposte: dict) -> str:
	"""A visit on a clinical sheet, as the Clinic tab writes it: started from the
	appointment, dated when it was, signed now."""
	from crm.clinica import cartella

	riga = cartella.start_sheet(lead, scheda, appuntamento)
	fatto = cartella.save_record(
		lead,
		name=riga["name"],
		kind="Visit",
		visibility="Care team",
		record_date=str(quando),
		answers=json.dumps(risposte, ensure_ascii=False),
		sign=1,
	)
	return fatto["name"]


def _scritta(lead: str, chi: str, utente: str, record: str, quando, motivo: str | None = None) -> dict:
	return {"lead": lead, "chi": chi, "utente": utente, "record": record, "quando": quando, "motivo": motivo}


# -- the visits -----------------------------------------------------------------------------


def _fisioterapia(ctx: Contesto, scheda: str | None) -> list[dict]:
	"""The physiotherapist's first visits on the sheet; a line for the sessions after;
	an addendum after a phone call."""
	from crm.clinica import cartella

	giulia = ctx.squadra("giulia")
	if not (giulia and scheda):
		return []
	scritte = []
	with ctx.come(giulia):
		for visita in appuntamenti(ctx, "prima_fisio", giulia, 30)[: ctx.quanti(12)]:
			motivo = ctx.rng.choice(list(D.FISIO))
			test, valutazione, piano = D.FISIO[motivo]
			risposte = {
				"motivo": motivo,
				"da_quando": ctx.rng.choice(D.DA_QUANDO),
				"dolore": ctx.rng.randint(3, 8),
				**anamnesi(ctx),
				"test": test,
				"valutazione": valutazione,
				"piano": piano,
			}
			record = visita_sulla_scheda(visita.lead, scheda, visita.appointment, visita.ends_on, risposte)
			scritte.append(_scritta(visita.lead, "giulia", giulia, record, visita.ends_on, motivo))
		for seduta in appuntamenti(ctx, "fisio", giulia, 21)[: ctx.quanti(10)]:
			cartella.save_record(
				seduta.lead,
				content=f"<p>{escape_html(ctx.rng.choice(D.NOTE_DI_SEDUTA))}</p>",
				kind="Note",
				record_date=str(seduta.ends_on),
				sign=1,
			)
		if scritte:
			prima = scritte[-1]
			cartella.save_record(
				prima["lead"],
				content=f"<p>{escape_html(D.ADDENDUM)}</p>",
				kind="Note",
				addendum_to=prima["record"],
				sign=1,
			)
	return scritte


def _osteopatia(ctx: Contesto) -> list[dict]:
	"""The osteopath's first visits, written freely; one only for his discipline."""
	from crm.clinica import cartella

	luca = ctx.squadra("luca")
	scritte = []
	with ctx.come(luca):
		for posizione, visita in enumerate(appuntamenti(ctx, "prima_osteo", luca, 30)[: ctx.quanti(8)]):
			motivo, storia, reperti, trattamento = D.OSTEO[posizione % len(D.OSTEO)]
			contenuto = "".join(
				f"<p><strong>{escape_html(titolo)}</strong><br>{escape_html(testo)}</p>"
				for titolo, testo in (
					("Motivo", motivo),
					("Storia", storia),
					("Valutazione", reperti),
					("Trattamento", trattamento),
				)
			)
			fatto = cartella.save_record(
				visita.lead,
				content=contenuto,
				kind="Visit",
				visibility="My discipline" if posizione % 4 == 3 else "Care team",
				record_date=str(visita.ends_on),
				sign=1,
			)
			scritte.append(_scritta(visita.lead, "luca", luca, fatto["name"], visita.ends_on, motivo))
	return scritte


def _nutrizione(ctx: Contesto, scheda: str | None) -> list[dict]:
	"""The dietitian's first visits on the sheet: the measures, the habits, the goal."""
	elena = ctx.squadra("elena")
	if not (elena and scheda):
		return []
	scritte = []
	with ctx.come(elena):
		for visita in appuntamenti(ctx, "nutri", elena, 45)[: ctx.quanti(10)]:
			donna = frappe.db.get_value("CRM Lead", visita.lead, "gender") != "Male"
			altezza = ctx.rng.randint(155, 176) if donna else ctx.rng.randint(167, 189)
			imc = ctx.rng.uniform(21.5, 31.5)
			peso = round(imc * (altezza / 100) ** 2, 1)
			obiettivo = (
				"Perdere peso"
				if imc > 26
				else ctx.rng.choice(
					("Alimentazione per lo sport", "Migliorare la digestione", "Mantenere il peso")
				)
			)
			risposte = {
				"peso": peso,
				"altezza": altezza,
				"vita": round(70 + (imc - 21) * 2.6 + (0 if donna else 9)),
				"pasti": ctx.rng.choice(D.PASTI[1:]),
				"attivita": ctx.rng.choice(D.ATTIVITA),
				**anamnesi(ctx),
				"obiettivo": obiettivo,
				"indicazioni": D.OBIETTIVI[obiettivo],
			}
			record = visita_sulla_scheda(visita.lead, scheda, visita.appointment, visita.ends_on, risposte)
			scritte.append(_scritta(visita.lead, "elena", elena, record, visita.ends_on, obiettivo))
	return scritte


# -- the summary, the consents, the dossier ------------------------------------------------------


def decide_la_sintesi(ctx: Contesto, scritte: list[dict]) -> None:
	"""What the sheets proposed for the summary: most confirmed, now and then thrown
	away, a few left to decide."""
	from crm.clinica import sintesi

	for scritta in scritte:
		with ctx.come(scritta["utente"]):
			for proposta in sintesi.get_summary(scritta["lead"])["proposals"]:
				if proposta.get("status") not in (None, "Proposed"):
					continue
				caso = ctx.rng.random()
				if caso < 0.8:
					sintesi.confirm_value(proposta["name"])
				elif caso < 0.88:
					sintesi.discard_value(proposta["name"])


def _sintesi(ctx: Contesto, scritte: list[dict]) -> None:
	from crm.clinica import sintesi

	decide_la_sintesi(ctx, [s for s in scritte if s["chi"] != "luca"])
	for scritta in scritte:
		if scritta["chi"] == "elena" and ctx.rng.random() < 0.5:
			with ctx.come(scritta["utente"]):
				pressione = f"{ctx.rng.randint(110, 135)}/{ctx.rng.randint(70, 85)}"
				sintesi.set_value(scritta["lead"], "blood_pressure", pressione)


def consensi_alla_visita(ctx: Contesto, scritte: list[dict]) -> None:
	"""The dossier's consent and the online reports', asked at the visit: most say
	yes. Recorded by who asked, today."""
	from crm.moduli import consensi

	chiesti = set()
	for scritta in scritte:
		if scritta["lead"] in chiesti:
			continue
		chiesti.add(scritta["lead"])
		with ctx.come(scritta["utente"]):
			if ctx.rng.random() < 0.85:
				consensi.record_consent(scritta["lead"], "health_dossier", "Given", "At the desk")
			if ctx.rng.random() < 0.6:
				consensi.record_consent(scritta["lead"], "online_reports", "Given", "At the desk")


def _oscura(ctx: Contesto, direttrice: str, scritte: list[dict]) -> None:
	"""Somebody asked that an episode stay with who wrote it: the director obscures it."""
	from crm.clinica import dossier

	scritta = next((s for s in scritte if s["chi"] == "luca"), None)
	if scritta:
		with ctx.come(direttrice):
			dossier.obscure(RECORD, scritta["record"], note=D.OSCURATA)


def _fuori_equipe(ctx: Contesto, scritte: list[dict]) -> None:
	"""The dietitian opens the record of one of the physiotherapist's patients she does
	not follow, with her reason; she reads it."""
	from crm.clinica import cartella, dossier

	elena = ctx.squadra("elena")
	if not elena:
		return
	suoi = {lead for lead, _fine in visti_da(ctx, elena, 400)}
	with ctx.come(elena):
		for scritta in scritte:
			if scritta["chi"] != "giulia" or scritta["lead"] in suoi:
				continue
			nome = frappe.db.get_value("CRM Lead", scritta["lead"], "lead_name") or ""
			trovata = next(
				(r for r in dossier.find_out_of_care(nome) if r["name"] == scritta["lead"]),
				None,
			)
			if not trovata or trovata.get("in_care"):
				continue
			dossier.open_out_of_care(scritta["lead"], D.FUORI_EQUIPE)
			cartella.get_record(scritta["lead"])
			return


# -- the documents ----------------------------------------------------------------------------


def documento_pdf(titolo: str, fonte: str, quando, persona: str, corpo: str) -> bytes:
	"""A report as a centre prints it: who made it, for whom, when, what it says."""
	from crm.moduli import pdf

	return pdf.pdf_da_html(
		f"""<!doctype html><html><head><meta charset="utf-8"><style>
		body {{ font-family: sans-serif; font-size: 11pt; margin: 2cm; color: #222; }}
		.fonte {{ font-size: 9pt; color: #555; border-bottom: 1px solid #ccc; padding-bottom: 6px; }}
		table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
		td, th {{ border-bottom: 1px solid #ddd; padding: 6px 4px; text-align: left; }}
		</style></head><body>
		<p class="fonte">{escape_html(fonte)}</p>
		<h2>{escape_html(titolo)}</h2>
		<p>Paziente: {escape_html(persona)}<br>Data: {formatdate(quando, "dd/MM/yyyy")}</p>
		{corpo}
		</body></html>"""
	)


def carica(nome: str, contenuto: bytes) -> str:
	"""The file as the Documents tab uploads it: private, attached to nothing yet, the
	session's."""
	return (
		frappe.get_doc({"doctype": "File", "file_name": nome, "is_private": 1, "content": contenuto})
		.insert(ignore_permissions=True)
		.name
	)


def _esami(ctx: Contesto) -> str:
	righe = []
	for nome, unita, basso, alto, intervallo in D.ESAMI:
		valore = ctx.rng.uniform(basso, alto)
		testo = f"{valore:.1f}".replace(".", ",") if alto < 10 else str(round(valore))
		righe.append(
			f"<tr><td>{escape_html(nome)}</td><td>{testo} {escape_html(unita)}</td>"
			f"<td>{escape_html(intervallo)}</td></tr>"
		)
	return (
		"<table><tr><th>Esame</th><th>Risultato</th><th>Valori di riferimento</th></tr>"
		+ "".join(righe)
		+ "</table>"
	)


def _documenti(ctx: Contesto, direttrice: str, scritte: list[dict]) -> None:
	"""What people brought, filed by the desk for their practitioner: a scan before the
	physiotherapy, the blood tests before the dietitian; the director's prescription."""
	from crm.documenti import api as documenti

	desk = ctx.squadra("desk") or ctx.utente
	immagini = [s for s in scritte if s["chi"] == "giulia" and s["motivo"] in D.IMMAGINI]
	for scritta in immagini[: ctx.quanti(5)]:
		titolo, referto = D.IMMAGINI[scritta["motivo"]]
		quando = getdate(scritta["quando"]) - datetime.timedelta(days=ctx.rng.randint(5, 25))
		persona = frappe.db.get_value("CRM Lead", scritta["lead"], "lead_name")
		contenuto = documento_pdf(
			titolo, D.CENTRO_IMMAGINI, quando, persona, f"<p>{escape_html(referto)}</p>"
		)
		with ctx.come(desk):
			documenti.add_document(
				scritta["lead"],
				carica(f"{titolo} - {persona}.pdf", contenuto),
				titolo,
				"Imaging",
				document_date=str(quando),
				source=D.CENTRO_IMMAGINI,
				practitioner=scritta["utente"],
				notes="Portata alla prima visita.",
			)
	for scritta in [s for s in scritte if s["chi"] == "elena"][: ctx.quanti(4)]:
		quando = getdate(scritta["quando"]) - datetime.timedelta(days=ctx.rng.randint(3, 15))
		persona = frappe.db.get_value("CRM Lead", scritta["lead"], "lead_name")
		contenuto = documento_pdf("Esami del sangue", D.LABORATORIO, quando, persona, _esami(ctx))
		with ctx.come(desk):
			documenti.add_document(
				scritta["lead"],
				carica(f"Esami del sangue - {persona}.pdf", contenuto),
				"Esami del sangue",
				"Test result",
				document_date=str(quando),
				source=D.LABORATORIO,
				practitioner=scritta["utente"],
				notes="Chiesti dalla dietista alla prima visita.",
			)
	scritta = next((s for s in scritte if s["chi"] == "giulia"), None)
	if scritta:
		titolo, testo = D.PRESCRIZIONE
		quando = getdate(scritta["quando"]) - datetime.timedelta(days=ctx.rng.randint(2, 6))
		persona = frappe.db.get_value("CRM Lead", scritta["lead"], "lead_name")
		corpo = f"<p>{escape_html(testo.format(motivo=scritta['motivo'].lower()))}</p><p>Dott.ssa {escape_html(' '.join(D.DIRETTRICE[1:3]))}</p>"
		with ctx.come(direttrice):
			documenti.add_document(
				scritta["lead"],
				carica(
					f"{titolo} - {persona}.pdf",
					documento_pdf(titolo, "Direzione sanitaria", quando, persona, corpo),
				),
				titolo,
				"Prescription",
				document_date=str(quando),
			)


def _online(ctx: Contesto, scritte: list[dict]) -> None:
	"""A visit's report given online to who agreed to it: the link by email, the code at
	the desk; the person already downloaded it."""
	from crm.documenti import consegna

	for scritta in scritte:
		email = frappe.db.get_value("CRM Lead", scritta["lead"], "email")
		consenso = frappe.db.exists(
			"CRM Consent", {"lead": scritta["lead"], "consent_type": "online_reports", "status": "Given"}
		)
		referto = frappe.db.get_value(
			DOCUMENTO, {"record": scritta["record"], "document_type": "Report"}, "name"
		)
		if not (email and consenso and referto):
			continue
		with ctx.come(scritta["utente"]):
			dato = consegna.deliver_online(referto, send_email=1)
		trovato = re.search(r"/(?:documento|referto)/([A-Za-z0-9_-]+)", dato.get("link") or "")
		if trovato:
			with ctx.come("Guest"):
				sessione = consegna.open_document(trovato.group(1), dato["code"])["session"]
				consegna.download_document(trovato.group(1), sessione)
			# what the person downloaded leaves nothing behind in this job
			for chiave in ("filename", "filecontent", "type"):
				frappe.local.response.pop(chiave, None)
		return


# -- the board and the record's readers --------------------------------------------------------


def _di_cura(ctx: Contesto, scritte: list[dict]) -> None:
	"""A word from the practitioner on the board of who has the area."""
	from crm.area import messaggi

	nell_area = set(
		frappe.get_all("CRM Area Access", filters={"enabled": 1, "relation": "Self"}, pluck="lead")
	)
	for chi in ("giulia", "elena"):
		scritta = next((s for s in scritte if s["chi"] == chi and s["lead"] in nell_area), None)
		if not scritta:
			continue
		nome = frappe.db.get_value("CRM Lead", scritta["lead"], "first_name")
		with ctx.come(scritta["utente"]):
			messaggi.post_message(scritta["lead"], D.DI_CURA[chi].format(nome=nome))


def _letture(ctx: Contesto, direttrice: str, scritte: list[dict]) -> None:
	"""Before their sessions the practitioners read the records of who comes, the
	director a few: every opening is in the access log."""
	from crm.clinica import cartella

	for scritta in scritte[:: max(1, len(scritte) // max(1, ctx.quanti(8)))]:
		with ctx.come(scritta["utente"]):
			cartella.get_record(scritta["lead"])
	for scritta in scritte[: ctx.quanti(3)]:
		with ctx.come(direttrice):
			cartella.get_record(scritta["lead"])
