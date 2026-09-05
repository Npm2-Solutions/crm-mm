<template>
  <div class="flex items-center justify-between gap-8 py-3 pl-2 pr-1">
    <div class="flex flex-col min-w-0">
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
  label: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>
