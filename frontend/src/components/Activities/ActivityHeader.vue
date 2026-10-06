<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <!--
    One row while it fits, two when it does not.

    On Activity the row is the channel picker and the New button, and nothing
    else. It used to open with the word «Activity» in large type — under a tab
    that already says «Activity», beside a list whose header says whose chat it
    is — and those seventy pixels were the ones the last pill needed: on the
    Conversations page «Comments» was cut to «Comme…».
  -->
  <!--
    On a phone the bar of tabs above already names the tab: the title steps
    aside, the tab's actions take the row, and a tab whose actions live in its
    own record has no header at all.
  -->
  <!-- on the conversation, while somebody writes on a phone, the channels
       stay where they are: only the bottom rises with the keyboard
       (telefono.css, «11») -->
  <div
    v-if="title !== 'Data'"
    ref="header"
    class="flex flex-wrap items-center justify-between gap-x-3 gap-y-2 px-3 text-lg-medium"
    :class="[
      title == 'Activity'
        ? 'py-2.5 sm:px-4'
        : 'pb-3 pt-5 sm:px-10 sm:pb-4 sm:pt-6 max-md:pt-3',
      { 'max-md:hidden': azioniNelRecord },
    ]"
  >
    <div
      v-if="title != 'Activity'"
      class="flex h-8 shrink-0 items-center text-xl-semibold text-ink-gray-8 max-md:hidden"
    >
      <!-- a tab named otherwise than its key: the area's (the clinic's patient
           area), the history of where the person came from -->
      {{ __(NOMI_DELLE_SCHEDE[title] || title) }}
    </div>
    <!--
      The channel picker. It changes the stream *and* the box underneath: picking
      WhatsApp and then typing into an email composer was the whole reason the
      four tabs existed.
    -->
    <div
      v-if="title == 'Activity'"
      class="flex min-w-0 flex-1 items-center justify-between gap-2"
    >
      <!-- scrolls rather than compresses: a pill squeezed until its count
           touches its label is a pill nobody can read. The strip that scrolls
           keeps 6px above and below the track: on a touch screen a pill's
           ring reaches that far (telefono.css), and the scrolling cut it at
           the track's edge, leaving a 32px strip to aim at. -->
      <div
        ref="striscia"
        class="-my-1.5 flex min-w-0 overflow-x-auto py-1.5 [&::-webkit-scrollbar]:h-0"
      >
        <div
          class="flex shrink-0 items-center gap-0.5 rounded-lg bg-surface-gray-2 p-0.5 text-p-sm"
          role="tablist"
        >
          <Tooltip
            v-for="option in channelOptions"
            :key="option.key"
            :text="compact && channel !== option.key ? __(option.label) : ''"
          >
            <button
              class="flex h-7 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-md px-2 transition-colors"
              :class="
                channel === option.key
                  ? 'bg-surface-elevation-2 text-ink-gray-9 shadow-sm dark:bg-surface-gray-4'
                  : 'text-ink-gray-6 hover:text-ink-gray-9'
              "
              role="tab"
              :aria-selected="channel === option.key"
              :aria-label="__(option.label)"
              @click="channel = option.key"
            >
              <component
                :is="option.icon"
                v-if="option.icon"
                class="size-3.5 shrink-0"
              />
              <!--
              Narrow, the pills that are not chosen keep their icon and their
              count and lose their word — the chosen one says where you are.
            -->
              <span v-if="!compact || channel === option.key || !option.icon">
                {{ __(option.label) }}
              </span>
              <span
                v-if="option.count"
                class="tabular-nums text-ink-gray-5"
                :class="channel === option.key ? 'text-ink-gray-5' : ''"
              >
                {{ option.count }}
              </span>
            </button>
          </Tooltip>
        </div>
      </div>
      <!--
        Everything that is not a message starts here, and it is here whatever
        the stream is filtered to: a note, a task, an event, a logged call are
        things you do *about* somebody rather than say to them.
      -->
      <Dropdown
        v-if="defaultActions.length"
        :options="defaultActions"
        @click.stop
      >
        <template #default="{ open }">
          <Button
            variant="solid"
            class="flex shrink-0 items-center gap-1"
            :label="__('New')"
            iconLeft="plus"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          />
        </template>
      </Dropdown>
    </div>
    <div
      v-else-if="title == 'Events'"
      class="flex items-center gap-2 max-md:w-full"
    >
      <!-- booking for the person is what this tab is for; an event (a call,
           a meeting) is the other thing it offers -->
      <Button
        v-if="canBook && puo('agenda.prenota')"
        variant="solid"
        class="max-md:flex-1"
        @click="bookAppointment"
      >
        <template #prefix>
          <span class="lucide-calendar-plus size-4" aria-hidden="true" />
        </template>
        <!-- half a phone wide, or in a record's column on a tablet held
             upright (narrower than 1024px), where «Programma un evento» was
             cut: the thing it makes, not the whole sentence -->
        <span class="max-lg:hidden">{{ __('Book an appointment') }}</span>
        <span class="lg:hidden">{{ __('Appointment') }}</span>
      </Button>
      <Button
        v-if="puo('agenda.prenota')"
        :variant="canBook ? 'subtle' : 'solid'"
        class="max-md:flex-1"
        @click="modalRef.showEvent()"
      >
        <template #prefix>
          <EventIcon class="h-4 w-4" />
        </template>
        <span class="max-lg:hidden">{{ __('Schedule an Event') }}</span>
        <span class="lg:hidden">{{ __('Event') }}</span>
      </Button>
    </div>
    <!-- each tab offers to add only what the level may add (doc 30) -->
    <template v-else-if="title == 'Notes'">
      <Button
        v-if="puo('note.scrivi')"
        variant="solid"
        class="max-md:w-full"
        :label="__('New Note')"
        iconLeft="plus"
        @click="modalRef.showNote()"
      />
    </template>
    <template v-else-if="title == 'Tasks'">
      <Button
        v-if="!solaLettura()"
        variant="solid"
        class="max-md:w-full"
        :label="__('New Task')"
        iconLeft="plus"
        @click="modalRef.showTask()"
      />
    </template>
    <template v-else-if="title == 'Attachments'">
      <Button
        v-if="canWrite"
        variant="solid"
        class="max-md:w-full"
        :label="__('Upload Attachment')"
        iconLeft="plus"
        @click="showFilesUploader = true"
      />
    </template>
    <!-- the record's buttons live in the record: signing is not a «New» -->
    <div v-else-if="azioniNelRecord" />
    <Dropdown
      v-else-if="defaultActions.length"
      :options="defaultActions"
      class="max-md:w-full"
      @click.stop
    >
      <template #default="{ open }">
        <Button
          variant="solid"
          class="flex items-center gap-1 max-md:w-full"
          :label="__('New')"
          iconLeft="plus"
          :iconRight="open ? 'chevron-up' : 'chevron-down'"
        />
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import { CHANNELS } from '@/utils/conversation'
import { globalStore } from '@/stores/global'
import { whatsappEnabled } from '@/composables/whatsapp'
import { smsEnabled } from '@/composables/sms'
import { callEnabled } from '@/composables/telephony'
import { useSchedulerMeta } from '@/composables/scheduling'
import { usersStore } from '@/stores/users'
import { useElementSize } from '@vueuse/core'
import { Dropdown, Tooltip } from 'frappe-ui'
import { computed, h, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  tabs: { type: Array, default: () => [] },
  title: { type: String, default: '' },
  doc: { type: Object, default: () => ({}) },
  modalRef: { type: Object, default: () => ({}) },
  counts: { type: Object, default: () => ({}) },
  // whether the record may be changed: attaching a file writes it
  canWrite: { type: Boolean, default: true },
})

