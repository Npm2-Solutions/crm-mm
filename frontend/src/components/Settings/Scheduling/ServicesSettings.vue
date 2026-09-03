<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-center justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Services') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'What you deliver: duration, who delivers it, which room it needs, and the base price.',
            )
          }}
        </p>
      </div>
      <Button
        variant="solid"
        :label="__('New service')"
        iconLeft="plus"
        @click="openEditor()"
      />
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="services.data?.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="service in services.data"
          :key="service.name"
          class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
          @click="openEditor(service.name)"
        >
          <span
            class="size-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: service.color || '#4C7EFF' }"
          />
          <div class="min-w-0 flex-1">
            <div class="truncate text-p-base-medium text-ink-gray-8">
              {{ service.service_name }}
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">
              {{ describe(service) }}
            </div>
          </div>
          <span class="shrink-0 text-p-sm text-ink-gray-5">
            {{ service.upcoming_count }} {{ __('upcoming') }}
          </span>
          <Badge
            :label="service.enabled ? __('Active') : __('Off')"
            :theme="service.enabled ? 'green' : 'gray'"
            size="sm"
          />
          <Button
            variant="ghost"
            icon="lucide-trash-2"
            @click.stop="remove(service)"
          />
        </div>
      </div>
      <div
        v-else-if="!services.loading"
        class="px-2 text-p-base text-ink-gray-5"
      >
        {{ __('No services yet. Create the first one!') }}
      </div>
    </div>
  </div>

  <Dialog v-model="showEditor" :options="{ title: editorTitle, size: '3xl' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-3 gap-3">
          <FormControl
            v-model="form.service_name"
            type="text"
            :label="__('Name')"
            required
          />
          <FormControl
            v-model="form.category"
            type="text"
            :label="__('Category')"
          />
          <FormControl
            v-model="form.color"
            type="text"
            :label="__('Colour (hex)')"
          />
        </div>
        <FormControl
          v-model="form.description"
          type="textarea"
          :rows="2"
          :label="__('Description')"
        />

        <div class="grid grid-cols-4 gap-3">
          <FormControl
            v-model.number="form.duration"
            type="number"
            min="5"
            :label="__('Duration (min)')"
          />
          <FormControl
            v-model.number="form.slot_interval"
            type="number"
            min="0"
            :label="__('Slot step (min)')"
          />
          <FormControl
            v-model.number="form.buffer_before"
            type="number"
            min="0"
            :label="__('Buffer before')"
          />
          <FormControl
            v-model.number="form.buffer_after"
            type="number"
            min="0"
            :label="__('Buffer after')"
          />
        </div>

        <!-- staffing -->
        <div class="rounded-lg border border-outline-gray-2 p-3">
          <div class="mb-2 text-p-base-medium text-ink-gray-8">
            {{ __('Who delivers it') }}
          </div>
          <div class="grid grid-cols-2 gap-3">
            <FormControl
              v-model="form.staff_selection"
              type="select"
              :label="__('Staffing')"
              :options="staffingOptions"
            />
            <FormControl
              v-if="form.staff_selection === 'Any one'"
              v-model.number="form.staff_count"
              type="number"
              min="1"
              :label="__('Professionals per appointment')"
            />
          </div>
          <p class="mt-1 text-p-xs text-ink-gray-5">{{ staffingHint }}</p>

          <div class="mt-3 flex flex-col gap-2">
            <div
              v-for="(row, i) in form.staff"
              :key="i"
              class="grid grid-cols-[1fr_160px_90px_32px] items-end gap-2"
            >
              <Link
                doctype="User"
                :modelValue="row.user"
                :placeholder="__('Professional')"
                @update:modelValue="(v) => (row.user = v)"
              />
              <FormControl
                v-model="row.role"
                type="text"
                :placeholder="__('Role (optional)')"
              />
              <FormControl
                v-model.number="row.priority"
                type="number"
                :placeholder="__('Priority')"
              />
              <Button
                variant="ghost"
                icon="lucide-trash-2"
                @click="form.staff.splice(i, 1)"
              />
            </div>
            <Button
              variant="ghost"
              size="sm"
              class="self-start"
              :label="__('Add professional')"
              iconLeft="plus"
              @click="form.staff.push({ user: '', role: '', priority: 0 })"
            />
          </div>

          <div
            v-if="form.staff_selection === 'One per role'"
            class="mt-3 flex flex-col gap-2"
          >
            <FormLabel :label="__('Roles needed')" />
            <div
              v-for="(row, i) in form.roles"
              :key="i"
              class="grid grid-cols-[1fr_90px_32px] items-end gap-2"
            >
              <FormControl
                v-model="row.role"
                type="text"
                :placeholder="__('Role')"
              />
              <FormControl
                v-model.number="row.staff_count"
                type="number"
                min="1"
              />
              <Button
                variant="ghost"
                icon="lucide-trash-2"
                @click="form.roles.splice(i, 1)"
              />
            </div>
            <Button
              variant="ghost"
              size="sm"
              class="self-start"
              :label="__('Add role')"
              iconLeft="plus"
              @click="form.roles.push({ role: '', staff_count: 1 })"
            />
          </div>
        </div>

        <!-- participants -->
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model.number="form.min_participants"
            type="number"
            min="1"
            :label="__('Minimum participants')"
          />
          <FormControl
            v-model.number="form.max_participants"
            type="number"
            min="1"
            :label="__('Maximum participants')"
            :description="__('Above 1 it becomes a group session')"
          />
        </div>

        <!-- resources -->
        <div class="flex flex-col gap-2">
          <FormLabel :label="__('Rooms & equipment it needs')" />
          <div
            v-for="(row, i) in form.resources"
            :key="i"
            class="grid grid-cols-[130px_1fr_70px_90px_32px] items-end gap-2"
          >
            <FormControl
              v-model="row.resource_type"
              type="select"
              :options="resourceTypeOptions"
            />
            <FormControl
              v-model="row.resource"
              type="select"
              :options="resourceOptions(row.resource_type)"
            />
            <FormControl v-model.number="row.quantity" type="number" min="1" />
            <label
              class="flex items-center gap-1.5 pb-2 text-p-xs text-ink-gray-7"
            >
              <Switch v-model="row.required" size="sm" /> {{ __('Required') }}
            </label>
            <Button
              variant="ghost"
              icon="lucide-trash-2"
              @click="form.resources.splice(i, 1)"
            />
          </div>
          <Button
            variant="ghost"
            size="sm"
            class="self-start"
            :label="__('Add requirement')"
            iconLeft="plus"
            @click="
              form.resources.push({
                resource_type: 'Room',
                resource: '',
                quantity: 1,
                required: true,
              })
            "
          />
          <p class="text-p-xs text-ink-gray-5">
            {{
              __('Leave the resource empty to take any free one of that type.')
            }}
          </p>
        </div>

        <!-- price & limits -->
        <div class="grid grid-cols-4 gap-3">
          <FormControl
            v-model.number="form.default_price"
            type="number"
            :label="__('Base price')"
          />
          <FormControl
            v-model="form.currency"
            type="text"
            :label="__('Currency')"
          />
          <FormControl
            v-model.number="form.min_notice_hours"
            type="number"
            min="0"
            :label="__('Min notice (h)')"
          />
          <FormControl
            v-model.number="form.max_horizon_days"
            type="number"
            min="1"
            :label="__('Horizon (days)')"
          />
        </div>

        <div class="flex flex-wrap gap-4">
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.enabled" size="sm" /> {{ __('Enabled') }}
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.price_per_participant" size="sm" />
            {{ __('Price is per participant') }}
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.bookable_online" size="sm" />
            {{ __('Bookable online') }}
          </label>
        </div>

        <WeeklyHours
          v-model="form.availability"
          :label="__('When it can be delivered')"
          :hint="__('Empty means any time the team is available.')"
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
import Link from '@/components/Controls/Link.vue'
import WeeklyHours from '@/components/Settings/Scheduling/WeeklyHours.vue'
import {
  createResource,
  Dialog,
  FormControl,
  FormLabel,
  Switch,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const services = createResource({
  url: 'crm.api.appointments.list_services',
  cache: 'crm-services-admin',
  auto: true,
})

const resources = createResource({
  url: 'crm.api.appointments.list_resources',
  cache: 'crm-resources-admin',
  auto: true,
})

const staffingOptions = [
  { label: __('Any one (round robin)'), value: 'Any one' },
  { label: __('All required (collective)'), value: 'All required' },
  { label: __('One per role'), value: 'One per role' },
]

const resourceTypeOptions = [
  { label: __('Any type'), value: '' },
  { label: __('Room'), value: 'Room' },
  { label: __('Equipment'), value: 'Equipment' },
  { label: __('Vehicle'), value: 'Vehicle' },
  { label: __('Other'), value: 'Other' },
]

function resourceOptions(type) {
  return [
    { label: __('Any free one'), value: '' },
    ...(resources.data || [])
      .filter((row) => !type || row.resource_type === type)
      .map((row) => ({ label: row.resource_name, value: row.name })),
  ]
}

const staffingHint = computed(() => {
  if (form.staff_selection === 'All required') {
    return __(
      'Every professional listed below is booked together — two therapists following one client.',
    )
  }
  if (form.staff_selection === 'One per role') {
    return __(
      'One free professional per role is picked, e.g. a therapist plus an assistant.',
    )
  }
  return __('The least busy free professional takes the appointment.')
})

function describe(service) {
  const parts = [`${service.duration} ${__('min')}`]
  parts.push(
    {
      'Any one': __('round robin'),
      'All required': __('collective'),
      'One per role': __('one per role'),
    }[service.staff_selection] || service.staff_selection,
  )
  if (service.max_participants > 1) {
    parts.push(__('up to {0} people').replace('{0}', service.max_participants))
  }
  if (service.default_price) {
    parts.push(`${service.default_price} ${service.currency || ''}`)
  }
  return parts.join(' · ')
}

const showEditor = ref(false)
const saving = ref(false)
const editingName = ref(null)

const emptyForm = () => ({
  service_name: '',
  category: '',
  color: '',
  description: '',
  enabled: true,
  duration: 30,
  slot_interval: 0,
  buffer_before: 0,
  buffer_after: 0,
  min_notice_hours: 0,
  max_horizon_days: 60,
  staff_selection: 'Any one',
  staff_count: 1,
  min_participants: 1,
  max_participants: 1,
  default_price: 0,
  currency: 'EUR',
  price_per_participant: false,
  bookable_online: false,
  staff: [],
  roles: [],
  resources: [],
  availability: [],
})

const form = reactive(emptyForm())

const editorTitle = computed(() =>
  editingName.value ? __('Edit service') : __('New service'),
)

function openEditor(name = null) {
  editingName.value = name
  Object.assign(form, emptyForm())
  if (!name) {
    showEditor.value = true
    return
  }
  createResource({
    url: 'crm.api.appointments.get_service',
    params: { name },
    auto: true,
    onSuccess: (data) => {
      Object.assign(form, data, {
        enabled: Boolean(data.enabled),
        price_per_participant: Boolean(data.price_per_participant),
        bookable_online: Boolean(data.bookable_online),
        staff: (data.staff || []).map((row) => ({
          user: row.user,
          role: row.role || '',
          priority: row.priority || 0,
        })),
        roles: (data.roles || []).map((row) => ({
          role: row.role,
          staff_count: row.staff_count || 1,
        })),
        resources: (data.resources || []).map((row) => ({
          resource_type: row.resource_type || '',
          resource: row.resource || '',
          quantity: row.quantity || 1,
          required: Boolean(row.required),
        })),
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
    url: 'crm.api.appointments.save_service',
    params: { name: editingName.value, service: { ...form } },
    auto: true,
    onSuccess: () => {
      saving.value = false
      showEditor.value = false
      toast.success(__('Service saved'))
      services.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

function remove(service) {
  createResource({
    url: 'crm.api.appointments.delete_service',
    params: { name: service.name },
    auto: true,
    onSuccess: () => services.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to delete')),
  })
}
</script>
