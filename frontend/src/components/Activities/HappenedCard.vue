<!--
  Something that happened, rather than something that was said.

  An appointment booked, a task set, a note written, a stage moved, a call: none
  of them is one side talking to the other, so none of them gets a side. They
  sit in the middle of the chat, the way a messenger puts its own notices
  between the messages — which is exactly what they are.

  Two shapes, by weight. Something with content to read — an appointment, a
  task, a note, an invoice — is a card. Something that is one fact — a call, a
  stage moved, a field changed — is one line on a chip, because giving a fact a
  card makes the eye stop for nothing.

  Both are as wide as what they hold, not as wide as the chat. A card stretched
  to the whole pane was a slab between two bubbles, and a one-line notice
  stretched the same way read as a divider rather than as something that
  happened.
-->
<template>
  <div class="flex justify-center px-3 sm:px-4">
    <!-- a card that stands for something with a page of its own opens it -->
    <component
      :is="opens ? 'button' : 'div'"
      v-if="card"
      :type="opens ? 'button' : undefined"
      class="w-full max-w-md rounded-xl border px-3 py-2 text-left shadow-sm"
      :class="[
        tone.edge,
        tone.fill,
        opens &&
          'transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3',
      ]"
      @click="opens && emit('open')"
    >
      <!-- a note brings its own header line, with its author and its menu -->
      <div
        v-if="icon || title || when"
        class="mb-1 flex items-center gap-2 text-p-xs"
        :class="tone.ink"
      >
        <component :is="icon" v-if="icon" class="size-3.5 shrink-0" />
        <span class="min-w-0 truncate font-medium">{{ title }}</span>
        <span v-if="when" class="ml-auto shrink-0 tabular-nums text-ink-gray-5">
          {{ when }}
        </span>
      </div>
      <div class="min-w-0 break-words text-base text-ink-gray-8">
        <slot />
      </div>
    </component>

    <div
      v-else
      class="flex max-w-[min(92%,36rem)] items-center gap-1.5 rounded-lg px-2.5 py-1 text-p-xs shadow-sm"
      :class="[tone.fill, tone.ink, tone.weight]"
    >
      <component :is="icon" v-if="icon" class="size-3.5 shrink-0" />
      <div class="min-w-0">
        <slot />
      </div>
      <span
        v-if="when"
        class="ml-1 shrink-0 font-normal tabular-nums text-ink-gray-5"
      >
        {{ when }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  kind: { type: String, default: '' },
  icon: { type: [Object, Function], default: null },
  title: { type: String, default: '' },
  when: { type: String, default: '' },
  // a card when there is something to read, a line when there is one fact
  card: { type: Boolean, default: false },
  // a call nobody answered is the one line here somebody has to act on
  alarm: { type: Boolean, default: false },
  // a click opens what it stands for (`open`): an appointment, an event
  opens: { type: Boolean, default: false },
})

const emit = defineEmits(['open'])

// The raised surface every notice sits on; a shade up from the chat's own
// background in both themes, which `surface-white` — the token these used to
// ask for — never was: it does not exist, so every card here was transparent.
const RAISED = 'bg-surface-elevation-2 dark:bg-surface-gray-2'

// Written out rather than assembled: Tailwind reads the source for class names
// and never sees one built from a variable.
const TONES = {
  // ours and nobody else's — the one thing in this chat the customer will
  // never see, and the reason it is the only tinted surface here
  note: {
    edge: 'border-outline-amber-2',
    fill: 'bg-surface-amber-1',
    ink: 'text-ink-amber-8',
  },
  // the move that is the point of the whole record
  stage: {
    edge: 'border-outline-gray-2',
    fill: RAISED,
    ink: 'text-ink-gray-8',
    weight: 'font-medium',
  },
}

const PLAIN = {
  edge: 'border-outline-gray-2',
  fill: RAISED,
  ink: 'text-ink-gray-6',
  weight: '',
}

const tone = computed(() => {
  const found = { ...PLAIN, ...TONES[props.kind] }
  // colour on a notice belongs to what went wrong, never to what kind it is
  if (props.alarm) return { ...found, ink: 'text-ink-red-6' }
  return found
})
</script>
