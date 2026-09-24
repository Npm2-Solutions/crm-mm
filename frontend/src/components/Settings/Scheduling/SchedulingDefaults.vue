<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-start justify-between gap-4 px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Studio hours & rules') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __('When the studio is open, and what the agenda refuses to book.')
          }}
        </p>
      </div>
      <Button
        variant="solid"
        :label="__('Save')"
        :loading="saving"
        @click="save"
      />
    </div>

    <div class="flex flex-1 flex-col gap-8 overflow-y-auto px-2 pb-4">
      <!-- 1. opening hours -->
      <section class="flex flex-col gap-3">
        <WeeklyHours
          v-model="form.default_availability"
          :label="__('Opening hours')"
          :anyTimeLabel="__('Always open')"
          :anyTimeHint="__('Nobody is limited by the studio hours.')"
          :hint="
            __('Everyone without their own hours in Team rota works these.')
          "
        />
        <Link
          class="max-w-sm"
          doctype="CRM Holiday List"
          :modelValue="form.default_holiday_list"
          :label="__('Holiday calendar')"
          :placeholder="__('None')"
          @update:modelValue="(v) => (form.default_holiday_list = v)"
        />
      </section>

      <!-- 2. new appointments -->
      <section class="flex flex-col gap-3">
        <h3 class="text-p-base-medium text-ink-gray-8">
          {{ __('New appointments') }}
        </h3>
        <div class="grid grid-cols-3 gap-3">
          <FormControl
            v-model.number="form.default_duration"
            type="number"
            min="5"
            :label="__('Default length (min)')"
          />
          <Link
            doctype="CRM Price List"
            :modelValue="form.default_price_list"
            :label="__('Price list')"
            :placeholder="__('None')"
            @update:modelValue="(v) => (form.default_price_list = v)"
          />
          <FormControl
            v-model="form.timezone"
            type="select"
            :label="__('Time zone')"
            :options="timezoneOptions"
          />
        </div>
      </section>

      <!-- 3. what the agenda refuses -->
      <section
        v-for="group in groups"
        :key="group.title"
        class="flex flex-col gap-2"
      >
        <div class="flex flex-col gap-0.5">
          <h3 class="text-p-base-medium text-ink-gray-8">{{ group.title }}</h3>
          <p v-if="group.hint" class="text-p-sm text-ink-gray-5">
            {{ group.hint }}
          </p>
        </div>
        <div
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <label
            v-for="rule in group.rules"
            :key="rule.field"
            class="flex cursor-pointer items-center justify-between gap-4 px-3 py-2.5 hover:bg-surface-gray-1"
          >
            <span class="flex flex-col">
              <span class="text-p-sm-medium text-ink-gray-8">{{
                rule.label
              }}</span>
              <span class="text-p-xs text-ink-gray-5">{{ rule.hint }}</span>
            </span>
            <Switch v-model="form[rule.field]" size="sm" />
          </label>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import WeeklyHours from '@/components/Settings/Scheduling/WeeklyHours.vue'
import { createResource, FormControl, Switch, toast } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const CHECKS = [
  'enforce_staff_conflicts',
  'enforce_resource_conflicts',
  'enforce_participant_conflicts',
  'enforce_working_hours',
  'allow_override',
  'sync_to_event',
  'check_google_busy',
]

const saving = ref(false)

const emptyForm = () => ({
  timezone: '',
  default_price_list: '',
  default_duration: 30,
  enforce_staff_conflicts: true,
  enforce_resource_conflicts: true,
  enforce_participant_conflicts: true,
  enforce_working_hours: false,
  allow_override: true,
  sync_to_event: true,
  check_google_busy: false,
  default_holiday_list: '',
  default_availability: [],
})

const form = reactive(emptyForm())

const settings = createResource({
  url: 'crm.api.appointments.get_scheduling_settings',
  auto: true,
  onSuccess: (data) => {
    Object.assign(form, emptyForm(), {
      timezone: data.timezone || '',
      default_price_list: data.default_price_list || '',
      default_duration: data.default_duration || 30,
      default_holiday_list: data.default_holiday_list || '',
      default_availability: data.default_availability || [],
    })
    CHECKS.forEach((field) => {
      form[field] = Boolean(data[field])
    })
  },
})

const groups = computed(() => [
  {
    title: __('Double bookings'),
    hint: __(
      'A manager can still force a clash when allowed: it is then written on the appointment.',
    ),
    rules: [
      {
        field: 'enforce_staff_conflicts',
        label: __('A professional in two places at once'),
        hint: __(
          'Counts appointments, online bookings and calendar events, with the pauses.',
        ),
      },
      {
        field: 'enforce_resource_conflicts',
        label: __('A room or machine over capacity'),
        hint: __('Each one holds as many appointments as its capacity.'),
      },
      {
        field: 'enforce_participant_conflicts',
        label: __('A client in two places at once'),
        hint: __('The same person cannot have two overlapping appointments.'),
      },
      {
        field: 'enforce_working_hours',
        label: __('Appointments outside working hours'),
        hint: __(
          'Off by default: an out-of-hours appointment is often on purpose.',
        ),
      },
      {
        field: 'allow_override',
        label: __('Managers can force a clash'),
        hint: __('The clash is recorded on the appointment.'),
      },
    ],
  },
  {
    title: __('Calendar and Google'),
    rules: [
      {
        field: 'sync_to_event',
        label: __('Show appointments in the calendar'),
        hint: __('Also what sends them to Google Calendar.'),
      },
      {
        field: 'check_google_busy',
        label: __('Google Calendar meetings block free slots'),
        hint: __('A bit slower to find free times.'),
      },
    ],
  },
])

// every IANA zone the browser knows, the empty one meaning the site's own
const timezoneOptions = computed(() => {
  let zones
  try {
    zones = Intl.supportedValuesOf('timeZone')
  } catch {
    zones = ['Europe/Rome']
  }
  if (form.timezone && !zones.includes(form.timezone))
    zones.unshift(form.timezone)
  return [
    {
      label: __('Site time zone ({0})', [settings.data?.site_timezone || '—']),
      value: '',
    },
    ...zones.map((zone) => ({ label: zone.replace(/_/g, ' '), value: zone })),
  ]
})

function save() {
  saving.value = true
  createResource({
    url: 'crm.api.appointments.save_scheduling_settings',
    params: { scheduling_settings: { ...form } },
    auto: true,
    onSuccess: () => {
      saving.value = false
      toast.success(__('Studio hours & rules saved'))
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}
</script>
