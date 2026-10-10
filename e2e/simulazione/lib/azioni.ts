// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect, type Locator, type Page } from '@playwright/test'
import { BASE, FINTI } from './banco'
import type { Persona } from './persone'
import type { Settimana } from './settimana'

/** What people do again and again in the week, through the screens. */

/** A tap on a touch screen, a click elsewhere. */
export async function premi(persona: Persona, azione: Locator) {
	await azione.scrollIntoViewIfNeeded().catch(() => {})
	if (persona.tocco) await azione.tap()
	else await azione.click()
}

export function esatto(testo: string): RegExp {
	return new RegExp(`^\\s*${testo.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*$`)
}

// -- /prenota ------------------------------------------------------------------------------

export type Prenotazione = {
	sede?: string
	servizio: string
	professionista?: string
	giorno: string
	ora: string
	nome: string
	email: string
	telefono?: string
	perAltro?: { nome: string; relazione?: string }
	convenzione?: string
	tessera?: string
	/** written where the page asks it: a payment online invoiced as healthcare */
	codiceFiscale?: string
	marketing?: boolean
	/** the cards tried on Stripe's page, in order */
	carte?: string[]
}

/** Up to the day's times on /prenota: the location, the service, who, the day. */
export async function finoAgliOrari(s: Settimana, chi: Persona, p: Prenotazione): Promise<Page> {
	const page = await chi.apri(s.browser, s.banco)
	await page.goto('/prenota', { waitUntil: 'domcontentloaded' })
	const main = page.locator('#main')
	await expect(main.locator('button.service, .staff-grid').first()).toBeVisible()
	if (await page.getByText('In quale sede?').isVisible()) {
		await premi(chi, main.locator('button.person', { hasText: p.sede || 'Qualsiasi sede' }).first())
	}
	await premi(
		chi,
		main.locator('button.service').filter({ has: page.locator('.name', { hasText: esatto(p.servizio) }) }),
	)
	await page.waitForTimeout(300)
	if (await page.getByText('Con chi vuoi prenotare?').isVisible()) {
		await premi(chi, main.locator('button.person', { hasText: p.professionista || 'Chiunque disponibile' }).first())
	}
	await expect(main.locator('.month')).toBeVisible()
	await expect(main.locator('.skeleton')).toHaveCount(0, { timeout: 30000 })
	for (let i = 0; i < 3; i++) {
		if (await main.locator(`button.day[data-day="${p.giorno}"]`).count()) break
		await premi(chi, main.locator('button.icon-btn').last())
		await expect(main.locator('.skeleton')).toHaveCount(0, { timeout: 30000 })
	}
	const giorno = main.locator(`button.day[data-day="${p.giorno}"]`)
	await expect(giorno, `${p.giorno} offered for ${p.servizio}`).toBeEnabled()
	await premi(chi, giorno)
	return page
}

/** A booking on /prenota as the person makes it, paid on Stripe's page when the
 * service asks: returns the booking's token. */
export async function prenotaOnline(s: Settimana, chi: Persona, p: Prenotazione): Promise<string> {
	const page = await finoAgliOrari(s, chi, p)
	const main = page.locator('#main')
	const orario = main.locator('button.time', { hasText: new RegExp(`^\\s*${p.ora}`) }).first()
	await main
		.locator('button.time')
		.first()
		.waitFor({ timeout: 15000 })
		.catch(() => {})
	if (!(await orario.count())) {
		const liberi = await main.locator('button.time').allInnerTexts()
		throw new Error(
			`${p.ora} is not free on ${p.giorno} for ${p.servizio}; free: ${liberi.map((t) => t.split('\n')[0]).join(', ')}`,
		)
	}
	await premi(chi, orario)
	await compilaDati(s, chi, page, p)
	await s.dito(chi, main.locator('button.primary[type=submit]'))
	await premi(chi, main.locator('button.primary[type=submit]'))
	// a deposit goes to Stripe's page; else the booking is done here
	await Promise.race([
		page.waitForURL((u) => u.toString().startsWith(`${FINTI}/checkout/`), { timeout: 45000 }),
		main.locator('.done-hero').waitFor({ timeout: 45000 }),
	])
	if (page.url().startsWith(FINTI)) await pagaSuStripe(s, chi, page, p.carte || ['4242424242424242'])
	await expect(main.locator('.done-hero h2')).toBeVisible({ timeout: 90000 })
	const token = new URL(page.url()).searchParams.get('token')
	if (!token) throw new Error('No token in the booking page address')
	return token
}

