<template>
  <div class="kpi flex h-full flex-col justify-end gap-1.5 px-4 pb-3">
    <div
      class="kpi-value truncate font-semibold leading-8 text-ink-gray-9"
      :title="exact"
    >
      {{ value }}
    </div>
    <div class="flex min-w-0 items-center gap-1.5 text-xs">
      <WidgetBadge v-if="badge" :badge="badge" />
      <span
        v-if="delta"
        class="inline-flex shrink-0 items-center gap-0.5 rounded px-1 py-px font-medium"
        :class="toneClass"
      >
        <span
          v-if="delta.direction === 'up'"
          class="lucide-arrow-up-right size-3"
          aria-hidden="true"
        />
        <span
          v-else-if="delta.direction === 'down'"
          class="lucide-arrow-down-right size-3"
          aria-hidden="true"
        />
        {{ delta.text }}
      </span>
      <span class="truncate text-ink-gray-5" :title="comparison">
        {{ comparison }}
      </span>
    </div>
    <div
      v-if="answer.progress != null"
      class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-2"
      role="meter"
      :aria-valuenow="answer.progress"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div
        class="h-full rounded-full"
        :style="{ width: `${answer.progress}%`, backgroundColor: fill }"
      />
    </div>
  </div>
</template>

<script setup>
import WidgetBadge from '@/components/Dashboard/WidgetBadge.vue'
import { describeDelta, formatValue } from '@/utils/dashboard'
import { useDarkCharts } from '@/components/Dashboard/meta'
import { colors } from '@/utils/dashboardCharts'
import { computed } from 'vue'

const props = defineProps({
  answer: { type: Object, required: true },
  badge: { type: Object, default: null },
  locale: { type: String, default: undefined },
})

const options = computed(() => ({
  locale: props.locale,
  currency: props.answer.currency,
}))

const value = computed(() =>
  formatValue(props.answer.value, props.answer.format, options.value),
)
const exact = computed(() =>
  formatValue(props.answer.value, props.answer.format, {
    ...options.value,
    compact: false,
  }),
)

const delta = computed(() => describeDelta(props.answer, props.locale))

const toneClass = computed(
  () =>
    ({
      good: 'bg-surface-green-2 text-ink-green-8',
      bad: 'bg-surface-red-2 text-ink-red-8',
      neutral: 'bg-surface-gray-2 text-ink-gray-6',
    })[delta.value?.tone || 'neutral'],
)

const comparison = computed(() => {
  if (props.answer.hint) return props.answer.hint
  if (props.answer.previous == null) return ''
  return __('vs {0} before', [
    formatValue(props.answer.previous, props.answer.format, options.value),
  ])
})

const dark = useDarkCharts()
const fill = computed(() => colors(1, dark.value)[0])
</script>

<style scoped>
/* the figure shrinks with its card, so a narrow tile (the builder with the
   library open) still shows "246.900 USD" whole; a normal row keeps 26px */
.kpi {
  container-type: inline-size;
}
.kpi-value {
  font-size: 26px;
}
@container (max-width: 170px) {
  .kpi-value {
    font-size: 21px;
  }
}
@container (max-width: 135px) {
  .kpi-value {
    font-size: 17px;
  }
}
</style>
