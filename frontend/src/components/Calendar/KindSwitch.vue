<!--
  Appointment or event: the first line of anything new on the calendar.

  They were two buttons in the header and two different screens, and a click
  on an empty slot always made an event — somebody booking clients all day
  started every booking by closing the wrong form. Now there is one «New»,
  the panel opens on whichever was made last, and this says which it is: an
  appointment is a service for a client, with who delivers it and where; an
  event is everything else. What was already filled in — the day, the time —
  goes across when it is switched.
-->
<template>
  <div class="px-4.5 pb-3">
    <TabButtons
      class="w-full [&_button>span]:w-full [&_button]:w-full [&_div]:w-full"
      :modelValue="modelValue"
      :buttons="buttons"
      @update:modelValue="(value) => value !== modelValue && pick(value)"
    />
    <p class="mt-1.5 text-p-xs text-ink-gray-5">{{ hint }}</p>
  </div>
</template>

<script setup>
import { TabButtons } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  // appointment or event
  modelValue: { type: String, default: 'appointment' },
})

const emit = defineEmits(['update:modelValue'])

const buttons = [
  { label: __('Appointment'), value: 'appointment' },
  { label: __('Event'), value: 'event' },
]

const hint = computed(() =>
  props.modelValue === 'appointment'
    ? __('A service for a client, with who delivers it and where.')
    : __('Anything else: a meeting, a call, time blocked out.'),
)

function pick(value) {
  emit('update:modelValue', value)
}
</script>
