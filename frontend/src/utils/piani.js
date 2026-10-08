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
    const misura = grammi ? misuraCasalinga(voce, grammi, t) : ''
    return (
      (voce.food_name || t('Food')) +
      (grammi ? ` · ${grammi} g` : '') +
      (misura ? ` (${misura})` : '') +
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
    if (LATI[voce.side]) parti.push(t(LATI[voce.side]))
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

// ------------------------------------------------------------------ the week
// A plan's moments are every day's or one weekday's: the editor shows one day at
// a time, copies a meal or a session into other days, a day into others.

// the moments the editor shows for a day: that day's own (every day's are
// their own day too)
export function momentiDelGiorno(momenti, giorno) {
  return (momenti || []).filter((m) => (m.day || OGNI_GIORNO) === giorno)
}

// how many moments each day holds, every day's first
export function momentiPerGiorno(momenti) {
  return [OGNI_GIORNO, ...GIORNI].map((giorno) => ({
    day: giorno,
    count: momentiDelGiorno(momenti, giorno).length,
  }))
}

// a moment and its items copied into a day: new keys, nothing shared with the
// original, so a check-in stays with the item it was made on
export function copiaMomento(momento, voci, giorno, random) {
  const nuovo = { ...momento, key: nuovaChiave(random), day: giorno }
  const sue = (voci || [])
    .filter((v) => v.moment === momento.key)
    .map((v) => ({ ...v, key: nuovaChiave(random), moment: nuovo.key }))
  return { momento: nuovo, voci: sue }
}

// an every-day moment made one of each weekday, to change day by day: seven
// copies in its place, in the order of the week
export function perOgniGiorno(momento, voci, random) {
  const nuovi = { momenti: [], voci: [] }
  for (const giorno of GIORNI) {
    const copia = copiaMomento(momento, voci, giorno, random)
    nuovi.momenti.push(copia.momento)
    nuovi.voci.push(...copia.voci)
  }
  return nuovi
}

// a day copied into others: each of its moments, with their items
export function copiaGiorno(momenti, voci, da, verso, random) {
  const nuovi = { momenti: [], voci: [] }
  for (const giorno of verso || []) {
    if (giorno === da) continue
    for (const momento of momentiDelGiorno(momenti, da)) {
      const copia = copiaMomento(momento, voci, giorno, random)
      nuovi.momenti.push(copia.momento)
      nuovi.voci.push(...copia.voci)
    }
  }
  return nuovi
}

// a group's standard portion, in grams, as the LARN (SINU, 2014) tables give
// them: what a food without a portion of its own starts from
export const PORZIONI = {
  'Cereals and tubers': 80,
  Legumes: 150,
  Meat: 100,
  Fish: 150,
  Eggs: 50,
  'Milk and dairy': 125,
  Vegetables: 200,
  Fruit: 150,
  'Oils and fats': 10,
  'Nuts and seeds': 30,
  Sweets: 30,
  Drinks: 200,
}

// the grams a food starts from in a plan: the library's portion, else its
// group's standard one, else 100 g; the nutritionist changes it
export function grammiIniziali(cibo) {
  const porzione = valore(cibo?.portion_g)
  if (porzione && porzione > 0) return porzione
  return PORZIONI[cibo?.food_group] || 100
}

// what a day gives: every day's moments and, for a weekday, its own
export function totaleDelGiorno(momenti, voci, cibi, giorno) {
  const chiavi = new Set(
    (momenti || [])
      .filter((m) => {
        const suo = m.day || OGNI_GIORNO
        return suo === OGNI_GIORNO || suo === giorno
      })
      .map((m) => m.key),
  )
  return nutrienti(
    (voci || []).filter((v) => chiavi.has(v.moment)),
    cibi,
  )
}

// each nutrient next to its target: how far the day has come, as a share the
// bar draws (capped at 1) and what is left or over; no target, no share
export function versoGliObiettivi(totale, obiettivi) {
  return NUTRIENTI.map((nome) => {
    const fatto = valore(totale?.[nome]) || 0
    const obiettivo = valore(obiettivi?.[nome])
    if (!obiettivo || obiettivo <= 0)
      return { key: nome, value: fatto, target: null, share: null, left: null }
    return {
      key: nome,
      value: fatto,
      target: obiettivo,
      share: Math.min(fatto / obiettivo, 1),
      left: mezzoSu(obiettivo - fatto, nome === 'kcal' ? 0 : 1),
    }
  })
}

/**
 * The moments as a week is read: every day's first, then Monday to Sunday,
 * each day's by its time (those without one after); otherwise as written.
 */
export function inOrdineDiGiorno(momenti) {
  const giorni = [OGNI_GIORNO, ...GIORNI]
  const posto = (m) => {
    const i = giorni.indexOf(m.day || OGNI_GIORNO)
    return i < 0 ? giorni.length : i
  }
  return (momenti || [])
    .map((m, i) => ({ m, i }))
    .sort(
      (a, b) =>
        posto(a.m) - posto(b.m) ||
        (a.m.time || '99').localeCompare(b.m.time || '99') ||
        a.i - b.i,
    )
    .map(({ m }) => m)
}

/**
 * How hard or painful the person said it was, 1 to 10, in the order said (0 is
 * not said): the average to one decimal, the last, how many; null when none —
 * the same as the server's `regole.fatica`.
 */
export function faticaDetta(valori) {
  const detti = (valori || [])
    .map(Number)
    .filter((v) => Number.isInteger(v) && v >= 1 && v <= 10)
  if (!detti.length) return null
  const media = detti.reduce((s, v) => s + v, 0) / detti.length
  return {
    average: Math.round(media * 10) / 10,
    last: detti[detti.length - 1],
    said: detti.length,
  }
}

/** A number of the food tables as the reader writes it: «87,6», «1.800». */
export function numeroDelleTabelle(n, locale = 'it-IT') {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(
    Number(n) || 0,
  )
}

// ------------------------------------------------------------------ how a food looks

/** Each group's mark and the category colour it is drawn in. */
export const ASPETTO_DEI_GRUPPI = {
  'Cereals and tubers': { icona: 'lucide-wheat', colore: 'amber' },
  Legumes: { icona: 'lucide-bean', colore: 'green' },
  Meat: { icona: 'lucide-beef', colore: 'rose' },
  Fish: { icona: 'lucide-fish', colore: 'blue' },
  Eggs: { icona: 'lucide-egg', colore: 'amber' },
  'Milk and dairy': { icona: 'lucide-milk', colore: 'blue' },
  Vegetables: { icona: 'lucide-carrot', colore: 'green' },
  Fruit: { icona: 'lucide-apple', colore: 'rose' },
  'Oils and fats': { icona: 'lucide-droplet', colore: 'amber' },
  'Nuts and seeds': { icona: 'lucide-nut', colore: 'amber' },
  Sweets: { icona: 'lucide-candy', colore: 'rose' },
  Drinks: { icona: 'lucide-cup-soda', colore: 'blue' },
  Other: { icona: 'lucide-utensils', colore: 'violet' },
}

// what a food's name says it is, in Italian and in English, before its group:
// the first that matches the start of a word
const ICONE_PER_NOME = [
  [/\b(acqua|water)\b/, 'lucide-glass-water'],
  [/\b(caff[eè]|coffee|espresso|cappuccino)/, 'lucide-coffee'],
  [/\b(vin[oi]|wine)\b/, 'lucide-wine'],
  [/\b(birr[ae]|beer)\b/, 'lucide-beer'],
  [/\b(gelat[oi]|sorbett|ice cream|sorbet)/, 'lucide-ice-cream-cone'],
  [/\b(tort[ae]|crostat|cake|tart\b)/, 'lucide-cake-slice'],
  [/\b(ciambell|krapfen|donut|doughnut)/, 'lucide-donut'],
  [/\b(cornett|brioche|croissant)/, 'lucide-croissant'],
  [/\b(biscott|frollin|cookie|biscuit)/, 'lucide-cookie'],
  [/\b(caramell|lecca|lollipop|sweet candy)/, 'lucide-lollipop'],
  [/\b(pizz[ae])\b/, 'lucide-pizza'],
  [/\b(hamburger|burger)/, 'lucide-hamburger'],
  [/\b(panin[oi]|tramezzin|sandwich)/, 'lucide-sandwich'],
  [/\b(zupp|minestr|vellutat|brodo|soup|broth)/, 'lucide-soup'],
  [/\b(popcorn)/, 'lucide-popcorn'],
  [/\b(prosciutt|salam|mortadell|speck|bresaola|ham\b|salami)/, 'lucide-ham'],
  [/\b(poll[oi]|tacchin|chicken|turkey)/, 'lucide-drumstick'],
  [
    /\b(cozz|vongol|gamber|scamp|calamar|totan|polp[oi]|seppi|mussel|clam|shrimp|prawn|squid|octopus|oyster|ostric)/,
    'lucide-shell',
  ],
  [/\b(insalat|lattug|rucol|salad|lettuce)/, 'lucide-salad'],
  [
    /\b(spinac|biet[ae]|bietol|cavol|broccol|verz|cicori|kale|spinach|chard|cabbage)/,
    'lucide-leafy-green',
  ],
  [/\b(banan)/, 'lucide-banana'],
  [/\b(ciliegi|amaren|cherr)/, 'lucide-cherry'],
  [
    /\b(arance?|aranci[ae]|limon|mandarin|clementin|pompelm|orange|lemon|grapefruit)/,
    'lucide-citrus',
  ],
  [/\b(uva|uvett|grape|raisin)/, 'lucide-grape'],
  [/\b(uov[oa]|egg)/, 'lucide-egg'],
  [/\b(latte|milk)\b/, 'lucide-milk'],
]

/** A food's mark and colour: by what its name says, else by its group. */
export function aspettoDelCibo(cibo) {
  const gruppo =
    ASPETTO_DEI_GRUPPI[cibo?.food_group] || ASPETTO_DEI_GRUPPI.Other
  const nome = (cibo?.food_name || '').toLowerCase()
  const trovata = ICONE_PER_NOME.find(([parola]) => parola.test(nome))
  return { icona: trovata ? trovata[1] : gruppo.icona, colore: gruppo.colore }
}

// ------------------------------------------------------------------ household measures

// the measures an Italian kitchen weighs by (CREA's and SINU's portions), first
// by what the name says, then by the group; a food with none is weighed
const MISURE_PER_NOME = [
  [/\b(fett[ae] biscottat|rusk)/, 10, ['{0} rusk', '{0} rusks']],
  [/\b(biscott|frollin|cookie|biscuit)/, 10, ['{0} biscuit', '{0} biscuits']],
  [/\b(pane|bread)\b/, 50, ['{0} slice', '{0} slices']],
  [/\b(uov[oa]|egg)/, 60, ['{0} egg', '{0} eggs']],
  [/\b(yogurt|yoghurt)/, 125, ['{0} jar', '{0} jars']],
  [
    /\b(zucchero|sugar|miele|honey|marmellat|confettur|jam)\b/,
    5,
    ['{0} teaspoon', '{0} teaspoons'],
  ],
  [/\b(grattugiat|grated)/, 10, ['{0} tablespoon', '{0} tablespoons']],
  [/\b(latte|milk|succo|juice)\b/, 125, ['{0} glass', '{0} glasses']],
  [
    /\b(fragol|mirtill|lampon|ribes|more|frutti di bosco|ciliegi|uva|strawberr|blueberr|raspberr|currant|cherr|grape)/,
    null,
  ],
]
const MISURE_PER_GRUPPO = {
  'Oils and fats': [10, ['{0} tablespoon', '{0} tablespoons']],
  'Nuts and seeds': [30, ['{0} handful', '{0} handfuls']],
  Fruit: [150, ['{0} medium fruit', '{0} medium fruits']],
}

// halves as a cook writes them
function mezzi(n) {
  const intero = Math.floor(n)
  const mezzo = n - intero >= 0.5
  if (!mezzo) return String(intero)
  return intero ? `${intero}½` : '½'
}

/**
 * The grams of a food as a kitchen measures them («1 tablespoon», «1½ slices»),
 * when they are near one (within 15%, in halves up to ten); '' otherwise.
 */
export function misuraCasalinga(cibo, grammi, t = (s, a) => format(s, a)) {
  const g = Number(grammi)
  if (!(g > 0)) return ''
  const nome = (cibo?.food_name || '').toLowerCase()
  const perNome = MISURE_PER_NOME.find(([parola]) => parola.test(nome))
  const misura = perNome
    ? perNome[1] && [perNome[1], perNome[2]]
    : MISURE_PER_GRUPPO[cibo?.food_group]
  if (!misura) return ''
  const [unita, [una, tante]] = misura
  const n = Math.round((g / unita) * 2) / 2
  if (n < 0.5 || n > 10) return ''
  if (Math.abs(n * unita - g) / g > 0.15) return ''
  return t(n > 1 ? tante : una, [mezzi(n)])
}

// ------------------------------------------------------------------ the same, another food

/**
 * A food's name to the first comma, without what is in brackets: «Pera,
 * cruda» is a pear, «Latte intero (alimento medio)» whole milk.
 */
export function nomeBreve(nome) {
  return (nome || '')
    .split(',')[0]
    .replace(/\s*\([^)]*\)/g, '')
    .trim()
}

