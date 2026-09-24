<!--
  One stream, four channels, and a selector above it.

  Email, WhatsApp, SMS and comments each had a tab of their own, so the question
  anybody actually asks of a record — what has been said to this person, and in
  what order — could only be answered by opening four tabs and remembering three
  of them.

  This component does the **arranging** and nothing else: which rows, in what
  order, on which side, with which badge. What a message looks like inside its
  bubble is still each channel's own component, because those already know about
  replies, reactions, attachments, failed sends and retries, and rewriting that
  to gain a layout would have lost all of it.

  Two shapes, and the rule is not decoration:

  - a message **between two people** has a direction, so it gets a side. Sent on
    the right, received on the left, the way every chat has taught everybody to
    read.
  - a comment, a note, a field that changed is addressed to **nobody**. Giving it
    a side would invent a sender and a recipient, so it takes the full width.

  The channel badge sits **on the bubble**, at its outer corner, and not in a
  column down the left. A column only works while everything is left-aligned:
  the moment half the rows are on the right, the icon is nowhere near the thing
  it describes.
-->
<template>
  <!--
    The conversation takes the pane it was given.

    It used to be capped at a reading column and centred, which on the narrow
    pane of a record meant a chat squeezed into the middle with empty margins on
    both sides — the width was spent on nothing. The cap belongs on the
    **bubble**, where it keeps a line readable; the column itself is the pane,
    the way every messenger draws one.
  -->
  <div class="min-h-full" :class="wallpaper ? 'wa-wallpaper' : ''">
    <div class="flex w-full flex-col">
      <!--
        One block per day, with the date pinned inside it.

        A long conversation is a wall of times with no dates: «12:57» says
        nothing about whether that was today or in April. The date is pinned
        inside its own day rather than alongside every other date in one list —
        sticky siblings all pin to the same line, so yesterday's date stayed on
        screen underneath today's instead of giving way to it. Bounded by its
        day, a date is carried off the top as that day ends and the next one
        takes its place.
      -->
      <div
        v-for="group in days"
        :key="group.key"
        class="flex flex-col"
        :class="channel === 'all' ? 'gap-1' : 'gap-1.5'"
      >
        <!-- a row with no time has no day to show, and an empty chip is worse
           than none -->
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

        <template v-for="row in group.rows" :key="row.key">
          <!-- a message: one side or the other -->
          <div
            v-if="row.direction !== 'internal'"
            class="flex px-3 sm:px-4"
            :class="row.direction === 'out' ? 'justify-end' : 'justify-start'"
          >
            <!-- and inside the pane, a bubble stops short of filling it: the
             other side has to have somewhere to be, and a line of ~80
             characters is where reading stays comfortable -->
            <div class="relative min-w-0 max-w-[min(80%,42rem)]">
              <SMSArea v-if="row.channel === 'sms'" :messages="[row.item]" />
              <WhatsAppArea
                v-else-if="row.channel === 'whatsapp'"
                v-model="whatsappMessages"
                v-model:reply="reply"
                :messages="[row.item]"
              />
              <!--
              A call reads as a bubble like everything else — same shape, same
              side, so the eye follows one conversation. A different surface,
              not a different green: borrowing WhatsApp's colour for a phone
              call would say the call happened on WhatsApp.
            -->
              <div
                v-else-if="row.channel === 'call'"
                class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-2"
              >
                <CallArea :activity="row.item" />
              </div>
              <div
                v-else
                class="rounded-lg border bg-surface-white p-3"
                :class="
                  row.direction === 'out'
                    ? 'border-outline-blue-1'
                    : 'border-outline-gray-2'
                "
              >
                <EmailArea :activity="row.item" :modalRef="modalRef" />
              </div>

              <!--
              The channel, under the bubble instead of pinned to its corner.

              A badge on the corner had nothing to sit on that was not already
              taken — the failed/Retry pair on one side, a reaction on the other
              — and it collided with whichever it met. Here it cannot collide
              with anything, it reads as words rather than as a symbol to
              decode, and it takes the side the message is on.
            -->
              <div
                v-if="channel === 'all'"
                class="flex items-center gap-1 px-1 pt-0.5 text-p-xs text-ink-gray-5"
                :class="
                  row.direction === 'out' ? 'justify-end' : 'justify-start'
                "
              >
                <component :is="iconFor(row.channel)" class="size-3" />
                <span>{{ __(labelFor(row)) }}</span>
              </div>
            </div>
          </div>

          <!-- addressed to nobody: the full width, and a header that says what it is -->
          <div v-else class="px-3 sm:px-4">
            <div class="flex items-start gap-2 py-1.5">
              <span
                class="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border border-outline-gray-2 bg-surface-white"
              >
                <component :is="iconFor(row.channel)" class="size-3" />
              </span>
              <div class="min-w-0 flex-1">
                <CommentArea
                  v-if="row.channel === 'comment'"
                  :activity="row.item"
                  @reload="emit('reload')"
                />
                <!-- everything the record did to itself: the caller renders those,
                 because it already knows how -->
                <slot v-else name="other" :item="row.item" :row="row" />
              </div>
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
import { buildStream, dayLabel, groupByDay } from '@/utils/conversation'
import { useTimelinePreferences } from '@/composables/useTimelinePreferences'
import { dayjs } from 'frappe-ui'
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

const days = computed(() =>
  groupByDay(
    buildStream(props.items, {
      channel: props.channel,
      newestFirst: isNewestFirst.value,
    }),
  ),
)

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

function labelFor(row) {
  const what = LABELS[row.channel] || 'Activity'
  // A call is not sent or received, it is made or taken. The side already says
  // which; the caption says it in words for anyone who reads before looking.
  if (row.channel === 'call') {
    if (row.direction === 'out') return `${what} — outgoing`
    if (row.direction === 'in') return `${what} — incoming`
    return what
  }
  if (row.direction === 'out') return `${what} — sent`
  if (row.direction === 'in') return `${what} — received`
  return what
}
</script>

<style scoped>
/*
  WhatsApp's paper: the shade, and a doodle over it.

  Drawn here rather than shipped as an asset — the real one is somebody else's
  artwork, and a tiled PNG is weight on every page load. Two colours and eleven
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
  background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300'><g fill='none' stroke='%23000000' stroke-opacity='0.075' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><g transform='translate(16 24) rotate(0)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(124 12) rotate(-12)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(232 26) rotate(8)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(56 104) rotate(0)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(152 92) rotate(10)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(244 116) rotate(-6)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g><g transform='translate(18 198) rotate(6)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(130 192) rotate(-8)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(238 214) rotate(0)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(82 256) rotate(-6)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(196 272) rotate(14)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g></g></svg>");
  background-size: 300px 300px;
  background-repeat: repeat;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
}

@media (prefers-color-scheme: dark) {
  .wa-wallpaper {
    /* WhatsApp's own dark paper, which is not grey but very nearly black */
    background-color: #0b141a;
    background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300'><g fill='none' stroke='%23ffffff' stroke-opacity='0.06' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><g transform='translate(16 24) rotate(0)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(124 12) rotate(-12)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(232 26) rotate(8)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(56 104) rotate(0)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(152 92) rotate(10)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(244 116) rotate(-6)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g><g transform='translate(18 198) rotate(6)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(130 192) rotate(-8)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(238 214) rotate(0)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(82 256) rotate(-6)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(196 272) rotate(14)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g></g></svg>");
  }
}
</style>
