// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect, type Page } from '@playwright/test'
import { esatto, premi } from './azioni'
import type { Persona } from './persone'
import type { Settimana } from './settimana'

/** The staff's screens: the agenda's panel, a person's page, the settings. */

/** A page of the settings, opened by its key as a link opens it (`?settings=`). */
export async function impostazioni(s: Settimana, chi: Persona, chiave: string, sopra = '/crm/accoglienza') {
	const page = await chi.apri(s.browser, s.banco)
	await page.goto(`${sopra}?settings=${encodeURIComponent(chiave)}`, { waitUntil: 'domcontentloaded' })
	await expect(page.getByRole('dialog').first()).toBeVisible({ timeout: 30000 })
	return page
}

/** The toast an action shows: its words, or a failure when it is an error. */
export async function esito(page: Page, atteso?: RegExp): Promise<string> {
	const toast = page.locator('[data-sonner-toast]').last()
	await toast.waitFor({ timeout: 30000 })
	const testo = ((await toast.innerText()) || '').trim()
	if ((await toast.getAttribute('data-type')) === 'error') throw new Error(`Error toast: ${testo}`)
	if (atteso && !atteso.test(testo)) throw new Error(`Toast «${testo}» instead of ${atteso}`)
	return testo
}

export type Partecipante = {
	nome: string
	telefono?: string
	email?: string
	/** already a person of the centre: found by name */
	esistente?: boolean
}

export type NuovoAppuntamento = {
	giorno: string
	ora: string
	servizio: string
	persone: Partecipante[]
	/** a convention, as the select names it */
	chiPaga?: string
	autorizzazione?: string
}

async function scegliPersona(page: Page, chi: Persona, riga: number, p: Partecipante) {
	const righe = page.locator('.lucide-user').locator('xpath=..')
	const qui = righe.nth(riga)
	if (p.esistente) {
		await premi(chi, qui.getByRole('button', { name: 'Per chi è?' }))
		const cerca = page.locator('input[id^=headlessui-combobox-input]').last()
		await cerca.fill(p.nome)
		const opzione = page.getByRole('option', { name: new RegExp(p.nome) }).first()
		await opzione.waitFor({ timeout: 15000 })
		await premi(chi, opzione)
		return
	}
	await premi(chi, qui.getByRole('button', { name: 'Non è in DottorCloud? Scrivi un nome' }))
	await qui.getByPlaceholder('Nome', { exact: true }).fill(p.nome)
	if (p.telefono) await qui.getByPlaceholder('Telefono').fill(p.telefono)
	if (p.email) await qui.getByPlaceholder('Email').fill(p.email)
}

/** A booking the desk takes on the phone, through the agenda's «Nuovo»: returns
 * the appointment. */
export async function nuovoAppuntamento(s: Settimana, chi: Persona, a: NuovoAppuntamento): Promise<string> {
	const page = await chi.apri(s.browser, s.banco)
	await page.goto(`/crm/calendar?date=${a.giorno}`, { waitUntil: 'domcontentloaded' })
	await premi(chi, page.getByRole('button', { name: 'Nuovo', exact: true }))
	await premi(chi, page.getByLabel('Servizio'))
	await premi(chi, page.getByRole('option', { name: new RegExp(`^${a.servizio} ·`) }))
	for (const [i, persona] of a.persone.entries()) {
		if (i > 0) await premi(chi, page.getByRole('button', { name: /^Aggiungi un partecipante/ }))
		await scegliPersona(page, chi, i, persona)
	}
	// the day is the agenda's open one (``?date=``): the hour
	const inizio = page.locator('.lucide-clock').locator('xpath=..').locator('input').first()
	await inizio.fill(a.ora)
	await inizio.press('Enter')
	if (a.chiPaga) {
		await premi(chi, page.getByLabel('Chi paga'))
		await premi(chi, page.getByRole('option', { name: new RegExp(a.chiPaga) }).first())
		if (a.autorizzazione) await page.getByLabel('Autorizzazione').fill(a.autorizzazione)
	}
	const salvato = page.waitForResponse((r) => r.url().includes('crm.api.appointments.save_appointment'), {
		timeout: 30000,
	})
	await premi(chi, page.getByRole('button', { name: "Prenota l'appuntamento" }))
	const risposta = await salvato
	const corpo = await risposta.json().catch(() => ({}))
	if (!risposta.ok()) {
		const messaggi = corpo._server_messages
			? JSON.parse(corpo._server_messages).map((m: string) => JSON.parse(m).message)
			: []
		throw new Error(`The appointment was not booked: ${messaggi.join(' ') || risposta.status()}`)
	}
	const nome = typeof corpo.message === 'string' ? corpo.message : corpo.message?.name
	if (!nome) throw new Error(`No appointment in the answer: ${JSON.stringify(corpo).slice(0, 200)}`)
	return nome
}

