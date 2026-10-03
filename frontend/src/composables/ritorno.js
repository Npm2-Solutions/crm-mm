// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A list found again as it was left when a back returns to it
 * (utils/ritorno.js).
 */
import { conserva, rimettiLoScorrimento, ritrova } from '@/utils/ritorno'
import { onBeforeUnmount, onMounted } from 'vue'

/**
 * Keeps list `chiave` as it is when its page goes, and puts it back when a
 * back returns to it: `stato()` reads what the list keeps (its search, its
 * rows...), `rimetti(salvato)` puts it back at once, while the page is made;
 * `contenitore`, the box that scrolls (when the list has one of its own), goes
 * back down to where it was once its rows are there. Gives back what was put
 * back, or null: the list then loads as it always does.
 */
export function useRitorno(
  chiave,
  { contenitore = null, stato = () => ({}), rimetti = () => {} },
) {
  const salvato = ritrova(chiave)
  if (salvato) rimetti(salvato)
  let smetti = null
  onMounted(() => {
    if (salvato) {
      smetti = rimettiLoScorrimento(contenitore?.value, salvato.scorrimento)
    }
  })
  onBeforeUnmount(() => {
    smetti?.()
    conserva(chiave, {
      ...stato(),
      scorrimento: contenitore?.value?.scrollTop || 0,
    })
  })
  return salvato
}
