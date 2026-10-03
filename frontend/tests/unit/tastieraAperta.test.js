// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// While somebody writes on a phone, the frame follows what the keyboard leaves.
import {
  SOGLIA_TASTIERA,
  seguiLaTastiera,
  siScrive,
  vistaConTastiera,
} from '@/utils/tastieraAperta'

describe('vistaConTastiera', () => {
  it('opens when somebody writes and a keyboard covers the bottom', () => {
    expect(
      vistaConTastiera({
        altezzaPagina: 844,
        altezzaVista: 508,
        scrivendo: true,
      }),
    ).toEqual({ aperta: true, altezza: 508, sopra: 0, sotto: 336 })
  })

  it('follows a page the browser slid towards the field', () => {
    expect(
      vistaConTastiera({
        altezzaPagina: 844,
        altezzaVista: 508,
        scostamento: 120,
        scrivendo: true,
      }),
    ).toEqual({ aperta: true, altezza: 508, sopra: 120, sotto: 216 })
  })

  it('stays closed for the address bar, or when nobody writes', () => {
    const chiusa = { aperta: false, altezza: null, sopra: 0, sotto: 0 }
    expect(
      vistaConTastiera({
        altezzaPagina: 844,
        altezzaVista: 844 - SOGLIA_TASTIERA,
        scrivendo: true,
      }),
    ).toEqual(chiusa)
    expect(
      vistaConTastiera({
        altezzaPagina: 844,
        altezzaVista: 508,
        scrivendo: false,
      }),
    ).toEqual(chiusa)
  })

  it('stays closed where the browser makes the page itself shorter', () => {
    expect(
      vistaConTastiera({
        altezzaPagina: 508,
        altezzaVista: 508,
        scrivendo: true,
      }).aperta,
    ).toBe(false)
  })
})

describe('siScrive', () => {
  function campo(html) {
    const box = document.createElement('div')
    box.innerHTML = html
    return box.firstElementChild
  }

  it('is a field a keyboard writes in', () => {
    expect(siScrive(campo('<input type="text">'))).toBe(true)
    expect(siScrive(campo('<input type="tel">'))).toBe(true)
    expect(siScrive(campo('<input>'))).toBe(true)
    expect(siScrive(campo('<textarea></textarea>'))).toBe(true)
  })

  it('is not a box, a button, a field one cannot change', () => {
    expect(siScrive(campo('<input type="checkbox">'))).toBe(false)
    expect(siScrive(campo('<button>Salva</button>'))).toBe(false)
    expect(siScrive(campo('<input type="text" readonly>'))).toBe(false)
    expect(siScrive(campo('<textarea disabled></textarea>'))).toBe(false)
    expect(siScrive(null)).toBe(false)
  })
})

describe('seguiLaTastiera', () => {
  function finestra() {
    const vista = new EventTarget()
    vista.height = 844
    vista.offsetTop = 0
    const win = {
      visualViewport: vista,
      document,
      innerHeight: 844,
      scrollY: 0,
      scrollTo: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      // the frames wait for `fotogramma()`, as a browser's wait for the screen
      requestAnimationFrame: (fn) => coda.push(fn),
      cancelAnimationFrame: vi.fn(),
    }
    const coda = []
    const fotogramma = () => coda.splice(0).forEach((fn) => fn())
    return { win, vista, fotogramma }
  }

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('marks the root while the keyboard is open, and clears it after', () => {
    const { win, vista, fotogramma } = finestra()
    const smetti = seguiLaTastiera(win)
    const input = document.createElement('input')
    document.body.append(input)
    input.focus()
    vista.height = 508
    vista.dispatchEvent(new Event('resize'))
    fotogramma()
    const radice = document.documentElement
    expect(radice.dataset.tastiera).toBe('aperta')
    expect(radice.style.getPropertyValue('--altezza-con-tastiera')).toBe(
      '508px',
    )
    expect(radice.style.getPropertyValue('--tastiera')).toBe('336px')
    vista.height = 844
    vista.dispatchEvent(new Event('resize'))
    fotogramma()
    expect(radice.dataset.tastiera).toBeUndefined()
    expect(radice.style.getPropertyValue('--tastiera')).toBe('')
    smetti()
  })

  it('does nothing until a field is written in', () => {
    const { win, vista, fotogramma } = finestra()
    const smetti = seguiLaTastiera(win)
    vista.height = 508
    vista.dispatchEvent(new Event('resize'))
    fotogramma()
    expect(document.documentElement.dataset.tastiera).toBeUndefined()
    smetti()
  })

  it('takes the page back to the top when the browser slid it', () => {
    const { win, vista, fotogramma } = finestra()
    const smetti = seguiLaTastiera(win)
    const input = document.createElement('input')
    document.body.append(input)
    input.focus()
    win.scrollY = 180
    vista.height = 508
    vista.dispatchEvent(new Event('resize'))
    fotogramma()
    expect(win.scrollTo).toHaveBeenCalledWith(0, 0)
    smetti()
    expect(document.documentElement.dataset.tastiera).toBeUndefined()
  })
})