/** The invoice dialog open on a draft: the client's details the desk asks for
 * where they are missing, how it was paid, «Emetti». Returns the toast's words. */
export type Intestataria = { name: string; vat: string; street: string; postcode: string; city: string }

export async function emettiLaBozza(
	s: Settimana,
	chi: Persona,
	page: Page,
	chiave: string,
	{ pagamento, azienda }: { pagamento?: RegExp; azienda?: Intestataria } = {},
): Promise<string> {
	const d = page.getByRole('dialog').last()
	await expect(d.getByRole('button', { name: 'Emetti', exact: true })).toBeVisible({ timeout: 30000 })
	if (azienda) {
		// made out to the company that pays: its VAT number, the SdI's code
		await premi(chi, d.getByLabel('Destinatario'))
		await premi(chi, page.getByRole('option', { name: /^Azienda o professionista/ }).first())
	}
	if (
		!(await d
			.getByLabel('Codice fiscale')
			.isVisible()
			.catch(() => false))
	)
		await premi(chi, d.getByRole('button', { name: 'Dati in fattura' }))
	const dati = s.persona(chiave)
	const campi: Array<[string, string, boolean?, boolean?]> = azienda
		? [
				['Nome in fattura', azienda.name, false, true],
				['Partita IVA', azienda.vat, false, true],
				['Codice fiscale', azienda.vat, false, true],
				['Indirizzo', azienda.street, true, true],
				['CAP', azienda.postcode, false, true],
				['Città', azienda.city, false, true],
				['Codice destinatario', '0000000', true, true],
			]
		: [
				['Codice fiscale', dati.fiscal_code],
				['Indirizzo', `${dati.address.street} ${dati.address.number}`, true],
				['CAP', dati.address.postcode],
				['Città', dati.address.city],
			]
	for (const [etichetta, valore, esatta, sempre] of campi) {
		const campo = d.getByLabel(etichetta, { exact: !!esatta }).first()
		if (sempre || !(await campo.inputValue().catch(() => 'x'))) await campo.fill(valore)
	}
	if (pagamento) {
		await premi(chi, d.getByLabel('Modalità di pagamento'))
		await premi(chi, page.getByRole('option', { name: pagamento }).first())
	}
	// the issue's own answer: a toast of the invoice before may still be on screen
	const emessa = page.waitForResponse((r) => r.url().includes('crm.invoicing.emissione.issue'), { timeout: 60000 })
	await premi(chi, d.getByRole('button', { name: 'Emetti', exact: true }))
	const risposta = await emessa
	if (!risposta.ok()) {
		const corpo = await risposta.json().catch(() => ({}))
		const messaggi = corpo._server_messages
			? JSON.parse(corpo._server_messages).map((m: string) => JSON.parse(m).message)
			: []
		throw new Error(`The invoice was not issued: ${messaggi.join(' ') || risposta.status()}`)
	}
	return esito(page, /emessa/i)
}

/** A person's page, on a tab. */
export async function persona(s: Settimana, chi: Persona, lead: string, scheda = 'summary'): Promise<Page> {
	const page = await chi.apri(s.browser, s.banco)
	await page.goto(`/crm/persone/${lead}#${scheda}`, { waitUntil: 'domcontentloaded' })
	await page.waitForLoadState('networkidle').catch(() => {})
	return page
}

export { esatto }
