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
              : __(
                  'Clients book it on the public page, within the limits below.',
                )
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

    <!-- how it is booked -->
    <div class="grid grid-cols-3 gap-3">
      <FormControl
        v-model="form.online_confirmation"
        type="select"
        :label="__('Confirmation')"
        :options="[
          { label: __('Automatic'), value: 'Automatic' },
          { label: __('Manual approval'), value: 'Manual approval' },
        ]"
      />
      <FormControl
        v-model.number="form.online_slot_interval"
        type="number"
        min="0"
        :label="__('Online start times every (min)')"
        :description="__('0 = the service slot step')"
      />
      <FormControl
        v-if="form.max_participants > 1"
        v-model.number="form.online_max_participants"
        type="number"
        min="1"
        :max="form.max_participants"
        :label="__('Seats per booking')"
      />
    </div>
    <div class="flex flex-wrap gap-4">
      <label class="flex items-center gap-2 text-sm text-ink-gray-7">
        <Switch v-model="form.allow_staff_choice" size="sm" />
        {{ __('Client picks the professional') }}
      </label>
      <label class="flex items-center gap-2 text-sm text-ink-gray-7">
        <Switch v-model="form.show_price_online" size="sm" />
        {{ __('Show the price') }}
      </label>
    </div>

    <!-- when -->
    <div>
      <div class="mb-2 text-p-sm-medium text-ink-gray-6">
        {{ __('When it can be booked') }}
      </div>
      <div class="grid grid-cols-3 gap-3">
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
        <FormControl
          v-model="form.same_day_cutoff"
          type="time"
          :label="__('Same-day bookings until')"
        />
      </div>
      <p class="mt-1 text-p-xs text-ink-gray-5">
        {{
          __(
            'Minimum notice and horizon above apply too. Leave a field empty for no limit.',
          )
        }}
      </p>
    </div>

    <!-- capacity -->
    <div>
      <div class="mb-2 text-p-sm-medium text-ink-gray-6">
        {{ __('Capacity') }}
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
      <div class="grid grid-cols-4 gap-3">
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
          v-model.number="form.max_per_customer_per_day"
          type="number"
          min="0"
          :label="__('Per client per day')"
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
      <div class="mt-2 flex flex-wrap gap-4">
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <Switch v-model="form.require_phone" size="sm" />
          {{ __('Phone required') }}
        </label>
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <Switch v-model="form.require_notes" size="sm" />
          {{ __('Answer required') }}
        </label>
      </div>
    </div>

    <!-- changes -->
    <div>
      <div class="mb-2 text-p-sm-medium text-ink-gray-6">
        {{ __('Cancelling and moving') }}
      </div>
      <div class="grid grid-cols-4 items-end gap-3">
        <label class="flex h-7 items-center gap-2 text-sm text-ink-gray-7">
          <Switch v-model="form.allow_online_cancel" size="sm" />
          {{ __('Can cancel') }}
        </label>
        <FormControl
          v-model.number="form.cancel_notice_hours"
          type="number"
          min="0"
          :disabled="!form.allow_online_cancel"
          :label="__('Cancel up to (h before)')"
        />
        <label class="flex h-7 items-center gap-2 text-sm text-ink-gray-7">
          <Switch v-model="form.allow_online_reschedule" size="sm" />
          {{ __('Can move') }}
        </label>
        <FormControl
          v-model.number="form.reschedule_notice_hours"
          type="number"
          min="0"
          :disabled="!form.allow_online_reschedule"
          :label="__('Move up to (h before)')"
        />
      </div>
      <FormControl
        v-if="form.allow_online_reschedule"
        v-model.number="form.max_reschedules"
        class="mt-3 w-1/4"
        type="number"
        min="0"
        :label="__('Max moves (0 = any)')"
      />
    </div>
  </div>
</template>

<script setup>
import {
  bookingLink,
  describeOnlineLimits,
  onlineProblems,
} from '@/utils/onlineBooking'
import { FormControl, Switch, toast } from 'frappe-ui'
import { computed } from 'vue'

const form = defineModel({ type: Object, required: true })
const props = defineProps({
  serviceName: { type: String, default: '' },
})

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
