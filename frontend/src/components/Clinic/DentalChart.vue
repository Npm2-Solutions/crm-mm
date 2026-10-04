<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The odontogram: the teeth as the dentist sees them - the patient's right on the
  left, the upper arch above the lower - each with a mark for each condition it
  has. A missing tooth is struck through. Picking a tooth says what it is; the
  card that holds the chart writes it. On a phone an arch's row wraps after its
  first quadrant: sixteen teeth side by side ran off the screen.
-->
<template>
  <div class="overflow-x-auto">
    <div class="flex w-max min-w-full flex-col items-center gap-1 py-1">
      <template v-for="(riga, n) in righe" :key="n">
        <!-- between the arches: where the mouth closes -->
        <div
          v-if="n === divisione"
          class="my-1 h-px w-full border-t border-dashed border-outline-gray-2"
        />
        <div class="flex items-end gap-0.5">
          <template v-for="(dente, i) in riga" :key="dente">
            <div
              v-if="!aCapo && i === riga.length / 2"
              class="mx-1 self-stretch border-l border-outline-gray-2"
              aria-hidden="true"
            />
            <button
              type="button"
              class="touch-target flex w-8 flex-col items-center gap-0.5 rounded px-0.5 py-1 hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
              :class="[
                n < divisione ? '' : 'flex-col-reverse',
                selected === String(dente)
                  ? 'bg-surface-gray-3 hover:bg-surface-gray-3'
                  : '',
              ]"
              :aria-label="etichetta(dente)"
              :aria-pressed="selected === String(dente)"
              :title="etichetta(dente)"
              @click="emit('select', String(dente))"
            >
              <span
                class="text-p-xs tabular-nums"
                :class="
                  mancante(rows, dente)
                    ? 'text-ink-gray-5 line-through'
                    : 'text-ink-gray-7'
                "
              >
                {{ dente }}
              </span>
              <span
                class="flex h-6 w-6 flex-wrap content-center items-center justify-center gap-0.5 rounded-sm border"
                :class="
                  mancante(rows, dente)
                    ? 'border-dashed border-outline-gray-2'
                    : 'border-outline-gray-3'
                "
              >
                <span
                  v-for="condizione in segni(dente)"
                  :key="condizione.condition"
                  class="size-2 rounded-sm"
                  :class="punto(condizione.condition)"
                />
              </span>
            </button>
          </template>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { isMobileView } from '@/composables/breakpoints'
import { arcate, delDente, mancante, segno as punto } from '@/utils/cure'
import { computed } from 'vue'

const props = defineProps({
  // the chart's rows: { tooth, condition, surfaces, note }
  rows: { type: Array, default: () => [] },
  dentition: { type: String, default: 'Permanent' },
  selected: { type: String, default: null },
})
const emit = defineEmits(['select'])

// on a phone each row wraps after its first quadrant, read on as one row
const aCapo = isMobileView
const righe = computed(() => {
  const intere = arcate(props.dentition)
  if (!aCapo.value) return intere
  return intere.flatMap((riga) => [
    riga.slice(0, riga.length / 2),
    riga.slice(riga.length / 2),
  ])
})
// the rows above the line are the upper arch: half of them
const divisione = computed(() => righe.value.length / 2)

// the marks of a tooth; a missing one has none
function segni(dente) {
  if (mancante(props.rows, dente)) return []
  return delDente(props.rows, dente).slice(0, 4)
}

function etichetta(dente) {
  const righe = delDente(props.rows, dente)
  if (!righe.length) return __('Tooth {0}', [dente])
  const cosa = righe
    .map((riga) =>
      [__(riga.condition), riga.surfaces].filter(Boolean).join(' '),
    )
    .join(', ')
  return __('Tooth {0}: {1}', [dente, cosa])
}
</script>
