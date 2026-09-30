<!--
  A cycle of sessions the person follows: ten of physiotherapy, six of laser.
  How far it is, what is left to book, until when it lasts. Booking stays with
  the centre: the next appointment is in the list below.
-->
<template>
  <article
    class="flex flex-col gap-2 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
  >
    <h3 class="text-base font-medium text-ink-gray-9">{{ cycle.service }}</h3>
    <div
      class="h-2 w-full overflow-hidden rounded-full bg-surface-gray-2"
      role="progressbar"
      :aria-valuenow="percentuale(cycle.counts)"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-label="__('Sessions used')"
    >
      <div
        class="h-full rounded-full bg-surface-gray-7"
        :style="{ width: `${percentuale(cycle.counts)}%` }"
      />
    </div>
    <p class="text-p-base text-ink-gray-8">{{ comeVa(cycle.counts, t) }}</p>
    <p class="text-p-sm text-ink-gray-6">
      {{ daPrenotare(cycle.counts, t) }}
      <template v-if="cycle.valid_until">
        · {{ __('valid until {0}', [day(cycle.valid_until)]) }}
      </template>
    </p>
  </article>
</template>

<script setup>
import { comeVa, daPrenotare, percentuale } from '@/utils/cicli'
import { day } from '../dates'

defineProps({ cycle: { type: Object, required: true } })

const t = (text, args) => __(text, args)
</script>
