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
    The paper fills the pane; the conversation does not.

    On a wide screen a stream that uses the whole width puts the two sides of a
    chat a screen apart, with nothing in between — and a chat read that way is
    not a chat, it is two columns of text. Every messenger caps the column and
    centres it, for the same reason a newspaper has columns: past a certain
    width the eye stops finding the next line.
  -->
  <div :class="wallpaper ? 'wa-wallpaper' : ''">
    <div
      class="mx-auto flex w-full max-w-4xl flex-col"
      :class="channel === 'all' ? 'gap-1' : 'gap-1.5'"
    >
      <template v-for="row in stream" :key="row.key">
        <!-- a message: one side or the other -->
        <div
          v-if="row.direction !== 'internal'"
          class="flex px-3 sm:px-10"
          :class="row.direction === 'out' ? 'justify-end' : 'justify-start'"
        >
          <!-- and inside the column, a bubble stops well short of filling it:
             a line of ~70 characters is where reading stays comfortable -->
          <div class="relative min-w-0 max-w-[min(85%,34rem)]">
            <!--
            The badge travels with the bubble, so it is legible on both sides.

            Only on the mixed stream: in a single channel every row is the same
            channel, and a badge repeated down the whole page says nothing while
            taking up the corner.

            Vertically centred, not at the top: the top corner is where the
            «failed / Retry» pair sits on an outgoing message, and the two were
            landing on each other.
          -->
            <span
              v-if="channel === 'all'"
              class="absolute top-1/2 z-10 flex size-5 -translate-y-1/2 items-center justify-center rounded-full border border-outline-gray-2 bg-surface-white shadow-sm"
              :class="row.direction === 'out' ? '-right-2.5' : '-left-2.5'"
              :title="__(labelFor(row))"
            >
              <component :is="iconFor(row.channel)" class="size-3" />
            </span>

            <SMSArea v-if="row.channel === 'sms'" :messages="[row.item]" />
            <WhatsAppArea
              v-else-if="row.channel === 'whatsapp'"
              v-model="whatsappMessages"
              v-model:reply="reply"
              :messages="[row.item]"
            />
            <CallArea v-else-if="row.channel === 'call'" :activity="row.item" />
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
          </div>
        </div>

        <!-- addressed to nobody: the full width, and a header that says what it is -->
        <div v-else class="px-3 sm:px-10">
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
import { buildStream } from '@/utils/conversation'
import { useTimelinePreferences } from '@/composables/useTimelinePreferences'
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

const stream = computed(() =>
  buildStream(props.items, {
    channel: props.channel,
    newestFirst: isNewestFirst.value,
  }),
)

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
  if (row.direction === 'out') return `${what} — sent`
  if (row.direction === 'in') return `${what} — received`
  return what
}
</script>

<style scoped>
/*
  WhatsApp's own paper. Drawn rather than shipped as an image: a tiled asset for
  a background is weight on every page load, and the pattern is three circles.
*/
.wa-wallpaper {
  background-color: #efeae2;
  background-image:
    radial-gradient(
      circle at 15% 25%,
      rgba(255, 255, 255, 0.55) 2px,
      transparent 2px
    ),
    radial-gradient(
      circle at 65% 70%,
      rgba(255, 255, 255, 0.45) 3px,
      transparent 3px
    ),
    radial-gradient(circle at 40% 90%, rgba(0, 0, 0, 0.03) 2px, transparent 2px);
  background-size: 120px 120px;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
}

@media (prefers-color-scheme: dark) {
  .wa-wallpaper {
    background-color: #0b141a;
    background-image:
      radial-gradient(
        circle at 15% 25%,
        rgba(255, 255, 255, 0.05) 2px,
        transparent 2px
      ),
      radial-gradient(
        circle at 65% 70%,
        rgba(255, 255, 255, 0.04) 3px,
        transparent 3px
      ),
      radial-gradient(
        circle at 40% 90%,
        rgba(255, 255, 255, 0.03) 2px,
        transparent 2px
      );
  }
}
</style>
