// Plans in the editor: the same rules as crm/piani/regole.py - the days, the rows'
// keys - and how an item reads; the nutrients of the clinic's diets as
// crm/clinica/piani_regole.py counts them. What a kind holds and what its screens
// offer comes from the server (crm.piani.api.descrivi_tipo): {key, items, features}.

// the kinds of item: a module's kinds of plan are named by the server
export const CIBO = 'Food'
export const GRUPPO = 'Food group'
export const ESERCIZIO = 'Exercise'
export const ABITUDINE = 'Habit'

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

// whether the screens offer something for a kind: "meals", "calories", "targets",
// "nutrients", "recipes", "shopping"
export function offre(tipo, funzione) {
  return Boolean(tipo?.features?.includes(funzione))
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

// where a plan starts: the day's meals for a kind that says so (a diet), every
// day for one that holds only habits, a session for the rest
export function momentiIniziali(tipo, nomi, random) {
  if (offre(tipo, 'meals'))
    return nomi.pasti.map((nome) => nuovoMomento(nome, OGNI_GIORNO, random))
  const generi = tipo?.items || []
  if (generi.length === 1 && generi[0] === ABITUDINE)
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

// ------------------------------------------------------------------ the shopping list
// The server sums the grams (crm/clinica/piani_regole.py, spesa); here they are
// read as a person buys them.

export const GIORNI_SPESA = [7, 14, 21, 28, 35]

// what to buy of a food: rounded up, to 10 g, or to 100 g past the kilo
export function daComprare(grammi) {
  const v = valore(grammi)
  if (v === null || v <= 0) return null
  if (v < 1000) return { value: Math.ceil(v / 10) * 10, unit: 'g' }
  return { value: Math.ceil(v / 100) / 10, unit: 'kg' }
}

// "560 g", "1,2 kg": in the reader's language
export function quantitaDaComprare(grammi, locale) {
  const q = daComprare(grammi)
  if (!q) return ''
  return `${q.value.toLocaleString(locale)} ${q.unit}`
}

// "80 g, 7 times": how the sum is made, when every time is the same
export function comeSiArriva(riga, t = (s, a) => format(s, a)) {
  if (riga.each && riga.times > 1)
    return t('{0} g, {1} times', [riga.each, riga.times])
  if (riga.times > 1) return t('{0} times', [riga.times])
  return ''
}

// the foods by group, in the order the server gives them
export function perGruppo(righe) {
  const gruppi = []
  for (const riga of righe || []) {
    const ultimo = gruppi[gruppi.length - 1]
    if (ultimo && ultimo.group === riga.food_group) ultimo.items.push(riga)
    else gruppi.push({ group: riga.food_group, items: [riga] })
  }
  return gruppi
}

// the list as words, to paste in a message: a line a food
export function testoDellaSpesa(lista, t = (s, a) => format(s, a), locale) {
  const righe = []
  for (const gruppo of perGruppo(lista?.foods)) {
    righe.push(t(gruppo.group).toUpperCase())
    for (const riga of gruppo.items) {
      const quanto = quantitaDaComprare(riga.grams, locale)
      righe.push(`- ${riga.food_name}${quanto ? ': ' + quanto : ''}`)
    }
  }
  for (const gruppo of lista?.groups || []) {
    righe.push(t('{0}: {1} portions', [t(gruppo.food_group), gruppo.portions]))
  }
  return righe.join('\n')
}

// who writes a kind the reader's qualification does not, in one line: «Medico
// chirurgo, Biologo o Dietista», as the reader's language lists them
export function chiLoScrive(nomi, locale = 'en-GB') {
  const elenco = (nomi || []).filter(Boolean)
  if (!elenco.length) return ''
  try {
    return new Intl.ListFormat(locale, {
      style: 'long',
      type: 'disjunction',
    }).format(elenco)
  } catch {
    return elenco.join(', ')
  }
}
