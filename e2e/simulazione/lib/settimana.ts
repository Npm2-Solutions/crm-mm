// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import type { Browser, Page } from '@playwright/test'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { Banco } from './banco'
import {
	grandeAbbastanza,
	largo,
	nomiCrudi,
	paroleCrude,
	testoCrudo,
	toastDiErrore,
	tocco,
	type Trovato,
} from './controlli'
import { RAPPORTO } from './inizio'
import { Persona } from './persone'
import { Rapporto, type Gravita, type Passo } from './rapporto'

export type Copione = {
	centre: string
	password: string
	team: Record<string, string>
	people: Array<{
		key: string
		first_name: string
		last_name: string
		email: string
		mobile: string
		sex: string
		birth_date: string
		device: string
		parent: string | null
		fiscal_code: string
		address: { street: string; number: string; postcode: string; city: string }
	}>
	services: Record<string, string>
	locations: Record<string, string>
	location_titles: Record<string, string>
	convention: string
	company_client: { name: string; vat: string; street: string; postcode: string; city: string; person: string }
	subscriptions: Record<string, string>
	week: Record<string, string>
}

/** What the staff hold, by role. */
const DISPOSITIVO_DEL_RUOLO: Record<string, string> = {
	segreteria: 'scrivania',
	responsabile: 'scrivania',
	medico: 'tablet',
	fisioterapista: 'telefono',
	dentista: 'scrivania_scura',
	dietista: 'piccolo',
	marketing: 'scrivania',
}

/** The scheduler, as the bench would run it if it ran: the jobs a centre's day
 * hears every few minutes (minutes between two runs), and the ones of every night.
 * The bench's own scheduler stays off: the suite runs them as the clock moves. */
export const FREQUENTI: Array<[string, number]> = [
	['crm.automation.engine.process_due_enrollments', 1],
	['crm.notifiche.posta.manda_le_email', 5],
	['crm.scheduling.attese.ogni_dieci_minuti', 10],
	['crm.pagamenti.pagamenti.ogni_dieci_minuti', 10],
	['crm.scheduling.promemoria.ogni_quarto_d_ora', 15],
	['crm.scheduling.esiti.fine_giornata', 60],
	['crm.api.conversations.wake_the_snoozed', 60],
]
export const NOTTURNI = [
	'crm.scheduling.abbonamenti.ogni_giorno',
	'crm.preventivi.rate.ogni_giorno',
	'crm.invoicing.solleciti.ogni_giorno',
	'crm.piani.programmi.apri_del_giorno',
	'crm.invoicing.monitoraggio.giornaliero',
	'crm.tessera_sanitaria.monitoraggio.giornaliero',
	'crm.esportazione.esporta.togli_le_vecchie',
	'crm.fcrm.doctype.crm_invitation.crm_invitation.expire_invitations',
	'crm.tessera_sanitaria.automatico.ogni_notte',
]

/** Console errors understood and harmless: (what, why). */
export const RUMORE: Array<[RegExp, string]> = [
	// the hosted page's favicon: the fake has none
	[/127\.0\.0\.1:8791\/favicon\.ico/, 'the fake Stripe page has no icon'],
	// a request to another site the simulation stopped: reported as such, not twice
	[/net::ERR_BLOCKED_BY_CLIENT/, 'a request the simulation stopped'],
	// a bench serving the test site on a port of its own has no realtime for it
	...(process.env.SIM_SENZA_SOCKET
		? ([[/socket\.io|status of 404 \(NOT FOUND\)/, 'no realtime on this bench (SIM_SENZA_SOCKET)']] as Array<
				[RegExp, string]
			>)
		: []),
]

export class Fallito extends Error {}

type OpzioniPasso = {
	/** steps (by key) this one needs: skipped when one of them failed */
	dopo?: string[]
	/** a key for later steps to depend on */
	chiave?: string
	/** words the screen may show though they look raw (a code the person typed) */
	ammessi?: RegExp[]
	/** 4xx answers the step expects */
	attesi?: RegExp[]
	/** no screenshot */
	senzaFoto?: boolean
}

/** The week being played: the bench, the personas, the shared memory of the days,
 * the steps and their report. */
export class Settimana {
	banco!: Banco
	copione!: Copione
	persone: Record<string, Persona> = {}
	rapporto = new Rapporto()
	giorno = ''
	stato: Record<string, any> = {}
	private numero = 0
	private esiti: Record<string, boolean> = {}
	private passoCorrente = ''
	private noteCorrenti: string[] = []
	private trovati: Array<Trovato & { dove: string }> = []
	private emailViste = new Set<string>()

