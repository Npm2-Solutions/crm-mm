// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect } from '@playwright/test'
import { finoAgliOrari, premi, prenotaOnline, type Prenotazione } from '../lib/azioni'
import { entraNellArea, linkDellArea } from '../lib/area'
import { collegamento } from '../lib/azioni'
import { emettiLaBozza, esito, impostazioni, nuovoAppuntamento, persona } from '../lib/scrivania'
import type { Settimana } from '../lib/settimana'
import { permessi } from './permessi'

/** Monday: the manager takes invoicing live, the patients book from home before
 * the centre opens, the desk opens and takes the phone, a class fills and the
 * waiting list takes the next. */
export async function lunedi(s: Settimana) {
	await s.giornata('lunedi', '07:40')
	await inProduzione(s)
	await prenotazioniOnline(s)
	await laSegreteriaApre(s)
	await fattureInBozza(s)
	await alTelefono(s)
	await listaDAttesa(s)
	await areaAperta(s)
	await laLezioneSiLibera(s)
	await promemoria(s)
	await laLezione(s)
	await laLezioneFinisce(s)
	await laCassa(s, 'lunedi', 'segreteria')
	await permessi(s)
}

async function inProduzione(s: Settimana) {
	const r = s.p('responsabile')
	await s.passo(
		'La responsabile entra dalla pagina di accesso e attiva la fatturazione',
		r,
		async () => {
			await r.entra(s.browser, s.banco, { dalModulo: true })
			const page = await impostazioni(s, r, 'Provider connection')
			const dialogo = page.getByRole('dialog').last()
			const inProva = dialogo.getByText('In prova', { exact: true })
			await expect(inProva.or(dialogo.getByText('Attiva', { exact: true }))).toBeVisible()
			if (await inProva.isVisible()) {
				await premi(r, dialogo.getByRole('button', { name: 'Attiva la fatturazione' }))
				await premi(r, page.getByRole('dialog').last().getByRole('button', { name: 'Attiva la fatturazione' }))
				await esito(page, /attiva/i)
			} else s.nota('La fatturazione era già attiva (una settimana di prima)')
			const azienda = await s.banco.valore('CRM Invoicing Company', { is_default: 1 }, 'provider_environment')
			s.verifica(azienda === 'production', 'Invoicing went live', azienda)
		},
		{ chiave: 'produzione' },
	)
}

/** Who books from home, each on their own phone: a deposit paid, a card declined
 * then another, a bank asking to confirm, an online visit paid in full, a fund in
 * direct form, a mother for her child. */
