<template>
  <div class="flex h-full flex-col px-4 pb-3">
    <div
      v-if="!answer.cells?.length"
      class="flex flex-1 items-center justify-center pb-4 text-sm text-ink-gray-5"
    >
      {{ __('Nothing in this period') }}
    </div>
    <template v-else>
      <div
        class="grid min-h-0 flex-1 gap-[2px]"
        :style="{
          gridTemplateColumns: `2.5rem repeat(${answer.x.length}, minmax(0, 1fr))`,
          gridTemplateRows: `repeat(${answer.y.length}, minmax(0, 1fr)) auto`,
        }"
        role="table"
        :aria-label="__('Heatmap')"
      >
        <template v-for="(day, row) in answer.y" :key="day">
          <div
            class="flex items-center text-2xs text-ink-gray-5"
            role="rowheader"
          >
            {{ day }}
          </div>
          <div
            v-for="(hour, column) in answer.x"
            :key="`${row}-${column}`"
            class="min-h-2 rounded-[3px]"
            :class="cells[`${column}:${row}`] ? '' : 'bg-surface-gray-1'"
            :style="cellStyle(column, row)"
            :title="`${day} ${hour}:00 · ${format(cells[`${column}:${row}`] || 0)}`"
            role="cell"
          />
        </template>
        <div />
        <div
          v-for="(hour, column) in answer.x"
          :key="`label-${column}`"
          class="pt-1 text-center text-2xs text-ink-gray-5"
        >
          {{ column % 3 === 0 ? hour : '' }}
        </div>
      </div>
      <div
        class="flex items-center justify-end gap-1.5 pt-2 text-2xs text-ink-gray-5"
      >
        <span>{{ __('Fewer') }}</span>
        <span
          v-for="step in legend"
          :key="step"
          class="size-2.5 rounded-sm"
          :style="{ backgroundColor: step }"
          aria-hidden="true"
        />
        <span>{{ __('More') }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { useDarkCharts } from '@/components/Dashboard/meta'
import { formatValue } from '@/utils/dashboard'
import { heatColor, sequential } from '@/utils/dashboardCharts'
import { computed } from 'vue'

const props = defineProps({
  answer: { type: Object, required: true },
  locale: { type: String, default: undefined },
})

const cells = computed(() => {
  const map = {}
  for (const [x, y, value] of props.answer.cells || []) map[`${x}:${y}`] = value
  return map
})

const dark = useDarkCharts()
const legend = computed(() => {
  const ramp = sequential(dark.value)
  return [ramp[2], ramp[5], ramp[8], ramp[12]]
})

function cellStyle(column, row) {
  const color = heatColor(
    cells.value[`${column}:${row}`],
    props.answer.max,
    dark.value,
  )
  return color ? { backgroundColor: color } : {}
}

function format(value) {
  return formatValue(value, props.answer.format, { locale: props.locale })
}
</script>