/** The grams of ``cibo`` that give ``kcal``, to 5 g; null without its energy. */
export function grammiEquivalenti(kcal, cibo) {
  const perCento = Number(cibo?.kcal)
  if (!(perCento > 0) || !(Number(kcal) > 0)) return null
  return Math.max(5, Math.round((kcal * 100) / perCento / 5) * 5)
}

// where a food's energy comes from, as three shares: what makes two foods alike
function profilo(cibo) {
  const e = Object.entries(KCAL_PER_GRAMMO).map(
    ([chiave, k]) => (Number(cibo?.[chiave]) || 0) * k,
  )
  const somma = e.reduce((s, x) => s + x, 0)
  return somma > 0 ? e.map((x) => x / somma) : null
}

function distanza(a, b) {
  if (!a || !b) return 1
  return a.reduce((s, x, i) => s + Math.abs(x - b[i]), 0)
}

// a food's kind: the first word of its name («Olio», «Burro», «Pera»)
function genereDelNome(nome) {
  return nomeBreve(nome).split(/\s+/)[0].toLowerCase()
}

/**
 * Foods of the same group that give what ``voce`` gives, each with its grams:
 * the alternatives a diet offers («Pera 160 g»), the most alike first (where
 * their energy comes from), one of each kind, the food itself left out.
 */
