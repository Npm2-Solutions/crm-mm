<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Rooms, machines and vehicles an appointment takes besides the people.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Rooms & Equipment') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Anything an appointment occupies besides people: consulting rooms, machines, vehicles.',
            )
          }}
        </p>
      </div>
      <Button
        variant="solid"
        :label="__('New resource')"
        iconLeft="plus"
        @click="openEditor()"
      />
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div v-for="group in grouped" :key="group.type" class="mb-4">
        <div class="mb-1.5 px-1 text-xs-medium text-ink-gray-5">
          {{ __(group.type) }}
        </div>
        <div
          class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
        >
          <!-- the row opens from its name, a button stretched over the row;
               the bin sits above it: a row that is a button holding another
               button is two controls in one for a screen reader -->
          <div
            v-for="resource in group.rows"
            :key="resource.name"
            class="relative flex items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
          >
            <span
              class="size-2.5 shrink-0 rounded-full"
              :style="{ backgroundColor: resource.color || '#8B8B8B' }"
            />
            <button
              type="button"
              class="min-w-0 flex-1 text-left after:absolute after:inset-0 after:content-[''] focus-visible:outline-none focus-visible:after:ring-2 focus-visible:after:ring-inset focus-visible:after:ring-outline-gray-4"
              @click="openEditor(resource.name)"
            >
              <span class="block truncate text-p-base-medium text-ink-gray-8">
                {{ resource.resource_name }}
              </span>
              <!-- on a phone what limits it goes on under itself: «Nessun
                   limite impos…» at 320 -->
              <span
                class="block truncate text-p-sm text-ink-gray-5 max-md:whitespace-normal"
              >
                {{ describe(resource) }}
              </span>
            </button>
            <Badge
              :label="resource.enabled ? __('Active') : __('Off')"
              :theme="resource.enabled ? 'green' : 'gray'"
              size="sm"
            />
            <Button
              class="relative z-10"
              :aria-label="__('Delete {0}', [resource.resource_name])"
              variant="ghost"
              icon="lucide-trash-2"
              @click="remove(resource)"
            />
          </div>
        </div>
      </div>
      <EmptyState
        v-if="!resources.data?.length && !resources.loading"
        :title="__('No rooms or equipment yet')"
        :text="
          __(
            'Add the first one: the agenda books it with the appointments that need it.',
          )
        "
      />
    </div>
  </div>

  <Dialog v-model="showEditor" :options="{ title: editorTitle, size: '2xl' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.resource_name"
            type="text"
            :label="__('Name')"
            required
          />
          <FormControl
            v-model="form.resource_type"
            type="select"
            :label="__('Type')"
            :options="typeOptions"
          />
        </div>
        <div class="grid grid-cols-3 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model.number="form.capacity"
            type="number"
            inputmode="numeric"
            min="1"
            :label="__('Concurrent appointments')"
            :description="__('1 means exclusive use')"
          />
          <FormControl
            v-model.number="form.seats"
            type="number"
            inputmode="numeric"
            min="0"
            :label="__('Seats')"
            :description="__('0 = no limit')"
          />
          <FormControl
            v-model="form.location"
            type="text"
            :label="__('Location')"
          />
        </div>
        <!-- where it is, where the centre has more than one location (docs/crm/62) -->
        <FormControl
          v-if="piuSedi"
          v-model="form.centre_location"
          type="select"
          :label="__('Centre location')"
          :options="opzioniSede"
          :description="
            __(
              'Empty: in any of them, as equipment that moves from one to another.',
            )
          "
        />
        <div class="grid grid-cols-3 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model.number="form.hourly_rate"
            type="number"
            :label="__('Hourly rate')"
          />
          <CampoValuta v-model="form.currency" :label="__('Currency')" />
        </div>
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <Switch v-model="form.enabled" size="sm" /> {{ __('Enabled') }}
        </label>
        <ColourPicker
          v-model="form.color"
          :label="__('Colour')"
          fallback="#6E6E6E"
        />
        <WeeklyHours
          v-model="form.availability"
          :label="__('When it can be used')"
          :anyTimeLabel="__('Whenever the team works')"
        />
        <FormControl
          v-model="form.description"
          type="textarea"
          :rows="2"
          :label="__('Notes')"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Save')"
        :loading="saving"
        @click="save"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { chiedi } from '@/utils/chiedi'
