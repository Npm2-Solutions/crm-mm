<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Where a feature is set up: its pages of the settings, the ones the person
  sees, each a step away (Settings > The centre > Features, doc 36).
-->
<template>
  <div v-if="link.length" class="flex flex-wrap items-center gap-1.5">
    <span class="text-p-sm text-ink-gray-5">{{ __('Set it up') }}</span>
    <button
      v-for="voce in link"
      :key="voce.page"
      type="button"
      class="inline-flex h-6 items-center gap-0.5 rounded-md max-md:h-8 bg-surface-gray-2 pl-2 pr-1 text-p-sm text-ink-gray-8 hover:bg-surface-gray-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
      @click="activeSettingsPage = voce.page"
    >
      {{ voce.tab ? `${__(voce.label)} › ${__(voce.tab)}` : __(voce.label) }}
      <span
        class="lucide-chevron-right size-3.5 text-ink-gray-5"
        aria-hidden="true"
      />
    </button>
  </div>
</template>

<script setup>
import { activeSettingsPage } from '@/composables/settings'
import { doveSiImposta } from '@/utils/funzionalita'
import { computed, inject } from 'vue'

const props = defineProps({
  // the pages the server names for the module, keys of the settings' menu
  pagine: { type: Array, default: () => [] },
})

// the menu the person sees, from the modal holding the page
const menu = inject('menuDelleImpostazioni', null)

const link = computed(() => doveSiImposta(menu?.value || [], props.pagine))
</script>
