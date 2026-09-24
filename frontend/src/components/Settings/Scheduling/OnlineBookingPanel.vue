<template>
  <div class="flex flex-col gap-4 rounded-lg border border-outline-gray-2 p-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex flex-col">
        <span class="text-p-base-medium text-ink-gray-8">
          {{ __('Online booking') }}
        </span>
        <span class="text-p-sm text-ink-gray-5">
          {{
            summary.length
              ? summary.join(' · ')
              : __('Clients book it on the booking page, with the rules below.')
          }}
        </span>
      </div>
      <div v-if="link" class="flex items-center gap-1">
        <Button
          variant="ghost"
          icon="lucide-copy"
          :tooltip="__('Copy booking link')"
          @click="copyLink"
        />
        <Button
          variant="ghost"
          icon="lucide-external-link"
          :tooltip="__('Open booking page')"
          :link="link"
        />
      </div>
    </div>

    <div
      v-if="problems.length"
      class="rounded bg-surface-red-1 px-3 py-2 text-p-sm text-ink-red-4"
    >
      <div v-for="problem in problems" :key="problem">{{ problem }}</div>
    </div>

    <!-- only this service -->
    <div class="flex flex-wrap gap-4">
      <label class="flex items-center gap-2 text-sm text-ink-gray-7">
        <Switch v-model="form.allow_staff_choice" size="sm" />
        {{ __('Client picks the professional') }}
      </label>
      <label class="flex items-center gap-2 text-sm text-ink-gray-7">
        <Switch v-model="form.show_price_online" size="sm" />
        {{ __('Show the price') }}
      </label>
      <label class="flex items-center gap-2 text-sm text-ink-gray-7">
        <Switch v-model="form.hide_from_menu" size="sm" />
        {{ __('Only via its direct link') }}
      </label>
      <FormControl
        v-if="form.max_participants > 1"
        v-model.number="form.online_max_participants"
        class="w-40"
        type="number"
        min="1"
        :max="form.max_participants"
        :label="__('Seats per booking')"
      />
    </div>

    <!-- inherited rules -->
    <div>
      <div class="mb-1 text-p-sm-medium text-ink-gray-6">
        {{ __('Rules') }}
      </div>
      <p class="mb-2 text-p-xs text-ink-gray-5">
        {{
          __(
            'Grey values come from Booking page defaults and follow them. Customise a rule to give this service its own value.',
          )
        }}
      </p>
      <div
        class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-2"
      >
        <div
          v-for="rule in INHERITED_RULES"
          :key="rule.key"
          class="grid grid-cols-[1fr_180px_120px] items-center gap-3 px-3 py-1.5"
        >
          <span class="text-p-sm text-ink-gray-7">{{ __(rule.label) }}</span>
          <div>
            <template v-if="isCustomised(form, rule.key)">
              <Switch
                v-if="rule.type === 'check'"
                v-model="form[rule.key]"
                size="sm"
              />
              <FormControl
                v-else-if="rule.type === 'select'"
                v-model="form[rule.key]"
                type="select"
                :options="confirmationOptions"
              />
              <FormControl
                v-else-if="rule.type === 'time'"
                v-model="form[rule.key]"
                type="time"
              />
              <FormControl
                v-else
                v-model.number="form[rule.key]"
                type="number"
                min="0"
              />
            </template>
            <span v-else class="text-p-sm text-ink-gray-5">
              {{ showValue(rule, inheritedValue(form, rule.key)) }}
            </span>
          </div>
          <Button
            v-if="isCustomised(form, rule.key)"
            variant="ghost"
            size="sm"
            :label="__('Use default')"
            @click="setCustomised(form, rule.key, false)"
          />
          <Button
            v-else
            variant="subtle"
            size="sm"
            :label="__('Customise')"
            @click="setCustomised(form, rule.key, true)"
          />
        </div>
      </div>
    </div>

    <!-- when -->
    <div class="grid grid-cols-2 gap-3">
      <FormControl
        v-model="form.booking_opens_on"
        type="date"
        :label="__('Bookable from')"
      />
      <FormControl
        v-model="form.booking_closes_on"
        type="date"
        :label="__('Bookable until')"
      />
    </div>

    <!-- capacity -->
    <div>
      <div class="mb-2 text-p-sm-medium text-ink-gray-6">
        {{ __('Capacity of this service') }}
      </div>
      <div class="grid grid-cols-3 gap-3">
        <FormControl
          v-model.number="form.max_bookings_per_day"
          type="number"
          min="0"
          :label="__('Max per day')"
        />
        <FormControl
          v-model.number="form.max_bookings_per_week"
          type="number"
          min="0"
          :label="__('Max per week')"
        />
        <FormControl
          v-model.number="form.max_concurrent"
          type="number"
          min="0"
          :label="__('Max at the same time')"
        />
      </div>
    </div>

    <!-- clients -->
    <div>
      <div class="mb-2 text-p-sm-medium text-ink-gray-6">
        {{ __('Clients') }}
      </div>
      <div class="grid grid-cols-3 gap-3">
        <FormControl
          v-model="form.customer_eligibility"
          type="select"
          :label="__('Who can book')"
          :options="[
            { label: __('Everyone'), value: 'Everyone' },
            { label: __('New clients only'), value: 'New customers only' },
            {
              label: __('Returning clients only'),
              value: 'Returning customers only',
            },
          ]"
        />
        <FormControl
          v-model.number="form.max_active_per_customer"
          type="number"
          min="0"
          :label="__('Upcoming per client')"
        />
        <FormControl
          v-model.number="form.min_days_between"
          type="number"
          min="0"
          :label="__('Days between visits')"
        />
      </div>
    </div>

    <!-- booking form -->
    <div>
      <div class="mb-2 text-p-sm-medium text-ink-gray-6">
        {{ __('Booking form') }}
      </div>
      <div class="grid grid-cols-2 gap-3">
        <FormControl
          v-model="form.online_question"
          type="text"
          :label="__('Question for the client')"
          :placeholder="__('e.g. Reason for the visit')"
        />
        <FormControl
          v-model="form.booking_instructions"
          type="text"
          :label="__('Instructions after booking')"
          :placeholder="__('e.g. Bring previous reports')"
        />
      </div>
      <label class="mt-2 flex items-center gap-2 text-sm text-ink-gray-7">
        <Switch v-model="form.require_notes" size="sm" />
        {{ __('Answer required') }}
      </label>
    </div>
  </div>