async function prenotazioniOnline(s: Settimana) {
	const sv = s.copione.services
	const prenotazioni: Array<[string, string, Omit<Prenotazione, 'nome' | 'email'>, string]> = [
		[
			'giulia',
			'08:05',
			{
				sede: 'Sede di Milano',
				servizio: sv.visita,
				giorno: s.data('mercoledi'),
				ora: '10:00',
				carte: ['4242424242424242'],
			},
			'Giulia prenota la visita medica di mercoledì e paga l’acconto con la carta',
		],
		[
			'marco',
			'08:15',
			{
				sede: 'Sede di Milano',
				servizio: sv.visita,
				giorno: s.data('venerdi'),
				ora: '09:00',
				carte: ['4000000000009995', '4242424242424242'],
			},
			'Marco prenota la visita di venerdì: la prima carta è rifiutata, la seconda passa',
		],
		[
			'sara',
			'08:25',
			{
				sede: 'Sede di Monza',
				servizio: sv.visita,
				giorno: s.data('martedi'),
				ora: '15:00',
				carte: ['4000002500003155'],
			},
			'Sara prenota a Monza per martedì: la banca chiede di confermare il pagamento',
		],
		[
			'luca',
			'08:35',
			{
				sede: 'Sede di Milano',
				servizio: sv.nutrizione_online,
				giorno: s.data('giovedi'),
				ora: '10:00',
				carte: ['4242424242424242'],
			},
			'Luca, col testo grande, prenota il controllo nutrizionale online e lo paga tutto',
		],
		[
			'anna',
			'08:45',
			{
				sede: 'Sede di Milano',
				servizio: sv.visita_fisio,
				giorno: s.data('martedi'),
				ora: '10:00',
				convenzione: s.copione.convention,
				tessera: 'FSP-0042-AN',
			},
			'Anna, col telefono di lato, prenota la visita fisioterapica con il fondo sanitario',
		],
		[
			'elena',
			'08:55',
			{
				sede: 'Sede di Milano',
				servizio: sv.odonto,
				giorno: s.data('mercoledi'),
				ora: '15:00',
				perAltro: { nome: 'Tommaso Rinaldi', relazione: 'Parent' },
			},
			'Elena prenota la prima visita dal dentista per suo figlio Tommaso',
		],
	]
	for (const [chiave, ora, prenotazione, titolo] of prenotazioni) {
		await s.alle(ora)
		const chi = s.p(chiave)
		const dati = s.persona(chiave)
		await s.passo(
			titolo,
			chi,
			async () => {
				const inizio = s.banco.ora
				const token = await prenotaOnline(s, chi, {
					...prenotazione,
					nome: chi.nome,
					email: chi.email,
					telefono: dati.mobile,
					marketing: chiave === 'giulia' || chiave === 'sara',
				})
				s.stato[chiave] = { ...(s.stato[chiave] || {}), token }
				const righe = await s.banco.lista(
					'CRM Appointment Participant',
					{ access_token: token },
					['parent', 'party', 'status', 'booked_by'],
					{ genitore: 'CRM Appointment' },
				)
				s.verifica(righe.length === 1, 'The booking has its place on the agenda', token)
				if (righe[0]) {
					s.stato[chiave].appuntamento = righe[0].parent
					// booked for somebody else: the place is theirs, the booker stays a person of their own
					s.stato[chiave].persona = righe[0].booked_by || righe[0].party
					if (prenotazione.perAltro) {
						s.verifica(
							!!righe[0].booked_by,
							'A booking for a child is the child’s, booked by the parent',
							JSON.stringify(righe[0]),
						)
						s.stato.tommaso = { persona: righe[0].party, appuntamento: righe[0].parent }
					}
				}
				const mail = await s.banco.attendiPosta(chi.email, /prenot|appuntament|richiest/i, { dopo: inizio })
				s.nota(`Email a ${chi.email}: «${mail.subject}»`)
				if (prenotazione.carte) {
					// what is paid online is invoiced the day it arrives: an advance invoice
					const appuntamento = righe[0]?.parent
					const acconti = await s.banco.lista('CRM Invoice', { advance_for: appuntamento }, [
						'name',
						'docstatus',
						'grand_total',
						'collected_on',
						'test_document',
					])
					s.verifica(acconti.length === 1, 'The deposit paid online has its advance invoice', JSON.stringify(acconti))
					if (acconti[0]) {
						// /prenota asks no codice fiscale: a healthcare invoice stays a draft
						// and whoever manages invoicing is told
						s.nota(`Fattura d’acconto ${acconti[0].docstatus === 1 ? 'emessa' : 'in bozza'}: ${acconti[0].name}`)
						if (acconti[0].docstatus === 0) {
							const avvisi = await s.banco.conta('CRM Notification', {
								notification_type_doc: acconti[0].name,
							})
							s.verifica(avvisi > 0, 'A draft of a payment online is told to invoicing', acconti[0].name)
						}
						if (s.esito('produzione'))
							s.verifica(!acconti[0].test_document, 'The advance invoice is a real one', acconti[0].name)
					}
				}
			},
			{ chiave: `${chiave}.prenota` },
		)
	}
}

/** What was paid online stayed a draft where the person gave no codice fiscale:
 * the manager is told, asks each one for it and issues the invoice, the day the
 * money arrived. */
