// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A questionnaire's total over time, drawn: where each signed form's total
 * falls, the line through them, the score's bands behind (the server's series,
 * `crm/moduli/andamenti_regole.py`). Pure: tested.
 */

// room on the left for the ticks, on the right for the bands' names, below
// for the dates
const MARGINI = { sopra: 8, sotto: 22, sinistra: 30, destra: 64 }

const numero = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null)

/** The bands that can be drawn: a number from and to each, in order. */
export function fasceDi(serie) {
  return (serie?.bands || [])
    .filter((b) => numero(b?.from) !== null && numero(b?.to) !== null)
    .sort((a, b) => a.from - b.from)
}

/**
 * The chart of a series in a box `larghezza` × `altezza`: the points (x by
 * date, y by total), the line, the bands as stripes and two ticks on the side.
 * One form alone sits in the middle.
 */
export function graficoDellAndamento(
  serie,
  { larghezza = 320, altezza = 140, margini = MARGINI } = {},
) {
  const punti = (serie?.points || []).filter((p) => numero(p.value) !== null)
  const fasce = fasceDi(serie)
  const valori = [
    ...punti.map((p) => p.value),
    ...fasce.flatMap((b) => [b.from, b.to]),
  ]
  let minimo = valori.length ? Math.min(0, ...valori) : 0
  let massimo = valori.length ? Math.max(...valori) : 1
  if (massimo === minimo) massimo = minimo + 1
  const sinistra = margini.sinistra
  const destra = larghezza - margini.destra
  const sopra = margini.sopra
  const sotto = altezza - margini.sotto
  const y = (v) => sotto - ((v - minimo) / (massimo - minimo)) * (sotto - sopra)
  const tempi = punti.map((p) => new Date(p.date).getTime())
  const primo = Math.min(...tempi)
  const ultimo = Math.max(...tempi)
  const x = (t) =>
    ultimo === primo
      ? (sinistra + destra) / 2
      : sinistra + ((t - primo) / (ultimo - primo)) * (destra - sinistra)
  const disegnati = punti.map((p, i) => ({
    ...p,
    x: Math.round(x(tempi[i]) * 10) / 10,
    y: Math.round(y(p.value) * 10) / 10,
  }))
  return {
    punti: disegnati,
    linea: disegnati.map((p, i) => `${i ? 'L' : 'M'}${p.x} ${p.y}`).join(''),
    // where the plot is: the stripes run across it, the bands' names after it
    area: { sinistra, destra, sopra, sotto },
    fasce: fasce.map((b, i) => {
      const alto = y(Math.min(b.to, massimo))
      const basso = y(Math.max(b.from, minimo))
      return {
        etichetta: b.label,
        y: Math.round(alto * 10) / 10,
        altezza: Math.round(Math.max(0, basso - alto) * 10) / 10,
        pari: i % 2 === 0,
      }
    }),
    tacche: [
      { valore: massimo, y: sopra },
      { valore: minimo, y: sotto },
    ],
    minimo,
    massimo,
  }
}

/** How the last total moved from the one before: `{ differenza, da }`, or null. */
export function variazione(serie) {
  const punti = (serie?.points || []).filter((p) => numero(p.value) !== null)
  if (punti.length < 2) return null
  const [prima, ultima] = punti.slice(-2)
  return {
    differenza: Math.round((ultima.value - prima.value) * 100) / 100,
    da: prima.date,
  }
}
