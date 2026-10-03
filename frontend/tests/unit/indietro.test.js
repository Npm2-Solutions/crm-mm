// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// Android's back closes what lies on top before it leaves the page.
import {
  chiudeConIndietro,
  chiudiPrimaDiTornare,
  dallaCronologia,
  qualcosaSopra,
} from '@/utils/indietro'
import { ref } from 'vue'

describe('dallaCronologia', () => {
  it("is a back when the history already holds the target's entry", () => {
    expect(
      dallaCronologia({ fullPath: '/calendar' }, { current: '/calendar' }),
    ).toBe(true)
  })

  it("is the app's own navigation while the history holds where it starts", () => {
    expect(
      dallaCronologia(
        { fullPath: '/calendar' },
        { current: '/leads/view/list' },
      ),
    ).toBe(false)
    expect(dallaCronologia({ fullPath: '/calendar' }, null)).toBe(false)
  })
})

describe('chiudiPrimaDiTornare', () => {
  function router() {
    const guardie = []
    return {
      beforeEach(guardia) {
        guardie.push(guardia)
        return () => guardie.splice(guardie.indexOf(guardia), 1)
      },
      prova: (to, from) => guardie[0]?.(to, from),
      guardie,
    }
  }

  function finestra(corrente) {
    return { history: { state: { current: corrente } }, document }
  }

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('closes a sheet and stays when a back arrives while it is open', () => {
    const foglio = document.createElement('div')
    foglio.className = 'dialog-content'
    foglio.dataset.state = 'open'
    document.body.append(foglio)
    const premuto = vi.fn()
    document.addEventListener('keydown', premuto)
    const r = router()
    const smetti = chiudiPrimaDiTornare(r, finestra('/calendar'))
    expect(r.prova({ fullPath: '/calendar' }, { fullPath: '/leads' })).toBe(
      false,
    )
    expect(premuto.mock.calls[0][0].key).toBe('Escape')
    document.removeEventListener('keydown', premuto)
    smetti()
    expect(r.guardie).toHaveLength(0)
  })

  it("lets the app's own navigation go while a sheet is open", () => {
    const foglio = document.createElement('div')
    foglio.className = 'dialog-content'
    foglio.dataset.state = 'open'
    document.body.append(foglio)
    const r = router()
    chiudiPrimaDiTornare(r, finestra('/leads'))
    expect(r.prova({ fullPath: '/calendar' }, { fullPath: '/leads' })).toBe(
      true,
    )
  })

  it('closes the last panel of the page first, then lets the back go', () => {
    const r = router()
    chiudiPrimaDiTornare(r, finestra('/leads'))
    const chiudi = vi.fn()
    const togli = chiudeConIndietro(chiudi)
    expect(qualcosaSopra()).toBe(true)
    expect(r.prova({ fullPath: '/leads' }, { fullPath: '/calendar' })).toBe(
      false,
    )
    expect(chiudi).toHaveBeenCalledTimes(1)
    togli()
    expect(qualcosaSopra()).toBe(false)
    expect(r.prova({ fullPath: '/leads' }, { fullPath: '/calendar' })).toBe(
      true,
    )
  })

  it('takes a panel inside the sheet on top one step back before the sheet', () => {
    const foglio = document.createElement('div')
    foglio.className = 'dialog-content'
    foglio.dataset.state = 'open'
    const impostazioni = document.createElement('div')
    foglio.append(impostazioni)
    document.body.append(foglio)
    const premuto = vi.fn()
    document.addEventListener('keydown', premuto)
    const r = router()
    chiudiPrimaDiTornare(r, finestra('/altro'))
    const indietro = vi.fn()
    const togli = chiudeConIndietro(indietro, ref(impostazioni))
    expect(r.prova({ fullPath: '/altro' }, { fullPath: '/calendar' })).toBe(
      false,
    )
    expect(indietro).toHaveBeenCalledTimes(1)
    expect(premuto).not.toHaveBeenCalled()
    togli()
    expect(r.prova({ fullPath: '/altro' }, { fullPath: '/calendar' })).toBe(
      false,
    )
    expect(premuto.mock.calls[0][0].key).toBe('Escape')
    document.removeEventListener('keydown', premuto)
  })
})
