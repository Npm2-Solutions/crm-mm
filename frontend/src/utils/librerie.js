// The centre's libraries in Settings: the columns of a food table as the person
// importing sees and changes them, and the foods found by their words. The table
// itself is read on the server (crm/clinica/tabelle.py).

// what a table's columns may be, in the order the check shows them
export const CAMPI_TABELLA = [
  { key: 'name', label: 'Name' },
  { key: 'code', label: 'Code' },
  { key: 'group', label: 'Category' },
  { key: 'kcal', label: 'Energy (kcal)' },
  { key: 'kj', label: 'Energy (kJ)' },
  { key: 'protein_g', label: 'Proteins (g)' },
  { key: 'carbs_g', label: 'Carbohydrates (g)' },
  { key: 'fat_g', label: 'Fats (g)' },
  { key: 'fibre_g', label: 'Fibre (g)' },
  { key: 'alcohol_g', label: 'Alcohol (g)' },
]

export const FONTI = ['CIQUAL', 'CREA', 'BDA-IEO', 'USDA']
// the tables that fill the gaps: their foods are chosen one by one
export const DA_SCEGLIERE = ['CIQUAL', 'USDA']

// the server's columns as the selects hold them: one index each, as text; the
// group keeps its first (the most precise) column
export function mappaDalServer(mapping) {
  const scelta = {}
  for (const { key } of CAMPI_TABELLA) {
    const valore = mapping?.[key]
    const indice = Array.isArray(valore) ? valore[0] : valore
    scelta[key] = indice === undefined || indice === null ? '' : String(indice)
  }
  return scelta
}

// the selects' columns as the server reads them: the group keeps the columns
// after its first one, when the first is the one recognised
export function mappaPerIlServer(scelta, originale = {}) {
  const mapping = {}
  for (const { key } of CAMPI_TABELLA) {
    const valore = scelta?.[key]
    if (valore === '' || valore === undefined || valore === null) continue
    const indice = Number(valore)
    if (!Number.isInteger(indice) || indice < 0) continue
    if (key === 'group') {
      const prima = Array.isArray(originale.group) ? originale.group : []
      mapping.group = prima[0] === indice ? prima : [indice]
    } else {
      mapping[key] = indice
    }
  }
  return mapping
}

// lower case, without accents: "Pâtes" is found by "pates"
export function normalizza(testo) {
  return String(testo ?? '')
    .replace(/œ/gi, 'oe')
    .replace(/æ/gi, 'ae')
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

// the foods whose name or code holds every word written, of a category if chosen
export function filtra(cibi, testo = '', categoria = '') {
  const parole = normalizza(testo).split(' ').filter(Boolean)
  return (cibi || []).filter((cibo) => {
    if (categoria && (cibo.category || '') !== categoria) return false
    if (!parole.length) return true
    const dove = normalizza(`${cibo.name} ${cibo.code || ''}`)
    return parole.every((parola) => dove.includes(parola))
  })
}

// the keys chosen at first: all of an Italian table, none of one that fills gaps
export function sceltiAllInizio(cibi, fonte) {
  if (DA_SCEGLIERE.includes(fonte)) return new Set()
  return new Set((cibi || []).map((cibo) => cibo.key))
}

// a food's values in one line, for the check: what is not known is not written
export function rigaValori(cibo, t = (s, a) => format(s, a)) {
  const parti = []
  if (cibo.kcal !== null && cibo.kcal !== undefined)
    parti.push(t('{0} kcal', [cibo.kcal]))
  const nomi = [
    ['protein_g', 'P'],
    ['carbs_g', 'C'],
    ['fat_g', 'F'],
    ['fibre_g', 'Fib'],
  ]
  for (const [campo, sigla] of nomi) {
    if (cibo[campo] !== null && cibo[campo] !== undefined)
      parti.push(`${sigla} ${cibo[campo]}`)
  }
  return parti.join(' · ')
}

function format(testo, argomenti = []) {
  return testo.replace(/{(\d+)}/g, (tutto, n) =>
    argomenti[n] === undefined ? tutto : String(argomenti[n]),
  )
}
