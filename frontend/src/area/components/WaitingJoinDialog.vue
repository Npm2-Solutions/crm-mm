<!--
  On a waiting list from the area: a service of the booking page, maybe with one
  professional, the days and parts of the day one can, until when, and how the
  centre tells. Joining again for the same service changes what one waits for.
-->
<template>
  <Dialog v-model="show" :options="{ title: __('Waiting list'), size: 'md' }">
    <template #body-content>
      <div v-if="!options" class="py-6 text-center text-p-sm text-ink-gray-5">
        …
      </div>
      <div v-else class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Choose the days and times you can: when a place frees up there we write to you, and it goes to whoever confirms first.',
            )
          }}
        </p>
        <FormControl
          v-model="form.service"
          type="select"
          :label="__('Service')"
          :placeholder="__('Choose a service')"
          :options="serviceOptions"
        />
        <FormControl
          v-if="staffOptions.length > 1"
          v-model="form.staff"
          type="select"
          :label="__('With')"
          :options="staffOptions"
        />
        <div class="flex flex-col gap-1.5">
          <span class="text-xs text-ink-gray-5">{{ __('Days') }}</span>
          <div class="flex flex-wrap gap-1.5">
            <Button
              v-for="giorno in GIORNI"
              :key="giorno"
              class="touch-target"
              :variant="form.days.includes(giorno) ? 'solid' : 'subtle'"
              :aria-pressed="form.days.includes(giorno)"
              :label="giornoBreve(giorno, locale)"
              @click="form.days = scegli(form.days, giorno, GIORNI)"
            />
          </div>
        </div>
        <div class="flex flex-col gap-1.5">
          <span class="text-xs text-ink-gray-5">{{ __('Times of day') }}</span>
          <div class="flex flex-wrap gap-1.5">
            <Button
              v-for="parte in PARTI"
              :key="parte"
              class="touch-target"
              :variant="form.parts.includes(parte) ? 'solid' : 'subtle'"
              :aria-pressed="form.parts.includes(parte)"
              :label="__(NOMI_DELLE_PARTI[parte])"
              @click="form.parts = scegli(form.parts, parte, PARTI)"
            />
          </div>
          <span
            v-if="!form.days.length && !form.parts.length"
            class="text-p-sm text-ink-gray-5"
          >
            {{ __('Nothing chosen: any day, any time.') }}
          </span>
        </div>
        <FormControl
          v-model="form.until"
          type="date"
          :format="FORMATO_DEL_CAMPO"
          :label="__('Until')"
        />
        <FormControl
          v-if="options.channels.length > 1"
          v-model="form.channel"
          type="select"
          :label="__('Write to me by')"
          :options="options.channels.map((c) => ({ label: __(c), value: c }))"
        />
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Put me on the list')"
          :loading="busy"
          :disabled="!form.service"
          @click="join"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  GIORNI,
  NOMI_DELLE_PARTI,
  PARTI,
  giornoBreve,
  scegli,
} from '@/utils/attese'
import { Button, Dialog, ErrorMessage, FormControl, call } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'
import { area, messageOf } from '../store'
import { locale } from '../translation'
import { FORMATO_DEL_CAMPO } from '../dates'

const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })

const options = ref(null)
const form = reactive({})
const busy = ref(false)
const error = ref('')

watch(show, async (open) => {
  if (!open) return
  error.value = ''
  options.value = null
  try {
    options.value = await call('crm.area.api.get_waiting_options', {
      person: area.person,
    })
    Object.assign(form, {
      service:
        options.value.services.length === 1
          ? options.value.services[0].name
          : '',
      staff: '',
      days: [],
      parts: [],
      until: options.value.until,
      channel: options.value.channels[0] || 'Email',
    })
  } catch (e) {
    error.value = __(messageOf(e))
    options.value = { services: [], channels: ['Email'], until: '' }
  }
})

const serviceOptions = computed(() =>
  (options.value?.services || []).map((service) => ({
    label: service.service_name,
    value: service.name,
  })),
)

const staffOptions = computed(() => {
  const service = (options.value?.services || []).find(
    (one) => one.name === form.service,
  )
  if (!service?.staff?.length) return []
  return [
    { label: __('Anybody'), value: '' },
    ...service.staff.map((one) => ({ label: one.name, value: one.user })),
  ]
})

watch(
  () => form.service,
  () => (form.staff = ''),
)

async function join() {
  busy.value = true
  error.value = ''
  try {
    const done = await call('crm.area.api.join_waiting_list', {
      person: area.person,
      service: form.service,
      staff: form.staff || null,
      days: JSON.stringify(form.days),
      parts: JSON.stringify(form.parts),
      until: form.until || null,
      channel: form.channel,
    })
    show.value = false
    emit('changed', done)
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}
</script>
