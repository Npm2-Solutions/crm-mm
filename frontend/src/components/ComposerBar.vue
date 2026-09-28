<!--
  The line you write on, before you need anything more.

  Email and comments opened as a full editor — toolbar, subject line, buttons —
  for a message that is usually one sentence. WhatsApp got this right from the
  start: a single line that grows as you type. So both of them start as a line
  too, and the editor arrives when you actually click into it.

  The ways of writing are the composer's tabs, just above this line; the line
  only has one job: say what you are about to write, and open it.
-->
<template>
  <div class="px-1.5 pb-1.5 pt-1">
    <!--
      A button, not an input: what opens is a real editor, and a line that takes
      a keystroke and then swaps itself for something else loses that keystroke.
    -->
    <button
      class="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-p-base text-ink-gray-4 transition-colors hover:bg-surface-alpha-gray-2 hover:text-ink-gray-5"
      @click="emit('open', channel)"
    >
      <span class="min-w-0 flex-1 truncate">{{ __(placeholder) }}</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // which way of writing the line is set to: email or comment
  channel: { type: String, default: 'email' },
})

const emit = defineEmits(['open'])

const PLACEHOLDERS = {
  email: 'Write an email…',
  comment: 'Write a note for the team…',
}

const placeholder = computed(
  () => PLACEHOLDERS[props.channel] || PLACEHOLDERS.email,
)
</script>
