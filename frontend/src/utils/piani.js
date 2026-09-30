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

// ------------------------------------------------------------------ nutrients
// The same totals as crm/clinica/piani_regole.py, on the cases of
// crm/clinica/tests/casi_nutrienti.json: the targets are the nutritionist's, the
// numbers come from the tables' values for 100 g, never from the assistant.

export const NUTRIENTI = ['kcal', 'protein_g', 'carbs_g', 'fat_g', 'fibre_g']

// a number as Python's float() reads it, or null
function valore(v) {
  if (v === null || v === undefined || typeof v === 'boolean') return null
  if (typeof v === 'number') return Number.isFinite(v) ? v : null
  const testo = String(v).trim()
  if (!testo) return null
  const n = Number(testo)
  return Number.isFinite(n) ? n : null
}

// half up, as the server rounds it
function mezzoSu(v, decimali = 0) {
  const scala = 10 ** decimali
  return Math.floor(v * scala + 0.5) / scala
}

// a quantity as a person weighs it: to 5 g, to the gram under 10 g, never 0
export function arrotondaGrammi(grammi) {
  const v = valore(grammi)
  if (v === null || v <= 0) return null
  if (v < 10) return Math.max(1, mezzoSu(v))
  return 5 * mezzoSu(v / 5)
}

// what the foods give: kcal to the unit, grams to one decimal; a food without
// grams, or not in the tables, counts nothing and is named in ``missing``
export function nutrienti(voci, cibi) {
  const totali = Object.fromEntries(NUTRIENTI.map((n) => [n, 0]))
  const missing = []
  for (const voce of voci || []) {
    if ((voce.kind || CIBO) !== CIBO || !voce.food) continue
    const cibo = (cibi || {})[voce.food]
    const grammi = valore(voce.quantity_g)
    if (!cibo || !grammi || grammi <= 0) {
      missing.push(voce.food)
      continue
    }
    for (const nome of NUTRIENTI) {
      const v = valore(cibo[nome])
      if (v !== null) totali[nome] += (v * grammi) / 100
    }
  }
  return {
    kcal: mezzoSu(totali.kcal),
    ...Object.fromEntries(
      NUTRIENTI.slice(1).map((n) => [n, mezzoSu(totali[n], 1)]),
    ),
    missing,
  }
}

// each day's totals: the every-day moments and that weekday's; one row, every
// day, when no moment is on a weekday of its own
export function perGiorno(momenti, voci, cibi) {
  const ogni = new Set(
    (momenti || [])
      .filter((m) => (m.day || OGNI_GIORNO) === OGNI_GIORNO)
      .map((m) => m.key),
  )
  const suoi = GIORNI.filter((g) => (momenti || []).some((m) => m.day === g))
  const del = (chiavi) =>
    nutrienti(
      (voci || []).filter((v) => chiavi.has(v.moment)),
      cibi,
    )
  if (!suoi.length) return [{ day: OGNI_GIORNO, ...del(ogni) }]
  return GIORNI.map((giorno) => {
    const chiavi = new Set(ogni)
    for (const m of momenti) if (m.day === giorno) chiavi.add(m.key)
    return { day: giorno, ...del(chiavi) }
  })
}

// a total in words, for the nutritionist: no colour, no judgement
export function rigaNutrienti(n, t = (s, a) => format(s, a)) {
  if (!n) return ''
  return [
    t('{0} kcal', [n.kcal]),
    t('proteins {0} g', [n.protein_g]),
    t('carbohydrates {0} g', [n.carbs_g]),
    t('fats {0} g', [n.fat_g]),
    t('fibre {0} g', [n.fibre_g]),
  ].join(' · ')
}
