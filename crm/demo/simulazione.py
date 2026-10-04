# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Three months of the centre's life, day by day, through the product's own rules.

The centre opened twelve weeks ago. Every working day each practitioner's shifts
fill up - more as the weeks go by - with the next session of somebody already in
care or with somebody new; the classes run at their hours with their regulars.
A person arrives a few days before their first visit, from the website, a friend,
Instagram; a request opens a deal in the new clients pipeline, the booking moves it,
the first visit attended wins it and makes a client - the CRM does that itself, as
it would for a real centre. At the first visit the course is agreed: a cycle of
sessions sold at the desk, or a quote of the whole path from the practitioner,
accepted, declined or still to decide; the sessions after it join the cycle and take
the quote's rows by themselves. Past appointments are attended, missed or cancelled;
today's are done, in the waiting room or still to come; the next three weeks are
booked less and less, as a real agenda is.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

import frappe
from frappe import _
from frappe.utils import get_datetime, getdate

from crm.demo import dati
from crm.demo.contesto import Contesto, indirizzo, nome_del_giorno

#: How far back the centre's history goes, and how far ahead its agenda.
GIORNI_INDIETRO = 84
GIORNI_AVANTI = 21

#: The services each practitioner sees new people for.
NUOVI_PER = {
	"giulia": (("fisio", 30), ("tecar", 8), ("massaggio", 5)),
	"luca": (("osteo", 20), ("massaggio", 3)),
	"elena": (("nutri", 17),),
}
PRATICO = {"fisio": "giulia", "tecar": "giulia", "osteo": "luca", "nutri": "elena"}
#: Who comes by a request worth a deal; the others book or walk in by themselves.
CON_TRATTATIVA = ("Website", "Reference", "Instagram", "Facebook", "Advertisement")


def prossimo(giorno: datetime.date, nome: str) -> datetime.date:
	"""The first ``nome`` day on or after ``giorno``."""
	giorno = getdate(giorno)
	while nome_del_giorno(giorno) != nome:
		giorno += datetime.timedelta(days=1)
	return giorno


def numero(ctx: Contesto) -> str:
	"""A mobile number nobody else in the demo has."""
	usati = ctx.memoria.setdefault("numeri", set())
	while True:
		prefisso = ctx.rng.choice(dati.PREFISSI)
		coda = f"{ctx.rng.randint(0, 9999):04d}"
		if (prefisso, coda) not in usati:
			usati.add((prefisso, coda))
			return f"+39 {prefisso} 555 {coda}"


def retrodata_persona(ctx: Contesto, persona, quando, chi: str | None) -> None:
	ctx.retrodata("CRM Lead", persona.name, quando, chi)
	contatto = frappe.db.get_value("CRM Lead", persona.name, "contact")
	if contatto:
		ctx.retrodata("Contact", contatto, quando, chi)


def cellulare_di(lead: str) -> str | None:
	return frappe.db.get_value("CRM Lead", lead, "mobile_no")


def persone_della_demo(ctx: Contesto) -> list[str]:
	return sorted(set(ctx.con_chiave("person.").values()))


def clienti_recenti(ctx: Contesto, quanti: int) -> list[str]:
	"""A few of the people who became clients in the last weeks."""
	persone = persone_della_demo(ctx)
	if not persone:
		return []
	return frappe.get_all(
		"CRM Lead",
		filters={"name": ["in", persone], "client_since": [">=", ctx.giorno(-20)]},
		pluck="name",
		order_by="client_since desc",
		limit=quanti,
	)


def persone_per_lavoro(ctx: Contesto) -> dict[str, list[str]]:
	"""The people each colleague would write about: their own clients."""
	persone = persone_della_demo(ctx)
	if not persone:
		return {}
	per = {"tutte": persone}
	for chiave in ("giulia", "luca", "elena", "davide"):
		utente = ctx.squadra(chiave)
		if not utente:
			continue
		righe = frappe.db.sql(
			"""select distinct p.party from `tabCRM Appointment Participant` p
			join `tabCRM Appointment Staff` s on s.parent = p.parent
			where s.user = %(utente)s and p.party in %(persone)s order by p.party""",
			{"utente": utente, "persone": persone},
		)
		per[chiave] = [riga[0] for riga in righe]
	richieste = frappe.get_all(
		"CRM Lead", filters={"name": ["in", persone], "client_since": ["is", "not set"]}, pluck="name"
	)
	per["desk"] = richieste or persone
	per["manager"] = per["io"] = persone
	return per


