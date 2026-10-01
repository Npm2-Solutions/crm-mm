<!--
  A subscription the person has: what it is, until when it lasts, and - when its
  entries are counted - how many are left this week or this month. Booking stays
  with the centre and the booking page: an appointment of a comprised service
  uses an entry by itself.
-->
<template>
  <article
    class="flex flex-col gap-2 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
  >
    <div class="flex items-start justify-between gap-2">
      <h3 class="min-w-0 text-base font-medium text-ink-gray-9">
        {{ subscription.type }}
      </h3>
      <Badge
        v-if="subscription.suspended_until"
        class="shrink-0"
        variant="subtle"
        theme="orange"
        :label="__('Suspended')"
      />
    </div>
    <p v-if="subscription.description" class="text-p-sm text-ink-gray-7">
      {{ subscription.description }}
    </p>
    <template v-if="left !== null">
      <div
        class="h-2 w-full overflow-hidden rounded-full bg-surface-gray-2"
        role="progressbar"
        :aria-valuenow="percentuale(subscription)"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="__('Entries used')"
      >
        <div
          class="h-full rounded-full bg-[var(--brand-segno)]"
          :style="{ width: `${percentuale(subscription)}%` }"
        />
      </div>
      <p class="text-p-base text-ink-gray-8">{{ leftLine }}</p>
    </template>
    <p class="text-p-sm text-ink-gray-6">{{ until }}</p>
  </article>
</template>

<script setup>
import { A_SETTIMANA, percentuale, rimasti } from '@/utils/abbonamenti'
import { Badge } from 'frappe-ui'
import { computed } from 'vue'
import { day } from '../dates'

const props = defineProps({ subscription: { type: Object, required: true } })

// entries still to use in this week or month; none counted, nothing to say
const left = computed(() =>
  props.subscription.used === null || props.subscription.used === undefined
    ? null
    : rimasti(props.subscription),
)

const leftLine = computed(() => {
  const week = props.subscription.entries === A_SETTIMANA
  if (left.value === 1)
    return week ? __('1 entry left this week') : __('1 entry left this month')
  return week
    ? __('{0} entries left this week', [left.value])
    : __('{0} entries left this month', [left.value])
})

const until = computed(() => {
  const parts = []
  if (props.subscription.suspended_until)
    parts.push(
      __('suspended until {0}', [day(props.subscription.suspended_until)]),
    )
  parts.push(
    props.subscription.auto_renew
      ? __('renews by itself on {0}', [
          day(nextDay(props.subscription.ends_on)),
        ])
      : __('valid until {0}', [day(props.subscription.ends_on)]),
  )
  return parts.join(' · ')
})

function nextDay(value) {
  const giorno = new Date(`${value}T00:00:00Z`)
  giorno.setUTCDate(giorno.getUTCDate() + 1)
  return giorno.toISOString().slice(0, 10)
}
</script>
