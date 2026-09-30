// Dental care plans in the browser: the same teeth, surfaces and sums as
// crm/clinica/cure_regole.py, and what the editor sends to the server.

export const PERMANENTE = 'Permanent'
export const MISTA = 'Mixed'
export const DECIDUA = 'Deciduous'

// the chart's conditions, in the order the server keeps them, with how they are
// drawn: a colour of the design system, never the only sign (the name is there)
export const CONDIZIONI = [
  { value: 'Caries', tone: 'red', surfaces: true },
  { value: 'Filling', tone: 'blue', surfaces: true },
  { value: 'Root canal', tone: 'violet' },
  { value: 'Crown', tone: 'amber' },
  { value: 'Implant', tone: 'gray' },
  { value: 'Missing', tone: 'gray' },
  { value: 'To extract', tone: 'red' },
  { value: 'Bridge', tone: 'amber' },
  { value: 'Fracture', tone: 'orange', surfaces: true },
  { value: 'Sealant', tone: 'green', surfaces: true },
  { value: 'Veneer', tone: 'blue' },
  { value: 'Mobile', tone: 'orange' },
  { value: 'Impacted', tone: 'gray' },
  { value: 'Other', tone: 'gray' },
]
const PER_NOME = Object.fromEntries(CONDIZIONI.map((c) => [c.value, c]))

export const TONI = {
  red: 'bg-surface-red-2 text-ink-red-8',
  blue: 'bg-surface-blue-2 text-ink-blue-8',
  violet: 'bg-surface-violet-2 text-ink-violet-8',
  amber: 'bg-surface-amber-2 text-ink-amber-8',
  orange: 'bg-surface-orange-2 text-ink-orange-8',
  green: 'bg-surface-green-2 text-ink-green-8',
  gray: 'bg-surface-gray-3 text-ink-gray-8',
}

// a mark on the chart: a filled square in the condition's colour, the words in
// its label and in the legend
const SEGNI = {
  Caries: 'bg-surface-red-6',
  Filling: 'bg-surface-blue-6',
  'Root canal': 'bg-surface-violet-6',
  Crown: 'bg-surface-amber-6',
  Implant: 'bg-surface-gray-7',
  'To extract': 'bg-surface-gray-9',
  Bridge: 'bg-surface-amber-8',
  Fracture: 'bg-surface-orange-6',
  Sealant: 'bg-surface-green-6',
  Veneer: 'bg-surface-blue-8',
  Mobile: 'bg-surface-orange-8',
  Impacted: 'bg-surface-gray-5',
  Other: 'bg-surface-gray-5',
}

export function segno(condizione) {
  return SEGNI[condizione] || 'bg-surface-gray-5'
}

export function tono(condizione) {
  return TONI[PER_NOME[condizione]?.tone || 'gray']
}

export function suSuperfici(condizione) {
  return Boolean(PER_NOME[condizione]?.surfaces)
}

export const STATO_PIANO = {
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

export function eDente(codice) {
  const numero = Number(String(codice ?? '').trim())
  if (!Number.isInteger(numero)) return false
  const quadrante = Math.floor(numero / 10)
  const dente = numero % 10
  if (quadrante >= 1 && quadrante <= 4) return dente >= 1 && dente <= 8
  if (quadrante >= 5 && quadrante <= 8) return dente >= 1 && dente <= 5
  return false
}

// the rows a chart draws, the patient's right on the viewer's left
export function arcate(dentizione = PERMANENTE) {
  const arcata = (destra, sinistra, quanti) => [
    ...Array.from({ length: quanti }, (_, i) => destra * 10 + quanti - i),
    ...Array.from({ length: quanti }, (_, i) => sinistra * 10 + i + 1),
  ]
  const permanenti = [arcata(1, 2, 8), arcata(4, 3, 8)]
  const decidui = [arcata(5, 6, 5), arcata(8, 7, 5)]
  if (dentizione === DECIDUA) return decidui
  if (dentizione === MISTA)
    return [permanenti[0], decidui[0], decidui[1], permanenti[1]]
  return permanenti
}

const SUPERFICI = ['M', 'O', 'D', 'V', 'L']
const SINONIMI = { I: 'O', B: 'V', P: 'L' }

// the surfaces in their order ("dom" is "MOD"); null when one is not a surface
export function superfici(testo) {
  const lettere = new Set()
  for (const carattere of String(testo || '')
    .toUpperCase()
    .replace(/[\s,]/g, '')) {
    const lettera = SINONIMI[carattere] || carattere
    if (!SUPERFICI.includes(lettera)) return null
    lettere.add(lettera)
  }
  return SUPERFICI.filter((s) => lettere.has(s)).join('')
}

// what a tooth is now: its rows of the chart
export function delDente(righe, dente) {
  return (righe || []).filter((riga) => String(riga.tooth) === String(dente))
}

export function mancante(righe, dente) {
  return delDente(righe, dente).some((riga) => riga.condition === 'Missing')
}

// a treatment's amount, as the server rounds it
export function importo(quantita, prezzo, sconto) {
  const q = Number(quantita) || 0
  const p = Number(prezzo) || 0
  const s = Math.min(Math.max(Number(sconto) || 0, 0), 100)
  return Math.round(((q * p * (100 - s)) / 100) * 100 + 1e-7) / 100
}

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

// a treatment's tooth and surfaces, as a dentist writes them: "36 MOD"
export function sulDente(voce) {
  return [voce?.tooth, voce?.surfaces].filter(Boolean).join(' ')
}

// the plan as the server takes it
export function perIlServer(piano) {
  return {
    title: (piano.title || '').trim(),
    price_list: piano.price_list || null,
    valid_until: piano.valid_until || null,
    patient_notes: (piano.patient_notes || '').trim() || null,
    items: (piano.items || []).map((voce) => ({
      service: voce.service,
      description: (voce.description || '').trim() || null,
      tooth: voce.tooth ? String(voce.tooth).trim() : null,
      surfaces: voce.tooth && voce.surfaces ? voce.surfaces : null,
      phase: Math.max(Number(voce.phase) || 1, 1),
      qty: Number(voce.qty) > 0 ? Number(voce.qty) : 1,
      rate: Number(voce.rate) || 0,
      discount: Number(voce.discount) || 0,
    })),
  }
}
