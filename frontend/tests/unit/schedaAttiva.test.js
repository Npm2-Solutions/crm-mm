// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The tab one is on, tapped again, takes its page back to the top.
import {
  alToccoDellaScheda,
  allaCimaConLaScheda,
  scatoleScorse,
} from '@/utils/schedaAttiva'

function pagina() {
  document.body.innerHTML = `
    <div data-cornice-telefono>
      <div class="overflow-y-auto" id="elenco"></div>
      <div class="overflow-y-auto" id="ferma"></div>
      <div class="dialog-scroll-container"><div class="overflow-y-auto" id="foglio"></div></div>
      <nav data-slot="mobile-nav">
        <button aria-current="page" id="qui"><span>Persone</span></button>
        <a href="/crm/calendar" id="altrove">Agenda</a>
      </nav>
    </div>`
  const elenco = document.getElementById('elenco')
  const foglio = document.getElementById('foglio')
  elenco.scrollTop = 600
  foglio.scrollTop = 200
  elenco.scrollTo = vi.fn()
  foglio.scrollTo = vi.fn()
  return { elenco, foglio }
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('allaCimaConLaScheda', () => {
  it('finds the page boxes that are scrolled, not a sheet’s', () => {
    const { elenco } = pagina()
    expect(scatoleScorse(document.body)).toEqual([elenco])
  })

  it('brings the page back to the top when its own tab is tapped again', () => {
    const { elenco, foglio } = pagina()
    const smetti = allaCimaConLaScheda(window)
    document.querySelector('#qui span').click()
    expect(elenco.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' })
    expect(foglio.scrollTo).not.toHaveBeenCalled()
    smetti()
  })

  it('leaves the page alone when another tab is tapped', () => {
    const { elenco } = pagina()
    const smetti = allaCimaConLaScheda(window)
    document
      .getElementById('altrove')
      .dispatchEvent(
        new MouseEvent('click', { bubbles: true, cancelable: true }),
      )
    expect(elenco.scrollTo).not.toHaveBeenCalled()
    smetti()
  })

  it('lets the page do its own first: a conversation open goes back to the list', () => {
    const { elenco } = pagina()
    const smetti = allaCimaConLaScheda(window)
    const torna = vi.fn(() => true)
    const togli = alToccoDellaScheda(torna)
    document.querySelector('#qui span').click()
    expect(torna).toHaveBeenCalledTimes(1)
    expect(elenco.scrollTo).not.toHaveBeenCalled()
    togli()
    document.querySelector('#qui span').click()
    expect(elenco.scrollTo).toHaveBeenCalledTimes(1)
    smetti()
  })
})
