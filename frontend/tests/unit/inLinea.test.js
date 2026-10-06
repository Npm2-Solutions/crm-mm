import { describe, expect, it } from 'vitest'
import { daRiprendere, giaRipreso, INSIEME, PAUSA } from '@/utils/inLinea'

describe('back in touch: when a page asks again', () => {
  it('after a while out of sight, not after a glance away', () => {
    const via = 1_000_000
    expect(daRiprendere(via, via + PAUSA * 1000)).toBe(true)
    expect(daRiprendere(via, via + 60 * 60 * 1000)).toBe(true)
    expect(daRiprendere(via, via + PAUSA * 1000 - 1)).toBe(false)
    // never out of sight
    expect(daRiprendere(null, via)).toBe(false)
  })

  it('back in sight and the connection back together ask once', () => {
    const ora = 5_000_000
    expect(giaRipreso(null, ora)).toBe(false)
    expect(giaRipreso(ora, ora + INSIEME * 1000 - 1)).toBe(true)
    expect(giaRipreso(ora, ora + INSIEME * 1000)).toBe(false)
  })
})
