// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect } from '@playwright/test'
import { entraNellArea } from '../lib/area'
import { collegamento, premi } from '../lib/azioni'
import { firmaLaVisita, nuovaVisita, scrivi } from '../lib/clinica'
import { STANZE_VIDEO } from '../lib/persone'
import { emettiLaBozza, fatturaDi, esito, persona } from '../lib/scrivania'
import type { Settimana } from '../lib/settimana'
import { laCassa } from './lunedi'
import { permessi } from './permessi'

/** Thursday: Marco cancels Friday's visit in time and gets his deposit back; Luca's
 * online visit with the dietitian, both entering the room; Paolo does not come;
 * Anna's first session of her cycle; marketing sends the autumn news to a list;
 * Giulia cancels her check-up too late, and the deposit stays. */
export async function giovedi(s: Settimana) {
	await s.giornata('giovedi', '07:30')
	await marcoDisdice(s)
	await laVisitaOnline(s)
	await paoloNonViene(s)
	await laCampagna(s)
	await laRecensione(s)
	await laSedutaDiAnna(s)
	await giuliaDisdiceTardi(s)
	await laCassa(s, 'giovedi', 'segreteria', 'milano')
	await permessi(s)
}

/** The booking's own page, from the link of its email: «Annulla prenotazione». */
async function disdiciDallEmail(s: Settimana, chiave: string, cerca: RegExp) {
	const chi = s.p(chiave)
	const mail = await s.banco.attendiPosta(chi.email, cerca, { dopo: s.data('lunedi') })
	const link = collegamento(mail.links, /prenota\?token=/)
	const page = await chi.apri(s.browser, s.banco)
	await page.goto(link, { waitUntil: 'domcontentloaded' })
	const annulla = page.getByRole('button', { name: 'Annulla prenotazione' })
	await expect(annulla).toBeVisible({ timeout: 30000 })
	await s.dito(chi, annulla)
	await premi(chi, annulla)
	await premi(chi, page.getByRole('button', { name: 'Sì, annulla' }))
	await expect(page.locator('.done-hero.cancelled')).toBeVisible({ timeout: 30000 })
	return page
}

async function marcoDisdice(s: Settimana) {
	await s.alle('08:00')
	const marco = s.p('marco')
	await s.passo(
		'Marco non può venire domani: disdice dalla email e riceve indietro l’acconto',
		marco,
		async () => {
			await disdiciDallEmail(s, 'marco', /prenotazion|confermat|ricevuto/i)
			const stato = await s.banco.valore('CRM Appointment', s.stato.marco.appuntamento, 'status')
			s.verifica(stato === 'Cancelled', 'The visit is cancelled', stato)
			const pagamento = await s.attendi(
				() =>
					s.banco.valore('CRM Online Payment', { appointment: s.stato.marco.appuntamento }, [
						'status',
						'refunded_amount',
					]),
				(v) => v?.status === 'Refunded',
				40,
			)
			s.nota(`Pagamento: ${JSON.stringify(pagamento)}`)
			s.verifica(
				pagamento?.status === 'Refunded',
				'A cancellation in time gives the deposit back',
				JSON.stringify(pagamento),
			)
			const acconto = await s.banco.valore(
				'CRM Invoice',
				{ advance_for: s.stato.marco.appuntamento, docstatus: 1 },
				'name',
			)
			const nota = await s.attendi(
				() =>
					s.banco.valore('CRM Invoice', { reference_invoice: acconto || '-', docstatus: 1 }, [
						'name',
						'document_type',
						'grand_total',
					]),
				(v) => !!v,
				30,
			)
			s.verifica(nota?.document_type === 'TD04', 'The refunded advance gets its credit note', JSON.stringify(nota))
			const rimborso = await s.banco.attendiPosta(marco.email, /annullat|rimbors/i, { dopo: s.data('giovedi') })
			s.nota(`Email: «${rimborso.subject}»`)
		},
		{ chiave: 'marco.disdice', dopo: ['marco.prenota'] },
	)
}

/** Luca's online visit: the dietitian starts it from her phone, Luca enters from
 * his area a few minutes before; both reach the same room. */
