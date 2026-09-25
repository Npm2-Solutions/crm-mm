<template>
  <Tooltip :text="tooltipText">
    <div :class="className">{{ displayText }}</div>
  </Tooltip>
</template>

<script setup>
import { Tooltip } from 'frappe-ui'
import { timeAgo, formatDate } from '@/utils'
import { useTimelinePreferences } from '@/composables/useTimelinePreferences'
import { computed } from 'vue'

const props = defineProps({
  date: { type: [String, Object], default: '' },
  // Format used for the exact timestamp (falls back to the default in formatDate)
  format: { type: String, default: '' },
  className: { type: String, default: 'text-sm text-ink-gray-5' },
  // Force the clock time, whatever the site prefers. In a conversation the day
  // is already written on the date chip above, so «23 hours ago» next to
  // «11:07 am» is two answers to one question, in two different units.
  exact: { type: Boolean, default: false },
})

const { showExactTimestamp } = useTimelinePreferences()

const relative = computed(() => __(timeAgo(props.date)))
const exact = computed(() => formatDate(props.date, props.format || undefined))

const wantsExact = computed(() => props.exact || showExactTimestamp.value)

const displayText = computed(() =>
  wantsExact.value ? exact.value : relative.value,
)
const tooltipText = computed(() =>
  wantsExact.value ? relative.value : exact.value,
)
</script>