async function fattureInBozza(s: Settimana) {
	await s.alle('09:10')
	const r = s.p('responsabile')
	const pagati = ['giulia', 'marco', 'sara', 'luca'].filter((k) => s.stato[k]?.appuntamento)
	await s.passo(
		'La responsabile apre la notifica delle fatture d’acconto in bozza, scrive i codici fiscali e le emette',
		r,
		async () => {
			const page = await r.apri(s.browser, s.banco)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			await premi(r, page.getByRole('button', { name: 'Notifiche' }).first())
			const notifica = page.getByText(/rimasta in bozza/).first()
			await expect(notifica).toBeVisible()
			await premi(r, notifica)
			await page.waitForURL(/\/crm\/fatture/)
			let emesse = 0
			for (const chiave of pagati) {
				const appuntamento = s.stato[chiave].appuntamento
				const bozza = await s.banco.valore('CRM Invoice', { advance_for: appuntamento }, ['name', 'docstatus'])
				if (!bozza || bozza.docstatus !== 0) continue
				const dialogo = page.getByRole('dialog').last()
				if (!(await dialogo.isVisible().catch(() => false)) || !(await dialogo.getByText(s.p(chiave).nome).count())) {
					await page.keyboard.press('Escape').catch(() => {})
					await page.goto(`/crm/fatture?open=${bozza.name}`, { waitUntil: 'domcontentloaded' })
				}
				await expect(page.getByRole('dialog').last()).toBeVisible()
				const d = page.getByRole('dialog').last()
				await expect(d.getByText('Prima di emetterla')).toBeVisible()
				if (
					!(await d
						.getByLabel('Codice fiscale')
						.isVisible()
						.catch(() => false))
				)
					await premi(r, d.getByRole('button', { name: 'Dati in fattura' }))
				const dati = s.persona(chiave)
				await d.getByLabel('Codice fiscale').fill(dati.fiscal_code)
				await d.getByLabel('Indirizzo', { exact: true }).fill(`${dati.address.street} ${dati.address.number}`)
				await d.getByLabel('CAP').fill(dati.address.postcode)
				await d.getByLabel('Città').fill(dati.address.city)
				await premi(r, d.getByRole('button', { name: 'Emetti', exact: true }))
				await esito(page, /emessa/i)
				const dopo = await s.banco.valore('CRM Invoice', bozza.name, ['docstatus', 'collected_on', 'posting_date'])
				s.verifica(dopo.docstatus === 1, 'The advance invoice is issued', `${chiave} ${bozza.name}`)
				s.verifica(!!dopo.collected_on, 'The advance invoice paid online is collected', `${chiave} ${bozza.name}`)
				s.verifica(
					dopo.posting_date === s.data('lunedi'),
					'The advance invoice is dated the day the money arrived',
					`${chiave} ${dopo.posting_date}`,
				)
				emesse += 1
			}
			s.nota(`${emesse} fatture d’acconto emesse`)
		},
		{ chiave: 'acconti.emessi', dopo: ['produzione'] },
	)
}

async function laSegreteriaApre(s: Settimana) {
	await s.alle('09:00')
	const seg = s.p('segreteria')
	await s.passo(
		'La segreteria entra e apre l’accoglienza e l’agenda della settimana',
		seg,
		async () => {
			const page = await seg.entra(s.browser, s.banco, { dalModulo: true })
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			await expect(page.getByText('Appuntamenti').first()).toBeVisible()
			await page.goto(`/crm/calendar?date=${s.data('martedi')}`, { waitUntil: 'domcontentloaded' })
			for (const chiave of ['sara', 'anna']) {
				if (!s.stato[chiave]?.appuntamento) continue
				await expect(page.getByText(s.p(chiave).nome).first(), `${chiave} on Tuesday's agenda`).toBeVisible()
			}
			// the week of one professional at a time
			await premi(seg, page.getByText('Settimana', { exact: true }).first())
			await page.waitForTimeout(800)
			await s.foto(seg, 'settimana')
		},
		{ chiave: 'segreteria.entra' },
	)
	await s.passo(
		'La segreteria conferma la visita di Anna col fondo e scrive l’autorizzazione',
		seg,
		async () => {
			const appuntamento = s.stato.anna?.appuntamento
			if (!appuntamento) throw new Error('Anna has no appointment')
			const prima = await s.banco.valore('CRM Appointment', appuntamento, ['status', 'convention', 'convention_form'])
			s.verifica(prima.status === 'Scheduled', 'A fund booking online waits for the centre', prima.status)
			s.verifica(prima.convention_form === 'Direct', 'The fund is in direct form', prima.convention_form)
			const page = await seg.apri(s.browser, s.banco)
			await page.goto(`/crm/calendar?date=${s.data('martedi')}`, { waitUntil: 'domcontentloaded' })
			await premi(seg, page.getByText(s.p('anna').nome).first())
			await expect(page.getByText('Autorizzazione mancante').first()).toBeVisible()
			// the authorisation from the fund, then the yes
			await premi(seg, page.getByRole('button', { name: 'Modifica' }))
			await page.getByLabel('Autorizzazione').fill('AUT-2026-0042')
			await premi(seg, page.getByRole('button', { name: 'Salva', exact: true }))
			await esito(page)
			await premi(seg, page.getByRole('button', { name: /Pianificat|In attesa/ }).first())
			await premi(seg, page.getByRole('menuitem', { name: /Confermato/ }).first())
			await esito(page)
			const dopo = await s.attendi(
				() => s.banco.valore('CRM Appointment', appuntamento, ['status', 'authorisation']),
				(v) => v?.status === 'Confirmed',
			)
			s.verifica(dopo.status === 'Confirmed', 'Anna’s visit is confirmed', dopo.status)
			s.verifica(dopo.authorisation === 'AUT-2026-0042', 'The authorisation is written', dopo.authorisation)
			await s.banco.attendiPosta(s.p('anna').email, /confermat/i, { dopo: s.banco.ora.slice(0, 10) })
		},
		{ chiave: 'anna.confermata', dopo: ['anna.prenota', 'segreteria.entra'] },
	)
}

