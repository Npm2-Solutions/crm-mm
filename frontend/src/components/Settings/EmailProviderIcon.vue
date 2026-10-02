<template>
  <div class="flex flex-col items-center">
    <div
      class="flex size-8 shrink-0 items-center justify-center rounded-xl bg-surface-gray-2"
      :class="{ 'ring-2 ring-outline-gray-4': selected }"
    >
      <img v-if="logo" :src="logo" class="size-4" alt="" />
      <!-- a provider without a picture shows its letter, one set up by hand the
           envelope: never an empty grey square -->
      <span
        v-else-if="name"
        class="text-sm-semibold text-ink-gray-7"
        aria-hidden="true"
        >{{ iniziale(name) }}</span
      >
      <span
        v-else
        class="lucide-mail size-4 text-ink-gray-6"
        aria-hidden="true"
      />
    </div>
    <p v-if="label" class="mt-2 text-center text-xs text-ink-gray-6">
      {{ label }}
    </p>
  </div>
</template>

<script setup>
import { iniziale } from '@/utils/caselle'

defineProps({
  logo: { type: String, default: '' },
  // the provider's name, for its letter when there is no picture
  name: { type: String, default: '' },
  label: { type: String, default: '' },
  selected: { type: Boolean, default: false },
})
</script>
