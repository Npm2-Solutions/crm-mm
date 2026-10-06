// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// DottorCloud's service worker, over /crm (crm/notifiche/spinta.py). It does two
// things: shows a notification the server sent, and opens the page it points to
// when it is touched. It keeps nothing in a cache and answers no request of the
// page: the app is always the server's.

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) =>
  event.waitUntil(self.clients.claim()),
)

self.addEventListener('push', (event) => {
  let dati = {}
  try {
    dati = event.data ? event.data.json() : {}
  } catch {
    dati = { body: event.data ? event.data.text() : '' }
  }
  const url = dati.url || '/crm'
  event.waitUntil(
    self.registration.showNotification(dati.title || 'DottorCloud', {
      body: dati.body || '',
      tag: dati.tag || undefined,
      // a conversation's newer message takes the older one's place, and rings
      renotify: Boolean(dati.tag),
      icon: dati.icon || undefined,
      badge: dati.badge || undefined,
      data: { url },
    }),
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const indirizzo = new URL(
    event.notification.data?.url || '/crm',
    self.location.origin,
  )
  event.waitUntil(apri(indirizzo))
})

// DottorCloud open somewhere: brought forward first, while the touch still
// counts (a browser lets a window come forward only right after it), then told
// where to go, without loading it again. A page that does not answer - asleep
// on a phone, a version from before this one - is taken there; none open, a
// new window
async function apri(indirizzo) {
  const finestre = await self.clients.matchAll({
    type: 'window',
    includeUncontrolled: true,
  })
  const aperta = finestre.find(
    (finestra) =>
      new URL(finestra.url).origin === indirizzo.origin &&
      new URL(finestra.url).pathname.startsWith('/crm'),
  )
  if (!aperta) return self.clients.openWindow(indirizzo.href)
  const davanti = (await aperta.focus().catch(() => null)) || aperta
  if (await vaDaSe(davanti, indirizzo)) return
  const portata = await davanti.navigate?.(indirizzo.href).catch(() => null)
  if (!portata) return self.clients.openWindow(indirizzo.href)
}

// How long a page has to say it went there by itself (main.js answers at once)
const ATTESA = 2500

// The page is told where to go, and answers on the port it is handed
function vaDaSe(finestra, indirizzo) {
  return new Promise((risolvi) => {
    const canale = new MessageChannel()
    const scaduta = setTimeout(() => risolvi(false), ATTESA)
    canale.port1.onmessage = () => {
      clearTimeout(scaduta)
      risolvi(true)
    }
    finestra.postMessage(
      {
        tipo: 'apri',
        url: indirizzo.pathname + indirizzo.search + indirizzo.hash,
      },
      [canale.port2],
    )
  })
}