/** The phone rings: four people into the Monday's Pilates class, which fills; a
 * first dental visit; a nutrition visit; a visit for a company's employee. */
async function alTelefono(s: Settimana) {
	const seg = s.p('segreteria')
	const sv = s.copione.services
	const nuovo = (chiave: string) => {
		const p = s.persona(chiave)
		return { nome: `${p.first_name} ${p.last_name}`, telefono: p.mobile, email: p.email }
	}
	await s.alle('09:30')
	await s.passo(
		'Al telefono: quattro persone nella lezione di Pilates di stasera, che si riempie',
		seg,
		async () => {
			const nome = await nuovoAppuntamento(s, seg, {
				giorno: s.data('lunedi'),
				ora: '18:00',
				servizio: sv.pilates,
				persone: ['paolo', 'chiara', 'federica', 'roberto'].map(nuovo),
			})
			s.stato.pilates = { lunedi: nome }
			const righe = await s.banco.lista(
				'CRM Appointment Participant',
				{ parent: nome },
				['party', 'participant_name', 'status'],
				{ genitore: 'CRM Appointment' },
			)
			s.verifica(righe.length === 4, 'Four people in the class', JSON.stringify(righe))
			for (const riga of righe) {
				const chiave = Object.keys(s.persone).find((k) => s.persone[k].nome === riga.participant_name)
				if (chiave) s.stato[chiave] = { ...(s.stato[chiave] || {}), persona: riga.party }
				s.verifica(!!riga.party, 'Somebody typed by the desk becomes a person', riga.participant_name)
			}
		},
		{ chiave: 'pilates.pieno', dopo: ['segreteria.entra'] },
	)
	const altri: Array<[string, string, string, string, string]> = [
		['roberto', sv.odonto, 'mercoledi', '09:30', 'Roberto prenota al telefono la prima visita dal dentista'],
		['paolo', sv.nutrizione, 'giovedi', '11:00', 'Paolo prenota al telefono la visita nutrizionale di giovedì'],
		['federica', sv.visita, 'venerdi', '10:00', 'Federica prenota la visita medica di venerdì, la paga la sua azienda'],
	]
	for (const [chiave, servizio, giorno, ora, titolo] of altri) {
		await s.passo(
			titolo,
			seg,
			async () => {
				const nome = await nuovoAppuntamento(s, seg, {
					giorno: s.data(giorno),
					ora,
					servizio,
					persone: [{ nome: s.p(chiave).nome, esistente: true }],
				})
				s.stato[chiave] = { ...(s.stato[chiave] || {}), [`appuntamento_${giorno}`]: nome }
				const persona = await s.banco.valore(
					'CRM Appointment Participant',
					{ parent: nome },
					'party',
					'CRM Appointment',
				)
				s.verifica(
					!persona || persona === s.stato[chiave].persona,
					'The person found by name is the same record, not a second one',
					`${persona} vs ${s.stato[chiave].persona}`,
				)
			},
			{ chiave: `${chiave}.${giorno}`, dopo: ['pilates.pieno'] },
		)
	}
}

/** Davide wants the same class: it is full, he joins the waiting list from
 * /prenota. */
