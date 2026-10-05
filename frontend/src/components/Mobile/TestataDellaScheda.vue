<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The head of a company's or a contact's page on a phone: the picture, the name
  and what it is, the one thing done with it as a button and the rest under «⋯»
  - copying the link, deleting last and in red - as a person's page has them.
  The picture changes from a small camera on its corner. A dark band across the
  picture, shown for good where nothing hovers, covered its initial; and a red
  «Delete» beside the name was the largest button on the page.
-->
<template>
  <div class="flex items-center gap-4 p-4">
    <div class="relative shrink-0">
      <Avatar
        size="3xl"
        class="size-14.5"
        :class="{ 'dc-avatar--round': tondo }"
        :label="nome || titolo"
        :image="immagine"
      />
      <template v-if="puoCambiare">
        <Dropdown v-if="immagine" :options="opzioniImmagine">
          <button
            type="button"
            :class="camera"
            :aria-label="__('Change Image')"
          >
            <span class="lucide-camera size-3.5" aria-hidden="true" />
          </button>
        </Dropdown>
        <button
          v-else
          type="button"
          :class="camera"
          :aria-label="__('Upload Image')"
          @click="emit('scegli')"
        >
          <span class="lucide-camera size-3.5" aria-hidden="true" />
        </button>
      </template>
    </div>
    <div class="flex min-w-0 flex-1 flex-col gap-1">
      <h1 class="truncate text-lg-medium text-ink-gray-9">{{ titolo }}</h1>
      <p v-if="riga" class="truncate text-p-sm text-ink-gray-6">{{ riga }}</p>
      <div v-if="$slots.default || voci.length" class="flex gap-1.5 pt-1">
        <slot />
        <Dropdown v-if="voci.length" :options="voci">
          <Button icon="more-horizontal" :aria-label="__('More')" />
        </Dropdown>
      </div>
      <ErrorMessage :message="errore" />
    </div>
  </div>
</template>

<script setup>
import { Avatar, Button, Dropdown, ErrorMessage } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  titolo: { type: String, default: '' },
  // whose initial the picture shows when there is none: the name without the
  // salutation, or «Sig. Mario Rossi» drew an S
  nome: { type: String, default: '' },
  riga: { type: String, default: '' },
  immagine: { type: String, default: '' },
  // a company's mark is round, a person's picture keeps the brand's tail
  tondo: { type: Boolean, default: false },
  puoCambiare: { type: Boolean, default: false },
  // what the «⋯» holds: falsy entries left out
  altro: { type: Array, default: () => [] },
  errore: { type: String, default: '' },
})

const emit = defineEmits(['scegli', 'togli'])

const voci = computed(() => props.altro.filter(Boolean))

const opzioniImmagine = computed(() => [
  {
    icon: 'upload',
    label: __('Change Image'),
    onClick: () => emit('scegli'),
  },
  {
    icon: 'trash-2',
    label: __('Remove Image'),
    onClick: () => emit('togli'),
  },
])

// on the picture's corner, ringed by the page so it reads apart from it
const camera =
  'touch-target absolute -bottom-0.5 -right-0.5 grid size-6 place-items-center rounded-full bg-surface-gray-2 text-ink-gray-8 ring-2 ring-[var(--surface-base)] hover:bg-surface-gray-3'
</script>
