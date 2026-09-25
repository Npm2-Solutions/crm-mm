<!-- eslint-disable vue/no-v-html -->
<!--
  Everything said to this person, in one chat.

  «All» is a chat, not a report: whatever the channel, a message somebody sent
  is a bubble on their side and a message we sent is a bubble on ours. That is
  the one arrangement everybody already knows how to read, and it is the reason
  somebody can work a whole day from this one view without opening the others.

  Two encodings, each meaning one thing and never the other:

  - **the side and the fill** say who — theirs on the left in white, ours on
    the right in grey. Always, on every channel.
  - **the colour** says which channel — green WhatsApp, blue email, violet SMS
    — and it lives on the edge of the bubble and its little icon, never on the
    fill. Tinting the fill by channel would make colour mean two things at once
    and a long chat a colour chart.

  What is **not** addressed to anybody does not get a side: a note we wrote each
  other, a field that changed, all of that sits in the middle of the chat the
  way a messenger puts its own notices there. The note is amber, because it is
  the one thing here the customer will never see.

  Each channel on its own then gets the view that suits it: WhatsApp its own
  paper and its own green, comments a timeline with a thread down the side, and
  email full-width cards — an email thread was never a chat.
-->
<template>
  <div
    class="min-h-full"
    :class="wallpaper ? 'wa-wallpaper' : 'bg-surface-gray-1'"
  >
    <div class="flex w-full flex-col pb-2">
      <!--
        One block per day, with the date pinned inside it. Sticky siblings all
        pin to the same line and pile up there, so yesterday's date stayed on
        screen underneath today's instead of giving way to it.
      -->
      <div
        v-for="group in days"
        :key="group.key"
        class="flex flex-col"
        :class="channel === 'all' ? 'gap-1' : 'gap-1.5'"
      >
        <div
          v-if="group.day"
          class="sticky top-0 z-20 flex justify-center py-2"
        >
          <span
            class="rounded-full bg-surface-gray-3 px-2.5 py-0.5 text-p-xs text-ink-gray-7 shadow-sm"
          >
            {{ __(dayLabelFor(group.day)) }}
          </span>
        </div>

        <!-- comments on their own: a thread, not a chat, because a note is
           addressed to nobody and a side would invent a recipient -->
        <template v-if="channel === 'comment'">
          <div class="flex flex-col px-3 sm:px-4">
            <TimelineEntry
              v-for="row in group.rows"
              :key="row.key"
              :channel="row.channel"
              :icon="iconFor(row.channel)"
            >
              <CommentArea
                v-if="row.channel === 'comment'"
                :activity="row.item"
                @reload="emit('reload')"
              />
              <slot v-else name="other" :item="row.item" :row="row" />
            </TimelineEntry>
          </div>
        </template>

        <!-- email on its own: full width, because a thread is not a chat -->
        <template v-else-if="channel === 'email'">
          <div class="flex flex-col gap-2 px-3 sm:px-4">
            <div
              v-for="row in group.rows"
              :key="row.key"
              class="rounded-lg border bg-surface-white p-3"
              :class="
                row.direction === 'in'
                  ? 'border-l-2 border-outline-blue-3'
                  : 'border-outline-gray-2'
              "
            >
              <EmailArea :activity="row.item" :modalRef="modalRef" />
            </div>
          </div>
        </template>

        <template v-for="row in group.rows" v-else :key="row.key">
          <!-- said to somebody: a side, and the colour of the channel it went by -->
          <div
            v-if="row.direction !== 'internal'"
            class="flex px-3 sm:px-4"
            :class="row.direction === 'out' ? 'justify-end' : 'justify-start'"
          >
            <div class="relative min-w-0 max-w-[min(80%,42rem)]">
              <!--
                WhatsApp keeps its own bubble in its own view: the green and the
                paper are what make that view a WhatsApp conversation rather than
                a list of messages. In the mixed chat it takes the house style
                like everything else, so one channel does not shout over four.
              -->
              <WhatsAppArea
                v-if="row.channel === 'whatsapp' && channel === 'whatsapp'"
                v-model="whatsappMessages"
                v-model:reply="reply"
                :messages="[row.item]"
              />
              <SMSArea
                v-else-if="row.channel === 'sms' && channel === 'sms'"
                :messages="[row.item]"
              />
              <ChatBubble
                v-else
                :channel="row.channel"
                :icon="iconFor(row.channel)"
                :mine="row.direction === 'out'"
                :speaker="speakerOf(row.item, me)"
                :time="row.at ? dayjs(row.at).format('HH:mm') : ''"
              >
                <WhatsAppArea
                  v-if="row.channel === 'whatsapp'"
                  v-model="whatsappMessages"
                  v-model:reply="reply"
                  bare
                  :messages="[row.item]"
                />
                <SMSArea
                  v-else-if="row.channel === 'sms'"
                  bare
                  :messages="[row.item]"
                />
                <CallArea
                  v-else-if="row.channel === 'call'"
                  :activity="row.item"
                />
                <EmailArea v-else :activity="row.item" :modalRef="modalRef" />
              </ChatBubble>
            </div>
          </div>

          <!--
            Addressed to nobody, so it sits in the middle — the way a messenger
            puts its own notices between the messages. These are the other half
            of the history: what was actually *done* between one message and the
            next, which is what the New menu at the top creates.
          -->
          <HappenedCard
            v-else-if="row.channel === 'comment'"
            kind="note"
            :icon="iconFor('comment')"
            card
          >
            <CommentArea :activity="row.item" @reload="emit('reload')" />
          </HappenedCard>

          <HappenedCard
            v-else-if="row.channel === 'note'"
            kind="note"
            :icon="NoteIcon"
            :title="__('Note')"
            :when="timeOf(row)"
            card
          >
            <div class="font-medium">{{ row.item.data?.title }}</div>
            <div
              v-if="row.item.data?.content"
              class="prose-sm max-w-none text-ink-gray-7"
              v-html="sanitizeHTML(row.item.data.content)"
            />
          </HappenedCard>

          <HappenedCard
            v-else-if="row.channel === 'appointment'"
            kind="appointment"
            :icon="CalendarIcon"
            :title="__('Appointment')"
            :when="whenOf(row.item.data?.starts_on)"
            card
          >
            <div class="flex items-center gap-2">
              <span class="font-medium">
                {{ row.item.data?.title || row.item.data?.service }}
              </span>
              <Badge
                v-if="row.item.data?.status"
                size="sm"
                :theme="appointmentTheme(row.item.data.status)"
                :label="__(row.item.data.status)"
              />
            </div>
          </HappenedCard>

          <HappenedCard
            v-else-if="row.channel === 'event'"
            kind="event"
            :icon="CalendarIcon"
            :title="__('Event')"
            :when="whenOf(row.item.data?.starts_on)"
            card
          >
            <span class="font-medium">{{ row.item.data?.subject }}</span>
          </HappenedCard>

          <HappenedCard
            v-else-if="row.channel === 'task'"
            kind="task"
            :icon="TaskIcon"
            :title="__('Task')"
            :when="timeOf(row)"
            card
          >
            <div class="flex items-center gap-2">
              <span
                class="font-medium"
                :class="
                  row.item.data?.status === 'Done'
                    ? 'text-ink-gray-5 line-through'
                    : ''
                "
              >
                {{ row.item.data?.title }}
              </span>
              <Badge
                v-if="row.item.data?.status"
                size="sm"
                :theme="row.item.data.status === 'Done' ? 'green' : 'gray'"
                :label="__(row.item.data.status)"
              />
            </div>
          </HappenedCard>

          <!--
            An invoice. The one row here that is money, so it says the amount at
            a size somebody can read from across the desk, and the badge is the
            only colour on it: a refused transmission is the single state in this
            whole stream that is somebody's job to fix today.
          -->
          <HappenedCard
            v-else-if="row.channel === 'invoice'"
            kind="invoice"
            :icon="MoneyIcon"
            :title="invoiceTitle(row.item.data)"
            :when="timeOf(row)"
            card
          >
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-lg font-semibold text-ink-gray-8">
                {{ amountOf(row.item.data) }}
              </span>
              <Badge
                v-if="statusOf(row.item.data)"
                size="sm"
                :theme="invoiceStatusTheme(statusOf(row.item.data))"
                :label="statusOf(row.item.data)"
              />
              <Badge
                v-if="row.item.data?.docstatus === 0"
                size="sm"
                theme="gray"
                :label="__('Draft')"
              />
            </div>
          </HappenedCard>

          <!--
            The stage moved. Every other field that changes is bookkeeping and
            reads as one quiet line; this one is the point of the whole record,
            so it is the line the eye is allowed to stop on.
          -->
          <HappenedCard
            v-else-if="isStageChange(row.item)"
            kind="stage"
            :icon="iconFor('')"
            :when="timeOf(row)"
          >
            <slot name="other" :item="row.item" :row="row" />
          </HappenedCard>

          <HappenedCard v-else :when="timeOf(row)">
            <slot name="other" :item="row.item" :row="row" />
          </HappenedCard>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import CallArea from '@/components/Activities/CallArea.vue'
