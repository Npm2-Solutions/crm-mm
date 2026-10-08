<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The agenda's filters in one place: on a phone the location (docs/crm/62),
  services, rooms or professionals, state, where it was booked - a list of ticks under each heading, how many are on
  beside «Filters». Five chips took a whole row above every day; whose agenda
  it is has a control of its own (ChiNellAgenda). On a phone the list is a
  sheet from the bottom (`data-foglio`, telefono.css).
-->
<template>
  <Popover placement="bottom-end">
    <template #target="{ togglePopover }">
      <Button
        :aria-label="attivi ? __('Filters, {0} on', [attivi]) : __('Filters')"
        @click="togglePopover"
      >
        <template #prefix>
          <span
            class="lucide-list-filter size-4 text-ink-gray-6"
            aria-hidden="true"
          />
        </template>
        <!-- on a phone its icon, so the row of the agenda's keys fits -->
        <span class="max-md:hidden">{{ __('Filters') }}</span>
        <span
          v-if="attivi"
          class="ml-0.5 rounded-full bg-[var(--brand-action)] px-1.5 text-p-xs tabular-nums text-[var(--on-brand-solid)]"
          aria-hidden="true"
        >
          {{ attivi }}
        </span>
      </Button>
    </template>
    <template #body-main>
      <div
        data-foglio
        class="flex max-h-[min(32rem,75vh)] w-72 flex-col gap-0.5 overflow-y-auto p-1.5"
      >
        <span class="flex items-center justify-between px-1.5 pb-1">
          <span class="text-p-sm-medium text-ink-gray-8">
            {{ __('Filters') }}
          </span>
          <Button
            v-if="attivi"
            variant="ghost"
            size="sm"
            :label="__('Clear all')"
            @click="$emit('azzera')"
          />
        </span>
        <template v-for="gruppo in gruppi" :key="gruppo.chiave">
          <span class="px-1.5 pb-0.5 pt-2.5 text-xs-medium text-ink-gray-5">
            {{ gruppo.titolo }}
          </span>
          <label
            v-for="opzione in gruppo.opzioni"
            :key="`${gruppo.chiave}-${opzione.value}`"
            class="flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 hover:bg-surface-gray-2"
          >
            <Checkbox
              :modelValue="scelto(gruppo, opzione.value)"
              @update:modelValue="alterna(gruppo, opzione.value)"
            />
            <span
              v-if="opzione.colore"
              class="size-2 shrink-0 rounded-full"
              :style="{ backgroundColor: opzione.colore }"
              aria-hidden="true"
            />
            <!-- one without a colour of its own (its appointments wear their
                 state's) keeps the names in line with a hollow dot -->
            <span
              v-else-if="colorati.has(gruppo.chiave)"
              class="size-2 shrink-0 rounded-full border border-outline-gray-4"
              aria-hidden="true"
            />
            <span class="truncate text-p-sm text-ink-gray-8">
              {{ opzione.label }}
            </span>
          </label>
          <p
            v-if="!gruppo.opzioni.length"
            class="px-1.5 py-1 text-p-sm text-ink-gray-5"
          >
            {{ gruppo.vuoto || __('Nothing to filter yet') }}
          </p>
        </template>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { Button, Checkbox, Popover } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  /** the filters, by key: `{ services: [], statuses: [], … }` */
  modelValue: { type: Object, required: true },
  /** `[{ chiave, titolo, opzioni: [{ value, label, colore? }], vuoto?,
   * singolo? }]`: a `singolo` group takes one value, '' its «all» */
  gruppi: { type: Array, default: () => [] },
})
const emit = defineEmits(['cambia', 'azzera'])

// the headings whose options are drawn with their colour
const colorati = computed(
  () =>
    new Set(
      props.gruppi
        .filter((gruppo) => gruppo.opzioni.some((opzione) => opzione.colore))
        .map((gruppo) => gruppo.chiave),
    ),
)

const attivi = computed(() =>
  props.gruppi.reduce(
    (somma, gruppo) => somma + (props.modelValue[gruppo.chiave] || []).length,
    0,
  ),
)

function cambia(chiave, valori) {
  emit('cambia', chiave, valori)
}

function scelto(gruppo, valore) {
  const ora = props.modelValue[gruppo.chiave] || []
  // one of a kind (the location): its «all» is ticked while nothing is
  if (gruppo.singolo && !valore) return !ora.length
  return ora.includes(valore)
}

function alterna(gruppo, valore) {
  const chiave = gruppo.chiave
  const ora = props.modelValue[chiave] || []
  if (gruppo.singolo) {
    cambia(chiave, valore && !ora.includes(valore) ? [valore] : [])
    return
  }
  cambia(
    chiave,
    ora.includes(valore) ? ora.filter((v) => v !== valore) : [...ora, valore],
  )
}
</script>
