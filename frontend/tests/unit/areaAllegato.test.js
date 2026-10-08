// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The file the person attaches to a message to the centre: a photo or a PDF,
// five megabytes at most, said before it is sent.
import { describe, expect, it } from 'vitest'
import { MAX_BYTE, cosaNonVa, quantoPesa } from '@/area/allegato'

describe('cosaNonVa', () => {
  it('a photo or a PDF goes', () => {
    expect(
      cosaNonVa({ name: 'r.pdf', type: 'application/pdf', size: 10 }),
    ).toBe(null)
    expect(cosaNonVa({ name: 'IMG_1.HEIC', type: '', size: 10 })).toBe(null)
    expect(cosaNonVa({ name: 'foto', type: 'image/jpeg', size: 10 })).toBe(null)
    expect(cosaNonVa(null)).toBe(null)
  })

  it('anything else, or too big, does not', () => {
    expect(
      cosaNonVa({ name: 'a.exe', type: 'application/x-msdownload', size: 1 }),
    ).toBe('Only a photo or a PDF can be attached')
    expect(
      cosaNonVa({ name: 'a.pdf', type: 'application/pdf', size: MAX_BYTE + 1 }),
    ).toBe('The file is larger than {0} MB')
  })
})

describe('quantoPesa', () => {
  it('in KB, then in MB the Italian way', () => {
    expect(quantoPesa(200)).toBe('1 KB')
    expect(quantoPesa(850 * 1024)).toBe('850 KB')
    expect(quantoPesa(2.4 * 1024 * 1024)).toBe('2,4 MB')
    expect(quantoPesa(2.4 * 1024 * 1024, 'en-GB')).toBe('2.4 MB')
  })
})
