/**
 * Whether the list of people stays beside the record you are reading.
 *
 * A per-person choice, not a setting on the site: on a wide screen the column
 * turns the record page into the third pane of an inbox, and on a laptop it
 * takes a third of the room the conversation needs. Both are right, for
 * different people on different days, so it is a switch with a memory.
 *
 * Kept in the browser rather than on the user record because it is worth
 * nothing to anybody else and a round trip to remember a toggle is a round trip
 * too many.
 */
import { ref, watch } from 'vue'

const KEY = 'crm:people-sidebar'
const WAITING = 'crm:people-sidebar-waiting'

function remembered(key, fallback = false) {
  try {
    const held = window.localStorage.getItem(key)
    return held === null ? fallback : held === '1'
  } catch {
    // a private window, or site data turned off: the switch still works, it
    // just forgets
    return fallback
  }
}

const open = ref(remembered(KEY))
const waitingOnly = ref(remembered(WAITING))

function keep(key, value) {
  try {
    window.localStorage.setItem(key, value ? '1' : '0')
  } catch {
    // nothing to do: see above
  }
}

watch(open, (value) => keep(KEY, value))
watch(waitingOnly, (value) => keep(WAITING, value))

export function usePeopleSidebar() {
  return {
    open,
    waitingOnly,
    toggle: () => (open.value = !open.value),
  }
}
