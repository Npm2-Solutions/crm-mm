<!-- Appointments: the cycles of sessions going on, what the person waits for,
     the ones coming, then the last ones. -->
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
    <section
      v-if="appointments.data?.waiting?.length || appointments.data?.can_wait"
      class="flex flex-col gap-2"
    >
      <div class="flex items-center justify-between gap-2">
        <h2 class="text-base font-medium text-ink-gray-7">
          {{ __('Waiting list') }}
        </h2>
        <Button
          v-if="appointments.data?.can_wait"
          :label="__('Join the waiting list')"
          icon-left="plus"
          @click="joining = true"
        />
      </div>
      <p
        v-if="said"
        class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
        role="status"
      >
        {{ said }}
      </p>
      <WaitingCard
        v-for="entry in appointments.data?.waiting || []"
        :key="entry.name"
        :entry="entry"
        @changed="changed"
      />
      <p
        v-if="appointments.data && !appointments.data.waiting.length"
        class="text-p-base text-ink-gray-5"
      >
        {{
          __(
            'No time suits you? Join the waiting list: when a place frees up we write to you.',
          )
        }}
      </p>
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
    <WaitingJoinDialog v-model="joining" @changed="changed('')" />
  </div>
</template>

<script setup>
import { Button, createResource } from 'frappe-ui'
import { ref } from 'vue'
import AppointmentCard from '../components/AppointmentCard.vue'
import CycleCard from '../components/CycleCard.vue'
import WaitingCard from '../components/WaitingCard.vue'
import WaitingJoinDialog from '../components/WaitingJoinDialog.vue'
import { area } from '../store'

const joining = ref(false)
// how the last answer went: the card of a place booked or a list left is gone
const said = ref('')

const appointments = createResource({
  url: 'crm.area.api.get_appointments',
  params: { person: area.person },
  auto: true,
})

function changed(message) {
  said.value = message || ''
  appointments.reload()
}
</script>
