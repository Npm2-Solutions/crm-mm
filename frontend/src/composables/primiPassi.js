// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The first steps (doc 37), shared by the sidebar's card and the panel: the
// server's list (crm/primi_passi.py), whether the panel is open, whether the
// person hid them - on this browser, a convenience - and taking a step.
import {
  activeSettingsPage,
  mobileSidebarOpened,
  showSettings,
} from '@/composables/settings'
import { useBroadcast } from '@/composables/useBroadcast'
import { sessionStore } from '@/stores/session'
import { daMostrare, riassunto } from '@/utils/primiPassi'
import { createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

export const pannelloPrimiPassi = ref(false)

const passi = createResource({
  url: 'crm.primi_passi.get_first_steps',
})

const nascosti = ref(null)

// a step is mostly taken in the settings: closing them, the list is read again
let ascolta = false
function ricaricaAllaChiusura() {
  if (ascolta) return
  ascolta = true
  watch(showSettings, (aperte) => {
    if (!aperte && passi.fetched) passi.reload()
  })
}

function chiave() {
  return 'primiPassiNascosti:' + (sessionStore().user || '')
}

function letti() {
  try {
    return localStorage.getItem(chiave()) === '1'
  } catch {
    return false
  }
}

export function usePrimiPassi() {
  const router = useRouter()
  const { send } = useBroadcast()
  if (nascosti.value === null) nascosti.value = letti()
  if (!passi.fetched && !passi.loading) passi.fetch()
  ricaricaAllaChiusura()

  const stato = computed(() => riassunto(passi.data))
  const visibili = computed(() => daMostrare(passi.data, nascosti.value))

  // A step done elsewhere ticks itself: the list is read again when the panel
  // opens, and when the settings close (above).
  function ricarica() {
    passi.reload()
  }

  function nascondi() {
    nascosti.value = true
    pannelloPrimiPassi.value = false
    try {
      localStorage.setItem(chiave(), '1')
    } catch {
      // a browser that keeps nothing shows them again next time
    }
  }

  function mostra() {
    nascosti.value = false
    try {
      localStorage.removeItem(chiave())
    } catch {
      // nothing kept, nothing to take away
    }
  }

  function apriPannello() {
    mobileSidebarOpened.value = false
    pannelloPrimiPassi.value = true
    ricarica()
  }

  // Where a step is taken: a page of the settings, or of the app, with what to
  // open there.
  function fai(passo) {
    pannelloPrimiPassi.value = false
    mobileSidebarOpened.value = false
    if (passo.page) {
      activeSettingsPage.value = passo.page
      showSettings.value = true
    } else if (passo.route) {
      router.push({ name: passo.route })
      if (passo.action === 'new' && passo.route === 'Leads')
        send('trigger_lead_create', true)
    }
  }

  return {
    passi,
    stato,
    visibili,
    nascosti,
    ricarica,
    nascondi,
    mostra,
    apriPannello,
    fai,
  }
}
