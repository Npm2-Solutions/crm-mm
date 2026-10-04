// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import { pezzi, segnaInHtml } from '@/utils/segnaposti'

describe('pezzi', () => {
  it('cuts a template into words and numbered places', () => {
    expect(pezzi('Ciao {{1}}, a {{ 2 }}!')).toEqual([
      { testo: 'Ciao ' },
      { posto: 1 },
      { testo: ', a ' },
      { posto: 2 },
      { testo: '!' },
    ])
  })

  it('keeps a text without places whole, and an empty one empty', () => {
    expect(pezzi('Buongiorno')).toEqual([{ testo: 'Buongiorno' }])
    expect(pezzi('')).toEqual([])
    expect(pezzi(null)).toEqual([])
  })

  it('starts and ends on a place', () => {
    expect(pezzi('{{1}} e {{1}}')).toEqual([
      { posto: 1 },
      { testo: ' e ' },
      { posto: 1 },
    ])
  })
})

describe('segnaInHtml', () => {
  it('draws each place as a chip with its number', () => {
    expect(segnaInHtml('<p>Ciao {{1}}</p>', 'chip')).toBe(
      '<p>Ciao <span class="chip">1</span></p>',
    )
  })

  it('leaves other braces alone', () => {
    expect(segnaInHtml('{{nome}} {1}', 'chip')).toBe('{{nome}} {1}')
  })
})
