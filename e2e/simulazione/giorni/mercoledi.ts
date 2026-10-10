// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect, type Page } from '@playwright/test'
import { entraNellArea, firmaSulPad, linkDellArea } from '../lib/area'
import { collegamento, pagaSuStripe, premi, prenotaOnline } from '../lib/azioni'
import { firmaLaVisita, nuovaVisita, scrivi } from '../lib/clinica'
import { FINTI } from '../lib/banco'
import { emettiLaBozza, fatturaDi, esito, nuovoAppuntamento, persona } from '../lib/scrivania'
import type { Persona } from '../lib/persone'
import type { Settimana } from '../lib/settimana'
import { laCassa } from './lunedi'
import { permessi } from './permessi'

/** Wednesday: Anna's cycle of sessions; Giulia's visit and its balance; the
 * dentist's first visit to Roberto, his care plan in instalments, signed in the
 * area; Paolo and Chiara buy the monthly subscription in the area; Tommaso at the
 * dentist with his mother; Anna's exercises at home, ticked in the evening; the
 * Wednesday class on subscriptions. */
export async function mercoledi(s: Settimana) {
	await s.giornata('mercoledi', '07:30')
	await ilCicloDiAnna(s)
	await robertoDalDentista(s)
	await laVisitaDiGiulia(s)
	await robertoPaga(s)
	await giuliaPaga(s)
	await ilPreventivoFirmato(s)
	await gliAbbonamenti(s)
	await leBozzeDegliAbbonamenti(s)
	await laLezioneInAbbonamento(s)
	await tommasoDalDentista(s)
	await gliEserciziDiAnna(s)
	await laLezioneDiStasera(s)
	await laCassa(s, 'mercoledi', 'segreteria', 'milano')
	await permessi(s)
	await annaSpunta(s)
}

/** The desk sells Anna the ten sessions the assessment planned, and books the
 * next two: they join the cycle by themselves. */
async function ilCicloDiAnna(s: Settimana) {
	await s.alle('08:40')
	const seg = s.p('segreteria')
	await s.passo(
		'La segreteria vende ad Anna il ciclo di fisioterapia e prenota le prossime sedute',
		seg,
		async () => {
			const page = await persona(s, seg, s.stato.anna.persona, 'subscriptions')
			await premi(seg, page.getByRole('button', { name: 'Vendi un ciclo' }).first())
			const d = page.getByRole('dialog').last()
			await premi(seg, d.getByLabel('Servizio'))
			await premi(seg, page.getByRole('option', { name: new RegExp(`^${s.copione.services.fisioterapia}`) }).first())
			await d.getByLabel('Sedute').fill('10')
			await premi(seg, d.getByRole('button', { name: 'Vendi il ciclo' }))
			await esito(page)
			await page.keyboard.press('Escape').catch(() => {})
			const ciclo = await s.banco.valore('CRM Session Cycle', { lead: s.stato.anna.persona }, ['name', 'sessions'])
			s.verifica(!!ciclo, 'The cycle is sold', JSON.stringify(ciclo))
			s.stato.anna.ciclo = ciclo?.name
			for (const [giorno, ora] of [
				['giovedi', '17:00'],
				['sabato', '10:00'],
			]) {
				const nome = await nuovoAppuntamento(s, seg, {
					giorno: s.data(giorno),
					ora,
					servizio: s.copione.services.fisioterapia,
					persone: [{ nome: s.p('anna').nome, esistente: true }],
				})
				s.stato.anna[`seduta_${giorno}`] = nome
				const nelCiclo = await s.banco.valore('CRM Appointment', nome, 'session_cycle')
				s.verifica(nelCiclo === ciclo?.name, 'The session joins the cycle by itself', `${giorno}: ${nelCiclo}`)
			}
		},
		{ chiave: 'anna.ciclo', dopo: ['anna.valutazione'] },
	)
}

/** The dentist's first visit to Roberto: the visit on the sheet, then the care
 * plan as a quote in instalments, proposed and sent to sign. */
