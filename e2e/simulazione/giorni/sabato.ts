// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect } from '@playwright/test'
import { entraNellArea } from '../lib/area'
import { pagaSuStripe, premi } from '../lib/azioni'
import { FINTI } from '../lib/banco'
import { firmaLaVisita, nuovaVisita, scrivi } from '../lib/clinica'
import { emettiLaBozza, fatturaDi, persona } from '../lib/scrivania'
import type { Settimana } from '../lib/settimana'
import { laCassa } from './lunedi'
import { permessi } from './permessi'

/** Saturday: the night's reminder of an invoice still to pay; Anna's second
 * session, started from the last visit; then a month later, the subscriptions'
 * charges on the saved cards (one refused, tried again, paid from the area) and the
 * care plan's instalment invoiced. */
export async function sabato(s: Settimana) {
	await s.giornata('sabato', '07:30')
	await ilSollecito(s)
	await laSecondaSeduta(s)
	await laCassa(s, 'sabato', 'segreteria', 'milano')
	await permessi(s)
	await unMeseDopo(s)
}

/** Tommaso's invoice, by bank transfer on Wednesday, is not paid three days later:
 * the night's round writes Elena a polite reminder. */
async function ilSollecito(s: Settimana) {
	await s.alle('08:00')
	const elena = s.p('elena')
	await s.passo(
		'Nella notte parte il sollecito gentile della fattura di Tommaso, alla mamma',
		elena,
		async () => {
			const mail = await s.banco.attendiPosta(elena.email, /fattura|pagare|sollecit|promemoria/i, {
				dopo: `${s.data('sabato')} 00:00`,
			})
			s.nota(`Sollecito: «${mail.subject}»`)
			const registro = await s.banco.conta('CRM Invoice Log', { invoice: s.stato.tommaso.fattura, event: 'reminded' })
			s.verifica(registro === 1, 'The reminder is written on the invoice’s log, once', String(registro))
			// not a company's: Federica's company is not reminded as a person
			const azienda = await s.banco.conta('CRM Invoice Log', {
				invoice: s.stato.federica?.fattura || '-',
				event: 'reminded',
			})
			s.verifica(azienda === 0, 'An invoice to a company is not reminded as a person’s', String(azienda))
		},
		{ chiave: 'sollecito', dopo: ['tommaso.fattura'] },
	)
}

/** Anna's second session: the follow-up started from Thursday's, signed; paid. */
async function laSecondaSeduta(s: Settimana) {
	await s.alle('09:55')
	const seg = s.p('segreteria')
	await s.passo(
		'Anna arriva per la seconda seduta',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const riga = page
				.getByRole('link', { name: s.p('anna').nome })
				.first()
				.locator('xpath=ancestor::div[contains(@class,"py-2")][1]')
			await expect(page.getByText(/Seduta 2 di 10/).first()).toBeVisible()
			await premi(seg, riga.getByRole('button', { name: 'Accogli' }))
			await expect(riga.getByRole('button', { name: 'Presente' })).toBeVisible()
		},
		{ chiave: 'anna.seduta2.arrivata', dopo: ['anna.ciclo'] },
	)
	await s.alle('10:05')
	const fisio = s.p('fisioterapista')
	await s.passo(
		'La fisioterapista parte dalla seduta di giovedì, cambia quello che è cambiato e firma',
		fisio,
		async () => {
			const page = await persona(s, fisio, s.stato.anna.persona, 'clinic')
			await nuovaVisita(fisio, page, /^Controllo fisioterapico: parti dall.ultima visita/)
			await expect(page.getByText(/Copiata dalla visita del/).first()).toBeVisible()
			const fatto = page.getByLabel(/^\s*Fatto oggi\s*\*?\s*$/).first()
			s.verifica(
				/Terapia manuale/.test(await fatto.inputValue()),
				'The answers of the last visit are there to change',
				await fatto.inputValue(),
			)
			await scrivi(page, 'Fatto oggi', 'Terapia manuale, progressione degli esercizi in carico.')
			await firmaLaVisita(fisio, page)
			const copiata = await s.banco.valore(
				'Clinic Record',
				{ lead: s.stato.anna.persona, copied_from: ['is', 'set'], docstatus: 1 },
				['name', 'copied_from'],
			)
			s.verifica(!!copiata, 'The visit keeps where it was copied from', JSON.stringify(copiata))
		},
		{ chiave: 'anna.seduta2', dopo: ['anna.seduta2.arrivata', 'anna.seduta1'] },
	)
	await s.alle('10:50')
	await s.passo(
		'Anna paga la seconda seduta in contanti',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const fattura = fatturaDi(page, s.p('anna').nome)
			await expect(fattura).toBeVisible({ timeout: 30000 })
			await premi(seg, fattura)
			await emettiLaBozza(s, seg, page, 'anna', { pagamento: /Contanti/ })
		},
		{ chiave: 'anna.seduta2.fattura', dopo: ['anna.seduta2'] },
	)
}

/** The rows of a subscription's instalments, in order. */
async function rateDi(s: Settimana, abbonamento: string) {
	return s.banco.lista(
		'CRM Subscription Instalment',
		{ parent: abbonamento },
		['name', 'due_on', 'amount', 'invoice', 'charge_attempts', 'charge_problem'],
		{ genitore: 'CRM Subscription', ordine: 'due_on asc' },
	)
}

