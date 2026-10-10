// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect } from '@playwright/test'
import { premi } from '../lib/azioni'
import { firmaLaVisita, nuovaVisita } from '../lib/clinica'
import { emettiLaBozza, fatturaDi, esito, impostazioni, persona } from '../lib/scrivania'
import type { Settimana } from '../lib/settimana'
import { laCassa } from './lunedi'
import { permessi } from './permessi'

/** Friday: Federica's visit invoiced to the company that pays for it; the manager
 * bills the fund for the month, reads the week's money on the dashboard and takes
 * the centre's data away. */
export async function venerdi(s: Settimana) {
	await s.giornata('venerdi', '07:30')
	await laVisitaDiFederica(s)
	await ilFondo(s)
	await ilCruscotto(s)
	await iDati(s)
	await laCassa(s, 'venerdi', 'segreteria', 'milano')
	await permessi(s)
}

async function laVisitaDiFederica(s: Settimana) {
	await s.alle('09:55')
	const seg = s.p('segreteria')
	await s.passo(
		'Federica arriva per la visita: la manda la sua azienda',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const riga = page
				.getByRole('link', { name: s.p('federica').nome })
				.first()
				.locator('xpath=ancestor::div[contains(@class,"py-2")][1]')
			await premi(seg, riga.getByRole('button', { name: 'Accogli' }))
			await expect(riga.getByRole('button', { name: 'Presente' })).toBeVisible()
		},
		{ chiave: 'federica.arrivata', dopo: ['federica.venerdi'] },
	)
	await s.alle('10:05')
	const medico = s.p('medico')
	await s.passo(
		'Il medico scrive la visita di Federica e la firma',
		medico,
		async () => {
			const page = await persona(s, medico, s.stato.federica.persona, 'clinic')
			await nuovaVisita(medico, page, /^Visita libera/)
			await page.getByLabel('Cosa è successo').fill('Visita di idoneità: nulla da segnalare. Idonea alla mansione.')
			await firmaLaVisita(medico, page)
		},
		{ chiave: 'federica.visita', dopo: ['federica.arrivata'] },
	)
	await s.alle('10:40')
	await s.passo(
		'La fattura della visita di Federica è intestata alla sua azienda, con bonifico',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const fattura = fatturaDi(page, s.p('federica').nome)
			await expect(fattura).toBeVisible({ timeout: 30000 })
			await premi(seg, fattura)
			await emettiLaBozza(s, seg, page, 'federica', { pagamento: /Bonifico/, azienda: s.copione.company_client })
			const emessa = await s.banco.valore(
				'CRM Invoice',
				{ appointment: s.stato.federica.appuntamento_venerdi, docstatus: 1 },
				['name', 'recipient_type', 'billing_name', 'tax_id', 'collected_on', 'ts_status'],
			)
			s.nota(`Fattura: ${JSON.stringify(emessa)}`)
			s.verifica(emessa?.recipient_type === 'soggetto_iva', 'Made out to a company', emessa?.recipient_type)
			s.verifica(emessa?.tax_id?.includes(s.copione.company_client.vat), 'With its VAT number', emessa?.tax_id)
			s.verifica(!emessa?.collected_on, 'A bank transfer is still to collect', emessa?.collected_on)
			s.stato.federica.fattura = emessa?.name
		},
		{ chiave: 'federica.fattura', dopo: ['federica.visita'] },
	)
}

/** The month's statement to the fund: the pratiche done, one invoice to the fund
 * through the SdI, for the fund's share. */
async function ilFondo(s: Settimana) {
	await s.alle('11:30')
	const r = s.p('responsabile')
	await s.passo(
		'La responsabile fattura al fondo le pratiche del mese',
		r,
		async () => {
			const page = await s.alLavoro(r)
			await page.goto('/crm/fatture', { waitUntil: 'domcontentloaded' })
			await premi(r, page.getByRole('button', { name: 'Convenzioni', exact: true }))
			const fondo = page.getByRole('button', { name: 'Fattura al fondo' })
			await expect(fondo).toBeVisible({ timeout: 30000 })
			await s.foto(r, 'pratiche')
			await premi(r, fondo)
			await esito(page, /fondo/i)
			const d = page.getByRole('dialog').last()
			await expect(d.getByRole('button', { name: 'Emetti', exact: true })).toBeVisible({ timeout: 30000 })
			const emessa = page.waitForResponse((x) => x.url().includes('crm.invoicing.emissione.issue'), { timeout: 60000 })
			await premi(r, d.getByRole('button', { name: 'Emetti', exact: true }))
			const risposta = await emessa
			s.verifica(risposta.ok(), 'The fund’s invoice is issued', String(risposta.status()))
			const quota = await s.banco.valore('CRM Appointment', s.stato.anna.appuntamento, 'fund_share')
			const fattura = await s.banco.valore('CRM Invoice', { party_type: 'CRM Organization', docstatus: 1 }, [
				'name',
				'grand_total',
				'billing_name',
				'recipient_type',
				'ts_status',
			])
			s.nota(`Fattura al fondo: ${JSON.stringify(fattura)}`)
			s.verifica(
				Number(fattura?.grand_total) === Number(quota),
				'The fund pays its share of the visit',
				`${fattura?.grand_total} vs ${quota}`,
			)
			s.verifica(
				fattura?.recipient_type === 'soggetto_iva',
				'The fund is invoiced as a VAT subject',
				fattura?.recipient_type,
			)
			const pratiche = await s.banco.chiama(
				'crm.convenzioni.api.get_claims',
				{ month: s.data('venerdi').slice(0, 7) },
				'GET',
			)
			const sua = (pratiche?.claims || []).find((p: any) => p.appointment === s.stato.anna.appuntamento)
			s.verifica(sua?.state === 'Billed', 'Anna’s pratica is billed', JSON.stringify(sua))
		},
		{ chiave: 'fondo.fattura', dopo: ['anna.quota'] },
	)
}

