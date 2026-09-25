<template>
  <div
    class="flex h-full flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8 text-ink-gray-8"
  >
    <div
      class="flex flex-col items-stretch gap-3 px-2 sm:flex-row sm:items-start sm:justify-between sm:gap-4"
    >
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Services') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'What you deliver and who delivers it. Click a service to edit it, a cell to assign a person or give them their own length, price and online flag.',
            )
          }}
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2 sm:shrink-0 sm:flex-nowrap">
        <FormControl
          v-model="query"
          type="text"
          class="w-full sm:w-44"
          :placeholder="__('Filter services…')"
        />
        <Button
          :label="__('Online booking')"
          icon-left="lucide-globe"
          :tooltip="__('Who clients can book online')"
          @click="activeSettingsPage = 'Online booking'"
        />
        <Button
          variant="solid"
          :label="__('New service')"
          iconLeft="plus"
          @click="openEditor()"
        />
      </div>
    </div>

    <TeamMatrix
      ref="grid"
      :query="query"
      @edit="(service) => openEditor(service.name)"
      @remove="remove"
    />
  </div>

  <Dialog v-model="showEditor" :options="{ title: editorTitle, size: '3xl' }">
    <template #body-content>
      <TabButtons
        v-model="editorTab"
        :buttons="editorTabs"
        class="mb-4"
        data-tabs-scroll
      />
      <div
        class="-mx-1 flex h-[min(540px,62vh)] flex-col gap-4 overflow-y-auto px-1 pb-1"
      >
        <!-- what it is and what it costs -->
        <template v-if="editorTab === 'details'">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
              :placeholder="__('e.g. Massages')"
            />
          </div>
          <ColourPicker v-model="form.color" :label="__('Colour')" />
          <FormControl
            v-model="form.description"
            type="textarea"
            :rows="2"
            :label="__('Description')"
          />
          <div class="grid grid-cols-[1fr_1fr_110px] gap-3">
            <FormControl
              v-model.number="form.duration"
              type="number"
              min="5"
              :label="__('Duration (min)')"
            />
            <FormControl
              v-model.number="form.default_price"
              type="number"
              min="0"
              :label="__('Base price')"
            />
            <FormControl
              v-model="form.currency"
              type="text"
              :label="__('Currency')"
            />
          </div>
          <FormControl
            v-model="form.location"
            type="text"
            :label="__('Location')"
            :placeholder="__('e.g. Via Roma 1, Milano — or Online')"
          />
          <div class="flex flex-wrap gap-4">
            <label class="flex items-center gap-2 text-sm text-ink-gray-7">
              <Switch v-model="form.enabled" size="sm" /> {{ __('Enabled') }}
            </label>
            <label class="flex items-center gap-2 text-sm text-ink-gray-7">
              <Switch v-model="form.price_per_participant" size="sm" />
              {{ __('Price is per participant') }}
            </label>
          </div>
          <!-- The website face of this service. The card itself (image, descriptions,
             button) is edited in Site → Showcase, so there is one place to get it
             right; the switch lives here because this is where you are when you
             decide a service should be public. -->
          <div
            v-if="editingName"
            class="flex items-center justify-between rounded-lg border border-outline-gray-2 px-3 py-2.5"
          >
            <div class="flex flex-col">
              <span class="text-p-base-medium text-ink-gray-8">
                {{ __('Publish on the website') }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{
                  publishedOnWebsite
                    ? __(
                        'Visible on the site. Edit its card under Site → Showcase.',
                      )
                    : __('Not on the site yet.')
                }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <Button
                v-if="publishedOnWebsite"
                variant="ghost"
                :label="__('Edit card')"
                @click="openShowcase"
              />
              <Switch
                size="sm"
                :modelValue="publishedOnWebsite"
                @update:modelValue="toggleWebsite"
              />
            </div>
          </div>
        </template>

        <!-- who delivers it: the service's row of the grid; own settings are set there -->
        <template v-else-if="editorTab === 'team'">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
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

          <div class="flex flex-col gap-2">
            <div
              v-for="(row, i) in form.staff"
              :key="i"
              class="flex items-center gap-2"
            >
              <PersonPicker
                class="flex-1"
                :modelValue="row.user"
                :placeholder="__('Professional')"
                :exclude="form.staff.map((r) => r.user)"
                @update:modelValue="(v) => (row.user = v)"
              />
              <FormControl
                v-if="form.staff_selection === 'One per role'"
                v-model="row.role"
                class="w-40"
                type="text"
                :placeholder="__('Role')"
              />
              <span
                v-if="ownSettings(row)"
                class="shrink-0 rounded bg-surface-blue-2 px-2 py-1 text-p-xs text-ink-blue-8"
                :title="__('Their own settings, from the grid')"
              >
                {{ ownSettings(row) }}
              </span>
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
              @click="addProfessional"
            />
          </div>
          <p class="text-p-sm text-ink-gray-5">
            {{
              __(
                "The same people as this service's row in the grid. Click their cell there for their own length, price, priority or online flag.",
              )
            }}
          </p>
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
        </template>

        <!-- what it occupies -->
        <template v-else-if="editorTab === 'space'">
          <!-- participants -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
              <FormControl
                v-model.number="row.quantity"
                type="number"
                min="1"
              />
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
                __(
                  'Leave the resource empty to take any free one of that type.',
                )
              }}
            </p>
          </div>
        </template>

        <!-- when -->
        <template v-else-if="editorTab === 'hours'">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
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
          <WeeklyHours
            v-model="form.availability"
            :label="__('When it can be delivered')"
            :anyTimeLabel="__('Whenever the team works')"
            :anyTimeHint="
              __('Bookable in any free slot of the people who deliver it.')
            "
            :hint="
              __(
                'e.g. first visits only on Tuesday morning. Still within each person\'s own hours.',
              )
            "
          />
          <p class="text-p-xs text-ink-gray-5">
            {{ __("Each person's own hours and days off: Team rota.") }}
          </p>
        </template>

        <!-- online -->
        <template v-else>
          <label
            class="flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 px-3 py-2.5"
          >
            <span class="flex flex-col">
              <span class="text-p-base-medium text-ink-gray-8">
                {{ __('Bookable online') }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{
                  __('Who clients can book for it: Booking → Online booking.')
                }}
              </span>
            </span>
            <Switch v-model="form.bookable_online" size="sm" />
          </label>
          <OnlineBookingPanel
            v-if="form.bookable_online"
            v-model="form"
            :serviceName="editingName || ''"
          />
        </template>
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
import ColourPicker from '@/components/Settings/Scheduling/ColourPicker.vue'
import PersonPicker from '@/components/Settings/Scheduling/PersonPicker.vue'
import WeeklyHours from '@/components/Settings/Scheduling/WeeklyHours.vue'
import { globalStore } from '@/stores/global'
import TeamMatrix from '@/components/Settings/Scheduling/TeamMatrix.vue'
import OnlineBookingPanel from '@/components/Settings/Scheduling/OnlineBookingPanel.vue'
import {
  INHERITED_RULES,
  ONLINE_DEFAULTS,
  onlineFieldsFrom,
} from '@/utils/onlineBooking'
import {
  call,
  createResource,
  Dialog,
  FormControl,
  FormLabel,
  Switch,
  TabButtons,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { activeSettingsPage, showSettings } from '@/composables/settings'

const router = useRouter()

const { $dialog } = globalStore()

const grid = ref(null)
const query = ref('')

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

const showEditor = ref(false)
const editorTab = ref('details')
const editorTabs = [
  { label: __('Details'), value: 'details' },
  { label: __('Team'), value: 'team' },
  { label: __('Rooms & group'), value: 'space' },
  { label: __('Hours'), value: 'hours' },
  { label: __('Online'), value: 'online' },
]

// one person's own settings, shown here, edited from the grid's cell
function ownSettings(row) {
  const parts = []
  if (row.duration) parts.push(`${row.duration}'`)
  if (row.custom_price) parts.push(`${row.price} ${form.currency || ''}`.trim())
  if (!row.bookable_online) parts.push(__('not online'))
  return parts.join(' · ')
}

function addProfessional() {
  form.staff.push({
    user: '',
    role: '',
    priority: 0,
    duration: null,
    price: null,
    custom_price: false,
    bookable_online: true,
  })
}

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
  location: '',
  ...ONLINE_DEFAULTS,
  online_overrides: [],
  online_defaults: {},
  hide_from_menu: false,
  staff: [],
  roles: [],
  resources: [],
  availability: [],
})

