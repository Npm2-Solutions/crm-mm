<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The reception desk: the day's appointments as the desk welcomes them - who
  is expected, who is in the waiting room, who came - with what the last days
  left without an outcome and what is left to invoice. A view of the agenda,
  beside it in the header's switch (utils/menu.js, SORELLE); the route keeps
  its first name, Today, and its first address, /oggi.
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs routeName="Today" label="Reception desk" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          icon="chevron-left"
          class="touch-target"
          :aria-label="__('Previous day')"
          @click="shift(-1)"
        />
        <Button
          variant="ghost"
          :label="dayLabel"
          :title="__('Back to today')"
          @click="date = null"
        />
        <Button
          variant="ghost"
          icon="chevron-right"
          class="touch-target"
          :aria-label="__('Next day')"
          @click="shift(1)"
        />
      </div>
    </template>
  </LayoutHeader>
  <!-- touch-pan-y: sideways, the finger is the page's (it changes the day) -->
  <div ref="contenitore" class="flex-1 touch-pan-y overflow-y-auto">
    <!-- pulled down from the top on a phone, the day reloads -->
    <TiraPerAggiornare v-bind="tira" />
    <div class="mx-auto flex max-w-4xl flex-col gap-8 px-5 py-6 max-md:px-4">
      <!-- how the day stands, at a glance: on a phone one short row -->
      <div class="dc-stat-row grid grid-cols-4 gap-3">
        <StatTile
          v-for="(stat, i) in stats"
          :key="stat.label"
          :label="__(stat.label)"
          :value="stat.value"
          :blocco="i === 0"
        />
      </div>

      <!-- the waiting room: who arrived first, first -->
      <section v-if="waiting.length" class="flex flex-col gap-2">
        <h2 class="text-lg-semibold text-ink-gray-8">
          {{ __('Waiting room') }}
        </h2>
        <div
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-4"
        >
          <!-- what they came for above who they are, as in the day below:
               under the buttons it read as belonging to the next person -->
          <div
            v-for="{ appointment, participant } in waiting"
            :key="participant.name"
            class="flex flex-col"
          >
            <div class="-mb-1 pt-3 text-p-sm text-ink-gray-5">
              {{ appointmentLine(appointment) }}
            </div>
            <ParticipantRow
              :appointment="appointment"
              :participant="participant"
              :canMark="appointment.can_mark"
              :past="giornoPassato"
              :now="now"
              @changed="day.reload()"
            />
          </div>
        </div>
      </section>

      <!-- the day, hour by hour -->
      <section class="flex flex-col gap-2">
        <h2 class="text-lg-semibold text-ink-gray-8">
          {{ __('Appointments') }}
        </h2>
        <div v-if="day.loading && !day.data" class="flex justify-center py-10">
          <LoaderMark />
        </div>
        <div
          v-else-if="!appointments.length"
          class="rounded-lg border border-outline-gray-2"
        >
          <EmptyState
            :title="__('Nothing booked on this day')"
            :text="
              __(
                'Whoever books appears here hour by hour: you check them in when they arrive, and mark who came.',
              )
            "
          >
            <Button
              :label="__('Open the agenda')"
              :route="{ name: 'Calendar' }"
            />
          </EmptyState>
        </div>
        <div
          v-else
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="appointment in appointments"
            :key="appointment.name"
            class="flex gap-4 px-4 py-3 max-md:flex-col max-md:gap-1"
          >
            <div
              class="w-24 shrink-0 pt-2 text-p-sm tabular-nums text-ink-gray-6"
            >
              {{ timeOf(appointment.starts_on) }}–{{
                timeOf(appointment.ends_on)
              }}
            </div>
            <div class="flex min-w-0 flex-1 flex-col">
              <div class="flex items-center gap-2 text-p-sm text-ink-gray-5">
                <span
                  class="size-2 shrink-0 rounded-full"
                  :style="{
                    background: appointment.color || 'var(--surface-gray-4)',
                  }"
                />
                <span class="truncate">{{ appointmentLine(appointment) }}</span>
              </div>
              <ParticipantRow
                v-for="participant in appointment.participants"
                :key="participant.name"
                :appointment="appointment"
                :participant="participant"
                :canMark="appointment.can_mark"
                :past="giornoPassato"
                :now="now"
                @changed="day.reload()"
              />
            </div>
          </div>
        </div>
      </section>

      <!-- what the last days left open: the agenda is only as good as this -->
      <section v-if="pastOpen.length" class="flex flex-col gap-2">
        <div class="flex flex-col gap-0.5">
          <h2 class="text-lg-semibold text-ink-gray-8">
            {{ __('Still without an outcome') }}
          </h2>
          <p class="text-p-sm text-ink-gray-5">
            {{
              __(
                "The last days' appointments nobody closed: the records, the reminders and the invoices all read the agenda.",
              )
            }}
          </p>
        </div>
        <!-- the first ones, the rest one tap away: a week left open is a page
             of its own, not something to scroll past to reach the invoices -->
        <div
          v-for="group in pastOpenShown"
          :key="group.day"
          class="flex flex-col gap-1"
        >
          <div class="text-p-sm text-ink-gray-6">
            {{ formatDate(group.day, 'dddd D MMMM') }}
          </div>
          <div
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-4"
          >
            <template
              v-for="appointment in group.appointments"
              :key="appointment.name"
            >
              <ParticipantRow
                v-for="participant in appointment.participants.filter(
                  (p) => p.status === 'Booked',
                )"
                :key="participant.name"
                :appointment="appointment"
                :participant="{ ...participant }"
                :canMark="appointment.can_mark"
                :past="true"
                :now="now"
                @changed="day.reload()"
              />
            </template>
          </div>
        </div>
        <Button
          v-if="pastOpenHidden"
          :label="__('Show all {0}', [pastOpenCount])"
          size="lg"
          class="self-start max-md:w-full"
          @click="allPastOpen = true"
        />
      </section>

      <!-- and what is left to invoice -->
      <RouterLink
        v-if="toInvoice.data?.length"
        :to="{ name: 'Invoices' }"
        class="flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 px-4 py-3 hover:bg-surface-gray-1"
      >
        <span class="min-w-0 text-p-base text-ink-gray-8">
          {{ __('{0} appointments to invoice', [toInvoice.data.length]) }}
        </span>
        <span
          class="lucide-chevron-right size-4 shrink-0 text-ink-gray-5"
          aria-hidden="true"
        />
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import StatTile from '@/components/Espresso/StatTile.vue'
import ParticipantRow from '@/components/Today/ParticipantRow.vue'
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useScorriGiorni } from '@/composables/scorriGiorni'
import { useTiraPerAggiornare } from '@/composables/tiraPerAggiornare'
import { laSeduta } from '@/utils/cicli'
import {
  byDay,
  firstOfPast,
  shiftDay,
  summarize,
  timeOf,
  waitingRoom,
} from '@/utils/oggi'
import { formatDate } from '@/utils'
import { adessoDelCentro } from '@/utils/scheduler'
import { Button, createResource, usePageMeta } from 'frappe-ui'
import { computed, onBeforeUnmount, ref, watch } from 'vue'

