// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// Notifications on a browser that colleagues share (composables/spinta.js): the
// device follows whoever signs in, and a logout lets it go, against a server
// that keeps one row per subscription as crm/notifiche/spinta.py does.
import { createHash } from 'node:crypto'
import { attiva, lascia, sincronizza } from '@/composables/spinta'

// the key a browser subscribes with (any P-256 point the browser takes)
const CHIAVE =
  'BP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A8'
const ANNA = 'anna@centro.it'
const BRUNO = 'bruno@centro.it'

const sessione = vi.hoisted(() => ({ user: null }))
// the server: whose each subscription is, by its endpoint's fingerprint, what
// it was asked, and whether it refuses (down, the session already gone)
const server = vi.hoisted(() => ({
  righe: new Map(),
  chiesto: [],
  rifiuta: false,
}))

vi.mock('@/stores/session', () => ({ sessionStore: () => sessione }))
vi.mock('frappe-ui', () => ({
  call: async (metodo, argomenti = {}) => {
    server.chiesto.push(metodo)
    if (server.rifiuta) throw new Error('502 Bad Gateway')
    const dispositivi = () =>
      [...server.righe]
        .filter(([, utente]) => utente === sessione.user)
        .map(([endpoint_hash]) => ({ endpoint_hash }))
    if (metodo === 'crm.notifiche.spinta.subscribe') {
      const { endpoint } = JSON.parse(argomenti.subscription)
      // a browser somebody else had turned on becomes this person's
      server.righe.set(impronta(endpoint), sessione.user)
    } else if (metodo === 'crm.notifiche.spinta.unsubscribe') {
      // only the session's own
      if (server.righe.get(argomenti.endpoint_hash) === sessione.user)
        server.righe.delete(argomenti.endpoint_hash)
    }
    return { public_key: CHIAVE, devices: dispositivi() }
  },
}))

function impronta(endpoint) {
  return createHash('sha256').update(endpoint).digest('hex')
}

// the browser: one service worker, its subscription when it has one
const browser = { abbonamento: null, fatti: 0 }
function nuovoAbbonamento() {
  browser.fatti += 1
  const abbonamento = {
    endpoint: `https://fcm.googleapis.com/fcm/send/dispositivo-${browser.fatti}`,
    options: {},
    async unsubscribe() {
      if (browser.abbonamento === abbonamento) browser.abbonamento = null
      return true
    },
    toJSON() {
      return { endpoint: this.endpoint, keys: { p256dh: 'p', auth: 'a' } }
    },
  }
  return abbonamento
}
const registrazione = {
  pushManager: {
    getSubscription: async () => browser.abbonamento,
    subscribe: async () => (browser.abbonamento = nuovoAbbonamento()),
  },
}

// whose the server says this browser's subscription is
function diChi() {
  return server.righe.get(impronta(browser.abbonamento.endpoint)) || null
}

function entra(utente) {
  sessione.user = utente
  server.chiesto.length = 0
}

beforeAll(() => {
  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: {
      register: async () => registrazione,
      ready: Promise.resolve(registrazione),
      getRegistration: async () => registrazione,
    },
  })
  window.PushManager = function PushManager() {}
  window.Notification = {
    permission: 'granted',
    requestPermission: async () => 'granted',
  }
})

afterAll(() => {
  delete navigator.serviceWorker
  delete window.PushManager
  delete window.Notification
})

beforeEach(() => {
  localStorage.clear()
  server.righe.clear()
  server.rifiuta = false
  browser.abbonamento = null
})

describe('the device follows whoever signs in', () => {
  it('is handed to each colleague who signs in after another, every time', async () => {
    // Anna turns them on, and opens DottorCloud again another day
    entra(ANNA)
    await attiva(CHIAVE)
    entra(ANNA)
    await sincronizza()
    expect(diChi()).toBe(ANNA)

    // Bruno signs in on the same browser: the server is asked, and hands it over
    entra(BRUNO)
    await sincronizza()
    expect(diChi()).toBe(BRUNO)

    // Anna again: asked as well, not «already synced» by a memo of hers
    entra(ANNA)
    await sincronizza()
    expect(server.chiesto).toContain('crm.notifiche.spinta.get_push')
    expect(diChi()).toBe(ANNA)
  })

  it('asks nothing of the server when it is already the one signed in', async () => {
    entra(ANNA)
    await attiva(CHIAVE)
    entra(ANNA)
    await sincronizza()
    expect(server.chiesto).toEqual([])
    expect(diChi()).toBe(ANNA)
  })

  it('takes away the memos older versions kept one per person', async () => {
    entra(ANNA)
    await attiva(CHIAVE)
    entra(BRUNO)
    await sincronizza()
    // what an older version left: Anna's memo, still equal to the subscription
    localStorage.setItem(
      `crm-spinta:${ANNA}`,
      impronta(browser.abbonamento.endpoint),
    )
    entra(ANNA)
    await sincronizza()
    expect(diChi()).toBe(ANNA)
    expect(localStorage.getItem(`crm-spinta:${ANNA}`)).toBeNull()
    expect(localStorage.getItem('crm-spinta')).toBe(
      `${ANNA}|${impronta(browser.abbonamento.endpoint)}`,
    )
  })

  it('stays out of a browser where they were never turned on', async () => {
    entra(ANNA)
    await sincronizza()
    expect(server.chiesto).toEqual([])
    expect(browser.abbonamento).toBeNull()
  })
})

describe('a logout lets the device go', () => {
  it('the server forgets it, and whoever signs in next is handed it', async () => {
    entra(ANNA)
    await attiva(CHIAVE)
    const prima = browser.abbonamento
    await lascia()
    // nobody's: nothing reaches the device
    expect(diChi()).toBeNull()
    expect(localStorage.getItem('crm-spinta')).toBeNull()
    // the browser kept its subscription, for Bruno's first opening
    expect(browser.abbonamento).toBe(prima)
    entra(BRUNO)
    await sincronizza()
    expect(diChi()).toBe(BRUNO)
  })

  it('the browser lets go of it when the server does not forget it', async () => {
    entra(ANNA)
    await attiva(CHIAVE)
    const segno = impronta(browser.abbonamento.endpoint)
    server.rifiuta = true
    await lascia()
    // nothing reaches the device: its push service now says it is gone, and
    // the server forgets the row at its next notification
    expect(browser.abbonamento).toBeNull()
    expect(server.righe.get(segno)).toBe(ANNA)
    expect(localStorage.getItem('crm-spinta')).toBeNull()
  })

  it('the browser lets go of somebody else’s, which the server does not forget for this session', async () => {
    // Anna's session ran out without a logout; Bruno signs in and is out again
    // before his first opening had synced the device
    entra(ANNA)
    await attiva(CHIAVE)
    entra(BRUNO)
    await lascia()
    expect(browser.abbonamento).toBeNull()
    expect(localStorage.getItem('crm-spinta')).toBeNull()
  })

  it('lets go of what the opening’s sync, still on its way, hands over', async () => {
    entra(ANNA)
    await attiva(CHIAVE)
    entra(ANNA)
    await sincronizza()
    // Bruno signs in, and out again while his first opening is still syncing
    entra(BRUNO)
    const apertura = sincronizza()
    await lascia()
    await apertura
    // nobody's: none of his notifications after he is out
    expect(diChi()).toBeNull()
    expect(localStorage.getItem('crm-spinta')).toBeNull()
  })

  it('asks nothing where the browser has no subscription', async () => {
    entra(ANNA)
    await lascia()
    expect(server.chiesto).toEqual([])
  })
})
