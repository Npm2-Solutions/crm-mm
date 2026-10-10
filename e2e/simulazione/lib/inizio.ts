// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { spawn } from 'node:child_process'
import { mkdirSync, openSync, readdirSync, rmSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const QUI = path.dirname(fileURLToPath(import.meta.url))
export const SIMULAZIONE = path.resolve(QUI, '..')
export const RAPPORTO = path.join(SIMULAZIONE, 'rapporto')

async function risponde(indirizzo: string): Promise<boolean> {
	try {
		const risposta = await fetch(indirizzo, { signal: AbortSignal.timeout(3000) })
		return risposta.ok
	} catch {
		return false
	}
}

/** Before the week: the bench answers, and the fake services run (started here if
 * they do not, left running after). */
export default async function inizio(): Promise<void> {
	mkdirSync(RAPPORTO, { recursive: true })
	// a new week starts a new report: the days and their screenshots of before go
	// (the fakes' state stays, and so does a week being resumed)
	if (!process.env.SIM_DA) {
		for (const voce of readdirSync(RAPPORTO)) {
			if (
				/^(lunedi|martedi|mercoledi|giovedi|venerdi|sabato|un_mese_dopo|tre_giorni_dopo)(\.md|\.html)?$|^passi\.json$|^stato\.json$/.test(
					voce,
				)
			)
				rmSync(path.join(RAPPORTO, voce), { recursive: true, force: true })
		}
	}
	const base = process.env.SIM_BASE || 'http://collaudo.localhost:8000'
	if (!(await risponde(`${base}/api/method/ping`))) {
		throw new Error(`The test bench does not answer at ${base}`)
	}
	const finti = process.env.SIM_FINTI || 'http://127.0.0.1:8791'
	if (await risponde(`${finti}/`)) return
	const porta = new URL(finti).port || '8791'
	const registro = openSync(path.join(RAPPORTO, 'finti.log'), 'a')
	const processo = spawn(
		'python3',
		[path.join(SIMULAZIONE, 'finti', 'server.py'), '--porta', porta, '--stato', path.join(RAPPORTO, 'finti.json')],
		{ detached: true, stdio: ['ignore', registro, registro] },
	)
	processo.unref()
	for (let i = 0; i < 30; i++) {
		if (await risponde(`${finti}/`)) return
		await new Promise((fatto) => setTimeout(fatto, 300))
	}
	throw new Error(`The fake services did not start at ${finti}`)
}
