<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <!--
    Bare: one line inside the notice in the chat. A call has no words, so what
    there is to say fits in a sentence — which way it went, how long it lasted
    or how it ended, and the recording if there is one. It was a title, a date
    badge, a duration badge and a status badge in a card: four shapes for one
    sentence, one of them repeating the date on the marker above it.
  -->
  <div v-if="bare" class="min-w-0">
    <div
      class="flex cursor-pointer flex-wrap items-center gap-x-1.5 gap-y-0.5"
      @click="showCallLogDetailModal = true"
    >
      <span>{{ headline }}</span>
      <template v-if="call.status == 'Completed' && call._duration">
        <span aria-hidden="true">·</span>
        <span class="tabular-nums">{{ call._duration }}</span>
      </template>
      <template v-else-if="outcome && outcome !== headline">
        <span aria-hidden="true">·</span>
        <span>{{ outcome }}</span>
      </template>
      <button
        v-if="call.recording_url"
        class="ml-0.5 inline-flex items-center gap-1 rounded px-1 font-medium text-ink-gray-8 hover:bg-surface-gray-3"
        @click.stop="call.show_recording = !call.show_recording"
      >
        <PlayIcon class="size-3" />
        {{ call.show_recording ? __('Hide') : __('Listen') }}
      </button>
    </div>
    <div
      v-if="call.show_recording && callLog?.data?.recording_url_path"
      class="mt-2"
      @click.stop
    >
      <AudioPlayer :src="callLog.data.recording_url_path" />
    </div>
    <CallLogDetailModal
      v-if="dettagliMontati"
      v-model="showCallLogDetailModal"
      v-model:callLog="callLog"
    />
  </div>
  <div v-else>
    <div class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base">
      <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
        <Avatar
          :image="call._caller.image"
          :label="call._caller.label"
          size="md"
        />
        <span class="font-medium text-ink-gray-8 ml-1">
          {{ call._caller.label }}
        </span>
        <span>{{
          call.type == 'Incoming'
            ? __('has reached out')
            : __('has made a call')
        }}</span>
      </div>
      <div class="ml-auto whitespace-nowrap">
        <TimelineTimestamp :date="call.creation" />
      </div>
    </div>
    <div
      class="flex cursor-pointer flex-col gap-2 rounded-md border border-outline-elevation-2 bg-surface-elevation-1 px-3 py-2.5 text-ink-gray-9"
      @click="showCallLogDetailModal = true"
    >
      <div class="flex items-center justify-between">
        <div class="inline-flex gap-2 items-center text-base-medium">
          <div>
            {{
              call.type == 'Incoming' ? __('Inbound Call') : __('Outbound Call')
            }}
          </div>
        </div>
        <div>
          <MultipleAvatar
            :avatars="[
              {
                image: call._caller.image,
                label: call._caller.label,
                name: call._caller.label,
              },
              {
                image: call._receiver.image,
                label: call._receiver.label,
                name: call._receiver.label,
              },
            ]"
            size="sm"
          />
        </div>
      </div>
      <div class="flex items-center flex-wrap gap-2">
        <Badge :label="giornoDellaChiamata(call.creation)">
          <template #prefix>
            <CalendarIcon class="size-3" />
          </template>
        </Badge>
        <Badge v-if="call.status == 'Completed'" :label="call._duration">
          <template #prefix>
            <DurationIcon class="size-3" />
          </template>
        </Badge>
        <Badge
          v-if="call.recording_url"
          :label="call.show_recording ? __('Hide Recording') : __('Listen')"
          class="cursor-pointer"
          @click.stop="call.show_recording = !call.show_recording"
        >
          <template #prefix>
            <PlayIcon class="size-3" />
          </template>
        </Badge>
        <InProgressBadge
          v-if="call.status === 'In Progress'"
          :label="getCallStatusLabel(call.status, call.type)"
        />
        <Badge
          v-else
          :label="getCallStatusLabel(call.status, call.type)"
          :theme="getCallStatusColor(call.status, call.type)"
        />
      </div>
      <div
        v-if="
          call.show_recording &&
          call.recording_url &&
          callLog?.data?.recording_url_path
        "
        class="flex flex-col items-center justify-between"
        @click.stop
      >
        <AudioPlayer :src="callLog.data.recording_url_path" />
      </div>
    </div>
    <CallLogDetailModal
      v-if="dettagliMontati"
      v-model="showCallLogDetailModal"
      v-model:callLog="callLog"
    />
  </div>
</template>
<script setup>
import PlayIcon from '@/components/Icons/PlayIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import InProgressBadge from '@/components/Espresso/InProgressBadge.vue'
import AudioPlayer from '@/components/Activities/AudioPlayer.vue'
import CallLogDetailModal from '@/components/Modals/CallLogDetailModal.vue'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { getCallStatusColor, getCallStatusLabel } from '@/utils/callLog.js'
import { formatDate } from '@/utils'
import { apertoUnaVolta } from '@/utils/aRichiesta'
import { Avatar, Badge, createResource, dayjs } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

// «dom 4 ott», as every day of DottorCloud is written, with the year when it is
// not this one: «ott 4, domenica» was English's order in Italian words
function giornoDellaChiamata(quando) {
  const questAnno = dayjs(quando).year() === dayjs().year()
  return formatDate(quando, questAnno ? 'ddd D MMM' : 'ddd D MMM YYYY')
}

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
  // the centred notice in the chat already says who, which way and when
  bare: { type: Boolean, default: false },
})

const call = reactive(props.activity)

// Which way, and — when nobody picked up — that first: a missed call is the
// one line in a chat somebody has to do something about.
const headline = computed(() => {
  const incoming = call.type == 'Incoming'
  if (call.status == 'No Answer')
    return incoming ? __('Missed call') : __('Call not answered')
  if (call.status == 'Busy')
    return incoming ? __('Call declined') : __('Line busy')
  return incoming ? __('Incoming call') : __('Outgoing call')
})

const outcome = computed(() =>
  ['No Answer', 'Busy', 'Completed'].includes(call.status)
    ? ''
    : getCallStatusLabel(call.status, call.type),
)

// The call's details - its recording, notes and tasks - are asked for when they
// are needed, the details opened or the recording played: asked for every call
// the conversation showed, and the details' window, mounted closed, opening each
// call as a document, a person with ten calls cost sixty requests to open.
const callLog = createResource({
  url: 'crm.fcrm.doctype.crm_call_log.crm_call_log.get_call_log',
  params: { name: call.name },
  cache: ['call_log', call.name],
})
const showCallLogDetailModal = ref(false)
const dettagliMontati = apertoUnaVolta(showCallLogDetailModal)
let chiesto = false
watch(
  () => showCallLogDetailModal.value || call.show_recording,
  (serve) => {
    if (!serve || chiesto) return
    chiesto = true
    callLog.fetch()
  },
)
</script>
