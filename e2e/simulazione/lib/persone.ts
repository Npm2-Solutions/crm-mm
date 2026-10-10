// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import type { Browser, BrowserContext, BrowserContextOptions, Page } from '@playwright/test'
import { BASE, FINTI, type Banco } from './banco'

/** The devices the personas hold: what each screen of the week is tried at. */
export const DISPOSITIVI: Record<string, BrowserContextOptions & { tocco?: boolean; nome: string }> = {
	scrivania: { nome: 'computer 1440', viewport: { width: 1440, height: 900 } },
	scrivania_scura: { nome: 'computer 1440, tema scuro', viewport: { width: 1440, height: 900 }, colorScheme: 'dark' },
	tablet: { nome: 'tablet 820 in verticale', viewport: { width: 820, height: 1180 }, hasTouch: true, tocco: true },
	telefono: {
		nome: 'telefono 390',
		viewport: { width: 390, height: 844 },
		deviceScaleFactor: 2,
		isMobile: true,
		hasTouch: true,
		tocco: true,
	},
	piccolo: {
		nome: 'telefono 320',
		viewport: { width: 320, height: 640 },
		deviceScaleFactor: 2,
		isMobile: true,
		hasTouch: true,
		tocco: true,
	},
	di_lato: {
		nome: 'telefono di lato 844×390',
		viewport: { width: 844, height: 390 },
		deviceScaleFactor: 2,
		isMobile: true,
		hasTouch: true,
		tocco: true,
	},
	// a 390 phone with Android's large text (130%): the page is 300 points wide
	testo_grande: {
		nome: 'telefono 390 con il testo al 130%',
		viewport: { width: 300, height: 649 },
		deviceScaleFactor: 2.6,
		isMobile: true,
		hasTouch: true,
		tocco: true,
	},
	scuro: {
		nome: 'telefono 390, tema scuro',
		viewport: { width: 390, height: 844 },
		deviceScaleFactor: 2,
		isMobile: true,
		hasTouch: true,
		colorScheme: 'dark',
		tocco: true,
	},
}

/** What happened on a persona's pages since the step began. */
export type Accaduto = {
	errori: string[]
	console: string[]
	risposte: string[]
	fuori: string[]
}

/** The hosts a browser of the simulation may reach: the bench and the fakes. */
function ammesso(indirizzo: string): boolean {
	try {
		const host = new URL(indirizzo).host
		return (
			['data:', 'blob:', 'about:'].some((p) => indirizzo.startsWith(p)) ||
			host === new URL(BASE).host ||
			host === new URL(FINTI).host ||
			// the socket of the bench (another port of the same host)
			new URL(indirizzo).hostname === new URL(BASE).hostname
		)
	} catch {
		return true
	}
}

/** Somebody of the week: the staff with their level, a patient with their phone. */
/** The host of the video rooms on a bench with fakes (`crm.collaudo.prepara`). */
export const STANZE_VIDEO = 'video.example.com'

export class Persona {
	contesto?: BrowserContext
	pagina?: Page
	/** the video rooms this persona's browser opened */
	stanze: string[] = []
	accaduto: Accaduto = { errori: [], console: [], risposte: [], fuori: [] }
	/** 4xx answers a step expects (a refusal it is testing) */
	attesi: RegExp[] = []

	constructor(
		readonly chiave: string,
		readonly nome: string,
		readonly dispositivo: keyof typeof DISPOSITIVI,
		readonly email: string,
		readonly password: string | null,
		readonly ip: string,
	) {}

	get tocco(): boolean {
		return !!DISPOSITIVI[this.dispositivo].tocco
	}

	get descrizione(): string {
		return `${this.nome} (${DISPOSITIVI[this.dispositivo].nome})`
	}

	/** The persona's browser, opened the first time: their device, Italian, Rome's
	 * clock at the bench's hour, their own address on the network. */
	async apri(browser: Browser, banco: Banco): Promise<Page> {
		if (this.pagina && !this.pagina.isClosed()) return this.pagina
		const { nome: _nome, tocco: _tocco, ...opzioni } = DISPOSITIVI[this.dispositivo]
		this.contesto = await browser.newContext({
			...opzioni,
			locale: 'it-IT',
			timezoneId: 'Europe/Rome',
			baseURL: BASE,
			extraHTTPHeaders: { 'X-Forwarded-For': this.ip },
		})
		await this.contesto.clock.install({ time: banco.adesso() })
		banco.quandoSiSposta(async (istante) => {
			if (this.contesto) await this.contesto.clock.setSystemTime(istante).catch(() => {})
		})
		// nothing leaves the bench: a request elsewhere is stopped, and said; the
		// video rooms' host `centro()` names for a bench with fakes is one of them
		await this.contesto.route(
			(url) => !ammesso(url.toString()),
			async (rotta) => {
				const indirizzo = new URL(rotta.request().url())
				if (indirizzo.hostname === STANZE_VIDEO) {
					this.stanze.push(indirizzo.toString())
					await rotta.fulfill({
						status: 200,
						contentType: 'text/html; charset=utf-8',
						body: `<!doctype html><title>Stanza video</title><h1>Stanza ${indirizzo.pathname}</h1>`,
					})
					return
				}
				this.accaduto.fuori.push(rotta.request().url().slice(0, 160))
				await rotta.abort('blockedbyclient')
			},
		)
		this.pagina = await this.contesto.newPage()
		this.ascolta(this.pagina)
		this.contesto.on('page', (altra) => this.ascolta(altra))
		return this.pagina
	}

	private ascolta(page: Page) {
		page.on('pageerror', (e) => this.accaduto.errori.push(e.message.slice(0, 300)))
		page.on('console', (m) => {
			if (m.type() === 'error') this.accaduto.console.push(m.text().slice(0, 300))
		})
		page.on('response', (r) => {
			const stato = r.status()
			const indirizzo = r.url()
			if (stato < 400 || !ammesso(indirizzo)) return
			// a bench without realtime for the test site (SIM_SENZA_SOCKET)
			if (process.env.SIM_SENZA_SOCKET && indirizzo.includes('/socket.io/')) return
			const corto = `${stato} ${r.request().method()} ${indirizzo.replace(BASE, '').slice(0, 140)}`
			if (stato >= 500 || !this.attesi.some((a) => a.test(corto))) this.accaduto.risposte.push(corto)
		})
	}

	/** What happened since the last time it was asked. */
	svuota(): Accaduto {
		const fatto = this.accaduto
		this.accaduto = { errori: [], console: [], risposte: [], fuori: [] }
		return fatto
	}

	/** Staff sign in as the framework's page lets them, through its form. */
	async entra(browser: Browser, banco: Banco, { dalModulo = false } = {}): Promise<Page> {
		const page = await this.apri(browser, banco)
		if (!this.password) throw new Error(`${this.nome} has no password`)
		if (dalModulo) {
			await page.goto('/login')
			await page.locator('#login_email').fill(this.email)
			await page.locator('#login_password').fill(this.password)
			await page.locator('form.form-login button[type=submit]').first().click()
			await page.waitForURL((u) => !u.pathname.startsWith('/login'), { timeout: 30000 })
			// where the sign-in lands, settled: a page left half-loaded aborts its calls
			await page.waitForLoadState('networkidle').catch(() => {})
		} else {
			const risposta = await page.request.post('/api/method/login', {
				form: { usr: this.email, pwd: this.password },
			})
			if (!risposta.ok()) throw new Error(`${this.email} cannot sign in: ${risposta.status()}`)
		}
		return page
	}
}
