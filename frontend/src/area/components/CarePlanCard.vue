<!--
  A dental care plan as the person reads it: proposed, the quote to think about;
  accepted, the treatments done and the ones to come, with when the next one is
  booked. What it costs, in all and done so far.
-->
<template>
  <article
    class="flex flex-col gap-3 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="flex min-w-0 flex-col gap-0.5">
        <h2 class="text-base font-medium text-ink-gray-9">{{ plan.title }}</h2>
        <p class="text-p-sm text-ink-gray-5">{{ plan.practitioner_name }}</p>
      </div>
      <Badge
        class="shrink-0"
        variant="subtle"
        :theme="plan.status === 'Proposed' ? 'blue' : 'green'"
        :label="labels[plan.status] || __(plan.status)"
      />
    </div>
    <p
      v-if="plan.status === 'Proposed' && plan.valid_until"
      class="text-p-sm text-ink-gray-7"
    >
      {{ __('The quote is valid until {0}.', [day(plan.valid_until)]) }}
    </p>
    <ul class="flex flex-col gap-2">
      <li
        v-for="(item, index) in plan.items"
        :key="index"
        class="flex items-start gap-3"
      >
        <span
          class="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full text-p-xs"
          :class="
            item.status === 'Done'
              ? 'bg-surface-green-2 text-ink-green-8'
              : 'bg-surface-gray-2 text-ink-gray-6'
          "
          :aria-label="item.status === 'Done' ? __('Done') : __('To do')"
        >
          {{ item.status === 'Done' ? '✓' : '' }}
        </span>
        <span class="flex min-w-0 flex-1 flex-col">
          <span class="text-p-base text-ink-gray-9">
            {{ item.description }}
            <span v-if="item.tooth" class="text-ink-gray-6">
              · {{ __('tooth {0}', [item.tooth]) }}
            </span>
          </span>
          <span v-if="item.when" class="text-p-sm text-ink-gray-6">
            {{ __('Booked for {0}', [when(item.when)]) }}
          </span>
        </span>
        <span class="shrink-0 text-p-sm tabular-nums text-ink-gray-7">
          {{ money(item.amount) }}
        </span>
      </li>
    </ul>
    <div class="flex flex-col gap-0.5 border-t border-outline-gray-1 pt-2">
      <div class="flex justify-between text-p-base font-medium text-ink-gray-9">
        <span>{{ __('Total') }}</span>
        <span class="tabular-nums">{{ money(plan.totals.net) }}</span>
      </div>
      <div
        v-if="plan.status !== 'Proposed'"
        class="flex justify-between text-p-sm text-ink-gray-6"
      >
        <span>{{ __('Done so far') }}</span>
        <span class="tabular-nums">{{ money(plan.totals.done) }}</span>
      </div>
    </div>
    <p
      v-if="plan.patient_notes"
      class="whitespace-pre-line text-p-sm text-ink-gray-7"
    >
      {{ plan.patient_notes }}
    </p>
  </article>
</template>

<script setup>
import { Badge } from 'frappe-ui'
import { day, when } from '../dates'

const props = defineProps({ plan: { type: Object, required: true } })

const labels = {
  Proposed: __('To decide'),
  Accepted: __('Going on'),
  Completed: __('Completed'),
}

function money(amount) {
  return new Intl.NumberFormat(document.documentElement.lang || 'it', {
    style: 'currency',
    currency: props.plan.currency || 'EUR',
  }).format(amount || 0)
}
</script>
