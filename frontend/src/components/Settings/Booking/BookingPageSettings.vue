<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-center justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Booking page') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'The public page where clients book your services. Each service keeps its own limits.',
            )
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

    <div class="flex flex-1 flex-col gap-6 overflow-y-auto px-2">
      <div
        class="flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-3 py-2"
      >
        <div class="flex min-w-0 flex-col">
          <span class="text-p-base-medium text-ink-gray-7">
            {{ __('Page address') }}
          </span>
          <span class="truncate text-p-sm text-ink-gray-5">{{ pageUrl }}</span>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <Button
            variant="ghost"
            icon="lucide-copy"
            :tooltip="__('Copy link')"
            @click="copy"
          />
          <Button
            variant="ghost"
            icon="lucide-external-link"
            :tooltip="__('Open booking page')"
            :link="pageUrl"
          />
        </div>
      </div>

      <label
        class="flex items-start gap-2.5 rounded-md border border-outline-gray-2 px-3 py-2"
      >
        <Switch
          v-model="form.online_booking_enabled"
          size="sm"
          class="mt-0.5"
        />
        <span class="flex flex-col">
          <span class="text-p-sm-medium text-ink-gray-8">
            {{ __('Online booking open') }}
          </span>
          <span class="text-p-xs text-ink-gray-5">
            {{
              __(
                'Closed, the page tells clients to get in touch. Services are published with "Bookable online" in Agenda → Services.',
              )
            }}
          </span>
        </span>
      </label>

      <section class="flex flex-col gap-3">
        <h3 class="text-p-base-medium text-ink-gray-8">{{ __('Content') }}</h3>
        <FormControl
          v-model="form.booking_page_title"
          type="text"
          :label="__('Page title')"
          :placeholder="__('Book an appointment')"
        />
        <FormControl
          v-model="form.booking_page_intro"
          type="textarea"
          :rows="2"
          :label="__('Intro text')"
        />
      </section>

      <section class="flex flex-col gap-3">
        <h3 class="text-p-base-medium text-ink-gray-8">{{ __('Privacy') }}</h3>
        <FormControl
          v-model="form.privacy_policy_url"
          type="text"
          :label="__('Privacy policy URL')"
          placeholder="https://…/privacy"
        />
        <label
          v-for="rule in checks"
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
          {{ __('Limit across all services') }}
        </h3>
        <FormControl
          v-model.number="form.max_active_per_customer"
          class="w-60"
          type="number"
          min="0"
          :label="__('Upcoming bookings per client')"
          :description="
            __('0 = no limit. Each service can set a stricter one.')
          "
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import { createResource, FormControl, Switch, toast } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const CHECKS = [
  'online_booking_enabled',
  'require_privacy_consent',
  'send_client_confirmation',
  'notify_staff_on_booking',
]
const FIELDS = [
  'booking_page_title',
  'booking_page_intro',
  'privacy_policy_url',
  'max_active_per_customer',
]

const pageUrl = `${window.location.origin}/prenota`
const saving = ref(false)
const form = reactive({
  online_booking_enabled: true,
  require_privacy_consent: true,
  send_client_confirmation: true,
  notify_staff_on_booking: true,
  booking_page_title: '',
  booking_page_intro: '',
  privacy_policy_url: '',
  max_active_per_customer: 0,
})

createResource({
  url: 'crm.api.appointments.get_scheduling_settings',
  auto: true,
  onSuccess: (data) => {
    // a site not yet migrated has no value: keep the permissive default
    CHECKS.forEach((field) => {
      if (data[field] !== undefined && data[field] !== null)
        form[field] = Boolean(data[field])
    })
    FIELDS.forEach((field) => {
      if (data[field] !== undefined && data[field] !== null)
        form[field] = data[field]
    })
  },
})

const checks = computed(() => [
  {
    field: 'require_privacy_consent',
    label: __('Ask for privacy consent'),
    hint: __('A required checkbox with the link to the policy above.'),
  },
  {
    field: 'send_client_confirmation',
    label: __('Email the client'),
    hint: __(
      'Confirmation with calendar file, plus approval, move and cancellation updates.',
    ),
  },
  {
    field: 'notify_staff_on_booking',
    label: __('Email the professional'),
    hint: __('On every new, moved or cancelled online booking.'),
  },
])

async function copy() {
  try {
    await navigator.clipboard.writeText(pageUrl)
    toast.success(__('Copied'))
  } catch {
    toast.error(pageUrl)
  }
}

function save() {
  saving.value = true
  createResource({
    url: 'crm.api.appointments.save_scheduling_settings',
    params: {
      scheduling_settings: {
        ...form,
        ...Object.fromEntries(CHECKS.map((f) => [f, form[f] ? 1 : 0])),
      },
    },
    auto: true,
    onSuccess: () => {
      saving.value = false
      toast.success(__('Booking page saved'))
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}
</script>