const { puo, solaLettura } = usersStore()

// the tabs whose buttons are in the record they show
// the tracking tab too: what the person did on the website is read, not
// added to, and its one button (the tracking's settings) is in it. The «New»
// the tabs whose words are not their key
const NOMI_DELLE_SCHEDE = { Area: 'Client area', Tracking: 'History' }

// it fell to offered every message and record of the Activity tab
const azioniNelRecord = computed(() =>
  [
    'Clinic',
    'Forms',
    'Area',
    'Documents',
    'Quotes',
    'Plans',
    'Tracking',
    'Subscriptions',
  ].includes(props.title),
)

// «write in this channel»: the composer is below, and it decides what opening
// one means
const emit = defineEmits(['write'])

const channel = defineModel('channel', { type: String, default: 'all' })

// the chosen pill in sight: chosen from elsewhere (the history's calls, after
// one is logged) it could sit past the strip's edge, its word cut («Chiamat»)
const striscia = ref(null)
watch(
  channel,
  () =>
    nextTick(() =>
      striscia.value
        ?.querySelector('[aria-selected="true"]')
        ?.scrollIntoView({ block: 'nearest', inline: 'nearest' }),
    ),
  { immediate: true },
)

// What each channel looks like up here, and what has to be switched on for it
// to be offered at all: an SMS chip on a CRM with no Twilio is a promise it
// cannot keep.
//
// The *list* is not here. It comes from CHANNELS, the same list the stream sorts
// rows into, because this pill strip used to hold a second copy of it — and a
// copy is how a channel ends up sorted into a pile that nothing offers a way to
// open, which is exactly what happened to the calls.
//
// And what the level reads (doc 30): Marketing and Accounting see the person,
// not their emails, the team's comments or the calls.
const DECORATION = {
  email: { icon: Email2Icon, condition: () => puo('conversazioni.vedi') },
  whatsapp: { icon: WhatsAppIcon, condition: () => whatsappEnabled.value },
  sms: { icon: SMSIcon, condition: () => smsEnabled.value },
  comment: { icon: CommentIcon, condition: () => puo('note.vedi') },
  call: { icon: PhoneIcon, condition: () => puo('telefono.registro') },
}

