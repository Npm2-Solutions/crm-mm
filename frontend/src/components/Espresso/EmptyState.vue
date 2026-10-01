<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The design system's EmptyState (brand/design-system/espresso/componenti/
  EmptyState): a small composition of the cover's blocks, the state in a
  title, a sentence with the real names that proposes what to do, the actions.
-->
<template>
  <div class="dc-empty">
    <EmptyArt />
    <h3 class="dc-empty__title">{{ title }}</h3>
    <p v-if="text" class="dc-empty__text">{{ text }}</p>
    <div v-if="$slots.default" class="dc-empty__actions">
      <slot />
    </div>
  </div>
</template>

<script setup>
import EmptyArt from '@/components/Espresso/EmptyArt.vue'

defineProps({
  // the state: «No visits today»
  title: { type: String, required: true },
  text: { type: String, default: '' },
})
</script>
