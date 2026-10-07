<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  What a day of a diet gives while it is written, next to the nutritionist's
  targets: the kcal first, then proteins, carbohydrates, fats and fibre, each with
  a bar that fills towards its target and what is left, or over. Numbers and the
  brand's mark, no colour that judges: the nutritionist reads them.
-->
<template>
  <div
    class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2.5"
    role="status"
  >
    <div class="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
      <span class="text-p-sm text-ink-gray-6">{{ title }}</span>
      <span class="text-base font-medium tabular-nums text-ink-gray-9">
        {{
          energia.target
            ? __('{0} of {1} kcal', [
                numero(energia.value),
                numero(energia.target),
              ])
            : __('{0} kcal', [numero(energia.value)])
        }}
        <span
          v-if="energia.left !== null"
          class="ml-1 text-p-sm font-normal text-ink-gray-6"
        >
          {{
            energia.left >= 0
              ? __('{0} left', [numero(energia.left)])
              : __('{0} over', [numero(-energia.left)])
          }}
        </span>
      </span>
    </div>
    <div class="grid grid-cols-4 gap-3 max-md:grid-cols-2">
      <div
        v-for="riga in macro"
        :key="riga.key"
        class="flex min-w-0 flex-col gap-1"
      >
        <span class="flex justify-between gap-1 text-p-xs text-ink-gray-6">
          <span class="truncate">{{ NOMI[riga.key] }}</span>
          <span class="shrink-0 tabular-nums text-ink-gray-8">
            {{ numero(riga.value)
            }}{{ riga.target ? ' / ' + numero(riga.target) : '' }} g
          </span>
        </span>
        <span
          class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-3"
          aria-hidden="true"
        >
          <span
            v-if="riga.share !== null"
            class="block h-full rounded-full bg-[var(--brand-segno,currentColor)]"
            :style="{ width: `${Math.round(riga.share * 100)}%` }"
          />
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { appLocale } from '@/utils/locale'
import { versoGliObiettivi } from '@/utils/piani'
import { computed } from 'vue'

const props = defineProps({
  // what the day gives, as nutrienti() counts it
  totals: { type: Object, required: true },
  targets: { type: Object, default: () => ({}) },
  // whose day: «Monday», «Every day»
  title: { type: String, default: '' },
})

const NOMI = {
  protein_g: __('Proteins'),
  carbs_g: __('Carbohydrates'),
  fat_g: __('Fats'),
  fibre_g: __('Fibre'),
}

const righe = computed(() => versoGliObiettivi(props.totals, props.targets))
const energia = computed(() => righe.value[0])
const macro = computed(() => righe.value.slice(1))

function numero(n) {
  return new Intl.NumberFormat(appLocale(), {
    maximumFractionDigits: 1,
  }).format(n || 0)
}
</script>
