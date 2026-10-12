<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The mark of a list pulled down from its top (composables/tiraPerAggiornare):
  an arrow that turns when letting go reloads, then the brand's loader while
  the list comes back. It takes no room when nobody pulls.

  A screen reader hears «Updating the list…» while it comes back, from a pull
  or from the page's «Refresh» (PulsanteAggiorna.vue), which is for whoever
  cannot pull: in a region there from the start, its words put in then. The
  region came with its words, inside a box hidden until that moment, and one
  inserted already filled is not announced reliably (Settings.vue's notice).
-->
<template>
  <div
    class="flex items-end justify-center overflow-hidden"
    :class="{ 'transition-[height] duration-200': !trascinando }"
    :style="{ height: `${distanza}px` }"
  >
    <div
      class="mb-3 flex size-8 items-center justify-center rounded-full bg-surface-elevation-2 text-ink-gray-7 shadow"
      :style="{ opacity: Math.min(1, distanza / 40) }"
      aria-hidden="true"
    >
      <LoadingIndicator v-if="inCorso" class="size-4" />
      <span
        v-else
        class="lucide-arrow-down size-4 transition-transform duration-150"
        :class="{ 'rotate-180': pronta }"
      />
    </div>
    <span class="sr-only" role="status">{{
      inCorso ? __('Updating the list…') : ''
    }}</span>
  </div>
</template>

<script setup>
import { LoadingIndicator } from 'frappe-ui'

// while a finger holds it the mark follows the finger; let go, it slides
defineProps({
  distanza: { type: Number, default: 0 },
  pronta: { type: Boolean, default: false },
  inCorso: { type: Boolean, default: false },
  trascinando: { type: Boolean, default: false },
  // the page's «Refresh» calls it (PulsanteAggiorna.vue), never the mark:
  // named here so that `v-bind` of the pull's state leaves it off the box
  aggiornaOra: { type: Function, default: null },
})
</script>
