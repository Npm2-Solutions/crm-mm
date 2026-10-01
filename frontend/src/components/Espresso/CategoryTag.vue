<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The design system's Tag (brand/design-system/espresso/componenti/Tag): what
  kind of thing it is, square with the cloud's tail - never a state's pill,
  which is a Badge. Blue documents, violet exercises and marketing, amber the
  waiting list and internal notes, rose specialties and allergies, green
  WhatsApp and what is done, brand what is the centre's.
-->
<template>
  <span class="dc-tag" :class="`dc-tag--${tono}`">
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  color: { type: String, default: 'brand' },
})

const TONI = ['blue', 'violet', 'amber', 'rose', 'green', 'brand']
const tono = computed(() =>
  TONI.includes(props.color) ? props.color : 'brand',
)
</script>