async function robertoDalDentista(s: Settimana) {
	await s.alle('09:25')
	const seg = s.p('segreteria')
	await s.passo(
		'Roberto arriva per la prima visita dal dentista',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const riga = page
				.getByRole('link', { name: s.p('roberto').nome })
				.first()
				.locator('xpath=ancestor::div[contains(@class,"py-2")][1]')
			await premi(seg, riga.getByRole('button', { name: 'Accogli' }))
			await expect(riga.getByRole('button', { name: 'Presente' })).toBeVisible()
		},
		{ chiave: 'roberto.arrivato', dopo: ['roberto.mercoledi'] },
	)
	await s.alle('09:35')
	const dentista = s.p('dentista')
	await s.passo(
		'La dentista scrive la prima visita di Roberto e la firma',
		dentista,
		async () => {
			const page = await persona(s, dentista, s.stato.roberto.persona, 'clinic')
			await nuovaVisita(dentista, page, /^Prima visita odontoiatrica/)
			await scrivi(page, 'Cosa porta il paziente', 'Fastidio al freddo in basso a sinistra da un mese.')
			await scrivi(page, 'Diagnosi', 'Carie occlusale su 36; 46 da devitalizzare; tartaro diffuso.')
			await firmaLaVisita(dentista, page)
		},
		{ chiave: 'roberto.visita', dopo: ['roberto.arrivato'] },
	)
	await s.passo(
		'La dentista scrive il piano di cura: un preventivo a rate, proposto e mandato da firmare',
		dentista,
		async () => {
			const page = await persona(s, dentista, s.stato.roberto.persona, 'quotes')
			await premi(dentista, page.getByRole('button', { name: 'Nuovo preventivo' }).first())
			const d = page.getByRole('dialog').last()
			await d.getByLabel('Titolo').fill('Piano di cura')
			const righe: Array<[string, string, string]> = [
				[s.copione.services.otturazione, '36', 'OM'],
				[s.copione.services.devitalizzazione, '46', ''],
				[s.copione.services.igiene, '', ''],
			]
			for (const [i, [servizio, dente, superfici]] of righe.entries()) {
				if (i > 0 || !(await d.getByRole('combobox', { name: 'Servizio' }).count()))
					await premi(dentista, d.getByRole('button', { name: 'Aggiungi un servizio' }))
				const servizi = d.getByRole('combobox', { name: 'Servizio' })
				await premi(dentista, servizi.nth(i))
				await premi(dentista, page.getByRole('option', { name: new RegExp(`^${servizio}`) }).first())
				if (dente) await d.getByRole('textbox', { name: 'Dente' }).nth(i).fill(dente)
				if (superfici) await d.getByRole('textbox', { name: 'Superfici' }).nth(i).fill(superfici)
			}
			await premi(dentista, d.getByRole('radio', { name: /rate/i }))
			await d.getByLabel(/^Acconto, /).fill('70')
			await d.getByLabel('Rate', { exact: true }).fill('4')
			await s.foto(dentista, 'preventivo')
			await premi(dentista, d.getByRole('button', { name: 'Proponi come preventivo' }))
			await esito(page)
			const preventivo = await s.attendi(
				() =>
					s.banco.valore('CRM Quote', { lead: s.stato.roberto.persona }, ['name', 'status', 'total_net', 'payment']),
				(v) => v?.status === 'Proposed',
			)
			s.nota(`Preventivo: ${JSON.stringify(preventivo)}`)
			s.verifica(preventivo?.status === 'Proposed', 'The quote is proposed', JSON.stringify(preventivo))
			s.verifica(Number(preventivo?.total_net) === 470, 'The quote adds up to its rows', String(preventivo?.total_net))
			s.stato.roberto.preventivo = preventivo?.name
			const rate = await s.banco.lista('CRM Quote Instalment', { parent: preventivo?.name }, ['kind', 'amount'], {
				genitore: 'CRM Quote',
			})
			s.verifica(rate.length === 5, 'A deposit and four instalments', JSON.stringify(rate))
			s.verifica(
				Math.round(rate.reduce((t, r) => t + Number(r.amount), 0) * 100) === 47000,
				'The instalments add up to the quote, to the cent',
				JSON.stringify(rate),
			)
			const manda = page.getByRole('dialog').last().getByRole('button', { name: 'Manda da firmare' })
			await premi(dentista, manda)
			const conferma = page.getByRole('dialog').last()
			const invia = conferma.getByRole('button', { name: /^Manda/ }).last()
			if (await invia.isVisible().catch(() => false)) await premi(dentista, invia)
			await esito(page)
			s.stato.roberto.mandato = s.banco.ora
		},
		{ chiave: 'roberto.preventivo', dopo: ['roberto.visita'] },
	)
}