async function laVisitaOnline(s: Settimana) {
	await s.alle('09:50')
	const luca = s.p('luca')
	await s.passo(
		'Luca, dieci minuti prima, entra nella visita online dalla sua area',
		luca,
		async () => {
			const invito = await s.banco.attendiPosta(luca.email, /area/i, { dopo: s.data('lunedi') })
			const page = await entraNellArea(s, luca, { link: (invito.links || []).find((l) => l.includes('/area')) })
			await page.goto('/area/appointments', { waitUntil: 'domcontentloaded' })
			const entra = page.getByRole('button', { name: 'Entra nella visita' }).first()
			await expect(entra).toBeVisible({ timeout: 30000 })
			await s.dito(luca, entra)
			const stanza = page
				.context()
				.waitForEvent('page', { timeout: 30000 })
				.catch(() => null)
			await premi(luca, entra)
			const aperta = await stanza
			// the room opens in a page of its own: its address once it is on its way
			if (aperta) await aperta.waitForURL((u) => u.protocol !== 'about:', { timeout: 30000 }).catch(() => {})
			const dove = aperta ? aperta.url() : page.url()
			s.nota(`Stanza: ${dove}`)
			s.verifica(dove.includes(STANZE_VIDEO), 'Luca reaches the video room', dove)
			s.stato.luca.stanza = new URL(dove).pathname
			if (aperta) await aperta.close()
		},
		{ chiave: 'luca.entra', dopo: ['luca.area'] },
	)
	await s.alle('10:00')
	const dietista = s.p('dietista')
	await s.passo(
		'La dietista avvia la visita online dal telefono, nella stessa stanza di Luca',
		dietista,
		async () => {
			const page = await s.alLavoro(dietista)
			await page.goto(`/crm/calendar?date=${s.data('giovedi')}`, { waitUntil: 'domcontentloaded' })
			await premi(dietista, page.getByText(luca.nome).first())
			const avvia = page.getByRole('button', { name: 'Avvia la visita online' }).first()
			await expect(avvia).toBeVisible({ timeout: 30000 })
			const stanza = page.context().waitForEvent('page', { timeout: 30000 })
			await premi(dietista, avvia)
			const aperta = await stanza
			await aperta.waitForURL((u) => u.protocol !== 'about:', { timeout: 30000 }).catch(() => {})
			const dove = aperta.url()
			s.verifica(dove.includes(STANZE_VIDEO), 'The dietitian reaches the video room', dove)
			s.verifica(
				!s.stato.luca.stanza || new URL(dove).pathname === s.stato.luca.stanza,
				'The same room for both',
				`${dove} vs ${s.stato.luca.stanza}`,
			)
			await aperta.close()
		},
		{ chiave: 'luca.visita.avviata', dopo: ['luca.prenota'] },
	)
	await s.alle('10:35')
	await s.passo(
		'La dietista scrive il controllo nutrizionale di Luca e lo firma; c’è già tutto pagato',
		dietista,
		async () => {
			const page = await persona(s, dietista, s.stato.luca.persona, 'clinic')
			await nuovaVisita(dietista, page, /^Controllo nutrizionale/)
			await scrivi(page, 'Peso', '78,5')
			await firmaLaVisita(dietista, page)
			// paid in full online: its advance invoice is its invoice
			const daFare = await s.banco.chiama('crm.invoicing.api.appointments_to_invoice', {}, 'GET')
			s.verifica(
				!(daFare || []).some((a: any) => a.name === s.stato.luca.appuntamento),
				'An appointment paid in full online is not to invoice again',
				JSON.stringify((daFare || []).map((a: any) => a.name)),
			)
		},
		{ chiave: 'luca.visita', dopo: ['luca.visita.avviata'] },
	)
}

/** Paolo's nutrition visit: he does not come; the desk marks him absent. */
async function paoloNonViene(s: Settimana) {
	await s.alle('11:25')
	const seg = s.p('segreteria')
	await s.passo(
		'Paolo non si presenta alla visita nutrizionale: la segreteria lo segna assente',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const riga = page
				.getByRole('link', { name: s.p('paolo').nome })
				.first()
				.locator('xpath=ancestor::div[contains(@class,"py-2")][1]')
			await premi(seg, riga.getByRole('button', { name: 'Assente' }))
			const stato = await s.attendi(
				() => s.banco.valore('CRM Appointment', s.stato.paolo.appuntamento_giovedi, 'status'),
				(v) => v === 'No Show',
			)
			s.verifica(stato === 'No Show', 'The appointment closes as a no-show', stato)
		},
		{ chiave: 'paolo.assente', dopo: ['paolo.giovedi'] },
	)
}

