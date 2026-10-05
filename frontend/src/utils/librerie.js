// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The centre's libraries in Settings: where a food comes from, and its values in
// one line. The library itself comes from the server (crm/clinica/librerie.py):
// the one DottorCloud ships, and the centre's own.

// the tables a food may come from: the library's, CIQUAL; the Italian ones a
// centre imported before the library came
export const FONTI = ['CIQUAL', 'CREA', 'BDA-IEO', 'USDA']

// a food's values in one line, in the reader's words and with their numbers
// (`lingua`, Intl's: «27,1» in Italian): what is not known is not written
export function rigaValori(cibo, t = (s, a) => format(s, a), lingua = 'it') {
  const parti = []
  if (cibo.kcal !== null && cibo.kcal !== undefined)
    parti.push(t('{0} kcal', [numeroDelCibo(cibo.kcal, lingua)]))
  // each sentence whole, for the catalog's check (paroleDaTradurre.test.js)
  const frasi = [
    ['protein_g', (n) => t('proteins {0} g', [n])],
    ['carbs_g', (n) => t('carbohydrates {0} g', [n])],
    ['fat_g', (n) => t('fats {0} g', [n])],
    ['fibre_g', (n) => t('fibre {0} g', [n])],
  ]
  for (const [campo, frase] of frasi) {
    if (cibo[campo] !== null && cibo[campo] !== undefined)
      parti.push(frase(numeroDelCibo(cibo[campo], lingua)))
  }
  return parti.join(' · ')
}

/** A food's number as the reader writes it, to one decimal: 0.083 is «0,1». */
export function numeroDelCibo(valore, lingua = 'it') {
  try {
    return new Intl.NumberFormat(lingua, { maximumFractionDigits: 1 }).format(
      valore,
    )
  } catch {
    return String(valore)
  }
}

function format(testo, argomenti = []) {
  return testo.replace(/{(\d+)}/g, (tutto, n) =>
    argomenti[n] === undefined ? tutto : String(argomenti[n]),
  )
}
