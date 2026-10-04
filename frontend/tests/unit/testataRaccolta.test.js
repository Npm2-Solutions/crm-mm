// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A record's card folds away on a phone while its tab is scrolled.
import {
  DOPO_UN_GESTO,
  SOGLIA_TESTATA,
  raccogliereLaTestata,
  useTestataRaccolta,
} from '@/composables/testataRaccolta'
import { createApp, h, nextTick, ref } from 'vue'

describe('raccogliereLaTestata', () => {
  const lunga = { altezza: 2000, visibile: 500, testata: 300 }

  it('folds the card once a long tab is scrolled past the threshold', () => {
    expect(raccogliereLaTestata({ ...lunga, cima: 10, raccolta: false })).toBe(
      false,
    )
    expect(
      raccogliereLaTestata({
        ...lunga,
        cima: SOGLIA_TESTATA + 1,
        raccolta: false,
      }),
    ).toBe(true)
  })

  it('stays folded until the tab is back at its top', () => {
    expect(raccogliereLaTestata({ ...lunga, cima: 5, raccolta: true })).toBe(
      true,
    )
    expect(raccogliereLaTestata({ ...lunga, cima: 0, raccolta: true })).toBe(
      false,
    )
    // an iPhone's bounce goes above the top
    expect(raccogliereLaTestata({ ...lunga, cima: -8, raccolta: true })).toBe(
      false,
    )
  })

  it('leaves the card where the tab would spring back without it', () => {
    // 600 to scroll, the card 300 tall: without it 300 are left, it folds
    expect(
      raccogliereLaTestata({
        altezza: 1100,
        visibile: 500,
        testata: 300,
        cima: 100,
        raccolta: false,
      }),
    ).toBe(true)
    // 310 to scroll: without the card ten are left, and it would come back
    expect(
      raccogliereLaTestata({
        altezza: 810,
        visibile: 500,
        testata: 300,
        cima: 100,
        raccolta: false,
      }),
    ).toBe(false)
  })

  it('changes nothing for a jump the page makes on its own', () => {
    // a conversation opening at its last message
    expect(
      raccogliereLaTestata({ ...lunga, prima: 0, cima: 1500, raccolta: false }),
    ).toBe(false)
    expect(
      raccogliereLaTestata({ ...lunga, prima: 0, cima: 1500, raccolta: true }),
    ).toBe(true)
    // a finger going up from there folds it, the top opens it
    expect(
      raccogliereLaTestata({
        ...lunga,
        prima: 1500,
        cima: 1440,
        raccolta: false,
      }),
    ).toBe(true)
    expect(
      raccogliereLaTestata({ ...lunga, prima: 1500, cima: 0, raccolta: true }),
    ).toBe(false)
  })
})

describe('raccogliereLaTestata without anybody scrolling', () => {
  const lunga = { altezza: 2000, visibile: 500, testata: 300 }

  it('leaves the card as it is, and opens it at the top', () => {
    expect(
      raccogliereLaTestata({
        ...lunga,
        cima: 300,
        raccolta: false,
        gesto: false,
      }),
    ).toBe(false)
    expect(
      raccogliereLaTestata({
        ...lunga,
        cima: 300,
        raccolta: true,
        gesto: false,
      }),
    ).toBe(true)
    expect(
      raccogliereLaTestata({ ...lunga, cima: 0, raccolta: true, gesto: false }),
    ).toBe(false)
  })
})

describe('useTestataRaccolta', () => {
  function monta() {
    const area = ref(null)
    const testata = ref(null)
    const scheda = ref(0)
    let raccolta
    const app = createApp({
      setup() {
        raccolta = useTestataRaccolta(area, testata, scheda)
        return () =>
          h('div', [
            h('div', { ref: testata }),
            h('div', { ref: area }, [h('div', { class: 'scheda' })]),
          ])
      },
    })
    const radice = document.createElement('div')
    document.body.append(radice)
    app.mount(radice)
    const box = radice.querySelector('.scheda')
    const misura = (el, misure) =>
      Object.entries(misure).forEach(([nome, valore]) =>
        Object.defineProperty(el, nome, { value: valore, configurable: true }),
      )
    misura(area.value, { clientHeight: 500 })
    misura(testata.value, { offsetHeight: 300 })
    misura(box, { clientHeight: 500, scrollHeight: 2000 })
    // a finger moves the box
    function scorri(el, cima) {
      el.dispatchEvent(new Event('touchmove', { bubbles: true }))
      daSolo(el, cima)
    }
    // the page moves it
    function daSolo(el, cima) {
      el.scrollTop = cima
      el.dispatchEvent(new Event('scroll'))
    }
    return {
      box,
      misura,
      scorri,
      daSolo,
      scheda,
      raccolta,
      smonta: () => app.unmount(),
    }
  }

  it('folds while the tab is scrolled and opens at its top', async () => {
    const { box, scorri, raccolta, smonta } = monta()
    await nextTick()
    scorri(box, 200)
    expect(raccolta.value).toBe(true)
    scorri(box, 40)
    expect(raccolta.value).toBe(true)
    scorri(box, 0)
    expect(raccolta.value).toBe(false)
    smonta()
  })

  it('pays no heed to a field, an editor or a small box inside the tab', async () => {
    const { box, misura, scorri, raccolta, smonta } = monta()
    await nextTick()
    const piccolo = document.createElement('div')
    const campo = document.createElement('textarea')
    const editor = document.createElement('div')
    editor.setAttribute('contenteditable', 'true')
    for (const el of [piccolo, campo, editor]) {
      box.append(el)
      misura(el, { clientHeight: el === piccolo ? 80 : 300, scrollHeight: 900 })
      scorri(el, 200)
    }
    expect(raccolta.value).toBe(false)
    scorri(box, 200)
    for (const el of [piccolo, campo, editor]) scorri(el, 0)
    expect(raccolta.value).toBe(true)
    smonta()
  })

  it('stays open while the tab scrolls by itself, not with the keyboard up', async () => {
    const { box, scorri, daSolo, raccolta, smonta } = monta()
    await nextTick()
    // the history opening at its newest day, in steps as it loads
    daSolo(box, 200)
    daSolo(box, 488)
    expect(raccolta.value).toBe(false)
    // a finger, then the momentum after it
    scorri(box, 520)
    expect(raccolta.value).toBe(true)
    daSolo(box, 0)
    expect(raccolta.value).toBe(false)
    // writing, the box follows the words
    vi.useFakeTimers()
    vi.advanceTimersByTime(DOPO_UN_GESTO + 1)
    document.documentElement.dataset.tastiera = 'aperta'
    daSolo(box, 200)
    expect(raccolta.value).toBe(true)
    delete document.documentElement.dataset.tastiera
    vi.useRealTimers()
    smonta()
  })

  it('stays open when the tab jumps to its end by itself', async () => {
    const { box, scorri, raccolta, smonta } = monta()
    await nextTick()
    scorri(box, 1500)
    expect(raccolta.value).toBe(false)
    scorri(box, 1450)
    expect(raccolta.value).toBe(true)
    smonta()
  })

  it('opens the card on another tab', async () => {
    const { box, scorri, scheda, raccolta, smonta } = monta()
    await nextTick()
    scorri(box, 200)
    expect(raccolta.value).toBe(true)
    scheda.value = 2
    await nextTick()
    expect(raccolta.value).toBe(false)
    smonta()
  })
})
