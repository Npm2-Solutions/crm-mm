<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  An entry of the settings with several sides: one page, its tabs along the top,
  drawn like a person's record (Activity, Emails, Notes…). The tab open is the page
  asked for (`activeSettingsPage`): a link to an old page's name lands on its tab,
  and choosing a tab here names that page, as a link would. With one tab left for
  this person there is no bar: the entry is that page.
-->
<template>
  <!-- the room left under the phone's own bar, not a screen's height: the
       tabs stay put and the page scrolls under them -->
  <div class="flex min-h-0 flex-1 flex-col">
    <div
      v-if="voce.tabs.length > 1"
      role="tablist"
      data-settings-tabs
      :aria-label="__(voce.label)"
      class="flex h-[45px] shrink-0 items-stretch gap-6 overflow-x-auto border-b border-outline-elevation-2 px-8 [scrollbar-width:none] max-md:gap-5 max-md:px-5 [&::-webkit-scrollbar]:hidden"
    >
      <button
        v-for="tab in voce.tabs"
        :id="`settings-tab-${slug(tab.key)}`"
        :key="tab.key"
        type="button"
        role="tab"
        :aria-selected="tab.key === scheda.key"
        :aria-controls="`settings-panel-${slug(voce.key)}`"
        :tabindex="tab.key === scheda.key ? 0 : -1"
        class="relative flex shrink-0 items-center whitespace-nowrap text-base transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-outline-gray-3"
        :class="
          tab.key === scheda.key
            ? 'text-ink-gray-9 after:absolute after:inset-x-0 after:bottom-0 after:h-[2px] after:bg-surface-gray-10'
            : 'text-ink-gray-5 hover:text-ink-gray-8'
        "
        @click="scegli(tab)"
        @keydown.right.prevent="sposta(1)"
        @keydown.left.prevent="sposta(-1)"
      >
        {{ __(tab.label) }}
      </button>
    </div>
    <div
      :id="`settings-panel-${slug(voce.key)}`"
      :role="voce.tabs.length > 1 ? 'tabpanel' : undefined"
      :aria-labelledby="
        voce.tabs.length > 1 ? `settings-tab-${slug(scheda.key)}` : undefined
      "
      class="min-h-0 flex-1 overflow-y-auto"
    >
      <component :is="scheda.component" :key="scheda.key" />
    </div>
  </div>
</template>

<script setup>
import { activeSettingsPage } from '@/composables/settings'
import { schedaDi } from '@/utils/impostazioni'
import { computed, nextTick } from 'vue'

const props = defineProps({
  // the entry, with the tabs this person may open, each with its component
  voce: { type: Object, required: true },
})

const scheda = computed(() => schedaDi(props.voce, activeSettingsPage.value))

function scegli(tab) {
  activeSettingsPage.value = tab.key
}

// the arrows move along the tabs, as in any tab bar
function sposta(passo) {
  const tabs = props.voce.tabs
  const qui = tabs.findIndex((tab) => tab.key === scheda.value.key)
  const dopo = (qui + passo + tabs.length) % tabs.length
  scegli(tabs[dopo])
  nextTick(() =>
    document.getElementById(`settings-tab-${slug(tabs[dopo].key)}`)?.focus(),
  )
}

function slug(testo) {
  return String(testo)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
}
</script>