async function listaDAttesa(s: Settimana) {
	await s.alle('10:00')
	const davide = s.p('davide')
	await s.passo(
		'Davide vuole la lezione di Pilates di stasera: è piena, si mette in lista d’attesa',
		davide,
		async () => {
			const page = await finoAgliOrari(s, davide, {
				sede: 'Sede di Milano',
				servizio: s.copione.services.pilates,
				giorno: s.data('lunedi'),
				ora: '18:00',
				nome: davide.nome,
				email: davide.email,
			})
			const main = page.locator('#main')
			const piena = main.locator('button.time.full', { hasText: '18:00' })
			await expect(piena).toBeVisible()
			await premi(davide, piena)
			await expect(main.locator('h2', { hasText: /Lista d.attesa/ })).toBeVisible()
			await main.locator('#f-full_name').fill(davide.nome)
			await main.locator('#f-email').fill(davide.email)
			if (await main.locator('#f-phone').count()) await main.locator('#f-phone').fill(s.persona('davide').mobile)
			if (await main.locator('#f-consent').count()) await main.locator('#f-consent').check()
			await premi(davide, main.locator('button.primary[type=submit]'))
			await expect(main.locator('h2', { hasText: /Sei in lista d.attesa/ })).toBeVisible()
			const voci = await s.banco.lista('CRM Waiting List Entry', { email: davide.email, status: 'Waiting' }, [
				'name',
				'status',
				'lead',
			])
			s.verifica(voci.length === 1, 'Davide is on the waiting list', JSON.stringify(voci))
			s.stato.davide = { ...(s.stato.davide || {}), attesa: voci[0]?.name, persona: voci[0]?.lead }
		},
		{ chiave: 'davide.attesa', dopo: ['pilates.pieno'] },
	)
}

/** The desk opens the area to whoever comes this week: a mother to her child's too. */
async function areaAperta(s: Settimana) {
	await s.alle('10:15')
	const seg = s.p('segreteria')
	const chi = ['giulia', 'sara', 'luca', 'anna', 'elena', 'paolo', 'chiara', 'roberto']
	for (const chiave of chi) {
		await s.passo(
			`La segreteria apre l’area a ${s.p(chiave).nome}`,
			seg,
			async () => {
				const lead = s.stato[chiave]?.persona
				if (!lead) throw new Error(`${chiave} is not a person yet`)
				await apriLArea(s, lead)
				await s.banco.attendiPosta(s.p(chiave).email, /area/i, { dopo: s.banco.ora.slice(0, 10) })
				const accessi = await s.banco.conta('CRM Area Access', { lead })
				s.verifica(accessi > 0, 'The area is open', chiave)
			},
			{ chiave: `${chiave}.area`, dopo: ['segreteria.entra'] },
		)
	}
	await s.passo(
		'La segreteria apre l’area di Tommaso alla mamma, Elena',
		seg,
		async () => {
			const tommaso = s.stato.tommaso?.persona
			if (!tommaso) throw new Error('Tommaso has no record of his own')
			await apriLArea(s, tommaso, { genitore: s.p('elena').email })
			const accesso = await s.banco.valore('CRM Area Access', { lead: tommaso }, ['user', 'relation'])
			s.verifica(accesso?.user === s.p('elena').email, 'Elena enters her son’s area', JSON.stringify(accesso))
		},
		{ chiave: 'tommaso.area', dopo: ['elena.area'] },
	)
}

async function apriLArea(s: Settimana, lead: string, { genitore }: { genitore?: string } = {}) {
	const seg = s.p('segreteria')
	const page = await persona(s, seg, lead, 'area')
	const apri = page.getByRole('button', { name: "Apri l'area" }).first()
	const aggiungi = page.getByRole('button', { name: 'Aggiungi qualcuno' }).first()
	await expect(apri.or(aggiungi)).toBeVisible()
	if (!genitore && (await aggiungi.isVisible())) {
		// opened already by itself: an invoice's email opens the area (doc 41)
		s.nota('L’area era già aperta: l’ha aperta l’email della fattura')
		return
	}
	await premi(seg, (await apri.isVisible()) ? apri : aggiungi)
	const dialogo = page.getByRole('dialog').last()
	if (genitore) {
		// «Who enters» is a select (reka-ui: a combobox and its options)
		await premi(seg, dialogo.getByRole('combobox').first())
		await premi(seg, page.getByRole('option', { name: /genitore/i }).first())
		await dialogo.getByLabel(/email/i).fill(genitore)
	}
	await premi(seg, dialogo.getByRole('button', { name: "Manda l'invito" }))
	await esito(page, /invito/i)
}

