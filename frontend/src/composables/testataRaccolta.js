// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A record's card on a phone - the person's name, what comes next, call and
 * write - folds away once the tab below it is scrolled, as a phone's own
 * contact card does, and comes back at the tab's top. The tabs scroll in boxes
 * of their own, so the card never went by itself: a third of the screen stayed
 * taken while one read a long tab, or wrote a visit with the keyboard up. The
 * name stays in the header above.
 */
import { onBeforeUnmount, ref, watch } from 'vue'

// how far a tab is scrolled before the card folds
export const SOGLIA_TESTATA = 24
// a box shorter than this is something inside a tab, not the tab
const ALTEZZA_MINIMA = 120
const CAMPI = 'textarea, input, select, [contenteditable]'

/**
 * Whether the card is folded once a tab's box went from `prima` to `cima`, of
 * `altezza`, with `visibile` of it shown, under a card `testata` tall. It
 * folds past the threshold only when what is below stays scrolled with the card
 * gone - else the box would spring back to its top, the card open, and again -
 * and folded it stays so until the tab is back at its top. A jump longer than
 * what the box shows is the page's own (a conversation opening at its last
 * message), not a finger's: it changes nothing.
 */
export function raccogliereLaTestata({
  prima = 0,
  cima,
  altezza,
  visibile,
  testata,
  raccolta,
}) {
  if (cima <= 0) return false
  if (Math.abs(cima - prima) > visibile) return raccolta
  if (raccolta) return true
  return cima > SOGLIA_TESTATA && altezza - visibile > testata + SOGLIA_TESTATA
}

/**
 * Listens to the boxes that scroll up and down inside `area` (a ref to the
 * tabs) and says whether the card (`testata`, a ref to it) is folded. A field
 * or an editor scrolling its own words is not the tab, nor is a box too short
 * to be one. Another tab (`scheda`, a ref) opens with the card open.
 */
export function useTestataRaccolta(area, testata, scheda) {
  const raccolta = ref(false)
  // where each box was: one moved sideways keeps its top, and says nothing
  const cime = new WeakMap()

  function scorre(evento) {
    const box = evento.target
    if (!(box instanceof HTMLElement) || box.clientHeight < ALTEZZA_MINIMA)
      return
    if (box.matches(CAMPI) || box.closest('[contenteditable]')) return
    const prima = cime.get(box) ?? 0
    const cima = box.scrollTop
    if (cima === prima) return
    cime.set(box, cima)
    raccolta.value = raccogliereLaTestata({
      prima,
      cima,
      altezza: box.scrollHeight,
      visibile: box.clientHeight,
      testata: testata.value?.offsetHeight || 0,
      raccolta: raccolta.value,
    })
  }

  function ascolta(nuova, vecchia) {
    vecchia?.removeEventListener('scroll', scorre, true)
    nuova?.addEventListener('scroll', scorre, { capture: true, passive: true })
  }

  watch(area, ascolta, { immediate: true, flush: 'post' })
  if (scheda) watch(scheda, () => (raccolta.value = false))
  onBeforeUnmount(() => ascolta(null, area.value))

  return raccolta
}
