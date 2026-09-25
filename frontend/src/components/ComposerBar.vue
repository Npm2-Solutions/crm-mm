<!--
  The thin line you write on, before you need anything more.

  Email and comments opened as a full editor — toolbar, subject line, buttons —
  for a message that is usually one sentence. WhatsApp got this right from the
  start: a single line that grows as you type. So both of them start as a line
  too, and the editor arrives when you actually click into it.

  The channel picker sits on the left of the bar rather than above it: they are
  one thing — what you are writing, and where it goes.

  Only ways of writing **to the customer** live here. A note, a task, an event,
  a logged call are things you do *about* somebody, not things you say to them,
  and they all live on the one button at the top. Two places to start the same
  kind of thing is how somebody ends up hunting for the one they used last time.
-->
<template>
  <div class="flex items-center gap-2 border-t px-3 py-2 sm:px-4">
    <div class="flex shrink-0 items-center gap-0.5">
      <Tooltip v-for="way in ways" :key="way.key" :text="__(way.label)">
        <button
          class="flex size-7 items-center justify-center rounded transition-colors"
          :class="
            way.key === channel
              ? 'bg-surface-gray-3 text-ink-gray-8'
              : 'text-ink-gray-5 hover:bg-surface-gray-2'
          "
          @click="pick(way.key)"
        >
          <component :is="way.icon" class="size-4" />
        </button>
      </Tooltip>
    </div>
    <!--
      A button, not an input: what opens is a real editor, and a line that takes
      a keystroke and then swaps itself for something else loses that keystroke.
    -->
    <button
      class="min-w-0 flex-1 truncate rounded-full border border-outline-gray-2 px-3 py-1.5 text-left text-p-sm text-ink-gray-4 transition-colors hover:border-outline-gray-3 hover:bg-surface-gray-1"
      @click="emit('open', channel)"
    >
      {{ __(placeholder) }}
    </button>
  </div>
</template>

<script setup>
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { whatsappEnabled } from '@/composables/whatsapp'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  // which way of writing is chosen: email, comment or whatsapp
  channel: { type: String, default: 'email' },
})

const emit = defineEmits(['open', 'update:channel'])

const WAYS = [
  {
    key: 'email',
    label: 'Email',
    icon: Email2Icon,
    placeholder: 'Write an email…',
  },
  {
    key: 'sms',
    label: 'SMS',
    icon: SMSIcon,
    placeholder: 'Write a text message…',
  },
  {
    key: 'whatsapp',
    label: 'WhatsApp',
    icon: WhatsAppIcon,
    placeholder: 'Write a WhatsApp message…',
  },
]

const ways = computed(() =>
  WAYS.filter((way) => way.key !== 'whatsapp' || whatsappEnabled.value),
)

const placeholder = computed(
  () => WAYS.find((way) => way.key === props.channel)?.placeholder || 'Write…',
)

function pick(key) {
  emit('update:channel', key)
  emit('open', key)
}
</script>
