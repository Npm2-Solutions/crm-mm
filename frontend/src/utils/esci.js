// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * What this browser keeps of a session after it, and the way out that takes
 * it away.
 *
 * Nothing about people outlives the page: what frappe-ui's resources fetch
 * stays in the page's memory (vite/frappeUi.js). Older versions kept a copy of
 * it in IndexedDB, a person's record and a list's names and numbers among it,
 * and no logout emptied it: on a computer that colleagues share, the next
 * session was drawn from the last one's people.
 *
 * Every logout goes through `esci`: the desk's and the tablet's handed to a
 * person (stores/session.js), the client area's (area/store.js). Whoever comes
 * next finds how the device is set, never what the last session wrote, was
 * writing or was looking at (utils/dopoLUscita.js).
 */
import { daTogliere } from '@/utils/dopoLUscita'

/** The database frappe-ui kept its copies in, before they stayed in the page. */
export const COPIE_DI_FRAPPE_UI = 'keyval-store'

/**
 * frappe-ui's copies that older versions left in this browser go. Nothing
 * waits for it: the browser deletes the database once no page of an older
 * version holds it open.
 */
export function togliLeCopie() {
  try {
    globalThis.indexedDB?.deleteDatabase(COPIE_DI_FRAPPE_UI)
  } catch {
    // a private window, site data blocked: nothing was kept there either
  }
}

// the keys of localStorage or sessionStorage that go (utils/dopoLUscita.js)
function svuota(nome, utenti) {
  try {
    const archivio = globalThis[nome]
    if (!archivio) return
    const chiavi = Array.from({ length: archivio.length }, (_, i) =>
      archivio.key(i),
    )
    for (const chiave of daTogliere(chiavi, utenti)) archivio.removeItem(chiave)
  } catch {
    // site data blocked: nothing was kept there either
  }
}

/**
 * Logs out, in this order:
 * - `prima`, while the session is still there: the desk lets this device's
 *   notifications go (composables/spinta.js `lascia`). Whatever happens to it,
 *   the logout goes on;
 * - `chiudi`, the server ending the session;
 * - once it has, frappe-ui's old copies, the drafts of `utenti` (whoever signs
 *   out: their user, and the email their drafts are kept under) and the app's
 *   keys that are no preference.
 *
 * When `chiudi` fails the session goes on, and nothing is taken away: its
 * drafts are still its own. Rejects then as `chiudi` did.
 */
export async function esci(chiudi, { utenti = [], prima } = {}) {
  if (prima) {
    try {
      await prima()
    } catch {
      // the device not let go: the session ends all the same
    }
  }
  const risposta = await chiudi()
  togliLeCopie()
  svuota('localStorage', utenti)
  svuota('sessionStorage', utenti)
  return risposta
}
