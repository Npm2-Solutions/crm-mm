// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect } from '@playwright/test'
import { compilaIModuli, entraNellArea, linkDellArea } from '../lib/area'
import { collegamento, premi } from '../lib/azioni'
import { firmaLaVisita, nuovaVisita, puntoSulCorpo, scegli, scrivi } from '../lib/clinica'
import { emettiLaBozza, fatturaDi, esito, persona } from '../lib/scrivania'
import type { Settimana } from '../lib/settimana'
import { laCassa } from './lunedi'
import { permessi } from './permessi'

/** Tuesday: Anna fills her forms from the area and comes to the physiotherapist,
 * who writes the first assessment on her phone and gives the report online; the
 * fund's visit is invoiced for Anna's share; at Monza, Sara says she is here from
 * the area, the doctor writes her history on the tablet, the manager invoices the
 * balance of the deposit from her phone; each location closes its cash. */
export async function martedi(s: Settimana) {
	await s.giornata('martedi', '07:30')
	await annaSiPrepara(s)
	await annaArriva(s)
	await laValutazione(s)
	await ilReferto(s)
	await laQuotaDiAnna(s)
	await saraAMonza(s)
	await laCassa(s, 'martedi', 'segreteria', 'milano')
	await laCassa(s, 'martedi', 'responsabile_telefono', 'monza')
	await permessi(s)
}

/** Before leaving home, Anna opens her area from the invitation and fills the
 * forms the centre asks before the first appointment. */
async function annaSiPrepara(s: Settimana) {
	await s.alle('08:30')
	const anna = s.p('anna')
	await s.passo(
		'Anna, prima di uscire, compila e firma col dito i moduli dall’area',
		anna,
		async () => {
			const invito = await s.banco.attendiPosta(anna.email, /area/i, { dopo: s.data('lunedi') })
			const page = await entraNellArea(s, anna, { link: linkDellArea(invito.links) })
			const firmati = await compilaIModuli(s, anna, page)
			s.nota(`${firmati} moduli firmati`)
			const consensi = await s.banco
				.lista('CRM Consent', { lead: s.stato.anna.persona }, ['consent_type', 'status'])
				.catch(() => [])
			s.nota(`Consensi: ${JSON.stringify(consensi)}`)
			const moduli = await s.banco.conta('CRM Form', { lead: s.stato.anna.persona, signed_on: ['is', 'set'] })
			s.verifica(moduli > 0, 'Anna’s form is signed', String(moduli))
			await page.goto('/area', { waitUntil: 'domcontentloaded' })
		},
		{ chiave: 'anna.moduli', dopo: ['anna.area'] },
	)
}

async function annaArriva(s: Settimana) {
	await s.alle('09:52')
	const seg = s.p('segreteria')
	await s.passo(
		'Anna arriva: la segreteria la accoglie',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const riga = page
				.getByRole('link', { name: s.p('anna').nome })
				.first()
				.locator('xpath=ancestor::div[contains(@class,"py-2")][1]')
			await premi(seg, riga.getByRole('button', { name: 'Accogli' }))
			await expect(riga.getByRole('button', { name: 'Presente' })).toBeVisible()
			// her forms are signed: nothing owed at the desk
			s.verifica(
				!(await riga.getByText(/moduli? da firmare|da compilare/i).count()),
				'The forms signed from the area are not asked again at the desk',
			)
		},
		{ chiave: 'anna.arrivata', dopo: ['anna.confermata'] },
	)
}

/** The physiotherapist, on her phone, writes the first assessment on the sheet:
 * why, where it hurts on the body chart, the plan; signed. */
async function laValutazione(s: Settimana) {
	await s.alle('10:05')
	const fisio = s.p('fisioterapista')
	await s.passo(
		'La fisioterapista scrive la valutazione di Anna dal telefono, col disegno sul corpo, e la firma',
		fisio,
		async () => {
			const page = await persona(s, fisio, s.stato.anna.persona, 'clinic')
			await nuovaVisita(fisio, page, /^Valutazione fisioterapica/)
			await scrivi(page, 'Cosa porta il paziente', 'Mal di schiena in basso da tre settimane, dopo un trasloco.')
			await scegli(fisio, page, 'Come è iniziato', 'Poco a poco')
			await scrivi(page, 'Da quando', 'Tre settimane')
			await puntoSulCorpo(fisio, page, {
				vista: 'Dietro',
				x: 0.55,
				y: 0.45,
				parole: 'Lombare destra, scende al gluteo',
				quanto: 6,
			})
			await scrivi(
				page,
				'Valutazione fisioterapica',
				'Lombalgia meccanica senza segni d’allarme. Dieci sedute: terapia manuale ed esercizio terapeutico.',
			)
			await s.foto(fisio, 'valutazione')
			const visita = await firmaLaVisita(fisio, page)
			s.stato.anna.visita = visita?.name
			// the visit says she came: the agenda knows it
			const stato = await s.attendi(
				() => s.banco.statoDi(s.stato.anna.appuntamento, s.stato.anna.persona),
				(v) => v === 'Attended',
				10,
			)
			s.verifica(stato === 'Attended', 'A visit written at the appointment says the person came', stato)
			const referto = await s.attendi(
				() => s.banco.valore('CRM Document', { lead: s.stato.anna.persona }, ['name', 'title', 'document_type']),
				(v) => !!v,
			)
			s.verifica(!!referto, 'The signed visit’s report is filed among her documents', JSON.stringify(referto))
			s.stato.anna.referto = referto?.name
		},
		{ chiave: 'anna.valutazione', dopo: ['anna.arrivata'] },
	)
}