@dataclass
class Persona:
	lead: str
	nome: str
	creata: datetime.datetime
	fonte: str
	#: the path they are on, the practitioner's key
	percorso: str | None = None
	pratico: str | None = None
	servizio_dopo: str | None = None
	restanti: int = 0
	prossima: datetime.date | None = None
	intervallo: tuple[int, int] = (7, 14)
	prenotato_da: str | None = None
	#: their first visit is behind them: what comes next is a session
	primo_fatto: bool = False
	#: the classes they come to (indexes of `dati.LEZIONI`), and until when
	lezioni: tuple[int, ...] = ()
	fino_a: datetime.date | None = None
	giorni: set = field(default_factory=set)
	trattativa: str | None = None
	#: the cycle or the quote agreed at the first visit
	ciclo: str | None = None
	preventivo: str | None = None
	prenotata: datetime.datetime | None = None
	ultima: datetime.datetime | None = None


class Simulazione:
	def __init__(self, ctx: Contesto):
		self.ctx = ctx
		self.rng = ctx.rng
		self.servizi = {chiave: ctx.trova(f"service.{chiave}") for chiave, *_resto in dati.SERVIZI}
		self.minuti = {riga[0]: riga[3] for riga in dati.SERVIZI}
		self.prezzi = {riga[0]: riga[4] for riga in dati.SERVIZI}
		self.stanza_di = {riga[0]: riga[6] for riga in dati.SERVIZI}
		self.stanze = {riga[0]: ctx.trova(f"room.{riga[0]}") for riga in dati.STANZE}
		self.squadra = {riga[0]: ctx.squadra(riga[0]) for riga in dati.SQUADRA}
		self.desk = self.squadra.get("desk") or ctx.utente
		self.inizio = ctx.giorno(-GIORNI_INDIETRO)
		self.fine = ctx.giorno(GIORNI_AVANTI)
		self.festivi = self._festivi()
		self.assenze = self._assenze()
		self.persone: list[Persona] = []
		self.nomi: set[str] = set()
		self.indirizzi: set[str] = set()
		self.contatore = 0
		self.appuntamenti = 0
		self.cicli = 0
		self.preventivi = 0
		self.stadi = self._stadi_nuovi_clienti()
		self.pipeline_dei_preventivi = self._pipeline_dei_preventivi()
		self.famiglia = prossimo(self.inizio + datetime.timedelta(days=45), "Tuesday")

	# -- the run -----------------------------------------------------------------------

	def esegui(self) -> None:
		self._fonti()
		for _volta in range(self.ctx.quanti(6)):
			self._nuovo_regolare(self.inizio + datetime.timedelta(days=self.rng.randint(0, 6)))
		giorno = self.inizio
		while giorno <= self.fine:
			if giorno.weekday() == 0:
				self.ctx.avanza(_("Week of {0}").format(giorno.strftime("%d/%m")))
			if giorno not in self.festivi:
				self._giornata(giorno)
			if giorno.weekday() == 6:
				self.ctx.salva()
			giorno += datetime.timedelta(days=1)
		self._richieste_senza_seguito()
		self._sistema_le_trattative()
		self._ultime_attivita()
		self.ctx.salva()

	def _giornata(self, giorno: datetime.date) -> None:
		nome = nome_del_giorno(giorno)
		if giorno == self.famiglia:
			self._famiglia(giorno)
		for indice, (giorno_lezione, ora, servizio) in enumerate(dati.LEZIONI):
			if giorno_lezione == nome:
				self._lezione(giorno, indice, ora, servizio)
		for chiave in ("giulia", "luca", "elena"):
			utente = self.squadra.get(chiave)
			if not utente or (utente, giorno) in self.assenze:
				continue
			for inizio, fine in dati.TURNI.get(chiave, {}).get(nome, ()):
				self._turno(chiave, giorno, inizio, fine)

	def _pienezza(self, giorno: datetime.date) -> float:
		"""How full a day is: a centre that grew in its first weeks, and an agenda that
		is booked less the further ahead it looks; less at a smaller scale."""
		return self._piena(giorno) * min(1.0, self.ctx.scala)

	def _piena(self, giorno: datetime.date) -> float:
		dall_apertura = (giorno - self.inizio).days
		mancano = (giorno - self.ctx.oggi).days
		if mancano > 14:
			return 0.2
		if mancano > 7:
			return 0.38
		if mancano > 0:
			return 0.62
		if mancano == 0:
			return 0.86
		if dall_apertura < 14:
			return 0.38
		if dall_apertura < 28:
			return 0.58
		return 0.74

	def _turno(self, chiave: str, giorno: datetime.date, inizio: str, fine: str) -> None:
		ora = self.ctx.alle(giorno, inizio)
		chiusura = self.ctx.alle(giorno, fine)
		pienezza = self._pienezza(giorno)
		while ora + datetime.timedelta(minutes=30) <= chiusura:
			if self.rng.random() > pienezza:
				ora += datetime.timedelta(minutes=self.rng.choice((15, 30, 45)))
				continue
			scelta = self._chi(chiave, giorno, ora, chiusura)
			if not scelta:
				ora += datetime.timedelta(minutes=15)
				continue
			persona, servizio = scelta
			minuti = self.minuti[servizio]
			self._appuntamento(giorno, ora, servizio, chiave, [persona])
			ora += datetime.timedelta(minutes=minuti + (15 if self.rng.random() < 0.2 else 0))

	# -- who comes ----------------------------------------------------------------------

	def _chi(self, chiave: str, giorno: datetime.date, ora: datetime.datetime, chiusura: datetime.datetime):
		"""The next session somebody in care is due for, or somebody new."""
		dovuti = []
		for p in self.persone:
			if p.pratico != chiave or not p.prossima or p.prossima > giorno or giorno in p.giorni:
				continue
			servizio = p.servizio_dopo if p.primo_fatto else dati.PERCORSI[p.percorso][0]
			if ora + datetime.timedelta(minutes=self.minuti[servizio]) <= chiusura:
				dovuti.append((p, servizio))
		if dovuti:
			return min(dovuti, key=lambda coppia: coppia[0].prossima)
		# somebody new in a slot nobody in care needs: fewer in the weeks ahead
		probabilita = 0.5 if giorno <= self.ctx.oggi else 0.3
		if self.rng.random() > probabilita:
			return None
		percorso = self.ctx.scegli_pesato(NUOVI_PER[chiave])
		primo = dati.PERCORSI[percorso][0]
		if ora + datetime.timedelta(minutes=self.minuti[primo]) > chiusura:
			return None
		persona = self._nuova_persona(giorno, percorso=percorso, pratico=chiave)
		return persona, primo

	def _nuova_persona(
		self,
		giorno: datetime.date,
		percorso: str | None = None,
		*,
		pratico: str | None = None,
		fonte: str | None = None,
		genere: str | None = None,
		nome: str | None = None,
		cognome: str | None = None,
		cellulare: str | None | bool = True,
		email: bool = True,
		creata: datetime.datetime | None = None,
	) -> Persona:
		ctx = self.ctx
		genere = genere or ctx.rng.choice(("Female", "Female", "Male"))
		nome, cognome = self._nome(genere, nome, cognome)
		fonte = fonte or ctx.scegli_pesato(dati.FONTI)
		if creata is None:
			prima = ctx.alle(giorno, "08:00") - datetime.timedelta(days=ctx.rng.randint(1, 12))
			creata = prima + datetime.timedelta(hours=ctx.rng.randint(1, 11), minutes=ctx.rng.randint(0, 59))
		creata = max(
			min(creata, ctx.adesso - datetime.timedelta(minutes=ctx.rng.randint(5, 90))),
			ctx.alle(self.inizio, "09:00") - datetime.timedelta(days=20),
		)
		proprietario = self.desk
		if percorso and ctx.rng.random() < 0.25:
			proprietario = self.squadra.get(PRATICO.get(percorso, "")) or self.desk
		indirizzo_email = None
		if email and ctx.rng.random() < 0.88:
			indirizzo_email = indirizzo(nome, cognome)
			numero_coda = 2
			while indirizzo_email in self.indirizzi:
				indirizzo_email = indirizzo(nome, cognome, numero_coda)
				numero_coda += 1
			self.indirizzi.add(indirizzo_email)
		if cellulare is True:
			cellulare = numero(ctx) if ctx.rng.random() < 0.96 else None
		with ctx.come(self.desk):
			doc = frappe.get_doc(
				{
					"doctype": "CRM Lead",
					"first_name": nome,
					"last_name": cognome,
					"gender": genere,
					"email": indirizzo_email,
					"mobile_no": cellulare or None,
					"source": fonte,
					"lead_owner": proprietario,
				}
			).insert(ignore_permissions=True)
		chi = "Administrator" if fonte == "Online booking" else self.desk
		retrodata_persona(ctx, doc, creata, chi)
		self.contatore += 1
		ctx.ricorda("CRM Lead", doc.name, f"person.{self.contatore}")
		persona = Persona(lead=doc.name, nome=f"{nome} {cognome}", creata=creata, fonte=fonte)
		if percorso:
			self._metti_in_percorso(persona, percorso, pratico)
		self._consenso(persona)
		if fonte in CON_TRATTATIVA and self.stadi:
			self._apri_trattativa(persona)
		self.persone.append(persona)
		return persona

	def _nome(self, genere: str, nome: str | None, cognome: str | None) -> tuple[str, str]:
		nomi = dati.NOMI_DONNA if genere == "Female" else dati.NOMI_UOMO
		for _tentativo in range(50):
			scelto = nome or self.rng.choice(nomi)
			di_famiglia = cognome or self.rng.choice(dati.COGNOMI)
			if f"{scelto} {di_famiglia}" not in self.nomi:
				break
		self.nomi.add(f"{scelto} {di_famiglia}")
		return scelto, di_famiglia

	def _metti_in_percorso(self, persona: Persona, percorso: str, pratico: str | None) -> None:
		_primo, dopo, (meno, piu), intervallo = dati.PERCORSI[percorso]
		persona.percorso = percorso
		persona.pratico = pratico or PRATICO.get(percorso) or "giulia"
		persona.servizio_dopo = dopo
		persona.restanti = self.rng.randint(meno, piu)
		persona.intervallo = intervallo

	def _consenso(self, persona: Persona) -> None:
		from crm.moduli import consensi
		from crm.moduli import registro as tipi

		caso = self.rng.random()
		if caso > 0.7:
			return
		stato = tipi.DATO if caso < 0.56 else tipi.RIFIUTATO
		canale = "Online booking" if persona.fonte == "Online booking" else "At the desk"
		try:
			nome = consensi.registra_risposta(persona.lead, "marketing", stato, canale)
		except frappe.ValidationError:
			return
		if nome:
			self.ctx.retrodata("CRM Consent", nome, persona.creata + datetime.timedelta(minutes=3), self.desk)

	def _apri_trattativa(self, persona: Persona) -> None:
		with self.ctx.come(self.desk):
			trattativa = frappe.get_doc(
				{
					"doctype": "CRM Deal",
					"status": self.stadi["Open"],
					"lead": persona.lead,
					"source": persona.fonte,
					"deal_owner": self.desk,
					"contacts": _contatti(persona.lead),
				}
			)
			trattativa.flags.from_inquiry = True
			trattativa.insert(ignore_permissions=True)
		frappe.db.set_value("CRM Lead", persona.lead, "converted", 1, update_modified=False)
		self.ctx.retrodata(
			"CRM Deal", trattativa.name, persona.creata + datetime.timedelta(minutes=2), self.desk
		)
		persona.trattativa = trattativa.name

	def _nuovo_regolare(self, dal: datetime.date) -> Persona:
		persona = self._nuova_persona(dal, fonte=self.ctx.scegli_pesato(dati.FONTI))
		quante = 2 if self.rng.random() < 0.35 else 1
		persona.lezioni = tuple(self.rng.sample(range(len(dati.LEZIONI)), quante))
		persona.prossima = dal
		if self.rng.random() < 0.2:
			persona.fino_a = dal + datetime.timedelta(days=self.rng.randint(25, 60))
		return persona

	def _famiglia(self, giorno: datetime.date) -> None:
		"""A mother books for her son, and pays: two people, linked."""
		from crm.persone.collegate import assicura_legame

		(nome_madre, cognome, genere_madre, cellulare), (nome_figlio, _c, genere_figlio, _n) = dati.FAMIGLIA
		creata = self.ctx.alle(giorno, "09:40") - datetime.timedelta(days=3)
		madre = self._nuova_persona(
			giorno,
			fonte="Reference",
			genere=genere_madre,
			nome=nome_madre,
			cognome=cognome,
			cellulare=cellulare,
			creata=creata,
		)
		figlio = self._nuova_persona(
			giorno,
			"fisio",
			fonte="Reference",
			genere=genere_figlio,
			nome=nome_figlio,
			cognome=cognome,
			cellulare=None,
			email=False,
			creata=creata + datetime.timedelta(minutes=4),
		)
		figlio.prenotato_da = madre.lead
		figlio.prossima = giorno
		assicura_legame(figlio.lead, madre.lead, "Parent", pays=1, books=1, represents=1)
		self.ctx.ricorda("CRM Lead", madre.lead, "family.parent")
		self.ctx.ricorda("CRM Lead", figlio.lead, "family.child")

	# -- the appointments -----------------------------------------------------------------

	def _lezione(self, giorno: datetime.date, indice: int, ora: str, servizio: str) -> None:
		utente = self.squadra.get("davide")
		if not utente or not self.servizi.get(servizio):
			return
		posti = next(riga[7] for riga in dati.SERVIZI if riga[0] == servizio)
		pienezza = self._pienezza(giorno)
		if self.rng.random() < pienezza * 0.35:
			self._nuovo_regolare(giorno).lezioni = (indice,)
		venuti = [
			p
			for p in self.persone
			if indice in p.lezioni
			and p.prossima
			and p.prossima <= giorno
			and (not p.fino_a or giorno <= p.fino_a)
			and giorno not in p.giorni
			and self.rng.random() < (0.85 if giorno <= self.ctx.oggi else 0.7)
		][:posti]
		if venuti:
			self._appuntamento(giorno, self.ctx.alle(giorno, ora), servizio, "davide", venuti)

	def _appuntamento(
		self,
		giorno: datetime.date,
		inizio: datetime.datetime,
		servizio: str,
		chiave: str,
		persone: list[Persona],
	) -> None:
		ctx = self.ctx
		fine = inizio + datetime.timedelta(minutes=self.minuti[servizio])
		annullato = self.rng.random() < (0.06 if fine <= ctx.adesso else 0.02)
		righe = []
		for persona in persone:
			esito, arrivo = self._esito(giorno, inizio, fine, annullato)
			riga = {
				"party_type": "CRM Lead",
				"party": persona.lead,
				"participant_name": persona.nome,
				"status": esito,
				"arrived_at": arrivo,
				"booked_by": persona.prenotato_da,
				"booked_online": 1 if persona.fonte == "Online booking" and not persona.giorni else 0,
			}
			righe.append((persona, riga))
		online = all(riga["booked_online"] for _p, riga in righe) and len(righe) == 1
		stato = "Cancelled" if annullato else ("Confirmed" if self.rng.random() < 0.6 else "Scheduled")
		prenotato = self._prenotato(inizio, [p for p, _r in righe])
		stanza = self.stanze.get(dati.STUDIO.get(chiave) or self.stanza_di[servizio])
		doc = frappe.get_doc(
			{
				"doctype": "CRM Appointment",
				"service": self.servizi[servizio],
				"status": stato,
				"starts_on": inizio,
				"ends_on": fine,
				"staff": [{"user": self.squadra[chiave], "status": "Confirmed"}],
				"participants": [riga for _p, riga in righe],
				"resources": [{"resource": stanza, "quantity": 1}] if stanza else [],
				"source": "Online" if online else "Internal",
				"cancellation_reason": self.rng.choice(dati.DISDETTE) if annullato else None,
			}
		)
		with ctx.come(self.desk):
			doc.insert(ignore_permissions=True)
		ctx.retrodata("CRM Appointment", doc.name, prenotato, "Administrator" if online else self.desk)
		self.appuntamenti += 1
		for persona, riga in righe:
			persona.giorni.add(giorno)
			if persona.prenotata is None:
				persona.prenotata = prenotato
			venuto = riga["status"] in ("Attended", "Arrived", "Booked")
			if venuto and inizio <= ctx.adesso:
				persona.ultima = max(persona.ultima or fine, min(fine, ctx.adesso))
			continua = True
			if (
				persona.percorso
				and not persona.primo_fatto
				and riga["status"] == "Attended"
				and servizio == dati.PERCORSI[persona.percorso][0]
			):
				continua = self._alla_prima_visita(persona, giorno, fine)
			self._dopo(persona, giorno, servizio, venuto and not annullato)
			if not continua:
				# they said no to the course: they do not come back for it
				persona.prossima = None

	def _esito(self, giorno, inizio, fine, annullato) -> tuple[str, datetime.datetime | None]:
		ctx = self.ctx
		if annullato:
			return "Cancelled", None
		arrivo = inizio - datetime.timedelta(minutes=self.rng.randint(2, 12))
		if fine <= ctx.adesso:
			ieri_o_poco_fa = 0 < (ctx.oggi - giorno).days <= 3
			if ieri_o_poco_fa and self.rng.random() < 0.08:
				# the desk did not mark them: the reception desk asks "did they come?"
				return "Booked", None
			if self.rng.random() < 0.035:
				return "No Show", None
			if giorno == ctx.oggi:
				return "Attended", arrivo
			return "Attended", arrivo
		if inizio <= ctx.adesso:
			return "Arrived", min(arrivo, ctx.adesso)
		if (
			giorno == ctx.oggi
			and inizio - ctx.adesso <= datetime.timedelta(minutes=40)
			and self.rng.random() < 0.7
		):
			# in the waiting room already
			return "Arrived", ctx.adesso - datetime.timedelta(minutes=self.rng.randint(1, 14))
		return "Booked", None

	def _prenotato(self, inizio: datetime.datetime, persone: list[Persona]) -> datetime.datetime:
		"""When it was booked: a few days before, never before the person existed nor
		after now."""
		piu_tardi = max(p.creata for p in persone) + datetime.timedelta(minutes=5)
		quando = inizio - datetime.timedelta(days=self.rng.randint(1, 12), hours=self.rng.randint(0, 6))
		quando = max(quando, piu_tardi)
		return min(
			quando, self.ctx.adesso - datetime.timedelta(minutes=2), inizio - datetime.timedelta(minutes=30)
		)

	def _dopo(self, persona: Persona, giorno: datetime.date, servizio: str, venuto: bool) -> None:
		"""What comes next for them: the next session in so many days."""
		if persona.lezioni:
			persona.prossima = giorno + datetime.timedelta(days=1)
			return
		if not persona.percorso:
			return
		if not venuto:
			# missed or cancelled: they book again in a few days
			persona.prossima = giorno + datetime.timedelta(days=self.rng.randint(2, 6))
			return
		if persona.primo_fatto:
			persona.restanti -= 1
		else:
			persona.primo_fatto = True
		if persona.restanti > 0:
			meno, piu = persona.intervallo
			persona.prossima = giorno + datetime.timedelta(days=self.rng.randint(meno, piu))
		elif self.rng.random() < 0.15:
			# some come back for a check, a while later
			persona.restanti = 1
			persona.prossima = giorno + datetime.timedelta(days=self.rng.randint(25, 40))
		else:
			persona.prossima = None

	# -- the course agreed at the first visit ----------------------------------------------

	def _alla_prima_visita(self, persona: Persona, giorno: datetime.date, fine: datetime.datetime) -> bool:
		"""After the first visit the course is agreed: a cycle of sessions paid ahead at
		the desk, a quote of the whole path from the practitioner, or nothing - the person
		pays session by session. What comes after follows by itself: a session joins the
		cycle, or takes its row of the quote. False when the person said no."""
		caso = self.rng.random()
		con_ciclo = dati.PERCORSI[persona.percorso][1] in dati.CICLI
		if con_ciclo and caso < 0.4:
			self._vendi_ciclo(persona, giorno, fine)
		elif (
			persona.percorso in dati.PREVENTIVI
			and self.pipeline_dei_preventivi is not None
			and caso < (0.65 if con_ciclo else 0.45)
		):
			return self._proponi_preventivo(persona, giorno, fine)
		return True

	def _vendi_ciclo(self, persona: Persona, giorno: datetime.date, fine: datetime.datetime) -> None:
		"""A pack of sessions sold at the desk after the first visit, for as many as the
		path needs; the sessions booked after it join it."""
		from crm.scheduling import cicli

		ctx = self.ctx
		servizio = dati.PERCORSI[persona.percorso][1]
		pacchetti = dati.CICLI[servizio]
		sedute = min((n for n in pacchetti if n >= persona.restanti), default=max(pacchetti))
		scade = None
		if ctx.rng.random() < 0.6:
			scade = giorno + datetime.timedelta(days=60 if sedute <= 5 else 120)
		with ctx.come(self.desk):
			ciclo = cicli.save_cycle(
				persona.lead,
				{
					"service": self.servizi[servizio],
					"sessions": sedute,
					"starts_on": giorno,
					"valid_until": scade,
					"price": pacchetti[sedute],
					"billing": cicli.INTERO if ctx.rng.random() < 0.6 else cicli.PER_SEDUTA,
					"missed_count": 1,
					"practitioner": self.squadra.get(persona.pratico),
					"notes": ctx.rng.choice(dati.NOTE_CICLI[servizio]),
				},
			)
		venduto = min(fine + datetime.timedelta(minutes=ctx.rng.randint(3, 15)), ctx.adesso)
		ctx.retrodata(cicli.CICLO, ciclo["name"], venduto, self.desk)
		persona.ciclo = ciclo["name"]
		self.cicli += 1

	def _proponi_preventivo(self, persona: Persona, giorno: datetime.date, fine: datetime.datetime) -> bool:
		"""The practitioner's quote of the whole path, one row a session, handed over
		after the first visit; the person says yes (the sessions take its rows), no, or
		has not decided yet when the visit was recent. False when they said no."""
		from crm.preventivi import api as preventivi

		ctx = self.ctx
		autore = self.squadra.get(persona.pratico)
		if not autore:
			return True
		titolo, parole, sconto = dati.PREVENTIVI[persona.percorso]
		servizio = dati.PERCORSI[persona.percorso][1]
		quante = max(persona.restanti, 1) + (1 if ctx.rng.random() < 0.3 else 0)
		meta = (quante + 1) // 2 if persona.percorso == "fisio" else quante
		voci = [
			{
				"service": self.servizi[servizio],
				"qty": 1,
				"rate": self.prezzi[servizio],
				"discount": sconto,
				"phase": 1 if numero < meta else 2,
			}
			for numero in range(quante)
		]
		proposto = min(
			fine + datetime.timedelta(minutes=ctx.rng.randint(5, 25)),
			ctx.adesso - datetime.timedelta(minutes=30),
		)
		with ctx.come(autore):
			bozza = preventivi.save_quote(
				persona.lead, {"title": titolo, "patient_notes": parole, "items": voci}
			)
			preventivi.propose_quote(bozza["name"])
		nome = bozza["name"]
		persona.preventivo = nome
		self.preventivi += 1

		caso = ctx.rng.random()
		if (ctx.oggi - giorno).days <= 7 and caso < 0.55:
			esito, quando = None, None
		elif caso < 0.85:
			esito = "si"
			quando = proposto + datetime.timedelta(hours=ctx.rng.choice((0, 0, 2, 20, 26)))
		else:
			esito = "no"
			quando = proposto + datetime.timedelta(days=ctx.rng.randint(1, 5), hours=ctx.rng.randint(0, 6))
		if quando:
			quando = min(quando, ctx.adesso - datetime.timedelta(minutes=10))
		with ctx.come(self.desk):
			if esito == "si":
				preventivi.accept_quote(nome, ctx.rng.choice(dati.SI_AL_PREVENTIVO))
			elif esito == "no":
				motivo, nota = ctx.rng.choice(dati.NO_AL_PREVENTIVO)
				preventivi.decline_quote(
					nome, motivo if frappe.db.exists("CRM Lost Reason", motivo) else None, nota
				)
		self._date_del_preventivo(nome, autore, proposto, esito, quando)
		return esito != "no"

	def _date_del_preventivo(self, nome, autore, proposto, esito, quando) -> None:
		"""A quote written as "now" while the past was replayed, put back at its moments:
		written and handed over after the visit, answered when the person did; its PDF
		and its deal with it."""
		from crm.preventivi import api as preventivi

		ctx = self.ctx
		valori = {
			"proposed_on": proposto,
			"valid_until": proposto.date() + datetime.timedelta(days=preventivi.giorni_di_validita()),
		}
		if esito == "si":
			valori["accepted_on"] = quando
		elif esito == "no":
			valori["declined_on"] = quando
		ctx.retrodata(preventivi.DOCTYPE, nome, proposto - datetime.timedelta(minutes=8), autore)
		frappe.db.set_value(
			preventivi.DOCTYPE, nome, {**valori, "modified": quando or proposto}, update_modified=False
		)
		for file in frappe.get_all(
			"File",
			filters={"attached_to_doctype": preventivi.DOCTYPE, "attached_to_name": nome},
			pluck="name",
		):
			ctx.retrodata("File", file, proposto, autore)
		trattativa = frappe.db.get_value(preventivi.DOCTYPE, nome, "deal")
		if not trattativa:
			return
		if get_datetime(frappe.db.get_value("CRM Deal", trattativa, "creation")) > proposto:
			ctx.retrodata("CRM Deal", trattativa, proposto, self.desk)
		chiusura = {"modified": quando or proposto}
		if quando:
			chiusura["closed_date"] = quando.date()
		frappe.db.set_value("CRM Deal", trattativa, chiusura, update_modified=False)
		self._ritempra_il_registro(trattativa, [quando] if quando else [])

	# -- the requests that went nowhere yet ------------------------------------------------

	def _richieste_senza_seguito(self) -> None:
		ctx = self.ctx
		if not self.stadi:
			return
		ctx.avanza(_("Requests"))
		for _volta in range(ctx.quanti(28)):
			# the recent ones are the most: the desk has them to call back
			giorni_fa = int(ctx.rng.betavariate(1.0, 2.4) * (GIORNI_INDIETRO - 10))
			creata = ctx.adesso - datetime.timedelta(days=giorni_fa, hours=ctx.rng.randint(0, 9))
			persona = self._nuova_persona(
				ctx.giorno(-giorni_fa), fonte=ctx.rng.choice(CON_TRATTATIVA), creata=creata
			)
			if not persona.trattativa:
				continue
			if giorni_fa <= 4:
				continue
			if giorni_fa <= 20 or ctx.rng.random() < 0.45:
				self._sposta(
					persona.trattativa, self.stadi.get("Ongoing"), creata + datetime.timedelta(days=1)
				)
			else:
				motivo, nota = ctx.rng.choice(dati.PERSI)
				self._sposta(
					persona.trattativa,
					self.stadi.get("Lost"),
					creata + datetime.timedelta(days=ctx.rng.randint(6, 15)),
					lost_reason=motivo if frappe.db.exists("CRM Lost Reason", motivo) else "Other",
					lost_notes=nota,
				)

	def _sposta(self, trattativa: str, stadio: str | None, quando: datetime.datetime, **altro) -> None:
		if not stadio:
			return
		quando = min(quando, self.ctx.adesso)
		doc = frappe.get_doc("CRM Deal", trattativa)
		doc.status = stadio
		doc.update(altro)
		doc.flags.from_inquiry = True
		with self.ctx.come(self.desk):
			doc.save(ignore_permissions=True)
		valori = {"modified": quando}
		if frappe.get_cached_value("CRM Deal Status", stadio, "type") in ("Won", "Lost"):
			valori["closed_date"] = quando.date()
		frappe.db.set_value("CRM Deal", trattativa, valori, update_modified=False)
		self._ritempra_il_registro(trattativa, [quando])

	# -- dates the CRM wrote as "now" while the past was replayed ---------------------------

	def _sistema_le_trattative(self) -> None:
		"""A deal the CRM moved while the past was replayed was moved at that past
		moment: closed the day the person first came, its stages logged then."""
		for persona in self.persone:
			if not persona.trattativa:
				continue
			cliente = frappe.db.get_value("CRM Lead", persona.lead, "client_since")
			tappe = [t for t in (persona.prenotata, get_datetime(cliente) if cliente else None) if t]
			valori = {}
			stato = frappe.db.get_value("CRM Deal", persona.trattativa, "status")
			tipo = frappe.get_cached_value("CRM Deal Status", stato, "type") if stato else None
			if tipo == "Won" and cliente:
				valori.update({"closed_date": getdate(cliente), "modified": get_datetime(cliente)})
			elif persona.prenotata:
				valori["modified"] = persona.prenotata
			if valori:
				frappe.db.set_value("CRM Deal", persona.trattativa, valori, update_modified=False)
			if tappe:
				self._ritempra_il_registro(persona.trattativa, tappe)

	def _ritempra_il_registro(self, trattativa: str, tappe: list[datetime.datetime]) -> None:
		"""The deal's stage log, at the moments it really moved."""
		creata = frappe.db.get_value("CRM Deal", trattativa, "creation")
		momenti = [get_datetime(creata), *sorted(get_datetime(t) for t in tappe)]
		righe = frappe.get_all(
			"CRM Status Change Log",
			filters={"parent": trattativa, "parenttype": "CRM Deal"},
			fields=["name"],
			order_by="idx asc",
		)
		for indice, riga in enumerate(righe):
			dal = momenti[min(indice, len(momenti) - 1)]
			al = momenti[indice + 1] if indice + 1 < len(momenti) and indice + 1 < len(righe) else None
			valori = {"from_date": dal}
			if al:
				valori.update({"to_date": al, "duration": max(0, int((al - dal).total_seconds()))})
			frappe.db.set_value("CRM Status Change Log", riga.name, valori, update_modified=False)

	def _ultime_attivita(self) -> None:
		"""A person's record was last touched when they last came, as the lists sort."""
		for persona in self.persone:
			quando = max(t for t in (persona.creata, persona.ultima, persona.prenotata) if t)
			quando = min(quando, self.ctx.adesso)
			frappe.db.set_value("CRM Lead", persona.lead, "modified", quando, update_modified=False)

	# -- what the simulation reads first -------------------------------------------------------

	def _festivi(self) -> set[datetime.date]:
		lista = self.ctx.trova("agenda.festivita")
		if not lista:
			return set()
		return {
			getdate(riga.date)
			for riga in frappe.get_all(
				"CRM Holiday", filters={"parent": lista, "parenttype": "CRM Holiday List"}, fields=["date"]
			)
		}

	def _assenze(self) -> set[tuple[str, datetime.date]]:
		utenti = [u for u in self.squadra.values() if u]
		if not utenti:
			return set()
		return {
			(riga.parent, getdate(riga.date))
			for riga in frappe.get_all(
				"CRM Availability Exception",
				filters={"parenttype": "CRM Staff Schedule", "parent": ["in", utenti], "unavailable": 1},
				fields=["parent", "date"],
			)
		}

	def _pipeline_dei_preventivi(self) -> str | None:
		"""The quotes pipeline, made as the product makes it when the centre has none:
		a quote handed over moves the person's deal in it."""
		from crm.demo import registro
		from crm.preventivi import pipeline

		with registro.fuori_dal_registro():
			return pipeline.crea()

	def _stadi_nuovi_clienti(self) -> dict[str, str]:
		"""The new clients pipeline's first, contacted, won and lost stages - made as the
		product makes it when the centre has none."""
		from crm.clienti import pipeline
		from crm.demo import registro

		with registro.fuori_dal_registro():
			pipeline.crea()
		nome = pipeline.quale()
		if not nome:
			return {}
		stadi = frappe.get_all(
			"CRM Deal Status",
			filters={"pipeline": nome},
			fields=["name", "type"],
			order_by="position asc",
		)
		trovati = {}
		for riga in stadi:
			trovati.setdefault(riga.type, riga.name)
		return trovati

	def _fonti(self) -> None:
		"""The sources the people come from, made as the channels make them."""
		for fonte, _peso in dati.FONTI:
			if not frappe.db.exists("CRM Lead Source", fonte):
				frappe.get_doc({"doctype": "CRM Lead Source", "source_name": fonte}).insert(
					ignore_permissions=True
				)


def _contatti(lead: str) -> list[dict]:
	contatto = frappe.db.get_value("CRM Lead", lead, "contact")
	return [{"contact": contatto, "is_primary": 1}] if contatto else []


def crea(ctx: Contesto) -> None:
	if not ctx.trova("service.fisio"):
		return
	Simulazione(ctx).esegui()
