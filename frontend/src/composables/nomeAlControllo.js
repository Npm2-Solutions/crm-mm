// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { getCurrentInstance, onMounted, onUpdated, ref } from 'vue'

// what a row of settings may hold to be named by its words: frappe-ui's switch
// (a button), a field, a select, a picker's button
const CONTROLLI =
  "[role='switch'], input:not([type='hidden']), select, textarea, [role='combobox'], button[aria-haspopup]"

/**
 * The words of a setting's row name the control beside them: the row draws
 * them as `<label :for="id">`, with the id of the first control in `scatola`
 * (given one when it has none). frappe-ui's Switch puts an `aria-label` on its
 * outer box, not on its button, so VoiceOver read «switch» and nothing else;
 * a label for it also flips it when its words are tapped.
 */
export function useNomeAlControllo(scatola) {
  const perId = ref('')
  const uid = getCurrentInstance()?.uid ?? Math.random().toString(36).slice(2)

  function trova() {
    const controllo = scatola.value?.querySelector(CONTROLLI)
    if (!controllo) {
      perId.value = ''
      return
    }
    if (!controllo.id) controllo.id = `riga-${uid}`
    perId.value = controllo.id
  }

  onMounted(trova)
  onUpdated(trova)
  return perId
}
