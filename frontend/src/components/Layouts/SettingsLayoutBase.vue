<template>
  <div class="flex flex-col h-full w-full text-ink-gray-8">
    <!-- Header -->
    <div
      class="flex justify-between items-start p-8 text-ink-gray-8 max-md:flex-col max-md:items-start max-md:gap-3 max-md:px-5 max-md:py-5"
    >
      <div class="flex flex-col gap-1">
        <slot name="title">
          <h2
            class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
          >
            {{ title }}
          </h2>
        </slot>
        <slot
          v-if="Boolean($slots['description']) || Boolean(description)"
          name="description"
        >
          <p class="text-p-base text-ink-gray-6">
            {{ description }}
          </p>
        </slot>
      </div>
      <slot v-if="Boolean($slots['header-actions'])" name="header-actions" />
    </div>
    <div
      v-if="Boolean($slots['header-bottom'])"
      class="p-8 pt-0 max-md:px-5 max-md:pb-5"
    >
      <slot name="header-bottom" />
    </div>
    <div class="h-full overflow-y-auto p-8 pt-0 max-md:px-5 max-md:pb-5">
      <slot name="content" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>
