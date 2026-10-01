// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The first steps without a screen (doc 37): how far along the person is, the
// next one to take, and whether the sidebar shows them. The steps and whether
// each is done come from the server (crm/primi_passi.py), from the centre's data.

// Done, how many, the next one not done, and how far in percent.
export function riassunto(dati) {
  const passi = dati?.steps || []
  const fatti = passi.filter((passo) => passo.done).length
  const totale = passi.length
  return {
    fatti,
    totale,
    prossimo: passi.find((passo) => !passo.done) || null,
    percentuale: totale ? Math.round((fatti / totale) * 100) : 0,
    finiti: totale > 0 && fatti === totale,
  }
}

// The sidebar shows them while some are left and the person did not hide them:
// a centre that already works has nothing to show.
export function daMostrare(dati, nascosti = false) {
  const { totale, finiti } = riassunto(dati)
  return totale > 0 && !finiti && !nascosti
}
