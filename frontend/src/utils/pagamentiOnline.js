// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// Online payments on the centre's own Stripe account (crm/pagamenti, doc 60): the
// key before it is sent, the connection in words, a payment in words. The same
// rules as crm/pagamenti/regole.py. `t` is the translator (`__`).

import { nomeDellaValuta } from '@/utils/valute'

/** What is wrong with what was pasted, before Stripe is asked; '' when nothing. */
export function problemaDellaChiave(chiave, t) {
  const pulita = (chiave || '').replace(/\s+/g, '')
  if (!pulita) return t('Paste the secret key of your Stripe account.')
  if (pulita.startsWith('pk_'))
    return t(
      'This is the publishable key: paste the secret key (sk_…) or a restricted key (rk_…).',
    )
  if (!modalita(pulita) || pulita.length < 20)
    return t('This is not a Stripe secret key: it starts with sk_ or rk_.')
  return ''
}

/** `test` or `live` from a secret or restricted key, else ''. */
export function modalita(chiave) {
  const pulita = (chiave || '').replace(/\s+/g, '')
  for (const prefisso of ['sk_', 'rk_']) {
    if (pulita.startsWith(prefisso + 'test_')) return 'test'
    if (pulita.startsWith(prefisso + 'live_')) return 'live'
  }
  return ''
}

/** The account's mode in words, and the badge's theme. */
export function modoInParole(modo, t) {
  if (modo === 'test')
    return {
      label: t('Test mode'),
      theme: 'orange',
      riga: t(
        'Test mode: no real money moves. Pay with the card 4242 4242 4242 4242.',
      ),
    }
  if (modo === 'live')
    return {
      label: t('Live payments'),
      theme: 'green',
      riga: t('Live: the payments are real and reach your account.'),
    }
  return { label: '', theme: 'gray', riga: '' }
}

/** The connected account, as the page lists it: [label, value]; its currency by
 * its name in `lingua`, never Stripe's code nor its id. */
export function righeDelCollegamento(stato, t, giorno, lingua = 'it') {
  if (!stato?.connected) return []
  return [
    [t('Account'), stato.account_name || t('No name on Stripe yet')],
    [t('Mode'), modoInParole(stato.mode, t).label],
    [t('Key'), stato.key],
    [t('Currency'), nomeDellaValuta(stato.currency, lingua)],
    [
      t('Connected'),
      [stato.connected_on ? giorno(stato.connected_on) : '', stato.connected_by]
        .filter(Boolean)
        .join(' · '),
    ],
  ].filter(([, valore]) => valore)
}

/** The hours before an appointment a cancellation gives the deposit back: a
 * whole number from 0. */
export function oreValide(ore) {
  const numero = Number(ore)
  if (!Number.isFinite(numero) || numero < 0) return 0
  return Math.floor(numero)
}

/** What was paid online of an invoice, in a line for the dialog. */
export function righeDeiPagamenti(online, t, giorno) {
  if (!online) return []
  const righe = (online.paid || []).map((p) =>
    p.refunded
      ? t('Paid online on {0}: {1}, {2} given back on Stripe', [
          giorno(p.paid_on),
          p.formatted_amount,
          p.formatted_refunded,
        ])
      : t('Paid online on {0}: {1}', [giorno(p.paid_on), p.formatted_amount]),
  )
  // the advance invoices of its appointment: this invoice is their balance
  for (const acconto of online.advances || [])
    righe.push(
      acconto.issued
        ? t('Advance invoice no. {0} of {1}: {2}', [
            acconto.number,
            giorno(acconto.date),
            acconto.formatted_amount,
          ])
        : t('Advance invoice still a draft: {0}', [acconto.formatted_amount]),
    )
  // a deposit paid before the advance invoices were made
  if (online.deposit)
    righe.push(
      t('Deposit paid online without an invoice: {0}', [
        online.deposit.formatted_amount,
      ]),
    )
  return righe
}

/** A card as a person reads it: «Visa •••• 4242». */
export function cartaInParole(carta) {
  if (!carta?.last4) return ''
  return [carta.brand, `•••• ${carta.last4}`].filter(Boolean).join(' ')
}

/**
 * The monthly charge of a subscription on its saved card, in words
 * (`crm.pagamenti.addebiti.della_carta`): `riga` what goes on, `problema` what
 * did not go through or stopped. In the area to the person; `reception` for the
 * desk's card. `giorno` writes a day.
 */
export function addebitoInParole(carta, t, giorno, { reception = false } = {}) {
  if (!carta) return { riga: '', problema: '' }
  const nome = cartaInParole(carta)
  if (!carta.active) {
    if (!carta.stopped_on) return { riga: '', problema: '' }
    return reception
      ? {
          riga: carta.stopped_by
            ? t('Card charges stopped on {0} · {1}', [
                giorno(carta.stopped_on),
                carta.stopped_by,
              ])
            : t('Card charges stopped on {0}', [giorno(carta.stopped_on)]),
          problema: '',
        }
      : {
          // said, not a problem: the instalments are owed as they always were
          riga: [
            t('Card charges stopped on {0}.', [giorno(carta.stopped_on)]),
            carta.fixed_term
              ? t('The instalments stay to pay as your subscription says.')
              : '',
          ]
            .filter(Boolean)
            .join(' '),
          problema: '',
        }
  }
  if (reception) {
    if (carta.failed)
      return {
        riga: t('Automatic charge on · card {0}', [nome]),
        problema: t('Not charged on {0}: the person has the link to pay', [
          giorno(carta.failed.on),
        ]),
      }
    return {
      riga: t('Automatic charge on · card {0}', [nome]),
      problema: carta.expired ? t('The card has expired.') : '',
    }
  }
  let riga = t('Monthly charge on the card {0}', [nome])
  if (carta.next_on && !carta.failed)
    riga = carta.next_amount
      ? t('Monthly charge on the card {0} · next {1}, {2}', [
          nome,
          giorno(carta.next_on),
          carta.next_amount,
        ])
      : t('Monthly charge on the card {0} · next {1}', [
          nome,
          giorno(carta.next_on),
        ])
  let problema = ''
  if (carta.failed) {
    problema = t('The charge of {0} did not go through: {1}', [
      giorno(carta.failed.on),
      carta.failed.reason,
    ])
    if (carta.failed.retries && carta.next_on)
      problema +=
        ' ' + t('The card is tried again on {0}.', [giorno(carta.next_on)])
  } else if (carta.expired) problema = t('The card has expired.')
  return { riga, problema }
}
