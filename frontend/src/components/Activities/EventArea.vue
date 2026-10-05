<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div v-if="events.length || appointments.length" class="pt-1">
    <!--
      A person's appointments, beside their events.

      This tab listed Event records only, and an appointment is not one: what
      a client had booked — the next visit, the cycle of treatments — could be
      found on the calendar and nowhere on the client. The next ones come
      first, soonest at the top; the past ones after, latest first.
    -->
    <section v-if="appointments.length" class="mb-6 px-3 sm:px-10">
      <template v-for="group in appointmentGroups" :key="group.key">
        <div
          v-if="group.rows.length"
          class="mb-2 mt-3 text-p-sm font-medium text-ink-gray-5 first:mt-0"
        >
          {{ group.label }}
        </div>
        <div class="flex flex-col gap-2">
          <button
            v-for="appointment in group.rows"
            :key="appointment.name"
            type="button"
            class="flex w-full items-center gap-3 rounded-lg border border-outline-elevation-2 bg-surface-elevation-1 px-3 py-2.5 text-left transition-colors hover:border-outline-gray-3"
            @click="openAppointment(appointment.name)"
          >
            <span
              class="w-[3px] self-stretch rounded-full"
              :style="{
                backgroundColor:
                  appointment.status === 'Cancelled'
                    ? 'var(--ink-gray-4)'
                    : appointment.color || 'var(--ink-blue-5)',
              }"
            />
            <span class="min-w-0 flex-1">
              <!-- the service and when go on under themselves: at 360px the
                   session of a cycle was «09:00 – 09:45 · …» -->
              <span
                class="block break-words text-base"
                :class="
                  appointment.status === 'Cancelled'
                    ? 'text-ink-gray-5 line-through'
                    : 'text-ink-gray-8'
                "
              >
                {{ appointment.service }}
              </span>
              <span class="block break-words text-p-sm text-ink-gray-5">
                {{ when(appointment) }}
                <template v-if="laSeduta(appointment.cycle, t)">
                  · {{ laSeduta(appointment.cycle, t) }}
                </template>
              </span>
            </span>
            <Badge
              variant="subtle"
              :theme="STATUS_THEME[appointment.status] || 'gray'"
              :label="__(appointment.status)"
            />
          </button>
        </div>
      </template>
    </section>

    <div
      v-if="appointments.length && events.length"
      class="mb-3 px-3 text-p-sm font-medium text-ink-gray-5 sm:px-10"
    >
      {{ __('Events') }}
    </div>
    <div
      v-for="(event, i) in events"
      :key="event.name"
      class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-3 sm:px-10"
    >
      <div
        class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-elevation-2"
        :class="i != events.length - 1 ? 'before:h-full' : 'before:h-4'"
      >
        <div
          class="flex h-8 w-7 items-center justify-center bg-surface-base text-ink-gray-8"
        >
          <CalendarIcon class="h-4 w-4" />
        </div>
      </div>
      <div class="mb-5">
        <div
          class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base"
        >
          <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
            <Avatar
              :image="event.owner.image"
              :label="event.owner.label"
              size="md"
            />
            <span class="font-medium text-ink-gray-8 ml-1">
              {{ event.owner.label }}
            </span>
            <span>{{ 'has created an event' }}</span>
          </div>
          <div class="ml-auto whitespace-nowrap">
            <TimelineTimestamp :date="event.creation" />
          </div>
        </div>
        <div
          class="flex gap-2 border cursor-pointer border-outline-elevation-2 rounded-lg bg-surface-elevation-1 px-2.5 py-2.5 text-ink-gray-9"
          @click="showEvent(event)"
        >
          <div
            class="flex w-[2px] rounded-lg"
            :style="{ backgroundColor: event.color || '#30A66D' }"
          />
          <div class="flex-1 flex flex-col gap-1 text-base">
            <div
              class="flex items-center justify-between gap-2 font-medium text-ink-gray-7"
            >
              <div>{{ event.subject }}</div>
              <MultipleAvatar
                v-if="event.participants?.length > 1"
                :avatars="event.participants"
                size="sm"
              />
            </div>
            <div
              class="flex justify-between gap-2 items-center text-ink-gray-6"
            >
              <div>
                {{
                  startEndTime(event.starts_on, event.ends_on, event.all_day)
                }}
              </div>
              <div>{{ startDate(event.starts_on) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <EmptyState
    v-else
    :title="__('No Events Scheduled')"
    :description="
      __('No events coming up. Create a new one to keep things on track.')
    "
    :icon="CalendarIcon"
    top="30%"
  />
</template>
<script setup>
import EmptyState from '@/components/ListViews/EmptyState.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import { useEvent, showEventModal, activeEvent } from '@/composables/event'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { laSeduta } from '@/utils/cicli'
import { adessoDelCentro } from '@/utils/scheduler'
import { Avatar, Badge, createResource, dayjs } from 'frappe-ui'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, default: '' },
  docname: { type: String, default: '' },
})

const router = useRouter()

function showEvent(e = {}) {
  showEventModal.value = true
  activeEvent.value = e
}

const { events, startEndTime, startDate } = useEvent({
  doctype: props.doctype,
  docname: props.docname,
})

// grey for cancelled, as its block on the calendar is
const STATUS_THEME = {
  Scheduled: 'blue',
  Confirmed: 'green',
  Completed: 'gray',
  'No Show': 'red',
  Cancelled: 'gray',
}

const booked = createResource({
  url: 'crm.api.appointments.get_person_appointments',
  params: { doctype: props.doctype, name: props.docname },
  cache: ['person-appointments', props.doctype, props.docname],
  auto: true,
})

const appointments = computed(() => booked.data || [])
const t = (text, args) => __(text, args)

const appointmentGroups = computed(() => {
  // the centre's now, as the appointments' times are the centre's: the
  // phone's own put tonight's appointment among the coming ones on a phone in
  // another time zone
  const now = dayjs(adessoDelCentro())
  const upcoming = appointments.value
    .filter((row) => dayjs(row.ends_on).isAfter(now))
    .sort((a, b) => dayjs(a.starts_on).diff(dayjs(b.starts_on)))
  const past = appointments.value.filter(
    (row) => !dayjs(row.ends_on).isAfter(now),
  )
  return [
    { key: 'upcoming', label: __('Coming up'), rows: upcoming },
    { key: 'past', label: __('Earlier'), rows: past },
  ]
})

function when(row) {
  const start = dayjs(row.starts_on)
  return `${start.format('ddd D MMM YYYY')} · ${start.format('HH:mm')} – ${dayjs(row.ends_on).format('HH:mm')}`
}

// on the calendar, open: where it can be moved, changed or cancelled
function openAppointment(name) {
  const row = appointments.value.find((one) => one.name === name)
  router.push({
    name: 'Calendar',
    query: {
      appointment: name,
      date: row ? dayjs(row.starts_on).format('YYYY-MM-DD') : undefined,
    },
  })
}
</script>
