// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import type { Locator, Page } from '@playwright/test'

/**
 * What holds after every step, on every persona's screen: nothing wider than the
 * device, no raw code or English word where Italian is read, the actions a finger
 * takes big enough. The page's errors, the server's answers and what tried to leave
 * the bench are collected as they happen (`persone.ts`).
 */

/** Words and codes that never reach an Italian reader: a code of the engine, a
 * state as the database keeps it, a value the code forgot to fill. */
export const CRUDE: Array<[RegExp, string]> = [
	[/\bundefined\b/, 'undefined'],
	[/\bNaN\b/, 'NaN'],
	[/\[object \w+\]/, '[object …]'],
	[/(^|[\s(:])null([\s).,;]|$)/, 'null'],
	[/\{\d\}|\{\{\s*\w+\s*\}\}/, 'a placeholder left unfilled'],
	[/\bEUR\b/, 'EUR'],
	[/\bMP\d\d\b/, 'a payment code (MP…)'],
	[/\bRF\d\d\b/, 'a tax regime code (RF…)'],
	[/\bTD\d\d\b/, 'a document code (TD…)'],
	[/\bN[1-7](\.\d)?\b(?!\s*(°|gr|g\b))/, 'a VAT nature code (N…)'],
	[
		/\b(Scheduled|Draft|Cancelled|Confirmed|Completed|Pending|Submitted|Unpaid|Overdue|Booked|Arrived|Attended|No Show)\b/,
		'a state in English',
	],
	[
		/\b(Save|Cancel|Submit|Delete|Loading|Search|Close|Back|Next|Previous|Today|Tomorrow|Yesterday|No results|Not found|Something went wrong|Are you sure|Required|Mandatory|Select|Add row|Upload|Download|Send|Confirm|Discard)\b/,
		'an English word of the interface',
	],
	[/\b\d{4}-\d{2}-\d{2}\b/, 'a date as the database writes it'],
	[/\b(sk|pk|rk)_(test|live)_\w+/, 'a Stripe key'],
	[
		/\b(Europe|America|Asia|Africa|Australia|Pacific|Atlantic|Indian)\/[A-Z][A-Za-z_]+/,
		'a time zone as the database names it',
	],
	[/Traceback|Exception:|frappe\.exceptions/, 'a traceback'],
]

export type Trovato = { gravita: 'bloccante' | 'grave' | 'minore' | 'estetico'; cosa: string; dettaglio?: string }

/** The words a reader sees, without what a screen reader alone reads. */
async function paroleVisibili(page: Page): Promise<string> {
	return page.evaluate(() => {
		const parti: string[] = []
		const passeggio = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
		while (passeggio.nextNode()) {
			const nodo = passeggio.currentNode as Text
			const testo = nodo.textContent?.trim()
			if (!testo) continue
			const elemento = nodo.parentElement
			if (!elemento || elemento.closest('script,style,noscript,code,pre,[data-crudo],.sr-only')) continue
			const stile = getComputedStyle(elemento)
			if (stile.visibility === 'hidden' || stile.display === 'none' || Number(stile.opacity) === 0) continue
			const r = elemento.getBoundingClientRect()
			if (r.width === 0 || r.height === 0) continue
			parti.push(testo)
		}
		return parti.join('\n')
	})
}

/** Raw codes and English words in a text (an email's subject and words). */
export function testoCrudo(testo: string): Trovato[] {
	const trovati: Trovato[] = []
	for (const [regola, nome] of CRUDE) {
		const riga = testo.split('\n').find((r) => regola.test(r))
		if (riga) trovati.push({ gravita: 'minore', cosa: `In an email: ${nome}`, dettaglio: riga.slice(0, 160) })
	}
	return trovati
}

/** Raw codes and English words on the screen; ``ammessi``: what the step knows is
 * right there (a name, a code the person typed). */
export async function paroleCrude(page: Page, ammessi: RegExp[] = []): Promise<Trovato[]> {
	let testo = await paroleVisibili(page).catch(() => '')
	for (const ammesso of ammessi)
		testo = testo.replace(new RegExp(ammesso, ammesso.flags.includes('g') ? ammesso.flags : ammesso.flags + 'g'), ' ')
	const trovati: Trovato[] = []
	for (const [regola, nome] of CRUDE) {
		const riga = testo.split('\n').find((r) => regola.test(r))
		if (riga) trovati.push({ gravita: 'minore', cosa: `On screen: ${nome}`, dettaglio: riga.slice(0, 160) })
	}
	return trovati
}

/** What a screen reader reads of the buttons without words: their names, never a
 * date as the database writes it nor an English word. */
export async function nomiCrudi(page: Page): Promise<Trovato[]> {
	const nomi = await page
		.evaluate(() =>
			Array.from(document.querySelectorAll('button[aria-label], a[aria-label], [role=button][aria-label]'))
				.filter((el) => {
					const r = el.getBoundingClientRect()
					return r.width > 0 && r.height > 0
				})
				.map((el) => el.getAttribute('aria-label') || ''),
		)
		.catch(() => [] as string[])
	const crudi = [
		...new Set(
			nomi.filter(
				(n) =>
					/^\d{4}-\d{2}-\d{2}/.test(n) ||
					/^(prev|next|previous|close|open|menu|more|less|back|search|clear|remove|add|edit|delete|options|settings|today|[-+‹›<>×])$/i.test(
						n.trim(),
					),
			),
		),
	]
	if (!crudi.length) return []
	return [
		{
			gravita: 'minore',
			cosa: 'Buttons a screen reader names in code or English',
			dettaglio: crudi.slice(0, 8).join(' · '),
		},
	]
}

