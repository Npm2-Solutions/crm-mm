<template>
  <div class="flex flex-col gap-2">
    <div v-if="label || hint" class="flex flex-col gap-0.5">
      <FormLabel v-if="label" :label="label" />
      <p v-if="hint" class="text-p-xs text-ink-gray-5">{{ hint }}</p>
    </div>
    <div
      class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
    >
      <div
        v-for="day in WEEKDAYS"
        :key="day"
        class="group flex min-h-11 items-start gap-3 px-3 py-2"
      >
        <label class="flex h-7 w-32 shrink-0 cursor-pointer items-center gap-2">
          <Switch
            size="sm"
            :modelValue="windows(day).length > 0"
            @update:modelValue="(on) => toggleDay(day, on)"
          />
          <span
            class="text-p-sm"
            :class="windows(day).length ? 'text-ink-gray-8' : 'text-ink-gray-5'"
            >{{ __(day) }}</span
          >
        </label>
        <div
          v-if="windows(day).length"
          class="flex flex-1 flex-wrap items-center gap-2"
        >
          <div
            v-for="(row, i) in windows(day)"
            :key="i"
            class="flex items-center gap-1"
          >
            <FormControl
              class="w-[92px]"
              :modelValue="hhmm(row.start_time)"
              type="time"
              @update:modelValue="(v) => patch(row, { start_time: v })"
            />
            <span class="text-ink-gray-4">–</span>
            <FormControl
              class="w-[92px]"
              :modelValue="hhmm(row.end_time)"
              type="time"
              @update:modelValue="(v) => patch(row, { end_time: v })"
            />
            <Button
              variant="ghost"
              size="sm"
              icon="lucide-x"
              :tooltip="__('Remove')"
              @click="remove(row)"
            />
          </div>
          <Button
            variant="ghost"
            size="sm"
            icon="lucide-plus"
            :tooltip="__('Add a time slot (e.g. after lunch)')"
            @click="addWindow(day)"
          />
          <span class="grow" />
          <Button
            variant="ghost"
            size="sm"
            class="opacity-0 transition-opacity group-hover:opacity-100"
            :label="__('Copy to all')"
            :tooltip="__('Use these hours on every open day')"
            icon-left="lucide-copy"
            @click="copyToAll(day)"
          />
        </div>
        <span v-else class="flex h-7 items-center text-p-sm text-ink-gray-4">
          {{ __('Closed') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
// A week, one line per day: switch it on, give it one or more time slots.
// The value stays the flat `[{ workday, start_time, end_time }]` the server
// stores, so every caller (team rota, services, studio hours) is unchanged.
import { Button, FormControl, FormLabel, Switch } from 'frappe-ui'
import { hhmm } from '@/utils/scheduler'

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

function windows(day) {
  return props.modelValue
    .filter((row) => row.workday === day)
    .sort((a, b) => hhmm(a.start_time).localeCompare(hhmm(b.start_time)))
}

// rows keep WEEKDAYS order so the saved table reads Monday → Sunday
function commit(rows) {
  emit(
    'update:modelValue',
    WEEKDAYS.flatMap((day) =>
      rows
        .filter((row) => row.workday === day)
        .sort((a, b) => hhmm(a.start_time).localeCompare(hhmm(b.start_time))),
    ),
  )
}

function patch(row, changes) {
  commit(props.modelValue.map((r) => (r === row ? { ...r, ...changes } : r)))
}

function remove(row) {
  commit(props.modelValue.filter((r) => r !== row))
}

function toggleDay(day, on) {
  if (!on) {
    commit(props.modelValue.filter((r) => r.workday !== day))
    return
  }
  // a new day copies the nearest working day, else a plain 9–18
  const template = WEEKDAYS.map((d) => windows(d)).find((w) => w.length) || [
    { start_time: '09:00', end_time: '18:00' },
  ]
  commit([
    ...props.modelValue,
    ...template.map((w) => ({
      workday: day,
      start_time: hhmm(w.start_time),
      end_time: hhmm(w.end_time),
    })),
  ])
}

function addWindow(day) {
  const last = windows(day).at(-1)
  const start = last ? hhmm(last.end_time) : '09:00'
  const [h, m] = start.split(':').map(Number)
  const end = `${String(Math.min(h + 2, 23)).padStart(2, '0')}:${String(m).padStart(2, '0')}`
  commit([
    ...props.modelValue,
    { workday: day, start_time: start, end_time: end },
  ])
}

function copyToAll(day) {
  const source = windows(day)
  const open = WEEKDAYS.filter((d) => windows(d).length)
  commit([
    ...props.modelValue.filter((r) => !open.includes(r.workday)),
    ...open.flatMap((d) =>
      source.map((w) => ({
        workday: d,
        start_time: hhmm(w.start_time),
        end_time: hhmm(w.end_time),
      })),
    ),
  ])
}
</script>