const channelOptions = computed(() =>
  CHANNELS.map((channel) => ({
    ...channel,
    ...DECORATION[channel.key],
  }))
    .filter((option) => !option.condition || option.condition())
    .map((option) => ({ ...option, count: props.counts?.[option.key] || 0 })),
)

// Measured on the row itself, not on the window: the same header sits in a
// record's wide tab and in the middle column of the Conversations page, and
// only the room it actually has says whether six words fit.
const header = ref(null)
const { width } = useElementSize(header)
const compact = computed(() => width.value > 0 && width.value < 660)

const { makeCall } = globalStore()
const router = useRouter()
const scheduling = useSchedulerMeta()

// who an appointment would be for: the person, or the person behind a deal
const person = computed(() =>
  props.doc?.doctype === 'CRM Deal' || props.doc?.lead
    ? props.doc.lead
    : props.doc?.name,
)

// something to book, and somebody to book it for
const canBook = computed(
  () => Boolean(person.value) && (scheduling.data?.services || []).length > 0,
)

function bookAppointment() {
  router.push({
    name: 'Calendar',
    query: { new: 'appointment', party: person.value },
  })
}

const showFilesUploader = defineModel('showFilesUploader', { type: Boolean })

// writing to somebody, or a comment for the team: the composer's, and the
// level's (doc 30). Marketing and Accounting read the person, not with them.
const converses = computed(() => puo('conversazioni.usa'))

const defaultActions = computed(() => {
  let actions = [
    {
      icon: h(WhatsAppIcon, { class: 'h-4 w-4' }),
      label: __('WhatsApp Message'),
      onClick: () => emit('write', 'whatsapp'),
      condition: () => whatsappEnabled.value && converses.value,
    },
    {
      icon: h(Email2Icon, { class: 'h-4 w-4' }),
      label: __('Email'),
      onClick: () => emit('write', 'email'),
      condition: () => converses.value,
    },
    {
      icon: h(SMSIcon, { class: 'h-4 w-4' }),
      label: __('SMS'),
      onClick: () => emit('write', 'sms'),
      condition: () => smsEnabled.value && converses.value,
    },
    // what the composer calls it: an «Internal note» for the team. «Comment»
    // sat two rows above «Note», which is something else (a Notes record)
    {
      icon: h(CommentIcon, { class: 'h-4 w-4' }),
      label: __('Internal note'),
      onClick: () => emit('write', 'comment'),
      condition: () => converses.value,
    },
    {
      icon: h(EventIcon, { class: 'h-4 w-4' }),
      label: __('Schedule an Event'),
      onClick: () => props.modalRef.showEvent(),
      condition: () => puo('agenda.prenota'),
    },
    // Booking starts from the person as often as from the calendar: «she
    // called to book». It opens the calendar — where the free times are — with
    // a new appointment already for them.
    {
      icon: h('span', {
        class: 'lucide-calendar-plus size-4',
        'aria-hidden': 'true',
      }),
      label: __('Book an appointment'),
      onClick: bookAppointment,
      condition: () => canBook.value && puo('agenda.prenota'),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Log a Call'),
      onClick: () => props.modalRef.createCallLog(),
      condition: () => puo('telefono.chiama'),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(props.doc.mobile_no),
      condition: () => callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('Note'),
      onClick: () => props.modalRef.showNote(),
      condition: () => puo('note.scrivi'),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('Task'),
      onClick: () => props.modalRef.showTask(),
      condition: () => !solaLettura(),
    },
    {
      icon: h(AttachmentIcon, { class: 'h-4 w-4' }),
      label: __('Upload Attachment'),
      onClick: () => (showFilesUploader.value = true),
      condition: () => props.canWrite,
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})
</script>
