// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// Online payments on the centre's own Stripe account (crm/pagamenti, doc 60): the
// key before it is sent, the connection in words, a payment in words. The same
// rules as crm/pagamenti/regole.py. `t` is the translator (`__`).

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

/** The connected account, as the page lists it: [label, value]. */
export function righeDelCollegamento(stato, t, giorno) {
  if (!stato?.connected) return []
  return [
    [t('Account'), stato.account_name || stato.account_id],
    [t('Mode'), modoInParole(stato.mode, t).label],
    [t('Key'), stato.key],
    [t('Currency'), stato.currency],
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
  if (online.deposit)
    righe.push(
      t('Deposit already paid online: {0}', [online.deposit.formatted_amount]),
    )
  return righe
}
