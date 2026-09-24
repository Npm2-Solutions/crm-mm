<template>
  <div class="flex flex-col gap-1.5">
    <span v-if="label" class="text-xs text-ink-gray-5">{{ label }}</span>
    <div class="flex flex-wrap items-center gap-2">
      <button
        v-for="colour in COLOURS"
        :key="colour"
        type="button"
        class="size-6 rounded-full ring-offset-2 ring-offset-surface-modals transition"
        :class="
          same(modelValue, colour)
            ? 'ring-2 ring-outline-gray-5'
            : 'hover:scale-110'
        "
        :style="{ backgroundColor: colour }"
        :title="colour"
        :aria-label="colour"
        @click="emit('update:modelValue', colour)"
      />
    </div>
  </div>
</template>

<script setup>
// The calendar colour of a service or a room: one tap instead of a hex code.
const COLOURS = [
  '#4C7EFF',
  '#30A46C',
  '#E5484D',
  '#F76B15',
  '#FFB224',
  '#8E4EC6',
  '#D6409F',
  '#12A594',
  '#6E6E6E',
]

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  /** what an empty value is painted as */
  fallback: { type: String, default: '#4C7EFF' },
})
const emit = defineEmits(['update:modelValue'])

function same(value, colour) {
  return (value || props.fallback).toLowerCase() === colour.toLowerCase()
}
</script>