async function robertoPaga(s: Settimana) {
	await s.alle('10:10')
	const seg = s.p('segreteria')
	await s.passo(
		'Roberto paga la prima visita al banco, con la carta',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const fattura = fatturaDi(page, s.p('roberto').nome)
			await expect(fattura).toBeVisible({ timeout: 30000 })
			await premi(seg, fattura)
			await emettiLaBozza(s, seg, page, 'roberto', { pagamento: /Carta/ })
		},
		{ chiave: 'roberto.fattura', dopo: ['roberto.visita'] },
	)
}

async function laVisitaDiGiulia(s: Settimana) {
	await s.alle('09:55')
	const seg = s.p('segreteria')
	await s.passo(
		'Giulia arriva per la visita medica',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const riga = page
				.getByRole('link', { name: s.p('giulia').nome })
				.first()
				.locator('xpath=ancestor::div[contains(@class,"py-2")][1]')
			await premi(seg, riga.getByRole('button', { name: 'Accogli' }))
			await expect(riga.getByRole('button', { name: 'Presente' })).toBeVisible()
		},
		{ chiave: 'giulia.arrivata', dopo: ['giulia.prenota'] },
	)
	await s.alle('10:05')
	const medico = s.p('medico')
	await s.passo(
		'Il medico scrive la visita di Giulia sul tablet e la firma',
		medico,
		async () => {
			const page = await persona(s, medico, s.stato.giulia.persona, 'clinic')
			await nuovaVisita(medico, page, /^Visita libera/)
			await page
				.getByLabel('Cosa è successo')
				.fill(
					'Cefalea tensiva da due settimane. Esame neurologico nella norma. Consigli posturali, controllo tra un mese.',
				)
			await firmaLaVisita(medico, page)
		},
		{ chiave: 'giulia.visita', dopo: ['giulia.arrivata'] },
	)
}

async function giuliaPaga(s: Settimana) {
	await s.alle('10:40')
	const seg = s.p('segreteria')
	await s.passo(
		'Giulia paga il saldo in contanti; prenota online il controllo di venerdì',
		[seg, s.p('giulia')],
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const fattura = fatturaDi(page, s.p('giulia').nome)
			await expect(fattura).toBeVisible({ timeout: 30000 })
			await premi(seg, fattura)
			await emettiLaBozza(s, seg, page, 'giulia', { pagamento: /Contanti/ })
			const saldo = await s.banco.valore('CRM Invoice', { appointment: s.stato.giulia.appuntamento, docstatus: 1 }, [
				'grand_total',
			])
			s.verifica(
				Number(saldo?.grand_total) === 90,
				'The balance is the price less the deposit',
				String(saldo?.grand_total),
			)
			// on the way home Giulia books the check-up the doctor asked for
			const giulia = s.p('giulia')
			const token = await prenotaOnline(s, giulia, {
				sede: 'Sede di Milano',
				servizio: s.copione.services.visita,
				giorno: s.data('venerdi'),
				ora: '11:30',
				nome: giulia.nome,
				email: giulia.email,
				telefono: s.persona('giulia').mobile,
			})
			const nome = await s.banco.valore('CRM Appointment', { booking_token: token }, 'name').catch(() => null)
			s.stato.giulia.controllo =
				nome ||
				(await s.banco.lista('CRM Appointment', { starts_on: ['like', `${s.data('venerdi')} 11:30%`] }, ['name']))[0]
					?.name
			s.verifica(!!s.stato.giulia.controllo, 'The check-up is booked', token)
		},
		{ chiave: 'giulia.controllo', dopo: ['giulia.visita'] },
	)
}

