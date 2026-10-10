// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { defineConfig } from '@playwright/test'

/**
 * The simulation of a real centre's week (e2e/simulazione/README.md): one test that
 * plays Monday to Saturday through the real screens, its personas each in their own
 * browser and device. Its report is in e2e/simulazione/rapporto (not versioned).
 *
 * SIM_BASE      the test bench (default http://collaudo.localhost:8000)
 * SIM_FINTI     the fake services (default http://127.0.0.1:8791), started if down
 * SIM_CHROMIUM  a Chromium to use instead of Playwright's own
 * SIM_DA        resume the week from a day (lunedi … sabato), its state kept
 */
export default defineConfig({
	testDir: '.',
	testMatch: /settimana\.spec\.ts/,
	fullyParallel: false,
	workers: 1,
	retries: 0,
	// a week is long: each day has its own steps and its own deadline
	timeout: 4 * 60 * 60 * 1000,
	reporter: [['list'], ['html', { outputFolder: 'rapporto/playwright', open: 'never' }]],
	outputDir: 'rapporto/risultati',
	globalSetup: './lib/inizio.ts',
	expect: { timeout: 15000 },
	use: {
		baseURL: process.env.SIM_BASE || 'http://collaudo.localhost:8000',
		actionTimeout: 20000,
		navigationTimeout: 45000,
		trace: 'retain-on-failure',
		launchOptions: process.env.SIM_CHROMIUM ? { executablePath: process.env.SIM_CHROMIUM } : {},
	},
})
