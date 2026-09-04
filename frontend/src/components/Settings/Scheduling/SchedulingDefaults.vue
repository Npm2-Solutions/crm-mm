<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-center justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Scheduling') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Defaults and conflict rules for the whole agenda.') }}
        </p>
      </div>
      <Button
        variant="solid"
        :label="__('Save')"
        :loading="saving"
        @click="save"
      />
    </div>

    <div class="flex flex-1 flex-col gap-6 overflow-y-auto px-2">
      <section class="flex flex-col gap-3">
        <h3 class="text-p-base-medium text-ink-gray-8">{{ __('Defaults') }}</h3>
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.timezone"
            type="text"
            :label="__('Scheduling timezone')"
            :placeholder="settings.data?.timezone || 'Europe/Rome'"
            :description="
              __(
                'IANA name the weekly hours are read in. Empty = site timezone.',
              )
            "
          />
          <Link
            doctype="CRM Price List"
            :modelValue="form.default_price_list"
            :label="__('Default price list')"
            @update:modelValue="(v) => (form.default_price_list = v)"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model.number="form.default_duration"
            type="number"
            min="5"
            :label="__('Default duration (min)')"
          />
          <FormControl
            v-model.number="form.cancellation_notice_hours"
            type="number"
            min="0"
            :label="__('Cancellation notice (h)')"
          />
        </div>
      </section>

      <section class="flex flex-col gap-2">
        <h3 class="text-p-base-medium text-ink-gray-8">
          {{ __('Conflict rules') }}
        </h3>
        <p class="text-p-xs text-ink-gray-5">
          {{
            __(
              'A blocked appointment can still be forced by a manager: the clash is then written on the record instead of disappearing.',
            )
          }}
        </p>
        <label
          v-for="rule in rules"
          :key="rule.field"
          class="flex items-start gap-2.5 rounded-md border border-outline-gray-2 px-3 py-2"
        >
          <Switch v-model="form[rule.field]" size="sm" class="mt-0.5" />
          <span class="flex flex-col">
            <span class="text-p-sm-medium text-ink-gray-8">{{
              rule.label
            }}</span>
            <span class="text-p-xs text-ink-gray-5">{{ rule.hint }}</span>
          </span>
        </label>
      </section>

      <section class="flex flex-col gap-3">
        <h3 class="text-p-base-medium text-ink-gray-8">
          {{ __('Fallback working hours') }}
        </h3>
        <p class="text-p-xs text-ink-gray-5">
          {{ __('Used for professionals without their own schedule.') }}
        </p>
        <Link
          doctype="CRM Holiday List"
          :modelValue="form.default_holiday_list"
          :label="__('Holiday list')"
          @update:modelValue="(v) => (form.default_holiday_list = v)"
        />
        <WeeklyHours
          v-model="form.default_availability"
          :label="__('Weekly hours')"
        />
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
  cancellation_notice_hours: 0,
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
      cancellation_notice_hours: data.cancellation_notice_hours || 0,
      default_holiday_list: data.default_holiday_list || '',
      default_availability: data.default_availability || [],
    })
    CHECKS.forEach((field) => {
      form[field] = Boolean(data[field])
    })
  },
})

const rules = computed(() => [
  {
    field: 'enforce_staff_conflicts',
    label: __('Block double-booked professionals'),
    hint: __(
      'Counts appointments, public bookings and calendar events, plus buffers.',
    ),
  },
  {
    field: 'enforce_resource_conflicts',
    label: __('Block over-booked rooms & equipment'),
    hint: __('Respects each resource capacity, not just "busy or free".'),
  },
  {
    field: 'enforce_participant_conflicts',
    label: __('Block double-booked clients'),
    hint: __('The same lead or contact cannot be in two places at once.'),
  },
  {
    field: 'enforce_working_hours',
    label: __('Block appointments outside working hours'),
    hint: __(
      'Off by default: an out-of-hours appointment is often deliberate.',
    ),
  },
  {
    field: 'allow_override',
    label: __('Let managers force a conflicting appointment'),
    hint: __('The conflict is recorded on the appointment.'),
  },
  {
    field: 'sync_to_event',
    label: __('Mirror appointments to the calendar Event doctype'),
    hint: __('Keeps them in the classic calendar and in Google Calendar sync.'),
  },
  {
    field: 'check_google_busy',
    label: __('Check Google Calendar busy blocks'),
    hint: __('Slower, but external meetings then block free slots too.'),
  },
])

function save() {
  saving.value = true
  createResource({
    url: 'crm.api.appointments.save_scheduling_settings',
    params: { scheduling_settings: { ...form } },
    auto: true,
    onSuccess: () => {
      saving.value = false
      toast.success(__('Scheduling settings saved'))
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}
</script>
