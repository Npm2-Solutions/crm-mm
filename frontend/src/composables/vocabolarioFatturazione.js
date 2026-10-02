// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The names of invoicing's codes, in the reader's language
 * (crm.invoicing.scelte.get_vocabulary): what a list row says instead of N4,
 * SP or `fisioterapista`. Loaded once per session.
 */
import { createResource } from 'frappe-ui'
import { computed } from 'vue'

let risorsa

export function useVocabolarioFatturazione() {
  if (!risorsa) {
    risorsa = createResource({
      url: 'crm.invoicing.scelte.get_vocabulary',
      cache: 'vocabolario-fatturazione',
      auto: true,
    })
  }
  return {
    nomi: computed(() => risorsa.data?.names || {}),
    profilo: computed(() => risorsa.data?.profile || 'generale'),
  }
}
