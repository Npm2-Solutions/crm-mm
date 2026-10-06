<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  How the agenda looks to whoever reads it, kept in their browser: columns by
  professional or by room, how tall an hour is, the colours by service or by
  state (with what each state's colour means), whether those off duty and the
  cancelled appointments show. Below, where the centre sets the agenda up and
  where one's own Google Calendar is connected.
-->
<template>
  <Popover placement="bottom-end">
    <template #target="{ togglePopover }">
      <Button :aria-label="__('View options')" @click="togglePopover">
        <template #prefix>
          <span
            class="lucide-sliders-horizontal size-4 text-ink-gray-6"
            aria-hidden="true"
          />
        </template>
        <span class="max-md:hidden">{{
          __('View', null, 'Agenda options')
        }}</span>
      </Button>
    </template>
    <template #body-main="{ close }">
      <div
        data-foglio
        class="flex w-80 flex-col gap-1 overflow-y-auto p-3 max-md:gap-2"
      >
        <span v-if="conColonne" class="flex flex-col gap-1.5 pb-2">
          <span class="text-xs-medium text-ink-gray-5">
            {{ __('Columns') }}
          </span>
          <TabButtons
            :modelValue="colonne"
            :buttons="[
              { label: __('Professionals'), value: 'staff' },
              { label: __('Rooms', null, 'Agenda columns'), value: 'resource' },
            ]"
            @update:modelValue="(valore) => $emit('update:colonne', valore)"
          />
        </span>
        <span v-if="conAltezza" class="flex flex-col gap-1.5 pb-2">
          <span class="text-xs-medium text-ink-gray-5">
            {{ __('Height of the hours') }}
          </span>
          <TabButtons
            :modelValue="altezza"
            :buttons="[
              {
                label: __('Compact', null, 'Agenda height'),
                value: 'compatta',
              },
              { label: __('Normal', null, 'Agenda height'), value: 'normale' },
              { label: __('Large', null, 'Agenda height'), value: 'ampia' },
            ]"
            @update:modelValue="(valore) => $emit('update:altezza', valore)"
          />
        </span>
        <span class="flex flex-col gap-1.5 pb-2">
          <span class="text-xs-medium text-ink-gray-5">
            {{ __('Colours') }}
          </span>
          <TabButtons
            :modelValue="colore"
            :buttons="[
              { label: __('By service'), value: 'servizio' },
              { label: __('By state'), value: 'stato' },
            ]"
            @update:modelValue="(valore) => $emit('update:colore', valore)"
          />
          <!-- what each state's colour means: never a colour alone -->
          <span
            v-if="colore === 'stato'"
            class="grid grid-cols-2 gap-x-3 gap-y-1 pt-1"
          >
            <span
              v-for="stato in STATI"
              :key="stato.valore"
              class="flex min-w-0 items-center gap-1.5 text-p-xs text-ink-gray-7"
            >
              <span
                class="size-2.5 shrink-0 rounded-sm"
                :style="{ background: COLORI_DEGLI_STATI[stato.valore] }"
                aria-hidden="true"
              />
              <span class="truncate">{{ stato.testo }}</span>
            </span>
          </span>
        </span>
        <label
          v-if="conTutti"
          class="flex cursor-pointer items-center justify-between gap-3 py-1"
        >
          <span class="text-p-sm text-ink-gray-8">
            {{ __('Show who is off duty') }}
          </span>
          <Switch
            :modelValue="tutti"
            :aria-label="__('Show who is off duty')"
            @update:modelValue="(valore) => $emit('update:tutti', valore)"
          />
        </label>
        <label
          class="flex cursor-pointer items-center justify-between gap-3 py-1"
        >
          <span class="text-p-sm text-ink-gray-8">
            {{ __('Show cancelled appointments') }}
          </span>
          <Switch
            :modelValue="annullati"
            :aria-label="__('Show cancelled appointments')"
            @update:modelValue="(valore) => $emit('update:annullati', valore)"
          />
        </label>
        <span
          v-if="impostazioni || google"
          class="mt-1 flex flex-col border-t border-outline-gray-2 pt-2"
        >
          <button
            v-if="impostazioni"
            type="button"
            class="flex items-center gap-2 rounded px-1.5 py-1.5 text-left text-p-sm text-ink-gray-8 hover:bg-surface-gray-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
            @click="apri('Calendar & reminders', close)"
          >
            <span
              class="lucide-settings size-4 text-ink-gray-6"
              aria-hidden="true"
            />
            {{ __('Agenda settings') }}
          </button>
          <button
            v-if="google"
            type="button"
            class="flex items-center gap-2 rounded px-1.5 py-1.5 text-left text-p-sm text-ink-gray-8 hover:bg-surface-gray-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
            @click="apri('Google Calendar', close)"
          >
            <span
              class="lucide-calendar-sync size-4 text-ink-gray-6"
              aria-hidden="true"
            />
            {{ __('Your Google Calendar') }}
          </button>
        </span>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { apriImpostazioni } from '@/composables/settings'
import { COLORI_DEGLI_STATI } from '@/utils/agenda'
import { Button, Popover, Switch, TabButtons } from 'frappe-ui'

defineProps({
  colonne: { type: String, default: 'staff' },
  altezza: { type: String, default: 'normale' },
  colore: { type: String, default: 'servizio' },
  tutti: { type: Boolean, default: false },
  annullati: { type: Boolean, default: false },
  /** what this view has: columns (a day, a week), hours (not a month), off duty (a day) */
  conColonne: { type: Boolean, default: true },
  conAltezza: { type: Boolean, default: true },
  conTutti: { type: Boolean, default: true },
  /** the links: the centre's agenda settings, one's own Google Calendar */
  impostazioni: { type: Boolean, default: false },
  google: { type: Boolean, default: false },
})
defineEmits([
  'update:colonne',
  'update:altezza',
  'update:colore',
  'update:tutti',
  'update:annullati',
])

const STATI = [
  { valore: 'Scheduled', testo: __('Booked') },
  { valore: 'Confirmed', testo: __('Confirmed') },
  { valore: 'Arrived', testo: __('In the waiting room') },
  { valore: 'Completed', testo: __('Completed') },
  { valore: 'No Show', testo: __('No Show') },
  { valore: 'Cancelled', testo: __('Cancelled') },
]

function apri(pagina, close) {
  close?.()
  apriImpostazioni({ page: pagina })
}
</script>