/** A required field is said by its control (`aria-required`), never by its mark in
 * the name a screen reader reads (the accessible name, not a label's text). */
export async function nomiConLaStella(page: Page): Promise<Trovato[]> {
	const albero = await page
		.locator('body')
		.ariaSnapshot({ timeout: 5000 })
		.catch(() => '')
	const stelle = [
		...albero.matchAll(/- (textbox|combobox|checkbox|radiogroup|spinbutton|listbox|searchbox) "([^"]*\*[^"]*)"/g),
	].map((m) => m[2])
	if (!stelle.length) return []
	return [
		{
			gravita: 'minore',
			cosa: 'A field a screen reader names with its asterisk',
			dettaglio: [...new Set(stelle)].slice(0, 6).join(' · '),
		},
	]
}

/** An error said to the person in a toast. */
export async function toastDiErrore(page: Page): Promise<Trovato[]> {
	const testi = await page
		.locator('[data-sonner-toast][data-type="error"]')
		.allInnerTexts()
		.catch(() => [] as string[])
	return testi.map((t) => ({ gravita: 'grave' as const, cosa: 'An error toast', dettaglio: t.trim().slice(0, 200) }))
}

/** Nothing wider than the screen: a page that scrolls sideways on a phone. */
export async function largo(page: Page): Promise<Trovato[]> {
	const misure = await page
		.evaluate(() => ({ largo: document.documentElement.scrollWidth, vista: window.innerWidth }))
		.catch(() => null)
	if (!misure || misure.largo <= misure.vista + 1) return []
	return [
		{
			gravita: 'grave',
			cosa: 'The page scrolls sideways',
			dettaglio: `${misure.largo}px of content on a ${misure.vista}px screen`,
		},
	]
}

/** On a touch screen the visible buttons with words are at least 40px tall, with
 * the invisible ring a small one may carry (`touch-target`, the area's own: an
 * ``::after`` that grows the place a thumb hits, the layout unchanged). */
export async function tocco(page: Page): Promise<Trovato[]> {
	const piccoli = await page
		.evaluate(() => {
			// how tall the place a finger hits is: the box, and the ring around it
			const altezza = (el: Element) => {
				const r = el.getBoundingClientRect()
				let alto = r.height
				for (const chi of [el, el.parentElement]) {
					if (!chi) continue
					const anello = getComputedStyle(chi, '::after')
					if (anello.content === 'none' || anello.position !== 'absolute') continue
					const sopra = parseFloat(anello.top) || 0
					const sotto = parseFloat(anello.bottom) || 0
					const suo = chi.getBoundingClientRect().height - sopra - sotto
					alto = Math.max(alto, suo)
				}
				return alto
			}
			const fuori: string[] = []
			const visti = new Set<string>()
			for (const el of Array.from(
				document.querySelectorAll('button, a[role=button], [role=tab], input[type=submit]'),
			)) {
				const r = el.getBoundingClientRect()
				if (r.width === 0 || r.height === 0 || r.bottom < 0 || r.top > innerHeight) continue
				const parole = (el.textContent || '').trim().replace(/\s+/g, ' ')
				if (!parole) continue
				if (el.closest('[data-tocco-libero]')) continue
				const stile = getComputedStyle(el)
				if (stile.visibility === 'hidden' || Number(stile.opacity) === 0) continue
				const alto = altezza(el)
				if (alto >= 39.5 || (alto >= 32 && r.width >= 40 && el.closest('nav, [role=tablist]'))) continue
				const chiave = `${parole.slice(0, 40)} (${Math.round(r.width)}×${Math.round(alto)})`
				if (!visti.has(chiave)) {
					visti.add(chiave)
					fuori.push(chiave)
				}
			}
			return fuori.slice(0, 12)
		})
		.catch(() => [] as string[])
	if (!piccoli.length) return []
	return [{ gravita: 'minore', cosa: 'Buttons smaller than a finger (under 40px)', dettaglio: piccoli.join(' · ') }]
}

/** A main action of the step, measured on a touch screen. */
export async function grandeAbbastanza(azione: Locator): Promise<Trovato[]> {
	const r = await azione.boundingBox().catch(() => null)
	if (!r) return []
	const anello = await azione
		.evaluate((el) => {
			const dopo = getComputedStyle(el, '::after')
			return dopo.content !== 'none' && dopo.position === 'absolute'
				? -(parseFloat(dopo.top) || 0) - (parseFloat(dopo.bottom) || 0)
				: 0
		})
		.catch(() => 0)
	if (r.height + anello >= 39.5) return []
	return [
		{
			gravita: 'grave',
			cosa: 'A main action smaller than a finger',
			dettaglio: `${Math.round(r.width)}×${Math.round(r.height)}`,
		},
	]
}
