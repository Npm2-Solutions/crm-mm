<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  «Enter the visit» on an online visit (crm.area.api.enter_online_visit): from a
  quarter of an hour before it until it ends, one tap opens its room; before, a
  line says from what time. The room's link is asked when the person taps, never
  kept in the page. When it shows comes from the server's clock (visitaOnline.js).
-->
<template>
  <div v-if="stato === 'aperta'" class="mt-3 flex flex-col gap-1.5">
    <Button
      variant="solid"
      size="lg"
      class="w-full"
      :label="__('Enter the visit')"
      :loading="busy"
      @click="entra"
    >
      <template #prefix>
        <LucideVideo class="size-4" aria-hidden="true" />
      </template>
    </Button>
    <ErrorMessage :message="error" />
  </div>
  <p
    v-else-if="stato === 'presto'"
    class="mt-2 flex items-start gap-1.5 text-sm"
    :class="deep ? '' : 'text-ink-gray-6'"
  >
    <LucideVideo class="mt-0.5 size-4 shrink-0" aria-hidden="true" />
    {{
      __(
        'You enter the visit from here from {0}, 15 minutes before it starts.',
        [appointment.online_visit.opens_at],
      )
    }}
  </p>
  <p
    v-else-if="stato === 'senza'"
    class="mt-2 flex items-start gap-1.5 text-sm"
    :class="deep ? '' : 'text-ink-gray-6'"
  >
    <LucideVideo class="mt-0.5 size-4 shrink-0" aria-hidden="true" />
    {{ __('The link to enter the visit will be here: the centre adds it.') }}
  </p>
</template>

<script setup>
import { Button, ErrorMessage, call } from 'frappe-ui'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import LucideVideo from '~icons/lucide/video'
import {
  apriLaStanza,
  prossimoCambioDellaVisita,
  statoDellaVisita,
} from '../visitaOnline'
import { area, messageOf } from '../store'

const props = defineProps({
  appointment: { type: Object, required: true },
  // on the next appointment's deep block: its own colours
  deep: { type: Boolean, default: false },
})

const busy = ref(false)
const error = ref('')
// when the server answered, and how long ago: the window is counted from there
const ricevuto = ref(Date.now())
const trascorsi = ref(0)
let timer = null

function guarda() {
  clearTimeout(timer)
  trascorsi.value = Date.now() - ricevuto.value
  const fra = prossimoCambioDellaVisita(props.appointment, trascorsi.value)
  // a phone asleep wakes late: looking again then is enough
  if (fra !== null) timer = setTimeout(guarda, fra + 500)
}

watch(
  () => props.appointment,
  () => {
    ricevuto.value = Date.now()
    guarda()
  },
  { immediate: true },
)
onBeforeUnmount(() => clearTimeout(timer))

const stato = computed(() =>
  statoDellaVisita(props.appointment, trascorsi.value),
)

function apriUnaScheda() {
  try {
    const scheda = window.open('', '_blank')
    if (scheda) scheda.opener = null
    return scheda
  } catch {
    return null
  }
}

async function entra() {
  busy.value = true
  error.value = ''
  // the tab opened while the tap is still the browser's: after the call it
  // would be a popup it blocks
  const scheda = apriUnaScheda()
  try {
    const risposta = await call('crm.area.api.enter_online_visit', {
      person: area.person,
      appointment: props.appointment.name,
    })
    apriLaStanza(risposta?.url, scheda)
  } catch (e) {
    scheda?.close?.()
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}
</script>
