<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The line that says what a tab is for: whole on a desk; on a phone its first
  two lines, with «Show more» when there is more, so what the tab holds starts
  in the first screen and not under five lines of explanation.
-->
<template>
  <div class="min-w-0 text-p-base text-ink-gray-6">
    <p ref="testo" :class="{ 'max-md:line-clamp-2': !aperta }">
      <slot />
    </p>
    <button
      v-if="tagliata && !aperta"
      type="button"
      class="touch-target mt-1 text-p-sm font-medium text-[var(--brand-action)] md:hidden"
      @click="aperta = true"
    >
      {{ __('Show more') }}
    </button>
  </div>
</template>

<script setup>
import { useResizeObserver } from '@vueuse/core'
import { ref } from 'vue'

const testo = ref(null)
const aperta = ref(false)
const tagliata = ref(false)

// whether the two lines hide something: a short line needs no button
useResizeObserver(testo, () => {
  const el = testo.value
  tagliata.value = !!el && el.scrollHeight > el.clientHeight + 1
})
</script>
