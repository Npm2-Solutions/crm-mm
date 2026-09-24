<template>
  <div class="flex h-full flex-col px-4 pb-3">
    <div
      v-if="!steps.length || !steps[0].value"
      class="flex flex-1 items-center justify-center pb-4 text-sm text-ink-gray-5"
    >
      {{ __('Nothing in this period') }}
    </div>
    <ol
      v-else
      class="flex min-h-0 flex-1 flex-col justify-center gap-2 overflow-y-auto"
    >
      <li
        v-for="(step, index) in steps"
        :key="`${index}-${step.label}`"
        class="flex items-center gap-3"
        :title="stepTitle(step, index)"
      >
        <span class="w-28 shrink-0 truncate text-xs text-ink-gray-7">
          {{ step.label }}
        </span>
        <span
          class="relative h-5 min-w-0 flex-1 overflow-hidden rounded bg-surface-gray-1"
        >
          <span
            class="absolute inset-y-0 left-0 rounded"
            :style="{
              width: `${Math.max(step.ofFirst || 0, step.value ? 1.5 : 0)}%`,
              backgroundColor: fill,
            }"
          />
        </span>
        <span class="w-24 shrink-0 text-right text-xs tabular-nums">
          <span class="font-medium text-ink-gray-9">{{
            format(step.value)
          }}</span>
          <span class="ml-1 text-ink-gray-5">{{ percent(step.ofFirst) }}</span>
        </span>
      </li>
    </ol>
  </div>
</template>

<script setup>
import { formatValue } from '@/utils/dashboard'
import { useDarkCharts } from '@/components/Dashboard/meta'
import { colors } from '@/utils/dashboardCharts'
import { computed } from 'vue'

const props = defineProps({
  answer: { type: Object, required: true },
  locale: { type: String, default: undefined },
})

const steps = computed(() => props.answer.steps || [])
const dark = useDarkCharts()
const fill = computed(() => colors(1, dark.value)[0])

function format(value) {
  return formatValue(value, props.answer.format, { locale: props.locale })
}

function percent(value) {
  return value == null
    ? ''
    : formatValue(value, 'percent', { locale: props.locale })
}

function stepTitle(step, index) {
  if (!index || step.ofPrevious == null) return step.label
  return __('{0}: {1} of the previous step', [
    step.label,
    percent(step.ofPrevious),
  ])
}
</script>
