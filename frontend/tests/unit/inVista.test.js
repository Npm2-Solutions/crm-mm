// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A field a settings page opens on stays in the middle while the page around it is
// still drawing, until the person takes the scroll.
import { cheLoScorre, tieniInVista } from '@/utils/inVista'

function pagina() {
  const box = document.createElement('div')
  box.style.overflowY = 'auto'
  // more than it shows: happy-dom lays nothing out
  Object.defineProperty(box, 'scrollHeight', { value: 900 })
  Object.defineProperty(box, 'clientHeight', { value: 600 })
  const sopra = document.createElement('div')
  const campo = document.createElement('div')
  box.append(sopra, campo)
  document.body.append(box)
  campo.scrollIntoView = vi.fn()
  return { box, sopra, campo }
}

// the frames and the clock in the test's hands
function finestra() {
  const timer = []
  return {
    getComputedStyle: (el) => window.getComputedStyle(el),
    document,
    MutationObserver: window.MutationObserver,
    requestAnimationFrame: (fai) => {
      fai()
      return 1
    },
    cancelAnimationFrame: () => {},
    setTimeout: (fai) => timer.push(fai),
    clearTimeout: () => {},
    passaIlTempo: () => timer.splice(0).forEach((fai) => fai()),
  }
}

const arriva = () => new Promise((fatto) => setTimeout(fatto, 0))

describe('cheLoScorre', () => {
  it('finds the box around that scrolls, else the page', () => {
    const { box, campo } = pagina()
    expect(cheLoScorre(campo)).toBe(box)
    // a box that says it scrolls but shows all it has is passed by
    const intero = document.createElement('div')
    intero.style.overflowY = 'auto'
    const dentro = document.createElement('div')
    intero.append(dentro)
    box.append(intero)
    expect(cheLoScorre(dentro)).toBe(box)
    const solo = document.createElement('div')
    document.body.append(solo)
    expect(cheLoScorre(solo)).toBe(
      document.scrollingElement || document.documentElement,
    )
  })
})

describe('tieniInVista', () => {
  it('brings the field to the middle at once', () => {
    const { campo } = pagina()
    tieniInVista(campo, { win: finestra() })
    expect(campo.scrollIntoView).toHaveBeenCalledWith({
      block: 'center',
      behavior: 'smooth',
    })
  })

  it('brings it back to the middle when a card comes above it', async () => {
    const { sopra, campo } = pagina()
    tieniInVista(campo, { win: finestra() })
    sopra.append(document.createElement('section'))
    await arriva()
    expect(campo.scrollIntoView).toHaveBeenCalledTimes(2)
  })

  it('leaves the scroll to a finger', async () => {
    const { box, sopra, campo } = pagina()
    tieniInVista(campo, { win: finestra() })
    box.dispatchEvent(new Event('touchstart'))
    sopra.append(document.createElement('section'))
    await arriva()
    expect(campo.scrollIntoView).toHaveBeenCalledTimes(1)
  })

  it('stops following once the page has had its time', async () => {
    const { sopra, campo } = pagina()
    const win = finestra()
    tieniInVista(campo, { win })
    win.passaIlTempo()
    sopra.append(document.createElement('section'))
    await arriva()
    expect(campo.scrollIntoView).toHaveBeenCalledTimes(1)
  })

  it('does nothing without a field', () => {
    expect(tieniInVista(null, { win: finestra() })).toBeTypeOf('function')
  })
})
