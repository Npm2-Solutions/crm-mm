<!--
  A menu's day, from the food tables: what each day gives next to the
  nutritionist's targets. Numbers only, no colours: the nutritionist reads them.
-->
<template>
  <div class="flex flex-col gap-2 rounded-lg bg-surface-gray-1 p-3">
    <span class="text-sm font-medium text-ink-gray-7">
      {{ __('The day, from the food tables') }}
    </span>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[34rem] text-p-sm">
        <thead>
          <tr class="text-ink-gray-5">
            <th class="py-1 pr-3 text-left font-normal" />
            <th
              v-for="column in columns"
              :key="column.key"
              class="px-2 py-1 text-right font-normal"
            >
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="hasTargets" class="text-ink-gray-5">
            <td class="py-1 pr-3">{{ __('Target') }}</td>
            <td
              v-for="column in columns"
              :key="column.key"
              class="px-2 py-1 text-right tabular-nums"
            >
              {{ Number(targets[column.key]) > 0 ? targets[column.key] : '–' }}
            </td>
          </tr>
          <tr
            v-for="row in days"
            :key="row.day"
            class="border-t border-outline-gray-1 text-ink-gray-8"
          >
            <td class="py-1 pr-3">{{ __(row.day) }}</td>
            <td
              v-for="column in columns"
              :key="column.key"
              class="px-2 py-1 text-right tabular-nums"
            >
              {{ row[column.key] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <span v-if="missing" class="text-p-xs text-ink-gray-5">
      {{
        missing === 1
          ? __(
              'A food without grams, or without values in the tables, is not counted',
            )
          : __(
              '{0} foods without grams, or without values in the tables, are not counted',
              [missing],
            )
      }}
    </span>
  </div>
</template>

<script setup>
import { NUTRIENTI } from '@/utils/piani'
import { computed } from 'vue'

const props = defineProps({
  // one row a day, as perGiorno counts it
  days: { type: Array, required: true },
  targets: { type: Object, default: () => ({}) },
  missing: { type: Number, default: 0 },
})

const columns = [
  { key: 'kcal', label: 'kcal' },
  { key: 'protein_g', label: __('Proteins (g)') },
  { key: 'carbs_g', label: __('Carbohydrates (g)') },
  { key: 'fat_g', label: __('Fats (g)') },
  { key: 'fibre_g', label: __('Fibre (g)') },
]

const hasTargets = computed(() =>
  NUTRIENTI.some((n) => Number(props.targets?.[n]) > 0),
)
</script>
