// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt
import { describe, expect, it } from 'vitest'
import {
  ASPETTI,
  aspetto,
  conteggio,
  orario,
  sezioneDi,
  sezioni,
  soloTesto,
} from '@/utils/notifiche'

const ADESSO = '2026-10-02 10:30:00'

describe('how a kind looks', () => {
  it('gives every kind a category of the design system and an icon', () => {
    const categorie = [
      'brand',
      'amber',
      'blue',
      'violet',
      'green',
      'rose',
      'gray',
    ]
    for (const [kind, look] of Object.entries(ASPETTI)) {
      expect(categorie, kind).toContain(look.colore)
      expect(look.icona, kind).toBeTruthy()
      expect(look.parola, kind).toBeTruthy()
    }
  })

  it('draws WhatsApp in its green and a mention in the notes amber', () => {
    expect(aspetto('whatsapp')).toMatchObject({ colore: 'green' })
    expect(aspetto('mention')).toMatchObject({ colore: 'amber' })
  })

  it('draws what it does not know as a plain notification', () => {
    expect(aspetto('something new')).toBe(ASPETTI.other)
    expect(aspetto(undefined)).toBe(ASPETTI.other)
  })
})

describe('the day a notification is filed under', () => {
  it('today, yesterday, this week, earlier', () => {
    expect(sezioneDi('2026-10-02 08:00:00', ADESSO)).toBe('today')
    expect(sezioneDi('2026-10-01 23:59:00', ADESSO)).toBe('yesterday')
    expect(sezioneDi('2026-09-27 12:00:00', ADESSO)).toBe('week')
    expect(sezioneDi('2026-09-25 12:00:00', ADESSO)).toBe('older')
  })

  it('a moment it cannot read is filed with the old ones', () => {
    expect(sezioneDi('', ADESSO)).toBe('older')
  })
})

describe('the days of the list', () => {
  const righe = [
    { name: 'a', creation: '2026-10-02 09:00:00' },
    { name: 'b', creation: '2026-10-02 07:00:00' },
    { name: 'c', creation: '2026-09-20 07:00:00' },
  ]

  it('keeps the order, a day only when it has some', () => {
    const giorni = sezioni(righe, ADESSO)
    expect(giorni.map((g) => g.key)).toEqual(['today', 'older'])
    expect(giorni[0].rows.map((r) => r.name)).toEqual(['a', 'b'])
    expect(giorni[1].label).toBe('Earlier')
  })

  it('cuts the days on the moment it is given', () => {
    // the server's 23:30 is already tomorrow on the reader's clock
    const giorni = sezioni(
      [{ name: 'x', creation: '2026-10-01 23:30:00' }],
      ADESSO,
      () => '2026-10-02 00:30:00',
    )
    expect(giorni[0].key).toBe('today')
  })

  it('has no days without rows', () => {
    expect(sezioni([], ADESSO)).toEqual([])
    expect(sezioni(null, ADESSO)).toEqual([])
  })
})

describe('the time on a row', () => {
  it('is the clock today and yesterday', () => {
    expect(orario('2026-10-02 09:05:00', ADESSO, 'it-IT')).toBe('09:05')
    expect(orario('2026-10-01 18:40:00', ADESSO, 'it-IT')).toBe('18:40')
  })

  it('is the weekday and the clock this week', () => {
    expect(orario('2026-09-28 14:00:00', ADESSO, 'it-IT')).toBe('lun 14:00')
  })

  it('is the date before, with the year once it is another', () => {
    expect(orario('2026-09-12 14:00:00', ADESSO, 'it-IT')).toBe('12 set')
    expect(orario('2025-12-30 14:00:00', ADESSO, 'it-IT')).toBe('30 dic 2025')
  })

  it('says nothing of a moment it cannot read', () => {
    expect(orario('', ADESSO, 'it-IT')).toBe('')
  })
})

describe('the words without their markup', () => {
  it('keeps the names and turns the entities back', () => {
    expect(
      soloTesto('<b>Anna</b> ti ha menzionato su <b>Rossi &amp; figli</b>'),
    ).toBe('Anna ti ha menzionato su Rossi & figli')
  })

  it('is nothing for nothing', () => {
    expect(soloTesto(null)).toBe('')
  })
})

describe('the count on the sidebar', () => {
  it('is empty with nothing to read, the number, then 99+', () => {
    expect(conteggio(0)).toBe('')
    expect(conteggio(undefined)).toBe('')
    expect(conteggio(7)).toBe('7')
    expect(conteggio(140)).toBe('99+')
  })
})
