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
// what somebody moves a box with: a finger that moves, a wheel, a key that
// scrolls. A tap moves nothing: tapping «Activity» the conversation went to
// its last message in two steps, and the second, inside the gesture's time,
// folded the card as if somebody had scrolled
const GESTI = ['touchmove', 'wheel', 'keydown']
const TASTI_CHE_SCORRONO = new Set([
  'ArrowUp',
  'ArrowDown',
  'PageUp',
  'PageDown',
  'Home',
  'End',
  ' ',
])

/** Whether `evento` is somebody moving what is under it: never a tap, nor a
 * key that does not scroll (Escape closing a menu). */
export function muoveLaPagina(evento) {
  if (evento.type === 'keydown') return TASTI_CHE_SCORRONO.has(evento.key)
  return GESTI.includes(evento.type)
}

// how long after a finger, a wheel or a key a box's scrolling is theirs
export const DOPO_UN_GESTO = 1500

/**
 * Whether the card is folded once a tab's box went from `prima` to `cima`, of
 * `altezza`, with `visibile` of it shown, under a card `testata` tall. It
 * folds past the threshold only when what is below stays scrolled with the card
 * gone - else the box would spring back to its top, the card open, and again -
 * and folded it stays so until the tab is back at its top. Only somebody's
 * scrolling folds it (`gesto`): a box that scrolls by itself - the history
 * opening at its newest day, a conversation at its last message - leaves the
 * card as it is, or a person's page opened with their card already gone. A
 * jump longer than what the box shows is the page's own too: it changes
 * nothing.
 */
export function raccogliereLaTestata({
  prima = 0,
  cima,
  altezza,
  visibile,
  testata,
  raccolta,
  gesto = true,
}) {
  if (cima <= 0) return false
  if (!gesto) return raccolta
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
  // when somebody last moved something in the tabs
  let ultimoGesto = 0
  const gesto = (evento) => {
    if (muoveLaPagina(evento)) ultimoGesto = Date.now()
  }

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
      // with the keyboard up the box follows the words one writes: theirs too
      gesto:
        Date.now() - ultimoGesto < DOPO_UN_GESTO ||
        document.documentElement.dataset.tastiera === 'aperta',
    })
  }

  function ascolta(nuova, vecchia) {
    vecchia?.removeEventListener('scroll', scorre, true)
    nuova?.addEventListener('scroll', scorre, { capture: true, passive: true })
    for (const tipo of GESTI) {
      vecchia?.removeEventListener(tipo, gesto, true)
      nuova?.addEventListener(tipo, gesto, { capture: true, passive: true })
    }
  }

  watch(area, ascolta, { immediate: true, flush: 'post' })
  if (scheda) watch(scheda, () => (raccolta.value = false))
  onBeforeUnmount(() => ascolta(null, area.value))

  return raccolta
}
