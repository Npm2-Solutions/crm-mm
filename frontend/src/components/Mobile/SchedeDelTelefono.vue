<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A record's tabs on a phone (docs/crm/29): a row of fifteen tabs
  scrolled sideways hides most of them, so the bar holds the few one opens every
  day - the ones asked for, in that order, the first four there are - and "More"
  holds the rest. When the open tab is one of those, "More" says its name. Each
  tab is as wide as its name and the room left is shared: in equal parts,
  «Documenti» was «Docu…» beside «Eventi». The bar holds as many as fit beside
  "More" (`quanteNellaBarra`): a page zoomed - large text on Android, 277
  points on a 360 phone - had four tabs read «Detta…», «Eve…», «Preventi…».
-->
<template>
  <div
    ref="barra"
    class="flex shrink-0 items-stretch border-b border-outline-gray-2 px-1"
    role="tablist"
    :aria-label="__('Sections')"
  >
    <button
      v-for="scheda in inBarra"
      :key="scheda.name"
      type="button"
      role="tab"
      :aria-selected="scheda.name === aperta?.name"
      class="relative flex min-w-0 flex-auto items-center justify-center px-1 py-3 text-base"
      :class="
        scheda.name === aperta?.name
          ? 'font-medium text-ink-gray-9'
          : 'text-ink-gray-5'
      "
      @click="apri(scheda)"
    >
      <span class="truncate">{{ scheda.label }}</span>
      <span
        v-if="scheda.name === aperta?.name"
        class="absolute inset-x-3 bottom-0 h-0.5 rounded-full bg-[var(--brand-action)]"
        aria-hidden="true"
      />
    </button>
    <Dropdown v-if="altre.length" :options="opzioniAltre" placement="right">
      <template #default="{ open }">
        <button
          type="button"
          role="tab"
          :aria-selected="apertaTraLeAltre"
          aria-haspopup="menu"
          class="relative flex min-w-0 flex-auto items-center justify-center gap-1 px-1 py-3 text-base"
          :class="
            apertaTraLeAltre ? 'font-medium text-ink-gray-9' : 'text-ink-gray-5'
          "
        >
          <span class="truncate">
            {{ apertaTraLeAltre ? aperta.label : __('More') }}
          </span>
          <span
            class="size-4 shrink-0"
            :class="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
            aria-hidden="true"
          />
          <span
            v-if="apertaTraLeAltre"
            class="absolute inset-x-3 bottom-0 h-0.5 rounded-full bg-[var(--brand-action)]"
            aria-hidden="true"
          />
        </button>
      </template>
    </Dropdown>
  </div>
</template>

<script setup>
import { quanteNellaBarra } from '@/utils/sulTelefono'
import { useElementSize } from '@vueuse/core'
import { Dropdown } from 'frappe-ui'
import { computed, h, onMounted, ref } from 'vue'

const props = defineProps({
  // the record's tabs, as the page's Tabs has them: { name, label, icon }
  tabs: { type: Array, required: true },
  // the names the bar holds, by preference: the first four there are
  principali: { type: Array, default: () => [] },
})
const indice = defineModel({ type: Number, default: 0 })

const QUANTE = 4

// the order the bar takes them in: the ones asked for, then the others
const inOrdine = computed(() => {
  const scelte = props.principali
    .map((nome) => props.tabs.find((t) => t.name === nome))
    .filter(Boolean)
  for (const scheda of props.tabs) {
    if (!scelte.includes(scheda)) scelte.push(scheda)
  }
  return scelte
})

// what the bar has room for: its width, and each word in the bar's own type
// as the open tab wears it (medium), with the tab's padding around it
const barra = ref(null)
const { width: spazio } = useElementSize(barra)
const font = ref('')
onMounted(() => {
  const misura = () => {
    const stile = barra.value && getComputedStyle(barra.value)
    if (stile) font.value = `500 ${stile.fontSize} ${stile.fontFamily}`
  }
  misura()
  // the typeface may arrive after the bar: measured again with it
  document.fonts?.ready?.then(misura)
})
let tela = null
function larghezzaDi(parole) {
  if (!font.value) return 0
  tela ||= document.createElement('canvas').getContext('2d')
  if (!tela) return 0
  tela.font = font.value
  return Math.ceil(tela.measureText(parole).width)
}
const MARGINE = 12
const quante = computed(() =>
  quanteNellaBarra(
    inOrdine.value.map((scheda) => larghezzaDi(scheda.label) + MARGINE),
    font.value ? spazio.value : 0,
    // «More» and its chevron
    larghezzaDi(__('More')) + MARGINE + 20,
    QUANTE,
  ),
)

const inBarra = computed(() =>
  // all of them, as they come, when they all fit: a "More" holding one tab
  // helps nobody
  quante.value >= props.tabs.length
    ? props.tabs
    : inOrdine.value.slice(0, quante.value),
)
const altre = computed(() =>
  props.tabs.filter((t) => !inBarra.value.includes(t)),
)
const aperta = computed(() => props.tabs[indice.value])
const apertaTraLeAltre = computed(() => altre.value.includes(aperta.value))

const opzioniAltre = computed(() =>
  altre.value.map((scheda) => ({
    label: scheda.label,
    icon: scheda.icon ? h(scheda.icon, { class: 'size-4' }) : undefined,
    onClick: () => apri(scheda),
  })),
)

function apri(scheda) {
  const i = props.tabs.indexOf(scheda)
  if (i >= 0) indice.value = i
}
</script>