/** Roberto reads the care plan in his area, accepts and signs it with his finger. */
async function ilPreventivoFirmato(s: Settimana) {
	await s.alle('12:00')
	const roberto = s.p('roberto')
	await s.passo(
		'Roberto legge il piano di cura nell’area, lo accetta e lo firma col dito',
		roberto,
		async () => {
			// every email of the area says only that there is news in it (doc 41)
			const mail = await s.banco.attendiPosta(roberto.email, /area|preventiv|firma/i, {
				dopo: s.stato.roberto.mandato || s.data('mercoledi'),
			})
			s.nota(`Email: «${mail.subject}»`)
			const page = await entraNellArea(s, roberto, { link: linkDellArea(mail.links) })
			await page.goto('/area/plans', { waitUntil: 'domcontentloaded' })
			const accetta = page.getByRole('button', { name: 'Accetta e firma' }).first()
			await expect(accetta).toBeVisible({ timeout: 30000 })
			await s.dito(roberto, accetta)
			await premi(roberto, accetta)
			const d = page.getByRole('dialog').last()
			await firmaSulPad(page, d.locator('canvas').first())
			await premi(roberto, d.getByRole('button', { name: 'Firma e accetta' }))
			// a code again, if the area asks it to say the signature is his
			const codice = page.getByLabel('Il codice')
			if (await codice.isVisible({ timeout: 4000 }).catch(() => false)) {
				const posta = await s.banco.attendiPosta(roberto.email, /codice/i, { dopo: s.banco.ora })
				await codice.fill(/\b(\d{6})\b/.exec(`${posta.subject} ${posta.text}`)?.[1] || '')
				await premi(roberto, page.getByRole('button', { name: 'Entra', exact: true }))
			}
			const stato = await s.attendi(
				() => s.banco.valore('CRM Quote', s.stato.roberto.preventivo, ['status', 'signed_on']),
				(v) => v?.status === 'Accepted',
			)
			s.verifica(stato?.status === 'Accepted', 'The care plan is accepted', JSON.stringify(stato))
			s.verifica(!!stato?.signed_on, 'Signed in the area', JSON.stringify(stato))
			await expect(page.getByText(/Accettato e firmato/).first()).toBeVisible()
		},
		{ chiave: 'roberto.firmato', dopo: ['roberto.preventivo'] },
	)
}

/** Paolo and Chiara buy the monthly subscription in their area, on Stripe's page;
 * Chiara's card is one that pays today and is refused next month. */
async function gliAbbonamenti(s: Settimana) {
	await s.alle('12:30')
	for (const [chiave, carta] of [
		['paolo', '4242424242424242'],
		['chiara', '4000000000000341'],
	] as const) {
		const chi = s.p(chiave)
		await s.passo(
			`${chi.nome} compra l’abbonamento mensile nell’area`,
			chi,
			async () => {
				const invito = await s.banco.attendiPosta(chi.email, /area/i, { dopo: s.data('lunedi') })
				const page = await entraNellArea(s, chi, { link: linkDellArea(invito.links) })
				await page.goto('/area/appointments', { waitUntil: 'domcontentloaded' })
				const carta_ = page.locator('article', { hasText: s.copione.subscriptions.mensile }).first()
				await expect(carta_).toBeVisible({ timeout: 30000 })
				await premi(chi, carta_.getByRole('button', { name: 'Acquista' }))
				// the sheet asks the codice fiscale where the billing details lack it
				const codice = page
					.getByRole('dialog')
					.last()
					.getByRole('textbox', { name: /^Codice fiscale/ })
				if (await codice.count()) {
					await codice.fill(s.persona(chiave).fiscal_code)
					s.nota('Il foglio d’acquisto chiede il codice fiscale')
				}
				const vai = page.getByRole('dialog').last().getByRole('button', { name: 'Vai al pagamento' })
				await s.dito(chi, vai)
				await premi(chi, vai)
				await page.waitForURL((u) => u.toString().startsWith(`${FINTI}/checkout/`), { timeout: 45000 })
				await pagaSuStripe(s, chi, page, [carta])
				await page.waitForURL(/\/area/, { timeout: 60000 })
				const abbonamento = await s.attendi(
					() =>
						s.banco.valore('CRM Subscription', { lead: s.stato[chiave].persona }, [
							'name',
							'status',
							'card_last4',
							'card_brand',
						]),
					(v) => !!v?.name,
					30,
				)
				s.nota(`Abbonamento: ${JSON.stringify(abbonamento)}`)
				s.verifica(!!abbonamento?.name, 'The subscription is sold', chiave)
				s.stato[chiave].abbonamento = abbonamento?.name
				const fattura = await s.attendi(
					() =>
						s.banco.valore(
							'CRM Invoice',
							{ party: s.stato[chiave].persona, payment_method: 'MP08', docstatus: ['<', 2] },
							['name', 'grand_total', 'collected_on', 'docstatus'],
						),
					(v) => !!v?.name,
				)
				s.verifica(!!fattura?.name, 'The first instalment is invoiced', JSON.stringify(fattura))
				if (fattura?.docstatus === 0) {
					// what the area does not ask (an address, for an electronic invoice): the
					// invoice waits as a draft, and the managers are told
					s.nota(`La fattura della prima rata è una bozza (${fattura.name})`)
					s.stato[chiave].bozza = fattura.name
				} else {
					s.verifica(!!fattura?.collected_on, 'Paid online: collected', JSON.stringify(fattura))
				}
				await expect(page.getByText(s.copione.subscriptions.mensile).first()).toBeVisible()
			},
			{ chiave: `${chiave}.abbonamento`, dopo: [`${chiave}.area`] },
		)
	}
}

