// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { request, type APIRequestContext } from '@playwright/test'

export const BASE = process.env.SIM_BASE || 'http://collaudo.localhost:8000'
export const FINTI = process.env.SIM_FINTI || 'http://127.0.0.1:8791'
const AGENZIA = process.env.SIM_ADMIN || 'Administrator'
const PAROLA = process.env.SIM_ADMIN_PASSWORD || 'admin'

export type Email = {
	name: string
	at: string
	to: string[]
	subject: string
	text: string
	links: string[]
	status: string
	reference: [string, string]
}

/** The bench as the agency reaches it: its clock, its scheduled jobs, the mail its
 * people received, its records to compare the screens with. Never a screen: what a
 * persona does goes through the browser. */
export class Banco {
	api!: APIRequestContext
	/** seconds between the real clock and the bench's */
	scarto = 0
	/** the bench's hour when the clock was last moved, as the centre reads it */
	ora = ''
	private orologi: Array<(istante: Date) => Promise<void>> = []

	static async apri(): Promise<Banco> {
		const banco = new Banco()
		banco.api = await request.newContext({ baseURL: BASE })
		const risposta = await banco.api.post('/api/method/login', {
			form: { usr: AGENZIA, pwd: PAROLA },
		})
		if (!risposta.ok()) throw new Error(`The agency cannot sign in: ${risposta.status()}`)
		const adesso = await banco.chiama('crm.collaudo.tempo.adesso', {}, 'GET')
		banco.scarto = adesso.offset
		banco.ora = adesso.now
		return banco
	}

	/** A link opened by nobody signed in, its redirect not followed: where it goes. */
	async richiestaGrezza(indirizzo: string): Promise<{ status: number; location: string | null }> {
		const ospite = await request.newContext({ baseURL: BASE })
		try {
			const risposta = await ospite.get(indirizzo, { maxRedirects: 0 })
			return { status: risposta.status(), location: risposta.headers()['location'] || null }
		} finally {
			await ospite.dispose()
		}
	}

	async chiama(metodo: string, dati: Record<string, unknown> = {}, verbo: 'GET' | 'POST' = 'POST') {
		const forma = Object.fromEntries(
			Object.entries(dati).map(([k, v]) => [k, typeof v === 'string' ? v : JSON.stringify(v)]),
		)
		const risposta =
			verbo === 'GET'
				? await this.api.get(`/api/method/${metodo}`, { params: forma })
				: await this.api.post(`/api/method/${metodo}`, { form: forma })
		const corpo = await risposta.json().catch(() => ({}))
		if (!risposta.ok()) {
			const messaggi = corpo._server_messages
				? JSON.parse(corpo._server_messages)
						.map((m: string) => JSON.parse(m).message)
						.join(' | ')
				: corpo.exception || risposta.status()
			throw new Error(`${metodo}: ${messaggi}`)
		}
		return corpo.message
	}

	/** The bench's hour now, as the centre writes it (``YYYY-MM-DD HH:MM``). */
	oraAdesso(): string {
		const parti = new Intl.DateTimeFormat('sv-SE', {
			timeZone: 'Europe/Rome',
			year: 'numeric',
			month: '2-digit',
			day: '2-digit',
			hour: '2-digit',
			minute: '2-digit',
			hourCycle: 'h23',
		}).format(this.adesso())
		return parti.replace('T', ' ')
	}

	/** The bench's hour as a browser holds it. */
	adesso(): Date {
		return new Date(Date.now() + this.scarto * 1000)
	}

	/** Called whenever the clock moves: a persona's browser follows it. */
	quandoSiSposta(segui: (istante: Date) => Promise<void>) {
		this.orologi.push(segui)
	}

