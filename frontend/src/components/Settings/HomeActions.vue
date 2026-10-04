<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  What the menu under the centre's name offers everyone, in order. The standard
  entries read in the user's language and only show or hide (Log out always
  shows: nobody is locked in); the centre's own links have a name and an
  address, a separator splits them into groups.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 p-8 text-ink-gray-8 max-md:px-5 max-md:py-5"
  >
    <div
      class="flex justify-between text-ink-gray-8 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Menu') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'What the menu under the centre’s name, at the top left, offers everyone.',
            )
          }}
        </p>
      </div>
      <div class="flex shrink-0 items-start gap-2">
        <AzioneImpostazioni
          v-if="document.isDirty"
          :loading="document.save?.loading"
          :disabled="Boolean(errore)"
          @click="updateSettings"
        />
      </div>
    </div>

    <div v-if="document.doc" class="flex flex-1 flex-col gap-3 overflow-y-auto">
      <Draggable
        v-model="document.doc.dropdown_items"
        item-key="name"
        handle=".maniglia"
        class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        @end="riordina"
      >
        <template #item="{ element: voce, index }">
          <div class="flex items-center gap-3 px-3 py-2.5">
            <button
              type="button"
              class="maniglia touch-target flex shrink-0 cursor-grab items-center text-ink-gray-5"
              :aria-label="__('Move')"
            >
              <span class="lucide-grip-vertical size-4" aria-hidden="true" />
            </button>

            <template v-if="voce.type === 'Separator'">
              <div class="flex min-w-0 flex-1 items-center gap-2">
                <span class="flex-1 border-t border-outline-gray-2" />
                <span class="shrink-0 text-p-sm text-ink-gray-5">
                  {{ __('Separator') }}
                </span>
                <span class="flex-1 border-t border-outline-gray-2" />
              </div>
            </template>

            <template v-else-if="voce.is_standard">
              <div class="flex min-w-0 flex-1 flex-col">
                <span
                  class="truncate text-base"
                  :class="voce.hidden ? 'text-ink-gray-5' : 'text-ink-gray-8'"
                >
                  {{ __(voce.label) }}
                </span>
                <span class="text-p-sm text-ink-gray-5">
                  {{ __(COSA_FA[voce.name1] || 'Comes with {brand}') }}
                </span>
              </div>
            </template>

            <template v-else>
              <div class="flex min-w-0 flex-1 flex-col gap-2">
                <div class="grid grid-cols-2 gap-2 max-md:grid-cols-1">
                  <FormControl
                    v-model="voce.label"
                    size="sm"
                    :placeholder="__('Name')"
                    :aria-label="__('Name')"
                  />
                  <FormControl
                    v-model="voce.route"
                    size="sm"
                    :placeholder="__('https://… or /crm/…')"
                    :aria-label="__('Address')"
                  />
                </div>
                <FormControl
                  v-model="voce.open_in_new_window"
                  type="checkbox"
                  :label="__('New window')"
                />
              </div>
            </template>

            <div class="flex shrink-0 items-center gap-1">
              <Switch
                v-if="voce.type !== 'Separator' && voce.name1 !== 'logout'"
                :model-value="!voce.hidden"
                size="sm"
                :aria-label="__('Visible')"
                @update:model-value="(v) => (voce.hidden = v ? 0 : 1)"
              />
              <Button
                v-if="!voce.is_standard"
                variant="ghost"
                icon="lucide-trash-2"
                :aria-label="__('Remove')"
                @click="togli(index)"
              />
            </div>
          </div>
        </template>
      </Draggable>

      <div class="flex flex-wrap gap-2">
        <Button
          :label="__('Add a link')"
          icon-left="lucide-plus"
          @click="aggiungi('Route')"
        />
        <Button :label="__('Add a separator')" @click="aggiungi('Separator')" />
      </div>
      <ErrorMessage :message="errore" />
    </div>
  </div>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import { showSettings } from '@/composables/settings'
import { useDocument } from '@/data/document'
import { safeDropdownRoute } from '@/utils/dropdownItems'
import { Button, ErrorMessage, FormControl, Switch } from 'frappe-ui'
import { computed, provide } from 'vue'
import Draggable from 'vuedraggable'

const { document, triggerOnChange } = useDocument(
  'FCRM Settings',
  'FCRM Settings',
)

provide('triggerOnChange', triggerOnChange)

// what each standard entry does, said under its name
const COSA_FA = {
  app_selector: 'Opens the other apps of the site',
  settings: 'Opens the settings',
  about: 'The version and the licence',
  logout: 'Always shown: nobody is left without a way out',
}

// a link the menu would not open is said before it is saved
const errore = computed(() => {
  const voci = document.doc?.dropdown_items || []
  if (
    voci.some((v) => v.type === 'Route' && !v.is_standard && !v.label?.trim())
  )
    return __('Every link needs a name.')
  if (
    voci.some(
      (v) =>
        v.type === 'Route' && !v.is_standard && !safeDropdownRoute(v.route),
    )
  )
    return __(
      'An address starts with https:// or with / for a page of {brand}.',
    )
  return ''
})

function riordina() {
  document.doc.dropdown_items.forEach((voce, i) => (voce.idx = i + 1))
}

function aggiungi(tipo) {
  const voci = document.doc.dropdown_items
  voci.push({
    name: Math.random().toString(36).slice(2, 12),
    __islocal: true,
    doctype: 'CRM Dropdown Item',
    parentfield: 'dropdown_items',
    parenttype: 'FCRM Settings',
    idx: voci.length + 1,
    type: tipo,
    label: '',
    route: '',
    hidden: 0,
    is_standard: 0,
    open_in_new_window: 1,
  })
}

function togli(indice) {
  document.doc.dropdown_items.splice(indice, 1)
  riordina()
}

function updateSettings() {
  document.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
    },
  })
}
</script>
