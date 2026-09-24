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
              'One page for every booking. Links narrow it to a category, a service or a professional — no calendars to multiply.',
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
      <!-- open / closed -->
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
                'Services appear when marked "Bookable online" (Agenda → Services); who delivers them online is set in Who does what.',
              )
            }}
          </span>
        </span>
      </label>

      <!-- link builder -->
      <section
        class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-3"
      >
        <h3 class="text-p-base-medium text-ink-gray-8">
          {{ __('Links, QR code and embed') }}
        </h3>
        <div class="grid grid-cols-3 gap-3">
          <FormControl
            v-model="link.category"
            type="select"
            :label="__('Category')"
            :options="categoryOptions"
            :disabled="Boolean(link.service)"
          />
          <FormControl
            v-model="link.service"
            type="select"
            :label="__('Service')"
            :options="serviceOptions"
          />
          <FormControl
            v-model="link.staff"
            type="select"
            :label="__('Professional')"
            :options="staffOptions"
          />
        </div>
        <div class="grid grid-cols-3 gap-3">
          <FormControl
            v-model="link.utm_source"
            type="text"
            :label="__('Campaign source (utm_source)')"
            :placeholder="__('e.g. instagram')"
          />
          <FormControl
            v-model="link.utm_campaign"
            type="text"
            :label="__('Campaign (utm_campaign)')"
          />
          <FormControl
            v-model.number="link.height"
            type="number"
            min="400"
            :label="__('Embed height (px)')"
          />
        </div>
        <div class="flex gap-4">
          <div class="flex min-w-0 flex-1 flex-col gap-2">
            <CopyRow :label="__('Link')" :value="linkUrl" />
            <CopyRow
              :label="__('Code to embed in a website')"
              :value="snippet"
            />
            <div class="flex gap-2">
              <Button
                icon-left="external-link"
                :label="__('Open')"
                :link="linkUrl"
              />
              <Button
                icon-left="download"
                :label="__('Download QR')"
                :disabled="!qr"
                @click="downloadQr"
              />
            </div>
          </div>
          <img
            v-if="qr"
            :src="qr"
            :alt="__('QR code')"
            class="size-32 shrink-0 rounded border border-outline-gray-2 bg-surface-white p-1"
          />
        </div>
      </section>

      <!-- defaults every service inherits -->
      <section class="flex flex-col gap-3">
        <div class="flex flex-col gap-1">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Default online rules') }}
          </h3>
          <p class="text-p-xs text-ink-gray-5">
            {{
              __(
                'Every service follows these unless it customises a rule in its online panel. Next to each: how many services follow it.',
              )
            }}
          </p>
        </div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-3">
          <RuleField
            v-for="item in DEFAULT_RULES"
            :key="item.key"
            :rule="item"
            :summary="summary.data?.[item.service]"
          >
            <Switch
              v-if="item.type === 'check'"
              v-model="form[item.key]"
              size="sm"
            />
            <FormControl
              v-else-if="item.type === 'select'"
              v-model="form[item.key]"
              type="select"
              :options="item.options()"
            />
            <FormControl
              v-else
              v-model="form[item.key]"
              :type="item.type"
              min="0"
            />
          </RuleField>
        </div>
      </section>

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
        <h3 class="text-p-base-medium text-ink-gray-8">
          {{ __('Privacy and notifications') }}
        </h3>
        <FormControl
          v-model="form.privacy_policy_url"
          type="text"
          :label="__('Privacy policy URL')"
          placeholder="https://…/privacy"
        />
        <label
          v-for="check in checks"
          :key="check.field"
          class="flex items-start gap-2.5 rounded-md border border-outline-gray-2 px-3 py-2"
        >
          <Switch v-model="form[check.field]" size="sm" class="mt-0.5" />
          <span class="flex flex-col">
            <span class="text-p-sm-medium text-ink-gray-8">{{
              check.label
            }}</span>
            <span class="text-p-xs text-ink-gray-5">{{ check.hint }}</span>
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
            __('0 = no limit. The stricter of this and a service limit wins.')
          "
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import CopyRow from '@/components/Settings/Booking/CopyRow.vue'
import { buildBookingLink, embedSnippet } from '@/utils/onlineBooking'
import { createResource, FormControl, Switch, toast } from 'frappe-ui'
import QRCode from 'qrcode'
import { computed, defineComponent, h, reactive, ref, watch } from 'vue'

// the rule on the settings page ↔ the service field that inherits it
const DEFAULT_RULES = [
  {
    key: 'default_min_notice_hours',
    service: 'min_notice_hours',
    type: 'number',
    label: () => __('Minimum notice (hours)'),
  },
  {
    key: 'default_max_horizon_days',
    service: 'max_horizon_days',
    type: 'number',
    label: () => __('Booking horizon (days)'),
  },
  {
    key: 'default_online_slot_interval',
    service: 'online_slot_interval',
    type: 'number',
    label: () => __('Online start times every (min, 0 = service step)'),
  },
  {
    key: 'default_same_day_cutoff',
    service: 'same_day_cutoff',
    type: 'time',
    label: () => __('Same-day bookings until'),
  },
  {
    key: 'default_online_confirmation',
    service: 'online_confirmation',
    type: 'select',
    label: () => __('Confirmation'),
    options: () => [
      { label: __('Automatic'), value: 'Automatic' },
      { label: __('Manual approval'), value: 'Manual approval' },
    ],
  },
  {
    key: 'default_require_phone',
    service: 'require_phone',
    type: 'check',
    label: () => __('Phone required'),
  },
  {
    key: 'default_allow_online_cancel',
    service: 'allow_online_cancel',
    type: 'check',
    label: () => __('Client can cancel online'),
  },
  {
    key: 'default_cancel_notice_hours',
    service: 'cancel_notice_hours',
    type: 'number',
    label: () => __('Cancel up to (hours before)'),
  },
  {
    key: 'default_allow_online_reschedule',
    service: 'allow_online_reschedule',
    type: 'check',
    label: () => __('Client can move online'),
  },
  {
    key: 'default_reschedule_notice_hours',
    service: 'reschedule_notice_hours',
    type: 'number',
    label: () => __('Move up to (hours before)'),
  },
  {
    key: 'default_max_reschedules',
    service: 'max_reschedules',
    type: 'number',
    label: () => __('Max moves (0 = any)'),
  },
  {
    key: 'default_max_per_customer_per_day',
    service: 'max_per_customer_per_day',
    type: 'number',
    label: () => __('Max per client per day (0 = any)'),
  },
]

