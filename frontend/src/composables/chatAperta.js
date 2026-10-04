// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A conversation open on a phone with its box to write in is the screen, as in
 * a phone's own messengers (telefono.css, «11»): while `aperta` is true the
 * page's root says so (`data-chat`), the bar at the bottom steps aside and the
 * box is the screen's bottom; with the keyboard up, what is not the messages
 * nor the words being written (`data-via-scrivendo`: a record's tabs, the
 * channels to read, the channels to write on) steps aside too. The bar and
 * the card above left a person's chat a quarter of an iPhone, and with the
 * keyboard up nearly nothing.
 */
import { onBeforeUnmount, toValue, watch } from 'vue'

// the pages that say so: one at a time, but one that opens while the last
// closes must not lose the mark to the other's goodbye
let aperte = 0

export function useChatAperta(aperta) {
  let mia = false
  function segna(si) {
    if (si === mia) return
    mia = si
    aperte += si ? 1 : -1
    if (aperte > 0) document.documentElement.dataset.chat = 'aperta'
    else delete document.documentElement.dataset.chat
  }
  watch(() => Boolean(toValue(aperta)), segna, { immediate: true })
  onBeforeUnmount(() => segna(false))
}
