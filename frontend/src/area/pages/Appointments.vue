<!-- Appointments: the cycles of sessions going on, the ones coming, then the
     last ones. -->
<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-xl font-semibold text-ink-gray-9">
      {{ __('Your appointments') }}
    </h1>
    <section
      v-if="appointments.data?.cycles?.length"
      class="flex flex-col gap-2"
    >
      <h2 class="text-base font-medium text-ink-gray-7">
        {{ __('Your cycles of sessions') }}
      </h2>
      <CycleCard
        v-for="cycle in appointments.data.cycles"
        :key="cycle.name"
        :cycle="cycle"
      />
    </section>
    <section class="flex flex-col gap-2">
      <h2 class="text-base font-medium text-ink-gray-7">
        {{ __('Coming up') }}
      </h2>
      <AppointmentCard
        v-for="appointment in appointments.data?.upcoming || []"
        :key="appointment.name"
        :appointment="appointment"
      />
      <p
        v-if="appointments.data && !appointments.data.upcoming.length"
        class="text-p-base text-ink-gray-5"
      >
        {{ __('No appointments booked.') }}
      </p>
    </section>
    <section v-if="appointments.data?.past?.length" class="flex flex-col gap-2">
      <h2 class="text-base font-medium text-ink-gray-7">{{ __('Past') }}</h2>
      <AppointmentCard
        v-for="appointment in appointments.data.past"
        :key="appointment.name"
        :appointment="appointment"
      />
    </section>
  </div>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import AppointmentCard from '../components/AppointmentCard.vue'
import CycleCard from '../components/CycleCard.vue'
import { area } from '../store'

const appointments = createResource({
  url: 'crm.clinica.area.api.get_appointments',
  params: { person: area.person },
  auto: true,
})
</script>
