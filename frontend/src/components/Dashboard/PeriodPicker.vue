<template>
  <div class="flex flex-wrap items-center gap-2">
    <Dropdown :options="options">
      <template #default="{ open }">
        <Button
          variant="outline"
          iconLeft="calendar"
          :iconRight="open ? 'chevron-up' : 'chevron-down'"
          :label="periodLabel(period)"
        />
      </template>
      <template #item-suffix="{ item }">
        <span
          v-if="item.key === period"
          class="lucide-check size-4 text-ink-gray-7"
          aria-hidden="true"
        />
      </template>
    </Dropdown>
    <DateRangePicker
      v-if="period === 'custom'"
      ref="picker"
      class="w-56"
      variant="outline"
      :modelValue="range"
      :placeholder="__('Choose the days')"
      @update:modelValue="setCustom"
    />
    <span v-else class="hidden text-sm text-ink-gray-5 sm:inline">
      {{ formatRange(range[0], range[1], locale) }}
    </span>
  </div>
</template>

<script setup>
import {
  PERIODS,
  formatRange,
  periodLabel,
  periodRange,
} from '@/utils/dashboard'
import { DateRangePicker, Dropdown } from 'frappe-ui'
import { computed, nextTick, ref } from 'vue'

defineProps({
  locale: { type: String, default: undefined },
})

const period = defineModel('period', { type: String, default: 'last_30_days' })
const range = defineModel('range', { type: Array, default: () => [] })

const picker = ref(null)

const options = computed(() => [
  {
    group: __('Period'),
    hideLabel: true,
    items: PERIODS.map((key) => ({
      key,
      label: periodLabel(key),
      onClick: () => choose(key),
    })),
  },
  {
    group: __('Custom'),
    hideLabel: true,
    items: [
      {
        key: 'custom',
        label: periodLabel('custom'),
        icon: 'lucide-calendar-range',
        onClick: () => {
          period.value = 'custom'
          nextTick(() => picker.value?.open?.())
        },
      },
    ],
  },
])

function choose(key) {
  period.value = key
  range.value = periodRange(key)
}

function setCustom(value) {
  const dates = Array.isArray(value) ? value : String(value || '').split(',')
  if (dates.length === 2 && dates[0] && dates[1]) {
    range.value =
      dates[0] <= dates[1] ? [dates[0], dates[1]] : [dates[1], dates[0]]
  }
}
</script>
