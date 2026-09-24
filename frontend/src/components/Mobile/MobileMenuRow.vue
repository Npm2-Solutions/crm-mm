<template>
  <!-- 48px tall: the smallest target a thumb hits reliably, and the reason the
       old drawer's 28px rows were a lottery. -->
  <button
    type="button"
    class="flex min-h-12 w-full items-center gap-3 rounded-lg px-2 text-left transition-colors active:bg-surface-gray-3"
    :class="
      active
        ? 'bg-surface-gray-2 text-ink-gray-9'
        : danger
          ? 'text-ink-red-4'
          : 'text-ink-gray-8'
    "
    :aria-current="active ? 'page' : undefined"
  >
    <Icon v-if="icon" :icon="icon" class="size-5 shrink-0" />
    <span class="min-w-0 flex-1 truncate text-base">{{ label }}</span>
    <Badge v-if="badge" :label="String(badge)" variant="subtle" />
  </button>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { Badge } from 'frappe-ui'

defineProps({
  icon: { type: [Object, Function, String], default: null },
  label: { type: String, required: true },
  active: { type: Boolean, default: false },
  danger: { type: Boolean, default: false },
  badge: { type: [Number, String], default: 0 },
})
</script>
