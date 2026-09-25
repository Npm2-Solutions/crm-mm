<!--
  The thin line you write on, before you need anything more.

  Email and comments opened as a full editor — toolbar, subject line, buttons —
  for a message that is usually one sentence. WhatsApp got this right from the
  start: a single line that grows as you type. So both of them start as a line
  too, and the editor arrives when you actually click into it.

  The channel picker used to sit on this bar. It lives above it now, on a strip
  of its own that stays put when an editor opens — see ChannelSwitcher — so the
  line here only has one job: say what you are about to write, and open it.

  Only ways of writing live on the strip above. A task, an event, a logged call
  are things you do *about* somebody rather than things you say to them, and
  they stay on the one button at the top.
-->
<template>
  <div class="px-3 pb-2 pt-1.5 sm:px-4">
    <!--
      A button, not an input: what opens is a real editor, and a line that takes
      a keystroke and then swaps itself for something else loses that keystroke.
    -->
    <button
      class="w-full truncate rounded-full border border-outline-gray-2 px-3 py-1.5 text-left text-p-sm text-ink-gray-4 transition-colors hover:border-outline-gray-3 hover:bg-surface-gray-1"
      @click="emit('open', channel)"
    >
      {{ __(placeholder) }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // which way of writing the line is set to: email, sms, whatsapp or comment
  channel: { type: String, default: 'email' },
})

const emit = defineEmits(['open'])

const PLACEHOLDERS = {
  email: 'Write an email…',
  sms: 'Write a text message…',
  whatsapp: 'Write a WhatsApp message…',
  comment: 'Write a comment for the team…',
}

const placeholder = computed(
  () => PLACEHOLDERS[props.channel] || PLACEHOLDERS.email,
)
</script>
