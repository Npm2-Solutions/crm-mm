<!--
  One message in the mixed chat.

  Two encodings, each meaning one thing and never the other:

  - **side and fill** say who. Theirs on the left in white, ours on the right in
    grey. Always, on every channel — so the eye learns it once.
  - **colour** says which channel, and it lives on the edge of the bubble and on
    its little icon, never on the fill. Tinting the fill by channel would make
    colour mean two things at once, and a long chat would read as a colour chart
    instead of a conversation.

  WhatsApp keeps its own green in its own view, where there is one channel and
  the green *is* the channel. Here it takes the house style like everything
  else, so one channel does not shout over four.
-->
<template>
  <div
    class="rounded-lg border px-3 py-2 shadow-sm"
    :class="[edge, mine ? 'bg-surface-gray-2' : 'bg-surface-white']"
  >
    <div
      v-if="speaker"
      class="mb-1 flex items-baseline gap-2 text-p-xs text-ink-gray-5"
    >
      <span class="truncate font-medium text-ink-gray-7">{{ speaker }}</span>
    </div>
    <div class="min-w-0 break-words text-base text-ink-gray-9">
      <slot />
    </div>
    <div class="mt-1 flex items-center justify-end gap-1.5 text-p-xs">
      <component :is="icon" v-if="icon" class="size-3" :class="ink" />
      <span class="text-ink-gray-4">{{ time }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  channel: { type: String, default: '' },
  icon: { type: [Object, Function], default: null },
  // ours, or theirs
  mine: { type: Boolean, default: false },
  speaker: { type: String, default: '' },
  time: { type: String, default: '' },
})

// Written out in full rather than built from the channel name, because Tailwind
// reads the source for class names and never sees one that is assembled.
const EDGES = {
  whatsapp: 'border-outline-green-3',
  email: 'border-outline-blue-3',
  sms: 'border-outline-violet-3',
  call: 'border-outline-gray-3',
}

const INKS = {
  whatsapp: 'text-ink-green-5',
  email: 'text-ink-blue-6',
  sms: 'text-ink-gray-6',
  call: 'text-ink-gray-5',
}

const edge = computed(() => EDGES[props.channel] || 'border-outline-gray-2')
const ink = computed(() => INKS[props.channel] || 'text-ink-gray-5')
</script>