const form = reactive(emptyForm())

// Published state is written straight through, not carried in `form`: the rest of this
// dialog is a draft until Save, and a publish switch that silently waited for Save would
// be a lie.
const publishedOnWebsite = ref(false)

async function toggleWebsite(value) {
  const previous = publishedOnWebsite.value
  publishedOnWebsite.value = value
  try {
    await call('crm.api.site.set_showcase_published', {
      doctype: 'CRM Service',
      name: editingName.value,
      published: value ? 1 : 0,
    })
    grid.value?.reload()
  } catch (error) {
    publishedOnWebsite.value = previous
    toast.error(error.messages?.[0] || __('Could not change it'))
  }
}

function openShowcase() {
  showEditor.value = false
  showSettings.value = false
  router.push({ name: 'Website' })
}

const editorTitle = computed(() =>
  editingName.value ? __('Edit service') : __('New service'),
)

function openEditor(name = null) {
  editingName.value = name
  editorTab.value = 'details'
  publishedOnWebsite.value = false
  Object.assign(form, emptyForm())
  if (!name) {
    // a new service follows the booking-page defaults: show them in its panel
    call('crm.api.appointments.get_scheduling_settings')
      .then((settings) => {
        form.online_defaults = Object.fromEntries(
          INHERITED_RULES.map((rule) => [
            rule.key,
            settings[`default_${rule.key}`],
          ]),
        )
      })
      .catch(() => {})
    showEditor.value = true
    return
  }
  createResource({
    url: 'crm.api.appointments.get_service',
    params: { name },
    auto: true,
    onSuccess: (data) => {
      Object.assign(form, data, onlineFieldsFrom(data), {
        enabled: Boolean(data.enabled),
        price_per_participant: Boolean(data.price_per_participant),
        bookable_online: Boolean(data.bookable_online),
        staff: (data.staff || []).map((row) => ({
          user: row.user,
          role: row.role || '',
          priority: row.priority || 0,
          duration: row.duration || null,
          custom_price: Boolean(row.custom_price),
          price: row.custom_price ? row.price : null,
          bookable_online: row.bookable_online !== 0,
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
      publishedOnWebsite.value = Boolean(data.publish_on_website)
      showEditor.value = true
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to load')),
  })
}

function save() {
  saving.value = true
  createResource({
    url: 'crm.api.appointments.save_service',
    params: {
      name: editingName.value,
      service: {
        ...form,
        staff: form.staff.map((row) => ({
          ...row,
          duration: Number(row.duration) || 0,
          custom_price: row.custom_price ? 1 : 0,
          price: Number(row.price) || 0,
          bookable_online: row.bookable_online ? 1 : 0,
        })),
        hide_from_menu: form.hide_from_menu ? 1 : 0,
      },
    },
    auto: true,
    onSuccess: () => {
      saving.value = false
      showEditor.value = false
      toast.success(__('Service saved'))
      grid.value?.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

function remove(service) {
  $dialog({
    title: __('Delete {0}?', [service.service_name]),
    message: __(
      'This cannot be undone. A service with appointments cannot be deleted: turn it off instead.',
    ),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        onClick: (close) => {
          close()
          createResource({
            url: 'crm.api.appointments.delete_service',
            params: { name: service.name },
            auto: true,
            onSuccess: () => grid.value?.reload(),
            onError: (e) =>
              toast.error(e.messages?.[0] || __('Failed to delete')),
          })
        },
      },
    ],
  })
}
</script>