// the centre's day, as the server counts it: a browser in another time zone
// would show tomorrow's arrivals at eleven at night. Null is today.
const date = ref(null)
// and its now, which the arrivals' times are read against
const now = ref(adessoDelCentro())

const day = createResource({
  url: 'crm.api.oggi.get_day',
  makeParams: () => ({ date: date.value }),
  auto: true,
})
watch(date, () => day.reload())

// what is left to invoice, for whoever issues invoices
const toInvoice = createResource({
  url: 'crm.invoicing.api.appointments_to_invoice',
})
watch(
  () => day.data?.can_invoice,
  (can) => can && !toInvoice.data && toInvoice.fetch(),
)

// the waiting times move, and a colleague may check somebody in from another desk
const timer = setInterval(() => {
  now.value = adessoDelCentro()
  if (!day.loading) day.reload()
}, 60000)
onBeforeUnmount(() => clearInterval(timer))

const appointments = computed(() => day.data?.appointments || [])
const waiting = computed(() => waitingRoom(appointments.value))
const pastOpen = computed(() => byDay(day.data?.past_open || []))

// what the last days left open: the first few, the rest when asked
const PAST_SHOWN = 4
const allPastOpen = ref(false)
const pastOpenShown = computed(() =>
  allPastOpen.value ? pastOpen.value : firstOfPast(pastOpen.value, PAST_SHOWN),
)
const pastOpenCount = computed(() =>
  (day.data?.past_open || []).reduce(
    (n, appointment) =>
      n + appointment.participants.filter((p) => p.status === 'Booked').length,
    0,
  ),
)
const pastOpenHidden = computed(
  () => !allPastOpen.value && pastOpenCount.value > PAST_SHOWN,
)
const stats = computed(() => {
  const counts = summarize(appointments.value)
  return [
    { label: 'Expected', value: counts.coming },
    { label: 'Waiting', value: counts.waiting },
    { label: 'Came', value: counts.came },
    { label: 'Did not come', value: counts.noShow },
  ]
})

const isToday = computed(() => !date.value || date.value === day.data?.today)
// a day gone by asks whether they came, never to check them in
const giornoPassato = computed(() =>
  Boolean(date.value && day.data?.today && date.value < day.data.today),
)
const dayLabel = computed(() =>
  isToday.value
    ? __('Today')
    : formatDate(day.data?.date || date.value, 'ddd D MMM'),
)

function shift(days) {
  date.value = shiftDay(day.data?.date || date.value, days)
}

// on a phone, as in the agenda's day: pulled down it reloads, swiped
// sideways it is the next day or the one before
const contenitore = ref(null)
const tira = useTiraPerAggiornare(contenitore, () =>
  Promise.all([day.reload(), toInvoice.data && toInvoice.reload()]),
)
useScorriGiorni(contenitore, shift, { segue: true })

// the service, which session of its cycle - "session 4 of 10" - and who
function appointmentLine(appointment) {
  const who = (appointment.staff || []).map((s) => s.full_name).join(', ')
  const session = laSeduta(appointment.cycle, (text, args) => __(text, args))
  return [appointment.service, session, who].filter(Boolean).join(' · ')
}

usePageMeta(() => ({ title: __('Reception desk') }))
</script>
