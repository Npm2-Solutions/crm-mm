<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-center justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
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
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="resource in group.rows"
            :key="resource.name"
            class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
            @click="openEditor(resource.name)"
          >
            <span
              class="size-2.5 shrink-0 rounded-full"
              :style="{ backgroundColor: resource.color || '#8B8B8B' }"
            />
            <div class="min-w-0 flex-1">
              <div class="truncate text-p-base-medium text-ink-gray-8">
                {{ resource.resource_name }}
              </div>
              <div class="truncate text-p-sm text-ink-gray-5">
                {{ describe(resource) }}
              </div>
            </div>
            <Badge
              :label="resource.enabled ? __('Active') : __('Off')"
              :theme="resource.enabled ? 'green' : 'gray'"
              size="sm"
            />
            <Button
              variant="ghost"
              icon="lucide-trash-2"
              @click.stop="remove(resource)"
            />
          </div>
        </div>
      </div>
      <div
        v-if="!resources.data?.length && !resources.loading"
        class="px-2 text-p-base text-ink-gray-5"
      >
        {{ __('No rooms or equipment yet. Add the first one!') }}
      </div>
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
        <div class="grid grid-cols-3 gap-3">
          <FormControl
            v-model.number="form.capacity"
            type="number"
            min="1"
            :label="__('Concurrent appointments')"
            :description="__('1 means exclusive use')"
          />
          <FormControl
            v-model.number="form.seats"
            type="number"
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
        <div class="grid grid-cols-3 gap-3">
          <FormControl
            v-model.number="form.hourly_rate"
            type="number"
            :label="__('Hourly rate')"
          />
          <FormControl
            v-model="form.currency"
            type="text"
            :label="__('Currency')"
          />
          <FormControl
            v-model="form.color"
            type="text"
            :label="__('Colour (hex)')"
          />
        </div>
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <Switch v-model="form.enabled" size="sm" /> {{ __('Enabled') }}
        </label>
        <WeeklyHours
          v-model="form.availability"
          :label="__('When it can be used')"
          :hint="__('Leave empty to make it available whenever the staff is.')"
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
import WeeklyHours from '@/components/Settings/Scheduling/WeeklyHours.vue'
import { createResource, Dialog, FormControl, Switch, toast } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

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

function describe(resource) {
  const parts = []
  if (resource.capacity > 1) {
    parts.push(__('{0} at a time').replace('{0}', resource.capacity))
  }
  if (resource.seats) parts.push(__('{0} seats').replace('{0}', resource.seats))
  if (resource.location) parts.push(resource.location)
  if (resource.hourly_rate) {
    parts.push(`${resource.hourly_rate} ${resource.currency || ''}/h`)
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
  createResource({
    url: 'crm.api.appointments.get_resource',
    params: { name },
    auto: true,
    onSuccess: (data) => {
      Object.assign(form, data, {
        enabled: Boolean(data.enabled),
        availability: data.availability || [],
      })
      showEditor.value = true
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to load')),
  })
}

function save() {
  saving.value = true
  createResource({
    url: 'crm.api.appointments.save_resource',
    params: { name: editingName.value, resource: { ...form } },
    auto: true,
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

function remove(resource) {
  createResource({
    url: 'crm.api.appointments.delete_resource',
    params: { name: resource.name },
    auto: true,
    onSuccess: () => resources.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to delete')),
  })
}
</script>
