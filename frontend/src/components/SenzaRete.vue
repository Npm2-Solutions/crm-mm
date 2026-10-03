<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The device has lost the network - a lift, a corridor, a basement - and
  nothing said so: a save failed with the browser's own words. A line under
  the header says it, and what it means, until the network comes back.
-->
<template>
  <div
    v-if="senzaRete"
    role="status"
    class="flex shrink-0 items-start gap-2 border-b border-outline-amber-2 bg-surface-amber-1 px-3 py-2 text-p-sm text-ink-amber-8"
  >
    <span class="lucide-wifi-off mt-0.5 size-4 shrink-0" aria-hidden="true" />
    <span class="min-w-0">
      {{ __('No network: until it comes back, changes are not saved.') }}
    </span>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const senzaRete = ref(navigator.onLine === false)

function guarda() {
  senzaRete.value = navigator.onLine === false
}

onMounted(() => {
  window.addEventListener('online', guarda)
  window.addEventListener('offline', guarda)
  guarda()
})
onBeforeUnmount(() => {
  window.removeEventListener('online', guarda)
  window.removeEventListener('offline', guarda)
})
</script>
