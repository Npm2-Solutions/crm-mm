<!--
  Where this person came from, and what they did — as one stream.

  It used to be three things stacked on one screen: the ad in a card, the two
  attribution snapshots in two more, and the timeline of visits underneath. The
  one question anybody actually asks of this panel is what happened and in what
  order, and none of the three answered it — the reader had to hold the ad in
  their head while reading the visits below it. So there is one timeline, and
  the ad, the touches, the visits and the events are all rows on it.
-->
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
      <div class="pt-4">
        <div class="flex items-baseline gap-2 pb-3">
          <span class="text-lg-semibold text-ink-gray-8">{{
            __('Timeline')
          }}</span>
          <span v-if="timeline.length" class="text-p-sm text-ink-gray-5">
            {{ __('{0} visits', [sessions.length]) }} ·
            {{ __('{0} events', [events.length]) }}
          </span>
        </div>

        <!--
          Nothing to show is a fact worth stating. A record attributed to the CRM
          itself never had a browser session, and silently rendering an empty
          space here reads as a broken screen rather than as an answer.
        -->
        <div
          v-if="!timeline.length"
          class="flex flex-col items-start gap-2 rounded-md border border-outline-gray-2 bg-surface-gray-1 px-3 py-3"
        >
          <div
            class="flex items-center gap-2 text-p-base-medium text-ink-gray-7"
          >
            <LucideInfo class="h-4 w-4 shrink-0" />
            {{ __('No visit recorded') }}
          </div>
          <p class="text-p-sm text-ink-gray-6">{{ emptyReason }}</p>
          <Button
            v-if="!isOfflineOrigin"
            :label="__('Set up lead tracking')"
            @click="openTrackingSettings"
          />
        </div>

        <div
          v-for="(row, i) in timeline"
          :key="row.key"
          class="grid grid-cols-[30px_minmax(0,_1fr)] gap-4"
        >
          <!-- the rail: unbroken except under the very last row -->
          <div
            class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-elevation-2"
            :class="i != timeline.length - 1 ? 'before:h-full' : 'before:h-4'"
          >
            <div
              class="flex items-center justify-center bg-surface-base text-ink-gray-7"
              :class="
                row.kind === 'event'
                  ? 'h-6 w-6 rounded-full bg-surface-gray-2 text-ink-gray-6'
                  : 'h-8 w-7'
              "
            >
              <component
                :is="iconFor(row)"
                :class="row.kind === 'event' ? 'h-3 w-3' : 'h-4 w-4'"
              />
            </div>
          </div>

          <div class="min-w-0 pb-3">
            <!-- the timestamp sits on the same line as whatever the row is -->
            <div class="flex items-start gap-2">
              <div class="min-w-0 flex-1">
                <AdCard v-if="row.kind === 'ad'" :ad="row.data" />

                <TouchCard
                  v-else-if="row.kind === 'touch'"
                  :title="
                    row.data.which === 'first'
                      ? __('First touch')
                      : __('Last touch')
                  "
                  :touch="row.data"
                  :theme="row.data.which === 'first' ? 'green' : 'blue'"
                />

                <template v-else-if="row.kind === 'visit'">
                  <div class="flex flex-wrap items-center gap-2 py-1">
                    <Badge
                      :label="__(row.data.source_category || 'Unknown')"
                      theme="blue"
                      size="sm"
                    />
                    <span
                      class="truncate text-base font-medium text-ink-gray-8"
                    >
                      {{ visitTitle(row.data) }}
                    </span>
                    <span
                      v-if="row.data.campaign"
                      class="truncate text-p-sm text-ink-gray-5"
                    >
                      · {{ row.data.campaign }}
                    </span>
                  </div>
                  <div
                    v-if="visitDetails(row.data).length"
                    class="flex flex-wrap items-center gap-x-3 gap-y-1 text-p-sm text-ink-gray-5"
                  >
                    <span
                      v-for="detail in visitDetails(row.data)"
                      :key="detail"
                      class="truncate"
                    >
                      {{ detail }}
                    </span>
                  </div>
                </template>

                <template v-else>
                  <span class="truncate text-base text-ink-gray-8">
                    {{ eventTitle(row.data) }}
                  </span>
                  <div
                    v-if="eventDetails(row.data).length"
                    class="flex flex-wrap items-center gap-x-3 text-p-sm text-ink-gray-5"
                  >
                    <span
                      v-for="detail in eventDetails(row.data)"
                      :key="detail"
                      class="truncate"
                    >
                      {{ detail }}
                    </span>
                  </div>
                </template>
              </div>
              <span v-if="row.at" class="shrink-0 whitespace-nowrap">
                <TimelineTimestamp :date="row.at" />
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import EmptyState from '@/components/ListViews/EmptyState.vue'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import TouchCard from '@/components/Activities/TouchCard.vue'
import AdCard from '@/components/Activities/AdCard.vue'
import { useTimelinePreferences } from '@/composables/useTimelinePreferences'
import { activeSettingsPage, showSettings } from '@/composables/settings'
import { buildTimeline, readableDuration } from '@/utils/journey'
import LucideCalendarClock from '~icons/lucide/calendar-clock'
import LucideCheck from '~icons/lucide/check'
import LucideEye from '~icons/lucide/eye'
import LucideFlag from '~icons/lucide/flag'
import LucideGlobe from '~icons/lucide/globe'
import LucideInfo from '~icons/lucide/info'
import LucideLink from '~icons/lucide/link'
import LucideMegaphone from '~icons/lucide/megaphone'
import LucidePhone from '~icons/lucide/phone'
import LucideRadar from '~icons/lucide/radar'
import LucideSparkles from '~icons/lucide/sparkles'
import LucideSquareCheck from '~icons/lucide/square-check'
import LucideTextCursorInput from '~icons/lucide/text-cursor-input'
import { Badge, Button, LoadingIndicator, createResource } from 'frappe-ui'
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

