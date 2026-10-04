<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A message of an automation, with the person's fields and the tracked links
  put in where the cursor is.
-->
<template>
  <div class="flex flex-col gap-1">
    <div class="flex items-center justify-between">
      <label v-if="label" class="text-xs text-ink-gray-5">{{ label }}</label>
      <Dropdown :options="mergeOptions" placement="right">
        <Button
          variant="ghost"
          size="sm"
          class="!text-ink-gray-5"
          :label="__('Insert field')"
        />
      </Dropdown>
    </div>
    <textarea
      v-if="type === 'textarea'"
      ref="input"
      :value="modelValue"
      :rows="rows"
      :placeholder="placeholder"
      class="form-textarea w-full"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <input
      v-else
      ref="input"
      :value="modelValue"
      :placeholder="placeholder"
      class="form-input w-full"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script setup>
import { Button, Dropdown } from 'frappe-ui'
import { computed, nextTick, ref } from 'vue'
import { MERGE_FIELDS } from '@/utils/automation'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  rows: { type: Number, default: 4 },
  placeholder: { type: String, default: '' },
  // the tracked links a message to the person may carry: each one gets their
  // own, so a click lands on their record
  links: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])

const input = ref(null)

const mergeOptions = computed(() => {
  const campi = MERGE_FIELDS.map((field) => ({
    label: `${__(field.label)} · ${field.token}`,
    onClick: () => insert(field.token),
  }))
  if (!props.links.length) return campi
  return [
    { group: __('Fields'), items: campi },
    {
      group: __('Tracked links'),
      items: props.links.map((slug) => ({
        label: slug,
        onClick: () => insert(`{{ tracked_link("${slug}") }}`),
      })),
    },
  ]
})

/** Drops the placeholder where the cursor is, not at the end of the text. */
function insert(token) {
  const element = input.value
  const value = props.modelValue || ''
  const start = element?.selectionStart ?? value.length
  const end = element?.selectionEnd ?? value.length
  emit('update:modelValue', value.slice(0, start) + token + value.slice(end))
  nextTick(() => {
    if (!element) return
    element.focus()
    const caret = start + token.length
    element.setSelectionRange(caret, caret)
  })
}
</script>
