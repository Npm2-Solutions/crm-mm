<template>
  <div class="h-full overflow-y-auto px-3 pb-5 sm:px-10">
    <div
      v-if="journey.loading"
      class="flex h-full flex-col items-center justify-center gap-3 text-2xl-medium text-ink-gray-4"
    >
      <LoadingIndicator class="h-6 w-6" />
      <span>{{ __('Loading...') }}</span>
    </div>

    <EmptyState v-else-if="!hasAnything" :title="__('Nothing tracked yet')" />

    <template v-else>
      <!-- What brought them in, and what brought them back -->
      <div class="grid grid-cols-1 gap-3 pt-4 sm:grid-cols-2">
        <TouchCard
          :title="__('First touch')"
          :touch="journey.data?.first_touch"
        />
        <TouchCard
          :title="__('Last touch')"
          :touch="journey.data?.last_touch"
        />
      </div>

      <!-- The journey itself -->
      <div v-if="events.length" class="pt-6">
        <div class="pb-2 text-p-base-medium text-ink-gray-7">
          {{ __('Journey') }}
        </div>
        <div
          v-for="(event, i) in events"
          :key="event.name"
          class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-4"
        >
          <div
            class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-elevation-2"
            :class="i != events.length - 1 ? 'before:h-full' : 'before:h-4'"
          >
            <div
              class="flex h-8 w-7 items-center justify-center bg-surface-base text-ink-gray-7"
            >
              <component :is="iconFor(event.event_type)" class="h-4 w-4" />
            </div>
          </div>
          <div class="mb-4 min-w-0">
            <div class="flex items-center justify-between gap-2 py-1">
              <span class="truncate text-base font-medium text-ink-gray-8">
                {{ event.label || event.path || event.event_type }}
              </span>
              <span class="ml-auto whitespace-nowrap">
                <TimelineTimestamp :date="event.occurred_on" />
              </span>
            </div>
            <div
              class="flex flex-wrap items-center gap-2 text-p-sm text-ink-gray-5"
            >
              <Badge :label="__(event.event_type)" theme="gray" size="sm" />
              <span v-if="event.path" class="truncate">{{ event.path }}</span>
              <span v-if="event.duration"
                >· {{ readableDuration(event.duration) }}</span
              >
              <span v-if="sessionLabel(event.session)"
                >· {{ sessionLabel(event.session) }}</span
              >
            </div>
          </div>
        </div>
      </div>

      <!-- Every visit, with the campaign behind it -->
      <div v-if="sessions.length" class="pt-4">
        <div class="pb-2 text-p-base-medium text-ink-gray-7">
          {{ __('Sessions') }}
        </div>
        <div
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="session in sessions"
            :key="session.name"
            class="flex flex-col gap-1 px-3 py-2.5"
          >
            <div class="flex flex-wrap items-center gap-2">
              <Badge
                :label="__(session.source_category || 'Unknown')"
                theme="blue"
                size="sm"
              />
              <span class="text-p-base text-ink-gray-7">
                {{ session.source }} / {{ session.medium }}
              </span>
              <span v-if="session.campaign" class="text-p-sm text-ink-gray-5">
                · {{ session.campaign }}
              </span>
              <span class="ml-auto text-p-sm text-ink-gray-5">
                <TimelineTimestamp :date="session.started_on" />
              </span>
            </div>
            <div class="flex flex-wrap gap-3 text-p-sm text-ink-gray-5">
              <span v-if="session.landing_page" class="truncate">{{
                session.landing_page
              }}</span>
              <span v-if="session.referrer_domain"
                >← {{ session.referrer_domain }}</span
              >
              <span v-if="session.page_view_count">
                {{ session.page_view_count }} {{ __('pages') }}
              </span>
              <span v-if="session.device_type">{{ session.device_type }}</span>
              <span v-if="session.browser">{{ session.browser }}</span>
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
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import { Badge, LoadingIndicator, createResource } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doctype: { type: String, default: 'CRM Lead' },
  docname: { type: String, default: '' },
})

const journey = createResource({
  url: 'crm.api.tracking.get_journey',
  params: { doctype: props.doctype, name: props.docname },
  auto: true,
})

const events = computed(() => journey.data?.events || [])
const sessions = computed(() => journey.data?.sessions || [])

const hasAnything = computed(
  () =>
    events.value.length ||
    sessions.value.length ||
    journey.data?.first_touch?.category,
)

const ICONS = {
  'Page View': DetailsIcon,
  'Form View': DetailsIcon,
  'Form Submitted': EmailIcon,
  'Link Clicked': LinkIcon,
  Booking: CalendarIcon,
  Call: PhoneIcon,
}

function iconFor(eventType) {
  return ICONS[eventType] || DetailsIcon
}

// Sessions are already loaded; label an event with the campaign of the visit it
// happened in, so a page view in the timeline carries its own attribution.
const sessionsByName = computed(() =>
  Object.fromEntries(sessions.value.map((s) => [s.name, s])),
)

function sessionLabel(name) {
  const session = sessionsByName.value[name]
  if (!session) return ''
  return session.campaign || session.source || ''
}

function readableDuration(seconds) {
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  return `${minutes}m ${seconds % 60}s`
}
</script>
