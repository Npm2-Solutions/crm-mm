// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect, type Page } from '@playwright/test'
import { premi } from './azioni'
import type { Persona } from './persone'
import { esito } from './scrivania'

/** What a practitioner does in a person's Clinic tab: a visit on a clinical
 * sheet, filled as the questions ask, signed. */

/** «Nuova visita» on a sheet (its words, as the menu says them). */
export async function nuovaVisita(chi: Persona, page: Page, scheda: string | RegExp) {
	const nuova = page.getByRole('button', { name: 'Nuova visita' }).first()
	await expect(nuova).toBeVisible({ timeout: 30000 })
	await premi(chi, nuova)
	await premi(chi, page.getByRole('menuitem', { name: scheda }).first())
	await expect(page.getByRole('button', { name: 'Firma', exact: true })).toBeVisible()
}

/** A question's words, as its control is named by them (a required one's mark
 * may be read with them). */
export function domanda(parole: string): RegExp {
	return new RegExp(`^\\s*${parole.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\*?\\s*$`)
}

/** A question that takes words or a number, by its words. */
export async function scrivi(page: Page, parole: string, valore: string) {
	await page.getByLabel(domanda(parole)).first().fill(valore)
}

/** A choice among buttons: the question's group, the option's words. */
export async function scegli(chi: Persona, page: Page, domanda: string, opzione: string) {
	const gruppo = page
		.getByRole('radiogroup', { name: domanda })
		.or(page.getByRole('group', { name: domanda }))
		.first()
	await premi(
		chi,
		gruppo
			.getByRole('radio', { name: opzione })
			.or(gruppo.getByRole('checkbox', { name: opzione }))
			.first(),
	)
}

/** A point on the body chart, with its words and how much it hurts. */
export async function puntoSulCorpo(
	chi: Persona,
	page: Page,
	{ vista = 'Davanti', x, y, parole, quanto }: { vista?: string; x: number; y: number; parole: string; quanto: number },
) {
	const sagoma = page.getByRole('img', { name: vista, exact: true }).first()
	await sagoma.scrollIntoViewIfNeeded()
	const box = await sagoma.boundingBox()
	if (!box) throw new Error('The body chart is not drawn')
	// a fraction of the outline, as a finger finds it
	const punto = { x: box.width * x, y: box.height * y }
	if (chi.tocco) await sagoma.tap({ position: punto })
	else await sagoma.click({ position: punto })
	await page.getByLabel('Cosa senti, dove').last().fill(parole)
	const intensita = page.getByRole('group', { name: /Quanto, da 0/ }).last()
	await premi(chi, intensita.getByRole('button', { name: String(quanto), exact: true }))
}

/** «Firma»: the visit is signed, its report made. Returns the record. */
export async function firmaLaVisita(chi: Persona, page: Page): Promise<any> {
	const salvata = page.waitForResponse((r) => r.url().includes('crm.clinica.cartella.save_record'), { timeout: 60000 })
	await premi(chi, page.getByRole('button', { name: 'Firma', exact: true }))
	const risposta = await salvata
	const corpo = await risposta.json().catch(() => ({}))
	if (!risposta.ok()) {
		const messaggi = corpo._server_messages
			? JSON.parse(corpo._server_messages).map((m: string) => JSON.parse(m).message)
			: []
		throw new Error(`The visit was not signed: ${messaggi.join(' ') || risposta.status()}`)
	}
	await esito(page, /Firmat/)
	return corpo.message
}
