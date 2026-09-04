<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between">
      <FormLabel :label="label" />
      <Button
        v-if="!modelValue.length"
        size="sm"
        variant="ghost"
        :label="__('Mon–Fri 9–18')"
        @click="fillWeekdays"
      />
    </div>
    <p v-if="hint" class="text-p-xs text-ink-gray-5">{{ hint }}</p>
    <div
      v-for="(row, i) in modelValue"
      :key="i"
      class="grid grid-cols-[1fr_1fr_1fr_32px] items-center gap-2"
    >
      <FormControl
        :modelValue="row.workday"
        type="select"
        :options="weekdayOptions"
        @update:modelValue="(v) => patch(i, { workday: v })"
      />
      <FormControl
        :modelValue="short(row.start_time)"
        type="time"
        @update:modelValue="(v) => patch(i, { start_time: v })"
      />
      <FormControl
        :modelValue="short(row.end_time)"
        type="time"
        @update:modelValue="(v) => patch(i, { end_time: v })"
      />
      <Button variant="ghost" icon="lucide-trash-2" @click="removeRow(i)" />
    </div>
    <Button
      variant="ghost"
      size="sm"
      class="self-start"
      :label="__('Add hours')"
      iconLeft="plus"
      @click="addRow"
    />
  </div>
</template>

<script setup>
import { Button, FormControl, FormLabel } from 'frappe-ui'
import { computed } from 'vue'

const WEEKDAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

const props = defineProps({
  /** `[{ workday, start_time, end_time }]` */
  modelValue: { type: Array, default: () => [] },
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const weekdayOptions = computed(() =>
  WEEKDAYS.map((day) => ({ label: __(day), value: day })),
)

/** `"09:00:00"` and `"09:00"` both come back from the server. */
function short(value) {
  return String(value || '').slice(0, 5)
}

function patch(index, changes) {
  const next = props.modelValue.map((row, i) =>
    i === index ? { ...row, ...changes } : row,
  )
  emit('update:modelValue', next)
}

function addRow() {
  emit('update:modelValue', [
    ...props.modelValue,
    { workday: 'Monday', start_time: '09:00', end_time: '18:00' },
  ])
}

function removeRow(index) {
  emit(
    'update:modelValue',
    props.modelValue.filter((_, i) => i !== index),
  )
}

function fillWeekdays() {
  emit(
    'update:modelValue',
    WEEKDAYS.slice(0, 5).map((day) => ({
      workday: day,
      start_time: '09:00',
      end_time: '18:00',
    })),
  )
}
</script>
