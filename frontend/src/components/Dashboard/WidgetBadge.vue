<template>
  <!-- what is going on now: the brand's soft green and the cross in place of
       the dot, as the design system's «in progress» -->
  <span
    class="inline-flex shrink-0 items-center gap-1 rounded-full px-1.5 py-0.5 text-2xs font-medium"
    :class="badge.live ? 'dc-in-corso' : 'bg-surface-gray-2 text-ink-gray-6'"
    :title="badge.hint"
  >
    <span
      v-if="badge.live"
      class="dc-cross"
      style="--s: 7px"
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
