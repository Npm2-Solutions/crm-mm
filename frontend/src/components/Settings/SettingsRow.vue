<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  One labelled setting: title and explanation on the left, the control on the
  right. The same row four settings pages were each spelling out by hand.

  The words keep at least 15rem. Where that and the control do not fit side by
  side — a phone, a wide field — the control goes under them instead of
  squeezing them into a column one word wide.
-->
<template>
  <!-- a switch stays beside its words, however narrow: only a wider control
       (a field, a select) goes under them -->
  <div
    class="flex flex-wrap has-[[role=switch]]:flex-nowrap items-center justify-between gap-x-4 gap-y-2 py-3 px-2"
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
  label: { type: String, required: true },
  description: { type: String, default: '' },
})

const scatola = ref(null)
const perId = useNomeAlControllo(scatola)
</script>
