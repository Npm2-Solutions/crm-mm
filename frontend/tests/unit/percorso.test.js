import { describe, expect, it } from 'vitest'
import { NOMI, sottotitolo } from '@/utils/percorso'

const giorno = (iso) => `[${iso}]`
const t = (testo, args = []) =>
  testo.replace(/\{(\d)\}/g, (_, i) => String(args[Number(i)]))
const opzioni = { oggi: '2026-05-04', giorno, t }

describe("the person's journey", () => {
  it('names the five steps', () => {
    expect(Object.keys(NOMI)).toEqual([
      'arrived',
      'booked',
      'came',
      'after',
      'home',
    ])
  })

  it('says through what and when a step was done', () => {
    expect(
      sottotitolo(
        { state: 'done', detail: 'instagram', on: '2026-05-02 09:00' },
        opzioni,
      ),
    ).toBe('Instagram · [2026-05-02]')
    expect(sottotitolo({ state: 'done', on: '2026-05-02' }, opzioni)).toBe(
      '[2026-05-02]',
    )
  })

  it('says when the person is expected', () => {
    expect(
      sottotitolo({ state: 'current', expected: '2026-05-04 10:30' }, opzioni),
    ).toBe('Today, 10:30')
    expect(
      sottotitolo({ state: 'current', expected: '2026-05-06 09:00' }, opzioni),
    ).toBe('[2026-05-06], 09:00')
  })

  it('says nothing under what is still to come', () => {
    expect(sottotitolo({ state: 'current' }, opzioni)).toBe('')
    expect(sottotitolo({ state: 'next' }, opzioni)).toBe('')
    expect(sottotitolo(null, opzioni)).toBe('')
  })
})