/** A day after the week: its date in the script, its night, its first hour. */
async function unAltroGiorno(s: Settimana, nome: string, data: string, ora = '07:30') {
	s.copione.week[nome] = data
	await s.giornata(nome, ora)
}

async function unMeseDopo(s: Settimana) {
	const paolo = s.stato.paolo?.abbonamento
	const chiara = s.stato.chiara?.abbonamento
	if (!paolo && !chiara) return
	const seconda = (await rateDi(s, paolo || chiara))[1]
	if (!seconda) return
	await unAltroGiorno(s, 'un_mese_dopo', seconda.due_on)
	await s.passo(
		'Un mese dopo: la seconda rata di Paolo è addebitata sulla carta e fatturata',
		s.p('paolo'),
		async () => {
			const rata = (await rateDi(s, paolo))[1]
			s.nota(`Rata: ${JSON.stringify(rata)}`)
			s.verifica(!!rata?.invoice, 'The instalment is invoiced', JSON.stringify(rata))
			const fattura = rata?.invoice
				? await s.banco.valore('CRM Invoice', rata.invoice, [
						'docstatus',
						'collected_on',
						'payment_method',
						'grand_total',
					])
				: null
			s.verifica(
				fattura?.docstatus === 1 && !!fattura?.collected_on && fattura?.payment_method === 'MP08',
				'Charged on the card: issued and collected',
				JSON.stringify(fattura),
			)
		},
		{ chiave: 'paolo.rata2', dopo: ['paolo.abbonamento'] },
	)
	const chi = s.p('chiara')
	await s.passo(
		'La carta di Chiara è rifiutata: niente fattura, Chiara riceve due righe per pagare',
		chi,
		async () => {
			const rata = (await rateDi(s, chiara))[1]
			s.nota(`Rata: ${JSON.stringify(rata)}`)
			s.verifica(!rata?.invoice, 'No invoice for money that did not arrive', JSON.stringify(rata))
			s.verifica(Number(rata?.charge_attempts) === 1, 'One attempt, written', JSON.stringify(rata))
			const mail = await s.banco.attendiPosta(chi.email, /pagament|carta|rata/i, { dopo: `${seconda.due_on} 00:00` })
			s.nota(`Email: «${mail.subject}»`)
		},
		{ chiave: 'chiara.rifiutata', dopo: ['chiara.abbonamento'] },
	)
	await s.passo(
		'Il preventivo di Roberto: la prima rata è fatturata quando scade',
		s.p('responsabile'),
		async () => {
			const rate = await s.banco.lista(
				'CRM Quote Instalment',
				{ parent: s.stato.roberto.preventivo },
				['kind', 'number', 'due_on', 'amount', 'status', 'invoice'],
				{ genitore: 'CRM Quote', ordine: 'idx asc' },
			)
			s.nota(`Rate: ${JSON.stringify(rate)}`)
			const acconto = rate.find((r) => r.kind === 'Deposit')
			s.verifica(!!acconto?.invoice, 'The deposit was invoiced on acceptance', JSON.stringify(acconto))
			const dovute = rate.filter((r) => r.kind === 'Instalment' && r.due_on <= seconda.due_on)
			s.verifica(
				dovute.every((r) => !!r.invoice),
				'Each instalment due is invoiced',
				JSON.stringify(dovute),
			)
		},
		{ chiave: 'roberto.rate', dopo: ['roberto.firmato'] },
	)
	// three days later the charge is tried again, then Chiara pays from her area
	const dopo = new Date(`${seconda.due_on}T12:00:00Z`)
	dopo.setUTCDate(dopo.getUTCDate() + 3)
	await unAltroGiorno(s, 'tre_giorni_dopo', dopo.toISOString().slice(0, 10))
	await s.passo(
		'Tre giorni dopo l’addebito è riprovato, rifiutato di nuovo',
		chi,
		async () => {
			const rata = (await rateDi(s, chiara))[1]
			s.verifica(Number(rata?.charge_attempts) === 2, 'Tried again three days later', JSON.stringify(rata))
			s.verifica(!rata?.invoice, 'Still no invoice', JSON.stringify(rata))
		},
		{ chiave: 'chiara.riprovata', dopo: ['chiara.rifiutata'] },
	)
	await s.alle('09:30')
	await s.passo(
		'Chiara paga la rata dalla sua area con un’altra carta',
		chi,
		async () => {
			const page = await entraNellArea(s, chi)
			await page.goto('/area/appointments', { waitUntil: 'domcontentloaded' })
			const paga = page.getByRole('button', { name: 'Paga ora' }).first()
			await expect(paga).toBeVisible({ timeout: 30000 })
			await s.dito(chi, paga)
			await premi(chi, paga)
			await page.waitForURL((u) => u.toString().startsWith(`${FINTI}/checkout/`), { timeout: 45000 })
			await pagaSuStripe(s, chi, page, ['4242424242424242'])
			await page.waitForURL(/\/area/, { timeout: 60000 })
			const rata = await s.attendi(
				async () => (await rateDi(s, chiara))[1],
				(r) => !!r?.invoice,
				30,
			)
			s.verifica(!!rata?.invoice, 'Paid, the instalment is invoiced', JSON.stringify(rata))
		},
		{ chiave: 'chiara.pagata', dopo: ['chiara.rifiutata'] },
	)
}
