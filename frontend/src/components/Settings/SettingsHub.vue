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
    <!-- a row wider than the pane scrolls sideways: the edge it goes on
         behind fades, and the tab open is always in sight. On a phone
         Meta's fourth tab was past the edge with nothing to say so -->
    <div
      v-if="voce.tabs.length > 1"
      ref="barra"
      role="tablist"
      data-settings-tabs
      :style="sfumatura"
      :aria-label="__(voce.label)"
      class="flex h-[45px] shrink-0 items-stretch gap-6 overflow-x-auto border-b border-outline-elevation-2 px-8 [scrollbar-width:none] max-md:gap-5 max-md:px-5 [&::-webkit-scrollbar]:hidden"
      @scroll.passive="misura"
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
      data-pagina-impostazioni
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
import { useResizeObserver } from '@vueuse/core'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

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

// which edges the row goes on behind, and the open tab brought into sight
const barra = ref(null)
const oltre = ref({ sinistra: false, destra: false })
function misura() {
  const el = barra.value
  if (!el) return
  oltre.value = {
    sinistra: el.scrollLeft > 1,
    destra: el.scrollLeft + el.clientWidth < el.scrollWidth - 1,
  }
}
const sfumatura = computed(() => {
  const { sinistra, destra } = oltre.value
  if (!sinistra && !destra) return {}
  const maschera = `linear-gradient(to right, ${sinistra ? 'transparent, black 32px' : 'black'}, ${destra ? 'black calc(100% - 32px), transparent' : 'black'})`
  return { maskImage: maschera, WebkitMaskImage: maschera }
})
function mostraLaScelta() {
  const el = barra.value
  const tab = el?.querySelector('[aria-selected="true"]')
  if (!el || !tab) return
  // the row scrolled by hand, never the page (scrollIntoView slid an iPhone's).
  // Where the tab is in the row's own content, from the two boxes: its
  // offsetLeft counts from an ancestor (the menu beside it on a desk), and
  // after a scroll by hand it put the row back at the start
  const riga = el.getBoundingClientRect()
  const box = tab.getBoundingClientRect()
  const inizio = box.left - riga.left + el.scrollLeft - 32
  const fine = box.right - riga.left + el.scrollLeft + 32
  if (inizio < el.scrollLeft) el.scrollLeft = Math.max(0, inizio)
  else if (fine > el.scrollLeft + el.clientWidth)
    el.scrollLeft = fine - el.clientWidth
  misura()
}
watch(
  () => scheda.value?.key,
  () => nextTick(mostraLaScelta),
)
onMounted(() => nextTick(mostraLaScelta))
useResizeObserver(barra, misura)

function slug(testo) {
  return String(testo)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
}
</script>
