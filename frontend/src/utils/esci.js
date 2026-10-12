// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * What this browser keeps of a session after it, and what takes it away.
 *
 * Nothing about people outlives the page: what frappe-ui's resources fetch
 * stays in the page's memory (vite/frappeUi.js). Older versions kept a copy of
 * it in IndexedDB, a person's record and a list's names and numbers among it,
 * and no logout emptied it: on a computer that colleagues share, the next
 * session was drawn from the last one's people.
 */

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
