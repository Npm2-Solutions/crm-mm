<!--
  A face for somebody who has not given us one: their initials, on a tint that
  stays with them.

  Forty grey circles with one letter each is a column the eye reads one by one
  — «L», «M», «S», «L» — until it finds the name. A tint that is always the same
  for the same person is how a list of chats lets you find somebody before you
  have read their name, and two initials tell apart the three Laura in it.
-->
<template>
  <span
    class="relative inline-flex shrink-0 select-none items-center justify-center overflow-hidden rounded-full font-medium"
    :class="[SIZES[size], image ? 'bg-surface-gray-2' : TINTS[toneOf(name)]]"
    :aria-label="name"
    role="img"
  >
    <img
      v-if="image && !broken"
      :src="image"
      :alt="name"
      class="size-full object-cover"
      @error="broken = true"
    />
    <span v-else aria-hidden="true">{{ initialsOf(name) || '?' }}</span>
  </span>
</template>

<script setup>
import { initialsOf, toneOf } from '@/utils/conversation'
import { ref } from 'vue'

defineProps({
  name: { type: String, default: '' },
  image: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const broken = ref(false)

const SIZES = {
  sm: 'size-6 text-2xs',
  md: 'size-8 text-p-xs',
  lg: 'size-10 text-p-sm',
  xl: 'size-16 text-xl',
}

// Eight tints, none of them the ones that mean something in the chat: no
// WhatsApp green, no note amber, no red. Written out: Tailwind reads the source
// for class names and never sees one that is assembled.
const TINTS = [
  'bg-surface-blue-2 text-ink-blue-8',
  'bg-surface-violet-2 text-ink-violet-8',
  'bg-surface-pink-2 text-ink-pink-8',
  'bg-surface-teal-2 text-ink-teal-8',
  'bg-surface-orange-2 text-ink-orange-8',
  'bg-surface-cyan-2 text-ink-cyan-8',
  'bg-surface-purple-2 text-ink-purple-8',
  'bg-surface-gray-3 text-ink-gray-7',
]
</script>
