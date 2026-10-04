// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A tooltip only where a pointer rests over things (src/utils/puntatore.js)
import { DOMANDA, siPosaIn } from '@/utils/puntatore'

function finestra(siPosa) {
  return {
    matchMedia: (domanda) => ({ matches: domanda === DOMANDA && siPosa }),
  }
}

describe('a pointer that rests', () => {
  it('asks whether any pointer of the screen hovers, a pen or a mouse too', () => {
    expect(DOMANDA).toBe('(any-hover: hover)')
  })

  it('is there on a computer, not on a phone touched', () => {
    expect(siPosaIn(finestra(true))).toBe(true)
    expect(siPosaIn(finestra(false))).toBe(false)
  })

  it('keeps the tooltips where the browser cannot say', () => {
    expect(siPosaIn(null)).toBe(true)
    expect(siPosaIn({})).toBe(true)
  })
})
