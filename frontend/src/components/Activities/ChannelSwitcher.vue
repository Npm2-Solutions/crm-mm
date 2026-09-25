<!--
  The ways of writing, on a strip that never goes away.

  It used to live inside the collapsed bar, which meant it disappeared the
  moment an editor opened: you picked email, the editor took the whole bottom
  of the screen, and to write a WhatsApp message instead you had to discard
  what was open to get the picker back. Choosing the wrong channel is the most
  ordinary mistake there is here, and the way out of it was the most expensive
  thing on the screen.

  So the strip sits above whatever is open — the line, the email editor, the
  WhatsApp box — and one click moves you across. What you typed is kept per
  channel (each box holds its own draft), so coming back finds it where you
  left it.
-->
<template>
  <div
    class="flex items-center gap-1 border-t border-outline-gray-2 bg-surface-white px-3 pt-2 sm:px-4"
  >
    <Tooltip v-for="way in ways" :key="way.key" :text="__(way.label)">
      <button
        class="flex h-7 items-center gap-1.5 rounded px-2 text-p-sm transition-colors"
        :class="
          way.key === channel
            ? ON[way.key]
            : 'text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-7'
        "
        :aria-pressed="way.key === channel"
        @click="emit('pick', way.key)"
      >
        <component :is="way.icon" class="size-4 shrink-0" />
        <!--
          The label rides along on a wide screen. On a phone the icons alone
          have to carry it, and four of them plus four words is a strip that
          scrolls sideways — which is the one thing a switcher must never do,
          because a target you have to find first is not a quick one.
        -->
        <span class="hidden sm:inline">{{ __(way.label) }}</span>
      </button>
    </Tooltip>
  </div>
</template>

<script setup>
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { whatsappEnabled } from '@/composables/whatsapp'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'

defineProps({
  // which way of writing is chosen. A reading-only channel («all», «call»)
  // highlights none of them, which is honest: there is nothing to write there.
  channel: { type: String, default: '' },
})

const emit = defineEmits(['pick'])

const WAYS = [
  { key: 'email', label: 'Email', icon: Email2Icon },
  { key: 'whatsapp', label: 'WhatsApp', icon: WhatsAppIcon },
  { key: 'sms', label: 'SMS', icon: SMSIcon },
  // written about somebody rather than to them, which is why it is last and
  // why its colour is the note's amber wherever it appears
  { key: 'comment', label: 'Comment', icon: CommentIcon },
]

// The chosen one wears its channel's colour — the same colour that channel has
// on the bubbles above — so the strip says where the next message is going
// without anybody reading a word. Written out, never assembled: Tailwind reads
// the source for class names and never sees one built from a variable.
const ON = {
  email: 'bg-surface-blue-2 text-ink-blue-8',
  whatsapp: 'bg-surface-green-2 text-ink-green-8',
  sms: 'bg-surface-violet-2 text-ink-violet-8',
  comment: 'bg-surface-amber-2 text-ink-amber-8',
}

const ways = computed(() =>
  WAYS.filter((way) => way.key !== 'whatsapp' || whatsappEnabled.value),
)
</script>