export function alternativeEquivalenti(voce, cibi, quante = 6) {
  const dettaglio = voce?.food_detail || {}
  const kcal = (Number(dettaglio.kcal) * Number(voce?.quantity_g)) / 100
  if (!(kcal > 0)) return []
  const suo = profilo(dettaglio)
  const proprio = nomeBreve(dettaglio.food_name || voce.food_name)
  const ordinati = (cibi || [])
    .map((cibo, i) => ({ cibo, i, d: distanza(suo, profilo(cibo)) }))
    // alike first; as alike, in the order the library gave them (the used first)
    .sort((a, b) => Math.round((a.d - b.d) * 100) || a.i - b.i)
  const generi = new Set()
  const fuori = []
  for (const { cibo } of ordinati) {
    if (cibo.name === voce.food) continue
    const nome = nomeBreve(cibo.food_name)
    const genere = genereDelNome(cibo.food_name)
    if (!nome || nome === proprio || generi.has(genere)) continue
    const grammi = grammiEquivalenti(kcal, cibo)
    if (!grammi) continue
    generi.add(genere)
    fuori.push({ name: cibo.name, food_name: nome, grams: grammi })
    if (fuori.length >= quante) break
  }
  return fuori
}

/** Alternatives written in one line, after what was there. */
export function aggiungiAlternativa(scritte, alternativa) {
  const parola = `${alternativa.food_name} ${alternativa.grams} g`
  const prima = (scritte || '').trim()
  if (!prima) return parola
  if (prima.includes(parola)) return prima
  return `${prima}; ${parola}`
}

