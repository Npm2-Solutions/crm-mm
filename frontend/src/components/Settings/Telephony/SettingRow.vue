<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  As SettingsRow: the control goes under the words when both do not fit.
-->
<template>
  <!-- a switch stays beside its words, however narrow: only a wider control
       (a field, a select) goes under them -->
  <div
    class="flex flex-wrap has-[[role=switch]]:flex-nowrap items-center justify-between gap-x-8 gap-y-2 py-3 pl-2 pr-1"
  >
    <div class="flex min-w-0 flex-1 basis-60 flex-col">
      <!-- the words name the control beside them, and tapping them flips a
           switch (useNomeAlControllo) -->
      <label
        :for="perId || undefined"
        class="text-p-base-medium text-ink-gray-7"
        :class="perId && 'cursor-pointer'"
      >
        {{ label }}
      </label>
      <div v-if="description" class="text-p-sm text-ink-gray-5">
        {{ description }}
      </div>
    </div>
    <div ref="scatola" class="shrink-0">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { useNomeAlControllo } from '@/composables/nomeAlControllo'
import { ref } from 'vue'

defineProps({
  label: { type: String, default: '' },
  description: { type: String, default: '' },
})

const scatola = ref(null)
const perId = useNomeAlControllo(scatola)
</script>
