<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <!-- one box that scrolls whatever it holds: pulled down from its top on a
       phone it reloads, the empty list too -->
  <div
    ref="contenitore"
    class="flex min-h-0 w-full flex-1 flex-col overflow-y-auto"
  >
    <TiraPerAggiornare v-bind="tira" class="shrink-0" />
    <!-- only the headings with something under them: events over, which the
         list may still hold, leave it, and the tab says there is nothing -->
    <template v-if="computedEvents.length">
      <template v-for="(event, i) in computedEvents" :key="event.type">
        <div class="p-3">
          <CollapsibleSection :opened="!event.collapsed">
            <template #header="{ opened, toggle: toggleHeader }">
              <div class="flex items-center justify-between">
                <div
                  class="flex text-ink-gray-6 max-w-fit cursor-pointer items-center gap-2 text-base"
                  @click="toggleHeader()"
                >
                  <span
                    class="lucide-chevron-right h-4 transition-all duration-300 ease-in-out"
                    :class="{ 'rotate-90': opened }"
                    aria-hidden="true"
                  />
                  <span>
                    {{ __(event.type) }}
                  </span>
                  <Badge :label="event.count" variant="ghost" size="sm" />
                </div>
              </div>
            </template>

            <div class="flex flex-col space-y-1 mt-2">
              <div
                v-for="e in event.items"
                :key="e.id"
                class="flex items-center justify-between gap-2 h-full p-2 group hover:bg-surface-gray-1 rounded cursor-pointer"
                @click="handleEventClick(e)"
              >
                <div class="flex items-stretch gap-1.5 flex-1 min-w-0">
                  <div
                    class="flex flex-col justify-center items-center shadow bg-surface-base size-8 rounded-[8px]"
                  >
                    <div
                      class="uppercase text-[8px] font-semibold text-ink-red-8"
                    >
                      {{ eventDate(e).month }}
                    </div>
                    <div class="text-base-semibold -mt-0.5">
                      {{ eventDate(e).day }}
                    </div>
                  </div>
                  <div class="flex flex-col gap-0.5 text-base truncate">
                    <div class="flex items-center gap-1">
                      <div class="flex justify-center items-center size-4">
                        <div
                          class="size-[6px] rounded shrink-0"
                          :style="{ backgroundColor: e.color || '#30A66D' }"
                        />
                      </div>
                      <div class="font-medium text-ink-gray-7">
                        {{ e.title }}
                      </div>
                    </div>
                    <div class="text-ink-gray-6 ml-1">
                      {{ formattedDateTime(e) }}
                    </div>
                  </div>
                </div>

                <div class="flex items-center gap-2 flex-shrink-0">
                  <MultipleAvatar
                    v-if="e.participants?.length > 1"
                    :avatars="e.participants"
                    size="sm"
                  />
                </div>
              </div>
            </div>
          </CollapsibleSection>
        </div>
        <div
          v-if="i < computedEvents.length - 1"
          class="border-t border-outline-elevation-2"
        />
      </template>
    </template>
    <div v-else class="flex flex-1 items-center justify-center px-6 py-10">
      <EmptyState
        :title="__('No Upcoming Events')"
        :text="__('You have no events scheduled')"
      />
    </div>
  </div>
</template>
<script setup>
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useTiraPerAggiornare } from '@/composables/tiraPerAggiornare'
import { useEventNotifications } from '@/data/notifications'
import { notificationsStore } from '@/stores/notifications'
import { tipoDellEvento } from '@/utils/avvisiDegliEventi'
import { adessoDelCentro, oraDelCentro } from '@/utils/scheduler'
import { useNow } from '@vueuse/core'
import { dayjs } from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const { events, ricarica } = useEventNotifications()

// pulled down on a phone: the events again, from the server, not over at the
// time of the pull
const contenitore = ref(null)
const tira = useTiraPerAggiornare(contenitore, () => ricarica())
// the pull, which the phone's «Refresh» runs too (PulsanteAggiorna)
defineExpose({ tira })
const { toggle } = notificationsStore()

function handleEventClick(e) {
  toggle()

  router.push({
    name: 'Calendar',
    query: {
      eventId: e.id,
      date: e.fromDate,
    },
  })
}

// the browser's clock a minute at a time: the headings follow the hour while
// the tab stays open, and an event leaves it once it is over
const orologio = useNow({ interval: 60 * 1000 })

const computedEvents = computed(() => {
  if (!events.value?.length) return []

  // the centre's now: an event's times are the centre's, and the phone's own
  // clock, in another time zone, called «starting now» what was hours away
  const adesso = oraDelCentro(adessoDelCentro(undefined, orologio.value))
  const mappedEvents = events.value
    .map((event) => ({
      id: event.name,
      title: event.subject,
      fromDate: dayjs(event.starts_on).format('YYYY-MM-DD'),
      fromTime: dayjs(event.starts_on).format('HH:mm'),
      toTime: dayjs(event.ends_on).format('HH:mm'),
      color: event.color,
      allDay: event.all_day,
      owner: event.owner,
      participants: event.participants,
      // null once it is over: it went under «Upcoming»
      type: tipoDellEvento(event, adesso),
    }))
    .filter((event) => event.type)

  const ongoingEvents = mappedEvents.filter((event) => event.type === 'ongoing')

  const startingNowEvents = mappedEvents.filter(
    (event) => event.type === 'startingNow',
  )

  const upcomingEvents = mappedEvents.filter(
    (event) => event.type === 'upcoming',
  )

  return [
    {
      type: 'Starting now',
      collapsed: false,
      count: startingNowEvents.length,
      items: startingNowEvents,
    },
    {
      type: 'Ongoing events',
      collapsed: false,
      count: ongoingEvents.length,
      items: ongoingEvents,
    },
    {
      type: 'Upcoming events',
      collapsed: false,
      count: upcomingEvents.length,
      items: upcomingEvents,
    },
  ].filter((gruppo) => gruppo.count)
})

// the day's clock, as everywhere in the app: «10:00 – 11:30»
const formattedDateTime = (e) => {
  if (e.allDay) return __('All Day')
  return `${e.fromTime} – ${e.toTime}`
}

function eventDate(e) {
  // return date and Month abbreviation return { month: 'Jun', day: '5' }

  const dateObj = dayjs(e.fromDate)
  return {
    day: dateObj.format('DD'),
    month: dateObj.format('MMM'),
  }
}
</script>
