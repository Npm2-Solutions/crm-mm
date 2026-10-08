// Quotes in the editor: the same sums as crm/preventivi/regole.py, the colours
// of their states, and a quote as the server takes it. A module's fields on a row
// (the clinic's tooth and surfaces) travel with it, named in ``campi``.

export const STATO = {
  Draft: 'orange',
  Proposed: 'blue',
  Accepted: 'green',
  Declined: 'red',
  Completed: 'gray',
  Closed: 'gray',
}

export const STATO_VOCE = {
  'To do': 'gray',
  Booked: 'blue',
  Done: 'green',
  Cancelled: 'gray',
}

// an instalment of a quote paid in instalments
export const STATO_RATA = {
  'To pay': 'gray',
  Invoiced: 'blue',
  Paid: 'green',
  Cancelled: 'gray',
}

// a row's amount, as the server rounds it
export function importo(quantita, prezzo, sconto) {
  const q = Number(quantita) || 0
  const p = Number(prezzo) || 0
  const s = Math.min(Math.max(Number(sconto) || 0, 0), 100)
  return Math.round(((q * p * (100 - s)) / 100) * 100 + 1e-7) / 100
}

// the quote's sums: a cancelled row does not count
export function totali(voci) {
  let lordo = 0
  let netto = 0
  let fatto = 0
  for (const voce of voci || []) {
    if (voce.status === 'Cancelled') continue
    lordo += (Number(voce.qty) || 0) * (Number(voce.rate) || 0)
    const valore = importo(voce.qty, voce.rate, voce.discount)
    netto += valore
    if (voce.status === 'Done') fatto += valore
  }
  const tondo = (n) => Math.round(n * 100) / 100
  return {
    gross: tondo(lordo),
    discount: tondo(lordo - netto),
    net: tondo(netto),
    done: tondo(fatto),
    left: tondo(netto - fatto),
  }
}

function testo(valore) {
  if (typeof valore !== 'string') return valore ?? null
  return valore.trim() || null
}

// the quote as the server takes it; a module's fields on its rows as they are
export function perIlServer(preventivo, campi = []) {
  return {
    title: (preventivo.title || '').trim(),
    price_list: preventivo.price_list || null,
    valid_until: preventivo.valid_until || null,
    patient_notes: (preventivo.patient_notes || '').trim() || null,
    // how it is paid: at once, or a deposit and instalments
    payment: preventivo.payment === A_RATE ? A_RATE : UNICA,
    deposit_type:
      preventivo.deposit_type === PERCENTUALE ? PERCENTUALE : 'Amount',
    deposit_value: Number(preventivo.deposit_value) || 0,
    instalments_count: Number.parseInt(preventivo.instalments_count, 10) || 0,
    every_months: Number(preventivo.every_months) === 2 ? 2 : 1,
    first_due_on: preventivo.first_due_on || null,
    items: (preventivo.items || []).map((voce) => ({
      service: voce.service,
      description: (voce.description || '').trim() || null,
      phase: Math.max(Number(voce.phase) || 1, 1),
      qty: Number(voce.qty) > 0 ? Number(voce.qty) : 1,
      rate: Number(voce.rate) || 0,
      discount: Number(voce.discount) || 0,
      ...Object.fromEntries(campi.map((campo) => [campo, testo(voce[campo])])),
    })),
  }
}

// --- paid in instalments (crm/preventivi/rate_regole.py, the same cases) ----------

export const UNICA = 'Single payment'
export const A_RATE = 'Instalments'
export const PERCENTUALE = 'Percent'
export const ACCONTO = 'Deposit'
export const MIN_RATE = 2
export const MAX_RATE = 36

const cent = (valore) => Math.round((Number(valore) || 0) * 100 + 1e-7) / 100

// the same day some months later; the last of the month when it is shorter
function piuMesi(giorno, mesi) {
  const [anno, mese, di] = giorno.split('-').map(Number)
  const totale = mese - 1 + mesi
  const a = anno + Math.floor(totale / 12)
  const m = (totale % 12) + 1
  const ultimo = new Date(Date.UTC(a, m, 0)).getUTCDate()
  return `${a}-${String(m).padStart(2, '0')}-${String(Math.min(di, ultimo)).padStart(2, '0')}`
}

