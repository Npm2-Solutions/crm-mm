<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The design system's StatTile (brand/design-system/espresso/componenti/
  StatTile): the number, the crosses in its corner; the most important of a
  row is a deep block, one a row.
-->
<template>
  <component
    :is="to ? 'RouterLink' : 'div'"
    :to="to"
    class="dc-stat"
    :class="{ 'dc-stat--brand': blocco, 'dc-stat--link': to }"
  >
    <span class="dc-crosses" aria-hidden="true" />
    <span class="dc-stat__label">{{ label }}</span>
    <span class="dc-stat__value">
      <slot>{{ value }}</slot>
    </span>
  </component>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '' },
  // the most important number of its row: a deep block
  blocco: { type: Boolean, default: false },
  to: { type: [String, Object], default: null },
})
</script>