	constructor(readonly browser: Browser) {}

	static async inizia(browser: Browser): Promise<Settimana> {
		const s = new Settimana(browser)
		s.banco = await Banco.apri()
		const memoria = path.join(RAPPORTO, 'stato.json')
		if (process.env.SIM_DA && existsSync(memoria)) {
			const salvata = JSON.parse(readFileSync(memoria, 'utf8'))
			s.copione = salvata.copione
			s.stato = salvata.stato
			s.esiti = salvata.esiti
			s.numero = salvata.numero
		} else {
			s.copione = await s.banco.chiama('crm.collaudo.api.copione', {}, 'GET')
		}
		for (const [ruolo, email] of Object.entries(s.copione.team)) {
			s.persone[ruolo] = new Persona(
				ruolo,
				ruolo,
				DISPOSITIVO_DEL_RUOLO[ruolo] as any,
				email,
				s.copione.password,
				`198.51.100.${10 + Object.keys(s.persone).length}`,
			)
		}
		// the manager carries her phone too: Monza on Tuesday afternoon, the evening
		s.persone.responsabile_telefono = new Persona(
			'responsabile_telefono',
			'responsabile, dal telefono',
			'telefono',
			s.copione.team.responsabile,
			s.copione.password,
			'198.51.100.40',
		)
		s.copione.people.forEach((p, i) => {
			s.persone[p.key] = new Persona(
				p.key,
				`${p.first_name} ${p.last_name}`,
				p.device as any,
				p.email,
				null,
				`203.0.113.${20 + i}`,
			)
		})
		await s.assicuraStripe()
		return s
	}

	/** The fake Stripe knows the centre's endpoint (made again, as «Check» makes it,
	 * where the fake was started afresh). */
	private async assicuraStripe() {
		const stato = await this.banco.finti('_stato')
		if (!stato.endpoint?.length) await this.banco.chiama('crm.pagamenti.collegamento.check_stripe')
	}

	salva() {
		writeFileSync(
			path.join(RAPPORTO, 'stato.json'),
			JSON.stringify({ copione: this.copione, stato: this.stato, esiti: this.esiti, numero: this.numero }, null, 1),
		)
		this.rapporto.scrivi({
			Centro: this.copione.centre,
			Banco: this.banco.api ? process.env.SIM_BASE || 'http://collaudo.localhost:8000' : '',
			Settimana: `${this.copione.week.lunedi} → ${this.copione.week.sabato}`,
			Scritto: new Date().toISOString(),
		})
	}

	/** Whether a step (by its key) went through. */
	esito(chiave: string): boolean {
		return this.esiti[chiave] === true
	}

	/** The person of the week, by key (a role or a patient). */
	p(chiave: string): Persona {
		const persona = this.persone[chiave]
		if (!persona) throw new Error(`Nobody is ${chiave}`)
		return persona
	}

	persona(chiave: string) {
		return this.copione.people.find((p) => p.key === chiave)!
	}

	/** A member of staff at work: their browser, signed in through the sign-in
	 * page the first time and again whenever the session went. */
	async alLavoro(chi: Persona): Promise<Page> {
		const page = await chi.apri(this.browser, this.banco)
		const chiEntra: { message?: string } = await page.request
			.get('/api/method/frappe.auth.get_logged_user')
			.then((r) => (r.ok() ? r.json() : {}))
			.catch(() => ({}))
		if (chiEntra?.message === chi.email) return page
		return chi.entra(this.browser, this.banco, { dalModulo: true })
	}

	/** The bench's clock to ``ora`` of the day being played; where the steps before
	 * already took it past, it goes on from there (a week's clock never goes back).
	 * The jobs due by then run, as the scheduler would have run them. */
	async alle(ora: string) {
		const quando = `${this.copione.week[this.giorno]} ${ora}`
		if (!(this.banco.ora && this.banco.oraAdesso() >= quando)) await this.banco.orologio(quando)
		await this.lavori()
	}

	/** The frequent jobs whose time came (their last run kept in the state). */
	async lavori() {
		const adesso = this.banco.adesso().getTime()
		const ultimi: Record<string, number> = (this.stato._lavori ||= {})
		for (const [metodo, minuti] of FREQUENTI) {
			if (ultimi[metodo] && adesso - ultimi[metodo] < minuti * 60000) continue
			ultimi[metodo] = adesso
			await this.banco.esegui(metodo).catch((e) => this.difettoDelBanco(metodo, e))
		}
	}