/** What the area's purchases left as drafts: the manager asks the codice fiscale
 * and issues them, the day the money arrived. */
async function leBozzeDegliAbbonamenti(s: Settimana) {
	const bozze = ['paolo', 'chiara'].filter((k) => s.stato[k]?.bozza)
	if (!bozze.length) return
	await s.alle('13:00')
	const r = s.p('responsabile')
	await s.passo(
		'La responsabile completa la fattura della prima rata rimasta in bozza e la emette',
		r,
		async () => {
			const page = await s.alLavoro(r)
			for (const chiave of bozze) {
				await page.goto(`/crm/fatture?open=${s.stato[chiave].bozza}`, { waitUntil: 'domcontentloaded' })
				await emettiLaBozza(s, r, page, chiave)
				const dopo = await s.banco.valore('CRM Invoice', s.stato[chiave].bozza, [
					'docstatus',
					'collected_on',
					'posting_date',
				])
				s.verifica(dopo?.docstatus === 1 && !!dopo?.collected_on, 'Issued and collected', JSON.stringify(dopo))
				s.verifica(dopo?.posting_date === s.data('mercoledi'), 'Dated the day the money arrived', dopo?.posting_date)
			}
		},
		{ chiave: 'abbonamenti.bozze' },
	)
}

/** Tommaso at the dentist with his mother: the visit, the invoice made out to her,
 * paid by bank transfer (still to collect). */
async function tommasoDalDentista(s: Settimana) {
	await s.alle('14:55')
	const seg = s.p('segreteria')
	await s.passo(
		'Elena porta Tommaso dal dentista: la segreteria lo accoglie',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const riga = page
				.getByRole('link', { name: s.p('tommaso').nome })
				.first()
				.locator('xpath=ancestor::div[contains(@class,"py-2")][1]')
			await premi(seg, riga.getByRole('button', { name: 'Accogli' }))
			await expect(riga.getByRole('button', { name: 'Presente' })).toBeVisible()
		},
		{ chiave: 'tommaso.arrivato', dopo: ['elena.prenota'] },
	)
	await s.alle('15:05')
	const dentista = s.p('dentista')
	await s.passo(
		'La dentista scrive la visita di Tommaso',
		dentista,
		async () => {
			const page = await persona(s, dentista, s.stato.tommaso.persona, 'clinic')
			await nuovaVisita(dentista, page, /^Prima visita odontoiatrica/)
			await scrivi(page, 'Cosa porta il paziente', 'Controllo: la mamma ha visto una macchia scura su un dente.')
			await scrivi(page, 'Diagnosi', 'Solco pigmentato su 46, nessuna carie. Sigillatura consigliata.')
			await firmaLaVisita(dentista, page)
		},
		{ chiave: 'tommaso.visita', dopo: ['tommaso.arrivato'] },
	)
	await s.alle('15:40')
	await s.passo(
		'La fattura della visita di Tommaso, col suo codice fiscale; la mamma paga con un bonifico',
		seg,
		async () => {
			const page = await s.alLavoro(seg)
			await page.goto('/crm/accoglienza', { waitUntil: 'domcontentloaded' })
			const fattura = fatturaDi(page, s.p('tommaso').nome)
			await expect(fattura).toBeVisible({ timeout: 30000 })
			await premi(seg, fattura)
			// a child booked by his mother is the invoice's client (his codice fiscale
			// for the Sistema TS); she pays it, by bank transfer
			await emettiLaBozza(s, seg, page, 'tommaso', { pagamento: /Bonifico/ })
			const emessa = await s.banco.valore('CRM Invoice', { appointment: s.stato.tommaso.appuntamento, docstatus: 1 }, [
				'name',
				'billing_name',
				'causale',
				'collected_on',
				'fiscal_code',
			])
			s.nota(`Fattura: ${JSON.stringify(emessa)}`)
			s.verifica(
				emessa?.fiscal_code === s.persona('tommaso').fiscal_code,
				'With the child’s codice fiscale',
				emessa?.fiscal_code,
			)
			s.verifica(!emessa?.collected_on, 'A bank transfer is still to collect', emessa?.collected_on)
			s.stato.tommaso.fattura = emessa?.name
			// the news of the invoice reaches whoever enters his area: his mother
			const avviso = await s.banco
				.attendiPosta(s.p('elena').email, /area/i, { dopo: s.banco.ora, secondi: 15 })
				.catch(() => null)
			s.verifica(!!avviso, 'His mother is told there is news in the area', s.p('elena').email, 'minore')
		},
		{ chiave: 'tommaso.fattura', dopo: ['tommaso.visita'] },
	)
}