/** The report goes online: the physiotherapist gives Anna the code there and
 * then; Anna opens the link of the email with it and downloads her report. */
async function ilReferto(s: Settimana) {
	await s.alle('10:50')
	const fisio = s.p('fisioterapista')
	await s.passo(
		'La fisioterapista mette online il referto e dà il codice ad Anna',
		fisio,
		async () => {
			const page = await persona(s, fisio, s.stato.anna.persona, 'documents')
			await premi(fisio, page.getByRole('button', { name: 'Azioni' }).first())
			// «to the person», in the clinic's words «to the patient»
			await premi(fisio, page.getByRole('menuitem', { name: /^Consegnalo al/ }))
			const d = page.getByRole('dialog').last()
			// «A mano · Online»: frappe-ui's tab buttons, a group of radios
			await premi(
				fisio,
				d
					.getByRole('radio', { name: 'Online', exact: true })
					.or(d.getByRole('tab', { name: 'Online', exact: true }))
					.or(d.getByRole('button', { name: 'Online', exact: true }))
					.first(),
			)
			await premi(fisio, d.getByRole('button', { name: 'Mettilo online' }))
			await expect(d.getByText(/^Il codice per aprirlo/)).toBeVisible()
			// the code, drawn digit by digit: read as the physiotherapist reads it out
			const testo = await d.innerText()
			const codice = (/Il codice per aprirlo[^\n]*\n+\s*([\d\s]{6,20})/.exec(testo)?.[1] || '').replace(/\s+/g, '')
			s.verifica(/^\d{6}$/.test(codice), 'The code is shown to give it', codice)
			s.stato.anna.codice = codice
			await s.foto(fisio, 'codice')
			await premi(fisio, d.getByRole('button', { name: 'Fine', exact: true }))
		},
		{ chiave: 'anna.referto.online', dopo: ['anna.valutazione'] },
	)
	const anna = s.p('anna')
	await s.passo(
		'Anna apre il referto dal link dell’email col codice e lo scarica',
		anna,
		async () => {
			const mail = await s.banco.attendiPosta(anna.email, /referto|documento/i, { dopo: s.data('martedi') })
			s.verifica(!mail.text.includes(s.stato.anna.codice), 'The code is not in the email', mail.subject)
			const link = collegamento(mail.links, /\/(documento|referto)\//)
			const page = await anna.apri(s.browser, s.banco)
			await page.goto(link, { waitUntil: 'domcontentloaded' })
			await page.getByLabel('Il codice').fill(s.stato.anna.codice)
			await premi(anna, page.getByRole('button', { name: 'Apri' }))
			const scarica = page
				.getByRole('link', { name: 'Scarica' })
				.or(page.getByRole('button', { name: 'Scarica' }))
				.first()
			await expect(scarica).toBeVisible()
			await s.dito(anna, scarica)
			const download = page.waitForEvent('download', { timeout: 30000 })
			await premi(anna, scarica)
			const file = await download
			s.nota(`Scaricato: ${file.suggestedFilename()}`)
			s.verifica(/\.pdf$/i.test(file.suggestedFilename()), 'The report is a PDF', file.suggestedFilename())
			const consegna = await s.banco.valore('CRM Document Delivery', { document: s.stato.anna.referto }, [
				'status',
				'downloads',
			])
			s.verifica(consegna?.status === 'Downloaded', 'The centre sees it was downloaded', JSON.stringify(consegna))
		},
		{ chiave: 'anna.referto.letto', dopo: ['anna.referto.online'] },
	)
}

/** The fund pays for Anna's visit in direct form: she pays her share at the desk,
 * in cash; the pratica is done and waits for the month's invoice to the fund. */
async function laQuotaDiAnna(s: Settimana) {
	await s.alle('11:00')
	const seg = s.p('segreteria')
	await s.passo(
		'Anna paga in contanti la sua quota della visita col fondo',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const fattura = fatturaDi(page, s.p('anna').nome)
			await expect(fattura).toBeVisible({ timeout: 30000 })
			await premi(seg, fattura)
			await emettiLaBozza(s, seg, page, 'anna', { pagamento: /Contanti/ })
			const emessa = await s.banco.valore('CRM Invoice', { appointment: s.stato.anna.appuntamento, docstatus: 1 }, [
				'name',
				'grand_total',
				'net_payable',
				'party',
			])
			const quota = await s.banco.valore('CRM Appointment', s.stato.anna.appuntamento, ['patient_share', 'fund_share'])
			s.nota(`Quote: ${JSON.stringify(quota)} · fattura ${JSON.stringify(emessa)}`)
			s.verifica(
				Number(emessa?.grand_total) === Number(quota?.patient_share),
				'Anna’s invoice is her share, not the price',
				`${emessa?.grand_total} vs ${quota?.patient_share}`,
			)
			const pratiche = await s.banco.chiama(
				'crm.convenzioni.api.get_claims',
				{ month: s.data('martedi').slice(0, 7) },
				'GET',
			)
			const sua = (pratiche?.claims || []).find((p: any) => p.appointment === s.stato.anna.appuntamento)
			s.verifica(sua?.state === 'Done', 'The pratica is done, to bill the fund', JSON.stringify(sua))
			await esito(page).catch(() => '')
		},
		{ chiave: 'anna.quota', dopo: ['anna.valutazione'] },
	)
}

