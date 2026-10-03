<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A record's tabs on a phone (docs/progetto-ghl/29): a row of fifteen tabs
  scrolled sideways hides most of them, so the bar holds the few one opens every
  day - the ones asked for, in that order, the first four there are - and "More"
  holds the rest. When the open tab is one of those, "More" says its name. Each
  tab is as wide as its name and the room left is shared: in equal parts,
  «Documenti» was «Docu…» beside «Eventi».
-->
<template>
  <div
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
import { Dropdown } from 'frappe-ui'
import { computed, h } from 'vue'

const props = defineProps({
  // the record's tabs, as the page's Tabs has them: { name, label, icon }
  tabs: { type: Array, required: true },
  // the names the bar holds, by preference: the first four there are
  principali: { type: Array, default: () => [] },
})
const indice = defineModel({ type: Number, default: 0 })

const QUANTE = 4

const inBarra = computed(() => {
  // five or fewer fit as they are: a "More" holding one tab helps nobody
  if (props.tabs.length <= QUANTE + 1) return props.tabs
  const scelte = props.principali
    .map((nome) => props.tabs.find((t) => t.name === nome))
    .filter(Boolean)
  for (const scheda of props.tabs) {
    if (scelte.length >= QUANTE) break
    if (!scelte.includes(scheda)) scelte.push(scheda)
  }
  return scelte.slice(0, QUANTE)
})
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
