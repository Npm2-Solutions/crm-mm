// Modifications copyright (c) 2026, NPM2 Solutions Srl

// The demo data (doc 53): whether they are in, loading them in a job whose
// progress arrives by the socket, taking them away in one request.

import { call, createResource, toast } from 'frappe-ui'
import { ref } from 'vue'
import { globalStore } from '@/stores/global'

const EVENTO = 'crm_demo_data'

const isDemoDataCreated = ref(window.demo_data_created || false)
// the part being made and its step, while a job makes them
const avanzamento = ref(null)
const togliendo = ref(false)

const stato = createResource({
  url: 'crm.demo.api.get_demo_state',
  onSuccess(dati) {
    isDemoDataCreated.value = Boolean(dati?.demo_data_created)
    if (dati?.working) {
      avanzamento.value = dati.progress ||
        avanzamento.value || { done: 0, total: 0 }
      segui()
    } else if (avanzamento.value && timer) {
      // the job ended and the socket did not say so: the page tells; a part
      // still to make is one that failed
      finito(!dati.demo_data_created || Boolean(dati.to_make?.length))
    } else {
      avanzamento.value = null
    }
  },
})

let inAscolto = false
let timer = null
let chiuso = false

// the job's end, said once whichever way it arrives
function finito(fallito) {
  if (chiuso) return
  chiuso = true
  clearInterval(timer)
  timer = null
  avanzamento.value = null
  if (fallito) {
    toast.warning(__('Some parts could not be made: the others are in.'))
  } else {
    toast.success(__('The demo data are ready.'))
  }
  // every list and the stores read them again
  setTimeout(() => window.location.reload(), 1200)
}

// what the job does, asked every few seconds: the socket may not be there
function segui() {
  if (timer) return
  chiuso = false
  timer = setInterval(() => stato.reload(), 4000)
}

function ascolta() {
  if (inAscolto) return
  inAscolto = true
  globalStore().$socket.on(EVENTO, (dati) => {
    if (dati?.state === 'progress') {
      avanzamento.value = {
        part: dati.parte,
        step: dati.step,
        done: dati.done,
        total: dati.total,
      }
    } else if (dati?.state === 'done') {
      finito(Boolean(dati.failed?.length))
    }
  })
}

export function useDemoData() {
  const { $dialog } = globalStore()

  async function loadDemoData() {
    ascolta()
    avanzamento.value = { done: 0, total: 0 }
    try {
      const esito = await call('crm.demo.api.load_demo_data')
      if (esito?.working) segui()
      else avanzamento.value = null
    } catch (errore) {
      avanzamento.value = null
      toast.error(
        errore?.messages?.[0] || __('The demo data could not be made.'),
      )
    }
    stato.reload()
  }

  async function togli() {
    togliendo.value = true
    try {
      await call('crm.demo.api.clear_demo_data')
      isDemoDataCreated.value = false
      toast.success(__('The demo data were removed.'))
      setTimeout(() => window.location.reload(), 800)
    } catch (errore) {
      togliendo.value = false
      toast.error(
        errore?.messages?.[0] || __('The demo data could not be removed.'),
      )
    }
  }

  const clearDemoData = () => {
    $dialog({
      title: __('Remove the demo data'),
      message: __(
        'Everything the demo made goes, and with it what is about its people, what you wrote too: notes, appointments, messages. The services, rooms and price lists you used for your own clients stay.',
      ),
      actions: [
        {
          label: __('Remove', null, 'Demo data'),
          theme: 'red',
          variant: 'solid',
          onClick: (close) => {
            close()
            togli()
          },
        },
      ],
    })
  }

  return {
    isDemoDataCreated,
    stato,
    avanzamento,
    togliendo,
    ascolta,
    loadDemoData,
    clearDemoData,
  }
}