/** Monza, in the afternoon: Sara says she is here from her area, the doctor
 * writes her history on the tablet, the manager invoices the balance from her
 * phone (the deposit came off). */
async function saraAMonza(s: Settimana) {
	await s.alle('14:50')
	const sara = s.p('sara')
	await s.passo(
		'Sara arriva a Monza e dice «sono qui» dalla sua area',
		sara,
		async () => {
			const invito = await s.banco.attendiPosta(sara.email, /area/i, { dopo: s.data('lunedi') })
			const page = await entraNellArea(s, sara, { link: linkDellArea(invito.links) })
			// the link may open another page of the area: today's is «Oggi»
			await premi(sara, page.getByRole('link', { name: 'Oggi' }).first())
			const qui = page.getByRole('button', { name: 'Sono qui' }).first()
			await expect(qui).toBeVisible()
			await s.dito(sara, qui)
			await premi(sara, qui)
			const stato = await s.attendi(
				() => s.banco.statoDi(s.stato.sara.appuntamento, s.stato.sara.persona),
				(v) => v === 'Arrived',
			)
			s.verifica(stato === 'Arrived', 'Sara is in the waiting room', stato)
		},
		{ chiave: 'sara.qui', dopo: ['sara.area'] },
	)
	await s.alle('15:05')
	const medico = s.p('medico')
	await s.passo(
		'Il medico, sul tablet, scrive l’anamnesi di Sara e la firma',
		medico,
		async () => {
			// the doctor's tablet is told Sara arrived
			const page = await persona(s, medico, s.stato.sara.persona, 'clinic')
			await nuovaVisita(medico, page, /^Anamnesi generale/)
			await scegli(medico, page, 'Allergie', 'Sì')
			await scrivi(page, 'Quali, e cosa succede', 'Penicillina: orticaria')
			await scegli(medico, page, 'Fumo', 'Mai')
			await scrivi(page, 'Peso', '64')
			await scrivi(page, 'Altezza', '168')
			await scrivi(page, 'Pressione arteriosa (mmHg)', '120/80')
			await page.getByLabel('Note', { exact: true }).last().fill('Visita di controllo: nulla da segnalare.')
			await s.foto(medico, 'anamnesi')
			await firmaLaVisita(medico, page)
			const stato = await s.attendi(
				() => s.banco.statoDi(s.stato.sara.appuntamento, s.stato.sara.persona),
				(v) => v === 'Attended',
				10,
			)
			s.verifica(stato === 'Attended', 'A visit written at the appointment says the person came', stato)
		},
		{ chiave: 'sara.visita', dopo: ['sara.prenota'] },
	)
	await s.alle('15:40')
	const resp = s.p('responsabile_telefono')
	await s.passo(
		'A Monza la responsabile, dal telefono, fa la fattura del saldo a Sara',
		resp,
		async () => {
			const page = await s.alLavoro(resp)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			// the desk of Monza: the location chosen, only its day shown
			const scelta = page.getByRole('button', { name: /^(Tutte le sedi|Sede di )/ }).first()
			await expect(scelta).toBeVisible()
			await premi(resp, scelta)
			await premi(resp, page.locator('[data-foglio] label').filter({ hasText: 'Sede di Monza' }).first())
			await page.keyboard.press('Escape').catch(() => {})
			await expect(page.getByRole('link', { name: s.p('anna').nome })).toHaveCount(0)
			const fattura = fatturaDi(page, s.p('sara').nome)
			await expect(fattura).toBeVisible({ timeout: 30000 })
			await premi(resp, fattura)
			await emettiLaBozza(s, resp, page, 'sara', { pagamento: /Carta/ })
			const saldo = await s.banco.valore('CRM Invoice', { appointment: s.stato.sara.appuntamento, docstatus: 1 }, [
				'grand_total',
				'causale',
				'centre_location',
			])
			s.nota(`Saldo: ${JSON.stringify(saldo)}`)
			s.verifica(
				Number(saldo?.grand_total) === 90,
				'The balance is the price less the deposit',
				String(saldo?.grand_total),
			)
			s.verifica(/acconto/i.test(saldo?.causale || ''), 'The balance names the advance invoice', saldo?.causale)
			s.verifica(saldo?.centre_location === s.copione.locations.monza, 'The balance is Monza’s', saldo?.centre_location)
		},
		{ chiave: 'sara.saldo', dopo: ['sara.visita'] },
	)
}
