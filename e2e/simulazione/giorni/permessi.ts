// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import type { Page } from '@playwright/test'
import type { Persona } from '../lib/persone'
import type { Settimana } from '../lib/settimana'

/** Every evening, what each one must not open, asked from their own browser as
 * the screens would ask it: refused in words, or answered with nothing - and the
 * answer never carries what it refused. */

type Risposta = { stato: number; corpo: any; testo: string }

type Prova = {
	/** what is tried, in the report's words */
	cosa: string
	metodo: string
	args?: (s: Settimana) => Record<string, unknown> | null
	post?: boolean
	/** an answer of 200 that says nothing: what it must look like */
	vuota?: (corpo: any) => boolean
	/** words that must not be in the answer (a person's name, a code) */
	segreti?: (s: Settimana) => string[]
}

const persona = (chiave: string) => (s: Settimana) => s.stato[chiave]?.persona

const CARTELLA = (chiave: string): Prova => ({
	cosa: `the clinical record of ${chiave}`,
	metodo: 'crm.clinica.cartella.get_record',
	args: (s) => (persona(chiave)(s) ? { lead: persona(chiave)(s) } : null),
	vuota: (c) => !c?.message?.records?.length,
})

const PROVE: Record<string, Prova[]> = {
	segreteria: [
		CARTELLA('giulia'),
		{ cosa: 'the Stripe connection', metodo: 'crm.pagamenti.collegamento.get_stripe_connection' },
		{ cosa: 'the exports of the centre’s data', metodo: 'crm.esportazione.esporta.get_exports' },
		{ cosa: 'the Twilio connection', metodo: 'crm.telephony.collegamento.get_twilio_connection' },
	],
	marketing: [
		CARTELLA('giulia'),
		{
			cosa: 'the invoices',
			metodo: 'frappe.client.get_list',
			args: () => ({ doctype: 'CRM Invoice', fields: JSON.stringify(['name', 'billing_name', 'grand_total']) }),
			vuota: (c) => !c?.message?.length,
		},
		{
			cosa: 'people’s email and mobile in full',
			metodo: 'frappe.client.get_list',
			args: () => ({
				doctype: 'CRM Lead',
				fields: JSON.stringify(['name', 'email', 'mobile_no']),
				limit_page_length: 50,
			}),
			vuota: () => true,
			segreti: (s) => s.copione.people.flatMap((p) => [p.email, p.mobile].filter(Boolean) as string[]),
		},
		{ cosa: 'the exports of the centre’s data', metodo: 'crm.esportazione.esporta.get_exports' },
	],
	fisioterapista: [
		{ cosa: 'the exports of the centre’s data', metodo: 'crm.esportazione.esporta.get_exports' },
		{ cosa: 'the Stripe connection', metodo: 'crm.pagamenti.collegamento.get_stripe_connection' },
	],
	dietista: [CARTELLA('roberto'), CARTELLA('sara')],
	paolo: [
		{
			cosa: 'another person’s invoices in the area',
			metodo: 'crm.area.api.get_invoices',
			args: (s) => (persona('giulia')(s) ? { person: persona('giulia')(s) } : null),
			segreti: (s) => [s.p('giulia').nome, s.persona('giulia').fiscal_code],
		},
		{
			cosa: 'another person’s appointments in the area',
			metodo: 'crm.area.api.get_appointments',
			args: (s) => (persona('giulia')(s) ? { person: persona('giulia')(s) } : null),
			segreti: (s) => [s.p('giulia').nome],
		},
		{
			cosa: 'the list of people',
			metodo: 'frappe.client.get_list',
			args: () => ({ doctype: 'CRM Lead', fields: JSON.stringify(['name', 'lead_name']) }),
			vuota: (c) => !c?.message?.length,
		},
	],
}

async function chiedi(page: Page, prova: Prova, args: Record<string, unknown>): Promise<Risposta> {
	const indirizzo = `/api/method/${prova.metodo}`
	const risposta = prova.post
		? await page.request.post(indirizzo, { form: args as Record<string, string> })
		: await page.request.get(indirizzo, { params: args as Record<string, string> })
	const testo = await risposta.text()
	let corpo: any = {}
	try {
		corpo = JSON.parse(testo)
	} catch {
		corpo = {}
	}
	return { stato: risposta.status(), corpo, testo }
}

/** The words a refusal says: the server's message, never only an exception's name. */
function parole(corpo: any): string {
	try {
		const messaggi = JSON.parse(corpo?._server_messages || '[]').map((m: string) => JSON.parse(m).message)
		return messaggi.join(' ')
	} catch {
		return ''
	}
}

export async function permessi(s: Settimana) {
	await s.alle('20:00')
	for (const [chiave, prove] of Object.entries(PROVE)) {
		const chi: Persona = s.p(chiave)
		const staff = !!chi.password
		await s.passo(
			`Chi non deve, non apre: ${chi.nome}`,
			chi,
			async () => {
				let page: Page
				if (staff) page = await s.alLavoro(chi)
				else {
					if (!chi.pagina) {
						s.nota('Not in the area today: nothing to try')
						return
					}
					page = chi.pagina
				}
				for (const prova of prove) {
					const args = prova.args ? prova.args(s) : {}
					if (args === null) continue
					const r = await chiedi(page, prova, args)
					const rifiutata = r.stato === 403 || r.stato === 401
					if (r.stato >= 500) {
						s.difetto('grave', `Asking ${prova.cosa} breaks the server`, `${r.stato} ${prova.metodo}`)
						continue
					}
					if (rifiutata) {
						const detto = parole(r.corpo)
						s.verifica(
							detto && !/PermissionError|Not permitted$/.test(detto),
							`The refusal of ${prova.cosa} says why in words`,
							detto || r.testo.slice(0, 160),
							'minore',
						)
					} else {
						s.verifica(
							r.stato === 200 && prova.vuota?.(r.corpo),
							`${chi.nome} must not read ${prova.cosa}`,
							`${r.stato} ${r.testo.slice(0, 200)}`,
						)
					}
					for (const segreto of prova.segreti?.(s) || []) {
						if (segreto && r.testo.includes(segreto))
							s.difetto('grave', `The answer about ${prova.cosa} carries what it refuses`, segreto)
					}
				}
				// a patient never reaches the staff's screens
				if (!staff) {
					await page.goto('/crm', { waitUntil: 'domcontentloaded' })
					await page.waitForLoadState('networkidle').catch(() => {})
					s.verifica(
						!new URL(page.url()).pathname.startsWith('/crm'),
						'A patient does not reach the staff’s screens',
						page.url(),
					)
				}
			},
			{ chiave: `${s.giorno}.permessi.${chiave}`, senzaFoto: true, attesi: [/^40[13] /] },
		)
	}
}
