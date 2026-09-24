<template>
  <div ref="root" class="h-full w-full">
    <div
      v-if="empty"
      class="flex h-full items-center justify-center px-4 pb-6 text-sm text-ink-gray-5"
    >
      {{ __('Nothing in this period') }}
    </div>

    <div
      v-else-if="answer.kind === 'donut'"
      class="flex h-full gap-3 px-3 pb-3"
      :class="stacked ? 'flex-col' : 'items-center'"
    >
      <div class="relative min-h-0 min-w-0 flex-1 self-stretch">
        <ECharts :options="options" class="h-full w-full" />
        <div
          class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center"
        >
          <span class="text-lg font-semibold leading-6 text-ink-gray-9">
            {{ format(total) }}
          </span>
          <span class="text-2xs text-ink-gray-5">{{ __('Total') }}</span>
        </div>
      </div>
      <ul
        class="flex shrink-0 flex-col justify-center gap-1.5 text-xs"
        :class="stacked ? 'w-full' : 'w-[48%] max-w-64'"
      >
        <li
          v-for="(slice, index) in answer.slices"
          :key="slice.label"
          class="flex min-w-0 items-center gap-2"
        >
          <span
            class="size-2 shrink-0 rounded-sm"
            :style="{ backgroundColor: palette[index] }"
            aria-hidden="true"
          />
          <span
            class="min-w-0 flex-1 truncate text-ink-gray-7"
            :title="slice.label"
          >
            {{ slice.label }}
          </span>
          <span class="shrink-0 tabular-nums font-medium text-ink-gray-9">
            {{ format(slice.value) }}
          </span>
          <span class="w-9 shrink-0 text-right tabular-nums text-ink-gray-5">
            {{ share(slice.value) }}
          </span>
        </li>
      </ul>
    </div>

    <div v-else class="h-full w-full px-3 pb-2">
      <ECharts :options="options" class="h-full w-full" />
    </div>
  </div>
</template>

<script setup>
import { formatValue } from '@/utils/dashboard'
import { useDarkCharts } from '@/components/Dashboard/meta'
import {
  axisOptions,
  donutOptions,
  seriesColors,
} from '@/utils/dashboardCharts'
import { useElementSize } from '@vueuse/core'
import { ECharts } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  answer: { type: Object, required: true },
  locale: { type: String, default: undefined },
})

const root = ref(null)
const { width } = useElementSize(root)

// a narrow donut puts its legend underneath instead of beside it
const stacked = computed(() => width.value > 0 && width.value < 360)

const dark = useDarkCharts()

const options = computed(() => {
  const settings = {
    dark: dark.value,
    locale: props.locale,
    currency: props.answer.currency,
  }
  if (props.answer.kind === 'donut') return donutOptions(props.answer, settings)
  // names under vertical bars wrap to the room each bar has
  if (props.answer.x?.type === 'category' && !props.answer.horizontal)
    settings.width = width.value
  return axisOptions(props.answer, settings)
})

const palette = computed(() =>
  seriesColors(props.answer.slices || [], dark.value),
)

const total = computed(() =>
  (props.answer.slices || []).reduce(
    (sum, slice) => sum + (Number(slice.value) || 0),
    0,
  ),
)

const empty = computed(() => {
  if (props.answer.kind === 'donut') return !total.value
  const series = props.answer.series || []
  return !series.some((item) =>
    (item.values || []).some((value) => Number(value)),
  )
})

function format(value) {
  return formatValue(value, props.answer.format, {
    locale: props.locale,
    currency: props.answer.currency,
  })
}

function share(value) {
  if (!total.value) return ''
  return `${Math.round((Number(value) / total.value) * 100)}%`
}
</script>
