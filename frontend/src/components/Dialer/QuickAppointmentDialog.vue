<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Book an appointment'), size: 'xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="rounded-md bg-surface-gray-2 px-3 py-2 text-sm">
          <span class="text-ink-gray-8">{{ context?.display_name }}</span>
          <span class="text-ink-gray-5"> · {{ context?.number }}</span>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.service"
            type="select"
            :label="__('Service')"
            :options="serviceOptions"
            @update:modelValue="loadSlots"
          />
          <FormControl
            v-model="form.from"
            type="date"
            :label="__('From')"
            @update:modelValue="loadSlots"
          />
        </div>

        <div v-if="slots.loading" class="flex justify-center py-8">
          <LoadingIndicator class="size-5" />
        </div>

        <ErrorMessage :message="error" />

        <div
          v-if="!slots.loading && form.service && !days.length && !error"
          class="rounded-md border border-dashed border-outline-gray-2 px-3 py-8 text-center text-sm text-ink-gray-5"
        >
          {{ __('No free slots in the next two weeks for this service.') }}
        </div>

        <div v-for="day in days" :key="day.label" class="flex flex-col gap-1.5">
          <div class="text-sm font-medium text-ink-gray-7">{{ day.label }}</div>
          <div class="flex flex-wrap gap-1.5">
            <Button
              v-for="slot in day.slots"
              :key="slot.start"
              :variant="picked?.start === slot.start ? 'solid' : 'outline'"
              :label="time(slot.start)"
              @click="picked = slot"
            />
          </div>
        </div>

        <FormControl
          v-if="picked"
          v-model="form.notes"
          type="textarea"
          :label="__('Notes')"
          :placeholder="__('What was agreed on the call (optional)')"
        />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Book')"
          :disabled="!picked"
          :loading="booking"
          @click="book"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  createResource,
  dayjs,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  context: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue', 'booked'])

const HORIZON_DAYS = 14

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const form = reactive({
  service: '',
  from: dayjs().format('YYYY-MM-DD'),
  notes: '',
})
const picked = ref(null)
const booking = ref(false)
const error = ref('')

const meta = createResource({
  url: 'crm.api.appointments.get_scheduler_meta',
  cache: 'scheduler-meta',
})

const slots = createResource({
  url: 'crm.api.appointments.get_available_slots',
  onError: (e) => (error.value = e.messages?.[0] || __('Could not load slots')),
})

const serviceOptions = computed(() => [
  { label: __('Choose a service'), value: '' },
  ...(meta.data?.services || []).map((s) => ({
    label: s.service_name,
    value: s.name,
  })),
])

// the picker is a flat list of times grouped under their day: mid-call nobody
// wants a month view, they want the next few openings they can offer out loud
const days = computed(() => {
  const grouped = new Map()
  for (const slot of slots.data || []) {
    const key = dayjs(slot.start).format('YYYY-MM-DD')
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key).push(slot)
  }
  return [...grouped.entries()].map(([key, list]) => ({
    label: dayjs(key).format('dddd D MMMM'),
    slots: list,
  }))
})

function time(value) {
  return dayjs(value).format('HH:mm')
}

function loadSlots() {
  picked.value = null
  error.value = ''
  if (!form.service) return
  slots.fetch({
    service: form.service,
    start_date: form.from,
    end_date: dayjs(form.from).add(HORIZON_DAYS, 'day').format('YYYY-MM-DD'),
  })
}

function book() {
  const record = props.context?.record
  if (!picked.value || !record) return
  booking.value = true
  error.value = ''

  createResource({
    url: 'crm.api.appointments.save_appointment',
    params: {
      appointment: {
        service: form.service,
        status: 'Scheduled',
        starts_on: picked.value.start,
        ends_on: picked.value.end,
        notes: form.notes || null,
        // the slot already resolved who and what is free at that instant; sending
        // it back keeps the booking on the same assignment the agent was shown
        staff: (picked.value.staff || []).map((user) => ({ user })),
        resources: picked.value.resources || [],
        participants: [
          {
            party_type: record.doctype,
            party: record.name,
            participant_name: props.context.display_name || record.name,
            email: record.email || null,
            phone: props.context.number || record.mobile_no || null,
          },
        ],
      },
    },
    auto: true,
    onSuccess: () => {
      booking.value = false
      show.value = false
      picked.value = null
      form.notes = ''
      toast.success(__('Appointment booked'))
      emit('booked')
    },
    onError: (e) => {
      booking.value = false
      error.value = e.messages?.[0] || __('Could not book the appointment')
    },
  })
}

watch(show, (open) => {
  if (!open) return
  error.value = ''
  meta.fetch()
  if (form.service) loadSlots()
})
</script>
