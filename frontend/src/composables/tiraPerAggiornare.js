// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Pulling a list down from its top reloads it, as in a phone's own apps. The
 * browser's own pull reloaded the whole app, a form half written with it, and
 * is off (telefono.css); this one reloads only the list under the finger.
 */
import { onBeforeUnmount, onMounted, reactive } from 'vue'

// how far the finger has to bring the mark down before letting go reloads
export const SOGLIA_TIRATA = 64
// the mark comes no further down than this
export const MASSIMO_TIRATA = 96

/** How far down the mark is for a finger that moved `delta` pixels down. */
export function tirata(delta) {
  if (!(delta > 0)) return 0
  // the list resists: half the finger's way, as a phone's own lists do
  return Math.min(MASSIMO_TIRATA, Math.round(delta / 2))
}

/**
 * Follows a finger on `contenitore` (a ref to the box that scrolls): when it
 * pulls the box down from its top past the threshold and lets go,
 * `aggiorna()` runs and the mark turns until it is done. Gives back the
 * mark's state: `distanza`, `pronta` (letting go reloads), `inCorso`,
 * `trascinando` (a finger holds it).
 */
export function useTiraPerAggiornare(contenitore, aggiorna) {
  const stato = reactive({
    distanza: 0,
    pronta: false,
    inCorso: false,
    trascinando: false,
  })
  let inizio = null

  function giu(evento) {
    const box = contenitore.value
    inizio =
      box && !stato.inCorso && evento.touches.length === 1 && box.scrollTop <= 0
        ? evento.touches[0].clientY
        : null
  }

  function muovi(evento) {
    if (inizio === null) return
    // the list scrolled instead: it is no pull
    if (contenitore.value?.scrollTop > 0) {
      annulla()
      return
    }
    stato.distanza = tirata(evento.touches[0].clientY - inizio)
    stato.pronta = stato.distanza >= SOGLIA_TIRATA
    stato.trascinando = stato.distanza > 0
  }

  async function su() {
    if (inizio === null) return
    inizio = null
    stato.trascinando = false
    if (!stato.pronta) {
      stato.distanza = 0
      return
    }
    stato.pronta = false
    stato.inCorso = true
    stato.distanza = SOGLIA_TIRATA
    try {
      await aggiorna()
    } finally {
      stato.inCorso = false
      stato.distanza = 0
    }
  }

  // the phone took the gesture back (a call, a swipe of the system): no reload
  function annulla() {
    inizio = null
    stato.trascinando = false
    if (stato.inCorso) return
    stato.distanza = 0
    stato.pronta = false
  }

  const ascolti = [
    ['touchstart', giu],
    ['touchmove', muovi],
    ['touchend', su],
    ['touchcancel', annulla],
  ]
  let box = null
  onMounted(() => {
    box = contenitore.value
    for (const [evento, fn] of ascolti) {
      box?.addEventListener(evento, fn, { passive: true })
    }
  })
  onBeforeUnmount(() => {
    for (const [evento, fn] of ascolti) box?.removeEventListener(evento, fn)
  })
  return stato
}
