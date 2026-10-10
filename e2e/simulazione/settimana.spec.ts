// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { expect, test } from '@playwright/test'
import { lunedi } from './giorni/lunedi'
import { Settimana } from './lib/settimana'

const GIORNI: Array<[string, (s: Settimana) => Promise<void>]> = [
	['lunedi', lunedi],
]

test('una settimana del centro', async ({ browser }) => {
	const s = await Settimana.inizia(browser)
	const da = process.env.SIM_DA
	const fino = process.env.SIM_FINO
	let attivo = !da
	for (const [nome, gioca] of GIORNI) {
		if (nome === da) attivo = true
		if (!attivo) continue
		await test.step(nome, async () => {
			await gioca(s)
		})
		s.salva()
		if (nome === fino) break
	}
	s.salva()
	const falliti = s.rapporto.passi
		.filter((p) => p.esito === 'fallito')
		.map((p) => `${p.giorno} ${p.numero}. ${p.titolo}`)
	expect.soft(falliti, 'steps that failed').toEqual([])
	const gravi = s.rapporto.difetti.filter((d) => d.gravita === 'bloccante' || d.gravita === 'grave')
	expect
		.soft(
			gravi.map((d) => `${d.giorno} ${d.passo}: ${d.cosa} ${d.dettaglio || ''}`),
			'serious defects',
		)
		.toEqual([])
})
