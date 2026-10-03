// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A list pulled down from its top reloads, as in a phone's own apps.
import {
  MASSIMO_TIRATA,
  SOGLIA_TIRATA,
  tirata,
  useTiraPerAggiornare,
} from '@/composables/tiraPerAggiornare'
import { createApp, h, nextTick, ref } from 'vue'

describe('tirata', () => {
  it('follows half the finger, up to a limit', () => {
    expect(tirata(40)).toBe(20)
    expect(tirata(2 * SOGLIA_TIRATA)).toBe(SOGLIA_TIRATA)
    expect(tirata(1000)).toBe(MASSIMO_TIRATA)
  })

  it('is nothing for a finger going up or not moving', () => {
    expect(tirata(-30)).toBe(0)
    expect(tirata(0)).toBe(0)
    expect(tirata(undefined)).toBe(0)
  })
})

describe('useTiraPerAggiornare', () => {
  function monta(aggiorna) {
    const contenitore = ref(null)
    let stato
    const app = createApp({
      setup() {
        stato = useTiraPerAggiornare(contenitore, aggiorna)
        return () => h('div', { ref: contenitore })
      },
    })
    const radice = document.createElement('div')
    document.body.append(radice)
    app.mount(radice)
    return { stato, box: contenitore.value, smonta: () => app.unmount() }
  }

  function tocco(box, tipo, y) {
    const evento = new Event(tipo)
    evento.touches = y === undefined ? [] : [{ clientY: y }]
    box.dispatchEvent(evento)
  }

  it('reloads once a pull past the threshold is let go, and turns until done', async () => {
    let finisci
    const aggiorna = vi.fn(() => new Promise((r) => (finisci = r)))
    const { stato, box, smonta } = monta(aggiorna)
    tocco(box, 'touchstart', 100)
    tocco(box, 'touchmove', 100 + 2 * SOGLIA_TIRATA + 10)
    expect(stato.pronta).toBe(true)
    expect(stato.trascinando).toBe(true)
    tocco(box, 'touchend')
    expect(aggiorna).toHaveBeenCalledTimes(1)
    expect(stato.inCorso).toBe(true)
    finisci()
    await nextTick()
    await nextTick()
    expect(stato.inCorso).toBe(false)
    expect(stato.distanza).toBe(0)
    smonta()
  })

  it('does nothing for a short pull', () => {
    const aggiorna = vi.fn()
    const { stato, box, smonta } = monta(aggiorna)
    tocco(box, 'touchstart', 100)
    tocco(box, 'touchmove', 140)
    tocco(box, 'touchend')
    expect(aggiorna).not.toHaveBeenCalled()
    expect(stato.distanza).toBe(0)
    smonta()
  })

  it('leaves a list that is scrolled down to scroll', () => {
    const aggiorna = vi.fn()
    const { stato, box, smonta } = monta(aggiorna)
    box.scrollTop = 200
    tocco(box, 'touchstart', 100)
    tocco(box, 'touchmove', 400)
    tocco(box, 'touchend')
    expect(aggiorna).not.toHaveBeenCalled()
    expect(stato.distanza).toBe(0)
    smonta()
  })

  it('follows a box drawn after the page, once the list has rows', async () => {
    const contenitore = ref(null)
    const pronta = ref(false)
    const aggiorna = vi.fn()
    const app = createApp({
      setup() {
        useTiraPerAggiornare(contenitore, aggiorna)
        return () => (pronta.value ? h('div', { ref: contenitore }) : h('span'))
      },
    })
    const radice = document.createElement('div')
    document.body.append(radice)
    app.mount(radice)
    pronta.value = true
    await nextTick()
    const box = contenitore.value
    tocco(box, 'touchstart', 100)
    tocco(box, 'touchmove', 100 + 2 * SOGLIA_TIRATA + 10)
    tocco(box, 'touchend')
    expect(aggiorna).toHaveBeenCalledTimes(1)
    app.unmount()
  })

  it('reloads nothing when the phone takes the gesture back', () => {
    const aggiorna = vi.fn()
    const { stato, box, smonta } = monta(aggiorna)
    tocco(box, 'touchstart', 100)
    tocco(box, 'touchmove', 400)
    tocco(box, 'touchcancel')
    expect(aggiorna).not.toHaveBeenCalled()
    expect(stato.distanza).toBe(0)
    smonta()
  })
})
