// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  prossimi,
  qualcosaDaDire,
  scadenza,
  ultimo,
  ultimoMessaggio,
} from '@/utils/riepilogo'

const adesso = new Date('2026-10-06T12:00:00')

const appuntamenti = [
  { name: 'a1', starts_on: '2026-10-20 09:00:00', status: 'Scheduled' },
  { name: 'a2', starts_on: '2026-10-08 10:00:00', status: 'Confirmed' },
  { name: 'a3', starts_on: '2026-10-07 10:00:00', status: 'Cancelled' },
  { name: 'a4', starts_on: '2026-10-09 10:00:00', status: 'Scheduled' },
  { name: 'a5', starts_on: '2026-10-30 10:00:00', status: 'Scheduled' },
  { name: 'p1', starts_on: '2026-10-01 10:00:00', status: 'Completed' },
  { name: 'p2', starts_on: '2026-10-05 10:00:00', status: 'Cancelled' },
  { name: 'p3', starts_on: '2026-09-20 10:00:00', status: 'No Show' },
]

describe('prossimi', () => {
  it('names the ones to come, the soonest first, never a cancelled one', () => {
    expect(prossimi(appuntamenti, adesso).map((a) => a.name)).toEqual([
      'a2',
      'a4',
      'a1',
    ])
  })

  it('names as many as asked, and none of nothing', () => {
    expect(prossimi(appuntamenti, adesso, 1).map((a) => a.name)).toEqual(['a2'])
    expect(prossimi([], adesso)).toEqual([])
    expect(prossimi(null, adesso)).toEqual([])
  })

  it('leaves out what is over and what has no moment', () => {
    const fatti = [
      { name: 'x', starts_on: '2026-10-06 13:00:00', status: 'Completed' },
      { name: 'y', starts_on: '', status: 'Scheduled' },
      { name: 'z', starts_on: '2026-10-06 12:00:00', status: 'Scheduled' },
    ]
    expect(prossimi(fatti, adesso).map((a) => a.name)).toEqual(['z'])
  })
})

describe('ultimo', () => {
  it('is the last before now however it went, not a cancelled one', () => {
    expect(ultimo(appuntamenti, adesso).name).toBe('p1')
  })

  it('is nothing for somebody who never came', () => {
    expect(ultimo(appuntamenti.slice(0, 5), adesso)).toBeNull()
    expect(ultimo([], adesso)).toBeNull()
  })
})

describe('ultimoMessaggio', () => {
  it('is what the person carries', () => {
    expect(
      ultimoMessaggio({
        last_conversation_on: '2026-10-06 09:30:00',
        last_conversation_channel: 'WhatsApp',
        last_conversation_direction: 'Incoming',
        last_conversation_preview: '  Posso spostare a giovedì?  ',
        conversation_unread: 1,
      }),
    ).toEqual({
      canale: 'WhatsApp',
      loro: true,
      testo: 'Posso spostare a giovedì?',
      quando: '2026-10-06 09:30:00',
      daLeggere: true,
    })
  })

  it('from here, and read', () => {
    const fatto = ultimoMessaggio({
      last_conversation_on: '2026-10-06 09:30:00',
      last_conversation_channel: 'Email',
      last_conversation_direction: 'Outgoing',
      conversation_unread: 0,
    })
    expect([fatto.loro, fatto.daLeggere, fatto.testo]).toEqual([
      false,
      false,
      '',
    ])
  })

  it('is nothing where nobody ever wrote', () => {
    expect(ultimoMessaggio({})).toBeNull()
    expect(ultimoMessaggio(null)).toBeNull()
  })
})

describe('scadenza', () => {
  it('says late, today or later against the centre’s today', () => {
    expect(scadenza('2026-10-05 18:00:00', '2026-10-06')).toBe('late')
    expect(scadenza('2026-10-06 18:00:00', '2026-10-06')).toBe('today')
    expect(scadenza('2026-10-07', '2026-10-06')).toBe('later')
  })

  it('says nothing of a task without a day', () => {
    expect(scadenza(null, '2026-10-06')).toBeNull()
    expect(scadenza('', '2026-10-06')).toBeNull()
  })
})

describe('qualcosaDaDire', () => {
  it('is false only when every part is empty', () => {
    expect(qualcosaDaDire()).toBe(false)
    expect(qualcosaDaDire({ righe: {} })).toBe(false)
    expect(qualcosaDaDire({ righe: { tasks: { count: 1 } } })).toBe(true)
    expect(qualcosaDaDire({ appuntamenti: [{ name: 'a' }] })).toBe(true)
    expect(qualcosaDaDire({ ultimoAppuntamento: { name: 'p' } })).toBe(true)
    expect(qualcosaDaDire({ messaggio: { testo: 'Ciao' } })).toBe(true)
  })
})
