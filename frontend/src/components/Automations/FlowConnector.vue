<template>
  <div
    class="group/connector relative flex w-full items-center justify-center"
    :class="tall ? 'h-9' : 'h-7'"
  >
    <div class="h-full w-px bg-outline-gray-3" />
    <button
      class="absolute grid size-5 place-items-center rounded-full border border-outline-gray-2 bg-surface-white text-ink-gray-6 shadow-sm transition group-hover/connector:opacity-100 hover:bg-surface-gray-2 focus:opacity-100"
      :class="always ? 'opacity-100' : 'opacity-0'"
      :title="__('Add a step here')"
      @click.stop="$emit('insert')"
    >
      <FeatherIcon name="plus" class="size-3" />
    </button>
  </div>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

defineProps({
  tall: { type: Boolean, default: false },
  always: { type: Boolean, default: false },
})
defineEmits(['insert'])
</script>
