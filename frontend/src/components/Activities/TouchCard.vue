<!--
  One attribution snapshot — the campaign that introduced this person, or the
  one that brought them back. Blank fields are dropped rather than shown empty:
  a direct visit has no campaign, and a row reading "Campaign: —" is noise.
-->
<template>
  <div class="rounded-lg border border-outline-gray-2 px-3 py-2.5">
    <div class="flex items-center justify-between gap-2 pb-2">
      <span class="text-p-base-medium text-ink-gray-7">{{ title }}</span>
      <Badge
        v-if="touch?.category"
        :label="__(touch.category)"
        :theme="theme"
        size="sm"
      />
    </div>
    <div v-if="rows.length" class="flex flex-col gap-1">
      <div v-for="row in rows" :key="row.label" class="flex gap-2 text-p-sm">
        <span class="w-24 shrink-0 text-ink-gray-5">{{ row.label }}</span>
        <span
          class="min-w-0 flex-1 truncate text-ink-gray-7"
          :title="row.value"
        >
          {{ row.value }}
        </span>
      </div>
    </div>
    <div v-else class="text-p-sm text-ink-gray-5">{{ __('Not recorded') }}</div>
  </div>
</template>

<script setup>
import { Badge } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  touch: { type: Object, default: () => ({}) },
  theme: { type: String, default: 'blue' },
})

const rows = computed(() => {
  const t = props.touch || {}
  return [
    { label: __('Source'), value: t.source },
    { label: __('Medium'), value: t.medium },
    { label: __('Campaign'), value: t.campaign },
    { label: __('Term'), value: t.term },
    { label: __('Content'), value: t.content },
    { label: __('Landing page'), value: t.landing_page },
    { label: __('Referrer'), value: t.referrer },
    { label: __('Date'), value: t.on },
  ].filter((row) => row.value)
})
</script>
