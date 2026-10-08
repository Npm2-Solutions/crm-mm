<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > The centre > Locations (docs/crm/62): where the centre is. Each
  location with its address - what the people booked read in the confirmation,
  the reminders and their area -, its phone, a map, its opening hours in the
  centre's words and, where it invoices under another company, which. With one
  location nothing changes anywhere: the agenda, the booking page and the
  reception desk name the locations from the second one on.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex min-w-0 flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Locations') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Where the centre is. From the second location on, the agenda, the booking page and the reception desk let you choose one, and every room and shift says where it is.',
            )
          }}
        </p>
      </div>
      <AzioneImpostazioni
        class="shrink-0"
        :label="__('New location')"
        @click="apri()"
      />
    </div>

    <div class="flex flex-1 flex-col gap-3 overflow-y-auto px-2 pb-2">
      <div
        v-if="elenco.length"
        class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
      >
        <button
          v-for="sede in elenco"
          :key="sede.name"
          type="button"
          class="flex w-full items-center gap-3 px-3 py-2.5 text-left hover:bg-surface-gray-1 max-md:min-h-14"
          @click="apri(sede)"
        >
          <span
            class="lucide-map-pin size-4 shrink-0 text-ink-gray-5"
            aria-hidden="true"
          />
          <span class="flex min-w-0 flex-1 flex-col">
            <span class="truncate text-p-base-medium text-ink-gray-8">
              {{ sede.location_name }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{ riga(sede) }}
            </span>
          </span>
          <Badge
            class="shrink-0"
            :label="
              sede.enabled
                ? __('Active', null, 'Location')
                : __('Off', null, 'Location')
            "
            :theme="sede.enabled ? 'green' : 'gray'"
            size="sm"
          />
        </button>
      </div>
      <p
        v-if="elenco.length === 1"
        class="px-1 text-p-sm text-ink-gray-6"
        role="note"
      >
        {{
          __(
            'With one location nothing changes: add the second to choose where in the agenda, the booking page and the reception desk.',
          )
        }}
      </p>
      <EmptyState
        v-if="!elenco.length && !dati.loading"
        :title="__('One centre, one place')"
        :text="
          __(
            'Add your locations if the centre has more than one: each with its address, its rooms and who works there.',
          )
        "
      />
    </div>
  </div>

  <Dialog
    v-model="editor"
    :options="{ title: modifica ? __('Edit location') : __('New location') }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl
          v-model="form.location_name"
          type="text"
          :label="__('Name')"
          :placeholder="__('e.g. Monza location')"
          required
        />
        <FormControl
          v-model="form.address_line"
          type="text"
          :label="__('Street and number')"
          autocomplete="street-address"
        />
        <div class="grid grid-cols-[7rem_1fr_5rem] gap-3 max-md:grid-cols-2">
          <FormControl
            v-model="form.pincode"
            type="text"
            :label="__('Postcode')"
            v-bind="tastiera('cifre')"
            autocomplete="postal-code"
          />
          <FormControl
            v-model="form.city"
            type="text"
            :label="__('City')"
            autocomplete="address-level2"
          />
          <FormControl
            v-model="form.province"
            type="text"
            maxlength="2"
            :label="__('Province')"
            v-bind="tastiera('codice')"
          />
        </div>
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.phone"
            type="tel"
            :label="__('Phone')"
            v-bind="tastiera('telefono')"
          />
          <FormControl
            v-model="form.email"
            type="email"
            :label="__('Email')"
            v-bind="tastiera('email')"
          />
        </div>
        <FormControl
          v-model="form.map_link"
          type="url"
          :label="__('Map link')"
          :description="
            __('The link of the place on a map, for whoever books there.')
          "
          v-bind="tastiera('url')"
        />
        <FormControl
          v-model="form.opening_hours"
          type="textarea"
          :rows="2"
          :label="__('Opening hours')"
          :placeholder="__('e.g. Mon-Fri 8-20, Sat 8-13')"
        />
        <FormControl
          v-if="aziende.length"
          v-model="form.company"
          type="select"
          :label="__('Issuing company')"
          :options="opzioniAziende"
          :description="
            __(
              'Who invoices what is done here. Empty: the centre\'s usual issuing company.',
            )
          "
        />
        <label class="flex items-center gap-2 text-p-base text-ink-gray-7">
          <Switch
            v-model="form.enabled"
            :aria-label="__('Active', null, 'Location')"
          />
          {{ __('Active', null, 'Location') }}
        </label>
        <p v-if="modifica && !form.enabled" class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Switched off, it is offered nowhere: its rooms and shifts keep it for when it is back.',
            )
          }}
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button
          v-if="modifica"
          variant="subtle"
          theme="red"
          icon="lucide-trash-2"
          :aria-label="__('Delete')"
          :loading="eliminando"
          @click="elimina"
        />
        <Button
          class="flex-1"
          variant="solid"
          :label="__('Save')"
          :loading="salvando"
          @click="salva"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import { aggiornaSedi } from '@/composables/sedi'
import { indirizzoDellaSede } from '@/utils/sedi'
import { tastiera } from '@/utils/tastiera'
import {
  Badge,
  Button,
  call,
  createResource,
  Dialog,
  FormControl,
  Switch,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const dati = createResource({
  url: 'crm.api.sedi.list_locations',
  auto: true,
})

const elenco = computed(() => dati.data?.locations || [])
const aziende = computed(() => dati.data?.companies || [])
const opzioniAziende = computed(() => [
  { label: __("The centre's usual company"), value: '' },
  ...aziende.value.map((azienda) => ({
    label: azienda.company_name,
    value: azienda.name,
  })),
])

// a location's line: where it is, how many rooms, who invoices there
function riga(sede) {
  const parti = [indirizzoDellaSede(sede) || __('No address yet')]
  parti.push(
    sede.rooms === 1 ? __('1 room') : __('{0} rooms', [sede.rooms || 0]),
  )
  if (sede.company_name) parti.push(sede.company_name)
  return parti.join(' · ')
}

const editor = ref(false)
const modifica = ref('')
const salvando = ref(false)
const eliminando = ref(false)

const vuoto = () => ({
  location_name: '',
  address_line: '',
  pincode: '',
  city: '',
  province: '',
  phone: '',
  email: '',
  map_link: '',
  opening_hours: '',
  company: '',
  enabled: true,
})
const form = reactive(vuoto())

function apri(sede = null) {
  modifica.value = sede?.name || ''
  Object.assign(form, vuoto())
  if (sede)
    Object.assign(
      form,
      Object.fromEntries(
        Object.keys(vuoto()).map((campo) => [campo, sede[campo] ?? '']),
      ),
      { enabled: Boolean(sede.enabled) },
    )
  editor.value = true
}

async function salva() {
  salvando.value = true
  try {
    const risposta = await call('crm.api.sedi.save_location', {
      name: modifica.value || null,
      location: { ...form, enabled: form.enabled ? 1 : 0 },
    })
    aggiornaSedi(risposta.boot)
    editor.value = false
    toast.success(__('Location saved'))
    dati.reload()
  } catch (e) {
    toast.error(e.messages?.[0] || __('Failed to save'))
  } finally {
    salvando.value = false
  }
}

async function elimina() {
  eliminando.value = true
  try {
    const risposta = await call('crm.api.sedi.delete_location', {
      name: modifica.value,
    })
    aggiornaSedi(risposta.boot)
    editor.value = false
    dati.reload()
  } catch (e) {
    toast.error(e.messages?.[0] || __('Failed to delete'))
  } finally {
    eliminando.value = false
  }
}
</script>
