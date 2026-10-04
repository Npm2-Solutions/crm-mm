// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { ref } from 'vue'

/**
 * Whether the screen has a pointer that rests over things: a mouse, a
 * trackpad, a pen. A tooltip opens only on one (reka-ui's trigger leaves a
 * touch alone), so on a phone or a tablet touched a tooltip is only the cost
 * of what it mounts: a dozen components each, two thirds of a person's page.
 * The build draws frappe-ui's Tooltip, and a Button's tooltip, as their
 * trigger alone without one (frontend/vite/frappeUi.js).
 */
export const DOMANDA = '(any-hover: hover)'

/** Whether `win` has a pointer that rests; a browser that cannot say has. */
export function siPosaIn(win) {
  if (!win?.matchMedia) return true
  return win.matchMedia(DOMANDA).matches
}

export const siPosa = ref(
  siPosaIn(typeof window === 'undefined' ? null : window),
)

// a mouse plugged into a tablet brings them back
if (typeof window !== 'undefined' && window.matchMedia) {
  window
    .matchMedia(DOMANDA)
    .addEventListener?.('change', (evento) => (siPosa.value = evento.matches))
}
