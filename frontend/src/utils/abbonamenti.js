// Subscriptions in words: what a type gives, how the entries of this week or
// month stand, until when it lasts, what a sale may be. The rules are
// crm/scheduling/abbonamenti_regole.py's.

export const SUBITO = 'Upfront'
export const MENSILE = 'Monthly'
export const ILLIMITATI = 'Unlimited'
export const A_SETTIMANA = 'Per week'
export const AL_MESE = 'Per month'
export const MAX_MESI = 36

// Active, Suspended, Expired, Closed: where a subscription stands
export const TEMA_DELLO_STATO = {
  Active: 'green',
  Suspended: 'orange',
  Expired: 'gray',
  Closed: 'gray',
}

// "3 months · 8 entries a month", "1 month · any number of entries"
export function cosaDa(tipo, t = (s, a) => format(s, a)) {
  if (!tipo) return ''
  const mesi = Number(tipo.months) || 1
  const durata = mesi === 1 ? t('1 month') : t('{0} months', [mesi])
  return [durata, quantiIngressi(tipo, t)].join(' · ')
}

// "8 entries a week", "any number of entries"
export function quantiIngressi(tipo, t = (s, a) => format(s, a)) {
  const n = Number(tipo?.entries_count) || 0
  if (tipo?.entries === A_SETTIMANA)
    return n === 1 ? t('1 entry a week') : t('{0} entries a week', [n])
  if (tipo?.entries === AL_MESE)
    return n === 1 ? t('1 entry a month') : t('{0} entries a month', [n])
  return t('any number of entries')
}

// how this week's or month's entries stand: "2 of 8 used this month"
export function questoPeriodo(abbonamento, t = (s, a) => format(s, a)) {
  if (!abbonamento || abbonamento.entries === ILLIMITATI) return ''
  if (abbonamento.used === null || abbonamento.used === undefined) return ''
  const usati = Number(abbonamento.used) || 0
  const totale = Number(abbonamento.entries_count) || 0
  return abbonamento.entries === A_SETTIMANA
    ? t('{0} of {1} used this week', [usati, totale])
    : t('{0} of {1} used this month', [usati, totale])
}

// entries still to use in the period, never below none
export function rimasti(abbonamento) {
  if (!abbonamento || abbonamento.entries === ILLIMITATI) return null
  return Math.max(
    (Number(abbonamento.entries_count) || 0) - (Number(abbonamento.used) || 0),
    0,
  )
}

// the used part of the period, for the bar
export function percentuale(abbonamento) {
  const totale = Number(abbonamento?.entries_count) || 0
  if (!totale || abbonamento?.entries === ILLIMITATI) return 0
  return Math.min(
    100,
    Math.round(((Number(abbonamento.used) || 0) / totale) * 100),
  )
}

// the instalments of a sale, as the server makes them: one, or one a month on
// the same day, the last taking the cents left over
export function rate(inizio, mesi, prezzo, pagamento) {
  const p = Math.round((Number(prezzo) || 0) * 100) / 100
  const n = Number(mesi) || 1
  if (!inizio) return []
  if (pagamento !== MENSILE || n <= 1) return [{ due_on: inizio, amount: p }]
  const quota = Math.round((p / n) * 100) / 100
  const fatte = []
  for (let i = 0; i < n; i++)
    fatte.push({ due_on: piuMesi(inizio, i), amount: quota })
  fatte[n - 1].amount = Math.round((p - quota * (n - 1)) * 100) / 100
  return fatte
}

// the same day some months later; the last of the month when it is shorter
export function piuMesi(giorno, mesi) {
  const [anno, mese, di] = giorno.split('-').map(Number)
  const totale = mese - 1 + mesi
  const a = anno + Math.floor(totale / 12)
  const m = (totale % 12) + 1
  const ultimo = new Date(Date.UTC(a, m, 0)).getUTCDate()
  return `${a}-${String(m).padStart(2, '0')}-${String(Math.min(di, ultimo)).padStart(2, '0')}`
}

// the last day: the day before the same day some months later
export function fine(inizio, mesi) {
  if (!inizio) return ''
  const dopo = piuMesi(inizio, Number(mesi) || 1)
  const giorno = new Date(`${dopo}T00:00:00Z`)
  giorno.setUTCDate(giorno.getUTCDate() - 1)
  return giorno.toISOString().slice(0, 10)
}

