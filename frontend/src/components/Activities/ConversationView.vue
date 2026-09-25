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
            puts its own notices between the messages. A note is amber: it is
            the one thing in this chat the customer will never see.
          -->
          <div v-else class="flex justify-center px-3 py-1 sm:px-4">
            <div
              v-if="row.channel === 'comment'"
              class="w-full max-w-[min(92%,44rem)] rounded-lg border border-outline-amber-2 bg-surface-amber-1 px-3 py-2"
            >
              <CommentArea :activity="row.item" @reload="emit('reload')" />
            </div>
            <div
              v-else
              class="flex w-full max-w-[min(92%,44rem)] items-center gap-2 rounded-full bg-surface-gray-2 px-3 py-1 text-p-xs text-ink-gray-6"
            >
              <slot name="other" :item="row.item" :row="row" />
            </div>
          </div>
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
import ChatBubble from '@/components/Activities/ChatBubble.vue'
import TimelineEntry from '@/components/Activities/TimelineEntry.vue'
import {
  buildStream,
  dayLabel,
  groupByDay,
  speakerOf,
} from '@/utils/conversation'
import { useTimelinePreferences } from '@/composables/useTimelinePreferences'
import { usersStore } from '@/stores/users'
import { dayjs } from 'frappe-ui'
import { computed, ref } from 'vue'

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

// The line above a message, and only where the message has none of its own.
// An email, a call and a note already say who and when inside their own
// component; saying it twice is how a card ends up taller than what it holds.
const SAYS_ITS_OWN = new Set(['email', 'comment', 'call'])

function headerOf(row) {
  if (SAYS_ITS_OWN.has(row.channel)) return { speaker: '', time: '' }
  return {
    speaker: speakerOf(row.item, me.value),
    time: row.at ? dayjs(row.at).format('HH:mm') : '',
  }
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

const LABELS = {
  whatsapp: 'WhatsApp',
  sms: 'SMS',
  email: 'Email',
  comment: 'Comment',
  call: 'Call',
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
