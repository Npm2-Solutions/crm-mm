// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A phone's list: a page at a time, and as it was left when a back returns.
import { useElencoDelTelefono } from '@/composables/elencoDelTelefono'
import { dimenticaTutto, segnaIRitorni } from '@/utils/ritorno'
import { createApp, h, nextTick } from 'vue'

// the server: 30 people a page, «Persona 0» to «Persona 99»; and what it was
// asked
const chieste = []
function pagina({ text = '', start = 0 }) {
  chieste.push({ text, start })
  const tutte = Array.from({ length: 100 }, (_, i) => ({
    name: `p${i}`,
    lead_name: `Persona ${i}`,
  })).filter((p) => p.lead_name.includes(text))
  const rows = tutte.slice(start, start + 30)
  return { rows, more: tutte.length > start + 30, start }
}

vi.mock('frappe-ui', async () => {
  const { reactive } = await import('vue')
  return {
    call: async (_url, parametri) => pagina(parametri),
    createResource(opzioni) {
      const risorsa = reactive({
        loading: false,
        fetched: false,
        submit(parametri) {
          const dati = pagina(parametri)
          risorsa.fetched = true
          opzioni.onSuccess(dati)
          return Promise.resolve(dati)
        },
      })
      return risorsa
    },
    // at once: the test types and looks
    debounce: (fn) => fn,
  }
})

const URL = 'crm.api.sul_telefono.get_people'

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
    vai(percorso) {
      win.history.state = { current: '/altrove' }
      guardie.forEach((g) => g({ fullPath: percorso }))
    },
    indietro(percorso) {
      win.history.state = { current: percorso }
      guardie.forEach((g) => g({ fullPath: percorso }))
    },
  }
}

function monta() {
  let elenco
  const app = createApp({
    setup() {
      elenco = useElencoDelTelefono(URL, 'persone')
      return () => h('div', { ref: elenco.contenitore })
    },
  })
  const radice = document.createElement('div')
  document.body.append(radice)
  app.mount(radice)
  return { elenco, smonta: () => app.unmount() }
}

let smetti = () => {}
beforeEach(() => {
  chieste.length = 0
})
afterEach(() => {
  smetti()
  dimenticaTutto()
  document.body.innerHTML = ''
})

describe('useElencoDelTelefono', () => {
  it('loads the first page, and the next one near the bottom', () => {
    const { elenco, smonta } = monta()
    expect(elenco.righe.value).toHaveLength(30)
    expect(elenco.altre.value).toBe(true)
    elenco.forseAltre()
    expect(chieste.at(-1)).toEqual({ text: '', start: 30 })
    expect(elenco.righe.value).toHaveLength(60)
    smonta()
  })

  it('comes back as it was on a back: the search, the rows, the pages asked again', async () => {
    const n = navigatore()
    smetti = segnaIRitorni(n.router, n.win)
    n.vai('/leads')
    const prima = monta()
    prima.elenco.testo.value = 'Persona 1'
    await nextTick()
    expect(prima.elenco.righe.value.map((p) => p.name)).toContain('p19')
    prima.smonta()

    n.indietro('/leads')
    chieste.length = 0
    const dopo = monta()
    // at once, before the server answers
    expect(dopo.elenco.testo.value).toBe('Persona 1')
    expect(dopo.elenco.righe.value).toHaveLength(11)
    // then the page it had, asked again with its search
    await new Promise((r) => setTimeout(r, 0))
    expect(chieste).toEqual([{ text: 'Persona 1', start: 0 }])
    dopo.smonta()
  })

  it('starts anew from the menu', async () => {
    const n = navigatore()
    smetti = segnaIRitorni(n.router, n.win)
    n.vai('/leads')
    const prima = monta()
    prima.elenco.testo.value = 'Persona 1'
    await nextTick()
    prima.smonta()

    n.vai('/leads')
    const dopo = monta()
    expect(dopo.elenco.testo.value).toBe('')
    expect(dopo.elenco.righe.value).toHaveLength(30)
    dopo.smonta()
  })
})