	/** The night's jobs, before the day: what a centre finds done in the morning. */
	async notte() {
		for (const metodo of NOTTURNI) await this.banco.esegui(metodo).catch((e) => this.difettoDelBanco(metodo, e))
	}

	private difettoDelBanco(metodo: string, errore: unknown) {
		this.rapporto.segna({
			gravita: 'grave',
			cosa: 'A scheduled job failed',
			dettaglio: `${metodo}: ${String((errore as Error)?.message || errore).slice(0, 200)}`,
			dove: 'server',
			passo: this.passoCorrente || 'the scheduler',
			giorno: this.giorno,
		})
	}

	/** A date of the week as the database keeps it. */
	data(giorno: string): string {
		return this.copione.week[giorno]
	}

	/** What ``leggi`` gives once ``basta`` holds, or after ``secondi`` what it gives:
	 * what a job or a webhook writes a moment after the screen. */
	async attendi<T>(leggi: () => Promise<T>, basta: (valore: T) => boolean, secondi = 20): Promise<T> {
		const fine = Date.now() + secondi * 1000
		let valore = await leggi()
		while (!basta(valore) && Date.now() < fine) {
			await new Promise((fatto) => setTimeout(fatto, 700))
			valore = await leggi()
		}
		return valore
	}

	nota(testo: string) {
		this.noteCorrenti.push(testo)
	}

	/** A defect found by the step itself (an assertion of what should be). */
	difetto(gravita: Gravita, cosa: string, dettaglio?: string, dove = '') {
		this.trovati.push({ gravita, cosa, dettaglio, dove })
	}

	/** Checked, and a defect when it does not hold; the step goes on. */
	verifica(condizione: unknown, cosa: string, dettaglio?: string, gravita: Gravita = 'grave'): boolean {
		if (!condizione) this.difetto(gravita, cosa, dettaglio)
		return !!condizione
	}

	/** A main action of the step must take a finger. */
	async dito(persona: Persona, azione: import('@playwright/test').Locator) {
		if (!persona.tocco) return
		for (const t of await grandeAbbastanza(azione)) this.trovati.push({ ...t, dove: persona.descrizione })
	}

	async foto(persona: Persona, nome: string): Promise<string | undefined> {
		const page = persona.pagina
		if (!page || page.isClosed()) return
		const cartella = path.join(RAPPORTO, this.giorno)
		mkdirSync(cartella, { recursive: true })
		const file = `${String(this.numero).padStart(2, '0')}-${persona.chiave}-${nome}`.replace(/[^\w.-]+/g, '-') + '.png'
		await page.screenshot({ path: path.join(cartella, file), fullPage: false }).catch(() => {})
		return `${this.giorno}/${file}`
	}