</template>

<script setup>
import {
  bookingLink,
  describeOnlineLimits,
  inheritedValue,
  INHERITED_RULES,
  isCustomised,
  onlineProblems,
  setCustomised,
} from '@/utils/onlineBooking'
import { FormControl, Switch, toast } from 'frappe-ui'
import { computed } from 'vue'

const form = defineModel({ type: Object, required: true })
const props = defineProps({
  serviceName: { type: String, default: '' },
})

const confirmationOptions = [
  { label: __('Automatic'), value: 'Automatic' },
  { label: __('Manual approval'), value: 'Manual approval' },
]

function showValue(rule, value) {
  if (rule.type === 'check') return value ? __('Yes') : __('No')
  if (rule.type === 'select') return __(value || 'Automatic')
  if (value === '' || value === null || value === undefined) return '—'
  return String(value)
}

const translate = (text, args) => __(text, args)
const summary = computed(() => describeOnlineLimits(form.value, translate))
const problems = computed(() => onlineProblems(form.value, translate))
const link = computed(() =>
  props.serviceName
    ? bookingLink(window.location.origin, {
        name: props.serviceName,
        website_slug: form.value.website_slug,
      })
    : '',
)

async function copyLink() {
  try {
    await navigator.clipboard.writeText(link.value)
    toast.success(__('Booking link copied'))
  } catch {
    toast.error(link.value)
  }
}
</script>
