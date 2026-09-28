<template>
  <div
    class="flex items-center justify-center w-8 h-8 bg-surface-gray-2 cursor-pointer rounded-xl hover:bg-surface-gray-3"
    :class="{ 'ring-2 ring-outline-gray-4': selected }"
  >
    <img v-if="logo" :src="logo" class="w-4 h-4" />
    <!-- an account set up by hand has no provider, and so no picture: the
         tile was an empty grey square -->
    <span
      v-else
      class="lucide-mail size-4 text-ink-gray-6"
      aria-hidden="true"
    />
  </div>
  <p v-if="label" class="text-xs text-center text-ink-gray-6 mt-2">
    {{ label }}
  </p>
</template>

<script setup>
defineProps({
  logo: { type: String, default: '' },
  label: { type: String, default: '' },
  selected: { type: Boolean, default: false },
})
</script>
