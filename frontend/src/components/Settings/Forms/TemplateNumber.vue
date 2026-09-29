<template>
  <FormControl
    :label="label"
    :placeholder="placeholder"
    inputmode="decimal"
    :model-value="modelValue ?? ''"
    @update:model-value="(value) => $emit('update:modelValue', numberOrText(value))"
  />
</template>

<script setup>
import { FormControl } from 'frappe-ui'

defineProps({
  modelValue: { type: [Number, String, null], default: null },
  label: { type: String, required: true },
  placeholder: { type: String, default: '' },
})
defineEmits(['update:modelValue'])

/** A number when it is one; what was typed otherwise, for the checks to name. */
function numberOrText(value) {
  const text = String(value ?? '').trim().replace(',', '.')
  if (text === '' || text === '-') return null
  const number = Number(text)
  return Number.isFinite(number) ? number : text
}
</script>
