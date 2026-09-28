<!--
  One message in the mixed chat: a speech balloon, with the tail on the side it
  came from.

  What went wrong before: this drew a name, a channel icon and a clock, and then
  put a whole message component inside — which drew its own name and its own
  clock. Every message carried two timestamps in two different formats and a
  border around a border. A bubble is a frame; a frame around a frame is not a
  design, it is a mistake left in.

  So the rule here is one line long: **the bubble owns the chrome, the slot owns
  the words.** Who, when, whether it was delivered, whether it was typed on
  somebody's phone — all of that is drawn here, once, in one place, in one
  format. What goes in the slot is the message and nothing else.

  Two encodings, each meaning one thing:

  - **the side, and the tail pointing to it**, say who. Theirs on the left,
    ours on the right. It is the oldest convention in messaging and it costs
    nothing to read.
  - **the fill** says which channel. A mixed chat has to say where each message
    came from on every single row, and a tint carries that without adding a
    mark to read. Ours is a shade deeper than theirs, so the two axes never
    collide.
-->
<template>
  <div class="relative" :class="mine ? 'pr-1.5' : 'pl-1.5'">
    <div
      class="relative rounded-2xl px-3 py-2 shadow-sm"
      :class="[fill, mine ? 'rounded-tr-sm' : 'rounded-tl-sm']"
    >
      <!--
        The tail. `bg-inherit` is the whole trick: it takes the bubble's own
        fill, so one tail serves every channel and can never drift out of
        step with the colour it hangs off. Clipped to a triangle rather than
        rotated, because a rotated square pokes a corner out the other side.
      -->
      <span
        aria-hidden="true"
        class="absolute top-0 size-2.5 bg-inherit"
        :class="
          mine
            ? '-right-[9px] [clip-path:polygon(0_0,100%_0,0_100%)]'
            : '-left-[9px] [clip-path:polygon(0_0,100%_0,100%_100%)]'
        "
      />

      <!--
        Their name, on their side only. Ours needs none: the side already says
        it, and a chat that signs every one of your own messages with your own
        name is a chat nobody would use.
      -->
      <div
        v-if="speaker && !mine"
        class="mb-0.5 truncate text-p-xs font-medium"
        :class="ink"
      >
        {{ speaker }}
      </div>

      <div class="min-w-0 break-words text-base text-ink-gray-9">
        <slot />
      </div>

      <!--
        The one footer. It floats to the end of the last line the way a chat's
        does, so a three-word message stays three words wide instead of being
        stretched to fit a clock underneath it.
      -->
      <div
        class="-mb-1 ml-2 flex items-center justify-end gap-1 text-p-xs leading-none text-ink-gray-5"
      >
        <component
          :is="icon"
          v-if="icon"
          class="size-3 shrink-0"
          :class="ink"
        />
        <!--
          Typed on somebody's phone rather than in here. The same number is used
          from the CRM and from the WhatsApp app in a pocket, and both halves
          land in this one chat; without the mark, «did I answer this, or did a
          colleague answer from his phone?» has no answer a week later.
        -->
        <Tooltip v-if="phone" :text="__('Sent from the phone')">
          <LucideSmartphone class="size-3 shrink-0" />
        </Tooltip>
        <span class="shrink-0 tabular-nums">{{ time }}</span>
        <CheckIcon v-if="tick === 'one'" class="size-3.5 shrink-0" />
        <DoubleCheckIcon
          v-else-if="tick"
          class="size-3.5 shrink-0"
          :class="tick === 'read' ? 'text-ink-blue-5' : ''"
        />
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
  icon: { type: [Object, Function], default: null },
  // ours, or theirs
  mine: { type: Boolean, default: false },
  speaker: { type: String, default: '' },
  time: { type: String, default: '' },
  // written from the WhatsApp app rather than from here
  phone: { type: Boolean, default: false },
  // what the carrier said happened to it, in the carrier's own words
  status: { type: String, default: '' },
})

// Written out in full rather than built from the channel name, because Tailwind
// reads the source for class names and never sees one that is assembled.
// Theirs is the light shade, ours one step deeper — the same hue either way, so
// the fill never has to be read twice to work out which channel it is.
const FILLS = {
  whatsapp: { in: 'bg-surface-green-1', out: 'bg-surface-green-2' },
  email: { in: 'bg-surface-blue-1', out: 'bg-surface-blue-2' },
  sms: { in: 'bg-surface-violet-1', out: 'bg-surface-violet-2' },
  call: { in: 'bg-surface-gray-2', out: 'bg-surface-gray-3' },
}

const INKS = {
  whatsapp: 'text-ink-green-7',
  email: 'text-ink-blue-7',
  sms: 'text-ink-violet-7',
  call: 'text-ink-gray-6',
}

const fill = computed(() => {
  const pair = FILLS[props.channel]
  if (!pair) return props.mine ? 'bg-surface-gray-3' : 'bg-surface-gray-2'
  return props.mine ? pair.out : pair.in
})

const ink = computed(() => INKS[props.channel] || 'text-ink-gray-6')

// Only on what we sent: a tick on something they sent us would be claiming we
// delivered it to ourselves.
const tick = computed(() => {
  if (!props.mine) return ''
  if (props.status === 'read') return 'read'
  if (props.status === 'delivered') return 'delivered'
  if (['sent', 'Success'].includes(props.status)) return 'one'
  return ''
})
</script>
