<!--
  Something that happened, rather than something that was said.

  An appointment booked, a task set, a note written, a stage moved: none of them
  is addressed to anybody, so none of them gets a side. They sit in the middle
  of the chat, the way a messenger puts its own notices between the messages —
  which is exactly what they are: notices about the record, in the order they
  happened.

  Two shapes, by weight. Something with content to read — an appointment, a
  task, a note — is a card. Something that is one fact — a stage moved, a file
  attached — is one line on a pill, because giving a fact a card makes the eye
  stop for nothing.
-->
<template>
  <div class="flex justify-center px-3 py-1 sm:px-4">
    <div
      v-if="card"
      class="w-full max-w-[min(92%,44rem)] rounded-lg border px-3 py-2"
      :class="[tone.edge, tone.fill]"
    >
      <div class="flex items-center gap-2 text-p-xs" :class="tone.ink">
        <component :is="icon" class="size-3.5 shrink-0" />
        <span class="font-medium">{{ title }}</span>
        <span v-if="when" class="ml-auto shrink-0 text-ink-gray-4">
          {{ when }}
        </span>
      </div>
      <div class="mt-1 text-base text-ink-gray-8">
        <slot />
      </div>
    </div>

    <div
      v-else
      class="flex w-full max-w-[min(92%,44rem)] items-center gap-2 rounded-full px-3 py-1 text-p-xs"
      :class="[tone.fill || 'bg-surface-gray-2', tone.ink]"
    >
      <component :is="icon" v-if="icon" class="size-3 shrink-0" />
      <slot />
      <span v-if="when" class="ml-auto shrink-0 text-ink-gray-4">
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
})

// Written out rather than assembled: Tailwind reads the source for class names
// and never sees one built from a variable.
const TONES = {
  // ours and nobody else's — the one thing in this chat the customer will
  // never see, and the reason it is the only tinted surface here
  note: {
    edge: 'border-outline-amber-2',
    fill: 'bg-surface-amber-1',
    ink: 'text-ink-amber-7',
  },
  appointment: {
    edge: 'border-outline-gray-3',
    fill: 'bg-surface-white',
    ink: 'text-ink-gray-7',
  },
  task: {
    edge: 'border-outline-gray-3',
    fill: 'bg-surface-white',
    ink: 'text-ink-gray-7',
  },
  event: {
    edge: 'border-outline-gray-3',
    fill: 'bg-surface-white',
    ink: 'text-ink-gray-7',
  },
  // the move that is the point of the whole record
  stage: {
    edge: 'border-outline-gray-2',
    fill: 'bg-surface-gray-3',
    ink: 'text-ink-gray-7',
  },
}

const QUIET = {
  edge: 'border-outline-gray-2',
  fill: '',
  ink: 'text-ink-gray-6',
}

const tone = computed(() => TONES[props.kind] || QUIET)
</script>