import CommentArea from '@/components/Activities/CommentArea.vue'
import EmailArea from '@/components/Activities/EmailArea.vue'
import SMSArea from '@/components/Activities/SMSArea.vue'
import WhatsAppArea from '@/components/Activities/WhatsAppArea.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import ChatBubble from '@/components/Activities/ChatBubble.vue'
import HappenedCard from '@/components/Activities/HappenedCard.vue'
import MoneyIcon from '@/components/Icons/MoneyIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import TimelineEntry from '@/components/Activities/TimelineEntry.vue'
import {
  buildStream,
  dayLabel,
  groupByDay,
  isStageChange,
  speakerOf,
} from '@/utils/conversation'
import {
  formatEuro,
  invoiceLabel,
  invoiceStatusTheme,
  isCreditNote,
  worstStatus,
} from '@/utils/invoicing'
import { sanitizeHTML } from '@/utils'
import { useTimelinePreferences } from '@/composables/useTimelinePreferences'
import { usersStore } from '@/stores/users'
import { Badge, dayjs } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  channel: { type: String, default: 'all' },
  modalRef: { type: Object, default: null },
})

const whatsappMessages = defineModel('whatsappMessages', {
  type: Object,
  default: () => ({}),
})
const reply = defineModel('reply', { type: Object, default: () => ({}) })

