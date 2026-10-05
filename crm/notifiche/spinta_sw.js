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

// DottorCloud open somewhere: it goes there by itself, without reloading; else a
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
  if (aperta) {
    aperta.postMessage({
      tipo: 'apri',
      url: indirizzo.pathname + indirizzo.search + indirizzo.hash,
    })
    return aperta.focus()
  }
  return self.clients.openWindow(indirizzo.href)
}
