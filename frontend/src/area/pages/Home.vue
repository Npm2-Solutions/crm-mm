<!-- The first screen: the next appointment, and what the centre gave online. -->
<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-xl font-semibold text-ink-gray-9">
      {{ __('Hello, {0}', [firstName]) }}
    </h1>
    <section class="flex flex-col gap-2">
      <h2 class="text-base font-medium text-ink-gray-7">
        {{ __('Your next appointment') }}
      </h2>
      <AppointmentCard v-if="next" :appointment="next" />
      <p v-else-if="appointments.data" class="text-p-base text-ink-gray-5">
        {{ __('No appointments booked.') }}
      </p>
    </section>
    <PrepareVisit />
    <TodayPlans />
    <router-link
      v-if="area.me?.chat"
      :to="{ name: 'Chat' }"
      class="flex items-center justify-between gap-3 rounded-lg bg-surface-white p-4 shadow-sm"
    >
      <span class="flex min-w-0 flex-col">
        <span class="text-p-base font-medium text-ink-gray-9">
          {{ __('A question about hours or bookings?') }}
        </span>
        <span class="text-p-sm text-ink-gray-5">
          {{ __('Ask the centre’s virtual assistant, an AI') }}
        </span>
      </span>
      <span class="shrink-0 text-p-sm text-ink-gray-7">→</span>
    </router-link>
    <section
      v-if="documents.data?.documents?.length"
      class="flex flex-col gap-2"
    >
      <div class="flex items-center justify-between">
        <h2 class="text-base font-medium text-ink-gray-7">
          {{ __('Documents online') }}
        </h2>
        <router-link
          :to="{ name: 'Documents' }"
          class="text-p-sm text-ink-gray-7 underline underline-offset-2"
        >
          {{ __('See all') }}
        </router-link>
      </div>
      <div
        class="rounded-lg bg-surface-white p-4 text-p-base text-ink-gray-8 shadow-sm"
      >
        {{ documents.data.documents[0].title }}
        <span class="block text-p-sm text-ink-gray-5">
          {{
            __('Online until {0}', [
              day(documents.data.documents[0].expires_on),
            ])
          }}
        </span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import { computed } from 'vue'
import AppointmentCard from '../components/AppointmentCard.vue'
import PrepareVisit from '../components/PrepareVisit.vue'
import TodayPlans from '../components/TodayPlans.vue'
import { day } from '../dates'
import { area } from '../store'

const person = area.person
const appointments = createResource({
  url: 'crm.clinica.area.api.get_appointments',
  params: { person },
  auto: true,
})
const documents = createResource({
  url: 'crm.clinica.area.api.get_documents',
  params: { person },
  auto: true,
})

const next = computed(() => appointments.data?.upcoming?.[0])
const firstName = computed(() => {
  const who = (area.me?.people || []).find((p) => p.name === person)
  return (who?.lead_name || area.me?.full_name || '').split(' ')[0]
})
</script>