const RuleField = defineComponent({
  props: {
    rule: { type: Object, required: true },
    summary: { type: Object, default: null },
  },
  setup(props, { slots }) {
    return () => {
      const s = props.summary
      const hint = s
        ? s.own.length
          ? __('{0} services follow it · own value in: {1}', [
              s.inherit,
              s.own.join(', '),
            ])
          : __('{0} services follow it', [s.inherit])
        : ''
      return h('div', { class: 'flex flex-col gap-1' }, [
        h('div', { class: 'flex items-center justify-between gap-2' }, [
          h('span', { class: 'text-xs text-ink-gray-5' }, props.rule.label()),
          props.rule.type === 'check' ? slots.default?.() : null,
        ]),
        props.rule.type === 'check' ? null : slots.default?.(),
        hint ? h('span', { class: 'text-p-xs text-ink-gray-4' }, hint) : null,
      ])
    }
  },
})

const CHECKS = [
  'online_booking_enabled',
  'require_privacy_consent',
  'send_client_confirmation',
  'notify_staff_on_booking',
  'default_require_phone',
  'default_allow_online_cancel',
  'default_allow_online_reschedule',
]
const FIELDS = [
  'booking_page_title',
  'booking_page_intro',
  'privacy_policy_url',
  'max_active_per_customer',
  'default_min_notice_hours',
  'default_max_horizon_days',
  'default_online_slot_interval',
  'default_same_day_cutoff',
  'default_online_confirmation',
  'default_cancel_notice_hours',
  'default_reschedule_notice_hours',
  'default_max_reschedules',
  'default_max_per_customer_per_day',
]

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
  default_min_notice_hours: 2,
  default_max_horizon_days: 60,
  default_online_slot_interval: 0,
  default_same_day_cutoff: '',
  default_online_confirmation: 'Automatic',
  default_require_phone: true,
  default_allow_online_cancel: true,
  default_cancel_notice_hours: 24,
  default_allow_online_reschedule: true,
  default_reschedule_notice_hours: 24,
  default_max_reschedules: 2,
  default_max_per_customer_per_day: 0,
})

createResource({
  url: 'crm.api.appointments.get_scheduling_settings',
  auto: true,
  onSuccess: (data) => {
    // a site not yet migrated has no value: keep the defaults above
    CHECKS.forEach((field) => {
      if (data[field] !== undefined && data[field] !== null)
        form[field] = Boolean(data[field])
    })
    FIELDS.forEach((field) => {
      if (data[field] !== undefined && data[field] !== null)
        form[field] = field.endsWith('cutoff')
          ? String(data[field]).slice(0, 5)
          : data[field]
    })
  },
})

const summary = createResource({
  url: 'crm.api.booking_admin.get_inheritance_summary',
  auto: true,
})

// -- link builder -------------------------------------------------------------

const catalog = createResource({
  url: 'crm.api.service_booking.get_catalog',
  params: { include_hidden: 1 },
  auto: true,
})

const link = reactive({
  category: '',
  service: '',
  staff: '',
  utm_source: '',
  utm_campaign: '',
  height: 820,
})

const categoryOptions = computed(() => [
  { label: __('All'), value: '' },
  ...(catalog.data?.categories || []).map((c) => ({ label: c, value: c })),
])
const serviceOptions = computed(() => [
  { label: __('Any (menu)'), value: '' },
  ...(catalog.data?.services || [])
    .filter((s) => !link.category || s.category === link.category)
    .map((s) => ({ label: s.name, value: s.id })),
])
const staffOptions = computed(() => [
  { label: __('Anyone'), value: '' },
  ...(catalog.data?.people || [])
    .filter((p) => !link.service || p.services.includes(link.service))
    .map((p) => ({ label: p.name, value: p.id })),
])

const linkUrl = computed(() =>
  buildBookingLink(window.location.origin, {
    category: link.category,
    service: link.service,
    staff: link.staff,
    utm: { source: link.utm_source, campaign: link.utm_campaign },
  }),
)
const snippet = computed(() => embedSnippet(linkUrl.value, link.height || 820))

const qr = ref('')
watch(
  linkUrl,
  async (url) => {
    try {
      qr.value = await QRCode.toDataURL(url, { margin: 1, width: 512 })
    } catch {
      qr.value = ''
    }
  },
  { immediate: true },
)

function downloadQr() {
  const a = document.createElement('a')
  a.href = qr.value
  a.download = 'prenota-qr.png'
  a.click()
}

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
      summary.reload()
      catalog.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}
</script>
