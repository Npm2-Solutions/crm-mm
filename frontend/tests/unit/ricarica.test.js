// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A part that does not arrive loads the page again: once, and only online.
import { daRicaricare } from '@/utils/ricarica'

describe('loading the page again when a part does not arrive', () => {
  const ora = 1_000_000

  it('loads it again, online, the first time', () => {
    expect(daRicaricare({ ora, ultima: 0, inRete: true })).toBe(true)
  })

  it('never twice in half a minute: the part is missing for good', () => {
    expect(daRicaricare({ ora, ultima: ora - 5_000, inRete: true })).toBe(false)
    expect(daRicaricare({ ora, ultima: ora - 29_999, inRete: true })).toBe(
      false,
    )
    expect(daRicaricare({ ora, ultima: ora - 30_000, inRete: true })).toBe(true)
  })

  it('never without the network: the browser would show its own error page', () => {
    expect(daRicaricare({ ora, ultima: 0, inRete: false })).toBe(false)
  })
})