/** Marketing sends the autumn news to the people of the centre: only who agreed
 * to marketing is enrolled, and the rest are left out with the reason. */
async function laCampagna(s: Settimana) {
	await s.alle('12:00')
	const marketing = s.p('marketing')
	await s.passo(
		'Il marketing manda le novità d’autunno a una lista: solo a chi ha detto sì',
		marketing,
		async () => {
			const dopo = s.banco.ora
			const page = await s.alLavoro(marketing)
			await page.goto('/crm/persone', { waitUntil: 'domcontentloaded' })
			await premi(marketing, page.getByRole('button', { name: 'Invia a un elenco' }))
			const d = page.getByRole('dialog').last()
			await premi(marketing, d.getByText('Novità d’autunno').or(d.getByText("Novità d'autunno")).first())
			const iscrivi = d.getByRole('button', { name: /^Iscrivi/ })
			await expect(iscrivi).toBeVisible({ timeout: 30000 })
			await s.foto(marketing, 'lista')
			await premi(marketing, iscrivi)
			await esito(page)
			const campagna = await s.attendi(
				() => s.banco.valore('CRM Automation Campaign', {}, ['name', 'status', 'enrolled', 'skipped', 'total']),
				(v) => !!v && v.status !== 'Queued' && v.status !== 'Running',
				60,
			)
			s.nota(`Campagna: ${JSON.stringify(campagna)}`)
			s.verifica(Number(campagna?.enrolled) > 0, 'Somebody who agreed is enrolled', JSON.stringify(campagna))
			await s.banco.esegui('crm.automation.engine.process_due_enrollments')
			const anna = await s.banco.attendiPosta(s.p('anna').email, /novità/i, { dopo, secondi: 30 })
			s.verifica(!!anna, 'Anna, who agreed in her form, gets the news')
			const altri = await s.banco.posta(undefined, dopo)
			const senzaConsenso = ['marco', 'davide']
				.map((k) => s.p(k).email)
				.filter((email) => altri.some((m) => (m.to || []).includes(email) && /novità/i.test(m.subject)))
			s.verifica(!senzaConsenso.length, 'Nobody who did not agree gets it', senzaConsenso.join(', '))
		},
		{ chiave: 'campagna', dopo: ['anna.moduli'] },
	)
}

/** The visits completed yesterday and today: two hours after, the review
 * request; its link counts the opening and goes to Google. */
async function laRecensione(s: Settimana) {
	await s.alle('12:30')
	const giulia = s.p('giulia')
	await s.passo(
		'Giulia riceve la richiesta di recensione e la apre',
		giulia,
		async () => {
			const mail = await s.banco.attendiPosta(giulia.email, /com.è andata/i, { dopo: s.data('mercoledi'), secondi: 30 })
			const link = collegamento(mail.links, /recension|review|\/r\//)
			const risposta = await s.banco.richiestaGrezza(link)
			s.nota(`Link: ${risposta.status} → ${risposta.location}`)
			s.verifica(
				risposta.status >= 300 && risposta.status < 400 && /google\./.test(risposta.location || ''),
				'The review link goes to Google',
				`${risposta.status} ${risposta.location}`,
			)
			const richiesta = await s.banco.valore('CRM Review Request', { lead: s.stato.giulia.persona }, [
				'name',
				'clicked_on',
			])
			s.verifica(!!richiesta?.clicked_on, 'The opening is counted', JSON.stringify(richiesta))
		},
		{ chiave: 'giulia.recensione', dopo: ['giulia.visita'] },
	)
}

/** Anna's first session of the cycle, on the follow-up sheet; invoiced at its price. */
async function laSedutaDiAnna(s: Settimana) {
	await s.alle('16:55')
	const seg = s.p('segreteria')
	await s.passo(
		'Anna arriva per la prima seduta del ciclo',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const riga = page
				.getByRole('link', { name: s.p('anna').nome })
				.first()
				.locator('xpath=ancestor::div[contains(@class,"py-2")][1]')
			await expect(page.getByText(/Seduta 1 di 10/).first()).toBeVisible()
			await premi(seg, riga.getByRole('button', { name: 'Accogli' }))
			await expect(riga.getByRole('button', { name: 'Presente' })).toBeVisible()
		},
		{ chiave: 'anna.seduta1.arrivata', dopo: ['anna.ciclo'] },
	)
	await s.alle('17:05')
	const fisio = s.p('fisioterapista')
	await s.passo(
		'La fisioterapista scrive il controllo della prima seduta e lo firma',
		fisio,
		async () => {
			const page = await persona(s, fisio, s.stato.anna.persona, 'clinic')
			await nuovaVisita(fisio, page, /^Controllo fisioterapico/)
			await scrivi(page, 'Fatto oggi', 'Terapia manuale lombare, esercizi di controllo motorio.')
			await firmaLaVisita(fisio, page)
		},
		{ chiave: 'anna.seduta1', dopo: ['anna.seduta1.arrivata'] },
	)
	await s.alle('17:50')
	await s.passo(
		'Anna paga la seduta con la carta',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const fattura = fatturaDi(page, s.p('anna').nome)
			await expect(fattura).toBeVisible({ timeout: 30000 })
			await premi(seg, fattura)
			await emettiLaBozza(s, seg, page, 'anna', { pagamento: /Carta/ })
			const emessa = await s.banco.valore('CRM Invoice', { appointment: s.stato.anna.seduta_giovedi, docstatus: 1 }, [
				'grand_total',
			])
			s.verifica(Number(emessa?.grand_total) === 50, 'A session of the cycle at its price', String(emessa?.grand_total))
		},
		{ chiave: 'anna.seduta1.fattura', dopo: ['anna.seduta1'] },
	)
}

