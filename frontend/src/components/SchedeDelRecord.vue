<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A record's tabs on a computer: frappe-ui's Tabs (reka-ui's, with their roles
  and arrow keys) with «More» for the ones that do not fit, as the phone has
  them (SchedeDelTelefono). A person has fourteen tabs and the column beside
  the panel holds eight: the row scrolled sideways without a scrollbar, and
  Documents, Quotes, Plans, the client area, the Clinic and the History were
  out of sight with nothing saying they were there. Here the bar holds as many
  as fit (`quanteNellaBarra`) and «More» names the rest; when the open tab is
  one of those, «More» says its name.

  The same props, model and slots as frappe-ui's Tabs: `tabs` ({ name, label,
  icon }), the index as v-model, `tab-item` to draw a tab's words (a count
  beside them), `tab-panel` for the open one.
-->
<template>
  <TabsRoot
    v-model="indice"
    :as="as"
    class="flex flex-1 flex-col overflow-hidden"
    orientation="horizontal"
  >
    <div
      ref="barra"
      class="relative flex min-h-[45px] shrink-0 items-stretch border-b border-outline-gray-2 px-5 text-base"
    >
      <TabsList
        class="flex min-w-0 items-stretch gap-6"
        :aria-label="__('Sections')"
      >
        <TabsTrigger
          v-for="scheda in inBarra"
          :key="scheda.name || scheda.label"
          :value="props.tabs.indexOf(scheda)"
          class="relative flex shrink-0 items-center gap-1.5 whitespace-nowrap text-base text-ink-gray-5 outline-none transition-colors hover:text-ink-gray-9 focus-visible:ring-2 focus-visible:ring-[var(--brand-action)] data-[state=active]:text-ink-gray-9"
        >
          <slot
            name="tab-item"
            v-bind="{ tab: scheda, selected: aperta === scheda }"
          >
            <Icona :icona="scheda.icon" />
            {{ scheda.label }}
          </slot>
          <span
            v-if="aperta === scheda"
            class="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-[var(--brand-action)]"
            aria-hidden="true"
          />
        </TabsTrigger>
      </TabsList>
      <Dropdown v-if="altre.length" :options="opzioniAltre" placement="right">
        <template #default="{ open }">
          <button
            type="button"
            aria-haspopup="menu"
            class="relative ml-6 flex shrink-0 items-center gap-1.5 whitespace-nowrap text-base outline-none hover:text-ink-gray-9 focus-visible:ring-2 focus-visible:ring-[var(--brand-action)]"
            :class="apertaTraLeAltre ? 'text-ink-gray-9' : 'text-ink-gray-5'"
            :aria-label="
              apertaTraLeAltre
                ? __('{0}, other sections', [aperta.label])
                : __('Other sections')
            "
          >
            <Icona v-if="apertaTraLeAltre" :icona="aperta.icon" />
            {{ apertaTraLeAltre ? aperta.label : __('More') }}
            <span
              class="size-4 shrink-0"
              :class="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
              aria-hidden="true"
            />
            <span
              v-if="apertaTraLeAltre"
              class="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-[var(--brand-action)]"
              aria-hidden="true"
            />
          </button>
        </template>
        <template #item-suffix="{ item }">
          <span
            v-if="item.scelta"
            class="dc-scelto lucide-check size-4 text-ink-gray-7"
            aria-hidden="true"
          />
        </template>
      </Dropdown>
    </div>
    <TabsContent
      v-for="(scheda, i) in props.tabs"
      :key="scheda.name || scheda.label"
      :value="i"
      class="flex flex-col overflow-auto data-[state=active]:flex data-[state=active]:grow"
    >
      <slot name="tab-panel" v-bind="{ tab: scheda }" />
    </TabsContent>
  </TabsRoot>
</template>

<script setup>
import { quanteNellaBarra } from '@/utils/sulTelefono'
import { useElementSize } from '@vueuse/core'
import { Dropdown } from 'frappe-ui'
import { TabsContent, TabsList, TabsRoot, TabsTrigger } from 'reka-ui'
import { computed, h, onMounted, ref } from 'vue'

const props = defineProps({
  // the record's tabs: { name, label, icon }
  tabs: { type: Array, required: true },
  as: { type: String, default: 'div' },
})
const indice = defineModel({ type: Number, default: 0 })

// a tab's icon: a component, or a Lucide class
const Icona = (p) => {
  if (!p.icona) return null
  if (typeof p.icona === 'string') {
    return h('span', {
      class: ['size-4 shrink-0', p.icona],
      'aria-hidden': 'true',
    })
  }
  return h(p.icona, { class: 'size-4 shrink-0', 'aria-hidden': 'true' })
}
Icona.props = ['icona']

// what the bar has room for: its width less its padding and «More», each tab
// its words in the bar's type, its icon and the gap after it
const barra = ref(null)
const { width: spazio } = useElementSize(barra)
const font = ref('')
onMounted(() => {
  const misura = () => {
    const stile = barra.value && getComputedStyle(barra.value)
    if (stile) font.value = `${stile.fontSize} ${stile.fontFamily}`
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
const ICONA = 16 + 6
const SPAZIO_TRA = 24
const PADDING = 40
const quante = computed(() =>
  quanteNellaBarra(
    props.tabs.map(
      (scheda) =>
        larghezzaDi(scheda.label) +
        (scheda.icon ? ICONA : 0) +
        SPAZIO_TRA +
        // a count drawn beside the words (tab-item)
        (scheda.count != null ? 28 : 0),
    ),
    font.value ? Math.max(0, spazio.value - PADDING) : 0,
    // «More» or the longest name it may say, its icon and chevron
    Math.max(
      larghezzaDi(__('More')),
      ...props.tabs.map((scheda) => larghezzaDi(scheda.label) + ICONA),
    ) +
      SPAZIO_TRA +
      22,
    props.tabs.length,
  ),
)

const inBarra = computed(() =>
  quante.value >= props.tabs.length
    ? props.tabs
    : props.tabs.slice(0, quante.value),
)
const altre = computed(() =>
  props.tabs.filter((scheda) => !inBarra.value.includes(scheda)),
)
const aperta = computed(() => props.tabs[indice.value])
const apertaTraLeAltre = computed(() => altre.value.includes(aperta.value))

const opzioniAltre = computed(() =>
  altre.value.map((scheda) => ({
    label: scheda.label,
    icon: scheda.icon
      ? typeof scheda.icon === 'string'
        ? scheda.icon
        : h(scheda.icon, { class: 'size-4' })
      : undefined,
    scelta: scheda === aperta.value,
    onClick: () => (indice.value = props.tabs.indexOf(scheda)),
  })),
)
</script>
