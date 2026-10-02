<!--
  A quote as the person reads it (crm.preventivi.area): proposed, to think about;
  accepted, the services done and the ones to come, with when the next one is
  booked - a dental care plan says the tooth too. What it costs, in all and done
  so far.
-->
<template>
  <article class="area-card flex flex-col gap-3">
    <div class="flex items-start justify-between gap-2">
      <div class="flex min-w-0 flex-col gap-0.5">
        <h2 class="area-row__title">{{ quote.title }}</h2>
        <p class="text-p-sm text-ink-gray-5">{{ quote.practitioner_name }}</p>
      </div>
      <!-- a care plan under way: the design system's «in progress» -->
      <InProgressBadge
        v-if="quote.status === 'Accepted'"
        class="shrink-0"
        :label="labels[quote.status]"
      />
      <Badge
        v-else
        class="shrink-0"
        variant="subtle"
        :theme="quote.status === 'Proposed' ? 'blue' : 'green'"
        :label="labels[quote.status] || __(quote.status)"
      />
    </div>
    <p
      v-if="quote.status === 'Proposed' && quote.valid_until"
      class="text-p-sm text-ink-gray-7"
    >
      {{ __('The quote is valid until {0}.', [day(quote.valid_until)]) }}
    </p>
    <ul class="flex flex-col gap-2">
      <li
        v-for="(item, index) in quote.items"
        :key="index"
        class="flex items-start gap-3"
      >
        <span
          class="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-[50%_50%_50%_22%]"
          :class="
            item.status === 'Done'
              ? 'bg-[var(--brand-subtle)] text-[var(--on-brand-subtle)]'
              : 'bg-surface-gray-2'
          "
          role="img"
          :aria-label="item.status === 'Done' ? __('Done') : __('To do')"
        >
          <LucideCheck
            v-if="item.status === 'Done'"
            class="size-3.5"
            aria-hidden="true"
          />
        </span>
        <span class="flex min-w-0 flex-1 flex-col">
          <span class="text-p-base text-ink-gray-9">
            {{ item.description }}
            <span v-if="item.detail" class="text-ink-gray-6">
              · {{ item.detail }}
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
        <span class="tabular-nums">{{ money(quote.totals.net) }}</span>
      </div>
      <div
        v-if="quote.status !== 'Proposed'"
        class="flex justify-between text-p-sm text-ink-gray-6"
      >
        <span>{{ __('Done so far') }}</span>
        <span class="tabular-nums">{{ money(quote.totals.done) }}</span>
      </div>
    </div>
    <p
      v-if="quote.patient_notes"
      class="whitespace-pre-line text-p-sm text-ink-gray-7"
    >
      {{ quote.patient_notes }}
    </p>
  </article>
</template>

<script setup>
import InProgressBadge from '@/components/Espresso/InProgressBadge.vue'
import { Badge } from 'frappe-ui'
import LucideCheck from '~icons/lucide/check'
import { day, when } from '../dates'

const props = defineProps({ quote: { type: Object, required: true } })

const labels = {
  Proposed: __('To decide'),
  Accepted: __('Going on'),
  Completed: __('Completed'),
}

function money(amount) {
  return new Intl.NumberFormat(document.documentElement.lang || 'it', {
    style: 'currency',
    currency: props.quote.currency || 'EUR',
  }).format(amount || 0)
}
</script>
