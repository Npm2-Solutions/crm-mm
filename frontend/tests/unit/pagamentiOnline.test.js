// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// Online payments' words and checks: the same rules as crm/pagamenti/regole.py.
import { expect, test } from 'vitest'
import {
  modalita,
  modoInParole,
  oreValide,
  problemaDellaChiave,
  righeDeiPagamenti,
  righeDelCollegamento,
} from '@/utils/pagamentiOnline'

const t = (testo, valori = []) =>
  testo.replace(/\{(\d)\}/g, (_, i) => String(valori[i]))

test('the key: its mode, and what is wrong before Stripe is asked', () => {
  expect(modalita('sk_test_51abc')).toBe('test')
  expect(modalita(' rk_live_51abc ')).toBe('live')
  expect(modalita('pk_test_51abc')).toBe('')
  expect(problemaDellaChiave('', t)).toMatch(/Paste/)
  expect(problemaDellaChiave('pk_live_' + 'x'.repeat(30), t)).toMatch(
    /publishable/,
  )
  expect(problemaDellaChiave('hello', t)).toMatch(/not a Stripe/)
  expect(problemaDellaChiave('sk_test_' + 'x'.repeat(30), t)).toBe('')
})

test('the mode in words', () => {
  expect(modoInParole('test', t).label).toBe('Test mode')
  expect(modoInParole('test', t).riga).toMatch(/4242/)
  expect(modoInParole('live', t).theme).toBe('green')
  expect(modoInParole('', t).label).toBe('')
})

test('the account in rows, nothing empty', () => {
  expect(righeDelCollegamento({ connected: false }, t, (g) => g)).toEqual([])
  const righe = righeDelCollegamento(
    {
      connected: true,
      account_name: 'Centro Aurora',
      mode: 'test',
      key: 'sk_test_…1234',
      currency: 'EUR',
      connected_on: '2026-10-08',
      connected_by: '',
    },
    t,
    (g) => `il ${g}`,
  )
  expect(righe).toEqual([
    ['Account', 'Centro Aurora'],
    ['Mode', 'Test mode'],
    ['Key', 'sk_test_…1234'],
    ['Currency', 'EUR'],
    ['Connected', 'il 2026-10-08'],
  ])
})

test('the hours: a whole number from zero', () => {
  expect(oreValide('24')).toBe(24)
  expect(oreValide(-3)).toBe(0)
  expect(oreValide('x')).toBe(0)
  expect(oreValide(2.7)).toBe(2)
})

test('what was paid online of an invoice, and its deposit', () => {
  expect(righeDeiPagamenti(null, t, (g) => g)).toEqual([])
  expect(
    righeDeiPagamenti(
      {
        paid: [
          { paid_on: '8 ott', formatted_amount: '44,00 €', refunded: 0 },
          {
            paid_on: '9 ott',
            formatted_amount: '10,00 €',
            refunded: 5,
            formatted_refunded: '5,00 €',
          },
        ],
        deposit: { formatted_amount: '30,00 €' },
      },
      t,
      (g) => g,
    ),
  ).toEqual([
    'Paid online on 8 ott: 44,00 €',
    'Paid online on 9 ott: 10,00 €, 5,00 € given back on Stripe',
    'Deposit already paid online: 30,00 €',
  ])
})
