// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// Back to a list finds it as it was left; opened anew it starts from the top.
import { useRitorno } from '@/composables/ritorno'
import {
  conserva,
  dimenticaTutto,
  rimettiLoScorrimento,
  ritrova,
  segnaIRitorni,
  senzaDoppioni,
} from '@/utils/ritorno'
import { createApp, h, ref } from 'vue'

// a router that only runs its guards, and a window whose history says where
// the browser is
function navigatore() {
  const guardie = []
  const win = { history: { state: null } }
  return {
    win,
    router: {
      beforeEach(guardia) {
        guardie.push(guardia)
        return () => guardie.splice(guardie.indexOf(guardia), 1)
      },
    },
    // a link or the menu: the history still holds the page being left
    vai(percorso, da = '/altrove') {
      win.history.state = { current: da }
      guardie.forEach((g) => g({ fullPath: percorso }))
    },
    // a back: the browser has already put the target's entry in place
    indietro(percorso) {
      win.history.state = { current: percorso }
      guardie.forEach((g) => g({ fullPath: percorso }))
    },
  }
}

let smetti = () => {}
afterEach(() => {
  smetti()
  dimenticaTutto()
  document.body.innerHTML = ''
})

describe('ritrova', () => {
  it('gives a list back only to a back', () => {
    const n = navigatore()
    smetti = segnaIRitorni(n.router, n.win)
    conserva('persone', { testo: 'Rossi' })
    n.vai('/leads')
    expect(ritrova('persone')).toBe(null)
    n.indietro('/leads')
    expect(ritrova('persone')).toEqual({ testo: 'Rossi' })
    expect(ritrova('contatti')).toBe(null)
  })
})

describe('senzaDoppioni', () => {
  it('keeps the first row of each name, and the rows without one', () => {
    const righe = [
      { name: 'a', v: 1 },
      { name: 'b' },
      { name: 'a', v: 2 },
      { titolo: 'senza nome' },
    ]
    expect(senzaDoppioni(righe)).toEqual([
      { name: 'a', v: 1 },
      { name: 'b' },
      { titolo: 'senza nome' },
    ])
  })
})

describe('rimettiLoScorrimento', () => {
  // a box that scrolls no further than its rows let it
  function scatola(altezza) {
    const box = document.createElement('div')
    let y = 0
    box.limite = altezza
    Object.defineProperty(box, 'scrollTop', {
      get: () => y,
      set: (valore) => (y = Math.min(valore, box.limite)),
    })
    document.body.append(box)
    return box
  }

  it('goes back down at once when the rows are there', () => {
    const box = scatola(1000)
    rimettiLoScorrimento(box, 600)
    expect(box.scrollTop).toBe(600)
  })

  it('waits for the rows, then goes back down', async () => {
    const box = scatola(0)
    rimettiLoScorrimento(box, 600)
    expect(box.scrollTop).toBe(0)
    box.limite = 1000
    box.append(document.createElement('p'))
    await new Promise((r) => setTimeout(r, 0))
    expect(box.scrollTop).toBe(600)
  })

  it('leaves the box where a finger takes it', async () => {
    const box = scatola(0)
    rimettiLoScorrimento(box, 600)
    box.dispatchEvent(new Event('touchstart'))
    box.limite = 1000
    box.append(document.createElement('p'))
    await new Promise((r) => setTimeout(r, 0))
    expect(box.scrollTop).toBe(0)
  })
})

describe('useRitorno', () => {
  function monta(stato, rimetti) {
    const contenitore = ref(null)
    let salvato
    const app = createApp({
      setup() {
        salvato = useRitorno('prova', { contenitore, stato, rimetti })
        return () => h('div', { ref: contenitore })
      },
    })
    const radice = document.createElement('div')
    document.body.append(radice)
    app.mount(radice)
    return { salvato, box: contenitore.value, smonta: () => app.unmount() }
  }

  it('keeps the list when its page goes, and puts it back on a back', () => {
    const n = navigatore()
    smetti = segnaIRitorni(n.router, n.win)
    n.vai('/leads')
    const rimetti = vi.fn()
    const prima = monta(() => ({ testo: 'Rossi' }), rimetti)
    expect(prima.salvato).toBe(null)
    prima.box.scrollTop = 480
    prima.smonta()

    n.indietro('/leads')
    const dopo = monta(() => ({}), rimetti)
    expect(rimetti).toHaveBeenCalledWith({ testo: 'Rossi', scorrimento: 480 })
    expect(dopo.salvato.testo).toBe('Rossi')
    expect(dopo.box.scrollTop).toBe(480)
    dopo.smonta()
  })

  it('starts from the top when the list is opened anew', () => {
    const n = navigatore()
    smetti = segnaIRitorni(n.router, n.win)
    n.vai('/leads')
    const prima = monta(() => ({ testo: 'Rossi' }), vi.fn())
    prima.smonta()
    n.vai('/leads')
    const rimetti = vi.fn()
    const dopo = monta(() => ({}), rimetti)
    expect(dopo.salvato).toBe(null)
    expect(rimetti).not.toHaveBeenCalled()
    dopo.smonta()
  })
})
