<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The phone at the top of every page (docs/crm/34): where a telephony
  is on, for whoever calls or reads the calls. Its mark counts the callbacks
  owed now; it opens the phone at hand (PhonePanel) - under the button on a
  computer, from the bottom on a phone. It replaces the keypad and the calls
  the menu had as pages: calling is something one does, not a place.
-->
<template>
  <template v-if="visibile">
    <Popover
      v-if="!isMobileView"
      v-model:open="aperto"
      side="bottom"
      align="end"
    >
      <template #trigger>
        <button
          type="button"
          :class="pulsante"
          :aria-label="etichetta"
          :title="etichetta"
        >
          <PhoneIcon class="size-4" />
          <span v-if="dovute" :class="segno">{{ dovute }}</span>
        </button>
      </template>
      <template #default="{ close }">
        <div class="max-h-[calc(100vh-4rem)] w-80 overflow-y-auto">
          <PhonePanel v-if="aperto" @done="close" />
        </div>
      </template>
    </Popover>
    <template v-else>
      <button
        type="button"
        :class="pulsante"
        :aria-label="etichetta"
        @click="aperto = true"
      >
        <PhoneIcon class="size-4" />
        <span v-if="dovute" :class="segno">{{ dovute }}</span>
      </button>
      <Dialog v-model="aperto" :options="{ title: __('Phone'), size: 'sm' }">
        <template #body-content>
          <div class="-mx-3 -mb-3">
            <PhonePanel v-if="aperto" @done="aperto = false" />
          </div>
        </template>
      </Dialog>
    </template>
  </template>
</template>

<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import PhonePanel from '@/components/Telephony/PhonePanel.vue'
import { isMobileView } from '@/composables/breakpoints'
import { usePannelloTelefono } from '@/composables/pannelloTelefono'
import { Dialog, Popover } from 'frappe-ui'
import { computed, ref } from 'vue'

const { visibile, dovute } = usePannelloTelefono()
const aperto = ref(false)

const etichetta = computed(() =>
  dovute.value ? __('Phone · {0} to call back', [dovute.value]) : __('Phone'),
)

const pulsante =
  'touch-target relative grid size-8 place-items-center rounded-md text-ink-gray-7 hover:bg-surface-gray-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3'
const segno =
  'absolute -right-1 -top-1 min-w-4 rounded-full bg-[var(--brand-action)] px-1 text-center text-[10px] font-semibold leading-4 text-[var(--on-brand-solid)]'
</script>
