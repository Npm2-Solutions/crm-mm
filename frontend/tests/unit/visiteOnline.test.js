// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// Online visits: the staff's link, and when the person enters from the area.
import { describe, expect, it, vi } from 'vitest'
import {
  apriLaStanza,
  prossimoCambioDellaVisita,
  statoDellaVisita,
} from '@/area/visitaOnline'
import {
  avviaLaVisita,
  linkDellaVisita,
  linkValido,
  statoDellaVisitaOnline,
} from '@/utils/visiteOnline'

const stanza = 'https://video.example.eu/abcdefghijklmnopqrstuvwx'

describe('linkDellaVisita', () => {
  it('gives an https room of an appointment not cancelled', () => {
    expect(linkDellaVisita({ video_link: stanza })).toBe(stanza)
    expect(linkDellaVisita({ video_link: ` ${stanza} ` })).toBe(stanza)
    expect(
      linkDellaVisita({ video_link: stanza, status: 'Cancelled' }),
    ).toBeNull()
    expect(linkDellaVisita({ video_link: 'http://x.eu/a' })).toBeNull()
    expect(linkDellaVisita({ video_link: 'javascript:alert(1)' })).toBeNull()
    expect(linkDellaVisita({})).toBeNull()
    expect(linkDellaVisita(null)).toBeNull()
  })

  it('checks a link the way the server does', () => {
    expect(linkValido('https://meet.google.com/abc-defg-hij')).toBe(true)
    expect(linkValido('https://')).toBe(false)
    expect(linkValido('https://a b.eu')).toBe(false)
    expect(linkValido('')).toBe(false)
  })
})

describe('statoDellaVisitaOnline', () => {
  it('starts it, or says it has no link yet', () => {
    expect(statoDellaVisitaOnline({ video_link: stanza })).toBe('avvia')
    expect(statoDellaVisitaOnline({ online_visit: true })).toBe('senza')
    expect(statoDellaVisitaOnline({ online_visit: false })).toBeNull()
    expect(
      statoDellaVisitaOnline({ online_visit: true, status: 'Cancelled' }),
    ).toBeNull()
  })
})

describe('avviaLaVisita', () => {
  it('opens the room in a tab of its own, never a link that is not one', () => {
    const finestra = { open: vi.fn() }
    expect(avviaLaVisita(stanza, finestra)).toBe(true)
    expect(finestra.open).toHaveBeenCalledWith(stanza, '_blank', 'noopener')
    expect(avviaLaVisita('ftp://x', finestra)).toBe(false)
    expect(finestra.open).toHaveBeenCalledTimes(1)
  })
})

const fra = (apre, chiude, extra = {}) => ({
  online: true,
  online_visit: { opens_in: apre, closes_in: chiude, opens_at: '09:45' },
  ...extra,
})

describe('statoDellaVisita', () => {
  it('opens a quarter of an hour before, closes at the end', () => {
    expect(statoDellaVisita(fra(600, 4200), 0)).toBe('presto')
    expect(statoDellaVisita(fra(600, 4200), 600_000)).toBe('aperta')
    expect(statoDellaVisita(fra(0, 4200), 0)).toBe('aperta')
    expect(statoDellaVisita(fra(0, 4200), 4_200_000)).toBeNull()
  })

  it('says when the room is missing, nothing when it is not online', () => {
    expect(statoDellaVisita({ online: true }, 0)).toBe('senza')
    expect(statoDellaVisita({ online: true, hidden: true }, 0)).toBeNull()
    expect(statoDellaVisita({ online: false }, 0)).toBeNull()
    expect(statoDellaVisita(fra(0, 10, { status: 'Cancelled' }), 0)).toBeNull()
    expect(statoDellaVisita(null, 0)).toBeNull()
  })

  it('looks again when it opens, then when it closes', () => {
    expect(prossimoCambioDellaVisita(fra(600, 4200), 0)).toBe(600_000)
    expect(prossimoCambioDellaVisita(fra(600, 4200), 700_000)).toBe(3_500_000)
    expect(prossimoCambioDellaVisita(fra(600, 4200), 4_300_000)).toBeNull()
    expect(prossimoCambioDellaVisita({ online: true }, 0)).toBeNull()
  })
})

describe('apriLaStanza', () => {
  it('fills the tab opened at the tap, else goes there', () => {
    const scheda = { closed: false, location: { href: '' } }
    expect(apriLaStanza(stanza, scheda)).toBe(true)
    expect(scheda.location.href).toBe(stanza)
    const finestra = { location: { assign: vi.fn() } }
    expect(apriLaStanza(stanza, null, finestra)).toBe(true)
    expect(finestra.location.assign).toHaveBeenCalledWith(stanza)
  })

  it('closes the tab on anything that is not a room', () => {
    const scheda = { closed: false, close: vi.fn(), location: { href: '' } }
    expect(apriLaStanza('http://x.eu', scheda)).toBe(false)
    expect(scheda.close).toHaveBeenCalled()
    expect(scheda.location.href).toBe('')
  })
})
