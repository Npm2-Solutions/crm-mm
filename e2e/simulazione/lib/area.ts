// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect, type Page } from '@playwright/test'
import { BASE } from './banco'
import { premi } from './azioni'
import type { Persona } from './persone'
import type { Settimana } from './settimana'

/** The client area as a person reaches it: from the link of an email, or with a
 * code by email; already in, it is just open. */
export async function entraNellArea(s: Settimana, chi: Persona, { link }: { link?: string } = {}): Promise<Page> {
	const page = await chi.apri(s.browser, s.banco)
	if (link) {
		await page.goto(link, { waitUntil: 'domcontentloaded' })
		// the link's door («Entra»), the code's (a link already spent), or already in
		const entra = page.getByRole('button', { name: 'Entra', exact: true })
		const email = page.getByLabel('Email')
		await expect(
			entra
				.or(email)
				.or(page.getByText(/Ciao, /))
				.first(),
		).toBeVisible({ timeout: 30000 })
		if ((await entra.isVisible()) && !(await email.isVisible())) {
			await s.dito(chi, entra)
			await premi(chi, entra)
		}
	} else {
		await page.goto('/area', { waitUntil: 'domcontentloaded' })
	}
	const porta = page.getByRole('heading', { name: 'Entra nella tua area' })
	const dentro = page.getByText(/Ciao, /).first()
	await expect(porta.or(dentro)).toBeVisible({ timeout: 30000 })
	if (await dentro.isVisible().catch(() => false)) return page
	// the door: the email, a code to it
	const dopo = s.banco.ora
	await page.getByLabel('Email').fill(chi.email)
	await s.dito(chi, page.getByRole('button', { name: 'Mandami il codice' }))
	await premi(chi, page.getByRole('button', { name: 'Mandami il codice' }))
	const mail = await s.banco.attendiPosta(chi.email, /codice/i, { dopo })
	const codice = /\b(\d{6})\b/.exec(`${mail.subject} ${mail.text}`)?.[1]
	if (!codice) throw new Error(`No code in «${mail.subject}»`)
	await page.getByLabel('Il codice').fill(codice)
	await premi(chi, page.getByRole('button', { name: 'Entra', exact: true }))
	await expect(dentro).toBeVisible({ timeout: 30000 })
	return page
}

/** The link to the area an email carries, if it has one. */
export function linkDellArea(links: string[]): string | undefined {
	return (
		links.find((l) => l.includes('/area/login?link=')) ||
		links.find((l) => l.startsWith(`${BASE}/area`) || l.includes('/area'))
	)
}

/** A signature drawn with a finger, or the mouse, on a pad (a canvas). */
export async function firmaSulPad(page: Page, tela: import('@playwright/test').Locator) {
	await tela.scrollIntoViewIfNeeded()
	const box = await tela.boundingBox()
	if (!box) throw new Error('The signature pad is not drawn')
	const y = box.y + box.height / 2
	await page.mouse.move(box.x + box.width * 0.15, y)
	await page.mouse.down()
	for (let i = 1; i <= 12; i++) {
		await page.mouse.move(box.x + box.width * (0.15 + i * 0.05), y + (i % 2 ? -1 : 1) * box.height * 0.15, {
			steps: 3,
		})
	}
	await page.mouse.up()
}

/** The forms the area says to fill before the appointment: each one opened on the
 * forms page, its consents answered, signed with a finger, back to the area. */
export async function compilaIModuli(
	s: Settimana,
	chi: Persona,
	page: Page,
	{ consensi = true }: { consensi?: boolean } = {},
): Promise<number> {
	const compila = page.getByRole('button', { name: /^(Compila|Continua)$/ }).first()
	await expect(compila).toBeVisible({ timeout: 30000 })
	await s.dito(chi, compila)
	await premi(chi, compila)
	await page.waitForURL(/\/modulo\//, { timeout: 30000 })
	let firmati = 0
	for (let giro = 0; giro < 5; giro++) {
		const scelta = page.locator('button.opt:not([disabled])').first()
		if (await scelta.isVisible({ timeout: 3000 }).catch(() => false)) await premi(chi, scelta)
		const invia = page.locator('button.primary').last()
		await expect(invia).toBeVisible({ timeout: 30000 })
		// each consent: the person's yes (or no)
		for (const blocco of await page.locator('.consent').all()) {
			const si = blocco.getByRole('button', { name: consensi ? 'Acconsento' : 'Non acconsento', exact: true })
			const solo = blocco.getByRole('button', { name: 'Acconsento', exact: true })
			await premi(chi, (await si.count()) ? si.first() : solo.first())
		}
		for (const tela of await page.locator('canvas').all()) await firmaSulPad(page, tela)
		await s.dito(chi, invia)
		await premi(chi, invia)
		firmati += 1
		const fatto = page.getByText(/È tutto fatto|Grazie|Torna ai moduli/).first()
		await expect(fatto).toBeVisible({ timeout: 60000 })
		const indietro = page.getByRole('button', { name: /Torna ai moduli/ })
		if (!(await indietro.isVisible().catch(() => false))) break
		await premi(chi, indietro)
		if (!(await page.locator('button.opt:not([disabled])').count())) break
	}
	return firmati
}
