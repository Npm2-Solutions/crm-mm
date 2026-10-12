// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// Notifications on this device: what the browser can do, the server's key,
// whose the browser is, where a touched notification opens.
import {
  MEMORIA,
  chiaveDelServer,
  cosaSaFare,
  daChiedere,
  esadecimale,
  memoriaDi,
  memorieVecchie,
  percorsoDellApp,
  statoDelDispositivo,
} from '@/utils/spinta'

const PRONTO = {
  serviceWorker: true,
  pushManager: true,
  notification: true,
  permesso: 'default',
}

describe('statoDelDispositivo', () => {
  it('can receive them where the browser has what it takes', () => {
    expect(statoDelDispositivo(PRONTO)).toBe('pronto')
    expect(statoDelDispositivo({ ...PRONTO, permesso: 'granted' })).toBe(
      'pronto',
    )
  })

  it('an iPhone only from the app on the home screen', () => {
    expect(statoDelDispositivo({ ...PRONTO, ios: true })).toBe('installa-prima')
    // Safari in a tab has no PushManager: still «put it on the home screen»
    expect(
      statoDelDispositivo({ ...PRONTO, pushManager: false, ios: true }),
    ).toBe('installa-prima')
    expect(
      statoDelDispositivo({ ...PRONTO, ios: true, installata: true }),
    ).toBe('pronto')
  })

  it('says when they were refused, and when the browser cannot', () => {
    expect(statoDelDispositivo({ ...PRONTO, permesso: 'denied' })).toBe(
      'bloccato',
    )
    expect(statoDelDispositivo({ ...PRONTO, serviceWorker: false })).toBe(
      'non-supportato',
    )
  })
})

describe('cosaSaFare', () => {
  it('asks the browser', () => {
    const win = {
      navigator: { serviceWorker: {} },
      PushManager: function () {},
      Notification: { permission: 'granted' },
    }
    expect(cosaSaFare(win, { ios: true, installata: true })).toEqual({
      serviceWorker: true,
      pushManager: true,
      notification: true,
      permesso: 'granted',
      ios: true,
      installata: true,
    })
    expect(cosaSaFare({ navigator: {} })).toMatchObject({
      serviceWorker: false,
      pushManager: false,
      notification: false,
      permesso: 'default',
    })
  })
})

describe('chiaveDelServer', () => {
  it('turns base64url into the bytes the browser wants', () => {
    const chiave =
      'BP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A8'
    const byte = chiaveDelServer(chiave)
    expect(byte).toBeInstanceOf(Uint8Array)
    expect(byte.length).toBe(65)
    expect(byte[0]).toBe(4)
  })
})

describe('the memo of whose the browser is', () => {
  const ANNA = 'anna@centro.it'
  const BRUNO = 'bruno@centro.it'

  it('is one for the browser: who, and which subscription', () => {
    expect(MEMORIA).toBe('crm-spinta')
    expect(memoriaDi(ANNA, 'f1')).toBe('anna@centro.it|f1')
    expect(memoriaDi(null, '')).toBe('|')
  })

  it('asks the server unless it says this person, with this subscription', () => {
    expect(daChiedere(memoriaDi(ANNA, 'f1'), ANNA, 'f1')).toBe(false)
    // a colleague signed in after Anna: asked, and handed the device
    expect(daChiedere(memoriaDi(ANNA, 'f1'), BRUNO, 'f1')).toBe(true)
    // and Anna again after him: asked as well, never «already synced»
    expect(daChiedere(memoriaDi(BRUNO, 'f1'), ANNA, 'f1')).toBe(true)
    // another subscription (the site's key changed), or nobody remembered
    expect(daChiedere(memoriaDi(ANNA, 'f1'), ANNA, 'f2')).toBe(true)
    expect(daChiedere(null, ANNA, 'f1')).toBe(true)
  })

  it('finds the memos older versions kept one per person', () => {
    expect(
      memorieVecchie([
        'crm-spinta:anna@centro.it',
        'crm-spinta',
        'crm-spinta:bruno@centro.it',
        'crmAgenda',
      ]),
    ).toEqual(['crm-spinta:anna@centro.it', 'crm-spinta:bruno@centro.it'])
    expect(memorieVecchie(null)).toEqual([])
  })
})

describe('esadecimale', () => {
  it('writes a digest as the server does', () => {
    expect(esadecimale(new Uint8Array([0, 15, 255]).buffer)).toBe('000fff')
  })
})

describe('percorsoDellApp', () => {
  it('opens DottorCloud’s page, without /crm', () => {
    expect(percorsoDellApp('/crm/leads/CRM-LEAD-1?notifica=abc#activity')).toBe(
      '/leads/CRM-LEAD-1?notifica=abc#activity',
    )
    expect(percorsoDellApp('/crm')).toBe('/')
  })

  it('never another site, nor another page of this one', () => {
    expect(percorsoDellApp('https://example.com/crm/leads')).toBeNull()
    expect(percorsoDellApp('/app/crm-lead')).toBeNull()
    expect(percorsoDellApp('/crm-form/contatti')).toBeNull()
  })
})
