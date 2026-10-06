<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A phone's switch between the agenda's views (list, day, month): a key as
  tall as the others in its row, its views a sheet of rows (telefono.css),
  where a select was a field of 40px beside keys of 32px.
-->
<template>
  <Dropdown :options="voci">
    <Button :aria-label="__('View: {0}', [attuale?.label || ''])">
      <template #prefix>
        <span
          :class="[ICONE[modelValue], 'size-4 text-ink-gray-6']"
          aria-hidden="true"
        />
      </template>
      {{ attuale?.label }}
      <template #suffix>
        <span
          class="lucide-chevron-down size-3.5 text-ink-gray-5"
          aria-hidden="true"
        />
      </template>
    </Button>
  </Dropdown>
</template>

<script setup>
import { Button, Dropdown } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, required: true },
  /** `[{ label, value }]`, the views a phone has */
  viste: { type: Array, required: true },
})
const emit = defineEmits(['update:modelValue'])

const ICONE = {
  elenco: 'lucide-list',
  giorno: 'lucide-calendar-1',
  mese: 'lucide-calendar-days',
}

const attuale = computed(() =>
  props.viste.find((vista) => vista.value === props.modelValue),
)

// the one on carries its tick, the others their own mark
const voci = computed(() =>
  props.viste.map((vista) => ({
    label: vista.label,
    icon:
      vista.value === props.modelValue ? 'lucide-check' : ICONE[vista.value],
    onClick: () => emit('update:modelValue', vista.value),
  })),
)
</script>
