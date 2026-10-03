// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The agenda's day changes with a sideways swipe, as a phone's calendar does.
import {
  SOGLIA_SCORRI,
  direzioneDelGesto,
  useScorriGiorni,
} from '@/composables/scorriGiorni'
import { createApp, h, ref } from 'vue'

describe('direzioneDelGesto', () => {
  it('takes a swipe to the left to the next day, to the right to the one before', () => {
    expect(direzioneDelGesto({ dx: -(SOGLIA_SCORRI + 10), dy: 5 })).toBe(1)
    expect(direzioneDelGesto({ dx: SOGLIA_SCORRI + 10, dy: -5 })).toBe(-1)
  })

  it('leaves a scroll and a twitch alone, takes a quick flick', () => {
    expect(direzioneDelGesto({ dx: -80, dy: 70 })).toBe(null)
    expect(direzioneDelGesto({ dx: -20, dy: 0 })).toBe(null)
    expect(direzioneDelGesto({ dx: -40, dy: 0, dt: 60 })).toBe(1)
    expect(direzioneDelGesto({ dx: -40, dy: 0, dt: 400 })).toBe(null)
  })
})

describe('useScorriGiorni', () => {
  let adesso = 0
  function monta(sposta) {
    const elemento = ref(null)
    const app = createApp({
      setup() {
        useScorriGiorni(elemento, sposta, {
          segue: true,
          win: { innerWidth: 390, setTimeout, performance: {} },
          ora: () => adesso,
        })
        return () => h('div', { ref: elemento })
      },
    })
    const radice = document.createElement('div')
    document.body.append(radice)
    app.mount(radice)
    return { box: elemento.value, smonta: () => app.unmount() }
  }

  function tocco(box, tipo, x, y) {
    const evento = new Event(tipo)
    evento.touches = x === undefined ? [] : [{ clientX: x, clientY: y }]
    evento.changedTouches = [{ clientX: x, clientY: y }]
    box.dispatchEvent(evento)
  }

  function trascina(box, da, a) {
    tocco(box, 'touchstart', da.x, da.y)
    for (let i = 1; i <= 5; i++) {
      adesso += 30
      tocco(
        box,
        'touchmove',
        da.x + ((a.x - da.x) * i) / 5,
        da.y + ((a.y - da.y) * i) / 5,
      )
    }
    const evento = new Event('touchend')
    evento.touches = []
    evento.changedTouches = [{ clientX: a.x, clientY: a.y }]
    box.dispatchEvent(evento)
  }

  it('moves a day for a swipe, and the box goes with the finger', () => {
    const sposta = vi.fn()
    const { box, smonta } = monta(sposta)
    tocco(box, 'touchstart', 300, 200)
    tocco(box, 'touchmove', 200, 205)
    expect(box.style.transform).toBe('translateX(-35px)')
    const fine = new Event('touchend')
    fine.touches = []
    fine.changedTouches = [{ clientX: 200, clientY: 205 }]
    box.dispatchEvent(fine)
    expect(sposta).toHaveBeenCalledWith(1)
    trascina(box, { x: 100, y: 200 }, { x: 250, y: 210 })
    expect(sposta).toHaveBeenLastCalledWith(-1)
    smonta()
  })

  it('leaves a scroll to the list, and the screen’s edge to the phone', () => {
    const sposta = vi.fn()
    const { box, smonta } = monta(sposta)
    trascina(box, { x: 200, y: 400 }, { x: 150, y: 200 })
    trascina(box, { x: 10, y: 200 }, { x: 200, y: 200 })
    expect(sposta).not.toHaveBeenCalled()
    smonta()
  })
})
