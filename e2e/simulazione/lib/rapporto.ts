// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { RAPPORTO, SIMULAZIONE } from './inizio'

export type Gravita = 'bloccante' | 'grave' | 'minore' | 'estetico'

export type Difetto = {
	gravita: Gravita
	cosa: string
	dettaglio?: string
	dove: string
	passo: string
	giorno: string
	volte: number
	schermata?: string
}

export type Passo = {
	giorno: string
	numero: number
	ora: string
	titolo: string
	chi: string[]
	esito: 'ok' | 'difetti' | 'fallito' | 'saltato'
	errore?: string
	secondi: number
	schermate: string[]
	note: string[]
	difetti: number
}

const ORDINE: Gravita[] = ['bloccante', 'grave', 'minore', 'estetico']
const ICONA: Record<Passo['esito'], string> = { ok: '✅', difetti: '⚠️', fallito: '❌', saltato: '⏭️' }

function escape(testo: string): string {
	return testo.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!)
}

/** The week's report: the steps of each day, what went wrong, where to look. */
export class Rapporto {
	passi: Passo[] = []
	difetti: Difetto[] = []

	constructor(readonly cartella = RAPPORTO) {
		mkdirSync(cartella, { recursive: true })
		const salvato = path.join(cartella, 'passi.json')
		if (process.env.SIM_DA && existsSync(salvato)) {
			const dati = JSON.parse(readFileSync(salvato, 'utf8'))
			this.passi = dati.passi
			this.difetti = dati.difetti
		}
	}

	segna(difetto: Omit<Difetto, 'volte'>): boolean {
		const uguale = this.difetti.find(
			(d) => d.cosa === difetto.cosa && d.dettaglio === difetto.dettaglio && d.dove === difetto.dove,
		)
		if (uguale) {
			uguale.volte += 1
			return false
		}
		this.difetti.push({ ...difetto, volte: 1 })
		return true
	}

	scrivi(intestazione: Record<string, string>) {
		writeFileSync(
			path.join(this.cartella, 'passi.json'),
			JSON.stringify({ passi: this.passi, difetti: this.difetti }, null, 1),
		)
		const giorni = [...new Set(this.passi.map((p) => p.giorno))]
		for (const giorno of giorni) this.scriviGiorno(giorno)
		this.scriviRiepilogo(giorni, intestazione)
	}

	private scriviGiorno(giorno: string) {
		const passi = this.passi.filter((p) => p.giorno === giorno)
		const difetti = this.difetti.filter((d) => d.giorno === giorno)
		const md = [`# ${giorno}`, '']
		for (const p of passi) {
			md.push(`## ${ICONA[p.esito]} ${p.numero}. ${p.ora} · ${p.titolo}`)
			md.push(`Chi: ${p.chi.join(', ')} · ${p.secondi.toFixed(1)} s`)
			if (p.errore) md.push('', '```', p.errore, '```')
			for (const nota of p.note) md.push(`- ${nota}`)
			for (const d of difetti.filter((d) => d.passo === `${p.numero}. ${p.titolo}`)) {
				md.push(`- **${d.gravita}** · ${d.dove} · ${d.cosa}${d.dettaglio ? ` — ${d.dettaglio}` : ''}`)
			}
			for (const s of p.schermate) md.push(`![${s}](${s})`)
			md.push('')
		}
		writeFileSync(path.join(this.cartella, `${giorno}.md`), md.join('\n'))

		const html = [
			`<!doctype html><html lang="it"><head><meta charset="utf-8"><title>${escape(giorno)}</title>`,
			'<style>body{font-family:system-ui;margin:24px;max-width:1200px}img{max-width:280px;max-height:420px;border:1px solid #ccc;margin:4px;vertical-align:top}',
			'.ok{color:#1b7f3a}.fallito{color:#b3261e}.difetti{color:#a15c00}pre{white-space:pre-wrap;background:#f6f6f6;padding:8px}</style></head><body>',
			`<h1>${escape(giorno)}</h1>`,
		]
		for (const p of passi) {
			html.push(`<h2 class="${p.esito}">${ICONA[p.esito]} ${p.numero}. ${escape(p.ora)} · ${escape(p.titolo)}</h2>`)
			html.push(`<p>Chi: ${escape(p.chi.join(', '))} · ${p.secondi.toFixed(1)} s</p>`)
			if (p.errore) html.push(`<pre>${escape(p.errore)}</pre>`)
			if (p.note.length) html.push(`<ul>${p.note.map((n) => `<li>${escape(n)}</li>`).join('')}</ul>`)
			const propri = difetti.filter((d) => d.passo === `${p.numero}. ${p.titolo}`)
			if (propri.length)
				html.push(
					`<ul>${propri.map((d) => `<li><b>${d.gravita}</b> · ${escape(d.dove)} · ${escape(d.cosa)}${d.dettaglio ? ` — ${escape(d.dettaglio)}` : ''}</li>`).join('')}</ul>`,
				)
			html.push(p.schermate.map((s) => `<a href="${s}"><img src="${s}" alt="${escape(s)}"></a>`).join(''))
		}
		html.push('</body></html>')
		writeFileSync(path.join(this.cartella, `${giorno}.html`), html.join('\n'))
	}

	private scriviRiepilogo(giorni: string[], intestazione: Record<string, string>) {
		const md = ['# Simulazione di una settimana del centro', '']
		for (const [chiave, valore] of Object.entries(intestazione)) md.push(`- **${chiave}**: ${valore}`)
		md.push('', '## I giorni', '', '| Giorno | Passi | ✅ | ⚠️ | ❌ | ⏭️ |', '|---|---|---|---|---|---|')
		for (const giorno of giorni) {
			const p = this.passi.filter((x) => x.giorno === giorno)
			const n = (e: Passo['esito']) => p.filter((x) => x.esito === e).length
			md.push(
				`| [${giorno}](${giorno}.html) | ${p.length} | ${n('ok')} | ${n('difetti')} | ${n('fallito')} | ${n('saltato')} |`,
			)
		}
		md.push('', '## Difetti trovati in questa corsa', '')
		const ordinati = [...this.difetti].sort((a, b) => ORDINE.indexOf(a.gravita) - ORDINE.indexOf(b.gravita))
		if (!ordinati.length) md.push('Nessuno.')
		for (const d of ordinati) {
			md.push(
				`- **${d.gravita}** · ${d.giorno} · ${d.passo} · ${d.dove} · ${d.cosa}${d.dettaglio ? ` — ${d.dettaglio}` : ''}${d.volte > 1 ? ` (×${d.volte})` : ''}`,
			)
		}
		const falliti = this.passi.filter((p) => p.esito === 'fallito')
		if (falliti.length) {
			md.push('', '## Passi falliti', '')
			for (const p of falliti) md.push(`- ${p.giorno} · ${p.numero}. ${p.titolo}: ${(p.errore || '').split('\n')[0]}`)
		}
		const noti = path.join(SIMULAZIONE, 'DIFETTI.md')
		if (existsSync(noti)) md.push('', readFileSync(noti, 'utf8').replace(/^# /m, '## '))
		writeFileSync(path.join(this.cartella, 'RIEPILOGO.md'), md.join('\n'))
	}
}
