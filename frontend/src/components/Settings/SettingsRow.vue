<!--
  One labelled setting: title and explanation on the left, the control on the
  right. The same row four settings pages were each spelling out by hand.
-->
<template>
  <div class="flex items-center justify-between gap-4 py-3 px-2">
    <div class="flex min-w-0 flex-col">
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
