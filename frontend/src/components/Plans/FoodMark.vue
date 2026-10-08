<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A food's mark: what its name says it is (a banana, a coffee), else its group,
  in the group's category colour - the catalogue's card, the editor's row and
  the patient's item tell a food at a glance. A mark beside its name, never in
  place of it.
-->
<template>
  <span
    class="flex shrink-0 items-center justify-center"
    :class="[forma, misure.box]"
    :style="{
      background: `var(--cat-${aspetto.colore}-subtle)`,
      color: `var(--cat-${aspetto.colore}-text)`,
    }"
    aria-hidden="true"
  >
    <span :class="[aspetto.icona, misure.icona]" />
  </span>
</template>

<script setup>
import { aspettoDelCibo } from '@/utils/piani'
import { computed } from 'vue'

const props = defineProps({
  // a food: its food_name and food_group are enough
  food: { type: Object, default: null },
  size: { type: String, default: 'md' },
})

const aspetto = computed(() => aspettoDelCibo(props.food))
const misure = computed(
  () =>
    ({
      sm: { box: 'size-8', icona: 'size-4' },
      md: { box: 'size-10', icona: 'size-5' },
      lg: { box: 'aspect-[4/3] w-full', icona: 'size-10' },
    })[props.size] || { box: 'size-10', icona: 'size-5' },
)
// the cloud's tail of the design system on the small marks
const forma = computed(() =>
  props.size === 'lg' ? '' : 'rounded-[10px_10px_10px_2px]',
)
</script>
