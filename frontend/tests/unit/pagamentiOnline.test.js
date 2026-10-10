// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// Online payments' words and checks: the same rules as crm/pagamenti/regole.py.
import { expect, test } from 'vitest'
import {
  accontoInParole,
  addebitoInParole,
  cartaInParole,
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
    'it',
  )
  expect(righe).toEqual([
    ['Account', 'Centro Aurora'],
    ['Mode', 'Test mode'],
    ['Key', 'sk_test_…1234'],
    ['Currency', 'Euro'],
    ['Connected', 'il 2026-10-08'],
  ])
})

test('an account without a name is not shown by its id', () => {
  const righe = righeDelCollegamento(
    { connected: true, account_id: 'acct_1AbC', currency: 'usd' },
    t,
    (g) => g,
    'it',
  )
  expect(righe[0]).toEqual(['Account', 'No name on Stripe yet'])
  expect(righe.find(([chi]) => chi === 'Currency')[1]).toBe(
    'Dollaro statunitense',
  )
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
        advances: [
          {
            number: '2026/S/12',
            date: '9 ott',
            formatted_amount: '30,00 €',
            issued: true,
          },
          { formatted_amount: '20,00 €', issued: false },
        ],
      },
      t,
      (g) => g,
    ),
  ).toEqual([
    'Paid online on 8 ott: 44,00 €',
    'Paid online on 9 ott: 10,00 €, 5,00 € given back on Stripe',
    'Advance invoice no. 2026/S/12 of 9 ott: 30,00 €',
    'Advance invoice still a draft: 20,00 €',
    'Deposit paid online without an invoice: 30,00 €',
  ])
})

test('a card in words', () => {
  expect(cartaInParole({ brand: 'Visa', last4: '4242' })).toBe('Visa •••• 4242')
  expect(cartaInParole({ last4: '0005' })).toBe('•••• 0005')
  expect(cartaInParole(null)).toBe('')
})

test('the monthly charge in the area and at the desk', () => {
  const g = (giorno) => `il ${giorno}`
  const carta = {
    active: true,
    brand: 'Visa',
    last4: '4242',
    next_on: '1 nov',
    next_amount: '40,00 €',
    fixed_term: true,
  }
  expect(addebitoInParole(null, t, g)).toEqual({ riga: '', problema: '' })
  expect(addebitoInParole(carta, t, g)).toEqual({
    riga: 'Monthly charge on the card Visa •••• 4242 · next il 1 nov, 40,00 €',
    problema: '',
  })
  expect(addebitoInParole({ ...carta, next_amount: null }, t, g).riga).toBe(
    'Monthly charge on the card Visa •••• 4242 · next il 1 nov',
  )
  const fallita = {
    ...carta,
    next_on: '4 nov',
    failed: { on: '1 nov', reason: 'The card has expired.', retries: true },
  }
  expect(addebitoInParole(fallita, t, g)).toEqual({
    riga: 'Monthly charge on the card Visa •••• 4242',
    problema:
      'The charge of il 1 nov did not go through: The card has expired. The card is tried again on il 4 nov.',
  })
  expect(
    addebitoInParole(
      { ...fallita, failed: { ...fallita.failed, retries: false } },
      t,
      g,
    ).problema,
  ).toBe('The charge of il 1 nov did not go through: The card has expired.')
  expect(addebitoInParole(fallita, t, g, { reception: true })).toEqual({
    riga: 'Automatic charge on · card Visa •••• 4242',
    problema: 'Not charged on il 1 nov: the person has the link to pay',
  })
  const ferma = {
    ...carta,
    active: false,
    stopped_on: '2 nov',
    stopped_by: 'Chiara',
  }
  expect(addebitoInParole(ferma, t, g)).toEqual({
    riga: 'Card charges stopped on il 2 nov. The instalments stay to pay as your subscription says.',
    problema: '',
  })
  expect(addebitoInParole(ferma, t, g, { reception: true }).riga).toBe(
    'Card charges stopped on il 2 nov · Chiara',
  )
  expect(
    addebitoInParole({ ...carta, active: false, stopped_on: null }, t, g),
  ).toEqual({ riga: '', problema: '' })
})

test('a booking’s deposit on its appointment, in a line', () => {
  const pagato = { state: 'paid', formatted_amount: '30,00 €' }
  expect(accontoInParole(null, t)).toBe('')
  expect(accontoInParole({ ...pagato, state: 'waiting' }, t)).toBe(
    'Deposit waiting for payment: 30,00 €',
  )
  expect(accontoInParole({ ...pagato, invoice: '2026/S/12' }, t)).toBe(
    'Deposit paid online: 30,00 € · invoice no. 2026/S/12',
  )
  expect(accontoInParole({ ...pagato, invoice_draft: true }, t)).toBe(
    'Deposit paid online: 30,00 € · invoice still a draft',
  )
  // the invoice's number only to whoever reads invoices: the server leaves it out
  expect(accontoInParole(pagato, t)).toBe('Deposit paid online: 30,00 €')
  // a cancellation that keeps it says so
  expect(
    accontoInParole({ ...pagato, kept: true, invoice: '2026/S/12' }, t),
  ).toBe('Deposit kept at the cancellation: 30,00 € · invoice no. 2026/S/12')
  const reso = {
    state: 'refunded',
    formatted_amount: '30,00 €',
    formatted_refunded: '30,00 €',
  }
  expect(accontoInParole(reso, t)).toBe('Deposit given back: 30,00 €')
  expect(accontoInParole({ ...reso, credit_note: '2026/S/13' }, t)).toBe(
    'Deposit given back: 30,00 € · credit note no. 2026/S/13',
  )
  expect(
    accontoInParole(
      { ...reso, refunded_by: 'Paolo Rinaldi', credit_note: '2026/S/13' },
      t,
    ),
  ).toBe(
    'Deposit given back by Paolo Rinaldi: 30,00 € · credit note no. 2026/S/13',
  )
  expect(
    accontoInParole(
      { ...reso, state: 'partly_refunded', formatted_refunded: '10,00 €' },
      t,
    ),
  ).toBe('Deposit given back in part: 10,00 € of 30,00 €')
})
