// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// While somebody writes on a phone, the page takes what the keyboard leaves,
// and on an iPhone it never slides.
import {
  ATTESA_TASTIERA,
  QUIETE,
  SOGLIA_TASTIERA,
  inVista,
  scatolaCheScorre,
  seguiLaTastiera,
  siScrive,
  spostamentoPerVedere,
  vistaConTastiera,
} from '@/utils/tastieraAperta'

const IPHONE =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1'
const ANDROID =
  'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36'

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

  it('opens where the browser made the page itself shorter, covering nothing', () => {
    expect(
      vistaConTastiera({
        altezzaPiena: 800,
        altezzaPagina: 470,
        altezzaVista: 470,
        scrivendo: true,
      }),
    ).toEqual({ aperta: true, altezza: 470, sopra: 0, sotto: 0 })
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
        altezzaPiena: 800,
        altezzaPagina: 800 - SOGLIA_TASTIERA,
        altezzaVista: 800 - SOGLIA_TASTIERA,
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

  it('stays closed when the page has its whole height', () => {
    expect(
      vistaConTastiera({
        altezzaPiena: 508,
        altezzaPagina: 508,
        altezzaVista: 508,
        scrivendo: true,
      }).aperta,
    ).toBe(false)
  })
})

describe('spostamentoPerVedere', () => {
  const box = { cima: 100, fondo: 500, sopra: 16, sotto: 16 }

  it('moves nothing for what is already in view', () => {
    expect(spostamentoPerVedere({ ...box, alto: 200, basso: 240 })).toBe(0)
  })

  it('brings up what lies under the bottom, by as little as it takes', () => {
    // the field ends at 560: 76 below the room's end (484)
    expect(spostamentoPerVedere({ ...box, alto: 520, basso: 560 })).toBe(76)
  })

  it('brings down what lies above the top', () => {
    expect(spostamentoPerVedere({ ...box, alto: 40, basso: 80 })).toBe(-76)
  })

  it('shows the top of what is taller than the room, from below', () => {
    expect(spostamentoPerVedere({ ...box, alto: 300, basso: 900 })).toBe(184)
  })

  it('leaves what is taller than the room and already across it', () => {
    expect(spostamentoPerVedere({ ...box, alto: 50, basso: 900 })).toBe(0)
  })
})

// a box of `altezza` with `contenuto` inside, drawn from `cima` on the screen
function scatola({
  cima = 0,
  altezza = 400,
  contenuto = 1000,
  overflow = 'auto',
}) {
  const box = document.createElement('div')
  box.style.overflowY = overflow
  Object.defineProperty(box, 'clientHeight', { value: altezza })
  Object.defineProperty(box, 'scrollHeight', { value: contenuto })
  Object.defineProperty(box, 'clientWidth', { value: 360 })
  Object.defineProperty(box, 'scrollWidth', { value: 360 })
  box.getBoundingClientRect = () => ({
    top: cima,
    bottom: cima + altezza,
    height: altezza,
  })
  return box
}

// an element drawn at `alto` on the screen in its box, moved as the box scrolls
function dentro(box, alto, altezza = 40) {
  const campo = document.createElement('input')
  box.append(campo)
  campo.getBoundingClientRect = () => ({
    top: alto - box.scrollTop,
    bottom: alto - box.scrollTop + altezza,
    height: altezza,
  })
  return campo
}

describe('inVista', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  function finestra(vista) {
    return {
      document,
      innerHeight: 844,
      visualViewport: vista,
      getComputedStyle: (el) => window.getComputedStyle(el),
      getSelection: () => null,
    }
  }

  it('scrolls the box, not the page, until the field is above the keyboard', () => {
    const box = scatola({ cima: 60, altezza: 784 })
    document.body.append(box)
    // the keyboard leaves 508 of the screen: the field at 600 is under it
    const campo = dentro(box, 600)
    inVista(campo, finestra({ offsetTop: 0, height: 508 }))
    // its end (640) 16 above what one sees (508)
    expect(box.scrollTop).toBe(148)
  })

  it('leaves a field in view where it is', () => {
    const box = scatola({ cima: 60, altezza: 784 })
    document.body.append(box)
    const campo = dentro(box, 200)
    inVista(campo, finestra({ offsetTop: 0, height: 508 }))
    expect(box.scrollTop).toBe(0)
  })

  it('keeps the room a sheet keeps for its actions', () => {
    const box = scatola({ cima: 100, altezza: 400 })
    box.style.scrollPaddingBottom = '80px'
    document.body.append(box)
    const campo = dentro(box, 440)
    inVista(campo, finestra({ offsetTop: 0, height: 844 }))
    // its end (480) 80 above the box's end (500)
    expect(box.scrollTop).toBe(60)
  })

  it('never scrolls a box that does not scroll', () => {
    const box = scatola({ cima: 60, altezza: 784, overflow: 'visible' })
    document.body.append(box)
    const campo = dentro(box, 600)
    inVista(campo, finestra({ offsetTop: 0, height: 508 }))
    expect(box.scrollTop).toBe(0)
  })
})

