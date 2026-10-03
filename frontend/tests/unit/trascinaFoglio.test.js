// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A sheet taken by its grabber follows the finger down and, far enough, closes.
import {
  PASSO_MINIMO,
  ZONA_MANIGLIA,
  siChiude,
  trascinaIFogli,
} from '@/utils/trascinaFoglio'

describe('siChiude', () => {
  it('closes past a third of the sheet, no more than 140 pixels', () => {
    expect(siChiude({ spostamento: 100, altezza: 300 })).toBe(true)
    expect(siChiude({ spostamento: 80, altezza: 300 })).toBe(false)
    expect(siChiude({ spostamento: 150, altezza: 800 })).toBe(true)
    expect(siChiude({ spostamento: 130, altezza: 800 })).toBe(false)
  })

  it('closes on a flick, not on a twitch', () => {
    expect(siChiude({ spostamento: 40, altezza: 800, velocita: 0.9 })).toBe(
      true,
    )
    expect(siChiude({ spostamento: 10, altezza: 800, velocita: 2 })).toBe(false)
    expect(siChiude({ spostamento: 0, altezza: 800 })).toBe(false)
  })
})

describe('trascinaIFogli', () => {
  let adesso = 0
  let smetti = () => {}

  // a dialog as frappe-ui draws it: the dimmed screen, then the box that
  // scrolls holding the sheet, its top 100 pixels down
  function foglio() {
    const sfondo = document.createElement('div')
    sfondo.className = 'dialog-overlay'
    const scatola = document.createElement('div')
    scatola.className = 'dialog-scroll-container'
    const posto = document.createElement('div')
    const f = document.createElement('div')
    f.className = 'dialog-content'
    f.dataset.state = 'open'
    f.getBoundingClientRect = () => ({ top: 100 })
    Object.defineProperty(f, 'offsetHeight', { value: 400 })
    const titolo = document.createElement('header')
    const campo = document.createElement('input')
    f.append(titolo, campo)
    posto.append(f)
    scatola.append(posto)
    document.body.append(sfondo, scatola)
    return { f, sfondo, titolo, campo, scatola }
  }

  function tocco(dove, tipo, y) {
    const evento = new Event(tipo, { bubbles: true })
    evento.touches = y === undefined ? [] : [{ clientY: y }]
    dove.dispatchEvent(evento)
  }

  // the finger from y0 to y1 in steps of 16 milliseconds
  function trascina(dove, y0, y1, passi = 10) {
    tocco(dove, 'touchstart', y0)
    for (let i = 1; i <= passi; i++) {
      adesso += 16
      tocco(dove, 'touchmove', y0 + ((y1 - y0) * i) / passi)
    }
  }

  beforeEach(() => {
    vi.useFakeTimers()
    adesso = 0
    smetti = trascinaIFogli(window, () => adesso)
  })
  afterEach(() => {
    smetti()
    vi.useRealTimers()
    document.body.innerHTML = ''
  })

  it('follows the finger from the title, and closes it let go far enough down', () => {
    const { f, sfondo, titolo } = foglio()
    const esc = vi.fn()
    document.addEventListener('keydown', esc)
    trascina(titolo, 120, 120 + 200, 40)
    expect(f.style.transform).toBe('translateY(200px)')
    expect(Number(sfondo.style.opacity)).toBeCloseTo(0.5)
    tocco(titolo, 'touchend')
    expect(f.style.transform).toBe('translateY(400px)')
    vi.advanceTimersByTime(200)
    expect(esc.mock.calls[0][0].key).toBe('Escape')
    document.removeEventListener('keydown', esc)
  })

  it('slides back up for a short pull', () => {
    const { f, titolo } = foglio()
    const esc = vi.fn()
    document.addEventListener('keydown', esc)
    trascina(titolo, 120, 160, 20)
    tocco(titolo, 'touchend')
    expect(f.style.transform).toBe('')
    vi.advanceTimersByTime(500)
    expect(esc).not.toHaveBeenCalled()
    document.removeEventListener('keydown', esc)
  })

  it('stays a tap below the first pixels', () => {
    const { f, titolo } = foglio()
    trascina(titolo, 120, 120 + PASSO_MINIMO - 2, 2)
    expect(f.style.transform).toBe('')
  })

  it('is not taken below its top, from a field, or scrolled', () => {
    const { f, titolo, campo, scatola } = foglio()
    trascina(titolo, 100 + ZONA_MANIGLIA + 20, 500)
    expect(f.style.transform).toBe('')
    tocco(titolo, 'touchend')
    trascina(campo, 120, 400)
    expect(f.style.transform).toBe('')
    tocco(campo, 'touchend')
    scatola.scrollTop = 50
    trascina(titolo, 120, 400)
    expect(f.style.transform).toBe('')
  })

  it('leaves a screen of its own, with no grabber, where it is', () => {
    const { f, titolo } = foglio()
    const vero = window.getComputedStyle
    vi.spyOn(window, 'getComputedStyle').mockImplementation((el, pseudo) =>
      pseudo === '::before' ? { content: 'none' } : vero(el, pseudo),
    )
    trascina(titolo, 120, 400)
    expect(f.style.transform).toBe('')
    window.getComputedStyle.mockRestore()
  })

  it('comes back up when the dialog may not close yet', () => {
    const { f, titolo } = foglio()
    trascina(titolo, 120, 400, 40)
    tocco(titolo, 'touchend')
    // nobody closes it: Escape is refused
    vi.advanceTimersByTime(400)
    expect(f.style.transform).toBe('')
    expect(f.style.animation).toBe('')
  })
})