const emit = defineEmits(['reload'])

const { isNewestFirst } = useTimelinePreferences()
const { getUser } = usersStore()

// What our own messages are signed with. The logged-in user's own name rather
// than «You», because a shared inbox is read by more than one person and «You»
// is then a different person on every screen.
const me = computed(() => getUser()?.full_name || __('You'))

const days = computed(() =>
  groupByDay(
    buildStream(props.items, {
      channel: props.channel,
      newestFirst: isNewestFirst.value,
    }),
  ).map((group) => ({
    ...group,
    rows: group.rows,
  })),
)

// The clock, for the things that sit in the middle: the day is already written
// on the chip above them.
function timeOf(row) {
  return row.at ? dayjs(row.at).format('HH:mm') : ''
}

// An appointment is the one thing here whose moment is not its own creation, so
// it says the date as well: «mer 8 ott, 15:00» is the fact, and the chip above
// only says which day it was booked on.
function whenOf(at) {
  return at ? dayjs(at).format('ddd D MMM, HH:mm') : ''
}

const APPOINTMENT_THEMES = {
  Scheduled: 'blue',
  Confirmed: 'green',
  Completed: 'gray',
  Cancelled: 'red',
  'No Show': 'orange',
}

function appointmentTheme(status) {
  return APPOINTMENT_THEMES[status] || 'gray'
}

// «Fattura n. 12» rather than «CRM Invoice / INV-2026-00012»: the number is what
// somebody quotes on the phone, and a credit note has to say it is one, because
// the amount alone reads as money coming in either way.
function invoiceTitle(invoice) {
  const kind = isCreditNote(invoice?.document_type)
    ? __('Credit note')
    : __('Invoice')
  const number = invoiceLabel(invoice)
  return number ? `${kind} ${number}` : kind
}