describe('scatolaCheScorre', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('is the nearest box with something to scroll', () => {
    const box = scatola({})
    const riga = document.createElement('div')
    box.append(riga)
    document.body.append(box)
    expect(scatolaCheScorre(riga)).toBe(box)
  })

  it('is none where only the page is left: a box with nothing to scroll', () => {
    const box = scatola({ altezza: 400, contenuto: 400 })
    const riga = document.createElement('div')
    box.append(riga)
    document.body.append(box)
    expect(scatolaCheScorre(riga)).toBeNull()
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
  // a browser's window: its frames and its timers wait for `fotogramma()`
  // and `tempo()`
  function finestra({ agente = ANDROID, altezza = 844 } = {}) {
    const vista = new EventTarget()
    vista.height = altezza
    vista.offsetTop = 0
    vista.scale = 1
    const coda = []
    const timer = new Map()
    let prossimo = 1
    const win = Object.assign(new EventTarget(), {
      visualViewport: vista,
      document,
      navigator: { userAgent: agente, platform: '', maxTouchPoints: 5 },
      HTMLElement: window.HTMLElement,
      innerWidth: 390,
      innerHeight: altezza,
      scrollY: 0,
      scrollTo: vi.fn(),
      scrollBy: vi.fn(),
      getComputedStyle: (el) => window.getComputedStyle(el),
      getSelection: () => null,
      requestAnimationFrame: (fn) => coda.push(fn),
      cancelAnimationFrame: vi.fn(),
      setTimeout: (fn) => {
        timer.set(prossimo, fn)
        return prossimo++
      },
      clearTimeout: (id) => timer.delete(id),
      performance: { now: () => 0 },
    })
    const fotogramma = () => {
      for (let giri = 0; giri < 5 && coda.length; giri++) {
        coda.splice(0).forEach((fn) => fn())
      }
    }
    const tempo = () => {
      const scaduti = [...timer.values()]
      timer.clear()
      scaduti.forEach((fn) => fn())
      fotogramma()
    }
    return { win, vista, fotogramma, tempo }
  }

  function tastiera(vista, altezza) {
    vista.height = altezza
    vista.dispatchEvent(new Event('resize'))
  }

  function tocco(tipo, bersaglio, dita = 1) {
    const evento = new Event(tipo, { bubbles: true, cancelable: true })
    Object.defineProperty(evento, 'touches', {
      value: Array.from({ length: tipo === 'touchend' ? 0 : dita }),
    })
    bersaglio.dispatchEvent(evento)
    return evento
  }

  const radice = document.documentElement

  afterEach(() => {
    document.body.innerHTML = ''
    document.activeElement?.blur?.()
  })

  it('marks the root while the keyboard is open, and clears it after', () => {
    const { win, vista, fotogramma } = finestra()
    const smetti = seguiLaTastiera(win)
    const input = document.createElement('input')
    document.body.append(input)
    input.focus()
    tastiera(vista, 508)
    fotogramma()
    expect(radice.dataset.tastiera).toBe('aperta')
    expect(radice.style.getPropertyValue('--altezza-con-tastiera')).toBe(
      '508px',
    )
    expect(radice.style.getPropertyValue('--tastiera')).toBe('336px')
    tastiera(vista, 844)
    fotogramma()
    expect(radice.dataset.tastiera).toBeUndefined()
    expect(radice.style.getPropertyValue('--tastiera')).toBe('')
    smetti()
  })

  it('does nothing until a field is written in', () => {
    const { win, vista, fotogramma } = finestra()
    const smetti = seguiLaTastiera(win)
    tastiera(vista, 508)
    fotogramma()
    expect(radice.dataset.tastiera).toBeUndefined()
    smetti()
  })

  it('knows a keyboard that made the page shorter: it covers nothing', () => {
    const { win, vista, fotogramma } = finestra()
    const smetti = seguiLaTastiera(win)
    const input = document.createElement('input')
    document.body.append(input)
    input.focus()
    win.innerHeight = 470
    vista.height = 470
    win.dispatchEvent(new Event('resize'))
    fotogramma()
    expect(radice.dataset.tastiera).toBe('aperta')
    expect(radice.style.getPropertyValue('--tastiera')).toBe('0px')
    expect(radice.style.getPropertyValue('--altezza-con-tastiera')).toBe(
      '470px',
    )
    smetti()
    expect(radice.dataset.tastiera).toBeUndefined()
  })

  it('does not follow a page sliding frame by frame, and takes it back once still', () => {
    const { win, vista, fotogramma, tempo } = finestra()
    const smetti = seguiLaTastiera(win)
    const input = document.createElement('input')
    document.body.append(input)
    input.focus()
    tastiera(vista, 508)
    fotogramma()
    // Safari slides what one sees under the finger
    for (const sopra of [40, 80, 120]) {
      vista.offsetTop = sopra
      win.scrollY = sopra
      vista.dispatchEvent(new Event('scroll'))
      fotogramma()
      expect(radice.style.getPropertyValue('--vista-sopra')).toBe('0px')
    }
    expect(win.scrollTo).not.toHaveBeenCalled()
    tempo()
    expect(win.scrollTo).toHaveBeenCalledWith(0, 0)
    smetti()
  })

  it('waits for the finger to leave before taking the page back', () => {
    const { win, vista, fotogramma, tempo } = finestra()
    const smetti = seguiLaTastiera(win)
    const input = document.createElement('input')
    document.body.append(input)
    input.focus()
    tastiera(vista, 508)
    fotogramma()
    tocco('touchstart', document.body)
    vista.offsetTop = 60
    vista.dispatchEvent(new Event('scroll'))
    tempo()
    expect(win.scrollTo).not.toHaveBeenCalled()
    tocco('touchend', document.body)
    tempo()
    expect(win.scrollTo).toHaveBeenCalledWith(0, 0)
    smetti()
  })

  it('leaves a page two fingers enlarged as it is', () => {
    const { win, vista, fotogramma } = finestra()
    const smetti = seguiLaTastiera(win)
    const input = document.createElement('input')
    document.body.append(input)
    input.focus()
    vista.scale = 2
    tastiera(vista, 254)
    fotogramma()
    expect(radice.dataset.tastiera).toBeUndefined()
    smetti()
  })

  it('closes the keyboard when the search key is pressed in a search', () => {
    const { win } = finestra()
    const smetti = seguiLaTastiera(win)
    const cerca = document.createElement('input')
    cerca.type = 'search'
    const nome = document.createElement('input')
    document.body.append(cerca, nome)
    const invio = (el) =>
      el.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }),
      )
    cerca.focus()
    invio(cerca)
    expect(document.activeElement).not.toBe(cerca)
    // any other field keeps Enter for itself
    nome.focus()
    invio(nome)
    expect(document.activeElement).toBe(nome)
    smetti()
  })

  describe('on an iPhone', () => {
    let spia
    beforeEach(() => {
      spia = vi.spyOn(window.HTMLElement.prototype, 'focus')
    })
    afterEach(() => {
      spia.mockRestore()
    })

    it('focuses without letting Safari scroll the page, and gives focus back after', () => {
      const { win } = finestra({ agente: IPHONE })
      const smetti = seguiLaTastiera(win)
      const input = document.createElement('input')
      document.body.append(input)
      input.focus()
      expect(spia).toHaveBeenLastCalledWith({ preventScroll: true })
      expect(document.activeElement).toBe(input)
      smetti()
      expect(window.HTMLElement.prototype.focus).toBe(spia)
    })

    it('shows a focused field in its box once the keyboard is up, or after a while', () => {
      const { win, vista, fotogramma, tempo } = finestra({ agente: IPHONE })
      const smetti = seguiLaTastiera(win)
      const box = scatola({ cima: 60, altezza: 784, contenuto: 2000 })
      document.body.append(box)
      const campo = dentro(box, 900)
      campo.focus()
      fotogramma()
      expect(box.scrollTop).toBe(0)
      tastiera(vista, 508)
      fotogramma()
      // its end (940) 16 above what the keyboard leaves (508)
      expect(box.scrollTop).toBe(448)
      // a focus no keyboard answers: shown in its box all the same
      box.scrollTop = 0
      campo.blur()
      tastiera(vista, 844)
      fotogramma()
      campo.focus()
      fotogramma()
      expect(box.scrollTop).toBe(0)
      tempo()
      expect(box.scrollTop).toBe(112)
      smetti()
    })

    it('hands a tapped field the focus from a place of its own', () => {
      const { win } = finestra({ agente: IPHONE })
      const smetti = seguiLaTastiera(win)
      const input = document.createElement('input')
      document.body.append(input)
      tocco('touchstart', input)
      const sosta = document.querySelector('[data-sosta-del-fuoco]')
      expect(sosta).not.toBeNull()
      expect(document.activeElement).toBe(sosta)
      smetti()
      expect(document.querySelector('[data-sosta-del-fuoco]')).toBeNull()
    })

    it('hands the focus to the next field without Safari scrolling to it', () => {
      const { win } = finestra({ agente: IPHONE })
      const smetti = seguiLaTastiera(win)
      const primo = document.createElement('input')
      const secondo = document.createElement('input')
      document.body.append(primo, secondo)
      primo.focus()
      spia.mockClear()
      // the keyboard's arrow, or a tap: the focus leaves for the second
      primo.dispatchEvent(new FocusEvent('blur', { relatedTarget: secondo }))
      expect(spia).toHaveBeenCalledTimes(1)
      expect(spia.mock.contexts[0]).toBe(secondo)
      expect(spia).toHaveBeenLastCalledWith({ preventScroll: true })
      smetti()
    })

    it('keeps the focus inside the sheet a tapped field is in', () => {
      const { win } = finestra({ agente: IPHONE })
      const smetti = seguiLaTastiera(win)
      const foglio = document.createElement('div')
      foglio.tabIndex = -1
      const input = document.createElement('input')
      foglio.append(input)
      document.body.append(foglio)
      tocco('touchstart', input)
      expect(document.activeElement).toBe(foglio)
      smetti()
    })

    it('stops a finger that would slide the page while the keyboard covers it', () => {
      const { win, vista, fotogramma } = finestra({ agente: IPHONE })
      const smetti = seguiLaTastiera(win)
      const input = document.createElement('input')
      const lista = scatola({ altezza: 300, contenuto: 900 })
      const riga = document.createElement('div')
      lista.append(riga)
      const testata = document.createElement('header')
      document.body.append(testata, lista, input)
      input.focus()
      tastiera(vista, 508)
      fotogramma()
      // on what does not scroll: stopped
      tocco('touchstart', testata)
      expect(tocco('touchmove', testata).defaultPrevented).toBe(true)
      // on a list with something to scroll: it scrolls
      tocco('touchstart', riga)
      expect(tocco('touchmove', riga).defaultPrevented).toBe(false)
      // two fingers enlarge
      tocco('touchstart', testata, 2)
      expect(tocco('touchmove', testata, 2).defaultPrevented).toBe(false)
      tocco('touchend', testata)
      // the keyboard gone, nothing is stopped
      input.blur()
      tastiera(vista, 844)
      fotogramma()
      tocco('touchstart', testata)
      expect(tocco('touchmove', testata).defaultPrevented).toBe(false)
      smetti()
    })

    it('does nothing of the kind on Android', () => {
      const { win, vista, fotogramma } = finestra({ agente: ANDROID })
      const smetti = seguiLaTastiera(win)
      const input = document.createElement('input')
      const testata = document.createElement('header')
      document.body.append(testata, input)
      tocco('touchstart', input)
      expect(document.querySelector('[data-sosta-del-fuoco]')).toBeNull()
      input.focus()
      expect(spia).toHaveBeenLastCalledWith()
      tastiera(vista, 508)
      fotogramma()
      tocco('touchstart', testata)
      expect(tocco('touchmove', testata).defaultPrevented).toBe(false)
      smetti()
    })
  })

  it('exports the waits it keeps', () => {
    expect(QUIETE).toBeGreaterThan(0)
    expect(ATTESA_TASTIERA).toBeGreaterThan(QUIETE)
  })
})