/** The week's money on the dashboard is the invoices' own. */
async function ilCruscotto(s: Settimana) {
	await s.alle('12:00')
	const r = s.p('responsabile')
	await s.passo(
		'La responsabile guarda il cruscotto: l’incassato della settimana torna con le fatture',
		r,
		async () => {
			const page = await s.alLavoro(r)
			await page.goto('/crm/dashboard', { waitUntil: 'domcontentloaded' })
			await page.waitForLoadState('networkidle').catch(() => {})
			await s.foto(r, 'cruscotto')
			const dal = s.data('lunedi')
			const al = s.data('venerdi')
			const risposta = await s.banco.chiama(
				'crm.api.dashboard.get_widgets_data',
				{ widgets: [{ i: 'x', name: 'collected' }], from_date: dal, to_date: al },
				'POST',
			)
			const mostrato = Number(risposta?.x?.data?.value ?? risposta?.x?.value ?? NaN)
			const fatture = await s.banco.lista(
				'CRM Invoice',
				{ docstatus: 1, collected_on: ['between', [dal, al]], test_document: 0, document_type: ['!=', 'TD04'] },
				['name', 'net_payable', 'grand_total'],
				{ limite: 500 },
			)
			const somma = Math.round(fatture.reduce((t, f) => t + Number(f.net_payable ?? f.grand_total ?? 0), 0) * 100) / 100
			s.nota(`Incassato: cruscotto ${mostrato}, fatture ${somma} (${fatture.length})`)
			s.verifica(
				Math.abs(mostrato - somma) < 0.005,
				'The dashboard’s collected is the invoices’',
				`${mostrato} vs ${somma}`,
			)
		},
		{ chiave: 'cruscotto' },
	)
}

/** The centre takes its data away: the archive made in a job, ready to download. */
async function iDati(s: Settimana) {
	await s.alle('12:30')
	const r = s.p('responsabile')
	await s.passo(
		'La responsabile scarica l’archivio dei dati del centro',
		r,
		async () => {
			await s.alLavoro(r)
			const page = await impostazioni(s, r, 'Your data')
			const fai = page
				.getByRole('button', { name: 'Prepara l’archivio' })
				.or(page.getByRole('button', { name: /archivio/ }))
			await premi(r, fai.first())
			const pronto = await s.attendi(
				// as her page asks it: the data are the centre's, the agency reads no archive
				() =>
					page.request
						.get('/api/method/crm.esportazione.esporta.get_exports')
						.then((x) => x.json())
						.then((x) => x.message)
						.catch(() => null),
				(v: any) => !!(v?.ready || []).length,
				120,
			)
			s.nota(`Archivi: ${JSON.stringify((pronto as any)?.ready || [])}`)
			s.verifica(!!((pronto as any)?.ready || []).length, 'The archive is ready', JSON.stringify(pronto))
			// the page again, as she comes back to it (without the socket of a bench that
			// has none for this site, the open page is not told)
			const pagina = await impostazioni(s, r, 'Your data')
			const scarica = pagina
				.getByRole('link', { name: 'Scarica', exact: true })
				.or(pagina.getByRole('button', { name: 'Scarica', exact: true }))
				.first()
			await expect(scarica).toBeVisible({ timeout: 30000 })
			const download = pagina.waitForEvent('download', { timeout: 60000 })
			await premi(r, scarica)
			const file = await download
			s.verifica(/\.zip$/i.test(file.suggestedFilename()), 'A ZIP of the centre’s data', file.suggestedFilename())
		},
		{ chiave: 'dati' },
	)
}
