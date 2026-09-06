<template>
  <Link
    v-if="control === 'link'"
    :modelValue="String(model ?? '')"
    :doctype="field.options"
    :placeholder="placeholder"
    @update:modelValue="(value) => (model = value)"
  />
  <FormControl
    v-else
    :modelValue="model"
    :type="control"
    :options="options"
    :placeholder="placeholder"
    @update:modelValue="(value) => (model = value)"
  />
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  /** DocType field meta: { fieldtype, options } — drives which control shows. */
  field: { type: Object, default: () => ({ fieldtype: 'Data', options: '' }) },
  placeholder: { type: String, default: '' },
})

const model = defineModel({ type: [String, Number], default: '' })

const control = computed(() => {
  const type = props.field?.fieldtype
  if (type === 'Select' || type === 'Check') return 'select'
  if (type === 'Link' && props.field.options) return 'link'
  if (['Int', 'Float', 'Currency', 'Percent', 'Rating'].includes(type)) {
    return 'number'
  }
  if (type === 'Date') return 'date'
  if (type === 'Datetime') return 'datetime-local'
  if (['Text', 'Small Text', 'Long Text'].includes(type)) return 'textarea'
  return 'text'
})

const options = computed(() => {
  if (props.field?.fieldtype === 'Check') {
    return [
      { label: __('Yes'), value: '1' },
      { label: __('No'), value: '0' },
    ]
  }
  if (props.field?.fieldtype !== 'Select') return undefined
  return (props.field.options || '')
    .split('\n')
    .map((option) => ({ label: option || __('(empty)'), value: option }))
})
</script>