	/** One step of the day: run, checked, photographed, reported. Never throws: a
	 * failed step is reported, and the steps that need it are skipped. */
	async passo(titolo: string, chi: Persona | Persona[], fai: () => Promise<void>, opzioni: OpzioniPasso = {}) {
		const persone = Array.isArray(chi) ? chi : [chi]
		this.numero += 1
		this.passoCorrente = `${this.numero}. ${titolo}`
		this.noteCorrenti = []
		this.trovati = []
		const inizio = Date.now()
		const oraBanco = this.banco.ora
		const voce: Passo = {
			giorno: this.giorno,
			numero: this.numero,
			ora: oraBanco.slice(11, 16),
			titolo,
			chi: persone.map((p) => p.descrizione),
			esito: 'ok',
			secondi: 0,
			schermate: [],
			note: this.noteCorrenti,
			difetti: 0,
		}
		const manca = (opzioni.dopo || []).filter((k) => this.esiti[k] === false || this.esiti[k] === undefined)
		if (manca.length) {
			voce.esito = 'saltato'
			voce.errore = `Needs: ${manca.join(', ')}`
			this.rapporto.passi.push(voce)
			if (opzioni.chiave) this.esiti[opzioni.chiave] = false
			console.log(`⏭️  ${this.giorno} ${voce.numero}. ${titolo} (needs ${manca.join(', ')})`)
			return false
		}
		for (const p of persone) {
			p.svuota()
			p.attesi = opzioni.attesi || []
		}
		let riuscito = true
		try {
			await fai()
		} catch (errore: any) {
			riuscito = false
			voce.esito = 'fallito'
			voce.errore = String(errore?.message || errore).slice(0, 2000)
		}
		// what the screens and the server say after it
		for (const p of persone) {
			const page = p.pagina
			if (page && !page.isClosed()) {
				await page.waitForTimeout(300)
				const controlli = [
					...(await largo(page)),
					...(await paroleCrude(page, opzioni.ammessi)),
					...(await nomiCrudi(page)),
					...(await toastDiErrore(page)),
					...(p.tocco ? await tocco(page) : []),
				]
				for (const t of controlli) this.trovati.push({ ...t, dove: `${p.descrizione} ${new URL(page.url()).pathname}` })
				if (!opzioni.senzaFoto || !riuscito) {
					const foto = await this.foto(p, titolo.slice(0, 40))
					if (foto) voce.schermate.push(foto)
				}
			}
			const accaduto = p.svuota()
			for (const e of accaduto.errori)
				this.trovati.push({ gravita: 'grave', cosa: 'Page error', dettaglio: e, dove: p.descrizione })
			for (const e of accaduto.console.filter((c) => !RUMORE.some(([r]) => r.test(c))))
				this.trovati.push({ gravita: 'minore', cosa: 'Console error', dettaglio: e, dove: p.descrizione })
			for (const r of accaduto.risposte)
				this.trovati.push({
					gravita: r.startsWith('5') ? 'grave' : 'minore',
					cosa: 'Server answered with an error',
					dettaglio: r,
					dove: p.descrizione,
				})
			for (const f of accaduto.fuori)
				this.trovati.push({ gravita: 'grave', cosa: 'A request left the bench', dettaglio: f, dove: p.descrizione })
		}
		if (oraBanco) {
			// every email the step made the centre send: its words, and never twice
			const posta = await this.banco.posta(undefined, oraBanco).catch(() => [])
			const stesse = new Set<string>()
			for (const m of posta) {
				if (this.emailViste.has(m.name)) continue
				this.emailViste.add(m.name)
				const dove = `email a ${(m.to || []).join(', ')}: «${m.subject.slice(0, 80)}»`
				for (const t of testoCrudo(`${m.subject}\n${m.text}`)) this.trovati.push({ ...t, dove })
				const chiave = `${(m.to || []).join(',')}|${m.subject}`
				if (stesse.has(chiave))
					this.trovati.push({ gravita: 'grave', cosa: 'The same email twice', dettaglio: m.subject, dove })
				stesse.add(chiave)
			}
			for (const e of await this.banco.errori(oraBanco).catch(() => [])) {
				const prima = (e.error || '').trim().split('\n').slice(-1)[0]
				this.trovati.push({
					gravita: 'grave',
					cosa: 'Error Log on the server',
					dettaglio: `${e.method}: ${prima}`.slice(0, 300),
					dove: 'server',
				})
			}
		}
		for (const t of this.trovati) {
			const nuovo = this.rapporto.segna({
				gravita: t.gravita,
				cosa: t.cosa,
				dettaglio: t.dettaglio,
				dove: t.dove,
				passo: this.passoCorrente,
				giorno: this.giorno,
				schermata: voce.schermate[0],
			})
			if (nuovo) voce.difetti += 1
		}
		if (riuscito && this.trovati.length) voce.esito = 'difetti'
		voce.secondi = (Date.now() - inizio) / 1000
		this.rapporto.passi.push(voce)
		if (opzioni.chiave) this.esiti[opzioni.chiave] = riuscito
		console.log(
			`${riuscito ? (this.trovati.length ? '⚠️ ' : '✅') : '❌'} ${this.giorno} ${voce.numero}. ${voce.ora} ${titolo}` +
				(voce.errore ? `\n     ${voce.errore.split('\n')[0]}` : '') +
				this.trovati.map((t) => `\n     · ${t.gravita} ${t.cosa}: ${(t.dettaglio || '').slice(0, 140)}`).join(''),
		)
		this.salva()
		return riuscito
	}

	/** A day begins: its night's jobs at five, then its first hour. */
	async giornata(nome: string, ora = '07:30') {
		this.giorno = nome
		await this.banco.orologio(`${this.copione.week[nome]} 05:00`)
		await this.notte()
		await this.alle(ora)
	}

	/** Open the page of a persona already in. */
	async vai(persona: Persona, indirizzo: string): Promise<Page> {
		const page = await persona.apri(this.browser, this.banco)
		await page.goto(indirizzo, { waitUntil: 'domcontentloaded' })
		return page
	}
}
