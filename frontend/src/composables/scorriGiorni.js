// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The agenda's day on a phone changes with a finger, as a phone's own calendar
 * does: the day's list swiped to the left is the next day, to the right the
 * day before; the week's strip swiped moves a week. It changed only by the
 * days' buttons and the arrows.
 *
 * Only a sideways swipe counts: a finger going mostly up or down scrolls the
 * list (or pulls it to reload), and one that starts at the screen's edge is the
 * phone's own back.
 */
import { onBeforeUnmount, onMounted, watch } from 'vue'

// how far the finger goes for the day to change, unless it is a quick flick
export const SOGLIA_SCORRI = 60
// the screen's edges belong to the phone's back gesture
const BORDO = 24

/**
 * Where a finger that moved `dx`, `dy` pixels in `dt` milliseconds takes the
 * day: 1 (the next, the finger went left), -1 (the one before), or null (no
 * sideways swipe: a scroll, a twitch).
 */
export function direzioneDelGesto({ dx, dy, dt = 0 }) {
  if (Math.abs(dx) < Math.abs(dy) * 1.5) return null
  const colpo = dt > 0 && Math.abs(dx) > 30 && Math.abs(dx) / dt > 0.4
  if (Math.abs(dx) < SOGLIA_SCORRI && !colpo) return null
  return dx < 0 ? 1 : -1
}

/**
 * Follows a finger on `elemento` (a ref to the box): a sideways swipe calls
 * `sposta(1)` or `sposta(-1)`. With `segue`, the box goes a little with the
 * finger while it swipes, and back when it lets go.
 */
export function useScorriGiorni(
  elemento,
  sposta,
  { segue = false, win = window, ora = () => win.performance.now() } = {},
) {
  let inizio = null
  let laterale = false

  function riporta() {
    const el = elemento.value
    if (!segue || !el) return
    el.style.transition = 'transform 160ms ease-out'
    el.style.transform = ''
    win.setTimeout(() => {
      el.style.transition = ''
    }, 170)
  }

  function giu(evento) {
    inizio = null
    laterale = false
    if (evento.touches.length !== 1) return
    const tocco = evento.touches[0]
    if (tocco.clientX < BORDO || tocco.clientX > win.innerWidth - BORDO) return
    inizio = { x: tocco.clientX, y: tocco.clientY, t: ora() }
  }

  function muovi(evento) {
    if (!inizio) return
    const tocco = evento.touches[0]
    const dx = tocco.clientX - inizio.x
    const dy = tocco.clientY - inizio.y
    if (!laterale) {
      // up or down first: the list scrolls, nothing here
      if (Math.abs(dy) > 10 && Math.abs(dy) >= Math.abs(dx)) {
        inizio = null
        return
      }
      if (Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        laterale = true
      }
    }
    if (laterale && segue && elemento.value) {
      elemento.value.style.transition = 'none'
      elemento.value.style.transform = `translateX(${dx * 0.35}px)`
    }
  }

  function su(evento) {
    if (!inizio) return
    const tocco = evento.changedTouches?.[0]
    const partenza = inizio
    inizio = null
    if (!laterale || !tocco) return
    riporta()
    const verso = direzioneDelGesto({
      dx: tocco.clientX - partenza.x,
      dy: tocco.clientY - partenza.y,
      dt: ora() - partenza.t,
    })
    if (verso) sposta(verso)
  }

  function annulla() {
    if (laterale) riporta()
    inizio = null
    laterale = false
  }

  const ascolti = [
    ['touchstart', giu],
    ['touchmove', muovi],
    ['touchend', su],
    ['touchcancel', annulla],
  ]
  let box = null
  function segui(nuovo) {
    if (nuovo === box) return
    for (const [nome, fn] of ascolti) box?.removeEventListener(nome, fn)
    box = nuovo || null
    for (const [nome, fn] of ascolti) {
      box?.addEventListener(nome, fn, { passive: true })
    }
  }
  watch(elemento, segui, { flush: 'post' })
  onMounted(() => segui(elemento.value))
  onBeforeUnmount(() => segui(null))
}
