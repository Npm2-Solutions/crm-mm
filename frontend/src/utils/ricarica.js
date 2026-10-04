// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// A part of DottorCloud that does not arrive - a new version was published while
// the page was open, and its old parts are gone from the server - left a page,
// a dialog or a settings page that never opened, and nothing said why. The page
// loads again, once: only when the version it runs is gone (its first file no
// longer on the server), never in a loop, and never without the network (the
// line under the header says so, SenzaRete.vue), where loading again would show
// the browser's own error page instead of DottorCloud. Another site's module
// that does not arrive (the framework's telemetry, blocked by a browser or a
// firewall) is the same event, and must not load the page again.

const CHIAVE = 'dc-ricaricata'
const ATTESA = 30 * 1000

/** Whether to load the page again: online, and not done in the last half minute. */
export function daRicaricare({ ora, ultima, inRete }) {
  return Boolean(inRete) && !(ultima > 0 && ora - ultima < ATTESA)
}

/** Whether the version this page runs is gone from the server: its first file. */
async function versioneSostituita() {
  const ingresso = document.querySelector(
    'script[type="module"][src*="/assets/crm/frontend/"]',
  )?.src
  if (!ingresso) return false
  try {
    const risposta = await fetch(ingresso, {
      method: 'HEAD',
      cache: 'no-store',
    })
    return risposta.status === 404
  } catch {
    // no answer at all: the network, not a new version
    return false
  }
}

export function ricaricaSeManca() {
  let inCorso = false
  window.addEventListener('vite:preloadError', async () => {
    if (inCorso) return
    inCorso = true
    try {
      const ora = Date.now()
      let ultima = 0
      try {
        ultima = Number(sessionStorage.getItem(CHIAVE)) || 0
      } catch {
        // a browser that keeps nothing: below, it is not loaded again
      }
      if (!daRicaricare({ ora, ultima, inRete: navigator.onLine !== false }))
        return
      if (!(await versioneSostituita())) return
      try {
        sessionStorage.setItem(CHIAVE, String(ora))
      } catch {
        // without a note of it, loading again could go on forever
        return
      }
      window.location.reload()
    } finally {
      inCorso = false
    }
  })
}