/** The reminders of tomorrow's appointments leave a day before; Sara answers she
 * will be there. Anna booked this morning: her booking's email was her reminder. */
async function promemoria(s: Settimana) {
	await s.alle('15:15')
	const sara = s.p('sara')
	await s.passo(
		'I promemoria di domani partono: Sara risponde «ci sarò» dal link dell’email',
		sara,
		async () => {
			const mail = await s.banco.attendiPosta(sara.email, /promemoria|domani|ricord/i, { dopo: s.data('lunedi') })
			s.nota(`Promemoria: «${mail.subject}»`)
			const link = collegamento(mail.links, /prenota\?token=|conferm/)
			const page = await sara.apri(s.browser, s.banco)
			await page.goto(link, { waitUntil: 'domcontentloaded' })
			const ci = page.getByRole('button', { name: 'Confermo che ci sarò' })
			await s.dito(sara, ci)
			await premi(sara, ci)
			await expect(page.getByText('Hai confermato: ti aspettiamo.')).toBeVisible()
			const risposta = await s.banco.valore('CRM Appointment Reminder', { appointment: s.stato.sara.appuntamento }, [
				'answer',
				'channel',
			])
			s.verifica(!!risposta?.answer, 'The answer is kept on the reminder', JSON.stringify(risposta))
			// Anna booked at a quarter to nine: no reminder on top of the booking's email
			const ad_anna = await s.banco.conta('CRM Appointment Reminder', {
				appointment: s.stato.anna?.appuntamento || '-',
			})
			s.verifica(ad_anna === 0, 'No reminder for what was booked just before its time', String(ad_anna))
		},
		{ chiave: 'sara.promemoria', dopo: ['sara.prenota'] },
	)
}

/** Chiara cannot come tonight and calls: her seat goes to the first on the list,
 * Davide, who confirms from the offer's email. */
async function laLezioneSiLibera(s: Settimana) {
	await s.alle('14:00')
	const seg = s.p('segreteria')
	await s.passo(
		'Chiara chiama: non viene stasera, la segreteria libera il suo posto',
		seg,
		async () => {
			const page = await seg.apri(s.browser, s.banco)
			await page.goto(`/crm/calendar?date=${s.data('lunedi')}`, { waitUntil: 'domcontentloaded' })
			await premi(seg, page.getByText(/Pilates di gruppo/).first())
			const riga = page
				.locator('div:has(> span.lucide-user)')
				.filter({ hasText: s.p('chiara').nome })
				.first()
			await premi(seg, riga.getByRole('button', { name: /Prenotat/ }).first())
			await premi(seg, page.getByRole('menuitem', { name: /Annullat|Disdett/ }).first())
			await page.waitForTimeout(1000)
			const stato = await s.banco.statoDi(s.stato.pilates.lunedi, s.stato.chiara.persona)
			s.verifica(stato === 'Cancelled', 'Chiara’s seat is free', stato)
		},
		{ chiave: 'chiara.disdice', dopo: ['pilates.pieno'] },
	)
	const davide = s.p('davide')
	await s.passo(
		'La lista d’attesa offre il posto a Davide, che conferma dal link',
		davide,
		async () => {
			const mail = await s.banco.attendiPosta(davide.email, /liberato un posto/i, {
				dopo: s.banco.ora.slice(0, 10),
				secondi: 40,
			})
			s.nota(`Offerta: «${mail.subject}»`)
			const link = collegamento(mail.links, /lista-attesa/)
			const page = await davide.apri(s.browser, s.banco)
			await page.goto(link, { waitUntil: 'domcontentloaded' })
			const prendo = page.locator('button.primary').first()
			await s.dito(davide, prendo)
			await premi(davide, prendo)
			await page.waitForLoadState('networkidle').catch(() => {})
			const righe = await s.banco.lista(
				'CRM Appointment Participant',
				{ parent: s.stato.pilates.lunedi, status: ['!=', 'Cancelled'] },
				['participant_name', 'party'],
				{ genitore: 'CRM Appointment' },
			)
			s.verifica(
				righe.some((r) => r.participant_name === davide.nome),
				'Davide has the seat',
				JSON.stringify(righe),
			)
			const d = righe.find((r) => r.participant_name === davide.nome)
			if (d) s.stato.davide = { ...(s.stato.davide || {}), persona: d.party }
		},
		{ chiave: 'davide.posto', dopo: ['chiara.disdice', 'davide.attesa'] },
	)
}

