// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// Settings > The centre > Features, without a screen (doc 36): the plan's
// modules split into what the product comprises and the extras, and the pages
// of the settings where each one is set up, among those the person sees.
import { trova } from '@/utils/impostazioni'

// What the product comprises, then the extras, each in the plan's order.
export function dividi(moduli = []) {
  return {
    compresi: moduli.filter((modulo) => modulo.included),
    extra: moduli.filter((modulo) => !modulo.included),
  }
}

// The pages a module is set up from, as links: the entry, and the tab when the
// page is one of the entry's several tabs; only those in the menu the person
// sees, each once.
export function doveSiImposta(menu, pagine = []) {
  const link = []
  for (const pagina of pagine) {
    const trovato = trova(menu, pagina)
    if (!trovato || link.some((l) => l.page === pagina)) continue
    const { voce, scheda } = trovato
    const gruppo = menu.find((g) => g.items.includes(voce))
    const unaDiPiu =
      voce.tabs?.length > 1 && scheda?.key === pagina && pagina !== voce.key
    link.push({
      page: pagina,
      label: voce.label,
      tab: unaDiPiu ? scheda.label : null,
      group: gruppo?.label || null,
    })
  }
  return link
}