// a person's place in an appointment, for its panel: "An entry of Pilates 8"; in a
// class, whose place it is: "Anna uses an entry of Pilates 8"
export function rigaDelPosto(posto, inUnaLezione, t = (s, a) => format(s, a)) {
  if (!posto) return ''
  const suo = (posto.options || []).find(
    (uno) => uno.name === posto.subscription,
  )
  if (!inUnaLezione) {
    if (!posto.subscription) return t('Not in a subscription')
    return suo ? t('An entry of {0}', [suo.type]) : t('In a subscription')
  }
  const nome = posto.participant_name
  if (!posto.subscription) return t('{0} is not in a subscription', [nome])
  return suo
    ? t('{0} uses an entry of {1}', [nome, suo.type])
    : t('{0} is in a subscription', [nome])
}

// what the sale form says before the server does: the first thing to put right
export function errore(modulo, t = (s, a) => format(s, a)) {
  if (!modulo.subscription_type) return t('Choose the type of subscription')
  if (!modulo.starts_on) return t('Choose the first day')
  if (modulo.price !== '' && modulo.price !== null && Number(modulo.price) < 0)
    return t('A price is not below zero')
  return ''
}

// the type's form, before the server: the first thing to put right
export function erroreDelTipo(tipo, t = (s, a) => format(s, a)) {
  const mesi = Number(tipo.months)
  if (!(tipo.type_name || '').trim()) return t('Give the type a name')
  if (!Number.isInteger(mesi) || mesi < 1 || mesi > MAX_MESI)
    return t('A subscription lasts from 1 to {0} months', [MAX_MESI])
  if (!(tipo.services || []).length)
    return t('Choose the services it comprises')
  if (tipo.entries !== ILLIMITATI && !(Number(tipo.entries_count) >= 1))
    return t('Say how many entries')
  if (tipo.sold_online && !tipo.billable_service)
    return t(
      'A subscription sold online needs a fiscal card: its invoice is made at the payment.',
    )
  if (tipo.sold_online && !(Number(tipo.price) > 0))
    return t('A subscription sold online needs a price.')
  return ''
}

// what selling a type from the client area means, under its switch; `vendita`
// is the centre's (`crm.pagamenti.collegamento.online_sales_on`)
export function rigaDellaVendita(tipo, vendita, t = (s, a) => format(s, a)) {
  if (!tipo?.billable_service)
    return t(
      'A subscription sold online needs a fiscal card: its invoice is made at the payment.',
    )
  const alMese = tipo.payment === MENSILE && Number(tipo.months) > 1
  if (alMese && !vendita?.card_charges)
    return t(
      'Paid by the month, it is sold online only with the monthly charge on the saved card: Settings > Invoicing > Online payments.',
    )
  return alMese
    ? t(
        'The person buys it from their area: the first instalment by card, the next ones charged on the same card on their day.',
      )
    : t(
        'The person buys it from their area and pays by card: its invoice is issued once paid.',
      )
}

// what one pays for a subscription bought from the client area (`crm.pagamenti.
// addebiti.in_vendita`): «186,66 € at once», «49,78 € a month, 3 instalments»
export function prezzoDellAcquisto(voce, t = (s, a) => format(s, a)) {
  if (!voce) return ''
  return voce.monthly
    ? t('{0} a month, {1} instalments', [
        voce.formatted_first,
        voce.instalments,
      ])
    : t('{0} at once', [voce.formatted_total])
}

// the words the person agrees to before the card is kept for the next
// instalments: the server's own (`addebiti.mandato`), on Stripe's page too
export function mandatoInParole(
  voce,
  t = (s, a) => format(s, a),
  giorno = (g) => g,
) {
  if (!voce?.monthly) return ''
  return t(
    'You authorise the centre to charge {0} every month on the card until {1}; you can stop it from your area.',
    [voce.formatted_first, giorno(voce.until)],
  )
}

function format(testo, argomenti = []) {
  return testo.replace(/{(\d+)}/g, (tutto, n) =>
    argomenti[n] === undefined ? tutto : String(argomenti[n]),
  )
}
