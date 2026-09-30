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