/** The evening's class: Paolo says he is here from the area, the desk checks the
 * others in, the physiotherapist closes the class on her phone, the desk invoices
 * each one and closes the cash. */
async function laLezione(s: Settimana) {
	await s.alle('17:45')
	const paolo = s.p('paolo')
	await s.passo(
		'Paolo entra nell’area dal link dell’invito e dice «sono qui»',
		paolo,
		async () => {
			const invito = await s.banco.attendiPosta(paolo.email, /area/i)
			const page = await entraNellArea(s, paolo, { link: linkDellArea(invito.links) })
			const qui = page.getByRole('button', { name: 'Sono qui' }).first()
			await expect(qui).toBeVisible()
			await s.dito(paolo, qui)
			await premi(paolo, qui)
			await page.waitForTimeout(1000)
			const stato = await s.banco.statoDi(s.stato.pilates.lunedi, s.stato.paolo.persona)
			s.verifica(stato === 'Arrived', 'Paolo is in the waiting room', stato)
		},
		{ chiave: 'paolo.qui', dopo: ['paolo.area', 'pilates.pieno'] },
	)
	await s.alle('17:55')
	const seg = s.p('segreteria')
	await s.passo(
		'In accoglienza: la segreteria accoglie gli altri della lezione',
		seg,
		async () => {
			const page = await seg.apri(s.browser, s.banco)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			for (const chiave of ['federica', 'roberto', 'davide']) {
				const nome = s.p(chiave).nome
				const riga = page
					.getByRole('link', { name: nome })
					.first()
					.locator('xpath=ancestor::div[contains(@class,"py-2")][1]')
				await premi(seg, riga.getByRole('button', { name: 'Accogli' }))
				await expect(riga.getByRole('button', { name: 'Presente' })).toBeVisible()
			}
		},
		{ chiave: 'lezione.arrivi', dopo: ['pilates.pieno'] },
	)
}

/** After the class: the physiotherapist says on her phone who came, the class
 * closes by itself; the desk invoices each place to whoever took it, as they pay. */
async function laLezioneFinisce(s: Settimana) {
	await s.alle('19:05')
	const fisio = s.p('fisioterapista')
	const venuti = ['paolo', 'federica', 'roberto', 'davide'].filter((k) => s.stato[k]?.persona)
	await s.passo(
		'La fisioterapista, dal telefono, segna chi è venuto alla lezione',
		fisio,
		async () => {
			const page = await s.alLavoro(fisio)
			await page.goto(`/crm/calendar?date=${s.data('lunedi')}`, { waitUntil: 'domcontentloaded' })
			await premi(fisio, page.getByText(/Pilates di gruppo/).first())
			for (const chiave of venuti) {
				const riga = page
					.locator('div:has(> span.lucide-user)')
					.filter({ hasText: s.p(chiave).nome })
					.first()
				await expect(riga).toBeVisible()
				await premi(fisio, riga.getByRole('button', { name: /Arrivat|Prenotat/ }).first())
				await premi(fisio, page.getByRole('menuitem', { name: /Venut/ }).first())
				await expect(riga.getByRole('button', { name: /Venut/ }).first()).toBeVisible()
			}
			const stato = await s.attendi(
				() => s.banco.valore('CRM Appointment', s.stato.pilates.lunedi, 'status'),
				(v) => v === 'Completed',
			)
			s.verifica(stato === 'Completed', 'The class closes by itself once everybody has an outcome', stato)
		},
		{ chiave: 'lezione.chiusa', dopo: ['lezione.arrivi'] },
	)
	await s.alle('19:15')
	const seg = s.p('segreteria')
	// as they leave, each one pays their place: cash, a card
	const pagamenti: Record<string, RegExp> = {
		paolo: /Contanti/,
		federica: /Carta/,
		roberto: /Contanti/,
		davide: /Contanti/,
	}
	await s.passo(
		'In accoglienza la segreteria fa la fattura a ciascuno della lezione',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			for (const chiave of venuti) {
				const nome = s.p(chiave).nome
				const fattura = page.getByRole('button', { name: `Emetti la fattura a ${nome}` })
				await expect(fattura).toBeVisible({ timeout: 30000 })
				await premi(seg, fattura)
				await emettiLaBozza(s, seg, page, chiave, { pagamento: pagamenti[chiave] })
				await page.keyboard.press('Escape').catch(() => {})
				await expect(fattura).toHaveCount(0, { timeout: 15000 })
			}
			const fatture = await s.banco.lista('CRM Invoice', { appointment: s.stato.pilates.lunedi, docstatus: 1 }, [
				'party',
				'grand_total',
				'payment_method',
				'collected_on',
			])
			const persone = fatture.map((f) => f.party).sort()
			const attese = venuti.map((k) => s.stato[k].persona).sort()
			s.verifica(
				JSON.stringify(persone) === JSON.stringify(attese),
				'Each one who came has the invoice of their place',
				JSON.stringify(fatture),
			)
			s.verifica(
				fatture.every((f) => Number(f.grand_total) === 20 && f.collected_on === s.data('lunedi')),
				'Each place is 20 €, collected today',
				JSON.stringify(fatture),
			)
		},
		{ chiave: 'lezione.fatture', dopo: ['lezione.chiusa'] },
	)
}

