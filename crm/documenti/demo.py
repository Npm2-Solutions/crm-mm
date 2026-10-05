# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's documents (a person's Documents tab), through the documents' own code.

This morning the desk filed what it kept on paper: the contract of every subscription
sold, signed by both and handed over; the certificate the regulars of the classes
brought, scanned. A few were given online as well: the link went by email - kept in
the demo, nothing leaves - with the code said at the desk, and somebody has already
downloaded theirs through the page.

Filed today, as the forms are signed today: what a document's register says (given,
opened, downloaded) is never dated back.
"""

from __future__ import annotations

import datetime
import io
import re
import textwrap

import frappe
from frappe import _
from frappe.utils import add_days, add_months, escape_html, fmt_money, formatdate

from crm.demo import dati
from crm.demo.contesto import Contesto
from crm.demo.simulazione import persone_della_demo

ABBONAMENTO = "CRM Subscription"

PAGAMENTO = {
	"Upfront": "in un'unica soluzione, alla firma",
	"Monthly": "in rate mensili, all'inizio di ogni mese",
}
INGRESSI = {
	"Per week": "{0} ingressi a settimana",
	"Per month": "{0} ingressi al mese",
	"Unlimited": "ingressi senza limite",
}


def crea(ctx: Contesto) -> None:
	ctx.avanza(_("Documents"))
	desk = ctx.squadra("desk") or ctx.utente
	contratti = _contratti(ctx, desk)
	_certificati(ctx, desk)
	# a certificate stays at the centre: it is what the person brought
	_online(ctx, desk, contratti)


# -- the subscriptions' contracts --------------------------------------------------------


def _contratti(ctx: Contesto, desk: str) -> list[str]:
	"""Every subscription sold has its contract, signed by both and handed over."""
	from crm.documenti import api, consegna
	from crm.documenti import regole as R
	from crm.moduli import pdf
	from crm.moduli.richieste import nome_del_centro

	persone = persone_della_demo(ctx)
	if not persone:
		return []
	abbonamenti = frappe.get_all(
		ABBONAMENTO,
		filters={"lead": ["in", persone], "renewal_of": ["is", "not set"]},
		fields=[
			"name",
			"lead",
			"lead_name",
			"subscription_type",
			"starts_on",
			"ends_on",
			"payment",
			"price",
			"currency",
			"entries",
			"entries_count",
			"can_suspend",
			"max_suspension_days",
			"auto_renew",
		],
		order_by="starts_on",
	)
	centro = nome_del_centro() or "Il centro"
	fatti = []
	for abbonamento in abbonamenti:
		contenuto = pdf.pdf_da_html(_contratto(centro, abbonamento))
		with ctx.come(desk):
			allegato = _carica(f"Contratto {abbonamento.lead_name} {abbonamento.name}.pdf", contenuto)
			riga = api.add_document(
				abbonamento.lead,
				allegato,
				f"Contratto · {abbonamento.subscription_type}",
				R.CONTRATTO,
				document_date=str(abbonamento.starts_on),
				notes=f"L'abbonamento {abbonamento.name}, firmato alla vendita.",
			)
			consegna.deliver_by_hand(riga["name"])
		fatti.append(riga["name"])
	return fatti


def _contratto(centro: str, abbonamento) -> str:
	"""The contract as the centre prints it: who, what, for how long, how it is paid."""
	e = escape_html
	ingressi = INGRESSI.get(abbonamento.entries or "Unlimited", INGRESSI["Unlimited"]).format(
		abbonamento.entries_count or ""
	)
	dal, al = (formatdate(giorno, "dd/MM/yyyy") for giorno in (abbonamento.starts_on, abbonamento.ends_on))
	prezzo = fmt_money(abbonamento.price, currency=abbonamento.currency or "EUR")
	pagamento = PAGAMENTO.get(abbonamento.payment, PAGAMENTO["Upfront"])
	clausole = [
		f"Validità: dal {dal} al {al}.",
		f"Comprende {ingressi}, nelle lezioni e nei servizi dell'abbonamento.",
		f"Prezzo: {prezzo}, {pagamento}.",
	]
	if abbonamento.can_suspend:
		clausole.append(
			f"Si può sospendere per malattia o vacanza fino a {abbonamento.max_suspension_days or 30} "
			"giorni: la scadenza si sposta di altrettanto."
		)
	clausole.append(
		"Si rinnova da solo alla scadenza, salvo disdetta prima della fine."
		if abbonamento.auto_renew
		else "Alla scadenza termina senza bisogno di disdetta."
	)
	clausole.append("Gli ingressi non usati entro il periodo non si recuperano.")
	voci = "".join(f"<li>{e(clausola)}</li>" for clausola in clausole)
	return f"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 22mm 20mm; }}
body {{ font-family: sans-serif; font-size: 11pt; color: #222; line-height: 1.5; }}
h1 {{ font-size: 18pt; margin: 0 0 4mm; }}
.centro {{ color: #666; margin-bottom: 10mm; }}
li {{ margin-bottom: 2mm; }}
.firme {{ display: flex; justify-content: space-between; margin-top: 22mm; }}
.firma {{ width: 45%; border-top: 1px solid #999; padding-top: 2mm; color: #666; font-size: 9pt; }}
</style></head><body>
<h1>Contratto di abbonamento</h1>
<div class="centro">{e(centro)} · {e(abbonamento.subscription_type)}</div>
<p>Tra <b>{e(centro)}</b> e <b>{e(abbonamento.lead_name)}</b> si conviene l'abbonamento
<b>{e(abbonamento.subscription_type)}</b> alle condizioni seguenti.</p>
<ol>{voci}</ol>
<p>Firmando, la persona dichiara di aver letto l'informativa sul trattamento dei dati.</p>
<div class="firme"><div class="firma">Per il centro</div><div class="firma">{e(abbonamento.lead_name)}</div></div>
</body></html>"""