// ------------------------------------------------------------------ where the energy comes from

/** Kilocalories in a gram (Atwater): what the shares are counted on. */
export const KCAL_PER_GRAMMO = { protein_g: 4, carbs_g: 4, fat_g: 9 }
/**
 * The adult's reference intake ranges (LARN 2014, RI), as a share of the
 * energy; proteins have none there, they are given in grams per kilo.
 */
export const INTERVALLI_LARN = {
  carbs_g: [45, 60],
  fat_g: [20, 35],
}

/**
 * Where a day's energy comes from: each macronutrient's share in whole
 * percents, and whether it is within LARN's range; [] when nothing counts.
 */
export function ripartizioneEnergia(totale) {
  const energie = Object.entries(KCAL_PER_GRAMMO).map(([chiave, k]) => [
    chiave,
    (Number(totale?.[chiave]) || 0) * k,
  ])
  const somma = energie.reduce((s, [, e]) => s + e, 0)
  if (!(somma > 0)) return []
  return energie.map(([chiave, e]) => {
    const share = Math.round((e / somma) * 100)
    const [min, max] = INTERVALLI_LARN[chiave] || [null, null]
    return {
      key: chiave,
      share,
      min,
      max,
      within: min === null ? null : share >= min && share <= max,
    }
  })
}

// ------------------------------------------------------------------ an exercise's dose

/** Which side an exercise is done on, in the words its row says. */
export const LATI = {
  'Each side': 'each side',
  Left: 'left side',
  Right: 'right side',
}

/** The doses a physiotherapist gives most, one tap each. */
export const DOSI = [
  { sets: 3, reps: '10' },
  { sets: 3, reps: '12' },
  { sets: 3, reps: '15' },
  { sets: 2, reps: '20' },
  { sets: 3, duration: '30 s' },
  { sets: 1, duration: '60 s' },
]

/** A dose as its chip reads it: «3 × 10», «3 × 30 s». */
export function testoDellaDose(dose) {
  return `${dose.sets} × ${dose.reps || dose.duration}`
}

/** The dose given to an item: sets with reps, or sets held for a time. */
export function conLaDose(voce, dose) {
  return {
    ...voce,
    sets: dose.sets,
    reps: dose.reps || '',
    duration: dose.duration || '',
  }
}
