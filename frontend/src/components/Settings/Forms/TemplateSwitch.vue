<template>
  <label class="flex items-start gap-2 text-base text-ink-gray-7">
    <Switch
      class="mt-0.5 shrink-0"
      size="sm"
      :model-value="Boolean(modelValue)"
      @update:model-value="(value) => $emit('update:modelValue', value)"
    />
    <span class="min-w-0">
      {{ label }}
      <span v-if="hint" class="block text-sm text-ink-gray-5">{{ hint }}</span>
    </span>
  </label>
</template>

<script setup>
import { Switch } from 'frappe-ui'

defineProps({
  modelValue: { type: [Boolean, Number], default: false },
  label: { type: String, required: true },
  hint: { type: String, default: '' },
})
defineEmits(['update:modelValue'])
</script>