import { globalStore } from '@/stores/global'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import ColourPicker from '@/components/Settings/Scheduling/ColourPicker.vue'
import WeeklyHours from '@/components/Settings/Scheduling/WeeklyHours.vue'
import CampoValuta from '@/components/Controls/CampoValuta.vue'
import { appLocale } from '@/utils/locale'
import { prezzo } from '@/utils/valute'
import { useSedi } from '@/composables/sedi'
import { nomeDellaSede, opzioniDelleSedi } from '@/utils/sedi'
import { createResource, Dialog, FormControl, Switch, toast } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const { $dialog } = globalStore()

const TYPES = ['Room', 'Equipment', 'Vehicle', 'Other']

const resources = createResource({
  url: 'crm.api.appointments.list_resources',
  cache: 'crm-resources-admin',
  auto: true,
})

const typeOptions = TYPES.map((t) => ({ label: __(t), value: t }))

const grouped = computed(() => {
  const rows = resources.data || []
  return TYPES.map((type) => ({
    type,
    rows: rows.filter((row) => row.resource_type === type),
  })).filter((group) => group.rows.length)
})

// the locations a room may be in (docs/crm/62): nothing where there is one
const { sedi, piuSedi } = useSedi()
const opzioniSede = computed(() =>
  opzioniDelleSedi(sedi.value, __('Any location')).map(({ value, label }) => ({
    value,
    label,
  })),
)

function describe(resource) {
  const parts = []
  if (piuSedi.value && resource.centre_location)
    parts.push(nomeDellaSede(sedi.value, resource.centre_location))
  if (resource.capacity > 1) {
    parts.push(__('{0} at a time', [resource.capacity]))
  }
  if (resource.seats > 1) parts.push(__('{0} seats', [resource.seats]))
  if (resource.location) parts.push(resource.location)
  if (resource.hourly_rate) {
    parts.push(
      __('{0} an hour', [
        prezzo(resource.hourly_rate, resource.currency, appLocale()),
      ]),
    )
  }
  return parts.join(' · ') || __('No limits set')
}

const showEditor = ref(false)
const saving = ref(false)
const editingName = ref(null)

const emptyForm = () => ({
  resource_name: '',
  resource_type: 'Room',
  enabled: true,
  capacity: 1,
  seats: 0,
  location: '',
  centre_location: '',
  hourly_rate: 0,
  currency: 'EUR',
  color: '',
  description: '',
  availability: [],
})

const form = reactive(emptyForm())

const editorTitle = computed(() =>
  editingName.value ? __('Edit resource') : __('New resource'),
)

function openEditor(name = null) {
  editingName.value = name
  Object.assign(form, emptyForm())
  if (!name) {
    showEditor.value = true
    return
  }
  chiedi({
    url: 'crm.api.appointments.get_resource',
    params: { name },
    onSuccess: (data) => {
      Object.assign(form, data, {
        enabled: Boolean(data.enabled),
        availability: data.availability || [],
        centre_location: data.centre_location || '',
      })
      showEditor.value = true
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to load')),
  })
}

function save() {
  saving.value = true
  chiedi({
    url: 'crm.api.appointments.save_resource',
    params: { name: editingName.value, resource: { ...form } },
    onSuccess: () => {
      saving.value = false
      showEditor.value = false
      toast.success(__('Resource saved'))
      resources.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

// a room goes after a yes that names it: one tap on the bin, a finger's width
// from the row that opens it, took it away with nothing to undo
function remove(resource) {
  $dialog({
    title: __('Delete {0}?', [resource.resource_name]),
    message: __(
      'The appointments that use it keep their day and time, without the room. To stop booking it and keep it, switch it off instead.',
    ),
    actions: [
      {
        label: __('Delete the room'),
        variant: 'solid',
        theme: 'red',
        onClick: (chiudi) => {
          chiudi()
          chiedi({
            url: 'crm.api.appointments.delete_resource',
            params: { name: resource.name },
            onSuccess: () => {
              toast.success(__('Deleted'))
              resources.reload()
            },
            onError: (e) =>
              toast.error(e.messages?.[0] || __('Failed to delete')),
          })
        },
      },
    ],
  })
}
</script>
