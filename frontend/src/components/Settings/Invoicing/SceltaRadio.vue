<!--
  One choice among a few, said in words: its name, and under it when it applies.
  The whole row is the target, so it is easy to hit on a phone.
-->
<template>
  <label
    class="flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2.5 hover:bg-surface-gray-1"
    :class="
      modelValue === scelta.value
        ? 'dc-scelto border-outline-gray-4'
        : 'border-outline-gray-2'
    "
  >
    <input
      type="radio"
      class="mt-1 shrink-0"
      :name="nome"
      :value="scelta.value"
      :checked="modelValue === scelta.value"
      @change="emit('update:modelValue', scelta.value)"
    />
    <span class="flex min-w-0 flex-col gap-0.5">
      <span class="text-p-base text-ink-gray-8">{{ scelta.label }}</span>
      <span v-if="scelta.description" class="text-p-sm text-ink-gray-6">
        {{ scelta.description }}
      </span>
    </span>
  </label>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  scelta: { type: Object, required: true },
  nome: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue'])
</script>