// Fetched here rather than inside the card, because the ad has to be placed in
// time with everything else and a component that fetches its own data cannot be
// sorted into a list. Never fatal: this screen does not depend on Meta.
const ad = createResource({
  url: 'crm.integrations.meta.api.get_record_ad',
  params: { doctype: props.doctype, name: props.docname },
  auto: true,
})

const events = computed(() => journey.data?.events || [])
const sessions = computed(() => journey.data?.sessions || [])

const timeline = computed(() =>
  buildTimeline(
    { ...(journey.data || {}), ad: ad.data || {} },
    { newestFirst: isNewestFirst.value },
  ),
)

const hasAnything = computed(
  () =>
    events.value.length ||
    sessions.value.length ||
    journey.data?.first_touch?.category,
)

/**
 * Records whose origin was never a browser: the CRM's own screens, or an API
 * that handed us a contact. They have attribution but can never have a journey,
 * so pointing their owner at the tracking script would be wrong advice.
 */
const OFFLINE_CATEGORIES = ['CRM UI', 'Third Party']

const isOfflineOrigin = computed(() =>
  OFFLINE_CATEGORIES.includes(journey.data?.first_touch?.category),
)

const emptyReason = computed(() => {
  const category = journey.data?.first_touch?.category
  if (category === 'CRM UI')
    return __(
      'This record was created by hand in the CRM, so there is no browsing to show. A journey appears for records that arrive from a form, a booking, or a site running the tracking script.',
    )
  if (category === 'Third Party')
    return __(
      'This record arrived through an integration rather than a browser, so there is no browsing to show.',
    )
  return __(
    'Nothing has been recorded for this visitor yet. Check that the tracking script is installed on the site this lead came from.',
  )
})

function openTrackingSettings() {
  activeSettingsPage.value = 'Lead Tracking'
  showSettings.value = true
}

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

function iconFor(row) {
  if (row.kind === 'ad') return LucideMegaphone
  if (row.kind === 'touch') return LucideFlag
  if (row.kind === 'visit') return LucideGlobe
  return ICONS[row.data.event_type] || LucideSparkles
}

function visitTitle(visit) {
  const source = visit.source || __('Unknown')
  return visit.medium ? `${source} / ${visit.medium}` : source
}

function visitDetails(visit) {
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
