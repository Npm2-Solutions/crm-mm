// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A phone's list of people, contacts, companies, calls or notes
 * (crm/api/sul_telefono.py): found by typing, a page at a time as it scrolls,
 * pulled down to reload, and found again as it was left when a back returns to
 * it - its search, its rows, where it was - then brought up to date.
 */
import { useRitorno } from '@/composables/ritorno'
import { useTiraPerAggiornare } from '@/composables/tiraPerAggiornare'
import { senzaDoppioni } from '@/utils/ritorno'
import { call, createResource, debounce } from 'frappe-ui'
import { ref, watch } from 'vue'

/**
 * The list the server's `url` gives a page of (`{ rows, more, start }`),
 * remembered as `chiave`. Gives back what the screen draws: `testo` (the
 * search), `righe`, `altre`, `contenitore` (the box that scrolls), `carica`,
 * `cerca()`, `forseAltre()` (on the box's scroll) and `tira` (the pull's
 * mark).
 */
export function useElencoDelTelefono(url, chiave) {
  const testo = ref('')
  const righe = ref([])
  const altre = ref(false)
  const contenitore = ref(null)
  // where each page loaded since the first starts: a list put back asks them
  // all again
  let inizi = [0]

  const carica = createResource({
    url,
    onSuccess(dati) {
      if (dati.start) {
        righe.value = senzaDoppioni([...righe.value, ...dati.rows])
        if (!inizi.includes(dati.start)) inizi.push(dati.start)
      } else {
        righe.value = dati.rows
        inizi = [0]
      }
      altre.value = dati.more
    },
  })

  function cerca() {
    return carica.submit({ text: testo.value.trim(), start: 0 })
  }

  // the list put back, brought up to date page by page and in silence: what
  // changed while it was away (a number put right on the person's page) is
  // what it shows, where it was
  async function rinfresca() {
    const parole = testo.value.trim()
    try {
      const pagine = await Promise.all(
        inizi.map((start) => call(url, { text: parole, start })),
      )
      if (testo.value.trim() !== parole) return
      righe.value = senzaDoppioni(pagine.flatMap((pagina) => pagina.rows))
      altre.value = Boolean(pagine.at(-1)?.more)
    } catch {
      if (testo.value.trim() === parole) cerca()
    }
  }

  const tornata = useRitorno(chiave, {
    contenitore,
    stato: () => ({
      testo: testo.value,
      righe: righe.value,
      altre: altre.value,
      inizi: [...inizi],
    }),
    rimetti: (salvato) => {
      testo.value = salvato.testo
      righe.value = salvato.righe
      altre.value = salvato.altre
      inizi = [...salvato.inizi]
    },
  })

  const tira = useTiraPerAggiornare(contenitore, cerca)

  // listening once the search is put back: putting it back asks for nothing
  watch(testo, debounce(cerca, 300))
  if (tornata && righe.value.length) rinfresca()
  else cerca()

  // near the bottom: the next page, once
  function forseAltre() {
    const el = contenitore.value
    if (!el || !altre.value || carica.loading) return
    if (el.scrollTop + el.clientHeight < el.scrollHeight - 300) return
    carica.submit({ text: testo.value.trim(), start: righe.value.length })
  }

  return { testo, righe, altre, contenitore, carica, cerca, forseAltre, tira }
}