function amountOf(invoice) {
  const total = invoice?.grand_total ?? invoice?.net_payable
  const signed = isCreditNote(invoice?.document_type) ? -Math.abs(total) : total
  return formatEuro(signed)
}

function statusOf(invoice) {
  return worstStatus(invoice || {})
}

// `Today` and `Yesterday` are what somebody is actually asking when they look
// at a date, so they get the words and everything else gets the date.
function dayLabelFor(day) {
  return dayLabel(
    day,
    dayjs().format('YYYY-MM-DD'),
    dayjs().subtract(1, 'day').format('YYYY-MM-DD'),
  )
}

// The WhatsApp view, and only that one, gets WhatsApp's own backdrop: it is what
// makes the difference between a list of messages and a conversation.
const wallpaper = computed(() => props.channel === 'whatsapp')

const ICONS = {
  whatsapp: WhatsAppIcon,
  sms: SMSIcon,
  email: Email2Icon,
  comment: CommentIcon,
  call: PhoneIcon,
}

function iconFor(channel) {
  return ICONS[channel] || DotIcon
}
</script>

<style scoped>
/*
  WhatsApp's paper: the shade, and a doodle over it.

  Drawn here rather than shipped as an asset — the real one is somebody else's
  artwork, and a tiled PNG is weight on every page load. Two colours and eighteen
  little line drawings, faint enough that the bubbles stay the thing you read:
  what the paper does is tell the eye it is looking at a chat rather than a list,
  and a plain beige rectangle does not do that.

  It fills the pane, not the messages. Drawn on the element's own box, the paper
  stopped where the last bubble stopped and left the rest of a half-empty
  conversation on the app's own background — a chat with the wallpaper torn off
  below it. `min-h-full` on the root is the other half of this: the box reaches
  the bottom of the scroller even when there are three messages in it.
*/
.wa-wallpaper {
  background-color: #efeae2;
  background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300'><g fill='none' stroke='%23000000' stroke-opacity='0.06' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><g transform='translate(12 18) rotate(-4) scale(0.8)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(118 44) rotate(-14) scale(0.75)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(214 10) rotate(9) scale(0.8)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(62 92) rotate(0) scale(0.8)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(166 116) rotate(11) scale(0.8)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(252 78) rotate(-7) scale(0.75)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g><g transform='translate(8 150) rotate(5) scale(0.8)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(108 168) rotate(-9) scale(0.8)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(206 196) rotate(3) scale(0.75)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(268 152) rotate(7) scale(0.7)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(40 236) rotate(13) scale(0.8)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(140 262) rotate(-11) scale(0.75)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(232 268) rotate(4) scale(0.75)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(70 62) rotate(-8) scale(0.6)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(152 20) rotate(6) scale(0.6)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(176 224) rotate(-5) scale(0.62)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(274 232) rotate(8) scale(0.62)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(96 126) rotate(5) scale(0.6)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g></g></svg>");
  background-size: 300px 300px;
  background-repeat: repeat;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
}

@media (prefers-color-scheme: dark) {
  .wa-wallpaper {
    /* WhatsApp's own dark paper, which is not grey but very nearly black */
    background-color: #0b141a;
    background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300'><g fill='none' stroke='%23ffffff' stroke-opacity='0.05' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><g transform='translate(12 18) rotate(-4) scale(0.8)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(118 44) rotate(-14) scale(0.75)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(214 10) rotate(9) scale(0.8)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(62 92) rotate(0) scale(0.8)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(166 116) rotate(11) scale(0.8)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(252 78) rotate(-7) scale(0.75)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g><g transform='translate(8 150) rotate(5) scale(0.8)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(108 168) rotate(-9) scale(0.8)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(206 196) rotate(3) scale(0.75)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(268 152) rotate(7) scale(0.7)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(40 236) rotate(13) scale(0.8)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(140 262) rotate(-11) scale(0.75)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(232 268) rotate(4) scale(0.75)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(70 62) rotate(-8) scale(0.6)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(152 20) rotate(6) scale(0.6)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(176 224) rotate(-5) scale(0.62)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(274 232) rotate(8) scale(0.62)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(96 126) rotate(5) scale(0.6)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g></g></svg>");
  }
}
</style>