# -- the certificates the regulars brought ----------------------------------------------


def _certificati(ctx: Contesto, desk: str) -> list[str]:
	"""The regulars of the classes brought their certificate for non-competitive sport:
	scanned at the desk, valid a year from when the doctor wrote it."""
	from crm.documenti import api
	from crm.documenti import regole as R

	persone = persone_della_demo(ctx)
	lezioni = [ctx.trova(f"service.{chiave}") for chiave in {riga[2] for riga in dati.LEZIONI}]
	lezioni = [servizio for servizio in lezioni if servizio]
	if not persone or not lezioni:
		return []
	abituali = frappe.db.sql(
		"""select p.party as lead, count(*) as volte
		from `tabCRM Appointment Participant` p
		join `tabCRM Appointment` a on a.name = p.parent
		where p.parenttype = 'CRM Appointment' and p.party_type = 'CRM Lead'
			and p.party in %(persone)s and a.service in %(lezioni)s and p.status = 'Attended'
		group by p.party having count(*) >= 2 order by count(*) desc, p.party""",
		{"persone": persone, "lezioni": lezioni},
		as_dict=True,
	)
	fatti = []
	for abituale in abituali[: ctx.quanti(16)]:
		nome, cognome = frappe.db.get_value("CRM Lead", abituale.lead, ["first_name", "last_name"])
		rilascio = add_days(ctx.oggi, -ctx.rng.randint(40, 320))
		with ctx.come(desk):
			allegato = _carica(f"Certificato {nome} {cognome}.jpg", _scansione(ctx, nome, cognome, rilascio))
			riga = api.add_document(
				abituale.lead,
				allegato,
				"Certificato medico per l'attività non agonistica",
				R.CERTIFICATO,
				document_date=str(rilascio),
				source="Medico di medicina generale",
				notes=f"Valido fino al {formatdate(add_months(rilascio, 12), 'dd/MM/yyyy')}.",
			)
		fatti.append(riga["name"])
	return fatti