/** The physiotherapist writes Anna's exercises at home from the library and
 * publishes them; in the evening Anna ticks one in her area and says how hard. */
async function gliEserciziDiAnna(s: Settimana) {
	await s.alle('16:30')
	const fisio = s.p('fisioterapista')
	await s.passo(
		'La fisioterapista scrive gli esercizi a casa di Anna dalla libreria e li pubblica',
		fisio,
		async () => {
			const page = await persona(s, fisio, s.stato.anna.persona, 'plans')
			await premi(fisio, page.getByRole('button', { name: /^Esercizi a casa/ }).first())
			const d = page.getByRole('dialog').last()
			await expect(d.getByLabel('Titolo')).toBeVisible()
			await d.getByLabel('Titolo').fill('Esercizi per la schiena')
			await premi(fisio, d.getByRole('button', { name: 'Esercizi', exact: true }).first())
			const libreria = page.getByRole('dialog').last()
			for (const cerca of ['ponte', 'plank']) {
				await libreria.getByLabel('Cerca', { exact: true }).first().fill(cerca)
				await page.waitForTimeout(800)
				const primo = libreria
					.locator('li button')
					.filter({ hasNotText: /Come si fa/ })
					.first()
				const nessuno = libreria.getByText('Nessun risultato.')
				await expect(primo.or(nessuno).first()).toBeVisible({ timeout: 20000 })
				if (await nessuno.isVisible()) {
					s.nota(`«${cerca}»: nessun esercizio nella libreria`)
					continue
				}
				await premi(fisio, primo)
			}
			await premi(fisio, libreria.getByRole('button', { name: /^Aggiungi \d/ }))
			await s.foto(fisio, 'piano')
			await premi(fisio, page.getByRole('dialog').last().getByRole('button', { name: 'Pubblica' }))
			await esito(page, /Pubblicat/)
			// health data: the agency reads none of it, its author does
			const piani = await page.request
				.get('/api/method/frappe.client.get_list', {
					params: {
						doctype: 'CRM Personal Plan',
						filters: JSON.stringify({ lead: s.stato.anna.persona }),
						fields: JSON.stringify(['name', 'status']),
					},
				})
				.then((x) => x.json())
				.then((x) => x.message || [])
				.catch(() => [])
			const piano = piani[0]
			s.verifica(piano?.status === 'Published', 'The plan is published', JSON.stringify(piani))
			const all_agenzia = await s.banco.conta('CRM Personal Plan', { lead: s.stato.anna.persona })
			s.verifica(all_agenzia === 0, 'The agency reads no health plan', String(all_agenzia))
			s.stato.anna.piano = piano?.name
		},
		{ chiave: 'anna.esercizi', dopo: ['anna.valutazione'] },
	)
}

