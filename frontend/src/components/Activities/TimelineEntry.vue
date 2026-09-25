<!--
  One thing that happened, in the mixed history.

  A chat puts «them» on the left and «us» on the right, and that works because a
  chat holds **one** conversation. A history holds four of them plus everything
  the record did to itself, so sides stop meaning anything: half the screen is
  empty, the eye crosses it on every row, and a note that is addressed to nobody
  has no side to be on. Every CRM that has solved this draws a single column
  with a gutter of icons, and so does this.

  Colour carries the channel, and it carries it in one place — the chip and a
  hairline down the side of the card. Not the whole card: five tinted surfaces
  stacked on each other is a colour chart, not a history.

  The one colour that says something other than «which channel» is amber: that
  is a note we wrote to each other, which the customer will never see. It is the
  difference worth a colour of its own.
-->
<template>
  <div class="relative grid grid-cols-[28px_minmax(0,1fr)] gap-3">
    <!-- the thread, and the icon sitting on it -->
    <div
      class="relative flex justify-center before:absolute before:left-1/2 before:top-0 before:h-full before:border-l before:border-outline-gray-2"
    >
      <span
        class="relative mt-1 flex size-7 shrink-0 items-center justify-center rounded-full border"
        :class="[tone.chip, tone.edge]"
      >
        <component :is="icon" class="size-3.5" :class="tone.ink" />
      </span>
    </div>

    <div class="min-w-0 pb-3">
      <div
        class="overflow-hidden rounded-lg border border-l-2 bg-surface-white"
        :class="[tone.edge, tone.card]"
      >
        <!--
          A header only where the message itself has none. An email, a call and
          a note already say who and when inside their own component, and saying
          it twice is how a card ends up taller than what it holds.
        -->
        <div
          v-if="speaker || time"
          class="flex items-baseline gap-2 border-b border-outline-gray-1 px-3 py-1.5"
        >
          <span class="truncate text-p-sm font-medium text-ink-gray-8">
            {{ speaker }}
          </span>
          <span class="shrink-0 text-p-xs" :class="tone.ink">{{ label }}</span>
          <span class="ml-auto shrink-0 text-p-xs text-ink-gray-4">
            {{ time }}
          </span>
        </div>
        <div class="px-3 py-2">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  channel: { type: String, default: '' },
  icon: { type: [Object, Function], default: null },
  label: { type: String, default: '' },
  speaker: { type: String, default: '' },
  time: { type: String, default: '' },
  // an incoming message is the one somebody has to do something about, so it
  // carries the colour; ours is the same shape, quieter
  incoming: { type: Boolean, default: false },
})

// Four colours, each meaning something, rather than one per channel for its own
// sake: green is WhatsApp, blue is email, violet is SMS, amber is ours and
// nobody else's. A call has no colour because a call has no content — it is an
// event, and grey is what an event looks like.
const TONES = {
  whatsapp: {
    chip: 'bg-surface-green-1',
    edge: 'border-outline-green-3',
    ink: 'text-ink-green-5',
    card: '',
  },
  email: {
    chip: 'bg-surface-blue-1',
    edge: 'border-outline-blue-3',
    ink: 'text-ink-blue-6',
    card: '',
  },
  sms: {
    chip: 'bg-surface-violet-1',
    edge: 'border-outline-violet-3',
    ink: 'text-ink-gray-6',
    card: '',
  },
  comment: {
    chip: 'bg-surface-amber-1',
    edge: 'border-outline-amber-2',
    ink: 'text-ink-amber-7',
    // the one tinted surface in the whole stream, because it is the one thing
    // here the customer will never see
    card: 'bg-surface-amber-1',
  },
  call: {
    chip: 'bg-surface-gray-2',
    edge: 'border-outline-gray-3',
    ink: 'text-ink-gray-6',
    card: '',
  },
}

const QUIET = {
  chip: 'bg-surface-gray-2',
  edge: 'border-outline-gray-2',
  ink: 'text-ink-gray-5',
  card: '',
}

const tone = computed(() => {
  const found = TONES[props.channel] || QUIET
  // ours is the same card with the colour turned down: the eye should land on
  // what came in, because that is what somebody still has to answer
  if (!props.incoming && props.channel !== 'comment') {
    return { ...found, edge: 'border-outline-gray-2' }
  }
  return found
})
</script>
