<template>
  <div class="grid grid-cols-[1.1fr_0.9fr_1.2fr_28px] items-center gap-2">
    <Autocomplete
      :modelValue="condition.field"
      :options="fieldOptions"
      :placeholder="__('field')"
      @update:modelValue="pickField"
    />
    <FormControl
      :modelValue="condition.operator"
      type="select"
      :options="operatorOptions"
      @update:modelValue="(value) => setOperator(value)"
    />
    <div v-if="!needsValue(condition.operator)" class="text-sm text-ink-gray-4">
      —
    </div>
    <ValueInput
      v-else
      :modelValue="condition.value"
      :field="field"
      :placeholder="__('value')"
      @update:modelValue="setValue"
    />
    <Button
      variant="ghost"
      icon="lucide-x"
      :label="__('Remove condition')"
      @click="$emit('remove')"
    />
  </div>
</template>

<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import ValueInput from './ValueInput.vue'
import { Button, FormControl } from 'frappe-ui'
import { computed } from 'vue'
import { needsValue, operatorsForFieldtype } from '@/utils/automation'

const props = defineProps({
  fields: { type: Array, default: () => [] },
})

defineEmits(['remove'])

const condition = defineModel({ type: Object, required: true })

const fieldOptions = computed(() =>
  props.fields.map((f) => ({
    label: f.label || f.fieldname,
    value: f.fieldname,
    description: f.fieldname,
  })),
)

const field = computed(
  () =>
    props.fields.find((f) => f.fieldname === condition.value.field) || {
      fieldtype: 'Data',
      options: '',
    },
)

const operatorOptions = computed(() =>
  operatorsForFieldtype(field.value.fieldtype).map((o) => ({
    label: __(o.label),
    value: o.value,
  })),
)

function setValue(value) {
  condition.value = { ...condition.value, value }
}

function setOperator(operator) {
  const next = { ...condition.value, operator }
  if (!needsValue(operator)) next.value = ''
  condition.value = next
}

function pickField(option) {
  const fieldname = option?.value || ''
  const picked = props.fields.find((f) => f.fieldname === fieldname)
  const allowed = operatorsForFieldtype(picked?.fieldtype)
  const next = { ...condition.value, field: fieldname, value: '' }
  // an operator that no longer applies to the new fieldtype would silently fail
  if (!allowed.some((o) => o.value === next.operator)) next.operator = 'equals'
  condition.value = next
}
</script>