// the deposit in money: an amount or a share of the total, within the total
export function acconto(totale, tipo, valore) {
  const tot = cent(totale)
  const numero = Number(valore) || 0
  const soldi = tipo === PERCENTUALE ? (tot * numero) / 100 : numero
  return Math.min(Math.max(cent(soldi), 0), tot)
}

// what is left in equal instalments to the cent, the cents left over on the last
export function quote(resto, numero) {
  const centesimi = Math.round((Number(resto) || 0) * 100)
  const base = numero ? Math.floor(centesimi / numero) : 0
  const fatto = Array.from({ length: numero }, () => base)
  if (numero) fatto[numero - 1] = centesimi - base * (numero - 1)
  return fatto.map((c) => c / 100)
}

// the schedule: the deposit, due when accepted, and the instalments from the
// first day, every month or two
export function pianoDelleRate(totale, soldiAcconto, numero, ogni, primo) {
  const tot = cent(totale)
  const anticipo = Math.min(cent(soldiAcconto), tot)
  const fatto = []
  if (anticipo > 0)
    fatto.push({ kind: ACCONTO, number: 0, due_on: null, amount: anticipo })
  quote(cent(tot - anticipo), Number(numero) || 0).forEach((soldi, n) =>
    fatto.push({
      kind: 'Instalment',
      number: n + 1,
      due_on: primo ? piuMesi(primo, n * (Number(ogni) || 1)) : null,
      amount: soldi,
    }),
  )
  return fatto
}

// what is wrong with a plan's terms; with `oggi`, the first is not in the past
export function problemiDelleRate(
  totale,
  tipo,
  valore,
  numero,
  ogni,
  primo,
  oggi = null,
) {
  const fatto = []
  const n = Number.parseInt(numero, 10) || 0
  if (n < MIN_RATE || n > MAX_RATE) fatto.push('Instalments: from {0} to {1}')
  if (![1, 2].includes(Number(ogni)))
    fatto.push('Instalments go every month or every two months')
  const v = Number(valore) || 0
  if (
    v < 0 ||
    (tipo === PERCENTUALE && v >= 100) ||
    (cent(totale) > 0 && acconto(totale, tipo, valore) >= cent(totale))
  )
    fatto.push('The deposit is less than the total')
  if (!primo) fatto.push('Choose the day of the first instalment')
  else if (oggi && primo < oggi)
    fatto.push('The first instalment is not in the past')
  if (!fatto.length && cent(totale) > 0) {
    const resto = cent(cent(totale) - acconto(totale, tipo, valore))
    if (Math.min(...quote(resto, n)) <= 0)
      fatto.push('Too many instalments for what is left to pay')
  }
  return fatto
}

// how the plan goes, as the server sums it (`riassunto`), in one line: «Rate: 3 di
// 10 pagate · prossima 1 novembre 2026, 250,00 €»; `ritardo` where some are late
export function fraseDelleRate(riassunto, t, giorno, soldi) {
  if (!riassunto?.count) return null
  const parti = [
    riassunto.paid >= riassunto.count && !riassunto.next
      ? t('Instalments: all {0} paid', [riassunto.count])
      : t('Instalments: {0} of {1} paid', [riassunto.paid, riassunto.count]),
  ]
  const prossima = riassunto.next
  if (prossima)
    parti.push(
      prossima.kind === ACCONTO || !prossima.due_on
        ? t('next the deposit, {0}', [soldi(prossima.amount)])
        : t('next {0}, {1}', [giorno(prossima.due_on), soldi(prossima.amount)]),
    )
  if (riassunto.late)
    parti.push(
      riassunto.late === 1
        ? t('1 late, {0}', [soldi(riassunto.late_amount)])
        : t('{0} late, {1}', [riassunto.late, soldi(riassunto.late_amount)]),
    )
  return { testo: parti.join(' · '), ritardo: Boolean(riassunto.late) }
}
