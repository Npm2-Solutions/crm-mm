<!--
  One labelled setting: title and explanation on the left, the control on the
  right. The same row four settings pages were each spelling out by hand.

  The words keep at least 15rem. Where that and the control do not fit side by
  side — a phone, a wide field — the control goes under them instead of
  squeezing them into a column one word wide.
-->
<template>
  <div
    class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 py-3 px-2"
  >
    <div class="flex min-w-0 flex-1 basis-60 flex-col">
      <div class="text-p-base-medium text-ink-gray-7">{{ label }}</div>
      <div v-if="description" class="text-p-sm text-ink-gray-5">
        {{ description }}
      </div>
    </div>
    <div class="shrink-0">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>
