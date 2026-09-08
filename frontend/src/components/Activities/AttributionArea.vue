<template>
  <div class="h-full overflow-y-auto px-3 pb-5 sm:px-10">
    <div
      v-if="journey.loading"
      class="flex h-full flex-col items-center justify-center gap-3 text-2xl-medium text-ink-gray-4"
    >
      <LoadingIndicator class="h-6 w-6" />
      <span>{{ __('Loading...') }}</span>
    </div>

    <EmptyState
      v-else-if="!hasAnything"
      :title="__('Nothing tracked yet')"
      :description="
        __(
          'No visit has been recorded for this record yet. Add the tracking script to your site, or check that this lead came in through a tracked form.',
        )
      "
      :icon="LucideRadar"
    />

    <template v-else>
      <!-- What brought them in, and what brought them back -->
      <div class="grid grid-cols-1 gap-3 pt-4 sm:grid-cols-2">
        <TouchCard
          :title="__('First touch')"
          :touch="journey.data?.first_touch"
          theme="green"
        />
        <TouchCard
          :title="__('Last touch')"
          :touch="journey.data?.last_touch"
          theme="blue"
        />
      </div>

      <!-- One stream: every visit, and what happened inside it -->
      <div v-if="timeline.length" class="pt-6">
        <div class="flex items-baseline gap-2 pb-3">
          <span class="text-lg-semibold text-ink-gray-8">{{
            __('Timeline')
          }}</span>
          <span class="text-p-sm text-ink-gray-5">
            {{ __('{0} visits', [sessions.length]) }} ·
            {{ __('{0} events', [events.length]) }}
          </span>
        </div>

        <div
          v-for="(visit, v) in timeline"
          :key="visit.name"
          class="grid grid-cols-[30px_minmax(0,_1fr)] gap-4"
        >
          <!-- the rail: unbroken except under the very last row -->
          <div
            class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-elevation-2"
            :class="
              v != timeline.length - 1 || visit.events.length
                ? 'before:h-full'
                : 'before:h-4'
            "
          >
            <div
              class="flex h-8 w-7 items-center justify-center bg-surface-base text-ink-gray-7"
            >
              <LucideGlobe class="h-4 w-4" />
            </div>
          </div>

          <!-- the visit, and the campaign behind it -->
          <div class="min-w-0 pb-3">
            <div class="flex flex-wrap items-center gap-2 py-1">
              <Badge
                v-if="!visit.unknown"
                :label="__(visit.source_category || 'Unknown')"
                theme="blue"
                size="sm"
              />
              <span class="truncate text-base font-medium text-ink-gray-8">
                {{ visitTitle(visit) }}
              </span>
              <span
                v-if="visit.campaign"
                class="truncate text-p-sm text-ink-gray-5"
              >
                · {{ visit.campaign }}
              </span>
              <span class="ml-auto whitespace-nowrap">
                <TimelineTimestamp :date="visit.started_on" />
              </span>
            </div>
            <div
              v-if="visitDetails(visit).length"
              class="flex flex-wrap items-center gap-x-3 gap-y-1 text-p-sm text-ink-gray-5"
            >
              <span
                v-for="detail in visitDetails(visit)"
                :key="detail"
                class="truncate"
              >
                {{ detail }}
              </span>
            </div>
          </div>

          <!-- the events of this visit, in the same stream -->
          <template v-for="(event, i) in visit.events" :key="event.name">
            <div
              class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-elevation-2"
              :class="
                v != timeline.length - 1 || i != visit.events.length - 1
                  ? 'before:h-full'
                  : 'before:h-3'
              "
            >
              <div
                class="flex h-6 w-6 items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-6"
              >
                <component :is="iconFor(event.event_type)" class="h-3 w-3" />
              </div>
            </div>
            <div class="min-w-0 pb-3">
              <div class="flex items-center justify-between gap-2">
                <span class="truncate text-base text-ink-gray-8">
                  {{ eventTitle(event) }}
                </span>
                <span class="ml-auto whitespace-nowrap">
                  <TimelineTimestamp :date="event.occurred_on" />
                </span>
              </div>
              <div
                v-if="eventDetails(event).length"
                class="flex flex-wrap items-center gap-x-3 text-p-sm text-ink-gray-5"
              >
                <span
                  v-for="detail in eventDetails(event)"
                  :key="detail"
                  class="truncate"
                >
                  {{ detail }}
                </span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import EmptyState from '@/components/ListViews/EmptyState.vue'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import TouchCard from '@/components/Activities/TouchCard.vue'
import { useTimelinePreferences } from '@/composables/useTimelinePreferences'
import { groupJourney, readableDuration } from '@/utils/journey'
import LucideCalendarClock from '~icons/lucide/calendar-clock'
import LucideCheck from '~icons/lucide/check'
import LucideEye from '~icons/lucide/eye'
import LucideGlobe from '~icons/lucide/globe'
import LucideLink from '~icons/lucide/link'
import LucidePhone from '~icons/lucide/phone'
import LucideRadar from '~icons/lucide/radar'
import LucideSparkles from '~icons/lucide/sparkles'
import LucideSquareCheck from '~icons/lucide/square-check'
import LucideTextCursorInput from '~icons/lucide/text-cursor-input'
import { Badge, LoadingIndicator, createResource } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doctype: { type: String, default: 'CRM Lead' },
  docname: { type: String, default: '' },
})

const { isNewestFirst } = useTimelinePreferences()

const journey = createResource({
  url: 'crm.api.tracking.get_journey',
  params: { doctype: props.doctype, name: props.docname },
  auto: true,
})

const events = computed(() => journey.data?.events || [])
const sessions = computed(() => journey.data?.sessions || [])

const timeline = computed(() =>
  groupJourney(sessions.value, events.value, {
    newestFirst: isNewestFirst.value,
  }),
)

const hasAnything = computed(
  () =>
    events.value.length ||
    sessions.value.length ||
    journey.data?.first_touch?.category,
)

const ICONS = {
  'Page View': LucideEye,
  'Form View': LucideTextCursorInput,
  'Form Submitted': LucideSquareCheck,
  'Link Clicked': LucideLink,
  Booking: LucideCalendarClock,
  Call: LucidePhone,
  Identified: LucideCheck,
  Custom: LucideSparkles,
}

function iconFor(eventType) {
  return ICONS[eventType] || LucideSparkles
}

function visitTitle(visit) {
  if (visit.unknown) return __('Earlier activity')
  const source = visit.source || __('Unknown')
  return visit.medium ? `${source} / ${visit.medium}` : source
}

function visitDetails(visit) {
  if (visit.unknown)
    return [__('The visit these belong to is no longer listed')]
  return [
    visit.landing_page,
    visit.referrer_domain ? `← ${visit.referrer_domain}` : '',
    visit.duration ? readableDuration(visit.duration) : '',
    [visit.device_type, visit.browser, visit.country]
      .filter(Boolean)
      .join(' · '),
  ].filter(Boolean)
}

function eventTitle(event) {
  const what = __(event.event_type)
  const which = event.label || event.path
  return which ? `${what} — ${which}` : what
}

function eventDetails(event) {
  return [
    event.label && event.path ? event.path : '',
    event.duration ? readableDuration(event.duration) : '',
  ].filter(Boolean)
}
</script>
