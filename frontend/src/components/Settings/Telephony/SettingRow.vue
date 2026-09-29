<!-- As SettingsRow: the control goes under the words when both do not fit. -->
<template>
  <div
    class="flex flex-wrap items-center justify-between gap-x-8 gap-y-2 py-3 pl-2 pr-1"
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
  label: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>
