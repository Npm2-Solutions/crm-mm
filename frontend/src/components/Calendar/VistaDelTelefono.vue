<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A phone's switch between the agenda's views (list, day, month): a key as
  tall as the others in its row, its views a sheet of rows (telefono.css),
  where a select was a field of 40px beside keys of 32px.
-->
<template>
  <Dropdown :options="voci">
    <template #item-suffix="{ selected }">
      <!-- the one on: the brand's cross, as in every menu of ours -->
      <span
        v-if="selected"
        class="dc-scelto lucide-check size-4 text-ink-gray-7"
        aria-hidden="true"
      />
    </template>
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

const voci = computed(() =>
  props.viste.map((vista) => ({
    label: vista.label,
    icon: ICONE[vista.value],
    selected: vista.value === props.modelValue,
    onClick: () => emit('update:modelValue', vista.value),
  })),
)
</script>
