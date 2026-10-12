// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// What the browser keeps of a session after it, and the way out that takes it
// away.
import fs from 'node:fs'
import path from 'node:path'
import { COPIE_DI_FRAPPE_UI, esci, togliLeCopie } from '@/utils/esci'

const ANNA = 'anna@centro.it'

afterEach(() => {
  delete globalThis.indexedDB
  localStorage.clear()
  sessionStorage.clear()
})

describe('togliLeCopie', () => {
  it('deletes the database frappe-ui kept its copies in', () => {
    const tolti = []
    globalThis.indexedDB = { deleteDatabase: (nome) => tolti.push(nome) }
    togliLeCopie()
    expect(tolti).toEqual([COPIE_DI_FRAPPE_UI])
    // idb-keyval's own store, as the pinned version names it
    const idbKeyval = fs.readFileSync(
      path.resolve(
        import.meta.dirname,
        '../../node_modules/idb-keyval/dist/index.js',
      ),
      'utf8',
    )
    expect(idbKeyval).toContain(`createStore('${COPIE_DI_FRAPPE_UI}'`)
  })

  it('asks nothing of a browser without IndexedDB, or that refuses it', () => {
    expect(() => togliLeCopie()).not.toThrow()
    globalThis.indexedDB = {
      deleteDatabase: () => {
        throw new Error('SecurityError')
      },
    }
    expect(() => togliLeCopie()).not.toThrow()
  })
})

describe('esci', () => {
  // what a reception PC holds at the end of Anna's day
  function unaGiornata() {
    localStorage.setItem('crmAgenda', '{"vista":"giorno"}')
    localStorage.setItem('menuPiegato', 'true')
    localStorage.setItem(`emailBoxContent-${ANNA}-CRM Lead-CRM-LEAD-0001`, 'x')
    localStorage.setItem(
      'smsDraft-bruno@centro.it-CRM Lead-CRM-LEAD-0002',
      'Domani alle 9',
    )
    localStorage.setItem('eventNotificationAlerts', '[{"title":"Visita"}]')
    localStorage.setItem('crm-spinta', `${ANNA}|f1`)
    sessionStorage.setItem('fieldLayoutTab:CRM Lead:CRM-LEAD-0001', 'Dati')
  }

  it('first lets the device go, then ends the session, then clears', async () => {
    unaGiornata()
    const fatto = []
    globalThis.indexedDB = {
      deleteDatabase: (nome) => fatto.push(`deleteDatabase ${nome}`),
    }
    const risposta = await esci(
      async () => {
        // the session is still whole when the server is asked to end it
        expect(localStorage.getItem('eventNotificationAlerts')).not.toBeNull()
        fatto.push('logout')
        return 'ok'
      },
      {
        utenti: [ANNA],
        prima: async () => fatto.push('lascia'),
      },
    )
    expect(risposta).toBe('ok')
    expect(fatto).toEqual(['lascia', 'logout', 'deleteDatabase keyval-store'])
    // how the device is set stays; a colleague's drafts stay theirs
    expect(Object.keys(localStorage).sort()).toEqual([
      'crmAgenda',
      'menuPiegato',
      'smsDraft-bruno@centro.it-CRM Lead-CRM-LEAD-0002',
    ])
    expect(sessionStorage.length).toBe(0)
  })

  it('clears nothing when the server did not end the session', async () => {
    unaGiornata()
    const tolti = []
    globalThis.indexedDB = { deleteDatabase: (nome) => tolti.push(nome) }
    const rifiuto = new Error('502 Bad Gateway')
    await expect(
      esci(() => Promise.reject(rifiuto), { utenti: [ANNA] }),
    ).rejects.toBe(rifiuto)
    // the session goes on, and its draft is still its own
    expect(
      localStorage.getItem(`emailBoxContent-${ANNA}-CRM Lead-CRM-LEAD-0001`),
    ).toBe('x')
    expect(localStorage.length).toBe(6)
    expect(sessionStorage.length).toBe(1)
    expect(tolti).toEqual([])
  })

  it('goes on when the device could not be let go', async () => {
    unaGiornata()
    let uscita = false
    await esci(
      async () => {
        uscita = true
      },
      {
        utenti: [ANNA],
        prima: () => {
          throw new Error('no service worker')
        },
      },
    )
    expect(uscita).toBe(true)
    expect(localStorage.getItem('eventNotificationAlerts')).toBeNull()
  })

  it('logs out a browser that keeps nothing', async () => {
    const storage = Object.getOwnPropertyDescriptor(globalThis, 'localStorage')
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      get() {
        throw new Error('SecurityError')
      },
    })
    try {
      await expect(esci(async () => 'ok')).resolves.toBe('ok')
    } finally {
      if (storage) Object.defineProperty(globalThis, 'localStorage', storage)
      else delete globalThis.localStorage
    }
  })
})
