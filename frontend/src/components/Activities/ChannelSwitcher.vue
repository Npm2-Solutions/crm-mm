<!--
  The ways of writing: the tabs along the top of the composer.

  It used to live inside the collapsed bar, which meant it disappeared the
  moment an editor opened; then it became a strip of its own above every box,
  so one click moves you across and what you typed is kept per channel. That
  stays. What changed is where it sits: on the composer, as its tabs, rather
  than as a row floating over it — it is the composer's own question, «where
  does this go», and it reads as one when it is part of the box that asks it.

  The chosen tab wears its channel's colour, the same one the channel's mark
  has on the bubbles above. Amber is the one that matters most: it is the note,
  which the customer will never see, and the whole composer turns amber with
  it, so nobody types an internal remark believing it is a reply — or a reply
  believing it is only a note.
-->
<template>
  <div class="flex items-center gap-0.5 px-1.5 pt-1.5" role="tablist">
    <Tooltip v-for="option in ways" :key="option.key" :text="__(option.hint)">
      <!-- where the icons alone carry it, each is a 40px square: as 32px
           pills 2px apart a thumb picked the channel beside -->
      <button
        class="flex h-7 items-center gap-1.5 rounded-md px-2 text-p-sm transition-colors max-sm:size-10 max-sm:justify-center max-sm:px-0"
        :class="
          option.key === way
            ? ON[option.key]
            : 'text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8'
        "
        role="tab"
        :aria-selected="option.key === way"
        :aria-label="
          drafted(option)
            ? `${__(option.label)} · ${__('draft')}`
            : __(option.label)
        "
        @click="emit('pick', option.key)"
      >
        <span class="relative shrink-0">
          <component :is="option.icon" class="size-4" />
          <!-- something half-written waits behind this tab -->
          <span
            v-if="drafted(option)"
            class="absolute -right-0.5 -top-0.5 size-1.5 rounded-full"
            :class="DOT[option.key]"
            aria-hidden="true"
          />
        </span>
        <!--
          The label rides along on a wide screen. On a phone the icons alone
          carry it, and four icons plus four words is a strip that scrolls
          sideways — which a switcher must never do, because a target you have
          to find first is not a quick one.
        -->
        <span class="hidden sm:inline">{{ __(option.label) }}</span>
      </button>
    </Tooltip>
    <div class="ml-auto flex min-w-0 items-center pr-1.5">
      <slot name="aside" />
    </div>
  </div>
</template>

<script setup>
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { smsEnabled } from '@/composables/sms'
import { whatsappEnabled } from '@/composables/whatsapp'
import { WAYS } from '@/utils/conversation'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  // which way of writing is chosen
  way: { type: String, default: '' },
  // the ways with something half-written in them
  drafts: { type: Array, default: () => [] },
})

// A dot on the tab of a channel holding a draft — not on the chosen one,
// whose draft is in plain sight in the box below it.
function drafted(option) {
  return option.key !== props.way && props.drafts.includes(option.key)
}

const emit = defineEmits(['pick'])

const DETAILS = {
  whatsapp: {
    label: 'WhatsApp',
    hint: 'Reply on WhatsApp',
    icon: WhatsAppIcon,
    condition: () => whatsappEnabled.value,
  },
  email: { label: 'Email', hint: 'Write an email', icon: Email2Icon },
  sms: {
    label: 'SMS',
    hint: 'Send a text message',
    icon: SMSIcon,
    condition: () => smsEnabled.value,
  },
  // written about somebody rather than to them, which is why it is last and
  // why its colour is the note's amber wherever it appears
  comment: {
    label: 'Note',
    hint: 'A note for the team: the customer will not see it',
    icon: CommentIcon,
  },
}

// Written out, never assembled: Tailwind reads the source for class names and
// never sees one built from a variable.
const ON = {
  whatsapp: 'bg-surface-green-2 text-ink-green-8',
  email: 'bg-surface-blue-2 text-ink-blue-8',
  sms: 'bg-surface-violet-2 text-ink-violet-8',
  comment: 'bg-surface-amber-2 text-ink-amber-8',
}

const DOT = {
  whatsapp: 'bg-surface-green-5',
  email: 'bg-surface-blue-5',
  sms: 'bg-surface-violet-5',
  comment: 'bg-surface-amber-5',
}

const ways = computed(() =>
  WAYS.map((key) => ({ key, ...DETAILS[key] })).filter(
    (option) => !option.condition || option.condition(),
  ),
)
</script>
