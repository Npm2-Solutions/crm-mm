<template>
  <span
    class="inline-flex shrink-0 items-center gap-1 rounded-full bg-surface-gray-2 px-1.5 py-0.5 text-2xs font-medium text-ink-gray-6"
    :title="badge.hint"
  >
    <span
      v-if="badge.live"
      class="size-1.5 rounded-full bg-[#1baf7a]"
      aria-hidden="true"
    />
    {{ badge.label }}
  </span>
</template>

<script setup>
defineProps({
  // { label, hint, live }
  badge: { type: Object, required: true },
})
</script>
