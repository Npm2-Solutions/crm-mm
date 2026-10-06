// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// When a page asks again for what it shows: the app back in sight after a
// while away, or its realtime connection back after a break. A phone puts the
// app it does not show to sleep, and what was said meanwhile - a message, a
// notification - never reached it.

/** Seconds out of sight after which a page asks again for what it shows. */
export const PAUSA = 15

/** Seconds within which a second reason to ask again is the same one: back in
 * sight and the connection back, together. */
export const INSIEME = 2

/** Whether a page that went out of sight at `nascostaDa` (ms) asks again now. */
export function daRiprendere(nascostaDa, adesso, pausa = PAUSA) {
  return nascostaDa != null && adesso - nascostaDa >= pausa * 1000
}

/** Whether asking again at `adesso` (ms) repeats the time asked at `ultima`. */
export function giaRipreso(ultima, adesso, insieme = INSIEME) {
  return ultima != null && adesso - ultima < insieme * 1000
}
