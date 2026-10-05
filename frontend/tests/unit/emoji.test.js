// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { gemoji } from 'gemoji'
import { describe, expect, it } from 'vitest'
import parole from '@/assets/emoji/it.json'
import {
  caricaLeParole,
  cercaLeEmoji,
  chiave,
  paroleDi,
  semplice,
  testoDiRicerca,
  trova,
} from '@/utils/emoji'

const di = (emoji) => {
  const voce = gemoji.find((g) => g.emoji === emoji)
  return testoDiRicerca(
    [voce.description, ...voce.names, ...voce.tags],
    parole,
    voce.emoji,
  )
}

describe('the emoji in Italian', () => {
  it('finds an emoji by its Italian words, and still by its English ones', () => {
    expect(trova(di('😀'), 'sorriso')).toBe(true)
    expect(trova(di('🙏'), 'grazie')).toBe(true)
    expect(trova(di('❤️'), 'cuore')).toBe(true)
    expect(trova(di('🏥'), 'ospedale')).toBe(true)
    expect(trova(di('🇮🇹'), 'italia')).toBe(true)
    expect(trova(di('😄'), 'smile')).toBe(true)
    expect(trova(di('😀'), 'ospedale')).toBe(false)
  })

  it('compares without accents, case or the kind of apostrophe', () => {
    expect(semplice('Felicità')).toBe('felicita')
    expect(semplice('d’accordo')).toBe("d'accordo")
    expect(trova(di('😃'), 'felicita')).toBe(true)
    expect(trova(di('😃'), 'FELICITÀ')).toBe(true)
    expect(trova(di('👍'), "d'accordo")).toBe(true)
  })

  it('finds everything when nothing is typed', () => {
    expect(trova(di('😀'), '')).toBe(true)
    expect(trova(di('😀'), '   ')).toBe(true)
  })

  it('names each emoji, the variation selector or not', () => {
    expect(chiave('❤️')).toBe('❤')
    expect(paroleDi(parole, '❤️').nome).toBe('cuore rosso')
    expect(paroleDi(parole, '🙏')).toEqual(
      expect.objectContaining({ nome: 'mani giunte' }),
    )
    expect(paroleDi(parole, '🙏').parole).toContain('grazie')
    expect(paroleDi(parole, 'nessuna')).toEqual({ nome: '', parole: [] })
    expect(paroleDi(null, '🙏')).toEqual({ nome: '', parole: [] })
  })

  it('has the Italian name of every emoji the picker shows', () => {
    const senza = gemoji.filter((voce) => !paroleDi(parole, voce.emoji).nome)
    expect(senza.map((voce) => voce.emoji)).toEqual([])
  })

  it('fetches nothing for a reader in another language', async () => {
    await expect(caricaLeParole('en')).resolves.toEqual({})
    await expect(caricaLeParole('')).resolves.toEqual({})
  })
})

describe('the editor’s list, the closest first', () => {
  // as the editor's list has them: its English short name, the Italian words
  const voci = ['😀', '😺', '😊', '😄', '🙏', '❤️', '💙', '💔'].map((emoji) => {
    const voce = gemoji.find((g) => g.emoji === emoji)
    return {
      emoji,
      name: paroleDi(parole, emoji).nome,
      cerca: testoDiRicerca(voce.names, parole, emoji),
    }
  })
  const prima = (cercato) => cercaLeEmoji(voci, cercato)[0]?.emoji

  it('puts first the one named so, then one whose name has the word', () => {
    expect(prima('cuore rosso')).toBe('❤️')
    expect(prima('cuore')).toBe('❤️')
    expect(prima('sorriso')).toBe('😀')
  })

  it('then one with that very word, English short names included', () => {
    expect(prima('grazie')).toBe('🙏')
    expect(prima('smile')).toBe('😄')
  })

  it('keeps out what does not hold the word, and keeps all for nothing typed', () => {
    expect(cercaLeEmoji(voci, 'ospedale')).toEqual([])
    expect(cercaLeEmoji(voci, '')).toHaveLength(voci.length)
  })
})
