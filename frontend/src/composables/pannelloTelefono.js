// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The phone at hand's data, one for the whole app: the button's badge (the
// callbacks owed now) and the panel's last calls come from the same call, asked
// again when the panel opens, when the window comes back and every few minutes.
import { callEnabled } from '@/composables/telephony'
import { usersStore } from '@/stores/users'
import { createResource } from 'frappe-ui'
import { useIntervalFn, useEventListener } from '@vueuse/core'
import { computed, effectScope, watch } from 'vue'

let pannello = null

export function usePannelloTelefono() {
  const { puo } = usersStore()
  // the phone is there where a telephony is on, for whoever calls or reads calls
  const visibile = computed(
    () =>
      callEnabled.value && (puo('telefono.chiama') || puo('telefono.registro')),
  )

  if (!pannello) {
    pannello = createResource({
      url: 'crm.telephony.pannello.get_phone_panel',
      cache: 'phone-panel',
    })
    const aggiorna = () => {
      if (visibile.value && document.visibilityState === 'visible')
        pannello.reload()
    }
    // the app's, not the first component's that asked: it outlives them all
    effectScope(true).run(() => {
      watch(visibile, (si) => si && pannello.reload(), { immediate: true })
      useIntervalFn(aggiorna, 3 * 60 * 1000)
      useEventListener(window, 'focus', aggiorna)
    })
  }

  const dovute = computed(() => pannello.data?.callbacks?.due || 0)

  return { pannello, visibile, dovute }
}
