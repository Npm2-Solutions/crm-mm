<!--
  The first screen, as the brand's phone has it: hello; the next appointment, the
  page's deep block, and what to prepare for it; the plans followed today, in the
  clouds of their kinds; the assistant for a question; what the centre gave
  online.
-->
<template>
  <div class="flex flex-col gap-5">
    <h1 class="area-title">{{ __('Hello, {0}', [firstName]) }}</h1>
    <section class="flex flex-col gap-2">
      <h2 class="sr-only">{{ __('Your next appointment') }}</h2>
      <NextAppointment v-if="next" :appointment="next" />
      <router-link
        v-else-if="appointments.data"
        :to="{ name: 'Appointments' }"
        class="area-card area-row"
      >
        <AreaChip icona="calendar" />
        <span class="min-w-0 flex-1">
          <span class="area-row__title">
            {{ __('No appointments booked.') }}
          </span>
          <span class="area-row__sub">{{ __('Your appointments') }}</span>
        </span>
        <LucideChevronRight class="area-row__go size-5" aria-hidden="true" />
      </router-link>
    </section>
    <PrepareVisit />
    <TodayPlans v-if="section('plans')" />
    <section
      v-if="area.me?.chat || documents.data?.documents?.length"
      class="flex flex-col gap-2"
    >
      <router-link
        v-if="area.me?.chat"
        :to="{ name: 'Chat' }"
        class="area-card area-row"
      >
        <AreaChip icona="message-circle-question" />
        <span class="min-w-0 flex-1">
          <span class="area-row__title">
            {{ __('A question about hours or bookings?') }}
          </span>
          <span class="area-row__sub">
            {{ __('Ask the centre’s virtual assistant, an AI') }}
          </span>
        </span>
        <LucideChevronRight class="area-row__go size-5" aria-hidden="true" />
      </router-link>
      <template v-if="documents.data?.documents?.length">
        <HiddenCard
          v-if="primo.hidden"
          :when="__('Online until {0}', [day(primo.expires_on)])"
        />
        <router-link
          v-else
          :to="{ name: 'Documents' }"
          class="area-card area-row"
        >
          <AreaChip colore="blue" icona="file-text" />
          <span class="min-w-0 flex-1">
            <span class="area-row__title">{{ primo.title }}</span>
            <span class="area-row__sub">
              {{ __('Online until {0}', [day(primo.expires_on)]) }}
            </span>
          </span>
          <LucideChevronRight class="area-row__go size-5" aria-hidden="true" />
        </router-link>
      </template>
    </section>
    <PasskeyCard v-if="!anteprima" />
    <InstallCard v-if="!anteprima" />
  </div>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import { computed } from 'vue'
import LucideChevronRight from '~icons/lucide/chevron-right'
import { anteprima } from '../anteprima'
import AreaChip from '../components/AreaChip.vue'
import HiddenCard from '../components/HiddenCard.vue'
import InstallCard from '../components/InstallCard.vue'
import NextAppointment from '../components/NextAppointment.vue'
import PasskeyCard from '../components/PasskeyCard.vue'
import PrepareVisit from '../components/PrepareVisit.vue'
import TodayPlans from '../components/TodayPlans.vue'
import { day } from '../dates'
import { area, section } from '../store'

const person = area.person
const appointments = createResource({
  url: 'crm.area.api.get_appointments',
  params: { person },
  auto: true,
})
const documents = createResource({
  url: 'crm.documenti.area.get_documents',
  params: { person },
  auto: section('documents'),
})

const next = computed(() => appointments.data?.upcoming?.[0])
// the last document the centre gave
const primo = computed(() => documents.data?.documents?.[0] || {})
const firstName = computed(() => {
  const who = (area.me?.people || []).find((p) => p.name === person)
  return (who?.lead_name || area.me?.full_name || '').split(' ')[0]
})
</script>
