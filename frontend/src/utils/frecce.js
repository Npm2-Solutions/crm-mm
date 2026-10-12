// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The arrows in a group of options of which one is picked, as a radio group
 * takes them (WAI-ARIA APG): the next or the one before, round the ends, Home
 * and End to the first and the last. `qui` is the option the key was pressed
 * on, `quante` how many there are. The index of the option the key goes to, or
 * undefined for a key that moves nothing, which stays the browser's.
 */
export function dopoLaFreccia(tasto, qui, quante) {
  if (!(qui >= 0 && qui < quante)) return undefined
  switch (tasto) {
    case 'ArrowDown':
    case 'ArrowRight':
      return (qui + 1) % quante
    case 'ArrowUp':
    case 'ArrowLeft':
      return (qui - 1 + quante) % quante
    case 'Home':
      return 0
    case 'End':
      return quante - 1
    default:
      return undefined
  }
}
