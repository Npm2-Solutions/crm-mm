<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  A page that does not open: a person one does not follow, a record gone. It
  is a state, not a fault, so it wears the design system's EmptyState - the
  cover's blocks, the state in a title, the sentence that says what to do -
  not a red sign (`utils/schedaChiusa.js` has the words).
-->
<template>
  <div class="grid h-full place-items-center px-4 py-12">
    <div class="dc-empty max-w-md">
      <EmptyArt />
      <h3 class="dc-empty__title">{{ errorTitle }}</h3>
      <!-- eslint-disable-next-line vue/no-v-html -->
      <p class="dc-empty__text" v-html="sanitizeHTML(errorMessage)" />
    </div>
  </div>
</template>

<script setup>
import EmptyArt from '@/components/Espresso/EmptyArt.vue'
import { sanitizeHTML } from '@/utils'

defineProps({
  errorTitle: { type: String, required: true },
  errorMessage: { type: String, required: true },
})
</script>