	/** The bench's clock to ``quando`` (the centre's ``YYYY-MM-DD HH:MM``), the fake
	 * services' and every browser's with it. */
	async orologio(quando: string) {
		const stato = await this.chiama('crm.collaudo.tempo.imposta', { quando })
		this.scarto = stato.offset
		this.ora = stato.now
		await fetch(`${FINTI}/_orologio`, { method: 'POST', body: String(this.scarto) })
		const istante = this.adesso()
		for (const segui of this.orologi) await segui(istante)
		return stato
	}

	/** A scheduled job, now, at the bench's hour. */
	async esegui(metodo: string) {
		return this.chiama('crm.collaudo.tempo.esegui', { metodo })
	}

	/** The mail ``a`` received (everybody's, without it) since ``dopo``. */
	async posta(a?: string, dopo?: string): Promise<Email[]> {
		return this.chiama('crm.collaudo.api.posta', { ...(a ? { a } : {}), ...(dopo ? { dopo } : {}) }, 'GET')
	}

	/** The newest email to ``a`` whose subject or words match, waiting for it a while
	 * (a job may write it after the request). */
	async attendiPosta(
		a: string,
		cerca: RegExp,
		{ dopo, secondi = 25 }: { dopo?: string; secondi?: number } = {},
	): Promise<Email> {
		const fine = Date.now() + secondi * 1000
		let viste: Email[] = []
		while (Date.now() < fine) {
			viste = await this.posta(a, dopo)
			const trovata = [...viste].reverse().find((m) => cerca.test(m.subject) || cerca.test(m.text))
			if (trovata) return trovata
			await new Promise((fatto) => setTimeout(fatto, 1000))
		}
		throw new Error(`No email to ${a} matching ${cerca} (seen: ${viste.map((m) => m.subject).join(' · ') || 'none'})`)
	}

	async sms(a?: string, dopo?: string) {
		return this.chiama('crm.collaudo.api.sms', { ...(a ? { a } : {}), ...(dopo ? { dopo } : {}) }, 'GET')
	}

	async errori(dopo: string): Promise<Array<{ name: string; method: string; error: string }>> {
		return this.chiama('crm.collaudo.api.errori', { dopo }, 'GET')
	}

	/** A value of a record (of a child table: ``genitore`` names its parent's type). */
	async valore(doctype: string, filtri: unknown, campo: string | string[], genitore?: string) {
		const risposta = await this.chiama(
			'frappe.client.get_value',
			{ doctype, filters: filtri, fieldname: campo, ...(genitore ? { parent: genitore } : {}) },
			'GET',
		)
		return Array.isArray(campo) ? risposta : risposta?.[campo]
	}

	/** The status of one person in an appointment. */
	async statoDi(appuntamento: string, persona: string): Promise<string | undefined> {
		return this.valore(
			'CRM Appointment Participant',
			{ parent: appuntamento, party: persona },
			'status',
			'CRM Appointment',
		)
	}

	async lista(
		doctype: string,
		filtri: unknown = {},
		campi: string[] = ['name'],
		{ ordine = 'creation asc', limite = 500, genitore }: { ordine?: string; limite?: number; genitore?: string } = {},
	): Promise<any[]> {
		return this.chiama(
			'frappe.client.get_list',
			{
				doctype,
				filters: filtri,
				fields: campi,
				order_by: ordine,
				limit_page_length: limite,
				...(genitore ? { parent: genitore } : {}),
			},
			'GET',
		)
	}

	async conta(doctype: string, filtri: unknown = {}): Promise<number> {
		return this.chiama('frappe.client.get_count', { doctype, filters: filtri }, 'GET')
	}

	async documento(doctype: string, nome: string) {
		const risposta = await this.api.get(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(nome)}`)
		if (!risposta.ok()) throw new Error(`${doctype} ${nome}: ${risposta.status()}`)
		return (await risposta.json()).data
	}

	async finti(porta: string, corpo?: string) {
		const risposta = await fetch(`${FINTI}/${porta}`, {
			method: corpo === undefined ? 'GET' : 'POST',
			body: corpo,
		})
		return risposta.json()
	}
}
