<!--
  One message in the mixed chat: a speech balloon, on the side it came from.

  The rule from before stays, because it was right: **the bubble owns the
  chrome, the slot owns the words.** Who, when, whether it arrived, whether it
  was typed on somebody's phone, whether it failed — all drawn here, once, in
  one format. What goes in the slot is the message and nothing else.

  What changed is what the colour means. The fill had been made to say the
  channel — green WhatsApp, blue email — with ours «one shade deeper» than
  theirs. On screen the two shades were one per cent of lightness apart, so in
  a conversation that is mostly WhatsApp every bubble was the same green and
  the side was left saying who spoke on its own. That is the one question a
  chat has to answer at a glance, and it is the question every messenger
  answers with the fill: theirs light, ours tinted. So here:

  - **the fill says who.** Theirs on the raised surface, ours in the house
    blue — the same for every channel, so the eye learns it once.
  - **the channel says itself in its mark**: the glyph beside the clock, in the
    channel's own colour. It is read when you look for it, which is how often
    anybody needs to know which way a message went.

  A run of messages from one side is one voice: the tail and the name go on the
  first of them, and the rest sit close underneath, the way every messenger
  stacks them.
-->
<template>
  <div
    class="group/bubble relative flex min-w-0 max-w-full"
    :class="[mine ? 'justify-end' : 'justify-start', reaction ? 'mb-3' : '']"
  >
    <div
      class="relative min-w-0 rounded-2xl px-3 pb-1.5 pt-2 text-base text-ink-gray-9"
      :class="[
        mine
          ? 'bg-surface-blue-3'
          : 'bg-surface-elevation-2 shadow-sm dark:bg-surface-gray-2',
        tail ? (mine ? 'rounded-tr-md' : 'rounded-tl-md') : '',
        failed ? 'ring-1 ring-inset ring-outline-red-3' : '',
      ]"
    >
      <!--
        The tail, on the first of a run only. `bg-inherit` is the whole trick:
        it takes the bubble's own fill, so one tail serves every side and can
        never drift out of step with the colour it hangs off. Clipped to a
        triangle rather than rotated, because a rotated square pokes a corner
        out the other side.
      -->
      <span
        v-if="tail"
        aria-hidden="true"
        class="absolute top-0 size-2.5 bg-inherit"
        :class="
          mine
            ? '-right-[9px] [clip-path:polygon(0_0,100%_0,0_100%)]'
            : '-left-[9px] [clip-path:polygon(0_0,100%_0,100%_100%)]'
        "
      />

      <!--
        A name only where the side does not already say it: somebody other
        than the person this conversation is with, or a colleague answering
        for us. Signing every message of a one-to-one chat with the name that
        is already in the header is a line of noise per message.
      -->
      <div
        v-if="speaker"
        class="mb-0.5 truncate text-p-xs font-medium"
        :class="mine ? 'text-ink-blue-8' : 'text-ink-gray-7'"
      >
        {{ speaker }}
      </div>

      <!--
        The words and the footer share a line while they fit and part when they
        do not — a flex row that wraps: «ok» keeps its clock beside it, a
        paragraph or an email takes the width and the clock drops to the corner
        underneath, the way WhatsApp itself does it.
      -->
      <div class="flex flex-wrap items-end gap-x-3">
        <div class="min-w-0 break-words">
          <slot />
        </div>

        <!--
          The one footer. A failed send says so here, in words and in the
          bubble's own space: it used to be a badge and a button pinned over
          the top corner, sitting on the first word of the message and on its
          clock.
        -->
        <div
          class="-mb-0.5 ml-auto flex shrink-0 items-center gap-1 pt-1 text-p-xs leading-none text-ink-gray-5"
        >
          <span v-if="failed" class="mr-auto flex items-center gap-1.5 pr-2">
            <Tooltip :text="failure || __('The message did not reach them')">
              <span class="flex items-center gap-1 text-ink-red-8">
                <span class="lucide-circle-alert size-3.5" aria-hidden="true" />
                {{ __('Not delivered') }}
              </span>
            </Tooltip>
            <button
              v-if="retryable"
              class="rounded font-medium text-ink-red-8 underline underline-offset-2 hover:text-ink-red-9 disabled:opacity-60"
              :disabled="retrying"
              @click="emit('retry')"
            >
              {{ retrying ? __('Sending…') : __('Retry') }}
            </button>
          </span>
          <Tooltip v-if="icon && label" :text="label">
            <component :is="icon" class="size-3 shrink-0" :class="ink" />
          </Tooltip>
          <!--
          Typed on somebody's phone rather than in here. The same number is used
          from the CRM and from the WhatsApp app in a pocket, and both halves
          land in this one chat; without the mark, «did I answer this, or did a
          colleague answer from his phone?» has no answer a week later.
        -->
          <Tooltip v-if="phone" :text="__('Sent from the phone')">
            <span
              class="lucide-smartphone size-3 shrink-0"
              aria-hidden="true"
            />
          </Tooltip>
          <Tooltip :text="moment">
            <span class="shrink-0 tabular-nums">{{ time }}</span>
          </Tooltip>
          <!-- what the ticks mean, for whoever has never had to learn it -->
          <Tooltip v-if="tick" :text="tickLabel(tick)">
            <span class="inline-flex shrink-0">
              <CheckIcon v-if="tick === 'one'" class="size-3.5" />
              <DoubleCheckIcon
                v-else
                class="size-3.5"
                :class="tick === 'read' ? 'text-ink-blue-7' : ''"
              />
            </span>
          </Tooltip>
        </div>
      </div>

      <!-- a reaction sits on the bottom edge, where every messenger puts it -->
      <span
        v-if="reaction"
        class="absolute -bottom-3 flex h-6 min-w-6 items-center justify-center rounded-full bg-surface-elevation-2 px-1 text-sm leading-none shadow-sm ring-1 ring-outline-gray-1"
        :class="mine ? 'right-3' : 'left-3'"
      >
        {{ reaction }}
      </span>

      <!--
        What can be done to it — answer, react — beside the bubble on its outer
        side, and only when the pointer is on it: a toolbar on every message is
        a toolbar nobody reads past.
      -->
      <div
        v-if="$slots.actions"
        class="absolute top-1/2 flex -translate-y-1/2 items-center gap-0.5 opacity-0 transition-opacity focus-within:opacity-100 group-hover/bubble:opacity-100"
        :class="mine ? 'right-full mr-1.5' : 'left-full ml-1.5'"
      >
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import DoubleCheckIcon from '@/components/Icons/DoubleCheckIcon.vue'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  channel: { type: String, default: '' },
  // the channel's glyph, and its name for the tooltip; left out where every
  // bubble is the same channel and the mark would say nothing
  icon: { type: [Object, Function], default: null },
  label: { type: String, default: '' },
  // ours, or theirs
  mine: { type: Boolean, default: false },
  // the first of a run carries the tail
  tail: { type: Boolean, default: true },
  speaker: { type: String, default: '' },
  time: { type: String, default: '' },
  // the whole moment, for the tooltip on the clock
  moment: { type: String, default: '' },
  // written from the WhatsApp app rather than from here
  phone: { type: Boolean, default: false },
  // what the carrier said happened to it, in the carrier's own words
  status: { type: String, default: '' },
  failed: { type: Boolean, default: false },
  // why, when the carrier said
  failure: { type: String, default: '' },
  retryable: { type: Boolean, default: false },
  retrying: { type: Boolean, default: false },
  reaction: { type: String, default: '' },
})

const emit = defineEmits(['retry'])

// Written out in full rather than built from the channel name, because Tailwind
// reads the source for class names and never sees one that is assembled.
const INKS = {
  whatsapp: 'text-ink-green-7',
  email: 'text-ink-blue-7',
  sms: 'text-ink-violet-7',
  call: 'text-ink-gray-6',
}

const ink = computed(() => INKS[props.channel] || 'text-ink-gray-6')

function tickLabel(which) {
  if (which === 'read') return __('Read by them')
  if (which === 'delivered') return __('Delivered to their phone')
  return __('Sent')
}

// Only on what we sent: a tick on something they sent us would be claiming we
// delivered it to ourselves. Nothing on a failed one — the footer says why.
const tick = computed(() => {
  if (!props.mine || props.failed) return ''
  const status = String(props.status || '').toLowerCase()
  if (status === 'read') return 'read'
  if (status === 'delivered') return 'delivered'
  if (['sent', 'success'].includes(status)) return 'one'
  return ''
})
</script>
