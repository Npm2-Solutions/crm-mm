// The centre's libraries in Settings: where a food comes from, and its values in
// one line. The library itself comes from the server (crm/clinica/librerie.py):
// the one DottorCloud ships, and the centre's own.

// the tables a food may come from: the library's, CIQUAL; the Italian ones a
// centre imported before the library came
export const FONTI = ['CIQUAL', 'CREA', 'BDA-IEO', 'USDA']

// a food's values in one line: what is not known is not written
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
