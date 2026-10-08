<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  «I'm here» on an appointment (crm.area.api.check_in): from half an hour
  before it until it ends, one tap tells the centre the person is there - the
  reception desk's waiting room counts from then, and the desk is told. Once
  said, a line says so. When it shows comes from the server's clock (arrivo.js).
-->
<template>
  <div v-if="stato === 'aperto'" class="mt-3 flex flex-col gap-1.5">
    <Button
      variant="solid"
      size="lg"
      class="w-full"
      :label="__('I’m here')"
      :loading="busy"
      @click="arrivo"
    >
      <template #prefix>
        <LucideMapPinCheck class="size-4" aria-hidden="true" />
      </template>
    </Button>
    <ErrorMessage :message="error" />
  </div>
  <p
    v-else-if="stato === 'arrivato'"
    class="mt-3 flex items-start gap-1.5 text-sm font-semibold"
    role="status"
  >
    <LucideCircleCheck class="mt-0.5 size-4 shrink-0" aria-hidden="true" />
    {{ __('You are in the waiting room: the centre knows you are here.') }}
  </p>
</template>

<script setup>
import { Button, ErrorMessage, call } from 'frappe-ui'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideMapPinCheck from '~icons/lucide/map-pin-check'
import { prossimoCambio, statoDellArrivo } from '../arrivo'
import { area, messageOf } from '../store'

const props = defineProps({ appointment: { type: Object, required: true } })

const busy = ref(false)
const error = ref('')
const detto = ref(false)
// when the server answered, and how long ago: the window is counted from there
const ricevuto = ref(Date.now())
const trascorsi = ref(0)
let timer = null

function guarda() {
  clearTimeout(timer)
  trascorsi.value = Date.now() - ricevuto.value
  const fra = prossimoCambio(props.appointment, trascorsi.value)
  // a phone asleep wakes late: looking again then is enough
  if (fra !== null) timer = setTimeout(guarda, fra + 500)
}

watch(
  () => props.appointment,
  () => {
    ricevuto.value = Date.now()
    detto.value = false
    guarda()
  },
  { immediate: true },
)
onBeforeUnmount(() => clearTimeout(timer))

const stato = computed(() =>
  detto.value
    ? 'arrivato'
    : statoDellArrivo(props.appointment, trascorsi.value),
)

async function arrivo() {
  busy.value = true
  error.value = ''
  try {
    await call('crm.area.api.check_in', {
      person: area.person,
      appointment: props.appointment.name,
    })
    detto.value = true
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}
</script>