/** The day's cash at a location: what the screen expects is what the invoices
 * collected in cash, to the cent, and it closes. */
export async function laCassa(s: Settimana, giorno: string, chi: string, dove = 'milano') {
	const sede = s.copione.location_titles[dove]
	await s.alle('19:40')
	const cassiere = s.p(chi)
	await s.passo(
		`Chiusura di cassa: ${sede}`,
		cassiere,
		async () => {
			const luogo = s.copione.locations[dove]
			// the cash the day collected there, from the invoices themselves
			const incassate = await s.banco.lista(
				'CRM Invoice',
				{ collected_on: s.data(giorno), centre_location: luogo, docstatus: 1, payment_method: 'MP01' },
				['name', 'grand_total', 'net_payable', 'document_type'],
			)
			const contanti =
				Math.round(incassate.reduce((t, f) => t + Number(f.net_payable || f.grand_total || 0), 0) * 100) / 100
			const conti = await s.banco.chiama('crm.api.oggi.get_cash_summary', { date: s.data(giorno), location: luogo })
			s.verifica(
				Math.abs(Number(conti?.expected_cash || 0) - contanti) < 0.005,
				'The cash expected is what the invoices collected in cash',
				`${conti?.expected_cash} vs ${contanti}`,
			)
			const page = await s.alLavoro(cassiere)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const scelta = page.getByRole('button', { name: /Tutte le sedi|Sede di/ }).first()
			if (await scelta.isVisible().catch(() => false)) {
				if (!(await scelta.innerText()).includes(sede)) {
					await premi(cassiere, scelta)
					await premi(cassiere, page.getByText(sede, { exact: true }).last())
				}
			}
			await premi(cassiere, page.getByRole('button', { name: /Chiusura di cassa/ }))
			const d = page.getByRole('dialog').last()
			await expect(d.getByText('Contanti attesi')).toBeVisible()
			await d.getByLabel('Contanti contati in cassa').fill(String(contanti).replace('.', ','))
			await premi(cassiere, d.getByRole('button', { name: /Chiudi la cassa|Chiudila di nuovo/ }))
			await esito(page, /cassa è chiusa/i)
			const chiusura = await s.banco.valore('CRM Cash Closing', { date: s.data(giorno), centre_location: luogo }, [
				'name',
				'centre_location',
				'expected_cash',
				'counted_cash',
				'difference',
			])
			s.nota(`Cassa: ${JSON.stringify(chiusura)}`)
			s.verifica(!!chiusura, 'The closing is kept', sede)
			s.verifica(
				Number(chiusura?.difference || 0) === 0,
				'The cash counted is the cash expected',
				JSON.stringify(chiusura),
			)
		},
		{ chiave: `${giorno}.cassa.${dove}` },
	)
}