async function annaSpunta(s: Settimana) {
	await s.alle('20:30')
	const anna = s.p('anna')
	await s.passo(
		'La sera Anna fa gli esercizi, li spunta nell’area e dice quanto è stato faticoso',
		anna,
		async () => {
			const page = await entraNellArea(s, anna)
			await page.goto('/area/plans', { waitUntil: 'domcontentloaded' })
			await premi(anna, page.getByText('Esercizi per la schiena').first())
			const fatto = page.getByRole('button', { name: 'Fatto', exact: true }).first()
			await expect(fatto).toBeVisible({ timeout: 30000 })
			await s.dito(anna, fatto)
			await premi(anna, fatto)
			const sette = page.getByRole('button', { name: '7 su 10' }).first()
			await expect(sette).toBeVisible()
			await premi(anna, sette)
			await expect(sette).toHaveAttribute('aria-pressed', 'true')
			// kept: the page again, as she opens it tomorrow
			await page.waitForTimeout(1500)
			await page.reload({ waitUntil: 'domcontentloaded' })
			await expect(page.getByRole('button', { name: 'Fatto', exact: true }).first()).toHaveAttribute(
				'aria-pressed',
				'true',
				{ timeout: 30000 },
			)
			await expect(page.getByRole('button', { name: '7 su 10' }).first()).toHaveAttribute('aria-pressed', 'true')
			// and her physiotherapist reads it beside the plan («Effort or pain 7/10»)
			const fisio = await persona(s, s.p('fisioterapista'), s.stato.anna.persona, 'plans')
			await expect(fisio.getByText(/7\/10/).first()).toBeVisible({ timeout: 30000 })
		},
		{ chiave: 'anna.spunta', dopo: ['anna.esercizi'] },
	)
}

/** The Wednesday class: Paolo and Chiara book it from /prenota with their
 * subscription; the physiotherapist says they came; nothing to invoice. */
async function laLezioneInAbbonamento(s: Settimana) {
	await s.alle('13:30')
	for (const chiave of ['paolo', 'chiara']) {
		const chi = s.p(chiave)
		await s.passo(
			`${chi.nome} prenota online la lezione di stasera, compresa nell’abbonamento`,
			chi,
			async () => {
				await prenotaOnline(s, chi, {
					sede: 'Sede di Milano',
					servizio: s.copione.services.pilates,
					giorno: s.data('mercoledi'),
					ora: '18:00',
					nome: chi.nome,
					email: chi.email,
					telefono: s.persona(chiave).mobile,
				})
				const lezione = (
					await s.banco.lista(
						'CRM Appointment',
						{ service: ['is', 'set'], starts_on: ['like', `${s.data('mercoledi')} 18:00%`] },
						['name'],
					)
				)[0]?.name
				s.stato.pilates.mercoledi = lezione
				const posto = await s.banco.valore(
					'CRM Appointment Participant',
					{ parent: lezione, party: s.stato[chiave].persona },
					['subscription', 'amount'],
					'CRM Appointment',
				)
				s.verifica(
					!!posto?.subscription && Number(posto.amount) === 0,
					'The place uses an entry of the subscription',
					JSON.stringify(posto),
				)
			},
			{ chiave: `${chiave}.lezione.mercoledi`, dopo: [`${chiave}.abbonamento`] },
		)
	}
}

/** After the class the physiotherapist says who came: their places are paid with
 * the subscriptions, nothing is left to invoice. */
async function laLezioneDiStasera(s: Settimana) {
	await s.alle('19:05')
	const fisio = s.p('fisioterapista')
	const venuti = ['paolo', 'chiara'].filter((k) => s.stato[k]?.abbonamento)
	await s.passo(
		'Dopo la lezione la fisioterapista segna chi è venuto: niente da fatturare, c’è l’abbonamento',
		fisio,
		async () => {
			const page = await s.alLavoro(fisio)
			await page.goto(`/crm/calendar?date=${s.data('mercoledi')}`, { waitUntil: 'domcontentloaded' })
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
			const daFare = await s.banco.chiama('crm.invoicing.api.appointments_to_invoice', {}, 'GET')
			s.verifica(
				!(daFare || []).some((a: any) => a.name === s.stato.pilates.mercoledi),
				'A class on subscriptions is not to invoice',
				JSON.stringify((daFare || []).map((a: any) => a.name)),
			)
			const ingressi = await s.banco.lista(
				'CRM Appointment Participant',
				{ parent: s.stato.pilates.mercoledi, subscription: ['is', 'set'] },
				['party', 'subscription', 'status'],
				{ genitore: 'CRM Appointment' },
			)
			s.verifica(ingressi.length === venuti.length, 'Each place uses its subscription', JSON.stringify(ingressi))
		},
		{ chiave: 'lezione.mercoledi', dopo: ['paolo.lezione.mercoledi'] },
	)
}

export type { Page, Persona }
export { collegamento }