def _scansione(ctx: Contesto, nome: str, cognome: str, rilascio: datetime.date) -> bytes:
	"""A certificate as the desk's scanner sees it: a sheet a little crooked, the
	doctor's stroke under the words."""
	from PIL import Image, ImageDraw, ImageFont

	larghezza, altezza = 1240, 1754
	foglio = Image.new("RGB", (larghezza, altezza), (252, 251, 246))
	matita = ImageDraw.Draw(foglio)
	grande = ImageFont.load_default(size=46)
	medio = ImageFont.load_default(size=30)
	piccolo = ImageFont.load_default(size=22)
	inchiostro = (34, 34, 40)

	y = 190
	for testo, carattere in (
		("CERTIFICATO MEDICO", grande),
		("per l'attività sportiva di tipo non agonistico", medio),
	):
		matita.text(
			((larghezza - matita.textlength(testo, font=carattere)) / 2, y),
			testo,
			fill=inchiostro,
			font=carattere,
		)
		y += 80
	y += 90
	paragrafo = (
		f"Si certifica che {nome} {cognome}, sulla base della visita medica e degli "
		"accertamenti eseguiti, non presenta controindicazioni in atto alla pratica di "
		"attività sportiva di tipo non agonistico."
	)
	for riga in textwrap.wrap(paragrafo, 58):
		matita.text((150, y), riga, fill=inchiostro, font=medio)
		y += 48
	y += 40
	for riga in textwrap.wrap("Il presente certificato ha validità annuale dalla data del rilascio.", 58):
		matita.text((150, y), riga, fill=inchiostro, font=medio)
		y += 48
	y += 140
	matita.text((150, y), f"Data {formatdate(rilascio, 'dd/MM/yyyy')}", fill=inchiostro, font=medio)
	matita.text((780, y), "Il medico", fill=inchiostro, font=medio)
	# the doctor's stroke, a little different each time
	x, base = 760, y + 110
	punti = [(x, base)]
	while x < 1080:
		x += ctx.rng.randint(16, 34)
		punti.append((x, base + ctx.rng.randint(-34, 30)))
	matita.line(punti, fill=(28, 40, 110), width=4, joint="curve")
	matita.text((150, altezza - 120), "Dati di prova", fill=(170, 170, 170), font=piccolo)

	storto = foglio.rotate(
		ctx.rng.uniform(-0.9, 0.9), resample=Image.Resampling.BICUBIC, fillcolor=(228, 228, 224)
	)
	memoria = io.BytesIO()
	storto.save(memoria, format="JPEG", quality=72)
	return memoria.getvalue()


# -- given online --------------------------------------------------------------------------


def _online(ctx: Contesto, desk: str, contratti: list[str]) -> None:
	"""A few contracts went online too, the code said at the desk; one person has
	already opened the page and downloaded theirs."""
	from crm.documenti import consegna

	scelti = ctx.rng.sample(contratti, min(len(contratti), ctx.quanti(4)))
	for posizione, documento in enumerate(scelti):
		with ctx.come(desk):
			dato = consegna.deliver_online(documento, send_email=1)
		if posizione:
			continue
		token = re.search(r"/documento/([A-Za-z0-9_-]+)", dato["link"]).group(1)
		with ctx.come("Guest"):
			sessione = consegna.open_document(token, dato["code"])["session"]
			consegna.download_document(token, sessione)
	# what the person downloaded leaves nothing behind in this job
	for chiave in ("filename", "filecontent", "type"):
		frappe.local.response.pop(chiave, None)


def _carica(nome: str, contenuto: bytes) -> str:
	"""The file as the person's page uploads it: private, attached to nothing yet,
	the session's."""
	return (
		frappe.get_doc({"doctype": "File", "file_name": nome, "is_private": 1, "content": contenuto})
		.insert(ignore_permissions=True)
		.name
	)
