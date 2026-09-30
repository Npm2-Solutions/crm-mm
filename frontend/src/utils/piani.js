// Plans in the editor: the same rules as crm/clinica/piani_regole.py - what each
// kind of plan holds, the days, the rows' keys - and how an item reads.

export const MENU = 'Meal plan'
export const SCAMBI = 'Exchange diet'
export const ALLENAMENTO = 'Training'
export const ESERCIZI = 'Home exercises'
export const ABITUDINI = 'Habits'
export const TIPI = [MENU, SCAMBI, ALLENAMENTO, ESERCIZI, ABITUDINI]

export const CIBO = 'Food'
export const GRUPPO = 'Food group'
export const ESERCIZIO = 'Exercise'
export const ABITUDINE = 'Habit'

// what each kind holds: a habit fits anywhere
export const VOCI = {
  [MENU]: [CIBO, ABITUDINE],
  [SCAMBI]: [GRUPPO, CIBO, ABITUDINE],
  [ALLENAMENTO]: [ESERCIZIO, ABITUDINE],
  [ESERCIZI]: [ESERCIZIO, ABITUDINE],
  [ABITUDINI]: [ABITUDINE],
}

export const OGNI_GIORNO = 'Every day'
export const GIORNI = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

export const GRUPPI = [
  'Cereals and tubers',
  'Legumes',
  'Meat',
  'Fish',
  'Eggs',
  'Milk and dairy',
  'Vegetables',
  'Fruit',
  'Oils and fats',
  'Nuts and seeds',
  'Sweets',
  'Drinks',
  'Other',
]

export const PARTI = [
  'Full body',
  'Chest',
  'Back',
  'Shoulders',
  'Arms',
  'Core',
  'Hips',
  'Legs',
  'Neck',
  'Other',
]

export const ESITI = ['Done', 'Partly', 'Skipped']

export function generiPer(tipo) {
  return VOCI[tipo] || []
}

export function isDieta(tipo) {
  return tipo === MENU || tipo === SCAMBI
}

// eight hex characters, as the server makes them: a check-in stays with its item
export function nuovaChiave(random = Math.random) {
  let chiave = ''
  for (let i = 0; i < 8; i++) chiave += Math.floor(random() * 16).toString(16)
  return chiave
}

export function nuovoMomento(label = '', day = OGNI_GIORNO, random) {
  return { key: nuovaChiave(random), label, day, time: null }
}

// where a plan starts: the day's meals for a diet, a session for a training
export function momentiIniziali(tipo, nomi, random) {
  if (isDieta(tipo))
    return nomi.pasti.map((nome) => nuovoMomento(nome, OGNI_GIORNO, random))
  if (tipo === ABITUDINI)
    return [nuovoMomento(nomi.giorno, OGNI_GIORNO, random)]
  return [nuovoMomento(nomi.seduta, OGNI_GIORNO, random)]
}

export function nuovaVoce(genere, momento, random) {
  const voce = {
    key: nuovaChiave(random),
    moment: momento,
    kind: genere,
    times_per_week: '0',
  }
  if (genere === ESERCIZIO) Object.assign(voce, { sets: 3, reps: '10' })
  if (genere === GRUPPO)
    Object.assign(voce, { food_group: GRUPPI[0], portions: 1 })
  return voce
}

function numero(valore) {
  const n = Number(valore)
  return Number.isFinite(n) && n > 0 ? n : null
}

// how an item reads, in the practitioner's and the patient's words (``t`` translates)
export function descrivi(voce, t = (s, a) => format(s, a)) {
  const volte = numero(voce.times_per_week)
  const aSettimana = volte ? ' · ' + t('{0} times a week', [volte]) : ''
  if (voce.kind === CIBO) {
    const grammi = numero(voce.quantity_g)
    return (
      (voce.food_name || t('Food')) +
      (grammi ? ` · ${grammi} g` : '') +
      aSettimana
    )
  }
  if (voce.kind === GRUPPO) {
    const porzioni = numero(voce.portions) || 1
    return (
      t(porzioni === 1 ? '{0} portion of {1}' : '{0} portions of {1}', [
        porzioni,
        t(voce.food_group || 'Other'),
      ]) + aSettimana
    )
  }
  if (voce.kind === ESERCIZIO) {
    const parti = [voce.exercise_name || t('Exercise')]
    const serie = numero(voce.sets)
    if (serie && voce.reps) parti.push(`${serie} × ${voce.reps}`)
    else if (serie) parti.push(t('{0} sets', [serie]))
    if (voce.duration) parti.push(voce.duration)
    if (voce.load) parti.push(voce.load)
    if (voce.rest) parti.push(t('rest {0}', [voce.rest]))
    return parti.join(' · ') + aSettimana
  }
  return (voce.text || '') + aSettimana
}

function format(testo, argomenti = []) {
  return testo.replace(/{(\d+)}/g, (tutto, n) =>
    argomenti[n] === undefined ? tutto : String(argomenti[n]),
  )
}

// an item's last days, oldest first: its outcome on each, or null
export function giorniDellaVoce(logs, chiave, giorni) {
  const perGiorno = {}
  for (const log of logs || []) {
    if (log.item_key === chiave) perGiorno[String(log.log_date)] = log.outcome
  }
  return giorni.map((giorno) => ({
    day: giorno,
    outcome: perGiorno[giorno] || null,
  }))
}

// the moments with their items, in the plan's order
export function perMomento(momenti, voci) {
  return (momenti || []).map((momento) => ({
    ...momento,
    items: (voci || []).filter((voce) => voce.moment === momento.key),
  }))
}