export async function compilaDati(s: Settimana, chi: Persona, page: Page, p: Prenotazione) {
	const main = page.locator('#main')
	await expect(main.locator('#f-full_name')).toBeVisible()
	if (p.perAltro) {
		await premi(chi, main.getByRole('button', { name: "Per un'altra persona" }))
		await main.locator('#f-for_name').fill(p.perAltro.nome)
		if (p.perAltro.relazione) await main.locator('#f-for_relation').selectOption(p.perAltro.relazione)
	}
	await main.locator('#f-full_name').fill(p.nome)
	await main.locator('#f-email').fill(p.email)
	if (p.telefono && (await main.locator('#f-phone').count())) await main.locator('#f-phone').fill(p.telefono)
	if (p.convenzione) {
		await main.locator('#f-convention').selectOption({ label: p.convenzione })
		if (p.tessera) await main.locator('#f-card_number').fill(p.tessera)
	}
	// what is paid online is invoiced the day it arrives: its codice fiscale, the
	// child's for a child (the field says whose)
	const cf = main.getByRole('textbox', { name: /^Codice fiscale/ })
	if (await cf.count()) {
		const chiViene = p.perAltro
			? s.copione.people.find((x) => `${x.first_name} ${x.last_name}` === p.perAltro?.nome)
			: s.copione.people.find((x) => x.email === p.email)
		const codice = p.codiceFiscale || chiViene?.fiscal_code
		if (codice) await cf.fill(codice)
		else s.nota(`/prenota asked a codice fiscale ${chi.nome} did not give`)
	}
	if (await main.locator('#f-consent').count()) await main.locator('#f-consent').check()
	if (p.marketing && (await main.locator('#f-marketing').count())) await main.locator('#f-marketing').check()
}

/** Stripe's hosted page: the cards tried in order until one goes through. */
export async function pagaSuStripe(s: Settimana, chi: Persona, page: Page, carte: string[]) {
	// the form posts and the page that comes is the answer: back on the bench, an
	// error, or the bank asking to confirm
	const invia = async (azione: Locator) => {
		await Promise.all([
			page.waitForEvent('framenavigated', { predicate: (f) => f === page.mainFrame(), timeout: 60000 }),
			premi(chi, azione),
		])
		await page.waitForLoadState('domcontentloaded')
	}
	for (const [i, carta] of carte.entries()) {
		await expect(page.locator('#carta')).toBeVisible()
		await page.locator('#carta').fill(carta.replace(/(\d{4})(?=\d)/g, '$1 '))
		await page.locator('#titolare').fill(chi.nome)
		await s.dito(chi, page.locator('[data-azione=paga]'))
		await invia(page.locator('[data-azione=paga]'))
		if (page.url().startsWith(FINTI) && (await page.locator('[data-azione=conferma]').count())) {
			s.nota(`${chi.nome}: la banca chiede di confermare il pagamento`)
			await invia(page.locator('[data-azione=conferma]'))
		}
		if (!page.url().startsWith(FINTI)) return
		const errore = await page
			.locator('.errore')
			.textContent()
			.catch(() => '')
		s.nota(`${chi.nome}: carta che finisce per ${carta.slice(-4)} rifiutata (${(errore || '').trim()})`)
		if (i === carte.length - 1) throw new Error(`Every card was declined: ${errore}`)
	}
}

// -- the mail ------------------------------------------------------------------------------

/** The link of an email that leads to the bench, the first one matching. */
export function collegamento(links: string[], cerca: RegExp): string {
	const trovato = links.find((l) => cerca.test(l) && (l.startsWith(BASE) || l.startsWith('/')))
	if (!trovato) throw new Error(`No link matching ${cerca} in: ${links.join(' ')}`)
	return trovato.startsWith('/') ? BASE + trovato : trovato
}