/** Giulia cannot come tomorrow morning: too late to cancel online, she calls; the
 * desk cancels it and the deposit stays with the centre. */
async function giuliaDisdiceTardi(s: Settimana) {
	await s.alle('18:30')
	const giulia = s.p('giulia')
	await s.passo(
		'Giulia non può venire domani: online è troppo tardi per annullare, e lo dice',
		giulia,
		async () => {
			const mail = await s.banco.attendiPosta(giulia.email, /11:30/, { dopo: s.data('mercoledi') })
			const link = collegamento(mail.links, /prenota\?token=/)
			const page = await giulia.apri(s.browser, s.banco)
			await page.goto(link, { waitUntil: 'domcontentloaded' })
			await expect(page.getByText('È troppo tardi per annullare online. Contattaci.')).toBeVisible({ timeout: 30000 })
			await expect(page.getByRole('button', { name: 'Annulla prenotazione' })).toHaveCount(0)
		},
		{ chiave: 'giulia.tardi', dopo: ['giulia.controllo'] },
	)
	const seg = s.p('segreteria')
	await s.passo(
		'Giulia chiama: la segreteria annulla il controllo, l’acconto resta al centro',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto(`/crm/calendar?date=${s.data('venerdi')}`, { waitUntil: 'domcontentloaded' })
			await premi(seg, page.getByText(giulia.nome).first())
			await premi(seg, page.getByRole('button', { name: /^Confermat|^Pianificat/ }).first())
			await premi(seg, page.getByRole('menuitem', { name: /^Annullat/ }).first())
			await expect(page.getByText('Annullare questo appuntamento?')).toBeVisible()
			await page.getByLabel('Perché').fill('Ha chiamato: non sta bene')
			await premi(seg, page.getByRole('button', { name: "Annulla l'appuntamento" }))
			await esito(page, /annullat/i)
			const stato = await s.banco.valore('CRM Appointment', s.stato.giulia.controllo, 'status')
			s.verifica(stato === 'Cancelled', 'The check-up is cancelled', stato)
			await new Promise((fatto) => setTimeout(fatto, 5000))
			const pagamento = await s.banco.valore('CRM Online Payment', { appointment: s.stato.giulia.controllo }, [
				'status',
				'refunded_amount',
			])
			s.verifica(pagamento?.status === 'Paid', 'A late cancellation keeps the deposit', JSON.stringify(pagamento))
			const acconto = await s.banco.valore(
				'CRM Invoice',
				{ advance_for: s.stato.giulia.controllo, docstatus: 1 },
				'name',
			)
			const nota = acconto ? await s.banco.conta('CRM Invoice', { reference_invoice: acconto, docstatus: 1 }) : 0
			s.verifica(nota === 0, 'No credit note for a deposit kept', String(nota))
		},
		{ chiave: 'giulia.disdice', dopo: ['giulia.tardi'] },
	)
}
