<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The design system's EmptyState (brand/dottorcloud/design-system/espresso/componenti/
  EmptyState): a small composition of the cover's blocks, the state in a
  title, a sentence with the real names that proposes what to do, the actions.
-->
<template>
  <div class="dc-empty">
    <EmptyArt />
    <!-- the words handed as they are written in the code read in the
         user's language: translated where they are drawn -->
    <!-- a heading at the level of where it stands: under a page's own name
         a page-sized state (the address that leads nowhere) is the next one -->
    <ElementoNativo :tag="`h${livello}`" class="dc-empty__title">
      {{ __(title) }}
    </ElementoNativo>
    <p v-if="text || description" class="dc-empty__text">
      {{ __(text || description) }}
    </p>
    <div v-if="$slots.default" class="dc-empty__actions">
      <slot />
    </div>
  </div>
</template>

<script setup>
import EmptyArt from '@/components/Espresso/EmptyArt.vue'
import ElementoNativo from '@/components/ElementoNativo.js'

defineProps({
  // the state: «No visits today»
  title: { type: String, required: true },
  text: { type: String, default: '' },
  // the name the lists' EmptyState gives the same sentence
  description: { type: String, default: '' },
  // its heading's level: 3 inside a page's section, 2 for a page of its own
  livello: { type: Number, default: 3 },
})
</script>
